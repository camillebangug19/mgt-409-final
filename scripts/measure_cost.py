#!/usr/bin/env python3
"""Measure what one full ReadyHome session costs (REQUIREMENTS.md 15, report §5).

Runs a complete survey against the live model with a throwaway database, then
reports measured token counts and the estimated cost. Set
READYHOME_HISTORY_TURNS to compare history strategies.

    cd backend
    READYHOME_HISTORY_TURNS=999 ./.venv/bin/python ../scripts/measure_cost.py --label "full history"
    READYHOME_HISTORY_TURNS=4   ./.venv/bin/python ../scripts/measure_cost.py --label "trimmed history"
"""

import argparse
import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

# Persona B from the test fixtures: grandparent on oxygen, no car, Florida.
PERSONA_B = [
    "", "2", "Adult", "Older adult (65+)", "Cane or walker", "Oxygen",
    "Yes, one person", "No pets", "32399", "FL", "Apartment", "No",
]
BASELINE = {"water": "Yes", "medication": "Partly", "backup power": "No",
            "transport": "No", "drive": "No", "leave": "No"}


async def run(label: str) -> dict:
    os.environ["READYHOME_DB"] = str(Path(tempfile.mkdtemp()) / "measure.db")

    from app import chat, db, plan, survey

    db.init_db()
    session_id = "measure"
    with db.session_db() as conn:
        db.create_session(conn, session_id)

    started = time.time()
    turns = 0
    scripted = iter(PERSONA_B)

    while turns < 45:
        with db.session_db() as conn:
            state = survey.survey_state(chat.load_answers(conn, session_id))
            if state["done"]:
                break
            try:
                message = next(scripted)
            except StopIteration:
                hint = (state["next_question_about"] or "").lower()
                message = next(
                    (v for k, v in BASELINE.items() if k in hint), "Partly"
                )
            await chat.run_turn(conn, session_id, message)
        turns += 1

    survey_seconds = time.time() - started

    with db.session_db() as conn:
        result = await plan.build_plan(conn, session_id)
        usage = plan.usage_summary(conn, session_id)

    return {
        "label": label,
        "history_turns": chat.HISTORY_TURNS,
        "survey_turns": turns,
        "survey_seconds": round(survey_seconds, 1),
        "score": result["score"],
        "steps_offered": [s["id"] for s in result["steps"]],
        "usage": usage,
    }


def show(data: dict) -> None:
    u = data["usage"]
    print(f"\n{'=' * 62}\n{data['label']}  (history_turns={data['history_turns']})\n{'=' * 62}")
    print(f"  survey turns        {data['survey_turns']}")
    print(f"  wall clock          {data['survey_seconds']}s")
    print(f"  final score         {data['score']}")
    print(f"  steps offered       {', '.join(data['steps_offered'])}")
    print(f"\n  {'agent':<14}{'input':>12}{'cached':>12}{'output':>10}{'est $':>10}")
    for row in u["agents"]:
        print(f"  {row['agent']:<14}{row['input_tokens']:>12,}{row['cached_tokens']:>12,}"
              f"{row['output_tokens']:>10,}{row['cost_usd']:>10.4f}")
    t = u["totals"]
    print(f"  {'TOTAL':<14}{t['input_tokens']:>12,}{t['cached_tokens']:>12,}"
          f"{t['output_tokens']:>10,}{t['cost_usd']:>10.4f}")
    p = u["projections"]
    print(f"\n  per session ${p['per_session']}  |  100 users ${p['per_100_users']}"
          f"  |  10,000 users ${p['per_10000_users']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="measured run")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    data = asyncio.run(run(args.label))
    show(data)

    out = args.out or ROOT / "docs" / "tokenomics.json"
    out.parent.mkdir(exist_ok=True)
    existing = json.loads(out.read_text()) if out.exists() else []
    existing = [r for r in existing if r["label"] != data["label"]]
    existing.append(data)
    out.write_text(json.dumps(existing, indent=2))
    print(f"\n  saved to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
