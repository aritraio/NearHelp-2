"""initial schema: users, sos_events, responses, kb_chunks + geo/vector indexes

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-15

Phase 0 (todos.md §0.2): users, sos_events, responses are required by the SOS
engine; kb_chunks ships in the same migration so the HNSW index acceptance
criterion is met at `alembic upgrade head` time (BLUEPRINT.md §3).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql as pgdialect

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # One engine, three roles: relational + geospatial + vectors (ADR-2, ADR-3).
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column(
            "languages", pgdialect.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False
        ),
        sa.Column(
            "skills", pgdialect.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False
        ),
        sa.Column("trust_score", sa.Float(), server_default=sa.text("50.0"), nullable=False),
        sa.Column(
            "location",
            Geography(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=True,
        ),
        sa.Column("fcm_token", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index("idx_users_location", "users", ["location"], postgresql_using="gist")

    op.create_table(
        "sos_events",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "broadcaster_id",
            sa.Uuid(),
            sa.ForeignKey(
                "users.id", ondelete="CASCADE", name=op.f("fk_sos_events_broadcaster_id_users")
            ),
            nullable=False,
        ),
        sa.Column("crisis_type", sa.String(length=50), nullable=True),
        sa.Column("sub_type", sa.String(length=50), nullable=True),
        sa.Column("severity_score", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "location",
            Geography(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column(
            "status", sa.String(length=20), server_default=sa.text("'pending'"), nullable=False
        ),
        sa.Column("is_anonymous", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_drill", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("radius_m", sa.Integer(), server_default=sa.text("2000"), nullable=False),
        sa.Column("escalation_wave", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_escalated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sos_events")),
        sa.UniqueConstraint("idempotency_key", name="uq_sos_events_idempotency_key"),
    )
    op.create_index("idx_sos_location", "sos_events", ["location"], postgresql_using="gist")
    op.create_index("idx_sos_status_created", "sos_events", ["status", "created_at"])

    op.create_table(
        "responses",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "sos_event_id",
            sa.Uuid(),
            sa.ForeignKey(
                "sos_events.id",
                ondelete="CASCADE",
                name=op.f("fk_responses_sos_event_id_sos_events"),
            ),
            nullable=False,
        ),
        sa.Column(
            "responder_id",
            sa.Uuid(),
            sa.ForeignKey(
                "users.id", ondelete="CASCADE", name=op.f("fk_responses_responder_id_users")
            ),
            nullable=False,
        ),
        sa.Column(
            "status", sa.String(length=20), server_default=sa.text("'notified'"), nullable=False
        ),
        sa.Column("eta_seconds", sa.Integer(), nullable=True),
        sa.Column("feedback_score", sa.SmallInteger(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_responses")),
        sa.UniqueConstraint("sos_event_id", "responder_id", name="uq_responses_event_responder"),
    )
    op.create_index("idx_responses_event", "responses", ["sos_event_id"])

    op.create_table(
        "kb_chunks",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("source", sa.String(length=200), nullable=False),
        sa.Column("procedure_name", sa.String(length=200), nullable=False),
        sa.Column("crisis_type", sa.String(length=50), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(384), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_kb_chunks")),
    )
    # HNSW needs raw SQL (op.create_index can't express the operator class).
    op.execute(
        "CREATE INDEX idx_kb_embedding ON kb_chunks USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_kb_embedding")
    op.drop_table("kb_chunks")
    op.drop_index("idx_responses_event", table_name="responses")
    op.drop_table("responses")
    op.drop_index("idx_sos_status_created", table_name="sos_events")
    op.drop_index("idx_sos_location", table_name="sos_events")
    op.drop_table("sos_events")
    op.drop_index("idx_users_location", table_name="users")
    op.drop_table("users")
