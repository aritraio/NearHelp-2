"""Auth request/response schemas (Phase 1)."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    # bcrypt hard-truncates above 72 bytes — reject instead of silently weakening.
    password: str = Field(min_length=8, max_length=72)
    name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9]{7,15}$")

    @field_validator("password")
    @classmethod
    def password_not_too_long_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password must be at most 72 bytes")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    phone: str | None
    languages: list[Any]
    skills: list[Any]
    trust_score: float
    created_at: datetime

    @classmethod
    def from_user(cls, user: Any) -> "UserOut":
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            phone=user.phone,
            languages=user.languages,
            skills=user.skills,
            trust_score=user.trust_score,
            created_at=user.created_at,
        )


class AuthResponse(BaseModel):
    token_type: str
    access_token: str
    expires_in: int
    refresh_token: str
    user: UserOut
