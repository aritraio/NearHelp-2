"""Push notifications — FCM data messages with a log-only dev fallback.

We send *data* messages at high priority (not notification messages): the app
controls rendering (full-screen SOS activity, DRILL banners, per-channel sound)
and can post the app-level ACK that gives us honest delivery metrics
(Architecture.md §8). FCM's UNREGISTERED response prunes stale device tokens.
"""

import logging
from typing import Protocol
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.device import UserDevice

logger = logging.getLogger("nearhelp.push")

CHUNK_SIZE = 50


class PushSender(Protocol):
    async def send_tokens(self, tokens: list[str], data: dict[str, str]) -> dict:
        """Returns {'success': n, 'failure': n, 'unregistered': [tokens]}."""
        ...


class LogPushSender:
    """Dev/demo fallback — no Firebase credentials configured.

    Logs one structured line per chunk. The two-device AC (real push on device
    B) requires the Firebase service account; until then this keeps the entire
    pipeline exercisable and honest about what happened.
    """

    async def send_tokens(self, tokens: list[str], data: dict[str, str]) -> dict:
        logger.info(
            "push (log-only sender)",
            extra={"devices": len(tokens), "payload": data},
        )
        return {"success": len(tokens), "failure": 0, "unregistered": []}


class FcmPushSender:
    """Real sender via firebase-admin; initializes lazily on first use."""

    def __init__(self, service_account_file: str) -> None:
        self._service_account_file = service_account_file
        self._app = None

    def _ensure_init(self) -> None:
        if self._app is None:
            import firebase_admin
            from firebase_admin import credentials

            cred = credentials.Certificate(self._service_account_file)
            self._app = firebase_admin.initialize_app(cred)

    async def send_tokens(self, tokens: list[str], data: dict[str, str]) -> dict:
        import firebase_admin.messaging as messaging

        self._ensure_init()
        message = messaging.MulticastMessage(
            tokens=tokens,
            data={k: str(v) for k, v in data.items()},
            android=messaging.AndroidConfig(priority="high"),
        )
        response = messaging.send_each_for_multicast(message)
        unregistered = []
        failures = 0
        for token, result in zip(tokens, response.responses, strict=True):
            if result.success:
                continue
            failures += 1
            exc = getattr(result, "exception", None)
            if exc is not None and getattr(exc, "code", None) == "UNREGISTERED":
                unregistered.append(token)
        return {
            "success": response.success_count,
            "failure": failures,
            "unregistered": unregistered,
        }


_sender: PushSender | None = None


def get_push_sender() -> PushSender:
    global _sender
    if _sender is None:
        account_file = get_settings().fcm_service_account_file
        _sender = FcmPushSender(account_file) if account_file else LogPushSender()
    return _sender


async def devices_for_responders(
    session: AsyncSession, responder_ids: list[UUID]
) -> dict[UUID, list[str]]:
    """Current FCM tokens per responder (all their registered devices)."""
    if not responder_ids:
        return {}
    rows = await session.execute(
        select(UserDevice.user_id, UserDevice.fcm_token).where(
            UserDevice.user_id.in_(responder_ids)
        )
    )
    devices: dict[UUID, list[str]] = {}
    for user_id, token in rows:
        devices.setdefault(user_id, []).append(token)
    return devices


async def prune_unregistered(session: AsyncSession, tokens: list[str]) -> int:
    """Delete device rows whose FCM token FCM reports dead — token hygiene."""
    if not tokens:
        return 0
    result = await session.execute(delete(UserDevice).where(UserDevice.fcm_token.in_(tokens)))
    return int(result.rowcount or 0)  # type: ignore[attr-defined]  # CursorResult at runtime


def sos_alert_payload(sos_id, crisis_type, severity, is_drill, lat, lon) -> dict[str, str]:
    """The data message the Android FCM receiver parses into the alert screen."""
    return {
        "type": "sos_alert",
        "sos_id": str(sos_id),
        "crisis_type": crisis_type or "other",
        "severity": str(severity if severity is not None else ""),
        "is_drill": "true" if is_drill else "false",
        "lat": f"{lat:.6f}",
        "lon": f"{lon:.6f}",
    }
