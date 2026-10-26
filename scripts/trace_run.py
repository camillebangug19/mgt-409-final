#!/usr/bin/env python3
"""Trace one complete run end to end (REQUIREMENTS.md 15).

Writes docs/traced_run.txt showing every stage in order:
survey turns -> score -> Coach -> verifier -> final steps -> completing a step.

    cd backend && ./.venv/bin/python ../scripts/trace_run.py
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

PERSONA = [
    "", "2", "Adult", "Older adult (65+)", "Cane or walker", "Oxygen",
    "Yes, one person", "No pets", "32399", "FL", "Apartment", "No",
]
BASELINE = {"water": "Yes", "medication": "Partly", "backup power": "No",
            "transport": "No", "drive": "No", "leave": "No"}

OUT: list[str] = []


def say(line: str = "") -> None:
    OUT.append(line)
    print(line, flush=True)


def rule(title: str) -> None:
    say()
    say("=" * 78)
    say(title)
    say("=" * 78)


async def main() -> int:
    os.environ["READYHOME_DB"] = str(Path(tempfile.mkdtemp()) / "trace.db")
    from app import chat, db, kb, plan, survey, verifier
    from app.agents.coach import CoachDeps, coach_prompt
    from app.scoring import rank_next_steps, score_readiness

    db.init_db()
    sid = "trace"
    with db.session_db() as conn:
        db.create_session(conn, sid)

    rule("STAGE 1 — SURVEY TURNS  (Survey Bot agent, gpt-6-luna)")
    say("Household: 2 people, one an older adult using a walker and home oxygen who")
    say("takes daily medication. No pets. Apartment in Florida. No car.")
    say()

    scripted = iter(PERSONA)
    turns = 0
    while turns < 45:
        with db.session_db() as conn:
            answers = chat.load_answers(conn, sid)
            state = survey.survey_state(answers)
            if state["done"]:
                break
            try:
                msg = next(scripted)
            except StopIteration:
                hint = (state["next_question_about"] or "").lower()
                msg = next((v for k, v in BASELINE.items() if k in hint), "Partly")
            before = set(answers)
            resp = await chat.run_turn(conn, sid, msg)
            after = chat.load_answers(conn, sid)
        turns += 1
        recorded = sorted(set(after) - before)
        say(f"[turn {turns:>2}] user: {msg or '(opens the chat)'}")
        say(f"           bot ({resp.mood}): {resp.message}")
        if recorded:
            say(f"           recorded: " + ", ".join(f"{k}={after[k]!r}" for k in recorded))
        say()

    say(f"Survey finished in {turns} turns.")

    with db.session_db() as conn:
        answers = chat.load_answers(conn, sid)
    profile = survey.build_profile(answers)
    baseline = survey.baseline_answers(answers)

    rule("STAGE 2 — SCORING  (plain Python, no model call)")
    result = score_readiness(profile, baseline)
    say(f"Applicable rubric items : {len(result.applicable_item_ids)} of {len(kb.rubric_items())}")
    say(f"  excluded as not applicable: "
        f"{sorted({i['id'] for i in kb.rubric_items()} - set(result.applicable_item_ids))}")
    say(f"Earned / max            : {result.earned} / {result.max_points}")
    say(f"Score                   : 1 + 9 x ({result.earned}/{result.max_points}) "
        f"= {result.score}  ({result.label})")
    for b in result.breakdown:
        say(f"    {b.category:<16} {b.earned:>5} / {b.max_points}")

    rule("STAGE 3 — RANKING  (plain Python, no model call)")
    steps = rank_next_steps(profile, baseline)
    for s in rank_next_steps(profile, baseline, limit=99):
        mark = "  <= shown" if s.id in {x.id for x in steps} else ""
        say(f"  {s.id:<22} +{s.points_gain:<5} {s.est_minutes:>3} min  {s.est_cost_band}{mark}")

    rule("STAGE 4 — COACH  (second agent, writes the wording only)")
    cands = [{"id": s.id, "title": s.title, "points_gain": s.points_gain} for s in steps]
    say("Prompt sent to the Coach:")
    for line in coach_prompt(profile, cands).splitlines():
        say(f"  | {line}")
    say()
    agent = plan.get_coach()
    coach_result = await agent.run(coach_prompt(profile, cands), deps=CoachDeps(profile=profile))
    say("Raw Coach output:")
    for n in coach_result.output.notes:
        say(f"  - {n.step_id}: {n.why}")
    say(f"Coach tokens: in={coach_result.usage.input_tokens} out={coach_result.usage.output_tokens}")

    rule("STAGE 5 — VERIFIER  (plain Python, runs before anything is shown)")
    allowed = {c["id"] for c in cands}
    kept, flagged = verifier.verify_plan(
        [{"step_id": n.step_id, "why": n.why} for n in coach_result.output.notes], allowed)
    say(f"Steps the ranker allows : {sorted(allowed)}")
    say(f"Steps the Coach returned: {[n.step_id for n in coach_result.output.notes]}")
    say(f"Kept after verification : {[k['step_id'] for k in kept]}")
    say(f"Flagged and removed     : {flagged or 'nothing — the Coach stayed inside the rules'}")
    say()
    say("Same check against a deliberately bad Coach reply:")
    bad = [{"step_id": "buy-a-bunker", "why": "Order one at https://not-real.example.com"},
           {"step_id": "meds-7day", "why": "Take 400 mg twice a day"}]
    bad_kept, bad_flagged = verifier.verify_plan(bad, allowed)
    for f in bad_flagged:
        say(f"  REMOVED: {f}")
    say(f"  survived: {[k['step_id'] + ' -> ' + k['why'] for k in bad_kept]}")

    rule("STAGE 6 — WHAT THE USER SEES, AND COMPLETING A STEP")
    with db.session_db() as conn:
        built = await plan.build_plan(conn, sid)
        say(f"Score {built['score']}/10 ({built['label']})")
        for s in built["steps"]:
            say(f"  +{s['points_gain']}  {s['title']}")
            say(f"        why: {s['why']}")
            say(f"        sources: {[x['title'] for x in s['sources']]}")
        first = built["steps"][0]
        done = plan.complete_step(conn, sid, first["id"],
                                  [i["item_id"] for i in first["self_check"]])
        say()
        say(f"Completing '{first['id']}': score {done['score_before']} -> {done['score_after']} "
            f"(advertised +{first['points_gain']})")
        after_plan = await plan.build_plan(conn, sid)
        say(f"Next three now: {[s['id'] for s in after_plan['steps']]}")
        usage = plan.usage_summary(conn, sid)

    rule("TOTAL MEASURED COST FOR THIS RUN")
    for a in usage["agents"]:
        say(f"  {a['agent']:<12} input {a['input_tokens']:>8,}  cached {a['cached_tokens']:>8,}"
            f"  output {a['output_tokens']:>6,}")
    t = usage["totals"]
    say(f"  {'TOTAL':<12} input {t['input_tokens']:>8,}  cached {t['cached_tokens']:>8,}"
        f"  output {t['output_tokens']:>6,}   est ${t['cost_usd']:.4f}")
    say()
    say("Token counts are measured. Dollar rates are an assumption; see pricing.py.")

    out = ROOT / "docs" / "traced_run.txt"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(OUT) + "\n", encoding="utf-8")
    print(f"\nwritten to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
