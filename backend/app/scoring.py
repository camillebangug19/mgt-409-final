"""Deterministic scoring and step ranking (REQUIREMENTS.md 6.1 / 6.3).

Plain Python on purpose: the LLM never decides a score or picks a step.
"""

from . import kb
from .models import (
    ANSWER_CREDIT,
    CategoryBreakdown,
    HouseholdProfile,
    NextStep,
    ScoreResult,
)

LABELS = (
    (3.0, "Just starting"),
    (5.5, "Getting there"),
    (7.5, "Well on your way"),
    (9.5, "Nearly ready"),
    (10.0, "Ready to go!"),
)


def label_for(score: float) -> str:
    for ceiling, label in LABELS:
        if score <= ceiling:
            return label
    return LABELS[-1][1]


def round_to_half(value: float) -> float:
    return round(value * 2) / 2


def applicable_items(profile: HouseholdProfile) -> list[dict]:
    flags = profile.flags()
    return [i for i in kb.rubric_items() if flags.get(i["applies_if"], False)]


def _credit(answers: dict[str, str], item_id: str) -> float:
    return ANSWER_CREDIT.get(answers.get(item_id, "no"), 0.0)


def score_readiness(profile: HouseholdProfile, answers: dict[str, str]) -> ScoreResult:
    """Score 1-10 in 0.5 steps: 1 + 9 * (earned / max of applicable items)."""
    items = applicable_items(profile)
    max_points = sum(i["points"] for i in items)
    earned = sum(i["points"] * _credit(answers, i["id"]) for i in items)

    ratio = (earned / max_points) if max_points else 0.0
    score = round_to_half(1 + 9 * ratio)

    by_category: dict[str, list[float]] = {}
    for item in items:
        slot = by_category.setdefault(item["category"], [0.0, 0.0])
        slot[0] += item["points"] * _credit(answers, item["id"])
        slot[1] += item["points"]

    return ScoreResult(
        score=score,
        label=label_for(score),
        earned=round(earned, 3),
        max_points=round(max_points, 3),
        breakdown=[
            CategoryBreakdown(category=c, earned=round(v[0], 3), max_points=round(v[1], 3))
            for c, v in by_category.items()
        ],
        missing_item_ids=[i["id"] for i in items if _credit(answers, i["id"]) < 1.0],
        applicable_item_ids=[i["id"] for i in items],
    )


def _step_priority(step: dict, profile: HouseholdProfile) -> int:
    """Lower sorts first. Life-safety steps outrank bigger but less urgent ones.

    REQUIREMENTS.md 5.2 says "sorted by points gained, then ease", but the
    persona expectations in 13.1 (B wants backup power + transportation in the
    top 3, C wants the evacuation helper) only hold if special-needs steps come
    first. TODO(camille): confirm this tiering is what you want for the report.
    """
    priority = step.get("priority", 2)
    flags = profile.flags()
    for flag, override in step.get("priority_if", {}).items():
        if flags.get(flag):
            priority = min(priority, override)
    return priority


def _raw_gain(step: dict, profile: HouseholdProfile, answers: dict[str, str]) -> float:
    """Rubric points still available on this step, for this household."""
    applicable = {i["id"]: i for i in applicable_items(profile)}
    total = 0.0
    for item_id in step["rubric_item_ids"]:
        item = applicable.get(item_id)
        if item:
            total += item["points"] * (1.0 - _credit(answers, item_id))
    return round(total, 4)


def _completed_answers(answers: dict[str, str], step: dict) -> dict[str, str]:
    updated = dict(answers)
    for item_id in step["rubric_item_ids"]:
        updated[item_id] = "yes"
    return updated


def score_gain(step: dict, profile: HouseholdProfile, answers: dict[str, str]) -> float:
    """What this step is worth on the 1-10 scale, for this household.

    This is the step's share of the scale before the 0.5 rounding that the
    displayed score uses: 9 * (points still on this step / applicable points).

    REQUIREMENTS.md 6.1 defines "+X" as the change in the displayed score, but
    the displayed score moves in 0.5 steps, so a small item near the top of the
    scale rounds away and the badge reads "+0 points" - which breaks the
    promise in section 1 that every completed step visibly earns something.
    Showing the true contribution keeps every badge positive and makes the
    badges sum to the points left to win.
    TODO(camille): mention this trade-off in the report; flip back to
    `round(after - before, 2)` if your professor wants the literal reading.
    """
    items = applicable_items(profile)
    max_points = sum(i["points"] for i in items)
    if not max_points:
        return 0.0
    return round(9 * _raw_gain(step, profile, answers) / max_points, 1)


def candidate_steps(
    profile: HouseholdProfile,
    answers: dict[str, str],
    completed_step_ids: set[str] | None = None,
) -> list[dict]:
    """Applicable steps with points still to gain, best first."""
    completed = completed_step_ids or set()
    applicable_ids = {i["id"] for i in applicable_items(profile)}

    candidates = []
    for step in kb.steps():
        if step["id"] in completed:
            continue
        if not (set(step["rubric_item_ids"]) & applicable_ids):
            continue
        gain = _raw_gain(step, profile, answers)
        if gain <= 0:
            continue
        candidates.append((_step_priority(step, profile), -gain, step["est_minutes"], step))

    candidates.sort(key=lambda row: row[:3])
    return [row[3] for row in candidates]


def rank_next_steps(
    profile: HouseholdProfile,
    answers: dict[str, str],
    completed_step_ids: set[str] | None = None,
    limit: int = 3,
) -> list[NextStep]:
    """The top `limit` next steps, each with the real score change it would give."""
    chosen = candidate_steps(profile, answers, completed_step_ids)[:limit]
    return [
        NextStep(
            id=step["id"],
            title=step["title"],
            points_gain=score_gain(step, profile, answers),
            est_minutes=step["est_minutes"],
            est_cost_band=step["est_cost_band"],
            how_to=step["how_to"],
            self_check=step["self_check"],
            source_ids=step["source_ids"] + step.get("state_extras", {}).get((profile.state or "").upper(), []),
            cheap_option_ids=step["cheap_option_ids"],
        )
        for step in chosen
    ]


def calc_quantities(profile: HouseholdProfile, days: int = 3) -> dict:
    """Water, food and pet quantities for this household (REQUIREMENTS.md 5.2)."""
    people = len(profile.people) or 1
    pets = sum(p.count for p in profile.pets)
    return {
        "days": days,
        "people": people,
        "water_gallons": people * days,  # 1 gallon per person per day
        "food_days": days,
        "pets": pets,
        "pet_water_gallons": pets * days,
        "meds_reminder": (
            "Keep a 7-day supply of daily medications. Not medical advice — ask your "
            "doctor or pharmacist about medications and medical devices."
            if profile.has_meds
            else None
        ),
    }
