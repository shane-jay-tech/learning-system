import json
import subprocess
from types import SimpleNamespace

import pytest

import core.ai_review as ai_review
from core.achievements import (
    ACHIEVEMENTS,
    _estimate_progress,
    get_all_earned,
    get_all_with_state,
)
from core.judge import _build_display, _normalize, _run_test_cases, _to_problem_dict, judge
from core.progress import ProgressDAO
from core.runners.base import BaseRunner, RunResult
from core.runners.sql_runner import SQLRunner, _render_table, _split_sql_statements, _validate_setup_sql
from core.utils import trim_text


@pytest.fixture
def dao(tmp_path):
    database = ProgressDAO(str(tmp_path / "edges.db"))
    yield database
    database.close()


def test_achievement_state_and_progress_estimators(dao):
    dao.set_meta("achievements_earned", "first_solve,unknown")
    dao.mark_status("python", "p1", "solved")
    states = {item["achievement"].id: item for item in get_all_with_state(dao)}
    assert states["first_solve"]["state"] == "earned"
    assert states["solve_10"]["state"] == "locked"
    assert get_all_earned(dao)[0].id == "first_solve"

    by_id = {a.id: a for a in ACHIEVEMENTS}
    assert _estimate_progress(by_id["streak_3"], 0, 2, 0, {}) == pytest.approx(2 / 3)
    assert _estimate_progress(by_id["multi_lang"], 0, 0, 3, {}) == 1.0
    assert _estimate_progress(by_id["python_first"], 0, 0, 0, {"python": {"solved": 1}}) == 1.0
    assert _estimate_progress(by_id["path_agent_done"], 0, 0, 0, {}) == 0.0


def test_ai_call_chain_and_post_check(monkeypatch):
    calls = []

    def fake_call(model, prompt, system, model_id=None):
        calls.append((model, model_id))
        return "answer" if model == "second" else ""

    monkeypatch.setattr(ai_review, "_call", fake_call)
    assert ai_review._call_chain("p", "s", (("first", None), ("second", "m"))) == "answer"
    assert calls == [("first", None), ("second", "m")]
    assert ai_review._call_chain("p", "s", ()) == ""

    harsh = "不足很多，问题是没有处理边界"
    checked = ai_review._post_check(harsh, difficulty=1, passed=True)
    assert "核心思路是正确的" in checked
    assert ai_review._post_check(harsh, difficulty=4, passed=True) == harsh


def test_ai_review_success_and_offline_friendly_fallback(monkeypatch):
    run = SimpleNamespace(stdout="ok", stderr="NameError: x")
    monkeypatch.setattr(ai_review, "_call_chain", lambda *a, **kw: "具体点评")
    assert ai_review.review("python", {"difficulty": 3}, "print(1)", run, True) == "具体点评"

    friendly = SimpleNamespace(title="变量名不存在", explanation="先定义变量。", suggested_action="检查拼写")
    monkeypatch.setattr(ai_review, "_call_chain", lambda *a, **kw: "")
    monkeypatch.setattr(ai_review, "_fe", SimpleNamespace(friendly_explain=lambda stderr: friendly))
    result = ai_review.review("python", {}, "x", run, False)
    assert "变量名不存在" in result
    assert "检查拼写" in result

    monkeypatch.setattr(ai_review, "_fe", SimpleNamespace(friendly_explain=lambda stderr: (_ for _ in ()).throw(ValueError())))
    assert "暂时不可用" in ai_review._offline_fallback(False, "boom")


def test_follow_up_and_lesson_prompt_keep_recent_history(monkeypatch):
    captured = []

    def fake_chain(prompt, system, chain):
        captured.append(prompt)
        return "reply"

    monkeypatch.setattr(ai_review, "_call_chain", fake_chain)
    history = [{"role": "user" if i % 2 == 0 else "ai", "text": f"message-{i}-" + "x" * 300} for i in range(12)]
    run = SimpleNamespace(stdout="out", stderr="")
    assert ai_review.follow_up("python", {"title": "t"}, "code", run, True, "review", history, "why") == "reply"
    assert "message-0" not in captured[-1]
    assert "message-11" in captured[-1]

    assert ai_review.ask_lesson("python", "loops", "lesson", [], "question") == "reply"
    assert "(无前序对话)" in captured[-1]

    monkeypatch.setattr(ai_review, "_call_chain", lambda *a, **kw: "")
    assert "暂时连不上" in ai_review.follow_up("python", {}, "", run, False, "", [], "?")
    assert "暂时连不上" in ai_review.ask_lesson("python", "", "", [], "?")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('prefix {"a": 1} suffix', {"a": 1}),
        ('[1, 2]', None),
        ('prefix {bad} suffix', None),
        ('nothing', None),
    ],
)
def test_extract_json_edge_cases(text, expected):
    assert ai_review._extract_json(text) == expected


def test_grade_open_clamps_scores_dimensions_and_cross_checks_pass(monkeypatch):
    response = {
        "passed": True,
        "score": 20,
        "feedback": "",
        "dimensions": [{"name": "正确性", "score": 120, "comment": "x"}, "bad"],
    }
    monkeypatch.setattr(ai_review, "_call", lambda *a, **kw: json.dumps(response, ensure_ascii=False))
    result = ai_review.grade_open_answer("python", {"reference_answer": "ref"}, "answer")
    assert result["passed"] is False
    assert result["score"] == 20
    assert result["feedback"] == "（AI 未给出点评文本）"
    assert result["dimensions"] == [{"name": "正确性", "score": 100, "comment": "x"}]

    response.update({"passed": False, "score": 90, "dimensions": {}})
    result = ai_review.grade_open_answer("python", {}, "answer")
    assert result["passed"] is True
    assert result["dimensions"] == []


def test_low_level_ai_call_handles_success_errors_and_model_override(monkeypatch):
    captured = {}

    def success(*args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(returncode=0, stdout=b" ok \n", stderr=b"")

    monkeypatch.setattr(ai_review.subprocess, "run", success)
    assert ai_review._call("deepseek", "p", model_id="flash") == "ok"
    assert captured["env"]["DEEPSEEK_MODEL"] == "flash"

    monkeypatch.setattr(ai_review.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=2, stdout=b"", stderr=b"bad"))
    assert ai_review._call("gpt", "p") == ""
    monkeypatch.setattr(ai_review.subprocess, "run", lambda *a, **kw: (_ for _ in ()).throw(subprocess.TimeoutExpired("x", 1)))
    assert ai_review._call("gpt", "p") == ""
    monkeypatch.setattr(ai_review.subprocess, "run", lambda *a, **kw: (_ for _ in ()).throw(OSError("boom")))
    assert ai_review._call("gpt", "p") == ""


def test_judge_helpers_and_unknown_language():
    obj = SimpleNamespace(id="p1", title="T", statement="S")
    assert _to_problem_dict({"id": "d"})["id"] == "d"
    assert _to_problem_dict(obj)["id"] == "p1"
    custom = SimpleNamespace(to_dict=lambda: {"id": "custom"})
    assert _to_problem_dict(custom) == {"id": "custom"}
    assert _normalize(None) == ""
    assert _normalize("[1] 2\n[2] 3\n", "r") == "2\n3"

    result = judge("brainfuck", {"id": "x"}, "code")
    assert not result.passed
    assert "暂不支持" in result.ai_feedback

    expected, actual = _build_display("sql", {"expected_rows": []}, SimpleNamespace(rows=None, stdout="fallback"))
    assert expected == "(空)"
    assert actual == "fallback"


def test_run_test_cases_reports_output_runtime_and_row_differences():
    class QueueRunner:
        def __init__(self, results):
            self.results = iter(results)

        def run(self, *args, **kwargs):
            return next(self.results)

    ok_wrong = RunResult(True, "wrong", "", False, 0)
    passed, _, hint = _run_test_cases(QueueRunner([ok_wrong]), "python", "", {"expected_output": "right"})
    assert not passed and "输出与期望" in hint

    failed = RunResult(False, "", "first line\nsecond", False, 1)
    pdict = {"tests": [{"expected_output": "a"}, {"expected_output": "b"}]}
    passed, _, hint = _run_test_cases(QueueRunner([failed]), "python", "", pdict)
    assert not passed and "第 1 组" in hint and "first line" in hint

    rows = SimpleNamespace(rows=[[1]], stdout="", ok=True, stderr="")
    passed, _, hint = _run_test_cases(QueueRunner([rows]), "sql", "", {"expected_rows": [[1], [2]]})
    assert not passed and "行数" in hint


def test_progress_meta_events_and_invalid_streak_rows(dao):
    assert dao.get_meta_ts("missing") is None
    dao.set_meta("k", "v")
    assert dao.get_meta_ts("k")

    with dao.conn:
        dao.conn.execute(
            "INSERT INTO attempts(lang, problem_id, code, passed, ai_feedback, ts) VALUES(?,?,?,?,?,?)",
            ("python", "bad", "", 0, "", "invalid"),
        )
    assert dao.daily_streak() == 0

    assert dao.milestone_progress([]) == {"total": 0, "solved": 0, "pct": 0.0}
    dao.mark_status("python", "p1", "solved")
    progress = dao.milestone_progress([{"lang": "python", "problem_id": "p1"}, {"lang": "sql", "problem_id": "s1"}])
    assert progress == {"total": 2, "solved": 1, "pct": 0.5}

    dao.emit_event("one", payload={"x": 1})
    dao.emit_event("two")
    assert dao.event_count() == 2
    assert dao.event_count("one") == 1
    events = dao.events_by_date()
    assert len(events) == 1
    assert events[0]["one"] == 1
    assert events[0]["two"] == 1


def test_progress_review_state_caps_and_resets(dao):
    for _ in range(8):
        dao.update_review_state("python", "p1", True, difficulty=5)
    row = dao.conn.execute(
        "SELECT interval_days, ease, review_streak, last_result FROM review_state WHERE lang='python' AND problem_id='p1'"
    ).fetchone()
    assert row[0] == 30
    assert row[1] >= 1.5
    assert row[2] == 8
    dao.update_review_state("python", "p1", False)
    row = dao.conn.execute(
        "SELECT interval_days, review_streak, last_result FROM review_state WHERE lang='python' AND problem_id='p1'"
    ).fetchone()
    assert row == (1, 0, "fail")


def test_sql_statement_split_validation_and_errors():
    sql = "SELECT ';' AS semi; SELECT [a;b] FROM t; SELECT \"x;y\""
    assert _split_sql_statements(sql) == ["SELECT ';' AS semi", "SELECT [a;b] FROM t", 'SELECT "x;y"']
    assert _validate_setup_sql("CREATE TABLE t(x); INSERT INTO t VALUES(1)") is None
    assert "不允许" in _validate_setup_sql("PRAGMA foreign_keys=OFF")

    runner = SQLRunner()
    assert "一条 SQL" in runner.run("SELECT 1; SELECT 2").stderr
    syntax = runner.run("SELECT * FROM missing")
    assert not syntax.ok and "no such table" in syntax.stderr
    empty = runner.run("WITH x AS (SELECT 1) SELECT * FROM x WHERE 0")
    assert empty.ok and empty.rows == []
    assert _render_table([], []) == ""


def test_base_runner_contract_and_text_trimming():
    with pytest.raises(NotImplementedError):
        BaseRunner().run("x")
    assert trim_text("abc", 10) == "abc"
    assert trim_text("abcdef", 4) == "abcd\n[... 已截断（>4 字符）]"
    assert trim_text(None, 4) == ""
