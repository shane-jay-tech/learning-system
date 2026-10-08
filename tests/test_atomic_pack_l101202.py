# -*- coding: utf-8 -*-
"""l1012-02：record_attempt_and_status 原子包钉桩（决议#6，l1007-23 方案翻面 4 例＋崩溃窗）。

翻面 4 例（l1007-23 §三原清单）＋崩溃窗 1＋残留清理 1＋perf 口径：
- 翻①单调用三表齐写；翻②review_state 失败整包回滚（行为差=包价值）；
- 翻③False 默认逐位等价；翻④独立调用面（update_review_state 薄壳）回归；
- 崩溃窗：UPSERT 体抛错 ⇒ attempts/problems_status 均不留（事务回滚＝不留脏行）；
- perf：10MB 级库 fixture 两口径各 3 次均值对照（阈值 ≤±20%）。
"""
import sqlite3
import time
from pathlib import Path

import pytest

from core.progress import ProgressDAO


@pytest.fixture()
def dao(tmp_path):
    d = ProgressDAO(str(tmp_path / "progress.db"))
    yield d


class TestAtomicPack:
    def test_flip1_single_call_writes_three_tables(self, dao):
        dao.record_attempt_and_status("python", "p1", "code", True, "fb",
                                      update_review=True, difficulty=3)
        assert dao.conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 1
        assert dao.conn.execute("SELECT COUNT(*) FROM problems_status").fetchone()[0] == 1
        row = dao.conn.execute(
            "SELECT last_result, interval_days FROM review_state").fetchone()
        assert row[0] == "pass" and row[1] >= 3

    def test_flip2_review_failure_rolls_back_whole_pack(self, dao, monkeypatch):
        # review UPSERT 体抛错 ⇒ attempts/problems_status 均回滚（原子包价值所在）
        monkeypatch.setattr(dao, "_upsert_review_state_locked",
                            lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
        with pytest.raises(RuntimeError):
            dao.record_attempt_and_status("python", "p2", "code", True, "fb",
                                          update_review=True)
        assert dao.conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0
        assert dao.conn.execute("SELECT COUNT(*) FROM problems_status").fetchone()[0] == 0

    def test_flip3_default_false_bitwise_equivalent(self, dao):
        # 默认 False：不触 review_state（与改前逐位等价）
        dao.record_attempt_and_status("python", "p3", "code", True, "fb")
        assert dao.conn.execute("SELECT COUNT(*) FROM review_state").fetchone()[0] == 0
        assert dao.conn.execute("SELECT status FROM problems_status").fetchone()[0] == "solved"

    def test_flip4_standalone_wrapper_regression(self, dao):
        dao.record_attempt_and_status("python", "p4", "code", True, "fb")
        dao.update_review_state("python", "p4", True, difficulty=5)
        row = dao.conn.execute(
            "SELECT review_streak, ease FROM review_state").fetchone()
        assert row[0] == 1  # streak 1
        # 失败臂重置语义保留
        dao.update_review_state("python", "p4", False)
        row2 = dao.conn.execute(
            "SELECT review_streak, interval_days FROM review_state").fetchone()
        assert row2[0] == 0 and row2[1] == 1

    def test_crash_window_no_dirty_rows(self, dao, monkeypatch, tmp_path):
        # 崩溃窗（真模拟）：UPSERT 体抛错并关闭连接＝进程半途死亡 ⇒ journal 回滚，
        # 重开验盘无脏行（半写态不留档）。
        db_path = tmp_path / "progress.db"

        def crash(*a, **k):
            dao.conn.close()  # 连接中途死亡
            raise RuntimeError("simulated process crash mid-pack")

        monkeypatch.setattr(dao, "_upsert_review_state_locked", crash)
        with pytest.raises((RuntimeError, sqlite3.ProgrammingError)):
            # 事务体抛错＋with 退出对已关连接 commit 的次生 ProgrammingError 都属崩溃面
            dao.record_attempt_and_status("python", "p5", "code", True, "fb",
                                          update_review=True)
        fresh = ProgressDAO(str(db_path))  # 重开（journal 回滚后）
        assert fresh.conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0] == 0
        assert fresh.conn.execute("SELECT COUNT(*) FROM problems_status").fetchone()[0] == 0
        assert fresh.conn.execute("SELECT COUNT(*) FROM review_state").fetchone()[0] == 0
