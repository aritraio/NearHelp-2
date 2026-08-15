"""phase 2: timeline_events (audit trail for the SOS state machine)

Revision ID: 0003_phase2_sos
Revises: 0002_phase1_auth
Create Date: 2026-08-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgdialect

revision: str = "0003_phase2_sos"
down_revision: str | None = "0002_phase1_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "timeline_events",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "sos_event_id",
            sa.Uuid(),
            sa.ForeignKey(
                "sos_events.id",
                ondelete="CASCADE",
                name=op.f("fk_timeline_events_sos_event_id_sos_events"),
            ),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column(
            "actor_id",
            sa.Uuid(),
            sa.ForeignKey(
                "users.id", ondelete="SET NULL", name=op.f("fk_timeline_events_actor_id_users")
            ),
            nullable=True,
        ),
        sa.Column(
            "details", pgdialect.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("clock_timestamp()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_timeline_events")),
    )
    op.create_index("idx_timeline_event", "timeline_events", ["sos_event_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_timeline_event", table_name="timeline_events")
    op.drop_table("timeline_events")
