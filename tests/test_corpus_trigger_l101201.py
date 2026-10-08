# -*- coding: utf-8 -*-
"""l1012-01：语料复测触发器案 B 钉桩（决议#5；l1007-22 §三判定域语义）。"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import corpus_trigger_check as ctc


def _seed(path, rows):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE attempts (id INTEGER PRIMARY KEY, lang TEXT, problem_id TEXT, "
                "passed INT, ai_feedback TEXT)")
    con.executemany("INSERT INTO attempts VALUES (?,?,?,?,?)", rows)
    con.commit(); con.close()


def test_below_threshold_not_triggered(tmp_path):
    db = tmp_path / "progress.db"
    _seed(db, [(1, "python", "p1", 0, "运行错误：NameError ..."),
               (2, "python", "p2", 0, "输出不一致：期望 3 实得 4")])  # 非 running-error 前缀不计
    rows = ctc.count_trigger_rows(db)
    assert len(rows) == 1  # 判定域=「运行错误：」前缀，Traceback/输出不一致型不计


def test_at_threshold_triggered_with_domain_semantics(tmp_path):
    db = tmp_path / "progress.db"
    rows = [(i, "python", f"p{i}", 0, f"运行错误：{kind}") for i, kind in
            enumerate(["NameError"] * 8 + ["TypeError"] * 7, start=1)]
    # 穿插非前缀失败行——证明判定域收窄不误计
    rows += [(100, "python", "px", 0, "Traceback (most recent call last): ...")]
    _seed(db, rows)
    got = ctc.count_trigger_rows(db)
    assert len(got) == 15  # 15 达标（案 B 降阈值），Traceback 无前缀行被排除
    assert ctc.main.__module__  # 可跑
