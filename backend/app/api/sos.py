"""SOS endpoints — the critical path (Phase 2).

Create requires an Idempotency-Key header (BLUEPRINT.md §4); respond is
naturally idempotent; visibility is limited to the broadcaster and notified
responders.
"""

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user_with_rate_limit
from app.core.rate_limit import consume_sos_quota
from app.core.redis import get_redis
from app.db.session import get_session
from app.models.sos import Response, SosEvent
from app.models.user import User
from app.schemas.sos import (
    MessageOut,
    ResolveRequest,
    ResponderOut,
    RespondOut,
    SosCreateRequest,
    SosOut,
    TimelineEventOut,
)
from app.services import sos_service
from app.services.geo import point

router = APIRouter(prefix="/api/sos", tags=["sos"])


async def _load_event_for_user(session: AsyncSession, sos_id: uuid.UUID, user: User) -> SosEvent:
    """Participant-gated load: broadcaster or a notified responder."""
    event = await session.get(SosEvent, sos_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="event not found")
    if event.broadcaster_id == user.id:
        return event
    if await sos_service.get_participation(session, event, user.id) is not None:
        return event
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="event not found")


async def _event_out(session: AsyncSession, event: SosEvent, responses: list[Response]) -> SosOut:
    lat, lon = await sos_service.event_lat_lon(session, event)
    return SosOut(
        id=event.id,
        status=event.status,
        crisis_type=event.crisis_type,
        severity_score=event.severity_score,
        description=event.description,
        lat=lat,
        lon=lon or 0.0,
        radius_m=event.radius_m,
        escalation_wave=event.escalation_wave,
        is_drill=event.is_drill,
        created_at=event.created_at,
        resolved_at=event.resolved_at,
        notified_count=len(responses),
        responders=[
            ResponderOut(
                responder_id=r.responder_id,
                name=r.responder_name,  # type: ignore[attr-defined]  # set by _load_responses
                status=r.status,
                eta_seconds=r.eta_seconds,
            )
            for r in responses
        ],
    )


@router.post("/create", response_model=SosOut, status_code=status.HTTP_201_CREATED)
async def create_sos(
    body: SosCreateRequest,
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> SosOut:
    if not (8 <= len(idempotency_key) <= 64):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header must be 8-64 characters",
        )
    await consume_sos_quota(redis, str(user.id))

    event, _created = await sos_service.create_sos(
        session,
        redis=redis,
        user=user,
        lat=body.lat,
        lon=body.lon,
        description=body.description,
        crisis_type=body.crisis_type,
        is_drill=body.is_drill,
        idempotency_key=idempotency_key,
    )
    responses = await _load_responses(session, event.id)
    return await _event_out(session, event, responses)


async def _load_responses(session: AsyncSession, sos_id: uuid.UUID) -> list[Response]:
    from app.models.user import User as UserModel

    rows = await session.execute(
        select(Response, UserModel.name.label("responder_name"))
        .join(UserModel, UserModel.id == Response.responder_id)
        .where(Response.sos_event_id == sos_id)
        .order_by(Response.created_at.asc())
    )
    result = []
    for response, name in rows:
        response.responder_name = name  # type: ignore[attr-defined]
        result.append(response)
    return result


@router.get("/nearby-count")
async def nearby_responder_count(
    lat: float,
    lon: float,
    radius_m: int = 2_000,
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    """Feeds the Home screen's 'N responders nearby' stat (DESIGN.md §4.1)."""
    if not (-90 <= lat <= 90 and -180 <= lon <= 180) or not (100 <= radius_m <= 10_000):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="lat/lon out of range or radius_m outside 100-10000",
        )
    origin = point(lat, lon)
    count = await session.scalar(
        select(func.count())
        .select_from(User)
        .where(
            User.id != user.id,
            User.is_active.is_(True),
            User.location.is_not(None),
            func.ST_DWithin(User.location, origin, radius_m),
        )
    )
    return {"count": int(count or 0)}


@router.get("/active", response_model=list[SosOut])
async def my_active_events(
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
) -> list[SosOut]:
    broadcasting = await session.scalars(
        select(SosEvent)
        .where(SosEvent.broadcaster_id == user.id, SosEvent.status.in_(("pending", "active")))
        .order_by(SosEvent.created_at.desc())
    )
    out = [
        await _event_out(session, event, await _load_responses(session, event.id))
        for event in broadcasting
    ]

    responding = await session.scalars(
        select(SosEvent)
        .join(Response, Response.sos_event_id == SosEvent.id)
        .where(
            Response.responder_id == user.id,
            SosEvent.status.in_(("pending", "active")),
            Response.status.in_(("accepted",)),
        )
        .order_by(SosEvent.created_at.desc())
    )
    for event in responding:
        out.append(await _event_out(session, event, await _load_responses(session, event.id)))
    return out


@router.get("/{sos_id}", response_model=SosOut)
async def get_sos(
    sos_id: uuid.UUID,
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
) -> SosOut:
    event = await _load_event_for_user(session, sos_id, user)
    return await _event_out(session, event, await _load_responses(session, event.id))


@router.post("/{sos_id}/respond", response_model=RespondOut)
async def respond_to_sos(
    sos_id: uuid.UUID,
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
) -> RespondOut:
    event = await _load_event_for_user(session, sos_id, user)
    if event.status not in ("pending", "active"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"event already {event.status}"
        )
    response = await sos_service.accept_response(session, event, user)
    return RespondOut(response_id=response.id, status=response.status)


@router.post("/{sos_id}/arrive", response_model=RespondOut)
async def arrive_on_scene(
    sos_id: uuid.UUID,
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
) -> RespondOut:
    """Accepted responder on scene (Phase 4): accepted → arrived + timeline."""
    event = await _load_event_for_user(session, sos_id, user)
    response = await sos_service.mark_arrived(session, event, user)
    return RespondOut(response_id=response.id, status=response.status)


@router.put("/{sos_id}/resolve", response_model=SosOut)
async def resolve(
    sos_id: uuid.UUID,
    body: ResolveRequest,
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
) -> SosOut:
    event = await _load_event_for_user(session, sos_id, user)
    if event.broadcaster_id != user.id:
        participation = await sos_service.get_participation(session, event, user.id)
        if participation is None or participation.status != "accepted":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="only the broadcaster or an accepted responder can resolve",
            )
    event = await sos_service.resolve_sos(session, event, user, body.outcome)
    return await _event_out(session, event, await _load_responses(session, event.id))


@router.post("/{sos_id}/ack", response_model=RespondOut)
async def ack_sos(
    sos_id: uuid.UUID,
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
) -> RespondOut:
    """App-level delivery ACK — the honest 'reached this device' signal."""
    event = await _load_event_for_user(session, sos_id, user)
    response = await sos_service.ack_response(session, event, user)
    return RespondOut(response_id=response.id, status=response.status)


@router.get("/{sos_id}/timeline", response_model=list[TimelineEventOut])
async def timeline(
    sos_id: uuid.UUID,
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
) -> list[TimelineEventOut]:
    from app.models.timeline import TimelineEvent

    event = await _load_event_for_user(session, sos_id, user)
    rows = await session.scalars(
        select(TimelineEvent)
        .where(TimelineEvent.sos_event_id == event.id)
        .order_by(TimelineEvent.created_at.asc())
    )
    return [
        TimelineEventOut(
            event_type=row.event_type,
            actor_id=row.actor_id,
            details=row.details,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/{sos_id}/messages", response_model=list[MessageOut])
async def messages(
    sos_id: uuid.UUID,
    user: User = Depends(current_user_with_rate_limit),
    session: AsyncSession = Depends(get_session),
) -> list[MessageOut]:
    """Chat history — the reconnect path after a WS drop (todos.md §4)."""
    from app.models.message import Message

    event = await _load_event_for_user(session, sos_id, user)
    rows = await session.execute(
        select(Message, User.name)
        .join(User, User.id == Message.sender_id, isouter=True)
        .where(Message.sos_event_id == event.id)
        .order_by(Message.created_at.asc())
        .limit(200)
    )
    return [
        MessageOut(
            id=message.id,
            sender_id=message.sender_id,
            sender_name=name or "unknown",
            text=message.text,
            created_at=message.created_at,
        )
        for message, name in rows
    ]
