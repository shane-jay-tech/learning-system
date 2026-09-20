# -*- coding: utf-8 -*-
"""judge_mode 显式化的等价性证明（D6 复核修复，2026-09-20）。

复核意见（GPT 干净版 JUDGE-001）：把 70 道 r 题从「缺失 judge_mode（吃 loader 隐式默认）」
改成「显式 judge_mode: run」，必须证明二者在 **loader / dispatcher / runner / 实题双跑结果**
四层语义完全等价；只靠注释或「loader 默认如此」的口头假设不算证明。

本文件就是那份证明（零网络；只读题库 + 临时目录副本）：
  ① loader 层：真题库 84 题逐个删掉 judge_mode: 行（模拟 D6 之前的写法），
     经 core.loader 归一化后的 Problem 与现状 Problem **dataclass 逐字段全等**；
  ② dispatcher 层：两种写法喂 core.judge.judge()，**走同一条 run 分支**——
     ai_open 分支零调用，runner 收到完全相同的 (code, stdin, expected)；
  ③ runner 层：确定性脚本 runner 对 70 道 run 题 × 正确/错误两种输出全量双跑，
     逐题比对 _run_test_cases 三元组；并用**真 RRunner** 对实题再双跑一遍
     （本机无 Rscript 时两边都拿到同一条「未检测到 Rscript」结果——仍是真 runner
     代码路径的差分对比；装了 R 则直接覆盖真实执行）；
  ④ 结果层：JudgeResult（passed/ai_feedback/expected_display/actual_display/diff_hint）
     逐字段相等，对「输出正确 / 输出错误 / 空代码」三种输入都成立。

**非空转保证（阴性对照）**：另有两个反向用例证明这套比较真的能看出差别——
删掉 ai_open 题的 judge_mode 后，归一化值与判分分支**必须**改变；否则上面的
「等价」就成了恒真断言（判分根本不看 judge_mode 也会通过）。
"""
import glob
import json
import shutil
from pathlib import Path

import yaml

import core.judge as judge_mod
import core.loader as loader_mod
from core.judge import judge
from core.loader import load_language
from core.progress import ProgressDAO
from core.runners.base import RunResult
from core.runners.r_runner import RRunner

CONTENT = Path("content")
CODE = 'cat("Hello, World!\\n")'
AI_OPEN = "ai_open"
RUN = "run"


# ------------------------------------------------------------------ 题库工具

def _r_files():
    return sorted(Path(p) for p in glob.glob("content/r/*/*.yaml"))


def _yaml_of(path: Path) -> dict:
    return yaml.safe_load(path.read_bytes()) or {}


def _pid(path: Path) -> str:
    return "r/%s/%s" % (path.parent.name, path.stem)


def _strip_judge_mode_lines(raw: bytes) -> bytes:
    """删掉第 0 列的 judge_mode: 行——模拟 D6 之前的隐式默认写法（保留原行尾）。"""
    text = raw.decode("utf-8")
    lines = text.splitlines(keepends=True)
    kept = [l for l in lines if not l.startswith("judge_mode:")]
    if len(kept) != len(lines) - 1:
        raise AssertionError("该文件不含恰好一行顶层 judge_mode: 行")
    return "".join(kept).encode("utf-8")


def _mirror_corpus(dst: Path, strip_run: bool):
    """把真题库 r 复制到临时 content/；strip_run 时删掉 run 题的显式 judge_mode 行。"""
    out = Path(dst) / "content" / "r"
    stripped, kept = [], []
    for f in _r_files():
        d = out / f.parent.name
        d.mkdir(parents=True, exist_ok=True)
        raw = f.read_bytes()
        if strip_run and _yaml_of(f).get("judge_mode") == RUN:
            raw = _strip_judge_mode_lines(raw)
            stripped.append(f)
        else:
            kept.append(f)
        (d / f.name).write_bytes(raw)
        lesson = f.parent / "_lesson.md"
        if lesson.exists():
            (d / "_lesson.md").write_bytes(lesson.read_bytes())
    return out.parent, stripped, kept


def _load_pair(tmp_content):
    """同时加载「现状真题库」与「临时改写的题库」，返回两个 topics 列表。"""
    loader_mod.invalidate_cache()
    try:
        return (load_language("r", str(CONTENT.resolve())),
                load_language("r", str(tmp_content)))
    finally:
        loader_mod.invalidate_cache()


class _ScriptedRunner:
    """确定性 runner：固定返回一个 RunResult，并记录每次调用参数。"""

    def __init__(self, result=None, fail_if_called=False):
        self.result = result if result is not None else RunResult(ok=True, stdout="", stderr="")
        self.fail_if_called = fail_if_called
        self.calls = []

    def run(self, code, stdin="", expected=None):
        if self.fail_if_called:
            raise AssertionError("runner 不该被调用")
        self.calls.append({"code": code, "stdin": stdin,
                           "expected": json.dumps(expected or {}, sort_keys=True,
                                                  ensure_ascii=False)})
        return self.result


def _result_tuple(r):
    return (r.passed, r.ai_feedback, r.expected_display, r.actual_display, r.diff_hint)


def _judge_fields(lang, problem, code, dao):
    return _result_tuple(judge(lang, problem, code, dao=dao))


# ------------------------------------------------------------------ ① loader 层

def test_loader层_缺失与显式run_归一等价(tmp_path):
    """70 道 run 题：删掉显式行后，loader 归一化结果与现状**逐字段全等**。"""
    tmp_content, stripped, kept = _mirror_corpus(tmp_path, strip_run=True)
    assert len(stripped) == 70, "应恰有 70 道 run 题被模拟成「缺失」"
    assert len(kept) == 14, "14 道 ai_open 题不该被改动"
    base, alt = _load_pair(tmp_content)

    assert [t.slug for t in base] == [t.slug for t in alt]
    assert sum(len(t.problems) for t in base) == 84
    for bt, at in zip(base, alt):
        assert bt.problems == at.problems, (
            "topic %s 归一化结果不等价：%s" % (
                bt.slug,
                [p.id for pb, p in zip(bt.problems, at.problems) if pb != p]))
        assert [p.to_dict() for p in bt.problems] == [p.to_dict() for p in at.problems]

    # 「缺失」那批的归一化值必须是显式 run，且 id 集合与源文件一一对应
    alt_by_id = {p.id: p for t in alt for p in t.problems}
    assert set(alt_by_id) == {_pid(f) for f in stripped} | {_pid(f) for f in kept}
    for f in stripped:
        assert alt_by_id[_pid(f)].judge_mode == RUN
    for f in kept:
        assert alt_by_id[_pid(f)].judge_mode == AI_OPEN


def test_loader层_阴性对照_删掉ai_open的judge_mode确实改变归一化(tmp_path):
    """非空转保证：若删行不改变任何东西，上面那条等价性测试就是恒真的废测试。"""
    ai_open = [f for f in _r_files() if _yaml_of(f).get("judge_mode") == AI_OPEN]
    assert len(ai_open) == 14
    tmp_content, _, _ = _mirror_corpus(tmp_path, strip_run=False)
    target = ai_open[0]
    (tmp_content / "r" / target.parent.name / target.name).write_bytes(
        _strip_judge_mode_lines(target.read_bytes()))
    base, alt = _load_pair(tmp_content)
    b = {p.id: p for t in base for p in t.problems}[_pid(target)]
    a = {p.id: p for t in alt for p in t.problems}[_pid(target)]
    assert b.judge_mode == AI_OPEN
    assert a.judge_mode == RUN, "缺省即 run——本用例证明这套比较能看出差别"


# ------------------------------------------------------------------ ② dispatcher 层

def _one_run_file():
    runs = [f for f in _r_files() if _yaml_of(f).get("judge_mode") == RUN]
    assert runs
    return runs[0]


def test_dispatcher层_两种写法走同一条run分支(monkeypatch, tmp_path):
    f = _one_run_file()
    explicit = _yaml_of(f)
    missing = {k: v for k, v in explicit.items() if k != "judge_mode"}

    rec = _ScriptedRunner(RunResult(ok=True, stdout=explicit["expected_output"], stderr=""))
    monkeypatch.setitem(judge_mod._RUNNERS, "r", rec)
    open_calls = []

    def _fake_open(*a, **kw):
        open_calls.append(a)
        return {"passed": True, "score": 100, "feedback": "不该走到 ai_open", "llm_ok": True}

    monkeypatch.setattr(judge_mod, "grade_open_answer", _fake_open)
    monkeypatch.setattr(judge_mod, "review", lambda *a, **kw: "FB")
    dao = ProgressDAO(str(tmp_path / "j.db"))
    try:
        r_exp = judge("r", explicit, CODE, dao=dao)
        r_mis = judge("r", missing, CODE, dao=dao)
    finally:
        dao.close()

    assert open_calls == [], "ai_open 分支被调用了——两种写法没有走同一条判分路径"
    assert len(rec.calls) == 2, "runner 调用次数应为 2（每种写法各一次）"
    assert rec.calls[0] == rec.calls[1], "runner 收到的 (code, stdin, expected) 不一致"
    assert r_exp.run_result is not None and r_mis.run_result is not None
    assert _result_tuple(r_exp) == _result_tuple(r_mis)


def test_dispatcher层_loader形态与裸dict形态四路一致(monkeypatch, tmp_path):
    """裸 dict（显式/缺失）与 loader 归一化 Problem（显式/缺失）四种输入结果全等。"""
    f = _one_run_file()
    explicit = _yaml_of(f)
    missing = {k: v for k, v in explicit.items() if k != "judge_mode"}
    tmp_content, _, _ = _mirror_corpus(tmp_path, strip_run=True)
    base_topics, alt_topics = _load_pair(tmp_content)
    p_base = {p.id: p for t in base_topics for p in t.problems}[_pid(f)]
    p_alt = {p.id: p for t in alt_topics for p in t.problems}[_pid(f)]
    assert p_base.judge_mode == RUN and p_alt.judge_mode == RUN

    rec = _ScriptedRunner(RunResult(ok=True, stdout=explicit["expected_output"], stderr=""))
    monkeypatch.setitem(judge_mod._RUNNERS, "r", rec)
    monkeypatch.setattr(judge_mod, "review", lambda *a, **kw: "FB")
    dao = ProgressDAO(str(tmp_path / "j2.db"))
    try:
        got = [_judge_fields("r", p, CODE, dao) for p in (explicit, missing, p_base, p_alt)]
    finally:
        dao.close()
    assert got[0] == got[1] == got[2] == got[3], "四种输入形态的结果不一致：%r" % (got,)
    assert len(rec.calls) == 4 and all(c == rec.calls[0] for c in rec.calls)


def test_dispatcher层_阴性对照_删掉ai_open的judge_mode确实换分支(monkeypatch, tmp_path):
    """反向证据：判分确实看 judge_mode——ai_open 题删掉该行后不再走 AI 分支。"""
    f = [x for x in _r_files() if _yaml_of(x).get("judge_mode") == AI_OPEN][0]
    explicit = _yaml_of(f)
    missing = {k: v for k, v in explicit.items() if k != "judge_mode"}

    calls = {"ai_open": 0, "run": 0}

    def _fake_open(*a, **kw):
        calls["ai_open"] += 1
        return {"passed": True, "score": 90, "feedback": "AI 评分", "llm_ok": True}

    class _CountingRunner(_ScriptedRunner):
        def run(self, code, stdin="", expected=None):
            calls["run"] += 1
            return super().run(code, stdin=stdin, expected=expected)

    monkeypatch.setattr(judge_mod, "grade_open_answer", _fake_open)
    monkeypatch.setattr(judge_mod, "review", lambda *a, **kw: "FB")   # 测试不碰网络
    monkeypatch.setitem(judge_mod._RUNNERS, "r", _CountingRunner())
    dao = ProgressDAO(str(tmp_path / "j3.db"))
    try:
        r_open = judge("r", explicit, "我的回答", dao=dao)
        r_downgraded = judge("r", missing, "我的回答", dao=dao)
    finally:
        dao.close()
    assert calls == {"ai_open": 1, "run": 1}, "两种配置应走不同分支：%r" % calls
    assert r_open.run_result is None and r_downgraded.run_result is not None


# ------------------------------------------------------------------ ③ runner 层 / ④ 结果层

def test_runner层_全量70题_正确与错误输出双跑逐题一致():
    """确定性 runner：每道 run 题在「输出正确 / 输出错误」两种输入下都比一次。"""
    run_problems = [(d, {k: v for k, v in d.items() if k != "judge_mode"})
                    for d in (_yaml_of(f) for f in _r_files()) if d.get("judge_mode") == RUN]
    assert len(run_problems) == 70
    checked = 0
    for explicit, missing in run_problems:
        correct = explicit.get("expected_output") or ""
        for stdout in (correct, correct + "多余的一行"):
            runner = _ScriptedRunner(RunResult(ok=True, stdout=stdout, stderr=""))
            a = judge_mod._run_test_cases(runner, "r", CODE, explicit)
            b = judge_mod._run_test_cases(runner, "r", CODE, missing)
            assert a == b, "题目形态双跑不一致：%r" % (explicit.get("title"),)
            checked += 1
    assert checked == 140, "应覆盖 70 题 × 2 种输出"


def test_runner层_真RRunner实题双跑_逐题RunResult一致():
    """实题双跑：真 RRunner 代码路径下，两种配置产出的 (passed, RunResult, diff_hint) 全等。"""
    real = RRunner()
    has_rscript = bool(shutil.which("Rscript") or real._resolve_rscript())
    run_files = [f for f in _r_files() if _yaml_of(f).get("judge_mode") == RUN]
    sample = run_files if not has_rscript else run_files[:3]  # 装了 R 时控时，抽 3 题
    assert sample, "run 题不得为空"
    for f in sample:
        explicit = _yaml_of(f)
        missing = {k: v for k, v in explicit.items() if k != "judge_mode"}
        a = judge_mod._run_test_cases(real, "r", CODE, explicit)
        b = judge_mod._run_test_cases(real, "r", CODE, missing)
        assert a == b, "真 runner 双跑不一致（Rscript=%s）：%s" % (has_rscript, _pid(f))
    assert len(sample) >= 1


def test_结果层_输出正确错误与空代码三种输入都等价(monkeypatch, tmp_path):
    f = _one_run_file()
    explicit = _yaml_of(f)
    missing = {k: v for k, v in explicit.items() if k != "judge_mode"}
    correct = explicit.get("expected_output") or ""
    monkeypatch.setattr(judge_mod, "review", lambda *a, **kw: "FB")
    dao = ProgressDAO(str(tmp_path / "j4.db"))
    try:
        for stdout in (correct, "错误的输出"):
            monkeypatch.setitem(judge_mod._RUNNERS, "r",
                                _ScriptedRunner(RunResult(ok=True, stdout=stdout, stderr="")))
            assert _judge_fields("r", explicit, CODE, dao) == _judge_fields("r", missing, CODE, dao)
        # 空代码：走 judge() 的早期返回，同样不看 judge_mode
        monkeypatch.setitem(judge_mod._RUNNERS, "r", _ScriptedRunner())
        a = _judge_fields("r", explicit, "   ", dao)
        b = _judge_fields("r", missing, "   ", dao)
        assert a == b and a[0] is False and a[4] == "代码为空"
    finally:
        dao.close()


# ------------------------------------------------------------------ 数据层契约

def test_数据层_84题源文件显式值与loader归一化值一致():
    from collections import Counter
    src = Counter()
    for f in _r_files():
        mode = _yaml_of(f).get("judge_mode")
        assert mode in (RUN, AI_OPEN), "%s 的 judge_mode 非法：%r" % (f, mode)
        src[mode] += 1
    assert dict(src) == {RUN: 70, AI_OPEN: 14}
    loader_mod.invalidate_cache()
    try:
        loaded = Counter(p.judge_mode for t in load_language("r") for p in t.problems)
    finally:
        loader_mod.invalidate_cache()
    assert dict(loaded) == dict(src), "源文件显式值与 loader 归一化值不一致"


def test_loader默认值契约_缺失None空串都归一为run():
    """归一化规则的书面契约：只有 ai_open 是特例，其余一律 run。"""
    for variant in ({}, {"judge_mode": None}, {"judge_mode": ""}, {"judge_mode": RUN}):
        data = dict(variant, title="t", statement="s")
        p = loader_mod._build_problem("r", "topic", "/tmp/01_x.yaml", data)
        assert p.judge_mode == RUN, "variant=%r 归一化为 %r" % (variant, p.judge_mode)
    p = loader_mod._build_problem("r", "topic", "/tmp/01_x.yaml", {"judge_mode": AI_OPEN})
    assert p.judge_mode == AI_OPEN
