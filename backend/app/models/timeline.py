"""Timeline events — the auditable record of everything that happened.

Every state transition on the SOS path appends a row here (Architecture.md §2:
"state machines, not flags"). `details` carries structured context
(geo/rank timings, notification counts, escalation radii).

Note: updated_at exists via the mixin but is meaningless for an append-only
table; only created_at matters.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UuidPkMixin


class TimelineEvent(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "timeline_events"
    __table_args__ = (Index("idx_timeline_event", "sos_event_id", "created_at"),)

    # clock_timestamp() (not now()): multiple events written in one transaction
    # still get distinct, monotonically increasing timestamps — the audit trail
    # keeps a strict order.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )

    sos_event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sos_events.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    details: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
