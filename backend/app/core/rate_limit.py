"""Rate limiting primitives (Phase 1) — Redis fixed-window counters.

Policy (todos.md Phase 1 / BLUEPRINT.md §6):
  - authenticated requests:  rate_limit_per_min per user (default 100/min)
  - unauthenticated /api/auth/*: auth_rate_limit_per_min per IP (default 30/min)
  - SOS daily quota (default 10/day) is enforced by the SOS engine in Phase 2
    via consume_sos_quota().

The Redis client is always injected (FastAPI DI or explicit argument) so tests
can swap in fakeredis. Failure mode: Redis unreachable → **fail open** and log
for rate limits — losing a limit for a minute beats bricking the path behind
it (Architecture.md §11). The SOS quota is the exception: it fails CLOSED.
"""

import logging

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.redis import get_redis

logger = logging.getLogger("nearhelp.rate_limit")


async def _hit(redis: Redis, key: str, limit: int, window_sec: int) -> bool:
    """Fixed-window counter; returns True when the request is allowed."""
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window_sec)
    return count <= limit


async def check_rate_limit(redis: Redis, key: str, limit: int, window_sec: int = 60) -> None:
    """Raise 429 when over limit. Fails open on Redis errors."""
    try:
        allowed = await _hit(redis, f"rl:{key}", limit, window_sec)
    except Exception:
        logger.exception("rate limit check failed (redis unreachable) — allowing request")
        return
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="rate limit exceeded — slow down",
        )


async def ip_rate_limit(request: Request, redis: Redis = Depends(get_redis)) -> None:
    """Dependency for unauthenticated endpoints (login/register brute-force guard)."""
    settings = get_settings()
    ip = request.client.host if request.client else "unknown"
    await check_rate_limit(redis, f"ip:{ip}", settings.auth_rate_limit_per_min)


async def user_rate_limit(redis: Redis, user_id: str) -> None:
    """Called with an injected client after authentication."""
    await check_rate_limit(redis, f"user:{user_id}", get_settings().rate_limit_per_min)


async def consume_sos_quota(redis: Redis, user_id: str) -> None:
    """Phase 2 hook: daily SOS quota (default 10/day per user). Fails CLOSED —
    a quota we can't check is a quota we don't grant (false emergencies hurt)."""
    settings = get_settings()
    try:
        allowed = await _hit(redis, f"sos_quota:{user_id}", settings.sos_daily_limit, 86_400)
    except Exception:
        logger.exception("sos quota check failed (redis unreachable)")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="quota service unavailable — try again",
        ) from None
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="daily SOS limit reached",
        )
