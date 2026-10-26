"""REQUIREMENTS.md 13.2 #3 — ranking the next steps."""

import pytest

from app import kb
from app.scoring import (
    _completed_answers,
    _raw_gain,
    _step_priority,
    candidate_steps,
    rank_next_steps,
    score_readiness,
)
from conftest import build_persona


def test_at_most_three_steps(persona):
    _, profile, answers = persona
    assert len(rank_next_steps(profile, answers)) <= 3


def test_only_applicable_steps_are_offered(persona):
    """A step must touch at least one rubric item that applies to this household."""
    _, profile, answers = persona
    applicable = set(score_readiness(profile, answers).applicable_item_ids)
    for step in candidate_steps(profile, answers):
        assert set(step["rubric_item_ids"]) & applicable


def test_sorted_by_gain_within_a_priority_tier(persona):
    _, profile, answers = persona
    rows = [
        (_step_priority(s, profile), _raw_gain(s, profile, answers), s["est_minutes"])
        for s in candidate_steps(profile, answers)
    ]
    for earlier, later in zip(rows, rows[1:]):
        assert earlier[0] <= later[0]
        if earlier[0] == later[0]:
            assert (earlier[1], -earlier[2]) >= (later[1], -later[2])


def test_points_gain_is_the_steps_true_share_of_the_scale(persona):
    """The '+X points' badge is the step's contribution before 0.5 rounding."""
    _, profile, answers = persona
    result = score_readiness(profile, answers)
    for next_step in rank_next_steps(profile, answers):
        step = kb.step_by_id(next_step.id)
        expected = 9 * _raw_gain(step, profile, answers) / result.max_points
        assert next_step.points_gain == round(expected, 1)


def test_no_step_is_ever_advertised_as_worth_nothing(persona):
    """A '+0 points' badge would break the promise that every step earns something."""
    _, profile, answers = persona
    for next_step in rank_next_steps(profile, answers):
        assert next_step.points_gain > 0, next_step.id


def test_the_badges_add_up_to_the_points_left_to_win(persona):
    """Every remaining step together should close the gap to 10."""
    _, profile, answers = persona
    result = score_readiness(profile, answers)
    total = sum(
        9 * _raw_gain(kb.step_by_id(s["id"]), profile, answers) / result.max_points
        for s in candidate_steps(profile, answers)
    )
    exact = 1 + 9 * (result.earned / result.max_points)
    assert total == pytest.approx(10 - exact, abs=0.01)


def test_completing_a_step_moves_the_displayed_score_up_or_holds_it(persona):
    """The displayed score rounds to 0.5, so it may hold, but it never drops."""
    _, profile, answers = persona
    before = score_readiness(profile, answers).score
    for next_step in rank_next_steps(profile, answers):
        step = kb.step_by_id(next_step.id)
        after = score_readiness(profile, _completed_answers(answers, step)).score
        assert after >= before


def test_completed_steps_never_reappear(persona):
    """Walk the whole list: each completed step drops out and the score rises."""
    _, profile, answers = persona
    completed: set[str] = set()
    previous = score_readiness(profile, answers).score

    while True:
        offered = rank_next_steps(profile, answers, completed)
        if not offered:
            break
        assert not ({s.id for s in offered} & completed)
        step = kb.step_by_id(offered[0].id)
        answers = _completed_answers(answers, step)
        completed.add(step["id"])
        current = score_readiness(profile, answers).score
        assert current >= previous
        previous = current

    assert previous == 10.0, "working through every step should reach a perfect score"


def test_persona_a_plan_step_in_top_three_and_no_stear():
    profile, answers = build_persona("A")
    top = rank_next_steps(profile, answers)
    assert "family-plan" in {s.id for s in top}
    # Nobody in persona A needs evacuation help, so the TX registry is not suggested.
    assert all("tx_stear" not in s.source_ids for s in top)


def test_persona_b_backup_power_and_transportation_in_top_three():
    profile, answers = build_persona("B")
    assert {"backup-power", "transportation-plan"} <= {s.id for s in rank_next_steps(profile, answers)}


def test_persona_b_florida_falls_back_to_national_links():
    resources = kb.local_resources("FL")
    assert resources
    assert all(r["state"] == "*" and r["verified"] for r in resources)


def test_persona_c_evacuation_helper_with_stear_and_pet_steps_present():
    profile, answers = build_persona("C")
    top = rank_next_steps(profile, answers)
    helper = next(s for s in top if s.id == "evacuation-helper")
    assert "tx_stear" in helper.source_ids, "TX households get the STEAR registry"
    assert "pet-kit-lodging" in {s["id"] for s in candidate_steps(profile, answers)}


def test_persona_d_has_no_steps_left():
    profile, answers = build_persona("D")
    assert rank_next_steps(profile, answers) == []


def test_unverified_state_links_are_hidden():
    """REQUIREMENTS.md 7.2 — TODO entries must never reach the UI."""
    for state in ("TX", "CT", "FL"):
        for resource in kb.local_resources(state):
            assert resource["verified"]
            assert resource["url"] != "TODO"


def test_every_step_source_exists_and_is_on_an_allowed_domain():
    """REQUIREMENTS.md 7 — no invented links."""
    for step in kb.steps():
        ids = step["source_ids"] + [s for v in step.get("state_extras", {}).values() for s in v]
        for source_id in ids:
            source = kb.source(source_id)
            assert source, f"{step['id']} references unknown source {source_id}"
            host = source["source_url"].split("/")[2].removeprefix("www.")
            allowed = kb.ALLOWED_DOMAINS + ("tdem.texas.gov",)
            assert any(host == d or host.endswith("." + d) for d in allowed), host
