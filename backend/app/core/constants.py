"""Shared domain constants — single source of truth for skill types.

Used by API validation, the seed script, and (in Phase 5) the Gemini
classification schema so the three can never drift apart.
"""

SKILL_TYPES = [
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
]

# Certificate upload whitelist (extension -> content type)
CERTIFICATE_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}
MAX_CERTIFICATE_MB = 5

# --- SOS engine (Phase 2) ------------------------------------------------------

CRISIS_TYPES = ["medical", "fire", "gas_leak", "accident", "security", "disaster", "power", "other"]

# Which responder skills matter per crisis type (proposal Module 6 scenarios).
SKILLS_BY_CRISIS: dict[str, list[str]] = {
    "medical": ["doctor", "nurse", "paramedic", "cpr_certified", "first_aid_trained"],
    "fire": ["firefighter"],
    "gas_leak": ["firefighter", "electrician"],
    "accident": ["doctor", "nurse", "paramedic", "first_aid_trained"],
    "security": ["police"],
    "disaster": ["doctor", "nurse", "first_aid_trained"],
    "power": ["electrician"],
    "other": [],
}

# How many responders to notify, by severity band (severity may be None pre-AI).
TOP_N_BY_SEVERITY: list[tuple[int, int]] = [
    (80, 200),  # critical — effectively everyone matched
    (50, 10),
    (20, 5),
    (0, 3),
]
TOP_N_DEFAULT = 5

# Escalation (Architecture.md §5): wave w arms at created_at + WAVE_SECONDS[w-1].
WAVE_SECONDS = [30, 45, 60]
WAVE_RADIUS_MULTIPLIER = {1: 2, 2: 3, 3: 1}  # wave 3 only prompts calling 108/112
PENDING_EXPIRE_MINUTES = 15

# Timeline event types
EVENT_SOS_CREATED = "sos_created"
EVENT_RESPONDERS_NOTIFIED = "responders_notified"
EVENT_RESPONSE_ACCEPTED = "response_accepted"
EVENT_SOS_RESOLVED = "sos_resolved"
EVENT_SOS_EXPIRED = "sos_expired"
EVENT_ESCALATION_WAVE = "escalation_wave"
EVENT_CALL_SERVICES_PROMPTED = "call_services_prompted"
