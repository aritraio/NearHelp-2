"""Trust score updates — minimal Phase 2 version.

Full badge/reputation engine lands in Phase 6; the SOS resolve flow only needs
the clamped delta application. Done at the SQL level (greatest/least) so
concurrent updates can never read-modify-write past the [0, 100] bounds.
"""

import uuid

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

TRUST_MIN = 0.0
TRUST_MAX = 100.0


async def apply_delta(session: AsyncSession, user_id: uuid.UUID, delta: float) -> None:
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            trust_score=func.greatest(TRUST_MIN, func.least(TRUST_MAX, User.trust_score + delta))
        )
    )
