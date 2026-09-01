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


def _utc_to_local_date(ts: str):
    """attempts.ts 是 UTC，事件表的 local_date 是本地日期——直接取前 10 位会把
    本地凌晨的提交永久归到前一天（时区错位）。"""
    if not ts:
        return None
    try:
        from datetime import datetime, timezone
        dt = datetime.strptime(ts.split('.')[0], "%Y-%m-%d %H:%M:%S")
        dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().date().isoformat()
    except (ValueError, TypeError):
        return None


def backfill(apply: bool = False, json_output: bool = False):
    import json as _json
    from core.progress import ProgressDAO

    dao = ProgressDAO()
    try:
        existing = dao.event_count()

        rows = dao.conn.execute(
            "SELECT id, lang, problem_id, passed, ts FROM attempts ORDER BY id"
        ).fetchall()

        # 按 attempt_id 去重：payload 里带 attempt_id，重跑不会重复插入，
        # 也不会把同题同天的多次提交误判成重复（此前按日期去重会丢记录）
        already_backfilled = set()
        if existing > 0:
            bf = dao.conn.execute(
                "SELECT event_type, lang, problem_id, payload_json FROM learning_events "
                "WHERE event_type IN ('attempt_submitted', 'problem_passed', 'problem_failed')"
            ).fetchall()
            for event_type, lang, pid, payload in bf:
                aid = None
                if payload:
                    try:
                        aid = _json.loads(payload).get("attempt_id")
                    except (ValueError, TypeError):
                        aid = None
                if aid is not None:
                    already_backfilled.add((event_type, lang, pid, aid))

        to_insert = []
        for row in rows:
            _id, lang, pid, passed, ts = row
            local_date = _utc_to_local_date(ts)
            if not local_date:
                continue

            key_submit = ("attempt_submitted", lang, pid, _id)
            if key_submit not in already_backfilled:
                to_insert.append(("attempt_submitted", lang, None, pid, None, None,
                                  _json.dumps({"passed": bool(passed), "attempt_id": _id},
                                              ensure_ascii=False),
                                  local_date))

            event_type = "problem_passed" if passed else "problem_failed"
            key_result = (event_type, lang, pid, _id)
            if key_result not in already_backfilled:
                to_insert.append((event_type, lang, None, pid, None, None,
                                  _json.dumps({"attempt_id": _id}, ensure_ascii=False),
                                  local_date))

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
