"""Integration: the AI pipeline against a real database + corpus.

Covers the Phase 5 ACs:
  - ingest → "cardiac arrest" retrieval returns CPR steps in top-5
  - fallback ladder: with no Gemini key configured, classification returns
    heuristic results and guidance serves retrieval-only — and the SOS path
    still works end-to-end within its latency budget.
"""

import asyncio
import time
import uuid
from pathlib import Path

from tests.conftest import auth_headers, register_user, set_location

VICTIM = {"lat": 22.5726, "lon": 88.3639}
CORPUS = Path(__file__).resolve().parent.parent.parent / "knowledge_base" / "protocols.json"


def _ingest() -> dict:
    from scripts.ingest_kb import ingest

    return asyncio.run(ingest(CORPUS))


def test_ingest_and_retrieval_ac(db_available, db_clean):
    if not db_available:
        import pytest

        pytest.skip("Postgres not reachable")
    summary = _ingest()
    assert summary["stored"] == summary["chunks"]
    assert summary["chunks"] > 50  # 17 procedures × steps
    assert summary["embedder"] == "lexical"  # no MiniLM/Gemini configured here

    from app.db.session import get_session_factory
    from app.services.ai.retrieve import retrieve

    async def check() -> None:
        factory = get_session_factory()
        async with factory() as session:
            chunks = await retrieve(session, "cardiac arrest, man not breathing", k=5)
            assert chunks, "retrieval returned nothing"
            assert any("CPR" in c.procedure_name for c in chunks), [
                c.procedure_name for c in chunks
            ]

    asyncio.run(check())


def test_fallback_ladder_guidance_served_without_llm(client, db_clean, monkeypatch):
    """The Phase 5 AC: key invalidated → retrieval-only guidance, SOS path fine."""
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "llm_provider", "none")
    monkeypatch.setattr(get_settings(), "embedder", "lexical")
    _ingest()

    victim = register_user(client, email="ai-victim@nearhelp.dev")
    set_location(client, victim["access_token"], VICTIM["lat"], VICTIM["lon"])

    started = time.perf_counter()
    created = client.post(
        "/api/sos/create",
        headers={**auth_headers(victim["access_token"]), "Idempotency-Key": uuid.uuid4().hex},
        json={
            "lat": VICTIM["lat"],
            "lon": VICTIM["lon"],
            "description": "man collapsed, not breathing",
        },
    )
    create_ms = (time.perf_counter() - started) * 1000
    assert created.status_code == 201
    # Alerts must not wait on AI: create stays in its latency budget.
    assert create_ms < 2_000, f"create took {create_ms:.0f} ms"

    sos_id = created.json()["id"]

    # Run the AI job directly (the worker isn't running inside tests).
    from app.worker import ai_pipeline

    result = asyncio.run(ai_pipeline({}, sos_id))
    assert result["classification"] == "heuristic"
    assert result["guidance_mode"] == "retrieval_only"

    guidance = client.get(
        f"/api/sos/{sos_id}/guidance", headers=auth_headers(victim["access_token"])
    )
    assert guidance.status_code == 200
    body = guidance.json()
    assert body["mode"] == "retrieval_only"
    assert body["steps"], "no steps served"
    assert all(step["source"] for step in body["steps"])
    assert "108" in body["disclaimer"]

    # Classification updated the event; the timeline tells the AI story.
    event = client.get(f"/api/sos/{sos_id}", headers=auth_headers(victim["access_token"])).json()
    assert event["crisis_type"] == "medical"
    assert event["severity_score"] >= 80
    timeline = client.get(
        f"/api/sos/{sos_id}/timeline", headers=auth_headers(victim["access_token"])
    ).json()
    types = [item["event_type"] for item in timeline]
    assert "ai_classified" in types
    assert "ai_guidance_ready" in types
