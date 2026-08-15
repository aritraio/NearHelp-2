"""Ingest the knowledge base into kb_chunks (embeddings included).

Idempotent by outcome: every run wipes and rebuilds the corpus from the JSON,
so the table always mirrors the file exactly. Embeddings use the configured
embedder (auto: MiniLM → Gemini → lexical; see app/services/ai/embedder.py).

    python -m scripts.ingest_kb [--file ../knowledge_base/protocols.json]
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from app.models.kb import KbChunk  # noqa: E402
from app.services.ai.embedder import get_embedder  # noqa: E402
from sqlalchemy import delete, text  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

DEFAULT_CORPUS = Path(__file__).resolve().parent.parent.parent / "knowledge_base" / "protocols.json"


async def ingest(corpus_path: Path) -> dict:
    data = json.loads(corpus_path.read_text())
    embedder = get_embedder()

    rows: list[dict] = []
    for procedure in data["procedures"]:
        for step_number, step_text in enumerate(procedure["steps"], start=1):
            rows.append(
                {
                    "source": procedure["source"],
                    "procedure_name": procedure["procedure_name"],
                    "crisis_type": procedure["crisis_type"],
                    "step_number": step_number,
                    "text": step_text,
                    # Embed step + procedure context so "chest pain" finds CPR.
                    "embed_text": (
                        f"{procedure['procedure_name']}. {procedure['crisis_type']}. {step_text}"
                    ),
                }
            )

    engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory() as session:
            wiped = (await session.execute(delete(KbChunk).where(True))).rowcount
            for start in range(0, len(rows), 64):
                batch = rows[start : start + 64]
                vectors = embedder.embed([row["embed_text"] for row in batch])
                for row, vector in zip(batch, vectors, strict=True):
                    session.add(
                        KbChunk(
                            source=row["source"],
                            procedure_name=row["procedure_name"],
                            crisis_type=row["crisis_type"],
                            step_number=row["step_number"],
                            text=row["text"],
                            embedding=vector,
                        )
                    )
            await session.commit()
            count = (await session.execute(text("SELECT COUNT(*) FROM kb_chunks"))).scalar_one()
    finally:
        await engine.dispose()

    return {
        "procedures": len(data["procedures"]),
        "chunks": len(rows),
        "stored": count,
        "replaced": wiped or 0,
        "embedder": embedder.name,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT_CORPUS)
    args = parser.parse_args()
    summary = asyncio.run(ingest(args.file))
    print(json.dumps(summary, indent=2))
    assert summary["chunks"] == summary["stored"], "ingestion count mismatch"
    print(f"\nINGEST OK — {summary['stored']} chunks via {summary['embedder']} embedder")


if __name__ == "__main__":
    main()
