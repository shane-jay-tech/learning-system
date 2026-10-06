# -*- coding: utf-8 -*-
"""l1006-03 幂等三件套定向例（l1004-07；用户 2026-10-06 拍板全落）。

② submission 窗口幂等（judge.py SUBMISSION_IDEMPOTENCY_WINDOW_MIN=10）；
③ 事件层当日去重（emit_event dedup_code_hash，报表 1:N→1:1、attempts/SRS 不动）；
④ payload 归一（attempt_id＋code_hash，与 backfill_events 形态一致）。

复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_submission_idempotency_l100603.py -q
"""
import json

import pytest

from core.progress import ProgressDAO

PROBLEM = {
    "id": "python/idem/1",
    "title": "t",
    "statement": "s",
    "expected_output": "Hello\n",
}
CODE = 'print("Hello")'
CHANGED = 'print("Hello", flush=True)'


@pytest.fixture
def dao(tmp_path):
    d = ProgressDAO(str(tmp_path / "idem.db"))
    yield d
    d.close()


@pytest.fixture
def no_llm(monkeypatch):
    monkeypatch.setattr("core.ai_review._call_chain", lambda *a, **kw: ("", None))


def _count(dao, sql, *args):
    return dao.conn.execute(sql, args).fetchone()[0]


def test_重放窗口内返回首次判定且零新行(dao, no_llm):
    from core.judge import judge
    r1 = judge("python", PROBLEM, CODE, dao=dao)
    assert r1.passed is True
    before = _count(dao, "SELECT COUNT(*) FROM attempts WHERE problem_id=?", PROBLEM["id"])
    r2 = judge("python", PROBLEM, CODE, dao=dao)          # 手抖双击形态
    assert r2.passed is True
    assert "未重复计分" in r2.diff_hint, r2.diff_hint
    assert _count(dao, "SELECT COUNT(*) FROM attempts WHERE problem_id=?", PROBLEM["id"]) == before == 1
    s = dao.conn.execute("SELECT review_streak FROM review_state WHERE problem_id=?", (PROBLEM["id"],)).fetchone()
    assert s[0] == 1, s                                   # SRS 零推进


def test_改码重提交不受幂等挡(dao, no_llm):
    from core.judge import judge
    judge("python", PROBLEM, CODE, dao=dao)
    r2 = judge("python", PROBLEM, CHANGED, dao=dao)       # 代码变了 ⇒ 新结算
    assert r2.passed is True and "未重复计分" not in (r2.diff_hint or "")
    assert _count(dao, "SELECT COUNT(*) FROM attempts WHERE problem_id=?", PROBLEM["id"]) == 2


def test_窗口外重复_attempts两行_事件当日去重_SRS照旧推进(dao, no_llm):
    from core.judge import judge
    judge("python", PROBLEM, CODE, dao=dao)
    # 模拟窗口外：把首击 ts 拨回 20 分钟前（attempts 行保留，重放查询不再命中）
    dao.conn.execute("UPDATE attempts SET ts = datetime('now', '-20 minutes') WHERE problem_id=?", (PROBLEM["id"],))
    dao.conn.commit()
    judge("python", PROBLEM, CODE, dao=dao)
    # ②窗口外允许重新结算 ⇒ attempts 2 行
    assert _count(dao, "SELECT COUNT(*) FROM attempts WHERE problem_id=?", PROBLEM["id"]) == 2
    # ③事件当日去重 ⇒ 报表 1:N→1:1
    assert _count(dao, "SELECT COUNT(*) FROM learning_events WHERE event_type='attempt_submitted' AND problem_id=?", PROBLEM["id"]) == 1
    assert _count(dao, "SELECT COUNT(*) FROM learning_events WHERE event_type='problem_passed' AND problem_id=?", PROBLEM["id"]) == 1
    # ③零 SRS 影响：两次结算 ⇒ streak 2（曲线口径不变）
    s = dao.conn.execute("SELECT review_streak FROM review_state WHERE problem_id=?", (PROBLEM["id"],)).fetchone()
    assert s[0] == 2, s


def test_payload归一带attempt_id与code_hash(dao, no_llm):
    from core.judge import judge
    judge("python", PROBLEM, CODE, dao=dao)
    rows = dao.conn.execute(
        "SELECT event_type, payload_json FROM learning_events "
        "WHERE problem_id=? AND event_type IN ('attempt_submitted','problem_passed') ORDER BY rowid",
        (PROBLEM["id"],)).fetchall()
    assert len(rows) == 2
    attempt_id = dao.conn.execute("SELECT id FROM attempts WHERE problem_id=?", (PROBLEM["id"],)).fetchone()[0]
    for et, pj in rows:
        payload = json.loads(pj)
        assert payload.get("attempt_id") == attempt_id, (et, payload)   # ④与 backfill 形态归一
        assert len(payload.get("code_hash", "")) == 16, (et, payload)   # ③去重键在 payload 可复算


def test_recommendation_completed当日1比1(dao, no_llm):
    from core.judge import judge
    dao.emit_event("recommendation_shown", lang="python", problem_id=PROBLEM["id"],
                   payload={"recommendation_id": "r-1", "reason_code": "due", "surface": "home", "rank": 1})
    judge("python", PROBLEM, CODE, dao=dao)
    # 窗口外二次结算（D3 面去重独立验证）
    dao.conn.execute("UPDATE attempts SET ts = datetime('now', '-20 minutes') WHERE problem_id=?", (PROBLEM["id"],))
    dao.conn.commit()
    judge("python", PROBLEM, CODE, dao=dao)
    shown = _count(dao, "SELECT COUNT(*) FROM learning_events WHERE event_type='recommendation_shown'")
    done = _count(dao, "SELECT COUNT(*) FROM learning_events WHERE event_type='recommendation_completed'")
    assert (shown, done) == (1, 1), (shown, done)
