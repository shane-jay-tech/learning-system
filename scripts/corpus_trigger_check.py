#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语料积累复测触发检查（l1012-01，决议#5 案 B 降阈采择；l1007-22 §三原文落码）。

触发条件（案 B，2026-10-09 用户采择）：
  attempts 中 passed=0 且 ai_feedback 以「运行错误：」开头（stderr 摘要稳定载体，
  judge.py diff_hint 前缀——不依赖 Traceback 字样恰好幸存）的失败行 **≥15**。

用法：python scripts/corpus_trigger_check.py [--db PATH] [--threshold 15]
输出：计数/阈值/判定 + 达标时列出样本（供 p50/p90/p99 粗版密度比对取材）。
零写库（只读连接）。
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

THRESHOLD = 15  # 案 B 降阈值（l1007-22 §三：原 30 → 15）
PREFIX = "运行错误："


def count_trigger_rows(db: Path) -> list:
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        return con.execute(
            "SELECT id, lang, problem_id, substr(ai_feedback, 1, 80) "
            "FROM attempts WHERE passed = 0 AND ai_feedback LIKE ? || '%'",
            (PREFIX,),
        ).fetchall()
    finally:
        con.close()


def main() -> int:
    ap = argparse.ArgumentParser(description="语料积累复测触发检查（案 B 口径，只读）")
    ap.add_argument("--db", default=str(Path(__file__).resolve().parents[1] / "data" / "progress.db"))
    ap.add_argument("--threshold", type=int, default=THRESHOLD)
    a = ap.parse_args()
    db = Path(a.db)
    if not db.exists():
        print(f"[trigger] progress.db 不存在（{db}）——无样本可判，视为未触发")
        return 0
    rows = count_trigger_rows(db)
    hit = len(rows) >= a.threshold
    print(f"[trigger] 运行错误型失败行 = {len(rows)} / 阈值 {a.threshold}（案 B） ⇒ "
          f"{'达标，可发起复测' if hit else '未达标，继续积累'}")
    for r in rows:
        print(f"  sample: attempts#{r[0]} {r[1]}/{r[2]} :: {r[3]}…")
    return 0 if hit else 1


if __name__ == "__main__":
    sys_exit = main()
    raise SystemExit(sys_exit)
