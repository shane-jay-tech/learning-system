# -*- coding: utf-8 -*-
"""执行阶段可区分性（编译期／运行期）与 `RunResult` 稳定结构。

对应信箱单 `20260925-120552-07d4`（A 档／test；执行班 `qoder-executor-20260925-1630-learn38`）。

卷宗原文：「测试模块语法、顶层 await、运行时异常和非零退出。
验收：每种错误可区分编译与运行阶段，返回稳定结构。」

**先证其在世**（两处与卷宗用词相关，都要点名）：
- 本仓**没有 JS/TS 前端**（`core/judge.py:16 _RUNNERS` 只有 python／sql／cpp／r／agent_dev；
  `core/runners/` 内 `rg -i 'node|javascript|typescript'` 零命中）
  ⇒ 卷宗的「顶层 await」按本仓实体收窄为 **Python 模块层 `await`**
  （`SyntaxError: 'await' outside function`，解释器在**编译期**拒收），不造 JS 概念。
- 「编译阶段」在 Python 侧＝解释器把 `main.py` compile 掉的阶段（早于任何一行执行）。

✅ **D-14 已修（r5 B3，2026-09-27 用户裁决）**：`error_kind` 词表加入 **`"syntax"`**——
`python_runner` 现在把失败分支交给本仓既有的 `error_feedback.classify()`，语法错（编译期）
与除零（运行期）不再落进同一个 `"runtime"`。**判题结论一字未改**（`ok`／`exit_code` 照旧），
变的只有这一列的分类。改前的那批"不可区分"钉子在本文件里按新口径逐条翻转。

覆盖面自证：每条"不可区分"的负向钉子都配一条"classify 层可区分"的正向对照；
每条结构断言都跑遍四类结局（成功／编译期错／运行期错／非零退出／超时／公开模式拒绝）。
"""
import dataclasses
import sys

import pytest

from core.progress import ProgressDAO
from core.judge import _error_summary
from core.runners.base import RunResult
from core.runners.error_feedback import classify, feedback, locate
from core.runners.python_runner import PythonRunner

#: `RunResult` 的字段全集（"稳定结构"的字面定义，改字段必须显式更新本钉子）
RESULT_FIELDS = ["ok", "stdout", "stderr", "timed_out", "exit_code",
                 "error_kind", "rows", "elapsed_ms"]

#: `python_runner` 实际会写出的 `error_kind` 词表（r5 B3 起含 syntax）
OBSERVED_ERROR_KINDS = {None, "runtime", "syntax", "timeout", "sandbox"}


@pytest.fixture(scope="module")
def runner():
    return PythonRunner()


@pytest.fixture(autouse=True)
def _sandbox_progress_db(monkeypatch, tmp_path):
    fake = tmp_path / "learn38-stage-sandbox.db"
    monkeypatch.setenv("LS_PROGRESS_DB", str(fake))
    assert ProgressDAO().db_path == str(fake)
    yield fake


# ---------------------------------------------------------------------------
# 1) 模块语法与顶层 await：编译期确实是一个独立阶段
# ---------------------------------------------------------------------------

class TestCompileStageIsReal:
    def test_top_level_await_is_refused_at_compile_stage(self, runner):
        """顶层 await（收窄到 Python 实体）：解释器**一行都没跑**就拒收。"""
        r = runner.run("import asyncio\nawait asyncio.sleep(1)\n")
        assert r.exit_code == 1
        assert "SyntaxError: 'await' outside function" in r.stderr
        assert classify("python", r.stderr) == "syntax"
        assert locate("python", r.stderr) == 2  # 折算掉 preamble 后是学生的第 2 行

    def test_await_inside_async_function_runs_fine(self, runner):
        """正向对照：同样的 `await` 放进协程里就正常跑完 ⇒ 上一条确实是阶段问题。"""
        r = runner.run("import asyncio\n"
                       "async def main():\n"
                       "    await asyncio.sleep(0.05)\n"
                       "    return 'awaited'\n"
                       "print(asyncio.run(main()))\n")
        assert r.exit_code == 0
        assert r.stdout.strip() == "awaited"
        assert classify("python", r.stderr) == "none"

    def test_compile_stage_precedes_any_runtime_exit(self, runner):
        """整文件先 compile ⇒ 第 3 行的语法错会让第 2 行的 `sys.exit(0)` **根本没机会跑**。"""
        r = runner.run("import sys\nsys.exit(0)\nx = (\n")
        assert r.exit_code == 1, "若运行期先发生，这里应当是退出码 0"
        assert classify("python", r.stderr) == "syntax"
        assert r.stdout == ""

    @pytest.mark.parametrize("code", [
        "def f(:\n    pass\n",           # 非法函数头
        "class\n",                        # 关键字独占
        "x = *\n",                        # 裸星号
        "for i in range(3) print(i)\n",   # 漏冒号
        "if True\n    pass\n",            # 条件漏冒号
        "lambda\n",
        "@\n",
        "x = 1;;\n",
    ])
    def test_module_syntax_variants_all_stay_in_the_compile_stage(self, runner, code):
        r = runner.run(code)
        assert r.exit_code == 1, repr(code)
        assert classify("python", r.stderr) == "syntax", repr(code)
        assert r.timed_out is False

    def test_a_valid_module_with_main_guard_runs(self, runner):
        """模块语法的正常面（正向对照）：`__main__` 守卫＋函数定义跑通。"""
        r = runner.run("def go():\n    return 5\n\n"
                       "if __name__ == '__main__':\n    print(go() * 2)\n")
        assert r.exit_code == 0 and r.stdout.strip() == "10"


# ---------------------------------------------------------------------------
# 2) D-14 已修：`error_kind` 层面编译期(syntax)／运行期(runtime) 现在可区分
# ---------------------------------------------------------------------------

COMPILE_CASES = {
    "top-level-await": "await 1\n",
    "bad-def-header": "def f(:\n    pass\n",
    "unclosed-paren": "print(\n",
}
RUNTIME_CASES = {
    "zero-division": "print(1 / 0)\n",
    "missing-name": "print(nope)\n",
    "bad-import": "import definitely_not_a_module_x9\n",
    "index-error": "print([1][5])\n",
}


class TestStageBlendInErrorKind:
    @pytest.mark.parametrize("case", sorted(COMPILE_CASES))
    def test_compile_errors_are_labelled_syntax(self, runner, case):
        """**D-14 修复后**：编译期错误的 `error_kind` 是 `"syntax"`，与运行期错分列。"""
        r = runner.run(COMPILE_CASES[case])
        assert r.error_kind == "syntax", case
        assert classify("python", r.stderr) == "syntax", "同源：classify 层也是 syntax"

    @pytest.mark.parametrize("case", sorted(RUNTIME_CASES))
    def test_runtime_errors_are_labelled_runtime(self, runner, case):
        r = runner.run(RUNTIME_CASES[case])
        assert r.error_kind == "runtime", case
        assert classify("python", r.stderr) in {"runtime", "undefined_name"}, case

    def test_two_stages_are_now_distinguishable(self, runner):
        """把两阶段各跑一次：**判题结论仍相同**（ok=False、exit_code=1），但分类不再塌成一格。"""
        comp = runner.run(COMPILE_CASES["unclosed-paren"])
        run = runner.run(RUNTIME_CASES["zero-division"])
        assert (comp.error_kind, run.error_kind) == ("syntax", "runtime")
        assert comp.exit_code == run.exit_code == 1
        assert classify("python", comp.stderr) != classify("python", run.stderr)

    def test_error_kind_vocabulary_emits_syntax_for_compile_stage(self, runner):
        """词表钉子（r5 B3 起）：编译期案例只出 syntax、运行期案例只出 runtime，成功为 None。"""
        seen = set()
        for code in list(COMPILE_CASES.values()) + list(RUNTIME_CASES.values()) + ["print(1)\n"]:
            seen.add(runner.run(code).error_kind)
        assert seen == {"syntax", "runtime", None}
        assert seen <= OBSERVED_ERROR_KINDS

    def test_syntax_error_can_surface_during_runtime_via_import(self, runner, tmp_path):
        """阶段与错误类**不能互推**：运行期 `import` 一个坏模块 ⇒ 运行期抛"编译期"错误。

        这条同时是"别用出现阶段反推错误类"的反例（也说明 `error_kind` 表述的是**错误类**、
        不是**出现阶段**：`syntax` 可以在运行期由 import 触发）。
        """
        r = runner.run(
            "import pathlib, sys\n"
            "pathlib.Path('badmod.py').write_text('def f(:\\n    pass\\n', encoding='utf-8')\n"
            "sys.path.insert(0, '.')\n"
            "import badmod\n"
        )
        assert r.exit_code == 1
        # r5 B3：error_kind 表述**错误类**（此处确为 SyntaxError）⇒ 记 syntax，不记 runtime；
        # 出现阶段（运行期）不在这个字段里，别拿它当阶段判据。
        assert r.error_kind == "syntax"
        assert classify("python", r.stderr) == "syntax"
        assert locate("python", r.stderr) == 4, "行号应指向 import 那一行，不是坏模块里的第 1 行"


# ---------------------------------------------------------------------------
# 3) 运行时异常
# ---------------------------------------------------------------------------

class TestRuntimeExceptions:
    @pytest.mark.parametrize("code,frag", [
        ("print(1 / 0)\n", "ZeroDivisionError: division by zero"),
        ("x = {}\nprint(x['k'])\n", "KeyError: 'k'"),
        ("import asyncio\nasyncio.run(main())\n", "NameError"),
        ("def f():\n    return f()\nf()\n", "RecursionError"),
        ("assert 1 == 2, 'nope'\n", "AssertionError: nope"),
    ])
    def test_runtime_exceptions_keep_one_shape(self, runner, code, frag):
        r = runner.run(code)
        assert r.exit_code == 1
        assert frag in r.stderr
        assert r.timed_out is False
        assert r.error_kind == "runtime"
        assert isinstance(r.elapsed_ms, int) and r.elapsed_ms >= 0

    def test_runtime_exception_leaves_stdout_before_the_raise(self, runner):
        """部分输出＋异常：`stdout` 仍保留抛错前已 flush 的内容，不被判定层吞掉。"""
        r = runner.run("print('first', flush=True)\nraise RuntimeError('x')\n")
        assert "first" in r.stdout
        assert r.exit_code == 1
        assert classify("python", r.stderr) == "runtime"


# ---------------------------------------------------------------------------
# 4) 非零退出（不是异常的那种）
# ---------------------------------------------------------------------------

class TestNonZeroExit:
    @pytest.mark.parametrize("code,expect", [
        ("import sys\nsys.exit(3)\n", 3),
        ("raise SystemExit(4)\n", 4),
        ("import os\nos._exit(7)\n", 7),
        ("import sys\nsys.exit('msg')\n", 1),  # 字符串退出 ⇒ 打印到 stderr，码 1
    ])
    def test_explicit_exit_codes_are_propagated_verbatim(self, runner, code, expect):
        r = runner.run(code)
        assert r.exit_code == expect
        assert r.ok is False
        assert r.error_kind == "runtime"
        assert r.timed_out is False

    def test_clean_nonzero_exit_is_classified_as_no_error(self, runner):
        """**D-15**：`ok=False` 但 `classify → "none"`（"没有错误"）——两层互相矛盾。

        配套正向对照：文案层有兜底（`_error_summary("") == "运行失败"`），
        所以学生不至于看到空串；但**退出码从头到尾没上过屏**。
        """
        r = runner.run("import sys\nsys.exit(3)\n")
        assert r.ok is False and r.exit_code == 3
        assert r.stderr == ""
        assert classify("python", r.stderr) == "none"
        assert feedback("python", r.stderr) == ""
        assert _error_summary(r.stderr) == "运行失败"     # 兜底确实在（别误报成"无提示"）
        assert "3" not in _error_summary(r.stderr)         # 实况：退出码丢了

    def test_exit_with_stderr_is_a_runtime_flavoured_failure(self, runner):
        r = runner.run("import sys\nsys.stderr.write('boom')\nsys.exit(9)\n")
        assert r.exit_code == 9
        assert classify("python", r.stderr) == "runtime"
        assert "boom" in r.stderr

    def test_os_exit_skips_buffered_stdout(self, runner):
        """`os._exit` 不走正常收尾 ⇒ 已写入缓冲的输出会丢（判题面看得到，属实况）。"""
        buffered = runner.run("import os\nprint('lost')\nos._exit(0)")
        flushed = runner.run("import os\nprint('kept', flush=True)\nos._exit(0)")
        assert buffered.exit_code == 0
        assert "lost" not in buffered.stdout
        assert "kept" in flushed.stdout


# ---------------------------------------------------------------------------
# 5) 稳定结构（卷宗第二条判据）
# ---------------------------------------------------------------------------

class TestStableStructure:
    def test_field_set_is_exactly_the_documented_eight(self):
        names = [f.name for f in dataclasses.fields(RunResult)]
        assert names == RESULT_FIELDS, names

    def test_every_outcome_class_returns_the_same_shape(self, runner):
        """成功／编译期／运行期／非零退出／超时／公开模式拒绝——六类结局字段类型一致。"""
        cases = [
            "print('x')\n",
            COMPILE_CASES["unclosed-paren"],
            RUNTIME_CASES["zero-division"],
            "import sys\nsys.exit(3)\n",
            "while True: pass",
            "import sys\nprint(sys.argv)\n",
        ]
        for code in cases:
            r = runner.run(code)
            assert isinstance(r, RunResult)
            assert isinstance(r.ok, bool) and isinstance(r.timed_out, bool)
            assert isinstance(r.stdout, str) and isinstance(r.stderr, str)
            assert isinstance(r.elapsed_ms, int) and r.elapsed_ms >= 0
            assert r.rows is None, "python 侧恒不填 rows（只有 SQL 用）"
            assert r.error_kind in OBSERVED_ERROR_KINDS
            assert (r.exit_code is None) == r.timed_out, (
                "实况：只有超时才有 exit_code=None；非超时必带整数码")

    def test_two_runs_of_the_same_code_are_field_for_field_identical(self, runner):
        """可复现性＝稳定结构的硬面：除 `elapsed_ms` 外逐字段相等（同码跑两次）。"""
        code = "import sys\nprint('a' * 10)\nsys.stderr.write('e')\nsys.exit(2)\n"
        a, b = runner.run(code), runner.run(code)
        for f in dataclasses.fields(RunResult):
            if f.name == "elapsed_ms":
                continue
            assert getattr(a, f.name) == getattr(b, f.name), f.name

    def test_public_deploy_returns_a_rejection_not_an_exception(self, runner, monkeypatch):
        """授权拒绝也是同一张结构：`error_kind='sandbox'`、退出码 None、不抛异常。"""
        monkeypatch.setenv("RUNNER_SECURITY_MODE", "public")
        r = runner.run("print('should not run')\n")
        assert isinstance(r, RunResult)
        assert r.ok is False and r.exit_code is None
        assert r.error_kind == "sandbox"
        assert r.stdout == ""
        assert "不允许执行学生代码" in r.stderr
        assert r.timed_out is False

    def test_unicode_and_crlf_sources_keep_the_shape(self, runner):
        """源文本形态（CRLF／中文／emoji 字符串）不改结构，只改内容。"""
        for code in ["print('中文')\r\n", "print('🎯')\n", "x='中'*3\nprint(x)\n"]:
            r = runner.run(code)
            assert r.exit_code == 0, repr(code)
            assert r.ok is True and r.error_kind is None


# ---------------------------------------------------------------------------
# 6) 宿主存活（本单的「不会使服务进程退出」形态）
# ---------------------------------------------------------------------------

class TestHostSurvives:
    def test_no_input_in_the_battery_raises_into_the_host(self, runner):
        """整批坏输入逐个返回 `RunResult`，异常一律不外溢到执行器进程。"""
        battery = list(COMPILE_CASES.values()) + list(RUNTIME_CASES.values()) + [
            "await 1\n", "import os\nos._exit(9)\n", "raise SystemExit\n",
            "x = " + "(" * 4000 + ")" * 4000 + "\n", "\ufeffx = 1\n", "① = 1\n",
        ]
        results = [runner.run(c) for c in battery]
        assert all(isinstance(x, RunResult) for x in results)
        assert len(results) == len(battery) == 13
        assert sum(1 for x in results if x.timed_out) == 0
        assert sys.stdout is not None  # 跑完 15 件后宿主的标准流还在
