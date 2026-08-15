"""Test configuration.

Integration tests need a real Postgres (PostGIS types) — no SQLite fallback.
They run automatically when DATABASE_URL is reachable (docker compose up, or
the CI service containers) and skip with a clear reason otherwise.
Redis is always faked (fakeredis) so rate-limit/revocation tests are hermetic.
"""

import asyncio
import os

# Point at the standard local stack before app settings are first resolved.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://nearhelp:nearhelp@localhost:5432/nearhelp"
)
os.environ.setdefault(
    "DATABASE_URL_SYNC", "postgresql+psycopg://nearhelp:nearhelp@localhost:5432/nearhelp"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CERTIFICATE_DIR", "/tmp/nearhelp-test-certificates")

import pytest  # noqa: E402
from app.core.redis import get_redis  # noqa: E402
from app.main import app  # noqa: E402
from fakeredis import FakeAsyncRedis  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


async def _db_reachable() -> bool:
    from app.db.session import get_engine
    from sqlalchemy import text

    try:
        async with asyncio.timeout(2.0):
            async with get_engine().connect() as conn:
                await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def db_available() -> bool:
    return asyncio.run(_db_reachable())


@pytest.fixture
def fake_redis():
    redis = FakeAsyncRedis(decode_responses=True)
    app.dependency_overrides[get_redis] = lambda: redis
    yield redis
    app.dependency_overrides.pop(get_redis, None)


@pytest.fixture
def client(fake_redis):
    """API client with faked Redis (rate limits, revocation list)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_clean(db_available):
    """Truncates user-owned tables before each integration test.

    TRUNCATE ... CASCADE clears skill_verifications / user_devices via FKs.
    """
    if not db_available:
        pytest.skip("Postgres not reachable at DATABASE_URL — start the stack (README)")
    from app.db.session import get_session_factory
    from sqlalchemy import text

    async def _truncate() -> None:
        async with get_session_factory()() as session:
            await session.execute(text("TRUNCATE users CASCADE"))
            await session.commit()

    asyncio.run(_truncate())


def register_user(
    client: TestClient, email: str = "user@test.dev", password: str = "secret123"
) -> dict:
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "name": "Test User"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
