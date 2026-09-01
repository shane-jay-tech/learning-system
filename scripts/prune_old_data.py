"""数据保留策略维护脚本：清理无限增长的 attempts / learning_events。

attempts 和 learning_events 是 append-only 表，长期使用会线性膨胀。
本脚本按「时间 + 每题保留最近 N 次」双重策略清理：

- learning_events：只删除 created_at 早于 --days 的事件
  （热力图只回看 90 天，推荐漏斗可选全部——保留 365 天足够）；
- attempts：删除 ts 早于 --days 且非「每题最近 --keep-per-problem 次」的记录
  （错题本/最近活动只依赖最近一次；每日趋势回看 ≤90 天）。

用法：
    python scripts/prune_old_data.py              # 干跑，只报将删除的行数
    python scripts/prune_old_data.py --apply      # 真正执行
    python scripts/prune_old_data.py --days 180 --keep-per-problem 10 --apply
    python scripts/prune_old_data.py --json       # JSON 输出
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 窗口函数一次算出「每题按 id 倒序的排名」，rn > keep 且时间过期的才删。
# （注意不能用 NOT IN 子查询：子查询为空时 NOT IN 恒真，会把全部旧记录误删）
_SELECT_CANDIDATES = (
    "SELECT id FROM ("
    "  SELECT id, ts,"
    "         ROW_NUMBER() OVER (PARTITION BY lang, problem_id ORDER BY id DESC) AS rn"
    "  FROM attempts"
    ") WHERE rn > ? AND ts < datetime('now', ?)"
)


def prune(days: int = 365, keep_per_problem: int = 20,
          apply: bool = False, json_output: bool = False) -> dict:
    from core.progress import ProgressDAO

    dao = ProgressDAO()
    try:
        event_rows = dao.conn.execute(
            "SELECT COUNT(*) FROM learning_events WHERE created_at < datetime('now', ?)",
            (f"-{int(days)} days",),
        ).fetchone()[0]

        attempt_rows = dao.conn.execute(
            f"SELECT COUNT(*) FROM attempts WHERE id IN ({_SELECT_CANDIDATES})",
            (int(keep_per_problem), f"-{int(days)} days"),
        ).fetchone()[0]

        if apply:
            with dao.conn:
                dao.conn.execute(
                    "DELETE FROM learning_events WHERE created_at < datetime('now', ?)",
                    (f"-{int(days)} days",),
                )
                dao.conn.execute(
                    f"DELETE FROM attempts WHERE id IN ({_SELECT_CANDIDATES})",
                    (int(keep_per_problem), f"-{int(days)} days"),
                )
            dao.checkpoint_wal()
            try:
                dao.conn.execute("VACUUM")
            except Exception:
                pass  # 有活跃连接时 VACUUM 可能失败，非致命

        summary = {
            "mode": "apply" if apply else "dry_run",
            "days": int(days),
            "keep_per_problem": int(keep_per_problem),
            "learning_events_to_delete": event_rows,
            "attempts_to_delete": attempt_rows,
        }
        if json_output:
            print(json.dumps(summary, indent=2))
        else:
            print(f"learning_events 早于 {days} 天：{event_rows} 条待删")
            print(f"attempts 早于 {days} 天且超出每题保留 {keep_per_problem} 次：{attempt_rows} 条待删")
            print("已执行删除 + checkpoint + VACUUM" if apply else "干跑完成——用 --apply 真正执行")
        return summary
    finally:
        dao.close()


def main():
    parser = argparse.ArgumentParser(description="Prune old attempts/events")
    parser.add_argument("--days", type=int, default=365, help="保留最近 N 天（默认 365）")
    parser.add_argument("--keep-per-problem", type=int, default=20,
                        help="每道题额外保留的最近作答次数（默认 20）")
    parser.add_argument("--apply", action="store_true", help="真正执行删除")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()
    prune(days=args.days, keep_per_problem=args.keep_per_problem,
          apply=args.apply, json_output=args.json)


if __name__ == "__main__":
    main()
