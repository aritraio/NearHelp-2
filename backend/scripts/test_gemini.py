"""Phase 0 AI smoke test: first structured-output Gemini call.

Run from backend/ with a key from https://aistudio.google.com/apikey:

    GEMINI_API_KEY=... python -m scripts.test_gemini "man collapsed, not breathing"

Exits 0 only if the response parses against the classification schema — this
is the AI-side acceptance criterion for Phase 0 (todos.md §0.3). The same
schema becomes /api/ai/classify's contract in Phase 5.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from google import genai  # noqa: E402
from google.genai import types  # noqa: E402

DEFAULT_REPORT = "A man in his 60s collapsed at the bus stop. He is unresponsive and not breathing."

PROMPT = """You are an emergency dispatcher triaging a bystander report.
Classify the emergency and assess severity. Consider immediacy of threat to
life, number of people affected, and time sensitivity.

Report: {report}"""

# Shared with the future /api/ai/classify endpoint (Architecture.md §6).
CLASSIFICATION_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "emergency_type": {
            "type": "string",
            "enum": ["medical", "fire", "gas_leak", "accident", "security", "disaster", "other"],
        },
        "sub_type": {"type": "string"},
        "severity_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "recommended_radius_km": {"type": "number", "minimum": 0.5, "maximum": 5},
        "suggested_responder_skills": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "doctor",
                    "nurse",
                    "paramedic",
                    "firefighter",
                    "police",
                    "cpr_certified",
                    "first_aid_trained",
                    "blood_donor",
                    "electrician",
                    "mechanic",
                ],
            },
        },
    },
    "required": ["emergency_type", "severity_score", "confidence", "suggested_responder_skills"],
}


async def main() -> int:
    settings = get_settings()
    if not settings.gemini_api_key:
        print("GEMINI_API_KEY not set — copy .env.example to .env and add your key.")
        return 2

    report = " ".join(sys.argv[1:]) or DEFAULT_REPORT
    client = genai.Client(api_key=settings.gemini_api_key)

    response = await client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=PROMPT.format(report=report),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CLASSIFICATION_SCHEMA,
        ),
    )

    data = json.loads(response.text)
    print(json.dumps(data, indent=2))

    assert data["emergency_type"], "emergency_type missing"
    assert 0 <= data["severity_score"] <= 100, "severity_score out of range"
    assert data["suggested_responder_skills"], "no skills suggested"
    print("\nSMOKE TEST PASSED — structured output parses against the schema")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
