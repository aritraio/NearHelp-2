"""Test configuration.

Integration tests need a real Postgres (PostGIS types) — no SQLite fallback.
They run automatically when the DB is reachable (docker compose up, or the CI
service containers) and skip with a clear reason otherwise. Redis is always
faked (fakeredis) so rate-limit/revocation tests are hermetic.

Loop hygiene: every TestClient runs the app in its own portal event loop, so
(a) fixture SQL goes through a separate SYNC engine, and (b) the app's cached
async engine/session factory are cleared after each test — otherwise pooled
asyncpg connections leak across loops and explode on reuse.
"""

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
os.environ.setdefault("GEMINI_API_KEY", "")
# Never pool asyncpg connections across the test/client event loops.
os.environ.setdefault("DATABASE_POOL", "null")

import pytest  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.redis import get_redis  # noqa: E402
from app.main import app  # noqa: E402
from fakeredis import FakeAsyncRedis  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

sync_engine = create_engine(get_settings().database_url_sync, pool_pre_ping=True)


def db_reachable() -> bool:
    try:
        with sync_engine.connect():
            return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def db_available() -> bool:
    return db_reachable()


@pytest.fixture(autouse=True)
def _fresh_engines():
    """Reset per-process engine caches so no test reuses another loop's pool."""
    from app.core import arq_pool
    from app.db import session as session_module

    arq_pool._pool = None  # noqa: SLF001
    yield
    session_module.get_engine.cache_clear()
    session_module.get_session_factory.cache_clear()
    arq_pool._pool = None  # noqa: SLF001


@pytest.fixture
def fake_redis():
    redis = FakeAsyncRedis(decode_responses=True)
    app.dependency_overrides[get_redis] = lambda: redis
    yield redis
    app.dependency_overrides.pop(get_redis, None)


@pytest.fixture
def client(fake_redis):
    """API client with faked Redis (rate limits, revocation list, quota)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_clean(db_available):
    """Truncates user-owned tables before each integration test.

    TRUNCATE ... CASCADE clears skill_verifications / user_devices /
    sos_events / responses / timeline_events via their FKs.
    """
    if not db_available:
        pytest.skip("Postgres not reachable at DATABASE_URL — start the stack (README)")
    with sync_engine.begin() as conn:
        conn.execute(text("TRUNCATE users CASCADE"))


def run_sql(statement: str, params: dict | None = None) -> None:
    """Fixture-side SQL through the sync engine (never the app's async pool)."""
    with sync_engine.begin() as conn:
        conn.execute(text(statement), params or {})


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


def set_location(client: TestClient, token: str, lat: float, lon: float) -> None:
    response = client.put(
        "/api/users/me/location", headers=auth_headers(token), json={"lat": lat, "lon": lon}
    )
    assert response.status_code == 204, response.text


def set_skills(email: str, skills: list[dict], trust: float = 50.0) -> None:
    import json as jsonlib

    run_sql(
        "UPDATE users SET skills = CAST(:skills AS jsonb), trust_score = :trust "
        "WHERE email = :email",
        {"skills": jsonlib.dumps(skills), "trust": trust, "email": email},
    )
