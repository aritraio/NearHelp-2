"""Seed N test users at random locations inside the Kolkata metro bbox.

Run from backend/ (needs a migrated database — see README quickstart):

    python -m scripts.seed_test_users            # 1000 users (default)
    python -m scripts.seed_test_users --count 500

All seeded users share the password "volunteer" (e.g. volunteer0001@nearhelp.dev).
Then proves the geo path end-to-end (Phase 0 acceptance criterion): runs the
exact ST_DWithin query the SOS engine will use and prints the closest seeded
responders to Salt Lake Sector V with distances in meters.
"""

import argparse
import asyncio
import random
import sys
import uuid
from collections.abc import Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.core.constants import SKILL_TYPES as SKILL_CATALOG  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.user import User  # noqa: E402
from geoalchemy2 import WKTElement  # noqa: E402
from sqlalchemy import delete, func, insert, select  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

# Kolkata metropolitan bbox (approximate)
LAT_MIN, LAT_MAX = 22.46, 22.65
LON_MIN, LON_MAX = 88.28, 88.45
LANGUAGES = [["en"], ["bn"], ["hi"], ["bn", "en"], ["hi", "en"]]

# Demo SOS origin: Salt Lake, Kolkata (proposal §12.3 uses the same reference point)
SALT_LAKE_LON, SALT_LAKE_LAT = 88.3639, 22.5726
QUERY_RADIUS_M = 3000
BATCH_SIZE = 200
SEED_PASSWORD = "volunteer"  # shared login password for all seeded test users
_SHARED_HASH = hash_password(SEED_PASSWORD)


def random_user_row(i: int, rng: random.Random) -> dict:
    skills = []
    if rng.random() < 0.45:  # ~45% of volunteers claim at least one skill
        skills = [
            {"skill_type": s, "verified": rng.random() < 0.5}
            for s in rng.sample(SKILL_CATALOG, rng.randint(1, 2))
        ]
    return {
        "id": uuid.uuid4(),
        "email": f"volunteer{i:04d}@nearhelp.dev",
        "name": f"Volunteer {i:04d}",
        # Shared dev password ("volunteer") — one hash, reused for all 1,000 rows.
        "password_hash": _SHARED_HASH,
        "phone": f"+9198{rng.randint(10**7, 10**8 - 1)}",
        "languages": rng.choice(LANGUAGES),
        "skills": skills,
        "trust_score": round(rng.uniform(30, 95), 1),
        "location": WKTElement(
            f"POINT({rng.uniform(LON_MIN, LON_MAX):.6f} {rng.uniform(LAT_MIN, LAT_MAX):.6f})",
            srid=4326,
        ),
        "is_active": True,
    }


async def seed(count: int) -> None:
    engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    rng = random.Random(42)  # deterministic — reproducible demos and benchmarks

    try:
        async with session_factory() as session:
            wiped = await session.execute(delete(User).where(User.email.like("%@nearhelp.dev")))
            await session.commit()
            print(f"removed {wiped.rowcount} previous test users")

            batch: Sequence[dict] = []
            for i in range(1, count + 1):
                batch = [*batch, random_user_row(i, rng)]
                if len(batch) >= BATCH_SIZE:
                    await session.execute(insert(User).values(list(batch)))
                    batch = []
            if batch:
                await session.execute(insert(User).values(list(batch)))
            await session.commit()
            print(f"inserted {count} test users (Kolkata bbox, seed=42)")

            # --- Phase 0 AC: the SOS engine's nearby-user query, for real ---
            origin = WKTElement(f"POINT({SALT_LAKE_LON} {SALT_LAKE_LAT})", srid=4326)
            distance = func.ST_Distance(User.location, origin).label("distance_m")

            within = await session.scalar(
                select(func.count())
                .select_from(User)
                .where(
                    User.is_active.is_(True), func.ST_DWithin(User.location, origin, QUERY_RADIUS_M)
                )
            )
            print(f"\nnearby query (r={QUERY_RADIUS_M}m from Salt Lake): {within} users found")

            rows = await session.execute(
                select(User.name, User.email, User.skills, User.trust_score, distance)
                .where(
                    User.is_active.is_(True), func.ST_DWithin(User.location, origin, QUERY_RADIUS_M)
                )
                .order_by(distance.asc())
                .limit(5)
            )
            print("closest 5 responders:")
            for name, _email, skills, trust, dist in rows:
                skill_names = [s["skill_type"] for s in skills] or ["unskilled"]
                print(
                    f"  {dist:>7.0f} m  {name:<16} trust={trust:<5} skills={','.join(skill_names)}"
                )
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1000)
    args = parser.parse_args()
    asyncio.run(seed(args.count))


if __name__ == "__main__":
    main()
