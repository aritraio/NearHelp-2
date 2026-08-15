"""AI outputs — the audit trail for every generated result (Phase 5).

Stores what was generated, how (mode), how fast (latency), with which prompt
version and which retrieved chunks — the defense's AI-latency data source and
the review trail for the hallucination safeguards.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UuidPkMixin


class AiOutput(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "ai_outputs"
    __table_args__ = (Index("idx_ai_outputs_event", "sos_event_id", "kind"),)

    sos_event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sos_events.id", ondelete="CASCADE"), nullable=True
    )
    # classification | severity | guidance | summary
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    # gemini | heuristic | retrieval_only | fallback
    mode: Mapped[str] = mapped_column(String(30), nullable=False)
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )
    retrieved_refs: Mapped[list[Any]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.clock_timestamp(), nullable=False
    )
