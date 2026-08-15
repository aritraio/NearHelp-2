"""Chat messages — persisted per event, pruned 30 days after resolution."""

import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UuidPkMixin


class Message(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (Index("idx_messages_event", "sos_event_id", "created_at"),)

    sos_event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sos_events.id", ondelete="CASCADE"), nullable=False
    )
    # SET NULL: the audit trail survives even if the account is deleted.
    sender_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # NOTE: the column is named `text`, so sqlalchemy.text is aliased above —
    # a same-named attribute would shadow it inside the class body.
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # ISO 639-1; translations are generated on the recipient side (Phase 5).
    language: Mapped[str] = mapped_column(String(8), server_default=sa_text("'en'"), nullable=False)
