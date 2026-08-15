"""phase 1: skill_verifications, user_devices; drop users.fcm_token

Revision ID: 0002_phase1_auth
Revises: 0001_initial
Create Date: 2026-08-15

- skill_verifications: skill claims with certificate proof awaiting admin review.
- user_devices: one row per (user, device) holding its current FCM token —
  replaces the single users.fcm_token column so registration is multi-device
  aware (Architecture.md §8).
- users.password_hash: bcrypt hash; nullable so seeded/OAuth-only users work.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgdialect

revision: str = "0002_phase1_auth"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "skill_verifications",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey(
                "users.id", ondelete="CASCADE", name=op.f("fk_skill_verifications_user_id_users")
            ),
            nullable=False,
        ),
        sa.Column("skill_type", sa.String(length=50), nullable=False),
        sa.Column("certificate_path", sa.String(length=500), nullable=True),
        sa.Column(
            "status", sa.String(length=20), server_default=sa.text("'pending'"), nullable=False
        ),
        sa.Column(
            "reviewed_by",
            sa.Uuid(),
            sa.ForeignKey(
                "users.id",
                ondelete="SET NULL",
                name=op.f("fk_skill_verifications_reviewed_by_users"),
            ),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_skill_verifications")),
    )
    op.create_index("idx_skill_verif_status", "skill_verifications", ["status", "created_at"])

    op.create_table(
        "user_devices",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey(
                "users.id", ondelete="CASCADE", name=op.f("fk_user_devices_user_id_users")
            ),
            nullable=False,
        ),
        sa.Column("device_id", sa.String(length=100), nullable=False),
        sa.Column("fcm_token", sa.String(length=255), nullable=False),
        sa.Column(
            "device_meta", pgdialect.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_devices")),
        sa.UniqueConstraint("user_id", "device_id", name="uq_user_devices_user_device"),
    )

    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=128), nullable=True),
    )
    op.drop_column("users", "fcm_token")


def downgrade() -> None:
    op.drop_column("users", "password_hash")
    op.add_column(
        "users",
        sa.Column("fcm_token", sa.String(length=255), nullable=True),
    )
    op.drop_table("user_devices")
    op.drop_index("idx_skill_verif_status", table_name="skill_verifications")
    op.drop_table("skill_verifications")
