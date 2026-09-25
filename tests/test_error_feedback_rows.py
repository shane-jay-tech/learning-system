# -*- coding: utf-8 -*-
"""执行器错误 → 行级反馈的映射层桩（20260925-120554-70e3，风险档 B / implementation）。

钉四件事，全部对应本单的验收句「相同错误不会出现互相矛盾的提示；原始诊断仍可追溯」：
  ① **行号不再自相矛盾**：Python 的 traceback 行号含 runner 注入的引导段，
     必须折算回学生编辑器里的行（偏移量由 `PREAMBLE` 现算，不写死数字）。
  ② **同一错误同类**：同一段诊断文本，四语言分类必须一致（矛盾面的根因是各写各的表）。
  ③ **原始诊断逐字可追溯**：映射层只读 stderr，不改写它；UI 仍拿得到原文。
  ④ **不改判题**：反馈只往 `diff_hint` 上**净加**文本，`passed`/`ok`/`error_kind`/`exit_code`
     的取值面一字不动（评分口径是用户可见面，超出本单授权）。
只读内容库＋跑真实子进程（与 tests/test_python_runner.py 同型），零写仓内文件。

🔴 一条本单实撞过的坑（写在这里防接班重踩）：`core/judge.py:_record_attempt` 在 **`dao=None`**
时会自己 `ProgressDAO()` 打开**生产库** `data/progress.db` 并写 attempts/problems_status/
review_state/learning_events 四张表——本班首版因此往真库写进过 14 行幽灵数据
（`problem_id='python/t/p'`，已逐行点名交回主班，见 result 的「遗留问题」）。
⇒ 本档所有 `judge(...)` 调用一律走 `tmp_path` 上的临时 dao（与 tests/test_judge.py 同型）。

复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_error_feedback_rows.py -q
"""
import re
from types import SimpleNamespace

import pytest

from core.judge import _error_summary, _row_feedback, judge
from core.progress import ProgressDAO
from core.runners import error_feedback as ef
from core.runners.cpp_runner import CppRunner
from core.runners.python_runner import PythonRunner
from core.runners.r_runner import RRunner
from core.runners.sql_runner import SQLRunner


@pytest.fixture
def dao(tmp_path):
    """临时库上的 dao——**绝不能传 None 给 judge()**（会写生产库，见档头）。"""
    d = ProgressDAO(str(tmp_path / "errfeed.db"))
    yield d
    d.close()


@pytest.fixture
def fake_review(monkeypatch):
    """把 LLM 点评面桩掉：本档只测反馈映射，不测点评文案，也不该为此联网。"""
    import core.judge as judge_mod
    monkeypatch.setattr(judge_mod, "review", lambda *a, **kw: "MOCK_FB")
    return "MOCK_FB"

# 一段"第 5 行才出错"的学生代码（行号按编辑器视角数）
CODE_LINE5 = "a = 1\nb = 2\nc = a + b\nprint('ok')\nprint(nope)\n"
RAW_NAMEERROR = (
    'Traceback (most recent call last):\n'
    '  File "/tmp/ls_py_x/main.py", line 11, in <module>\n'
    '    print(nope)\n'
    "NameError: name 'nope' is not defined\n"
)


# ---------------------------------------------------------------- ① 行号折算
def test_行号折算回编辑器行_偏移量由preamble现算():
    assert ef.PREAMBLE_LINES == len(ef.PREAMBLE.splitlines())
    r = PythonRunner().run(CODE_LINE5)
    got = ef.locate("python", r.stderr)
    assert got == 5, (
        f"学生代码第 5 行报错却被折算成 {got}——折算与引导段脱钩了（引导段行数变了没同步）")
    assert ef.locate("agent_dev", r.stderr) == 5   # agent_dev 复用 PythonRunner


def test_折算端到端_diff_hint里出现的行号就是编辑器行号():
    r = PythonRunner().run(CODE_LINE5)
    hint = _row_feedback("python", r)
    assert "第 5 行：" in hint, hint
    # 反例自证：原始诊断里那个更大的行号仍在 stderr（可追溯），但没漏进反馈
    assert re.search(r"line \d+", hint) is None, f"反馈里混进了未折算的行号：{hint}"


def test_定位不到行号时绝不瞎报一个():
    assert ef.locate("sql", "no such table: students") is None
    assert ef.where_phrase("sql", "no such table: students") == ""
    assert ef.locate("python", "boom without any file frame") is None


def test_cpp_行列定位_两种报文形态():
    a = "main.cpp:12:5: error: expected ';' before '}' token\n"
    b = "main.cpp(12:5): error: expected ';' before '}' token\n"
    assert ef.locate("cpp", a) == 12 and ef.locate("cpp", b) == 12
    assert ef.locate_column("cpp", a) == 5
    assert ef.where_phrase("cpp", a) == "第 12 行第 5 列："


# ---------------------------------------------------------------- ② 同类同判
@pytest.mark.parametrize("lang", ["python", "agent_dev", "sql", "cpp", "r"])
def test_同一段诊断_四语言分类一致(lang):
    """分类只认文本，不认语言 ⇒ 同串必同类（互相矛盾的根因就是各认各的）。"""
    assert ef.classify(lang, RAW_NAMEERROR) == "undefined_name"
    assert ef.classify(lang, "operation is not supported", timed_out=True) == "timeout"


def test_错误类词表稳定且都有话术():
    assert set(ef.KINDS) == {"toolchain", "policy", "timeout", "syntax",
                             "undefined_name", "type", "runtime", "none"}
    for kind in ef.KINDS:
        assert isinstance(ef.headline(kind), str)
    assert ef.classify("python", "随便一句没见过的话") == "runtime"
    assert ef.classify("python", "") == "none"


def test_提示表按语言限定_SQL的话术不会串到R报文():
    # R 的 "unexpected ')' " 类报文若被 SQL 规则命中，会得到一句讲 SQL 括号的错话
    assert "SQL" not in ef.hint_only("r", 'Error: unexpected ")" in "if (TRUE)"')
    assert "关键字" in ef.hint_only("sql", 'near ")" syntax error')


def test_python与r不再是裸英文_与sql_cpp共用一张表():
    assert "拼写" in ef.hint_only("python", RAW_NAMEERROR)
    assert "library()" in ef.hint_only("r", 'Error: could not find function "ggplot"')
    assert ef.hint_only("cpp", "error: 'foo' was not declared in this scope")
    assert ef.hint_only("sql", "no such column: nam")


# ---------------------------------------------------------------- ③ 可追溯
def test_反馈是净加_原始诊断逐字保留在stderr():
    r = PythonRunner().run(CODE_LINE5)
    assert "NameError: name 'nope' is not defined" in r.stderr   # 原文未被映射层改写
    assert r.stderr.startswith("Traceback (most recent call last):")
    summary = _error_summary(r.stderr)
    hint = _row_feedback("python", r)
    assert summary in hint, f"反馈把原有要点吞掉了：{hint!r} vs {summary!r}"


def test_已带中文提示的stderr不再重复追加一遍():
    stderr = ('no such table: students\n\n💡 中文提示：'
              '表「students」不存在——检查表名拼写（题目 setup 建了哪些表？）')
    hint = _row_feedback("sql", SimpleNamespace(stderr=stderr))
    assert hint.count("表「students」不存在") == 1, hint


# ---------------------------------------------------------------- ④ 不改判题
def test_映射层是纯函数_不吃ok_不改passed():
    """同一串 stderr，无论 ok=True/False，分类与反馈文本完全相同。"""
    for ok in (True, False):
        rr = SimpleNamespace(stderr=RAW_NAMEERROR, ok=ok, timed_out=False,
                             exit_code=1, error_kind="runtime")
        assert ef.classify("python", rr.stderr) == "undefined_name"
        assert _row_feedback("python", rr) == _row_feedback(
            "python", SimpleNamespace(stderr=RAW_NAMEERROR))


def test_判题结论面逐字未变_通过题与失败题各一例(fake_review, dao):
    """本单授权面只有"反馈"，这里钉住判题三件套没被顺带动过。"""
    problem = {"id": "python/t/p", "title": "t", "statement": "s", "judge_mode": "run",
               "expected_output": "ok\nnope\n", "tests": None, "setup_sql": None,
               "expected_rows": None, "hints": [], "difficulty": 1, "topic": "t"}
    res = judge("python", problem, CODE_LINE5, dao=dao)
    assert res.passed is False                      # 判题结论：仍是"未通过"
    assert res.run_result.ok is False               # 执行器结论：仍是失败
    assert res.run_result.error_kind == "runtime"   # 机器可读分类：未被本单改写
    assert res.run_result.exit_code == 1            # 退出码原样透传
    assert "第 5 行" in res.diff_hint               # ← 只有反馈变丰富了
    res2 = judge("python", dict(problem, expected_output="ok\n"), "print('ok')\n", dao=dao)
    assert res2.passed is True and res2.run_result.ok is True


def test_SQL真实失败仍给得出反馈():
    r = SQLRunner().run("SELECT nam FROM missing_table_x")
    hint = _row_feedback("sql", r)
    assert r.ok is False and hint
    assert "拼写" in hint, hint


def test_无dao的生产库路径在本档不可达(monkeypatch, fake_review, dao):
    """把「dao 缺省 → 自己开生产库」这条路钉成必抛，防本档再变回真写手。"""
    import core.judge as judge_mod

    def _boom(*a, **kw):
        raise AssertionError("触发了 ProgressDAO() 无参路径——那会写 data/progress.db")

    monkeypatch.setattr(judge_mod, "ProgressDAO", _boom)
    problem = {"id": "python/t/p", "statement": "s", "expected_output": "nope\n"}
    res = judge_mod.judge("python", problem, CODE_LINE5, dao=dao)
    assert res.passed is False          # 正常走完判题，且一次都没碰 _boom


# ---------------------------------------------------------------- ⑤ 超时话术单源
def test_超时话术单源_每处都带上预算秒数():
    """超时是本单点名的"互相矛盾"高发面：同一类错误不得一处有秒数一处没有。"""
    for what in ("编译", "程序运行", "代码运行", "R 脚本运行", "SQL 执行"):
        s = ef.timeout_message(what, 5)
        assert re.fullmatch(rf"{what}超时（超过 5 秒）。", s), s
        assert ef.timeout_budget(s) == 5, f"话术里的秒数读不回来：{s}"
    assert ef.timeout_message("程序运行", 3, "有备注") == "程序运行超时（超过 3 秒），有备注。"
    # 逐字回归：既有测试钉的是「编译超时」子串，改后仍在
    assert "编译超时" in ef.timeout_message("编译", 7)


def test_四个runner的超时文案都走单源函数():
    import core.runners.cpp_runner as cpp
    import core.runners.python_runner as py
    import core.runners.r_runner as rr
    import core.runners.sql_runner as sq
    for name, mod in {"cpp": cpp, "python": py, "r": rr, "sql": sq}.items():
        text = open(mod.__file__, encoding="utf-8").read()
        assert "timeout_message(" in text, f"{name} 的超时文案没走单源函数"
    # 端到端：真跑一次 python 超时，报文里必须读得回预算秒数
    r = PythonRunner().run("import time\nstart = time.time()\nwhile time.time() - start < 30: pass")
    assert ef.timeout_budget(r.stderr) == PythonRunner.timeout_sec
    assert r.timed_out is True and r.error_kind == "timeout"


def test_引导段挪位后写出的学生文件逐字节不变():
    """python_runner 改成 import 常量，必须与改动前的内联字面量**逐字相同**。"""
    assert ef.PREAMBLE == (
        "import sys\n"
        "try:\n"
        "    sys.stdout.reconfigure(encoding='utf-8')\n"
        "    sys.stderr.reconfigure(encoding='utf-8')\n"
        "except Exception:\n"
        "    pass\n"
    )
    assert ef.PREAMBLE_LINES == 6
