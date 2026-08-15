"""Password hashing and JWT issue/verify (Phase 1).

Token shape (both types):
    sub  — user id (string UUID)
    type — "access" | "refresh"
    exp / iat — epoch seconds
    jti — unique id; tracked for refresh-token rotation revocation
"""

import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings

BCRYPT_COST = 12
_BCRYPT_MAX_PASSWORD_BYTES = 72  # bcrypt truncates silently above this


class PasswordTooLong(Exception):
    pass


def hash_password(password: str) -> str:
    if len(password.encode("utf-8")) > _BCRYPT_MAX_PASSWORD_BYTES:
        raise PasswordTooLong
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_COST)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _token(user_id: uuid.UUID, token_type: str, ttl: timedelta) -> tuple[str, str, int]:
    """Returns (token, jti, ttl_seconds)."""
    settings = get_settings()
    now = datetime.now(UTC)
    ttl_seconds = int(ttl.total_seconds())
    jti = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
        "jti": jti,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, jti, ttl_seconds


def create_token_pair(user_id: uuid.UUID) -> dict[str, Any]:
    settings = get_settings()
    access, _access_jti, _ = _token(
        user_id, "access", timedelta(minutes=settings.access_token_ttl_min)
    )
    refresh, _refresh_jti, _ = _token(
        user_id, "refresh", timedelta(days=settings.refresh_token_ttl_days)
    )
    return {
        "token_type": "bearer",
        "access_token": access,
        "expires_in": settings.access_token_ttl_min * 60,
        "refresh_token": refresh,
    }


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Decode and validate a JWT; raises jwt.PyJWTError on any problem."""
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"expected {expected_type} token")
    return payload


def refresh_expiry_seconds(payload: dict[str, Any]) -> int:
    """Remaining lifetime of a token — used as the revocation-list TTL."""
    return max(0, int(payload["exp"] - time.time()))
