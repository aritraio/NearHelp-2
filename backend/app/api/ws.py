"""WebSocket channel for one SOS event (Architecture.md §7).

Auth: one-time tickets issued over REST (`POST /api/sos/{id}/ws-ticket`,
participants only), consumed atomically via Redis GETDEL — no long-lived token
ever appears in a URL. The relay handles two client messages:

    location_update {lat, lon, ts}   → rate-limited to 1 / 2 s per socket,
                                       broadcast as responder_update + persisted
                                       to users.location (fresh geo queries)
    send_message {text, language}    → persisted to messages, broadcast as
                                       new_message to everyone on the channel

Server pushes (accept/arrive/resolve/escalation) arrive via broadcast_safe
from the services; malformed client frames are dropped, never fatal.
"""

import asyncio
import logging
import secrets
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from geoalchemy2 import WKTElement
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.redis import get_redis
from app.db.session import get_session, get_session_factory
from app.models.message import Message
from app.models.sos import SosEvent
from app.models.user import User
from app.realtime import manager
from app.realtime.manager import Connection
from app.services import sos_service

logger = logging.getLogger("nearhelp.ws")

router = APIRouter(tags=["realtime"])

TICKET_TTL_S = 60
LOCATION_MIN_INTERVAL_S = 2.0
MAX_MESSAGE_LEN = 1_000


class WsTicketOut(BaseModel):
    ticket: str
    expires_in: int


def _point(lat: float, lon: float) -> WKTElement:
    return WKTElement(f"POINT({lon:.8f} {lat:.8f})", srid=4326)


@router.post("/api/sos/{sos_id}/ws-ticket", response_model=WsTicketOut)
async def issue_ticket(
    sos_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> WsTicketOut:
    """Participants only: a 60-second, single-use connection ticket."""
    event = await session.get(SosEvent, sos_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="event not found")
    if event.broadcaster_id != user.id and (
        await sos_service.get_participation(session, event, user.id) is None
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="event not found")

    ticket = secrets.token_urlsafe(24)
    await redis.setex(f"ws_ticket:{ticket}", TICKET_TTL_S, f"{sos_id}:{user.id}")
    return WsTicketOut(ticket=ticket, expires_in=TICKET_TTL_S)


async def _consume_ticket(ticket: str, sos_id: uuid.UUID) -> tuple[uuid.UUID, str, str] | None:
    """GETDEL: exactly one connection can ever use a ticket."""
    if not ticket:
        return None
    raw = await get_redis().getdel(f"ws_ticket:{ticket}")
    if not raw:
        return None
    try:
        ticket_sos, ticket_user = str(raw).split(":")
        if uuid.UUID(ticket_sos) != sos_id:
            return None
        user_id = uuid.UUID(ticket_user)
    except ValueError:
        return None

    async with get_session_factory()() as session:
        user = await session.get(User, user_id)
        event = await session.get(SosEvent, sos_id)
        if user is None or event is None or not user.is_active:
            return None
        role = "broadcaster" if event.broadcaster_id == user_id else "responder"
        return user_id, user.name, role


@router.websocket("/api/ws/{sos_id}")
async def sos_channel(websocket: WebSocket, sos_id: uuid.UUID) -> None:
    consumed = await _consume_ticket(websocket.query_params.get("ticket", ""), sos_id)
    if consumed is None:
        await websocket.close(code=4401)
        return
    user_id, name, role = consumed

    await websocket.accept()
    connection = Connection(websocket=websocket, user_id=user_id, name=name, role=role)
    manager.connect(sos_id, connection)

    session_factory = get_session_factory()
    try:
        while True:
            data = await websocket.receive_json()
            kind = data.get("type")
            if kind == "location_update":
                await _handle_location(sos_id, connection, data, session_factory)
            elif kind == "send_message":
                await _handle_message(sos_id, connection, data, session_factory)
            # Unknown frame types are ignored — forward compatibility.
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(sos_id, user_id)


async def _handle_location(sos_id, connection, data: dict, session_factory) -> None:
    now = time.monotonic()
    if now - connection.last_location_at < LOCATION_MIN_INTERVAL_S:
        return  # rate limited: drop, don't disconnect
    try:
        lat = float(data["lat"])
        lon = float(data["lon"])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return
    except (KeyError, TypeError, ValueError):
        return
    connection.last_location_at = now

    # Keep users.location fresh so later geo queries see moving responders.
    async with session_factory() as session:
        await session.execute(
            update(User).where(User.id == connection.user_id).values(location=_point(lat, lon))
        )
        await session.commit()

    asyncio.get_running_loop().create_task(
        manager.broadcast(
            sos_id,
            {
                "type": "responder_update",
                "responder_id": str(connection.user_id),
                "name": connection.name,
                "lat": lat,
                "lon": lon,
                "ts": data.get("ts") or time.time(),
            },
        )
    )


async def _handle_message(sos_id, connection, data: dict, session_factory) -> None:
    text = str(data.get("text", "")).strip()[:MAX_MESSAGE_LEN]
    if not text:
        return
    language = str(data.get("language") or "en")[:8]

    async with session_factory() as session:
        message = Message(
            sos_event_id=sos_id, sender_id=connection.user_id, text=text, language=language
        )
        session.add(message)
        await session.commit()
        # Server defaults (id, created_at) need a reload before use.
        await session.refresh(message)
        message_id = str(message.id)
        created_at = message.created_at.isoformat()

    asyncio.get_running_loop().create_task(
        manager.broadcast(
            sos_id,
            {
                "type": "new_message",
                "id": message_id,
                "sender_id": str(connection.user_id),
                "sender_name": connection.name,
                "text": text,
                "language": language,
                "created_at": created_at,
            },
        )
    )
