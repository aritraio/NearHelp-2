"""Output guardrails — the last line of defense (Architecture.md §6).

The prompt constrains the model; these functions assume it failed and check
the text anyway. Unit-tested in CI so a prompt regression cannot silently
ship (todos.md §5.2).
"""

import re

# Dosages / prescriptions / invasive procedures / diagnosis language.
BLOCKLIST_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("dosage", re.compile(r"\b\d+\s*(?:mg|mcg|g|ml|grams?|milligrams?|tablets?|pills?)\b", re.I)),
    ("prescription", re.compile(r"\b(prescri\w*|dose of \w+|take \d+ )", re.I)),
    ("diagnosis", re.compile(r"\b(diagnos\w*|you have|confirmed to be)\b", re.I)),
    ("invasive", re.compile(r"\b(surg\w*|incision|stitch\w*|cut open|suture)\b", re.I)),
    ("injection-advice", re.compile(r"\b(inject\w*)\b", re.I)),
]

# Terms that MUST appear before any medication/injection advice is allowed
# (adrenaline auto-injector use IS part of anaphylaxis protocol).
_INJECTOR_ALLOWED = re.compile(r"auto.?injector|epipen|adrenaline", re.I)


def find_violations(text: str) -> list[str]:
    """Returns the list of violated rule names for a generated output."""
    violations: list[str] = []
    for name, pattern in BLOCKLIST_PATTERNS:
        matches = pattern.findall(text)
        if not matches:
            continue
        if name == "injection-advice" and _INJECTOR_ALLOWED.search(text):
            # Injector guidance within anaphylaxis protocol is legitimate.
            continue
        violations.append(name)
    return violations


CITATION_RE = re.compile(r"\[P(\d+)\]")


def extract_citations(step: str) -> list[int]:
    return [int(m) for m in CITATION_RE.findall(step)]


def has_citation(step: str) -> bool:
    return bool(CITATION_RE.search(step))


def strip_citation(step: str) -> str:
    return CITATION_RE.sub("", step).strip()


def sanitize_steps(steps: list[str], max_procedure_index: int) -> tuple[list[str], bool]:
    """Drops uncited or out-of-range steps.

    Returns (clean_steps_with_citations, all_valid). When nothing survives,
    the caller serves the fallback line instead of the model's text.
    """
    clean: list[str] = []
    for step in steps:
        citations = extract_citations(step)
        if not citations:
            continue
        if any(index >= max_procedure_index for index in citations):
            continue
        if find_violations(step):
            continue
        clean.append(step.strip())
    return clean, bool(clean) and len(clean) == len(steps)
