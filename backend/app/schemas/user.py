"""User profile request/response schemas (Phase 1)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9]{7,15}$")
    languages: list[str] | None = None

    @field_validator("languages")
    @classmethod
    def iso_639_1_codes(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        if len(value) > 5:
            raise ValueError("at most 5 languages")
        for code in value:
            if len(code) != 2 or not code.isalpha() or not code.islower():
                raise ValueError(f"invalid ISO 639-1 code: {code!r}")
        return value


class FcmTokenRequest(BaseModel):
    # device_id: stable per install (client-generated UUID) — the upsert key
    # that makes FCM registration multi-device aware.
    device_id: str = Field(min_length=8, max_length=100)
    fcm_token: str = Field(min_length=20, max_length=255)


class LocationUpdateRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class SkillClaimRequest(BaseModel):
    skill_type: str


class SkillVerificationOut(BaseModel):
    id: uuid.UUID
    skill_type: str
    status: str
    submitted_at: datetime
    has_certificate: bool
