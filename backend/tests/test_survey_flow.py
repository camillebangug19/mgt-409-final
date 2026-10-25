"""REQUIREMENTS.md 13.2 #4 — the survey asks for everything, and only what applies.

No real API calls: the agent runs against a scripted FunctionModel.
"""

import pytest

from app import survey
from app.survey import SlotError, build_profile, required_slots, survey_state, validate_slot
from stub_model import SCRIPTED_ANSWERS


def fill(slots: dict) -> dict:
    return {slot: validate_slot(slot, value) for slot, value in slots.items()}


def walk_the_survey(script: dict, baseline: str = "no") -> dict:
    """Answer whatever the engine asks until it says done. Mirrors the agent loop."""
    answers: dict = {}
    for _ in range(100):
        state = survey_state(answers)
        if state["done"]:
            return answers
        slot = state["next_slot"]
        answers[slot] = validate_slot(slot, script.get(slot, baseline))
    raise AssertionError("survey did not finish")


# --- every required slot gets asked --------------------------------------

def test_every_required_slot_is_asked_exactly_once():
    asked: list[str] = []
    answers: dict = {}
    for _ in range(100):
        state = survey_state(answers)
        if state["done"]:
            break
        slot = state["next_slot"]
        asked.append(slot)
        answers[slot] = validate_slot(slot, SCRIPTED_ANSWERS.get(slot, "no"))

    assert len(asked) == len(set(asked)), "a slot was asked twice"
    assert set(asked) == {slot for slot, _ in required_slots(answers)}


def test_the_survey_walks_the_sections_in_order():
    answers: dict = {}
    seen: list[str] = []
    for _ in range(100):
        state = survey_state(answers)
        if state["done"]:
            break
        if state["next_section"] not in seen:
            seen.append(state["next_section"])
        answers[state["next_slot"]] = validate_slot(
            state["next_slot"], SCRIPTED_ANSWERS.get(state["next_slot"], "no")
        )
    assert seen == list(survey.SECTIONS)


def test_a_person_slot_exists_for_each_household_member():
    answers = fill({"num_people": 3})
    missing = survey_state(answers)["missing"]
    assert missing[:3] == ["person_1", "person_2", "person_3"]
    # Later sections stay on the list, so progress is measured against the
    # real total rather than collapsing to whatever is known so far.
    assert "pets" in missing and "zip_code" in missing


def test_a_skipped_person_is_still_asked_for():
    """Answering person 2 but not person 1 must not strand the survey."""
    answers = fill({"num_people": 2, "person_2": "older_adult"})
    state = survey_state(answers)
    assert state["next_slot"] == "person_1"
    assert not state["done"]


def test_slots_cannot_be_answered_out_of_order():
    from app.survey import is_askable

    answers = fill({"num_people": 2})
    # Baseline questions do not exist until we know who lives there.
    assert not is_askable("water", answers)
    assert not is_askable("backup_power", answers)
    # Nor does a person who is not in the household.
    assert not is_askable("person_5", answers)
    assert is_askable("person_1", answers)
    assert is_askable("pets", answers)


def test_progress_reflects_the_real_total_once_the_size_is_known():
    answers = fill({"num_people": 2, "person_1": "adult"})
    state = survey_state(answers)
    assert state["progress"] < 0.5, "two of many answered, not two of three"


# --- conditional slots ----------------------------------------------------

def test_infant_feeding_is_asked_only_when_there_is_an_infant():
    with_infant = fill({"num_people": 2, "person_1": "adult", "person_2": "infant"})
    without = fill({"num_people": 2, "person_1": "adult", "person_2": "child"})

    assert "infant_feeding_method" in survey_state(with_infant)["missing"]
    assert "infant_feeding_method" not in survey_state(without)["missing"]


def test_pet_questions_are_skipped_when_there_are_no_pets():
    script = {**SCRIPTED_ANSWERS, "pets": "none"}
    answers = walk_the_survey(script)
    assert "pet_go_kit" not in answers and "pet_lodging" not in answers

    with_pets = walk_the_survey(SCRIPTED_ANSWERS)
    assert "pet_go_kit" in with_pets and "pet_lodging" in with_pets


def test_medical_questions_are_skipped_when_nobody_has_that_need():
    answers = walk_the_survey(SCRIPTED_ANSWERS)
    assert "meds_7day" not in answers
    assert "backup_power" not in answers

    script = {
        **SCRIPTED_ANSWERS,
        "daily_meds": {"people": [1]},
        "power_equipment": {"people": [{"person": 1, "equipment": ["oxygen"]}]},
    }
    with_needs = walk_the_survey(script)
    assert "meds_7day" in with_needs and "backup_power" in with_needs


def test_evacuation_helper_is_asked_only_when_someone_needs_help():
    script = {**SCRIPTED_ANSWERS, "mobility_needs": {"people": [{"person": 1, "mobility": "wheelchair"}]}}
    assert "evacuation_helper" in walk_the_survey(script)
    assert "evacuation_helper" not in walk_the_survey(SCRIPTED_ANSWERS)


# --- done ------------------------------------------------------------------

def test_done_is_false_until_every_slot_is_filled():
    answers: dict = {}
    assert not survey_state(answers)["done"]
    for _ in range(100):
        state = survey_state(answers)
        if state["done"]:
            break
        assert state["next_slot"], "not done, so there must be a next question"
        answers[state["next_slot"]] = validate_slot(
            state["next_slot"], SCRIPTED_ANSWERS.get(state["next_slot"], "no")
        )
    assert survey_state(answers)["done"]
    assert survey_state(answers)["next_slot"] is None


def test_progress_rises_and_never_exceeds_one():
    answers: dict = {}
    previous = -1.0
    for _ in range(100):
        state = survey_state(answers)
        assert 0.0 <= state["progress"] <= 1.0
        if state["done"]:
            break
        answers[state["next_slot"]] = validate_slot(
            state["next_slot"], SCRIPTED_ANSWERS.get(state["next_slot"], "no")
        )
    assert survey_state(answers)["progress"] == 1.0


def test_the_finished_survey_builds_the_expected_profile():
    answers = walk_the_survey(SCRIPTED_ANSWERS)
    profile = build_profile(answers)
    assert len(profile.people) == 4
    assert profile.has_infant and profile.has_pets
    assert profile.state == "TX" and profile.zip_code == "78701"
    assert [p.infant_feeding for p in profile.people if p.age_group == "infant"] == ["formula"]


# --- validation -------------------------------------------------------------

@pytest.mark.parametrize(
    "slot,value",
    [
        ("num_people", "lots"),
        ("num_people", 0),
        ("zip_code", "787"),
        ("zip_code", "not a zip"),
        ("state", "Texas"),
        ("housing_type", "castle"),
        ("person_1", {"age_group": "grown up"}),
        ("water", "maybe"),
        ("nonexistent_slot", "x"),
    ],
)
def test_bad_values_are_rejected(slot, value):
    with pytest.raises(SlotError):
        validate_slot(slot, value)


@pytest.mark.parametrize(
    "slot,value,expected",
    [
        ("state", "tx", "TX"),
        ("has_vehicle", "Yes", True),
        ("has_vehicle", "no", False),
        ("water", "Not Sure", "not_sure"),
        ("person_1", "older adult", {"age_group": "older_adult"}),
        ("pets", "none", {"none": True}),
    ],
)
def test_values_are_normalised(slot, value, expected):
    assert validate_slot(slot, value) == expected


def test_nicknames_are_optional_and_capped():
    assert validate_slot("person_1", {"age_group": "adult"}) == {"age_group": "adult"}
    person = validate_slot("person_1", {"age_group": "adult", "nickname": "G" * 80})
    assert len(person["nickname"]) == 40
