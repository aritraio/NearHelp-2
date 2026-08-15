"""SOS engine — creation, participation, and the state machine.

State machine (Architecture.md §5):
    PENDING → ACTIVE (first responder accepts) → RESOLVED
    PENDING → EXPIRED (escalation tick, 15 min without any acceptance)

Every transition appends a timeline event. The create path keeps its budget:
validate → quota → persist → geo → rank → response rows → enqueue fan-out.
Nothing synchronous talks to FCM or Gemini.
"""

import logging
import time
import uuid

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import constants as c
from app.core.arq_pool import get_arq_pool
from app.models.sos import Response, SosEvent
from app.models.timeline import TimelineEvent
from app.models.user import User
from app.realtime import broadcast_safe
from app.services.geo import nearby_users, point
from app.services.ranking import rank_candidates, top_n_for_severity
from app.services.trust import apply_delta

logger = logging.getLogger("nearhelp.sos")

IDEMPOTENCY_TTL_S = 86_400
RESPOND_TRUST_DELTA = 3.0  # accepted responders earn +3 when the event resolves
DEFAULT_RADIUS_M = 2_000  # severity-driven radii arrive with the AI module (Phase 5)


async def record_timeline(
    session: AsyncSession,
    sos_event_id: uuid.UUID,
    event_type: str,
    actor_id: uuid.UUID | None = None,
    details: dict | None = None,
) -> None:
    session.add(
        TimelineEvent(
            sos_event_id=sos_event_id,
            event_type=event_type,
            actor_id=actor_id,
            details=details or {},
        )
    )


async def create_sos(
    session: AsyncSession,
    redis: Redis,
    user: User,
    lat: float,
    lon: float,
    description: str | None,
    crisis_type: str | None,
    is_drill: bool,
    idempotency_key: str,
) -> tuple[SosEvent, bool]:
    """Creates the event + initial responder wave. Returns (event, created?).

    Idempotency: Redis guards the fast path; the Postgres unique index on
    sos_events.idempotency_key is the durable backstop (Architecture.md §10).
    """
    cache_key = f"idem:sos:{idempotency_key}"
    if existing_id := await redis.get(cache_key):
        event = await session.get(SosEvent, uuid.UUID(existing_id))
        if event is not None:
            return event, False

    event = SosEvent(
        broadcaster_id=user.id,
        crisis_type=crisis_type,
        description=description,
        location=point(lat, lon),
        status="pending",
        is_drill=is_drill,
        radius_m=DEFAULT_RADIUS_M,
        idempotency_key=idempotency_key,
    )
    session.add(event)
    try:
        await session.flush()
    except IntegrityError:
        # Backstop path: a duplicate slipped past Redis (restart, eviction).
        await session.rollback()
        existing = await session.scalar(
            select(SosEvent).where(SosEvent.idempotency_key == idempotency_key)
        )
        assert existing is not None
        return existing, False

    await redis.set(cache_key, str(event.id), ex=IDEMPOTENCY_TTL_S)

    await record_timeline(
        session,
        event.id,
        c.EVENT_SOS_CREATED,
        actor_id=user.id,
        details={"crisis_type": crisis_type, "is_drill": is_drill},
    )
    await _notify_wave(session, event, wave=0, exclude={user.id})
    await session.commit()
    await session.refresh(event)
    return event, True


async def event_lat_lon(session: AsyncSession, event: SosEvent) -> tuple[float, float]:
    """Extract (lat, lon) from the event's GEOGRAPHY point."""
    location = event.location
    assert location is not None
    row = (
        await session.execute(
            select(
                func.ST_Y(location).label("lat"),
                func.ST_X(location).label("lon"),
            )
        )
    ).one()
    return float(row.lat), float(row.lon)


async def _notify_wave(
    session: AsyncSession, event: SosEvent, wave: int, exclude: set[uuid.UUID]
) -> list[uuid.UUID]:
    """Geo + rank + Response rows + enqueue fan-out for one notification wave."""
    lat, lon = await event_lat_lon(session, event)

    geo_started = time.perf_counter()
    candidates = await nearby_users(
        session, lat=lat, lon=lon, radius_m=event.radius_m, exclude_user_ids=exclude
    )
    geo_ms = int((time.perf_counter() - geo_started) * 1000)

    rank_started = time.perf_counter()
    ranked = rank_candidates(
        candidates,
        crisis_type=event.crisis_type,
        radius_m=event.radius_m,
        top_n=top_n_for_severity(event.severity_score),
    )
    rank_ms = int((time.perf_counter() - rank_started) * 1000)

    responder_ids = [r.candidate.user_id for r in ranked]
    for r in ranked:
        session.add(
            Response(sos_event_id=event.id, responder_id=r.candidate.user_id, status="notified")
        )
    await session.flush()

    await record_timeline(
        session,
        event.id,
        c.EVENT_RESPONDERS_NOTIFIED,
        details={
            "wave": wave,
            "notified": len(responder_ids),
            "radius_m": event.radius_m,
            "geo_ms": geo_ms,
            "rank_ms": rank_ms,
        },
    )

    try:
        pool = await get_arq_pool()
        await pool.enqueue_job("fan_out_sos", str(event.id), wave, responder_ids)
    except Exception:
        # Fan-out degradation is visible (timeline has the wave) and the tick
        # re-escalates; never fail the create because Redis/arq blinked.
        logger.exception("fan-out enqueue failed for sos %s wave %s", event.id, wave)
    return responder_ids


async def get_participation(
    session: AsyncSession, event: SosEvent, user_id: uuid.UUID
) -> Response | None:
    return await session.scalar(
        select(Response).where(Response.sos_event_id == event.id, Response.responder_id == user_id)
    )


async def accept_response(session: AsyncSession, event: SosEvent, user: User) -> Response:
    """Idempotent accept: notified/acked → accepted; event PENDING → ACTIVE."""
    response = await get_participation(session, event, user.id)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you were not notified for this emergency",
        )
    if response.status == "accepted":
        return response
    if response.status not in ("notified", "acked"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"response already {response.status}",
        )

    response.status = "accepted"
    if event.status == "pending":
        event.status = "active"
    await record_timeline(session, event.id, c.EVENT_RESPONSE_ACCEPTED, actor_id=user.id)
    await session.commit()
    await session.refresh(response)
    broadcast_safe(
        event.id,
        {"type": "responder_accepted", "responder_id": str(user.id), "name": user.name},
    )
    return response


async def mark_arrived(session: AsyncSession, event: SosEvent, user: User) -> Response:
    """Accepted responder on scene (Phase 4): accepted → arrived."""
    response = await get_participation(session, event, user.id)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you were not notified for this emergency",
        )
    if response.status == "arrived":
        return response
    if response.status != "accepted":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"cannot arrive from status {response.status}",
        )

    response.status = "arrived"
    await record_timeline(session, event.id, c.EVENT_RESPONDER_ARRIVED, actor_id=user.id)
    await session.commit()
    await session.refresh(response)
    broadcast_safe(
        event.id,
        {"type": "responder_arrived", "responder_id": str(user.id), "name": user.name},
    )
    return response


async def ack_response(session: AsyncSession, event: SosEvent, user: User) -> Response:
    """App-level delivery ACK (Architecture.md §8): notified → acked."""
    response = await get_participation(session, event, user.id)
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="you were not notified for this emergency",
        )
    if response.status == "notified":
        response.status = "acked"
        await session.commit()
        await session.refresh(response)
    return response


async def resolve_sos(
    session: AsyncSession, event: SosEvent, user: User, outcome: str | None
) -> SosEvent:
    if event.status not in ("pending", "active"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"event already {event.status}"
        )
    event.status = "resolved"
    event.resolved_at = func.now()
    await record_timeline(
        session, event.id, c.EVENT_SOS_RESOLVED, actor_id=user.id, details={"outcome": outcome}
    )

    # Accepted responders earn trust once the event is genuinely resolved.
    accepted = await session.scalars(
        select(Response).where(Response.sos_event_id == event.id, Response.status == "accepted")
    )
    for response in accepted:
        await apply_delta(session, response.responder_id, RESPOND_TRUST_DELTA)

    await session.commit()
    await session.refresh(event)
    broadcast_safe(event.id, {"type": "sos_resolved", "resolved_by": str(user.id)})
    return event
