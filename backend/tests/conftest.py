import json
import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.models import HouseholdProfile  # noqa: E402
from app.scoring import applicable_items  # noqa: E402

PERSONAS = json.loads((Path(__file__).parent / "fixtures" / "personas.json").read_text())["personas"]


def build_persona(key: str) -> tuple[HouseholdProfile, dict[str, str]]:
    """Return (profile, answers) with 'the rest' filled from default_answer."""
    spec = PERSONAS[key]
    profile = HouseholdProfile(**spec["profile"])
    answers = {i["id"]: spec["default_answer"] for i in applicable_items(profile)}
    answers.update(spec["answers"])
    return profile, answers


@pytest.fixture(params=sorted(PERSONAS))
def persona(request):
    key = request.param
    profile, answers = build_persona(key)
    return key, profile, answers


def pytest_collection_modifyitems(config, items):
    """Skip live tests unless RUN_LIVE=1 (REQUIREMENTS.md 13).

    The default suite must never touch the network, so anything marked
    `live` is skipped unless it is asked for explicitly.
    """
    if os.environ.get("RUN_LIVE") == "1":
        return
    skip = pytest.mark.skip(reason="live test: set RUN_LIVE=1 to run against the real model")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)
