"""Internal endpoints — machine-driven, protected by a shared secret.

Cloud Scheduler (or the worker's dev cron) hits /internal/escalation/tick
every ~10 s. The secret header keeps stray traffic out; the endpoint itself is
idempotent by construction (wave CAS — Architecture.md §5).
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_session
from app.services import escalation

logger = logging.getLogger("nearhelp.internal")

router = APIRouter(prefix="/internal", tags=["internal"], include_in_schema=False)


def _guard(secret: str | None) -> None:
    if secret != get_settings().internal_tick_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")


@router.post("/escalation/tick")
async def escalation_tick(
    session: AsyncSession = Depends(get_session),
    x_tick_secret: str | None = Header(default=None),
) -> dict[str, int]:
    _guard(x_tick_secret)
    summary = await escalation.run_escalation_tick(session)
    if any(summary.values()):
        logger.info("escalation tick: %s", summary)
    return summary
