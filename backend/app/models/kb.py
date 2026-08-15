"""RAG knowledge-base chunks — the pgvector side of Postgres (ADR-3).

Chunked at procedure level (source, procedure, step) per proposal Module 11.
`embedding` is nullable so the corpus can be ingested text-first in Phase 5
and backfilled by the embedding script without touching the schema.
"""

from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UuidPkMixin

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension


class KbChunk(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "kb_chunks"

    source: Mapped[str] = mapped_column(String(200), nullable=False)
    procedure_name: Mapped[str] = mapped_column(String(200), nullable=False)
    crisis_type: Mapped[str] = mapped_column(String(50), nullable=False)
    step_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # The HNSW (vector_cosine_ops) index is created in migration 0001.
    embedding: Mapped[Any] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
