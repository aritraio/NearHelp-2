"""Geo service — the only place PostGIS is queried (Architecture.md §3.3).

Returns plain Candidate rows so ranking stays a pure function and the Digital
Twin simulator can call either layer directly for benchmarks.
"""

import uuid
from dataclasses import dataclass
from typing import Any

from geoalchemy2 import WKTElement
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@dataclass(frozen=True)
class Candidate:
    user_id: uuid.UUID
    name: str
    skills: list[dict[str, Any]]
    trust_score: float
    distance_m: float


def point(lat: float, lon: float) -> WKTElement:
    return WKTElement(f"POINT({lon:.8f} {lat:.8f})", srid=4326)


async def nearby_users(
    session: AsyncSession,
    lat: float,
    lon: float,
    radius_m: int,
    exclude_user_ids: set[uuid.UUID] | None = None,
    limit: int = 200,
) -> list[Candidate]:
    """Active users with a location within radius_m, nearest first.

    GEOGRAPHY gives ST_DWithin/ST_Distance meters without projection math.
    """
    origin = point(lat, lon)
    distance = func.ST_Distance(User.location, origin).label("distance_m")
    stmt: Select = (
        select(User.id, User.name, User.skills, User.trust_score, distance)
        .where(
            User.is_active.is_(True),
            User.location.is_not(None),
            func.ST_DWithin(User.location, origin, radius_m),
        )
        .order_by(distance.asc())
        .limit(limit)
    )
    if exclude_user_ids:
        stmt = stmt.where(User.id.not_in(exclude_user_ids))

    rows = await session.execute(stmt)
    return [
        Candidate(
            user_id=row.id,
            name=row.name,
            skills=list(row.skills),
            trust_score=row.trust_score,
            distance_m=float(row.distance_m),
        )
        for row in rows
    ]
