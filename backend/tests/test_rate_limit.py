"""Rate limiting behavior against fakeredis — no real Redis needed."""

import pytest
from app.core.config import get_settings
from app.core.rate_limit import check_rate_limit, consume_sos_quota
from fastapi import HTTPException

from tests.conftest import auth_headers, register_user


async def test_per_user_limit_blocks_after_window_quota(fake_redis):
    settings = get_settings()
    key = "user:test-user"
    for _ in range(settings.rate_limit_per_min):
        await check_rate_limit(fake_redis, key, settings.rate_limit_per_min)

    with pytest.raises(HTTPException) as exc:
        await check_rate_limit(fake_redis, key, settings.rate_limit_per_min)
    assert exc.value.status_code == 429


async def test_sos_daily_quota(fake_redis):
    settings = get_settings()
    for _ in range(settings.sos_daily_limit):
        await consume_sos_quota(fake_redis, "sos-user")

    with pytest.raises(HTTPException) as exc:
        await consume_sos_quota(fake_redis, "sos-user")
    assert exc.value.status_code == 429


def test_authenticated_requests_rate_limited(client, db_clean, fake_redis):
    """The 100/min user limit is enforced on /api/users/me."""
    settings = get_settings()
    tokens = register_user(client, email="limited@nearhelp.dev")
    headers = auth_headers(tokens["access_token"])

    codes = [
        client.get("/api/users/me", headers=headers).status_code
        for _ in range(settings.rate_limit_per_min + 2)
    ]
    assert 200 in codes
    assert codes[-1] == 429


def test_ip_rate_limit_on_auth(client, db_clean, fake_redis):
    """Login brute-forcing hits the per-IP limit."""
    settings = get_settings()
    original = settings.auth_rate_limit_per_min
    settings.auth_rate_limit_per_min = 5
    try:
        codes = [
            client.post(
                "/api/auth/login", json={"email": "x@y.dev", "password": "wrong-wrong"}
            ).status_code
            for _ in range(7)
        ]
    finally:
        settings.auth_rate_limit_per_min = original
    assert codes[-1] == 429
