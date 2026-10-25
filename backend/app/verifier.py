"""Checks Coach output before it reaches the user (REQUIREMENTS.md 5 / 10).

Three rules:
  1. A step must be one the Python ranker already chose. No invented steps.
  2. A link must already exist in the knowledge base. No invented URLs.
  3. No dosing language. Medication wording points at a doctor or pharmacist.

Anything removed is recorded in `flagged` so it can be shown in the report.
"""

import re

from . import kb

MEDICAL_DISCLAIMER = (
    "Not medical advice. Ask your doctor or pharmacist about medications and medical devices."
)

# Dosing language: a quantity plus a unit, or an explicit instruction to take an amount.
DOSING_PATTERNS = (
    r"\b\d+(\.\d+)?\s*(mg|milligram|mcg|microgram|ml|millilitre|milliliter|cc|g|gram|iu|units?)\b",
    r"\b\d+(\.\d+)?\s*(pill|tablet|capsule|dose|puff|drop|spray)s?\b",
    r"\b\d+\s*(pill|tablet|capsule|dose|puff)s?\s+(a|per|each)\s+(day|night|hour|morning|evening)\b",
    r"\b(double|triple|halve|increase|decrease|reduce|skip|stop taking)\s+(the\s+|your\s+|their\s+)?(dose|dosage|medication|meds)\b",
    r"\bevery\s+\d+\s*(hours?|hrs?)\b",
    r"\b(dosage|dosing)\s+(is|of|should)\b",
)

URL_PATTERN = re.compile(r"https?://[^\s\]\)\"'<>]+")


class VerificationResult:
    def __init__(self, text: str, flagged: list[str], blocked: bool = False):
        self.text = text
        self.flagged = flagged
        self.blocked = blocked

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"VerificationResult(blocked={self.blocked}, flagged={self.flagged})"


def contains_dosing(text: str) -> bool:
    lowered = (text or "").lower()
    return any(re.search(pattern, lowered) for pattern in DOSING_PATTERNS)


def check_text(text: str, context: str = "text") -> VerificationResult:
    """Strip unknown URLs and block dosing language."""
    flagged: list[str] = []
    cleaned = text or ""

    if contains_dosing(cleaned):
        flagged.append(f"{context}: dosing language blocked")
        return VerificationResult(MEDICAL_DISCLAIMER, flagged, blocked=True)

    allowed = kb.allowed_urls()
    for url in URL_PATTERN.findall(cleaned):
        if url.rstrip(".,);") not in allowed:
            flagged.append(f"{context}: removed unknown link {url}")
            cleaned = cleaned.replace(url, "")

    return VerificationResult(re.sub(r"\s{2,}", " ", cleaned).strip(), flagged)


def verify_plan(plan_items: list[dict], allowed_step_ids: set[str]) -> tuple[list[dict], list[str]]:
    """Keep only steps the ranker chose, with their KB text cleaned.

    Args:
        plan_items: what the Coach returned, each {step_id, why}.
        allowed_step_ids: the step ids rank_next_steps produced.

    Returns:
        (kept items, flagged messages)
    """
    flagged: list[str] = []
    kept: list[dict] = []
    seen: set[str] = set()

    for item in plan_items:
        step_id = (item.get("step_id") or "").strip()

        if step_id not in allowed_step_ids:
            flagged.append(f"invented or unranked step removed: {step_id or '(blank)'}")
            continue
        if step_id in seen:
            flagged.append(f"duplicate step removed: {step_id}")
            continue

        result = check_text(item.get("why", ""), context=f"why for {step_id}")
        flagged.extend(result.flagged)
        seen.add(step_id)
        kept.append({"step_id": step_id, "why": result.text})

    return kept, flagged


def verify_sources(source_ids: list[str], context: str = "sources") -> tuple[list[str], list[str]]:
    """Drop any source id that is not in the knowledge base."""
    flagged: list[str] = []
    kept: list[str] = []
    for source_id in source_ids:
        if kb.source(source_id):
            kept.append(source_id)
        else:
            flagged.append(f"{context}: removed unknown source {source_id}")
    return kept, flagged
