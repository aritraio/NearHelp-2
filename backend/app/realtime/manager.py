"""In-process WebSocket channel manager (Architecture.md §7).

One channel per SOS event; participants keyed by user id (one socket per user
per event). Server-side pushes (accept/resolve/escalation) call broadcast_safe
from request handlers; the single-instance fan-out is plain dict iteration —
the Redis pub/sub extraction for multi-instance is a later config change and
this class is the only thing that would change.
"""

import asyncio
import contextlib
import logging
import uuid
from dataclasses import dataclass, field

from fastapi import WebSocket

logger = logging.getLogger("nearhelp.realtime")


@dataclass
class Connection:
    websocket: WebSocket
    user_id: uuid.UUID
    name: str
    role: str  # broadcaster | responder
    last_location_at: float = field(default=-10.0)


class ConnectionManager:
    def __init__(self) -> None:
        self._channels: dict[uuid.UUID, dict[uuid.UUID, Connection]] = {}

    def connect(self, sos_id: uuid.UUID, connection: Connection) -> None:
        self._channels.setdefault(sos_id, {})[connection.user_id] = connection
        logger.info(
            "ws connect sos=%s user=%s (%d on channel)",
            sos_id,
            connection.user_id,
            len(self._channels[sos_id]),
        )

    def disconnect(self, sos_id: uuid.UUID, user_id: uuid.UUID) -> None:
        channel = self._channels.get(sos_id)
        if channel and channel.pop(user_id, None) is not None:
            logger.info("ws disconnect sos=%s user=%s", sos_id, user_id)
        if channel is not None and not channel:
            self._channels.pop(sos_id, None)

    def get(self, sos_id: uuid.UUID, user_id: uuid.UUID) -> Connection | None:
        return self._channels.get(sos_id, {}).get(user_id)

    async def broadcast(
        self, sos_id: uuid.UUID, payload: dict, exclude_user: uuid.UUID | None = None
    ) -> None:
        for user_id, connection in list(self._channels.get(sos_id, {}).items()):
            if exclude_user is not None and user_id == exclude_user:
                continue
            await self._send(connection, payload)

    async def send_to_user(self, sos_id: uuid.UUID, user_id: uuid.UUID, payload: dict) -> None:
        connection = self.get(sos_id, user_id)
        if connection is not None:
            await self._send(connection, payload)

    async def _send(self, connection: Connection, payload: dict) -> None:
        try:
            await connection.websocket.send_json(payload)
        except Exception:
            # Socket died mid-send; the receive loop's finally will clean up.
            logger.debug("ws send failed user=%s", connection.user_id)

    async def close_all(self) -> None:
        """Graceful drain on shutdown (todos.md §4)."""
        for channel in list(self._channels.values()):
            for connection in list(channel.values()):
                with contextlib.suppress(Exception):
                    await connection.websocket.close(code=1001)
        self._channels.clear()


manager = ConnectionManager()


def broadcast_safe(sos_id: uuid.UUID, payload: dict) -> None:
    """Fire-and-forget broadcast from request handlers; never raises."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast(sos_id, payload))
    except RuntimeError:
        pass  # no running loop (CLI context) — nothing to notify
