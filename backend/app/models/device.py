"""Per-device FCM registrations (Architecture.md §8 — token hygiene).

One user may own several devices; each (user, device) keeps its current FCM
token. Replaces the Phase 0 single `users.fcm_token` column (migration 0002).
"""

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UuidPkMixin


class UserDevice(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "user_devices"
    __table_args__ = (UniqueConstraint("user_id", "device_id", name="uq_user_devices_user_device"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Stable client-generated identifier (UUID stored on first launch).
    device_id: Mapped[str] = mapped_column(String(100), nullable=False)
    # Current FCM registration token; rotated by re-POSTing the same device_id.
    fcm_token: Mapped[str] = mapped_column(String(255), nullable=False)
    # Metadata for the readiness indicator / debugging, e.g. {"model": "Pixel 8"}.
    device_meta: Mapped[dict | None] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), nullable=True
    )
