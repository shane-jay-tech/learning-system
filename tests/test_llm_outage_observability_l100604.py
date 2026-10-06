# -*- coding: utf-8 -*-
"""l1006-04：LLM 断线写库 C 案定向例（l1004-08；用户 2026-10-06 拍板「可见但不混入计分」）。

① run 臂降级 llm_degraded 结构化位（attempts 计数零变化）；
② 开放题断线 ai_open_degraded 事件（不写 attempt）；
③ 脏 JSON（llm_ok=True 但 score=None）ai_open_scored payload degraded 位（照写 attempt 钉住）。

复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_llm_outage_observability_l100604.py -q
"""
import json

import pytest

from core.progress import ProgressDAO

PROBLEM = {
    "id": "python/out/1",
    "title": "t",
    "statement": "s",
    "expected_output": "Hello\n",
}
CODE = 'print("Hello")'
OPEN_P = {"id": "python/out/open1", "title": "t", "statement": "s",
          "judge_mode": "ai_open", "rubric": "r", "reference_answer": "x"}


@pytest.fixture
def dao(tmp_path):
    d = ProgressDAO(str(tmp_path / "outage.db"))
    yield d
    d.close()


@pytest.fixture
def no_llm(monkeypatch):
    monkeypatch.setattr("core.ai_review._call_chain", lambda *a, **kw: ("", None))


def _count(dao, sql, *args):
    return dao.conn.execute(sql, args).fetchone()[0]


def test_1_run臂断线_llm_degraded位_true且attempts计数不变(dao, no_llm):
    from core.judge import judge
    r = judge("python", PROBLEM, CODE, dao=dao)
    assert r.passed is True
    payload = json.loads(dao.conn.execute(
        "SELECT payload_json FROM learning_events WHERE event_type='attempt_submitted' "
        "AND problem_id=?", (PROBLEM["id"],)).fetchone()[0])
    assert payload["llm_degraded"] is True, payload
    # 零变化钉：attempts 照写 1 行（run 臂计分依据本地跑测，断线不改变计数）
    assert _count(dao, "SELECT COUNT(*) FROM attempts WHERE problem_id=?", PROBLEM["id"]) == 1


def test_1_run臂在线_llm_degraded位_false(dao, monkeypatch):
    monkeypatch.setattr("core.ai_review._call_chain",
                        lambda *a, **kw: ("这份点评提到了输出格式，建议对照示例检查空格。", "stub"))
    from core.judge import judge
    r = judge("python", PROBLEM, CODE, dao=dao)
    assert r.passed is True
    payload = json.loads(dao.conn.execute(
        "SELECT payload_json FROM learning_events WHERE event_type='attempt_submitted' "
        "AND problem_id=?", (PROBLEM["id"],)).fetchone()[0])
    assert payload["llm_degraded"] is False, payload


def test_2_开放题断线发ai_open_degraded且零attempt(dao, no_llm):
    from core.judge import judge
    r = judge("python", OPEN_P, "我的回答", dao=dao)
    assert r.passed is False
    assert _count(dao, "SELECT COUNT(*) FROM learning_events WHERE event_type='ai_open_degraded' "
                       "AND problem_id=?", OPEN_P["id"]) == 1
    payload = json.loads(dao.conn.execute(
        "SELECT payload_json FROM learning_events WHERE event_type='ai_open_degraded'").fetchone()[0])
    assert payload["reason"] == "llm_unavailable"
    # 零变化钉：断线不写 attempt（「不把基础设施故障算成用户失败」原则保持）
    assert _count(dao, "SELECT COUNT(*) FROM attempts WHERE problem_id=?", OPEN_P["id"]) == 0
    assert dao.get_status("python", OPEN_P["id"]) == "unseen"


def test_3_脏JSON_degraded位_true且attempt照写(dao, monkeypatch):
    """llm_ok=True 但 score=None（脏 JSON）⇒ attempt 照写＋ai_open_scored degraded 显式位。"""
    def dirty_grade(lang, problem, answer):
        return {"passed": True, "score": None, "feedback": "文本在但分没了", "llm_ok": True}
    monkeypatch.setattr("core.judge.grade_open_answer", dirty_grade)
    from core.judge import judge
    r = judge("python", OPEN_P, "我的回答", dao=dao)
    assert r.passed is True
    payload = json.loads(dao.conn.execute(
        "SELECT payload_json FROM learning_events WHERE event_type='ai_open_scored'").fetchone()[0])
    assert payload["degraded"] is True and payload["score"] is None, payload
    assert _count(dao, "SELECT COUNT(*) FROM attempts WHERE problem_id=?", OPEN_P["id"]) == 1
    # 维度空 ⇒ rubric_scores 无行（既有的半防护保持，degraded 位使其可观测）
    assert _count(dao, "SELECT COUNT(*) FROM rubric_scores WHERE problem_id=?", OPEN_P["id"]) == 0


def test_3_干净JSON_degraded位_false(dao, monkeypatch):
    def good_grade(lang, problem, answer):
        return {"passed": True, "score": 90, "feedback": "好",
                "dimensions": [{"name": "清晰度", "score": 90}], "llm_ok": True}
    monkeypatch.setattr("core.judge.grade_open_answer", good_grade)
    from core.judge import judge
    judge("python", OPEN_P, "我的回答", dao=dao)
    payload = json.loads(dao.conn.execute(
        "SELECT payload_json FROM learning_events WHERE event_type='ai_open_scored'").fetchone()[0])
    assert payload["degraded"] is False, payload
