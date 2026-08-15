"""Skill verification queue rows — proposal Module 3, minimal Phase 1 version.

Users claim a skill with optional certificate proof; admins approve/reject in
Phase 6. Approval also bumps trust (+5, Trust Service).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UuidPkMixin


class SkillVerification(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "skill_verifications"
    __table_args__ = (Index("idx_skill_verif_status", "status", "created_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    skill_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relative storage key (filename only) — resolved against Settings.certificate_dir.
    certificate_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # pending | approved | rejected
    status: Mapped[str] = mapped_column(
        String(20), server_default=text("'pending'"), nullable=False
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
