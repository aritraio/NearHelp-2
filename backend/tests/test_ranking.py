"""Ranking unit tests — no DB, pure function (proposal §12.3 validation).

Scenario: cardiac arrest. Responder 1 is 200 m away, unskilled, trust 60.
Responder 2 is 800 m away, verified nurse + CPR, trust 85. With a 3 km radius
the skilled responder must rank decisively higher.
"""

import uuid

from app.core.config import get_settings
from app.services.geo import Candidate
from app.services.ranking import rank_candidates, top_n_for_severity

VICTIM = (22.5726, 88.3639)  # Salt Lake — reference point from proposal §12.3


def candidate(
    distance_m: float, skills: list[dict] | None = None, trust: float = 50.0
) -> Candidate:
    return Candidate(
        user_id=uuid.uuid4(),
        name="Responder",
        skills=skills or [],
        trust_score=trust,
        distance_m=distance_m,
    )


def test_proposal_123_nurse_800m_beats_unskilled_200m():
    unskilled_close = candidate(200, skills=[], trust=60.0)
    nurse_far = candidate(
        800,
        skills=[
            {"skill_type": "nurse", "verified": True},
            {"skill_type": "cpr_certified", "verified": True},
        ],
        trust=85.0,
    )
    ranked = rank_candidates([unskilled_close, nurse_far], "medical", radius_m=3000, top_n=5)

    assert ranked[0].candidate.user_id == nurse_far.user_id
    assert ranked[0].score > ranked[1].score

    # The unskilled responder matches the proposal's §12.3 arithmetic exactly
    # (0.4·(1−200/3000) + 0 + 0.25·0.60 = 0.523). The nurse scores 0.7158
    # rather than the proposal's illustrative 0.926: §12.3 assumed a full
    # skill match (S=1.2), while the implemented formula normalizes over the
    # 5-skill medical requirement set (2/5 + 0.2 verified = 0.6 → 0.35·0.6).
    # The claim under test — skilled beats merely-close — holds decisively.
    assert abs(ranked[1].score - 0.523) < 0.01
    assert abs(ranked[0].score - 0.7158) < 0.01
    assert ranked[0].score - ranked[1].score > 0.15


def test_distance_dominates_between_equal_skills():
    near = candidate(100, skills=[{"skill_type": "nurse", "verified": True}], trust=50.0)
    far = candidate(2000, skills=[{"skill_type": "nurse", "verified": True}], trust=50.0)
    ranked = rank_candidates([far, near], "medical", radius_m=3000, top_n=5)
    assert ranked[0].candidate.user_id == near.user_id


def test_verified_beats_unverified_same_distance():
    verified = candidate(500, skills=[{"skill_type": "nurse", "verified": True}], trust=50.0)
    unverified = candidate(500, skills=[{"skill_type": "nurse", "verified": False}], trust=50.0)
    ranked = rank_candidates([unverified, verified], "medical", radius_m=3000, top_n=5)
    assert ranked[0].candidate.user_id == verified.user_id


def test_trust_breaks_ties():
    high = candidate(500, trust=90.0)
    low = candidate(500, trust=10.0)
    ranked = rank_candidates([low, high], "other", radius_m=3000, top_n=5)
    assert ranked[0].candidate.user_id == high.user_id


def test_top_n_truncates():
    candidates = [candidate(i * 100) for i in range(20)]
    ranked = rank_candidates(candidates, "other", radius_m=3000, top_n=3)
    assert len(ranked) == 3


def test_irrelevant_skills_do_not_score():
    plumber = candidate(500, skills=[{"skill_type": "mechanic", "verified": True}], trust=50.0)
    ranked = rank_candidates([plumber], "medical", radius_m=3000, top_n=5)
    settings = get_settings()
    proximity = 1 - 500 / 3000
    expected = settings.ranking_w1_distance * proximity + settings.ranking_w3_trust * 0.5
    assert abs(ranked[0].score - round(expected, 4)) < 1e-6


def test_severity_bands_map_top_n():
    assert top_n_for_severity(96) == 200
    assert top_n_for_severity(80) == 200
    assert top_n_for_severity(79) == 10
    assert top_n_for_severity(50) == 10
    assert top_n_for_severity(49) == 5
    assert top_n_for_severity(20) == 5
    assert top_n_for_severity(19) == 3
    assert top_n_for_severity(0) == 3
    assert top_n_for_severity(None) == 5
