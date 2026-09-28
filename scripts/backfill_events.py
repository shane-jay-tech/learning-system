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


def backfill(apply: bool = False, json_output: bool = False, db_path=None):
    import json as _json
    from collections import Counter
    from core.progress import ProgressDAO

    # db_path 显式注库（l927-13）：回填测试需要"确定指到沙盒库"的硬手段。
    # 此前只靠 LS_PROGRESS_DB 一道缝隔离，而 20260925-154239 的 +30 行事故正是
    # 夹具的 monkeypatch.undo() 把那道 env 撤掉后发生的 ⇒ 加参数，不改默认行为。
    # 未注库时保持**旧的无参构造**（`tests/test_scripts.py` 把 ProgressDAO monkeypatch 成
    # 零参 lambda，多传一个位置参就 TypeError）；pytest 态下无参构造已由 A5① 闸拦住。
    dao = ProgressDAO(db_path) if db_path else ProgressDAO()
    try:
        existing = dao.event_count()

        rows = dao.conn.execute(
            "SELECT id, lang, problem_id, passed, ts FROM attempts ORDER BY id"
        ).fetchall()

        # 去重键（l927-13 修 §D 缺陷）——分层两套键，缺一个都不对：
        #   ① 精确键：payload 带 attempt_id 的行 → (event_type, lang, problem_id, attempt_id)。
        #      这条保住"同题同天的多次提交不被误判成重复"（原注释的诉求）。
        #   ② 退化键：payload 不带 attempt_id 的老行（2026-07 年代的回填产物）→
        #      (event_type, lang, problem_id, local_date) 的**计数额度**，一行一条额度。
        # 只按 ① 判重的旧实现，遇到老行永远判不出重复 ⇒ duplicate_skipped=0、
        # 任何人重跑一次 --apply 就把既有 attempts 整批再复制一遍（热力图当日翻倍），
        # 机理与实测形态见 zcode-bridge/done/20260925-154239-abdf.result.md §D。
        # 按 ② 给老行配额度而不是直接按日期判重，是为了既不重复计数也不丢记录：
        # 老行覆盖不到的第 N 次提交照样补插，且补插的行带 attempt_id，下次走精确键。
        exact_keys = set()
        legacy_quota = Counter()
        legacy_rows = 0
        if existing > 0:
            bf = dao.conn.execute(
                "SELECT event_type, lang, problem_id, payload_json, local_date FROM learning_events "
                "WHERE event_type IN ('attempt_submitted', 'problem_passed', 'problem_failed')"
            ).fetchall()
            for event_type, lang, pid, payload, local_date in bf:
                aid = None
                if payload:
                    try:
                        aid = _json.loads(payload).get("attempt_id")
                    except (ValueError, TypeError):
                        aid = None
                if aid is not None:
                    exact_keys.add((event_type, lang, pid, aid))
                else:
                    # payload_json 为 NULL 或 payload 里没有 attempt_id —— 都是老行形态
                    legacy_quota[(event_type, lang, pid, local_date)] += 1
                    legacy_rows += 1

        to_insert = []
        duplicate_skipped = 0
        for row in rows:
            _id, lang, pid, passed, ts = row
            local_date = _utc_to_local_date(ts)
            if not local_date:
                continue

            event_type = "problem_passed" if passed else "problem_failed"
            candidates = (
                ("attempt_submitted",
                 _json.dumps({"passed": bool(passed), "attempt_id": _id}, ensure_ascii=False)),
                (event_type, _json.dumps({"attempt_id": _id}, ensure_ascii=False)),
            )

            for cand_type, payload in candidates:
                # ① 精确键命中 ⇒ 这笔 attempt 已经回填过
                if (cand_type, lang, pid, _id) in exact_keys:
                    duplicate_skipped += 1
                    continue
                # ② 老行额度命中 ⇒ 已有一行代表它（消费额度，保住多次提交各占一行）
                quota_key = (cand_type, lang, pid, local_date)
                if legacy_quota[quota_key] > 0:
                    legacy_quota[quota_key] -= 1
                    duplicate_skipped += 1
                    continue
                to_insert.append((cand_type, lang, None, pid, None, None, payload, local_date))

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
            # duplicate_skipped 改为"实际跳过的候选笔数"（旧口径是去重索引大小，
            # 恰好让 §D 那次事故自报 0、掩盖了"一笔都没判出来"的事实）
            "duplicate_skipped": duplicate_skipped,
            "dedup_exact_keys": len(exact_keys),
            "legacy_events_without_attempt_id": legacy_rows,
            "events_to_create": len(to_insert),
            "created": created,
            "events_after": final_count,
        }

        if json_output:
            print(_json.dumps(summary, indent=2))
        else:
            print(f"Found {len(rows)} historical attempts")
            print(f"Events to insert: {len(to_insert)} (skipping {duplicate_skipped} duplicates)")
            if legacy_rows:
                print(f"Matched against {legacy_rows} legacy events without attempt_id")
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
    parser.add_argument("--db", default=None,
                        help="Explicit sqlite path (default: LS_PROGRESS_DB or data/progress.db)")
    args = parser.parse_args()
    backfill(apply=args.apply, json_output=args.json, db_path=args.db)


if __name__ == "__main__":
    main()
