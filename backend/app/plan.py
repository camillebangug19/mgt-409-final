"""Builds the score reveal and the three next steps.

Order of operations (REQUIREMENTS.md 5):
    score_readiness -> rank_next_steps -> Coach -> verifier -> UI
Python picks the steps and the points. The Coach only adds wording, and the
verifier drops anything it invented.
"""

from . import chat, db, kb, survey, verifier
from .agents.coach import CoachDeps, build_coach_agent, coach_prompt
from .models import HouseholdProfile
from .scoring import calc_quantities, rank_next_steps, score_readiness
from .tools.guidance import get_local_resources

# Coach wording per (session, step). Cached so re-scoring after a completed
# step does not pay for the same sentence twice.
_NOTES: dict[tuple[str, str], str] = {}

_coach = None


def get_coach(model=None):
    global _coach
    if model is not None:
        return build_coach_agent(model)
    if _coach is None:
        _coach = build_coach_agent()
    return _coach


def reset_notes(session_id: str | None = None) -> None:
    if session_id is None:
        _NOTES.clear()
    else:
        for key in [k for k in _NOTES if k[0] == session_id]:
            del _NOTES[key]


def _resolve_sources(source_ids: list[str]) -> list[dict]:
    kept, _ = verifier.verify_sources(source_ids)
    return [{"id": sid, **kb.source(sid)} for sid in kept]


def _resolve_cheap_options(option_ids: list[str]) -> list[dict]:
    options = []
    for option_id in option_ids:
        option = kb.cheap_option(option_id)
        if not option:
            continue
        source = kb.source(option["source_id"])
        options.append({
            "id": option["id"],
            "label": option["label"],
            "cost_band": option["cost_band"],
            "source": {"id": option["source_id"], **source} if source else None,
        })
    return options


async def _coach_notes(
    session_id: str,
    profile: HouseholdProfile,
    candidates: list[dict],
    model=None,
) -> tuple[dict[str, str], list[str]]:
    """Personalised wording for each candidate, verified. Falls back to the KB."""
    flagged: list[str] = []
    wanted = [c for c in candidates if (session_id, c["id"]) not in _NOTES]

    if wanted:
        try:
            result = await get_coach(model).run(
                coach_prompt(profile, wanted), deps=CoachDeps(profile=profile)
            )
            items = [{"step_id": n.step_id, "why": n.why} for n in result.output.notes]
            kept, plan_flags = verifier.verify_plan(items, {c["id"] for c in wanted})
            flagged.extend(plan_flags)
            for item in kept:
                _NOTES[(session_id, item["step_id"])] = item["why"]
        except Exception as exc:  # the app still works without the Coach
            flagged.append(f"coach unavailable, using knowledge-base wording ({type(exc).__name__})")

    notes: dict[str, str] = {}
    for candidate in candidates:
        cached = _NOTES.get((session_id, candidate["id"]))
        if not cached:
            module = kb.guidance_module(candidate["id"])
            cached = module["summary"] if module else ""
        notes[candidate["id"]] = cached
    return notes, flagged


async def build_plan(conn, session_id: str, model=None) -> dict:
    """The score, the three next steps, and everything the UI needs to show them."""
    answers = chat.load_answers(conn, session_id)
    profile = survey.build_profile(answers)
    baseline = survey.baseline_answers(answers)
    completed = db.completed_steps(conn, session_id)

    result = score_readiness(profile, baseline)
    steps = rank_next_steps(profile, baseline, completed)

    candidates = [{"id": s.id, "title": s.title, "points_gain": s.points_gain} for s in steps]
    notes, flagged = await _coach_notes(session_id, profile, candidates, model)

    step_payload = []
    for step in steps:
        raw = kb.step_by_id(step.id) or {}
        why_check = verifier.check_text(notes.get(step.id, ""), context=f"why for {step.id}")
        flagged.extend(why_check.flagged)
        step_payload.append({
            "id": step.id,
            "title": step.title,
            "points_gain": step.points_gain,
            "why": why_check.text,
            "est_minutes": step.est_minutes,
            "est_cost_band": step.est_cost_band,
            "how_to": step.how_to,
            "self_check": step.self_check,
            "sources": _resolve_sources(step.source_ids),
            "cheap_options": _resolve_cheap_options(step.cheap_option_ids),
            "medical_note": raw.get("medical_note"),
        })

    return {
        "score": result.score,
        "label": result.label,
        "earned": result.earned,
        "max_points": result.max_points,
        "breakdown": [b.model_dump() for b in result.breakdown],
        "steps": step_payload,
        "completed_step_ids": sorted(completed),
        "local_resources": get_local_resources(profile.state),
        "quantities": calc_quantities(profile),
        "rubric_note": kb.rubric_note(),
        "disclaimer": verifier.MEDICAL_DISCLAIMER,
        "flagged": flagged,
    }


def complete_step(conn, session_id: str, step_id: str, checked_item_ids: list[str]) -> dict:
    """Mark the self-checked items as done. Returns the score before and after.

    Only the items the user actually ticked are credited, so a phased step like
    the kit can be completed a piece at a time without overstating readiness.
    """
    step = kb.step_by_id(step_id)
    if not step:
        raise KeyError(step_id)

    answers = chat.load_answers(conn, session_id)
    profile = survey.build_profile(answers)
    before = score_readiness(profile, survey.baseline_answers(answers)).score

    valid = set(step["rubric_item_ids"])
    credited = [item for item in checked_item_ids if item in valid]
    for item_id in credited:
        answers[item_id] = "yes"
        db.save_answer(conn, session_id, item_id, '"yes"')

    after_answers = survey.baseline_answers(answers)
    after = score_readiness(profile, after_answers).score

    # The step only leaves the list once every item on it is done.
    if all(after_answers.get(i) == "yes" for i in valid):
        db.complete_step(conn, session_id, step_id)

    db.record_score(conn, session_id, after)
    db.log_event(conn, session_id, "step_completed", {
        "step_id": step_id,
        "items": credited,
        "score_before": before,
        "score_after": after,
    })

    return {"step_id": step_id, "score_before": before, "score_after": after,
            "delta": round(after - before, 2), "credited": credited}
