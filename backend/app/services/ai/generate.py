"""Guidance generation — the RAG pipeline with its fallback ladder.

Ladder (improvements.md §1.2, tested as a Phase 5 AC):
  1. Gemini with citation-enforcing prompt + schema retry
  2. Retrieval-only: top protocol steps VERBATIM with citations (no LLM)
  3. Fallback line: "wait for professional help / call 108-112"

Every step that survives must cite a retrieved procedure and pass the
blocklist — otherwise it is dropped, and if nothing survives we fall through
to the fallback line. Output is never free-form advice.
"""

import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai import guardrails
from app.services.ai.llm_client import get_llm
from app.services.ai.prompts import (
    GUIDANCE_SYSTEM,
    GUIDANCE_USER_TEMPLATE,
    PROMPT_VERSION,
    format_procedures,
)
from app.services.ai.retrieve import RetrievedChunk, retrieve

FALLBACK_LINE = (
    "Please wait for professional medical help. Call 108 or 112 now and stay with the person."
)

GUIDANCE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "steps": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": ["steps"],
}


@dataclass
class Guidance:
    mode: str  # rag | retrieval_only | fallback
    steps: list[dict[str, str]] = field(default_factory=list)  # {text, source}
    summary: str = ""
    retrieved_refs: list[dict[str, str]] = field(default_factory=list)
    prompt_version: str = PROMPT_VERSION
    latency_ms: int = 0

    def as_payload(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "steps": self.steps,
            "summary": self.summary,
            "retrieved_refs": self.retrieved_refs,
            "prompt_version": self.prompt_version,
        }


def _ref(chunk: RetrievedChunk, index: int) -> dict[str, str]:
    return {
        "ref": f"[P{index}]",
        "source": chunk.source,
        "procedure": chunk.procedure_name,
        **({"step": str(chunk.step_number)} if chunk.step_number else {}),
    }


def _ref_label(chunk: RetrievedChunk) -> str:
    step = f", step {chunk.step_number}" if chunk.step_number else ""
    return f"{chunk.source} — {chunk.procedure_name}{step}"


async def generate_guidance(
    session: AsyncSession,
    crisis_type: str | None,
    description: str | None,
) -> Guidance:
    started = time.perf_counter()
    query = (crisis_type or "") + " " + (description or "")
    query = query.strip() or crisis_type or "emergency"

    chunks = await retrieve(session, query, crisis_type=crisis_type, k=5)
    if not chunks:
        return _finish(Guidance(mode="fallback", summary=FALLBACK_LINE, steps=[]), started)

    refs = [_ref(chunk, index) for index, chunk in enumerate(chunks)]

    # --- Rung 1: LLM generation over the retrieved procedures -----------------
    llm = get_llm()
    if llm.name != "disabled":
        raw = await llm.generate_json(
            system=GUIDANCE_SYSTEM,
            user=GUIDANCE_USER_TEMPLATE.format(
                procedures=format_procedures(chunks),
                crisis_type=crisis_type or "unknown",
                description=description or "not provided",
            ),
            schema=GUIDANCE_SCHEMA,
        )
        if raw and isinstance(raw.get("steps"), list):
            steps_raw = [str(s) for s in raw["steps"]][:8]
            clean, _all_valid = guardrails.sanitize_steps(steps_raw, len(chunks))
            if clean:
                guidance = Guidance(
                    mode="rag",
                    summary=str(raw.get("summary", ""))[:300],
                    retrieved_refs=refs,
                )
                for step_text in clean:
                    citation = guardrails.extract_citations(step_text)[0]
                    guidance.steps.append(
                        {
                            "text": guardrails.strip_citation(step_text),
                            "source": _ref_label(chunks[citation]),
                        }
                    )
                return _finish(guidance, started)
        # LLM failed OR nothing survived sanitization → rung 2.

    # --- Rung 2: retrieval-only — verbatim protocol steps with citations -------
    guidance = Guidance(mode="retrieval_only", summary="", retrieved_refs=refs)
    for chunk in chunks[:8]:
        guidance.steps.append({"text": chunk.chunk_text, "source": _ref_label(chunk)})
    guidance.summary = f"Verified protocol steps ({guidance.steps[0]['source'].split(' — ')[0]})."
    return _finish(guidance, started)


def _finish(guidance: Guidance, started: float) -> Guidance:
    guidance.latency_ms = int((time.perf_counter() - started) * 1000)
    return guidance
