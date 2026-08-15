"""NearHelp AI backend — application entrypoint.

uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import ai, auth, health, internal, sos, users, ws
from app.core.config import get_settings
from app.core.logging import configure_logging

logger = logging.getLogger("nearhelp")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("startup", extra={"env": settings.env})
    yield
    logger.info("shutdown")
    from app.db.session import get_engine
    from app.realtime import manager

    await manager.close_all()  # graceful WebSocket drain (todos.md §4)
    await get_engine().dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title="NearHelp AI",
        version="0.1.0",
        description="AI-powered community emergency response network",
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(sos.router)
    app.include_router(internal.router)
    app.include_router(ws.router)
    app.include_router(ai.router)
    ai.register_sos_guidance_route(sos.router)
    return app


app = create_app()
