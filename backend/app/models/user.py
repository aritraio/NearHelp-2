"""User model — identity, skills, trust, live location (BLUEPRINT.md §3).

Privacy rule (Architecture.md §9): `location` is written only while the user
participates in an active SOS event and is nulled by the retention job after.
"""

from typing import Any

from geoalchemy2 import Geography
from sqlalchemy import Boolean, Float, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UuidPkMixin


class User(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (Index("idx_users_location", "location", postgresql_using="gist"),)

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # Nullable: seeded test users and (later) OAuth-only accounts may not have one.
    password_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ISO 639-1 codes, e.g. ["bn", "en"]
    languages: Mapped[list[Any]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    # [{skill_type, verified, certificate_url?}] — proposal Module 3 catalog
    skills: Mapped[list[Any]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), nullable=False
    )
    trust_score: Mapped[float] = mapped_column(Float, server_default=text("50.0"), nullable=False)

    # GEOGRAPHY(Point, 4326) — meters-based ST_DWithin/ST_Distance for free.
    location: Mapped[Any] = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=True
    )

    # FCM tokens live in user_devices (multi-device, migration 0002).
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), nullable=False)
