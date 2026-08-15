"""phase 4: messages table (event chat persistence)

Revision ID: 0004_phase4_realtime
Revises: 0003_phase2_sos
Create Date: 2026-08-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_phase4_realtime"
down_revision: str | None = "0003_phase2_sos"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "sos_event_id",
            sa.Uuid(),
            sa.ForeignKey(
                "sos_events.id",
                ondelete="CASCADE",
                name=op.f("fk_messages_sos_event_id_sos_events"),
            ),
            nullable=False,
        ),
        sa.Column(
            "sender_id",
            sa.Uuid(),
            sa.ForeignKey(
                "users.id", ondelete="SET NULL", name=op.f("fk_messages_sender_id_users")
            ),
            nullable=True,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=8), server_default=sa.text("'en'"), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
    )
    op.create_index("idx_messages_event", "messages", ["sos_event_id", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_messages_event", table_name="messages")
    op.drop_table("messages")
