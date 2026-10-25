"""REQUIREMENTS.md 13.2 #5 — invented steps and links are removed; dosing is blocked."""

import pytest

from app import kb
from app.verifier import (
    MEDICAL_DISCLAIMER,
    check_text,
    contains_dosing,
    verify_plan,
    verify_sources,
)

ALLOWED_STEPS = {"family-plan", "kit-phases", "alerts-on"}


# --- invented steps --------------------------------------------------------

def test_an_invented_step_is_removed_and_flagged():
    kept, flagged = verify_plan(
        [
            {"step_id": "family-plan", "why": "You have no written plan yet."},
            {"step_id": "buy-a-generator-from-my-friend", "why": "Trust me."},
        ],
        ALLOWED_STEPS,
    )
    assert [item["step_id"] for item in kept] == ["family-plan"]
    assert any("buy-a-generator-from-my-friend" in message for message in flagged)


def test_a_real_step_that_was_not_ranked_is_still_removed():
    """The Coach may only use the candidates it was given."""
    kept, flagged = verify_plan([{"step_id": "pet-kit-lodging", "why": "..."}], ALLOWED_STEPS)
    assert kept == []
    assert flagged and "pet-kit-lodging" in flagged[0]


def test_duplicate_steps_are_removed():
    kept, flagged = verify_plan(
        [{"step_id": "family-plan", "why": "a"}, {"step_id": "family-plan", "why": "b"}],
        ALLOWED_STEPS,
    )
    assert len(kept) == 1
    assert any("duplicate" in message for message in flagged)


def test_a_blank_step_id_is_removed():
    kept, flagged = verify_plan([{"step_id": "", "why": "..."}], ALLOWED_STEPS)
    assert kept == []
    assert flagged


# --- invented links --------------------------------------------------------

def test_an_invented_url_is_removed_and_flagged():
    result = check_text("Order one at https://prepper-deals.example.com/kit today")
    assert "prepper-deals.example.com" not in result.text
    assert any("removed unknown link" in message for message in result.flagged)


def test_a_knowledge_base_url_survives():
    result = check_text("Full checklist at https://www.ready.gov/kit")
    assert "https://www.ready.gov/kit" in result.text
    assert result.flagged == []


def test_a_plausible_but_unlisted_gov_url_is_still_removed():
    """Being on an allowed domain is not enough; it has to be in the KB."""
    result = check_text("See https://www.ready.gov/make-a-plan for more")
    assert "make-a-plan" not in result.text
    assert result.flagged


def test_urls_inside_coach_notes_are_stripped():
    kept, flagged = verify_plan(
        [{"step_id": "family-plan", "why": "Do it at https://notreal.example.com"}],
        ALLOWED_STEPS,
    )
    assert "notreal.example.com" not in kept[0]["why"]
    assert flagged


def test_unknown_source_ids_are_dropped():
    kept, flagged = verify_sources(["ready_kit", "made_up_source"])
    assert kept == ["ready_kit"]
    assert any("made_up_source" in message for message in flagged)


def test_every_kb_url_passes_its_own_verifier():
    for url in kb.allowed_urls():
        assert check_text(f"See {url}").flagged == []


# --- medical overreach -----------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "Take 500 mg of ibuprofen twice a day",
        "Give the baby 2 tablets before bed",
        "Take 3 pills each morning",
        "You should double the dose during an outage",
        "Use the inhaler every 4 hours",
        "The dosage is 10 ml",
        "Stop taking your medication if the power goes out",
    ],
)
def test_dosing_language_is_blocked(text):
    assert contains_dosing(text)
    result = check_text(text)
    assert result.blocked
    assert result.text == MEDICAL_DISCLAIMER


@pytest.mark.parametrize(
    "text",
    [
        "Keep a 7-day supply of daily medications",
        "Ask your doctor or pharmacist how to build up a spare supply",
        "Write down what each person takes and keep it with your documents",
        "Store one gallon of water per person per day",
        "Pack three days of food",
    ],
)
def test_legitimate_preparedness_wording_is_allowed(text):
    assert not contains_dosing(text)
    assert not check_text(text).blocked


def test_a_dosing_note_is_replaced_in_the_plan():
    kept, flagged = verify_plan(
        [{"step_id": "family-plan", "why": "Keep 400 mg on hand for the baby."}],
        ALLOWED_STEPS,
    )
    assert kept[0]["why"] == MEDICAL_DISCLAIMER
    assert any("dosing" in message for message in flagged)


def test_the_medication_step_tells_people_to_ask_a_professional():
    step = kb.step_by_id("meds-7day")
    assert "doctor or pharmacist" in " ".join(step["how_to"]) + step.get("medical_note", "")
    assert not contains_dosing(" ".join(step["how_to"]))


def test_no_kb_step_contains_dosing_language():
    for step in kb.steps():
        text = " ".join(step["how_to"]) + " " + step["title"]
        assert not contains_dosing(text), step["id"]
