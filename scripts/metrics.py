#!/usr/bin/env python3
"""Print the success metrics from SQLite (REQUIREMENTS.md 6.4).

North-star metric: steps completed per user.
Also: survey completion rate, and score change from first to latest.

    cd backend && ./.venv/bin/python ../scripts/metrics.py
    ./.venv/bin/python ../scripts/metrics.py --db /path/to/readyhome.db
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app import db, events  # noqa: E402


def _one(conn, sql: str, default=0):
    row = conn.execute(sql).fetchone()
    value = row[0] if row else None
    return default if value is None else value


def gather(conn) -> dict:
    sessions = _one(conn, "SELECT COUNT(*) FROM sessions")
    started = _one(conn, "SELECT COUNT(DISTINCT session_id) FROM events WHERE name = 'survey_started'")
    completed = _one(conn, "SELECT COUNT(*) FROM sessions WHERE survey_done = 1")
    steps = _one(conn, "SELECT COUNT(*) FROM step_completions")
    with_steps = _one(conn, "SELECT COUNT(DISTINCT session_id) FROM step_completions")

    improved = conn.execute(
        """SELECT first_score, latest_score FROM sessions
            WHERE first_score IS NOT NULL AND latest_score IS NOT NULL"""
    ).fetchall()
    deltas = [r["latest_score"] - r["first_score"] for r in improved]

    tokens = conn.execute(
        """SELECT COALESCE(SUM(input_tokens), 0) AS i,
                  COALESCE(SUM(cached_tokens), 0) AS c,
                  COALESCE(SUM(output_tokens), 0) AS o FROM usage"""
    ).fetchone()

    return {
        "sessions": sessions,
        "started": started,
        "completed": completed,
        "completion_rate": (completed / started * 100) if started else 0.0,
        "steps": steps,
        "with_steps": with_steps,
        "steps_per_user": (steps / sessions) if sessions else 0.0,
        "steps_per_finisher": (steps / completed) if completed else 0.0,
        "scored": len(improved),
        "avg_first": (sum(r["first_score"] for r in improved) / len(improved)) if improved else 0.0,
        "avg_latest": (sum(r["latest_score"] for r in improved) / len(improved)) if improved else 0.0,
        "avg_delta": (sum(deltas) / len(deltas)) if deltas else 0.0,
        "improved": sum(1 for d in deltas if d > 0),
        "events": events.counts(conn),
        "tokens": {"input": tokens["i"], "cached": tokens["c"], "output": tokens["o"]},
        "popular": conn.execute(
            """SELECT step_id, COUNT(*) AS n FROM step_completions
                GROUP BY step_id ORDER BY n DESC LIMIT 5"""
        ).fetchall(),
    }


def report(m: dict) -> str:
    lines = [
        "ReadyHome metrics",
        "=" * 46,
        "",
        "NORTH STAR",
        f"  Steps completed per user     {m['steps_per_user']:.2f}",
        f"    ({m['steps']} steps across {m['sessions']} sessions)",
        f"  Steps per finished survey    {m['steps_per_finisher']:.2f}",
        f"  Sessions with >= 1 step      {m['with_steps']}",
        "",
        "SURVEY COMPLETION",
        f"  Started                      {m['started']}",
        f"  Completed                    {m['completed']}",
        f"  Completion rate              {m['completion_rate']:.1f}%",
        "",
        "SCORE CHANGE (first -> latest)",
        f"  Sessions scored              {m['scored']}",
        f"  Average first score          {m['avg_first']:.2f}",
        f"  Average latest score         {m['avg_latest']:.2f}",
        f"  Average change               {m['avg_delta']:+.2f}",
        f"  Sessions that improved       {m['improved']}",
        "",
        "EVENTS",
    ]
    lines += [f"  {name:<28} {count}" for name, count in m["events"].items()]
    lines += [
        "",
        "MOST COMPLETED STEPS",
    ]
    lines += (
        [f"  {r['step_id']:<28} {r['n']}" for r in m["popular"]]
        if m["popular"]
        else ["  (none yet)"]
    )
    lines += [
        "",
        "TOKENS USED (all time)",
        f"  Input                        {m['tokens']['input']:,}",
        f"  Cached input                 {m['tokens']['cached']:,}",
        f"  Output                       {m['tokens']['output']:,}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=None, help="path to readyhome.db")
    args = parser.parse_args()

    path = args.db or db.db_path()
    if not Path(path).exists():
        print(f"No database at {path}. Run the app first.", file=sys.stderr)
        return 1

    with db.session_db(path) as conn:
        print(report(gather(conn)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
