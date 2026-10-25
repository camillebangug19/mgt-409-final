"""Loads the knowledge base JSON files. These are the only source of guidance."""

import json
from functools import lru_cache

from .config import KB_DIR

ALLOWED_DOMAINS = (
    "ready.gov",
    "fema.gov",
    "cdc.gov",
    "aap.org",
    "healthychildren.org",
    "redcross.org",
    "acl.gov",
    "hhs.gov",
)


@lru_cache(maxsize=None)
def _load(name: str) -> dict:
    with open(KB_DIR / f"{name}.json", encoding="utf-8") as fh:
        return json.load(fh)


def rubric_items() -> list[dict]:
    return _load("rubric")["items"]


def rubric_note() -> str:
    return _load("rubric")["note"]


def steps() -> list[dict]:
    return _load("steps")["steps"]


def step_by_id(step_id: str) -> dict | None:
    return next((s for s in steps() if s["id"] == step_id), None)


def sources() -> dict:
    return _load("guidance")["sources"]


def source(source_id: str) -> dict | None:
    return sources().get(source_id)


def guidance_module(module_id: str) -> dict | None:
    return _load("guidance")["modules"].get(module_id)


def cheap_options() -> list[dict]:
    return _load("cheap_options")["options"]


def cheap_option(option_id: str) -> dict | None:
    return next((o for o in cheap_options() if o["id"] == option_id), None)


def local_resources(state: str | None) -> list[dict]:
    """Verified state links, falling back to Ready.gov/FEMA (REQUIREMENTS.md 5.2)."""
    data = _load("local_resources")
    entries = data["states"].get((state or "").upper(), [])
    verified = [e for e in entries if e.get("verified")]
    return verified or list(data["fallback"])


def allowed_urls() -> set[str]:
    """Every URL the app is allowed to show, drawn only from the KB."""
    urls = {s["source_url"] for s in sources().values()}
    data = _load("local_resources")
    for entry in data["fallback"]:
        urls.add(entry["url"])
    for entries in data["states"].values():
        urls.update(e["url"] for e in entries if e.get("verified"))
    return urls
