"""Auth endpoints — register / login / refresh (Phase 1).

Refresh rotation: every refresh invalidates the presented token's jti (Redis
revocation list, TTL = remaining token lifetime) and issues a new pair. A
replayed token therefore fails with 401. Revocation fails CLOSED: if Redis is
unreachable we refuse to rotate rather than risk honoring a revoked token.
"""

import logging
import uuid

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import ip_rate_limit
from app.core.redis import get_redis
from app.core.security import (
    create_token_pair,
    decode_token,
    hash_password,
    refresh_expiry_seconds,
    verify_password,
)
from app.db.session import get_session
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RefreshRequest, RegisterRequest, UserOut

logger = logging.getLogger("nearhelp.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"], dependencies=[Depends(ip_rate_limit)])


def _auth_response(user: User) -> AuthResponse:
    return AuthResponse(**create_token_pair(user.id), user=UserOut.from_user(user))


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    email = body.email.lower()
    existing = await session.scalar(select(User).where(func.lower(User.email) == email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="an account with this email exists"
        )
    user = User(
        email=email,
        name=body.name,
        phone=body.phone,
        password_hash=hash_password(body.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info("user registered", extra={"path": "/api/auth/register", "status": 201})
    return _auth_response(user)


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> AuthResponse:
    user = await session.scalar(select(User).where(func.lower(User.email) == body.email.lower()))
    if (
        user is None
        or user.password_hash is None
        or not verify_password(body.password, user.password_hash)
    ):
        # Same message for unknown email and wrong password — no account enumeration.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid email or password"
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="account suspended")
    return _auth_response(user)


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_session),
    redis: Redis = Depends(get_redis),
) -> AuthResponse:
    try:
        payload = decode_token(body.refresh_token, expected_type="refresh")
    except pyjwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired refresh token"
        ) from None

    jti = payload["jti"]
    try:
        if await redis.get(f"revoked:{jti}"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="refresh token already used or revoked",
            )
    except HTTPException:
        raise
    except Exception:
        # Fail CLOSED — do not mint tokens when we cannot check revocation.
        logger.exception("revocation list unreachable — refusing token refresh")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="token service temporarily unavailable",
        ) from None

    user = await session.get(User, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found or suspended"
        )

    # Rotate: burn the old jti for its remaining lifetime, then issue a new pair.
    ttl = refresh_expiry_seconds(payload)
    if ttl > 0:
        await redis.setex(f"revoked:{jti}", ttl, "1")
    return _auth_response(user)
