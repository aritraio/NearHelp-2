"""Unit tests for the AI safety layers — these gate every PR in CI.

No database, no network: the guardrail regexes, citation validation, the
heuristic classifier, embedder determinism, and the RRF merge.
"""

import uuid

from app.services.ai import guardrails
from app.services.ai.classify import heuristic_classify, severity_radius
from app.services.ai.embedder import LexicalEmbedder, tokenize
from app.services.ai.retrieve import rrf_merge

# --- Guardrails ----------------------------------------------------------------


def test_dosage_blocked():
    assert "dosage" in guardrails.find_violations("give 500 mg of paracetamol")


def test_prescription_and_diagnosis_blocked():
    assert "prescription" in guardrails.find_violations("you should take 2 tablets now")
    assert "diagnosis" in guardrails.find_violations("my diagnosis is cardiac arrest")


def test_invasive_procedures_blocked():
    assert "invasive" in guardrails.find_violations("make an incision and drain the wound")


def test_clean_first_aid_text_passes():
    text = (
        "Push hard and fast in the center of the chest, about 5-6 cm deep, "
        "at 100-120 per minute. Call 108 for an ambulance."
    )
    assert guardrails.find_violations(text) == []


def test_adrenaline_autoinjector_guidance_allowed():
    # Injector use is part of anaphylaxis protocol — not a violation.
    text = "Help them use their adrenaline auto-injector: firm push into the outer thigh."
    assert "injection-advice" not in guardrails.find_violations(text)


def test_citations_required_and_validated():
    assert guardrails.has_citation("Begin CPR [P0]")
    assert not guardrails.has_citation("Begin CPR")
    assert guardrails.strip_citation("Begin CPR [P0]") == "Begin CPR"
    assert guardrails.extract_citations("do X [P0] then Y [P2]") == [0, 2]


def test_sanitize_steps_drops_uncited_and_out_of_range():
    steps = [
        "Valid step one [P0]",
        "No citation here",
        "Out of range [P9]",
        "Prescribe 300 mg amoxicillin [P1]",
    ]
    clean, all_valid = guardrails.sanitize_steps(steps, max_procedure_index=2)
    assert clean == ["Valid step one [P0]"]
    assert all_valid is False


# --- Heuristic classifier ---------------------------------------------------------


def test_heuristic_classifies_critical_medical():
    result = heuristic_classify("man collapsed, not breathing, no pulse")
    assert result.emergency_type == "medical"
    assert result.severity_score >= 80


def test_heuristic_classifies_each_crisis_family():
    cases = {
        "kitchen fire, flames everywhere": "fire",
        "smell of gas, cylinder leaking": "gas_leak",
        "two cars collided on the highway": "accident",
        "armed robbery in the shop": "security",
        "flood water entering the house": "disaster",
        "electrocuted by a live wire": "power",
    }
    for text, expected in cases.items():
        assert heuristic_classify(text).emergency_type == expected, text


def test_heuristic_defaults_to_other_without_signals():
    result = heuristic_classify("need help carrying groceries upstairs")
    assert result.emergency_type == "other"
    assert 20 <= result.severity_score < 80


def test_severity_radius_bands():
    assert severity_radius(96) == 3_000
    assert severity_radius(60) == 2_500
    assert severity_radius(30) == 1_500
    assert severity_radius(10) == 1_000


# --- Lexical embedder --------------------------------------------------------------


def test_lexical_embedder_deterministic_and_normalized():
    embedder = LexicalEmbedder(dim=384)
    a = embedder.embed(["cardiac arrest CPR"])[0]
    b = embedder.embed(["cardiac arrest CPR"])[0]
    assert a == b
    assert len(a) == 384
    assert abs(sum(v * v for v in a) - 1.0) < 1e-6


def test_lexical_embedder_similarity_ranks_relevant_text_higher():
    embedder = LexicalEmbedder(dim=384)
    query = embedder.embed(["snakebite leg swelling"])[0]
    snake = embedder.embed(["snakebite first response keep the limb still anti-venom"])[0]
    cpr = embedder.embed(["chest compressions rescue breaths AED"])[0]

    def cosine(x: list[float], y: list[float]) -> float:
        return sum(i * j for i, j in zip(x, y, strict=True))

    assert cosine(query, snake) > cosine(query, cpr)


def test_tokenize_drops_stopwords():
    assert "the" not in tokenize("The man is not breathing")
    assert tokenize("The man is not breathing") == ["man", "not", "breathing"]


# --- RRF merge ----------------------------------------------------------------------


def _row(procedure: str) -> dict:
    return {
        "source": "t",
        "procedure_name": procedure,
        "crisis_type": "medical",
        "step_number": 1,
        "chunk_text": "x",
    }


def test_rrf_merge_prefers_chunks_found_by_both_legs():
    both, vector_only, fts_only = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    merged = rrf_merge(
        vector_rows=[(both, _row("A")), (vector_only, _row("B"))],
        fts_rows=[(fts_only, _row("C")), (both, _row("A"))],
        crisis_type="medical",
        k=3,
    )
    assert merged[0].id == both
    assert {m.id for m in merged} == {both, vector_only, fts_only}


def test_rrf_merge_crisis_boost_reorders():
    target, neutral = uuid.uuid4(), uuid.uuid4()
    rows = {target: _row("A"), neutral: _row("B")}
    rows[target]["crisis_type"] = "fire"
    merged = rrf_merge(
        vector_rows=[(neutral, rows[neutral]), (target, rows[target])],
        fts_rows=[],
        crisis_type="fire",
        k=2,
    )
    assert merged[0].id == target
