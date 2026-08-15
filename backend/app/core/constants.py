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
