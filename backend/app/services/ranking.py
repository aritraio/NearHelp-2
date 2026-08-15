"""Responder ranking — a pure function over geo candidates (proposal §12).

score = w1 · (1 − distance/radius)          proximity
      + w2 · skillMatch (+0.2 verified)     relevance
      + w3 · trust/100                      reliability

Weights come from Settings so the Phase 7 ablation study can sweep them without
redeploys. No I/O happens here: unit tests cover the §12.3 validation scenario.
"""

from dataclasses import dataclass

from app.core.config import get_settings
from app.core.constants import SKILLS_BY_CRISIS, TOP_N_BY_SEVERITY, TOP_N_DEFAULT
from app.services.geo import Candidate

VERIFIED_BONUS = 0.2
SKILL_MATCH_CAP = 1.2  # 1.0 match + 0.2 verified bonus


@dataclass(frozen=True)
class Ranked:
    candidate: Candidate
    score: float


def top_n_for_severity(severity: int | None) -> int:
    if severity is None:
        return TOP_N_DEFAULT
    for threshold, n in TOP_N_BY_SEVERITY:
        if severity >= threshold:
            return n
    return TOP_N_DEFAULT


def _skill_score(skills: list[dict], required: list[str]) -> float:
    """|user ∩ required| / |required|, +0.2 when any matched skill is verified."""
    if not required:
        return 0.0
    required_set = set(required)
    matched = [s for s in skills if s.get("skill_type") in required_set]
    base = len(matched) / len(required)
    bonus = VERIFIED_BONUS if any(s.get("verified") for s in matched) else 0.0
    return min(base + bonus, SKILL_MATCH_CAP)


def rank_candidates(
    candidates: list[Candidate],
    crisis_type: str | None,
    radius_m: int,
    top_n: int,
) -> list[Ranked]:
    settings = get_settings()
    required = SKILLS_BY_CRISIS.get(crisis_type or "other", [])

    ranked: list[Ranked] = []
    for candidate in candidates:
        proximity = max(0.0, 1.0 - min(candidate.distance_m / radius_m, 1.0))
        skill = _skill_score(candidate.skills, required)
        trust = candidate.trust_score / 100.0
        score = (
            settings.ranking_w1_distance * proximity
            + settings.ranking_w2_skill * skill
            + settings.ranking_w3_trust * trust
        )
        ranked.append(Ranked(candidate=candidate, score=round(score, 4)))

    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked[:top_n]
