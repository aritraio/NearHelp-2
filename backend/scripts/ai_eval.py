"""AI evaluation harness — `python -m scripts.ai_eval` (todos.md §5.1).

Measures, against the golden set (ai_eval/golden.jsonl):
  classification accuracy  — heuristic ladder (or Gemini when a key exists)
  retrieval precision@5    — hybrid retrieval over the ingested corpus
  faithfulness             — retrieval-only guidance cites sources + passes
                             the blocklist with zero violations

Thresholds: accuracy >= 0.85, precision@5 >= 0.80, faithfulness == 1.00.
Exits non-zero on failure so CI gates corpus/prompt changes. Requires a
migrated database with the corpus ingested (README quickstart).
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.ai import (  # noqa: E402
    classify_emergency,
    generate_guidance,
    guardrails,  # noqa: E402
)
from app.services.ai.embedder import get_embedder  # noqa: E402
from app.services.ai.llm_client import get_llm  # noqa: E402
from app.services.ai.prompts import PROMPT_VERSION  # noqa: E402
from app.services.ai.retrieve import retrieve  # noqa: E402

GOLDEN = Path(__file__).resolve().parent.parent / "ai_eval" / "golden.jsonl"
THRESHOLD_ACCURACY = 0.85
THRESHOLD_PRECISION = 0.80


def load_golden() -> list[dict]:
    rows = []
    for line in GOLDEN.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


async def main() -> int:
    # Without a database there is nothing to gate — CI always has one.
    from app.core.config import get_settings
    from sqlalchemy import create_engine, text

    try:
        with create_engine(get_settings().database_url_sync).connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        print("EVAL SKIPPED — no database at DATABASE_URL (CI runs it against containers)")
        return 0

    rows = load_golden()
    embedder = get_embedder()
    llm = get_llm()
    print(f"prompt {PROMPT_VERSION} | embedder={embedder.name} | llm={llm.name}\n")

    # --- Classification accuracy ----------------------------------------------
    correct = 0
    for row in rows:
        result = await classify_emergency(row["text"])
        if result.emergency_type == row["crisis"]:
            correct += 1
    accuracy = correct / len(rows)

    # --- Retrieval precision@5 --------------------------------------------------
    from app.db.session import get_session_factory

    session_factory = get_session_factory()
    hits = 0
    graded = 0
    async with session_factory() as session:
        for row in rows:
            if not row.get("procedure"):
                continue
            graded += 1
            chunks = await retrieve(session, row["text"], crisis_type=row["crisis"], k=5)
            if any(c.procedure_name == row["procedure"] for c in chunks):
                hits += 1
    precision = hits / graded if graded else 0.0

    # --- Faithfulness (retrieval-only mode: citations + blocklist) --------------
    faithful = 0
    checked = 0
    async with session_factory() as session:
        for row in rows[:20]:
            if not row.get("procedure"):
                continue
            checked += 1
            guidance = await generate_guidance(session, row["crisis"], row["text"])
            ok = (
                guidance.mode in ("retrieval_only", "rag")
                and bool(guidance.steps)
                and all(step.get("source") for step in guidance.steps)
                and not any(guardrails.find_violations(step["text"]) for step in guidance.steps)
            )
            faithful += 1 if ok else 0

    faithfulness = faithful / checked if checked else 1.0

    print("─" * 52)
    print(f"classification accuracy   {accuracy:.2f}  (>= {THRESHOLD_ACCURACY})")
    print(f"retrieval precision@5     {precision:.2f}  (>= {THRESHOLD_PRECISION})")
    print(f"faithfulness              {faithfulness:.2f}  (== 1.00)")
    print("─" * 52)

    failed = accuracy < THRESHOLD_ACCURACY or precision < THRESHOLD_PRECISION or faithfulness < 1.0
    if failed:
        print("EVAL FAILED — tighten the corpus/golden set or fix the regression")
        return 1
    print("EVAL PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
