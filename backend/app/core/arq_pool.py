"""Shared arq client pool — enqueue background jobs from the API layer."""

import logging

from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import get_settings

logger = logging.getLogger("nearhelp.arq")

_pool = None


async def get_arq_pool():
    """Lazily connect to the arq queue; caller handles connection failures."""
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    return _pool
