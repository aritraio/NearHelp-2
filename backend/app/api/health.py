"""Health endpoints — process liveness plus honest database readiness.

Returns 200 whenever the process can serve traffic; the `db` field reports
connectivity separately ("down" still answers 200 by design — the compose
healthcheck gates on process health, and operators get the real DB state
without pages of false alarms from a one-line endpoint).
"""

import asyncio

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import get_engine

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    db_state = "up"
    try:
        async with asyncio.timeout(2.0):
            async with get_engine().connect() as conn:
                await conn.execute(text("SELECT 1"))
    except Exception:
        db_state = "down"
    return {"status": "ok", "db": db_state, "env": get_settings().env}
