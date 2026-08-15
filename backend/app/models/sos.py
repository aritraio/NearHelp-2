"""SOS events and responder participation (BLUEPRINT.md §3).

The status state machine (PENDING → ACTIVE → RESOLVED | EXPIRED) and the
escalation_wave counter are owned by the Event/Escalation services — the
columns exist here so the durable tick can scan them (Architecture.md §5).
"""

import uuid
from datetime import datetime
from typing import Any

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UuidPkMixin


class SosEvent(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "sos_events"
    __table_args__ = (
        Index("idx_sos_location", "location", postgresql_using="gist"),
        Index("idx_sos_status_created", "status", "created_at"),
        UniqueConstraint("idempotency_key", name="uq_sos_events_idempotency_key"),
    )

    broadcaster_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    crisis_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sub_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    severity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    location: Mapped[Any] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )

    # pending | active | resolved | expired
    status: Mapped[str] = mapped_column(
        String(20), server_default=text("'pending'"), nullable=False
    )
    is_anonymous: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), nullable=False
    )
    is_drill: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)

    radius_m: Mapped[int] = mapped_column(Integer, server_default=text("2000"), nullable=False)
    escalation_wave: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
    last_escalated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Client-generated; Redis guards fast retries, this unique index is the backstop.
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)


class Response(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "responses"
    __table_args__ = (
        UniqueConstraint("sos_event_id", "responder_id", name="uq_responses_event_responder"),
        Index("idx_responses_event", "sos_event_id"),
    )

    sos_event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sos_events.id", ondelete="CASCADE"), nullable=False
    )
    responder_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # notified | acked | accepted | arrived | completed | undelivered
    status: Mapped[str] = mapped_column(
        String(20), server_default=text("'notified'"), nullable=False
    )
    eta_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
