"""Emergency classification + severity — one LLM call, safe fallback.

Ladder (Architecture.md §6): Gemini structured output (1 retry) → heuristic
keyword classifier → conservative defaults (type=other, severity 50). The
heuristic layer doubles as the offline/CI path, so the eval harness measures
both. Severity drives the responder radius (proposal §5).
"""

import re
import time
from dataclasses import dataclass, field
from typing import Any

from app.services.ai.llm_client import get_llm
from app.services.ai.prompts import PROMPT_VERSION

CRISIS_TYPES = [
    "medical",
    "fire",
    "gas_leak",
    "accident",
    "security",
    "disaster",
    "power",
    "other",
]

CLASSIFICATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "emergency_type": {"type": "string", "enum": CRISIS_TYPES},
        "sub_type": {"type": "string"},
        "severity_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "recommended_radius_km": {"type": "number", "minimum": 0.5, "maximum": 5},
        "suggested_responder_skills": {"type": "array", "items": {"type": "string"}},
        "reasoning": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["emergency_type", "severity_score", "confidence"],
}

# Keyword weights for the heuristic classifier: (crisis, word, weight).
_KEYWORDS: list[tuple[str, str, int]] = [
    ("medical", "cardiac", 6),
    ("medical", "arrest", 6),
    ("medical", "breathing", 4),
    ("medical", "cpr", 6),
    ("medical", "unconscious", 5),
    ("medical", "collapsed", 4),
    ("medical", "chest pain", 5),
    ("medical", "choking", 6),
    ("medical", "bleeding", 5),
    ("medical", "blood", 3),
    ("medical", "burn", 4),
    ("medical", "snake", 6),
    ("medical", "snakebite", 6),
    ("medical", "seizure", 6),
    ("medical", "fit", 2),
    ("medical", "stroke", 6),
    ("medical", "paralysis", 4),
    ("medical", "fainted", 4),
    ("medical", "dizzy", 2),
    ("medical", "heart", 4),
    ("medical", "allergic", 5),
    ("medical", "swelling", 2),
    ("medical", "poison", 6),
    ("medical", "heat", 2),
    ("medical", "medical", 2),
    ("medical", "ambulance", 2),
    ("medical", "injury", 2),
    ("medical", "hurt", 2),
    ("medical", "wound", 3),
    ("medical", "patient", 2),
    ("fire", "fire", 8),
    ("fire", "smoke", 4),
    ("fire", "flames", 7),
    ("fire", "burning", 5),
    ("fire", "burnt", 4),
    ("gas_leak", "gas", 6),
    ("gas_leak", "leak", 4),
    ("gas_leak", "smell of gas", 8),
    ("gas_leak", "cylinder", 5),
    ("gas_leak", "lpg", 6),
    ("accident", "accident", 7),
    ("accident", "crash", 6),
    ("accident", "car", 3),
    ("accident", "vehicle", 4),
    ("accident", "bike", 3),
    ("accident", "truck", 4),
    ("accident", "collision", 6),
    ("accident", "road", 3),
    ("accident", "hit", 3),
    ("security", "attack", 6),
    ("security", "threat", 5),
    ("security", "robbery", 7),
    ("security", "assault", 7),
    ("security", "weapon", 6),
    ("security", "knife", 4),
    ("security", "gun", 5),
    ("security", "fight", 3),
    ("security", "stalker", 4),
    ("disaster", "flood", 8),
    ("disaster", "earthquake", 9),
    ("disaster", "cyclone", 6),
    ("disaster", "tsunami", 9),
    ("disaster", "landslide", 7),
    ("disaster", "drown", 4),
    ("power", "electric", 6),
    ("power", "shock", 5),
    ("power", "wire", 3),
    ("power", "transformer", 5),
    ("power", "electrocuted", 8),
    ("power", "power line", 5),
]

# Criticality keywords push severity up regardless of type.
_CRITICAL_WORDS = [
    "not breathing",
    "unconscious",
    "cardiac",
    "arrest",
    "choking",
    "severe bleeding",
    "unresponsive",
    "collapsed",
    "snakebite",
    "stroke",
    "trapped",
    "drowning",
]
_HIGH_WORDS = ["bleeding", "burn", "accident", "fire", "shock", "seizure", "chest pain"]


@dataclass
class Classification:
    emergency_type: str
    sub_type: str | None
    severity_score: int
    confidence: float
    recommended_radius_km: float
    suggested_skills: list[str] = field(default_factory=list)
    source: str = "heuristic"  # gemini | heuristic | defaults
    prompt_version: str = PROMPT_VERSION
    latency_ms: int = 0

    def as_payload(self) -> dict[str, Any]:
        return {
            "emergency_type": self.emergency_type,
            "sub_type": self.sub_type,
            "severity_score": self.severity_score,
            "confidence": self.confidence,
            "recommended_radius_km": self.recommended_radius_km,
            "suggested_responder_skills": self.suggested_skills,
            "source": self.source,
        }


def severity_radius(severity: int) -> int:
    """Proposal §5 severity→radius bands, in meters."""
    if severity >= 80:
        return 3_000
    if severity >= 50:
        return 2_500
    if severity >= 20:
        return 1_500
    return 1_000


def heuristic_classify(text: str) -> Classification:
    lowered = text.lower()
    scores: dict[str, int] = {}
    matched_words: dict[str, list[str]] = {}
    for crisis, keyword, weight in _KEYWORDS:
        # Whole-word matching: "car" must not fire inside "carrying".
        if re.search(rf"\b{re.escape(keyword)}(?:s|es)?\b", lowered):
            scores[crisis] = scores.get(crisis, 0) + weight
            matched_words.setdefault(crisis, []).append(keyword)

    crisis_type = max(scores, key=lambda k: scores[k]) if scores else "other"
    confidence = min(0.9, 0.3 + 0.15 * len(matched_words.get(crisis_type, [])))

    severity = 50
    if any(word in lowered for word in _CRITICAL_WORDS):
        severity = 85
    elif any(word in lowered for word in _HIGH_WORDS):
        severity = 65
    elif scores:
        severity = 55
    else:
        severity = 40

    return Classification(
        emergency_type=crisis_type,
        sub_type=matched_words.get(crisis_type, [None])[0],
        severity_score=severity,
        confidence=round(confidence, 2),
        recommended_radius_km=severity_radius(severity) / 1000,
        suggested_skills=_SKILLS_BY_CRISIS.get(crisis_type, []),
        source="heuristic",
    )


_SKILLS_BY_CRISIS: dict[str, list[str]] = {
    "medical": ["doctor", "nurse", "paramedic", "cpr_certified"],
    "fire": ["firefighter"],
    "gas_leak": ["firefighter", "electrician"],
    "accident": ["doctor", "paramedic", "first_aid_trained"],
    "security": ["police"],
    "disaster": ["doctor", "nurse", "first_aid_trained"],
    "power": ["electrician"],
    "other": [],
}


async def classify_emergency(text: str) -> Classification:
    """LLM-structured classification with the safe fallback ladder."""
    llm = get_llm()
    started = time.perf_counter()
    if llm.name != "disabled":
        from app.services.ai.prompts import CLASSIFY_SYSTEM

        raw = await llm.generate_json(
            system=CLASSIFY_SYSTEM,
            user=f"Bystander report:\n{text}",
            schema=CLASSIFICATION_SCHEMA,
        )
        if raw and raw.get("emergency_type") in CRISIS_TYPES:
            severity = int(raw.get("severity_score", 50))
            result = Classification(
                emergency_type=raw["emergency_type"],
                sub_type=raw.get("sub_type"),
                severity_score=severity,
                confidence=float(raw.get("confidence", 0.5)),
                recommended_radius_km=float(raw.get("recommended_radius_km", 2.0)),
                suggested_skills=[
                    s for s in raw.get("suggested_responder_skills", []) if isinstance(s, str)
                ][:6],
                source="gemini",
            )
            result.latency_ms = int((time.perf_counter() - started) * 1000)
            return result

    fallback = heuristic_classify(text)
    fallback.latency_ms = int((time.perf_counter() - started) * 1000)
    return fallback
