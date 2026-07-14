"""Backfill learning_events from historical attempts table.

Usage:
    python scripts/backfill_events.py              # Dry run
    python scripts/backfill_events.py --apply      # Actually insert events
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def backfill(apply: bool = False, json_output: bool = False):
    import json as _json
    from core.progress import ProgressDAO

    dao = ProgressDAO()
    try:
        existing = dao.event_count()

        rows = dao.conn.execute(
            "SELECT id, lang, problem_id, passed, ts FROM attempts ORDER BY id"
        ).fetchall()

        already_backfilled = set()
        if existing > 0:
            bf = dao.conn.execute(
                "SELECT event_type, lang, problem_id, local_date FROM learning_events "
                "WHERE event_type IN ('attempt_submitted', 'problem_passed', 'problem_failed')"
            ).fetchall()
            already_backfilled = {(r[0], r[1], r[2], r[3]) for r in bf}

        to_insert = []
        for row in rows:
            _id, lang, pid, passed, ts = row
            local_date = ts[:10] if ts else None
            if not local_date:
                continue

            key_submit = ("attempt_submitted", lang, pid, local_date)
            if key_submit not in already_backfilled:
                to_insert.append(("attempt_submitted", lang, None, pid, None, None,
                                  f'{{"passed": {"true" if passed else "false"}}}', local_date))

            event_type = "problem_passed" if passed else "problem_failed"
            key_result = (event_type, lang, pid, local_date)
            if key_result not in already_backfilled:
                to_insert.append((event_type, lang, None, pid, None, None, None, local_date))

        created = 0
        if apply and to_insert:
            with dao.conn:
                dao.conn.executemany(
                    "INSERT INTO learning_events "
                    "(event_type, lang, topic_id, problem_id, path_id, milestone_id, payload_json, local_date) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    to_insert,
                )
            created = len(to_insert)

        final_count = dao.event_count()

        summary = {
            "mode": "apply" if apply else "dry_run",
            "attempts_seen": len(rows),
            "events_before": existing,
            "duplicate_skipped": len(already_backfilled),
            "events_to_create": len(to_insert),
            "created": created,
            "events_after": final_count,
        }

        if json_output:
            print(_json.dumps(summary, indent=2))
        else:
            print(f"Found {len(rows)} historical attempts")
            print(f"Events to insert: {len(to_insert)} (skipping {len(already_backfilled)} existing)")
            if apply:
                print(f"Inserted {created} events.")
            else:
                print("Dry run — use --apply to insert.")
            print(f"Total events now: {final_count}")

        return summary
    finally:
        dao.close()


def main():
    parser = argparse.ArgumentParser(description="Backfill learning events from attempts")
    parser.add_argument("--apply", action="store_true", help="Actually insert events")
    parser.add_argument("--json", action="store_true", help="Output JSON summary")
    args = parser.parse_args()
    backfill(apply=args.apply, json_output=args.json)


if __name__ == "__main__":
    main()
