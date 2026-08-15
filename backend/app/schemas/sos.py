"""SOS request/response schemas (Phase 2)."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.core.constants import CRISIS_TYPES


class SosCreateRequest(BaseModel):
    description: str | None = Field(default=None, max_length=2000)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    crisis_type: str | None = None
    is_drill: bool = False

    @field_validator("crisis_type")
    @classmethod
    def known_crisis(cls, value: str | None) -> str | None:
        if value is not None and value not in CRISIS_TYPES:
            raise ValueError(f"unknown crisis_type (allowed: {', '.join(CRISIS_TYPES)})")
        return value


class ResponderOut(BaseModel):
    responder_id: uuid.UUID
    name: str
    status: str
    eta_seconds: int | None


class SosOut(BaseModel):
    id: uuid.UUID
    status: str
    crisis_type: str | None
    severity_score: int | None
    description: str | None
    lat: float
    lon: float
    radius_m: int
    escalation_wave: int
    is_drill: bool
    created_at: datetime
    resolved_at: datetime | None
    notified_count: int
    responders: list[ResponderOut]


class RespondOut(BaseModel):
    response_id: uuid.UUID
    status: str


class ResolveRequest(BaseModel):
    outcome: str | None = Field(default=None, max_length=500)


class TimelineEventOut(BaseModel):
    event_type: str
    actor_id: uuid.UUID | None
    details: dict[str, Any]
    created_at: datetime
