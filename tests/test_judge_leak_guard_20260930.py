# -*- coding: utf-8 -*-
"""判据泄漏防护（K-1/K-2/K-3，154241 Q-1 验收③最小方案 → l927-15 落地）。

锚点 done/20260925-154241-2218.result.md：三条判据同根——「判定即公开完整期望值」：
  K-1 空代码提交即得答案（expected_display 无折叠）→ 现在空路径**不构造**期望显示；
  K-2 答错后「期望输出」栏端出全量答案 → 现在**未通过只下发规模差异**（行数/字符数/行数差），
      通过后才全量对照（earned reveal，与开放题「写完再看」同构）；
  K-3 逐格 oracle「实际 Alice / 期望 1」可反复试探重建结果集 → 现在**定位给坐标与列类型，不给值**
      （行数 oracle 保留：属方向线索，不泄露数据值）。
判分口径零变化：passed/ok/error_kind/exit_code 取值面不在这三条的授权面内。
dao 一律走 tmp_path（绝不让 judge() 缺省开生产库，见 test_error_feedback_rows.py 档头）。

复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_judge_leak_guard_20260930.py -q
"""
from types import SimpleNamespace

import pytest

import core.judge as judge_mod
from core.judge import _build_display, _run_test_cases, judge
from core.progress import ProgressDAO
from core.runners.base import RunResult


@pytest.fixture
def dao(tmp_path):
    d = ProgressDAO(str(tmp_path / "leakguard.db"))
    yield d
    d.close()


@pytest.fixture
def fake_review(monkeypatch):
    monkeypatch.setattr(judge_mod, "review", lambda *a, **kw: "MOCK_FB")


class RowsRunner:
    def __init__(self, rows):
        self.rows = rows

    def run(self, *a, **kw):
        return SimpleNamespace(rows=self.rows, stdout="", ok=True, stderr="")


class FakePythonRunner:
    """可编程回填 stdout 的假 runner（judge 端到端用，不跑真解释器）。"""

    def __init__(self, stdout):
        self._stdout = stdout

    def run(self, code, stdin="", expected=None):
        return RunResult(True, self._stdout, "", False, 0)


# ---------------------------------------------------------------- K-1 空代码
def test_k1_空代码不再构造期望显示(fake_review, dao):
    r = judge("python", {"id": "python/t/k1", "expected_output": "SECRET\n"}, "   ", dao=dao)
    assert r.passed is False and r.diff_hint == "代码为空"
    assert r.expected_display == "", f"空提交不该拿到期望显示：{r.expected_display!r}"
    assert r.actual_display == "(空)"


# ---------------------------------------------------------------- K-2 两段式显示
def test_k2_未通过只给行数差异_不给期望值():
    exp, act = _build_display(
        "sql", {"expected_rows": [[1, "Alice", 92], [2, "Bob", 87]]},
        SimpleNamespace(rows=[[1, "x", 9]], stdout="", ok=True, stderr=""), passed=False)
    assert "期望 2 行" in exp
    assert "Alice" not in exp and "Bob" not in exp and "92" not in exp
    assert act == "1 | x | 9"          # 学生自己的输出照常显示（不是泄漏面）


def test_k2_通过后全量对照():
    exp, _ = _build_display(
        "sql", {"expected_rows": [[1, "Alice", 92], [2, "Bob", 87]]},
        SimpleNamespace(rows=[[1, "Alice", 92], [2, "Bob", 87]], stdout="", ok=True, stderr=""),
        passed=True)
    assert "Alice" in exp and "Bob" in exp   # earned reveal


def test_k2_文本题未通过只给规模():
    exp, _ = _build_display(
        "python", {"expected_output": "line-one\nline-two\nline-three\n"},
        SimpleNamespace(stdout="mine", ok=True, stderr=""), passed=False)
    assert "3 行" in exp and "字符" in exp
    assert "line-one" not in exp and "line-three" not in exp


def test_k2_端到端_答错拿不到答案_答对给全量(fake_review, dao, monkeypatch):
    problem = {"id": "python/t/k2", "title": "t", "statement": "s", "judge_mode": "run",
               "expected_output": "SECRET-OUTPUT\n", "tests": None, "setup_sql": None,
               "expected_rows": None, "hints": [], "difficulty": 1, "topic": "t"}
    monkeypatch.setattr(judge_mod, "_RUNNERS",
                        {"python": FakePythonRunner("my own output\n")})
    r = judge("python", problem, "print('x')", dao=dao)
    assert r.passed is False
    assert "SECRET-OUTPUT" not in r.expected_display
    assert "SECRET-OUTPUT" not in r.diff_hint

    monkeypatch.setattr(judge_mod, "_RUNNERS",
                        {"python": FakePythonRunner("SECRET-OUTPUT\n")})
    r2 = judge("python", problem, "print('SECRET-OUTPUT')", dao=dao)
    assert r2.passed is True and r2.expected_display == "SECRET-OUTPUT"


# ---------------------------------------------------------------- K-3 逐格定位不给值
def test_k3_逐格提示给坐标与类型_不给值():
    passed, _, hint = _run_test_cases(
        RowsRunner([["Alice", 92]]), "sql", "", {"expected_rows": [[1, 87]]})
    assert not passed
    assert "第 1 行第 1 列" in hint and "整数" in hint
    assert "Alice" not in hint and "87" not in hint and "92" not in hint
    assert "ORDER BY" in hint          # 原方向性话术保留


def test_k3_行数oracle保留_属方向不泄露值():
    passed, _, hint = _run_test_cases(
        RowsRunner([[1]]), "sql", "", {"expected_rows": [[1], [2], [3], [4], [5]]})
    assert not passed and "行数：实际 1 / 期望 5" in hint


def test_k3_类型词表_布尔小数空值():
    assert judge_mod._type_cn(True) == "布尔" and judge_mod._type_cn(False) == "布尔"
    assert judge_mod._type_cn(1.5) == "小数"
    assert judge_mod._type_cn(None) == "空值"
    assert judge_mod._type_cn("x") == "文本"
