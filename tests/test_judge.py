import pytest

import core.judge as judge_mod
from core.judge import judge
from core.progress import ProgressDAO
import core.ai_review as ai_review_mod


@pytest.fixture
def fake_review(monkeypatch):
    monkeypatch.setattr(judge_mod, "review", lambda *a, **kw: "MOCK_FB")
    return "MOCK_FB"


@pytest.fixture
def dao(tmp_path):
    d = ProgressDAO(str(tmp_path / "j.db"))
    yield d
    d.close()


def test_python_correct_marks_solved(fake_review, dao):
    problem = {
        "id": "python/t/01",
        "title": "say hello",
        "statement": "...",
        "expected_output": "Hello\n",
    }
    r = judge("python", problem, 'print("Hello")', dao=dao)
    assert r.passed is True
    assert r.ai_feedback == fake_review
    assert dao.get_status("python", "python/t/01") == "solved"


def test_python_wrong_marks_wrong(fake_review, dao):
    problem = {
        "id": "python/t/02",
        "title": "say hello",
        "statement": "...",
        "expected_output": "Hello\n",
    }
    r = judge("python", problem, 'print("World")', dao=dao)
    assert r.passed is False
    assert dao.get_status("python", "python/t/02") == "wrong"
    assert any(m["problem_id"] == "python/t/02" for m in dao.list_mistakes())


def test_wrong_then_right_clears_mistake(fake_review, dao):
    problem = {
        "id": "python/t/03",
        "title": "x",
        "statement": "",
        "expected_output": "Hello\n",
    }
    judge("python", problem, 'print("oops")', dao=dao)
    assert any(m["problem_id"] == "python/t/03" for m in dao.list_mistakes())
    judge("python", problem, 'print("Hello")', dao=dao)
    assert all(m["problem_id"] != "python/t/03" for m in dao.list_mistakes())
    assert dao.get_status("python", "python/t/03") == "solved"


def test_sql_expected_rows(fake_review, dao):
    problem = {
        "id": "sql/t/01",
        "title": "select",
        "statement": "",
        "setup_sql": "CREATE TABLE t(x INTEGER); INSERT INTO t VALUES (1),(2);",
        "expected_rows": [[1], [2]],
    }
    r = judge("sql", problem, "SELECT x FROM t ORDER BY x", dao=dao)
    assert r.passed is True
    assert dao.get_status("sql", "sql/t/01") == "solved"


def test_normalizes_trailing_newline(fake_review, dao):
    problem = {"id": "python/t/04", "title": "", "statement": "", "expected_output": "Hi\n"}
    r = judge("python", problem, 'print("Hi")', dao=dao)
    assert r.passed is True


# -------------------------------------------------------------------
# 开放题（judge_mode=ai_open）—— AI 评分路径
# -------------------------------------------------------------------

def test_ai_open_passed(monkeypatch, dao):
    """开放题判为通过；DAO 记 solved，且不跑 runner（run_result is None）。"""
    def fake_grade(lang, problem, answer):
        return {"passed": True, "score": 90, "feedback": "OK", "llm_ok": True}
    monkeypatch.setattr(judge_mod, "grade_open_answer", fake_grade)

    problem = {
        "id": "python/open01",
        "judge_mode": "ai_open",
        "reference_answer": "ref answer",
    }
    r = judge("python", problem, "student answer", dao=dao)
    assert r.passed is True
    assert r.run_result is None
    assert r.ai_feedback == "OK"
    assert r.expected_display == "ref answer"
    assert dao.get_status("python", "python/open01") == "solved"


def test_ai_open_failed(monkeypatch, dao):
    """开放题判为未通过；DAO 记 wrong。"""
    def fake_grade(*a, **kw):
        return {"passed": False, "score": 40, "feedback": "bad", "llm_ok": True}
    monkeypatch.setattr(judge_mod, "grade_open_answer", fake_grade)

    problem = {"id": "python/open02", "judge_mode": "ai_open"}
    r = judge("python", problem, "bad answer", dao=dao)
    assert r.passed is False
    assert dao.get_status("python", "python/open02") == "wrong"


def test_ai_open_llm_unavailable_no_record(monkeypatch, dao):
    """LLM 不可用时不记录 attempt（基础设施故障不算用户失败）。"""
    monkeypatch.setattr(
        judge_mod, "grade_open_answer",
        lambda *a, **kw: {"passed": False, "score": None, "feedback": "err", "llm_ok": False},
    )
    problem = {"id": "python/open03", "judge_mode": "ai_open"}
    r = judge("python", problem, "answer", dao=dao)
    assert r.passed is False
    assert dao.get_status("python", "python/open03") == "unseen"
    assert not any(m["problem_id"] == "python/open03" for m in dao.list_mistakes())


def test_ai_open_no_runner_for_unknown_lang(monkeypatch, dao):
    """开放题分支在语言检查之前——即使 lang 没有 runner 也能评判。"""
    monkeypatch.setattr(
        judge_mod, "grade_open_answer",
        lambda *a, **kw: {"passed": True, "score": 88, "feedback": "good", "llm_ok": True},
    )
    problem = {"id": "agent_dev/o/1", "judge_mode": "ai_open"}
    r = judge("agent_dev", problem, "我的回答", dao=dao)
    assert r.passed is True
    assert r.run_result is None


def test_grade_open_parses_clean_json(monkeypatch):
    """标准 JSON 输出被正确解析。"""
    monkeypatch.setattr(
        ai_review_mod, "_call",
        lambda *a, **kw: '{"passed": true, "score": 85, "feedback": "讲清楚了输入输出"}',
    )
    res = ai_review_mod.grade_open_answer("python", {"statement": "q", "rubric": "- 要点"}, "ans")
    assert res["passed"] is True
    assert res["score"] == 85
    assert res["llm_ok"] is True


def test_grade_open_parses_fenced_json(monkeypatch):
    """带 ```json 围栏的输出也能解析。"""
    monkeypatch.setattr(
        ai_review_mod, "_call",
        lambda *a, **kw: '```json\n{"passed": false, "score": 50, "feedback": "缺边界"}\n```',
    )
    res = ai_review_mod.grade_open_answer("python", {}, "ans")
    assert res["passed"] is False
    assert res["score"] == 50
    assert res["llm_ok"] is True


def test_grade_open_string_bool_and_float_score(monkeypatch):
    """passed 是字符串 'false'、score 是浮点字符串时，解析要正确。"""
    monkeypatch.setattr(
        ai_review_mod, "_call",
        lambda *a, **kw: '{"passed": "false", "score": "50.5", "feedback": "ok"}',
    )
    res = ai_review_mod.grade_open_answer("python", {}, "ans")
    assert res["passed"] is False  # 字符串 "false" 不能被当成 True
    assert res["score"] == 50


def test_grade_open_fallback_pass(monkeypatch):
    """非 JSON 输出且含「通过」-> 启发式 passed=True，原文当 feedback。"""
    monkeypatch.setattr(ai_review_mod, "_call", lambda *a, **kw: "你这道题通过了，非常好")
    res = ai_review_mod.grade_open_answer("python", {"statement": "某题"}, "学生的回答")
    assert res["passed"] is True
    assert res["llm_ok"] is True
    assert "通过" in res["feedback"]


def test_grade_open_fallback_fail(monkeypatch):
    """非 JSON 输出且不含「通过」-> 启发式 passed=False。"""
    monkeypatch.setattr(ai_review_mod, "_call", lambda *a, **kw: "还有欠缺，没有覆盖重点")
    res = ai_review_mod.grade_open_answer("python", {}, "ans")
    assert res["passed"] is False
    assert res["llm_ok"] is True


def test_grade_open_fallback_negation_not_fooled(monkeypatch):
    """兜底启发式：含「通过」但实为失败的措辞（没有通过测试）不能误判成 passed。"""
    monkeypatch.setattr(ai_review_mod, "_call",
                        lambda *a, **kw: "你的边界处理没有通过测试用例，需要再改。")
    res = ai_review_mod.grade_open_answer("python", {}, "ans")
    assert res["passed"] is False


def test_grade_open_llm_down(monkeypatch):
    """两个模型都返回空 -> llm_ok=False，给友好提示。"""
    monkeypatch.setattr(ai_review_mod, "_call", lambda *a, **kw: "")
    res = ai_review_mod.grade_open_answer("python", {}, "ans")
    assert res["passed"] is False
    assert res["llm_ok"] is False
    assert "暂时不可用" in res["feedback"]


def test_run_mode_backward_compat(fake_review, dao):
    """缺省 judge_mode 的题仍走 runner，run_result 被填充。"""
    problem = {"id": "python/t_back", "expected_output": "Hello\n"}
    r = judge("python", problem, 'print("Hello")', dao=dao)
    assert r.passed is True
    assert r.run_result is not None
    assert dao.get_status("python", "python/t_back") == "solved"
