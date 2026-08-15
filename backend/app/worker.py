"""arq worker — background jobs (FCM fan-out, AI pipeline, retention).

Run with: `arq app.worker.WorkerSettings` (this is the compose `worker` service).
Phase 0 ships only the smoke-test task; real jobs land with Phases 2 and 5.
"""

import logging
import os

from arq.connections import RedisSettings

logger = logging.getLogger("nearhelp.worker")


async def startup(ctx: dict) -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info("worker started")


async def shutdown(ctx: dict) -> None:
    logger.info("worker stopped")


async def ping(ctx: dict) -> str:
    """Smoke-test task — proves the worker is reachable through Redis."""
    return "pong"


class WorkerSettings:
    """arq entrypoint class (convention: settings as class attributes)."""

    functions = [ping]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    job_timeout = 60
    max_jobs = 10
