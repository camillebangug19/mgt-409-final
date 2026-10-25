"""REQUIREMENTS.md 13.2 #2 — scoring rules."""

import pytest

from app.models import HouseholdProfile, Person, Pet
from app.scoring import round_to_half, score_readiness
from conftest import build_persona


def test_persona_c_scores_one():
    """All No -> the floor of the scale."""
    profile, answers = build_persona("C")
    assert score_readiness(profile, answers).score == 1.0


def test_persona_d_scores_ten():
    """All Yes -> a perfect score and the 'Ready to go!' label."""
    profile, answers = build_persona("D")
    result = score_readiness(profile, answers)
    assert result.score == 10.0
    assert result.label == "Ready to go!"


def test_scores_stay_in_range_and_on_half_steps(persona):
    _, profile, answers = persona
    score = score_readiness(profile, answers).score
    assert 1.0 <= score <= 10.0
    assert score * 2 == int(score * 2), f"{score} is not a 0.5 step"


def test_items_that_do_not_apply_are_excluded():
    """Persona D has no pets, no infant and no medical needs."""
    profile, answers = build_persona("D")
    applicable = set(score_readiness(profile, answers).applicable_item_ids)
    for excluded in ("pet_go_kit", "pet_lodging", "infant_feeding", "meds_7day", "backup_power"):
        assert excluded not in applicable
    assert "water" in applicable


def test_items_apply_when_the_household_has_that_need():
    profile, answers = build_persona("A")
    applicable = set(score_readiness(profile, answers).applicable_item_ids)
    assert "infant_feeding" in applicable
    assert {"pet_go_kit", "pet_lodging"} <= applicable
    assert "backup_power" not in applicable


def test_partly_is_half_credit():
    profile = HouseholdProfile(people=[Person(age_group="adult")])
    base = {i: "no" for i in score_readiness(profile, {}).applicable_item_ids}

    none = score_readiness(profile, base)
    partly = score_readiness(profile, {**base, "water": "partly"})
    full = score_readiness(profile, {**base, "water": "yes"})

    assert partly.earned == pytest.approx((none.earned + full.earned) / 2)


def test_not_sure_scores_the_same_as_no():
    profile = HouseholdProfile(people=[Person(age_group="adult")])
    base = {i: "no" for i in score_readiness(profile, {}).applicable_item_ids}
    assert score_readiness(profile, {**base, "water": "not_sure"}).earned == score_readiness(profile, base).earned


def test_answering_an_item_never_lowers_the_score(persona):
    """Completing anything only ever moves the score up."""
    _, profile, answers = persona
    before = score_readiness(profile, answers)
    for item_id in before.applicable_item_ids:
        improved = {**answers, item_id: "yes"}
        assert score_readiness(profile, improved).score >= before.score


def test_a_household_with_pets_has_a_pets_category():
    profile = HouseholdProfile(people=[Person(age_group="adult")], pets=[Pet(species="cat")])
    categories = {b.category for b in score_readiness(profile, {}).breakdown}
    assert "Pets" in categories


@pytest.mark.parametrize("raw,expected", [(1.0, 1.0), (5.24, 5.0), (5.26, 5.5), (9.9, 10.0)])
def test_round_to_half(raw, expected):
    assert round_to_half(raw) == expected
