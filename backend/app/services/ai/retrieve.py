"""Hybrid retrieval — pgvector cosine + Postgres full-text, merged by RRF.

Medical protocol text is keyword-shaped ("unresponsive", "compressions"),
so lexical search earns its seat next to vectors (tech-stack.md §5.2). The
merge is Reciprocal Rank Fusion: score = Σ 1/(60 + rank), plus a small boost
when the chunk's crisis_type matches the query context.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.embedder import get_embedder

RRF_K = 60
CRISIS_MATCH_BOOST = 0.02


@dataclass(frozen=True)
class RetrievedChunk:
    id: uuid.UUID
    source: str
    procedure_name: str
    crisis_type: str
    step_number: int | None
    chunk_text: str
    score: float


async def retrieve(
    session: AsyncSession,
    query: str,
    crisis_type: str | None = None,
    k: int = 5,
) -> list[RetrievedChunk]:
    """Top-k hybrid retrieval over kb_chunks."""
    embedder = get_embedder()
    query_vector = embedder.embed([query])[0]
    vector_literal = "[" + ", ".join(f"{v:.6f}" for v in query_vector) + "]"

    vector_sql = text("""
        SELECT id, source, procedure_name, crisis_type, step_number, chunk_text,
               1 - (embedding <=> CAST(:vec AS vector)) AS similarity
        FROM kb_chunks
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> CAST(:vec AS vector)
        LIMIT :fetch
    """)
    fts_sql = text("""
        SELECT id, source, procedure_name, crisis_type, step_number, chunk_text,
               ts_rank(to_tsvector('english', chunk_text),
                       websearch_to_tsquery('english', :query)) AS rank
        FROM kb_chunks
        WHERE to_tsvector('english', chunk_text) @@ websearch_to_tsquery('english', :query)
        ORDER BY rank DESC
        LIMIT :fetch
    """)

    fetch = max(k * 3, 15)
    vector_rows = (
        await session.execute(vector_sql, {"vec": vector_literal, "fetch": fetch})
    ).mappings()
    fts_rows = (await session.execute(fts_sql, {"query": query, "fetch": fetch})).mappings()

    return rrf_merge(
        vector_rows=[(row["id"], dict(row)) for row in vector_rows],
        fts_rows=[(row["id"], dict(row)) for row in fts_rows],
        crisis_type=crisis_type,
        k=k,
    )


def rrf_merge(
    vector_rows: list[tuple[uuid.UUID, dict]],
    fts_rows: list[tuple[uuid.UUID, dict]],
    crisis_type: str | None,
    k: int,
) -> list[RetrievedChunk]:
    """Pure merge — unit-tested; both lists must be relevance-ordered."""
    scores: dict[uuid.UUID, float] = {}
    rows_by_id: dict[uuid.UUID, dict] = {}

    for rank, (chunk_id, row) in enumerate(vector_rows):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank)
        rows_by_id[chunk_id] = row
    for rank, (chunk_id, row) in enumerate(fts_rows):
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank)
        rows_by_id.setdefault(chunk_id, row)

    if crisis_type:
        for chunk_id, row in rows_by_id.items():
            if row.get("crisis_type") == crisis_type:
                scores[chunk_id] = scores.get(chunk_id, 0.0) + CRISIS_MATCH_BOOST

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:k]
    return [
        RetrievedChunk(
            id=chunk_id,
            source=row["source"],
            procedure_name=row["procedure_name"],
            crisis_type=row["crisis_type"],
            step_number=row["step_number"],
            chunk_text=row["chunk_text"],
            score=round(score, 5),
        )
        for chunk_id, score in ranked
        for row in [rows_by_id[chunk_id]]
    ]
