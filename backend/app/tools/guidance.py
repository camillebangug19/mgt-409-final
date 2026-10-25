"""Lookup tools for the Coach. Every answer comes from the knowledge base."""

from .. import kb
from ..models import HouseholdProfile
from ..scoring import calc_quantities


def get_guidance(module_id: str) -> dict:
    """Vetted guidance text and sources for one step."""
    module = kb.guidance_module(module_id)
    if not module:
        return {"found": False, "module_id": module_id}
    return {
        "found": True,
        "module_id": module_id,
        "summary": module["summary"],
        "sources": [
            {"id": sid, **kb.source(sid)} for sid in module["source_ids"] if kb.source(sid)
        ],
    }


def get_local_resources(state: str | None) -> dict:
    """Verified state links, or the national fallback (REQUIREMENTS.md 5.2)."""
    resources = kb.local_resources(state)
    return {
        "state": (state or "").upper() or None,
        "is_fallback": all(r["state"] == "*" for r in resources),
        "resources": resources,
    }


def quantities_for(profile: HouseholdProfile, days: int = 3) -> dict:
    """Water, food and pet quantities for this household."""
    return calc_quantities(profile, days)
