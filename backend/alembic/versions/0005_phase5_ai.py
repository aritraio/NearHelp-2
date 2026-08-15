"""phase 5: ai_outputs (AI audit trail: mode, prompt version, refs, latency)

Revision ID: 0005_phase5_ai
Revises: 0004_phase4_realtime
Create Date: 2026-08-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgdialect

revision: str = "0005_phase5_ai"
down_revision: str | None = "0004_phase4_realtime"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_outputs",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "sos_event_id",
            sa.Uuid(),
            sa.ForeignKey(
                "sos_events.id",
                ondelete="CASCADE",
                name=op.f("fk_ai_outputs_sos_event_id_sos_events"),
            ),
            nullable=True,
        ),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("mode", sa.String(length=30), nullable=False),
        sa.Column("prompt_version", sa.String(length=20), nullable=True),
        sa.Column(
            "payload", pgdialect.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column(
            "retrieved_refs",
            pgdialect.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("latency_ms", sa.Integer(), server_default=sa.text("0"), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_outputs")),
    )
    op.create_index("idx_ai_outputs_event", "ai_outputs", ["sos_event_id", "kind"])


def downgrade() -> None:
    op.drop_index("idx_ai_outputs_event", table_name="ai_outputs")
    op.drop_table("ai_outputs")
