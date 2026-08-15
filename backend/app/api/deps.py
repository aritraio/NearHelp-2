"""Shared FastAPI dependencies — current-user resolution and per-user rate limit."""

import uuid

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import user_rate_limit
from app.core.redis import get_redis
from app.core.security import decode_token
from app.db.session import get_session
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except pyjwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = await session.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user not found or suspended",
        )
    return user


async def current_user_with_rate_limit(
    user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis),
) -> User:
    """Authenticated user + the 100 req/min per-user limit (BLUEPRINT.md §6)."""
    await user_rate_limit(redis, str(user.id))
    return user
