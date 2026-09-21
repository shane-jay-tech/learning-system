# -*- coding: utf-8 -*-
"""错题本 _lookup_problem 模块级缓存桩的语义钉（l922-119）。

钉两条此前无测试、但确实是 :10/:16 那 5 行存在理由的语义：
1. **命中不重扫**：同 (lang, pid) 的第二次调用不再触发 find_problem——这是「100 道错题
   从 O(M×P) 降为 O(M+P)」的全部依据；若哪天有人把 :15 的 `if key not in
   _problem_lookup_cache` 改成真值判断，本文件立刻红。
2. **负结论同样进缓存**：find_problem 查无此题返回 (None, None)，该假值元组照样被存进
   字典并复用（判据是 `key not in`，不是 `not cached_value`），所以 missing 题也只扫
   一遍；页面侧 :72/:100 再用 `problem_obj.title if problem_obj else <problem_id>`
   回退成「拿题号当标题」。missing 回退展示这条一并钉住。

失效边界（**已知限制，本单只钉现状语义、不改 ui/**）：
- `_problem_lookup_cache` 是进程级可变全局，**没有任何失效通道**：既不看 content/ 下
  yaml 的 mtime，也不随 st.rerun() 清（rerun 只重跑脚本体，Python 模块对象不销毁）。
  ⇒ 开发模式下改了题面/题号/题目顺序，页面仍拿旧对象，**必须重启 streamlit 进程**才生效。
  test_已知限制_改题库后仍拿旧对象_需重启进程 就是这条限制的可执行说明书。
  加失效（mtime 进键／暴露 clear 入口）属实现变更，需拍板，本单不动 ui/。
- 缓存无上限：键数量级 = 题库题目总数，只存引用不存副本，不构成泄漏面。

测试间隔离（完成标准 ③）：autouse fixture 每例前后清空 `_problem_lookup_cache`。
它是模块级全局，本文件内例与例之间必然互相污染；tests/test_mistakes_edges.py 走的是
打桩 `_lookup_problem`（不碰这个字典），故本 fixture 对那 3 例无副作用。
"""
import pytest

import ui.pages.mistakes as mistakes_page
from tests.test_ui_behavior import FakeStreamlit


class _Problem:
    """替身题目对象：页面只读 .title（:100），不碰别的属性。"""

    def __init__(self, title):
        self.title = title


class _Dao:
    """页面签名要 dao，但 _render_wrong_problems 体内不用它；任何触碰都判越界。"""

    def __getattr__(self, name):
        raise AssertionError(f"渲染函数不该触碰 DAO.{name}（越界＝本测试前提失效）")


@pytest.fixture(autouse=True)
def _清空查找缓存():
    """逐例重置进程级缓存：避免本文件内例间污染，也不把脏字典留给后续文件。"""
    cache = mistakes_page._problem_lookup_cache
    cache.clear()
    yield
    cache.clear()


def _fake_find_problem(result_map):
    """可计数 find_problem 桩。返回 (桩函数, 调用记录 list)。

    result_map: {(lang, pid): (topic_obj, problem_obj)}；表里没有则按真实现返回 (None, None)。
    第三参 content_dir 保留，与 core/loader.find_problem 的签名兼容。
    """
    calls = []

    def fake(lang, pid, content_dir=None):
        calls.append((lang, pid))
        return result_map.get((lang, pid), (None, None))

    return fake, calls


def _mistake(pid, lang="python"):
    return {"lang": lang, "problem_id": pid, "ts": "2026-09-21 13:00:00",
            "code": "print(1)", "ai_feedback": ""}


def _render_with(monkeypatch, pid, result_map):
    """暖好 find_problem 桩＋假 st，渲染一行错题，返回 (markdown 文本, caption 文本, 调用记录)。"""
    fake_find, calls = _fake_find_problem(result_map)
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find)
    st = FakeStreamlit()
    monkeypatch.setattr(mistakes_page, "st", st)
    monkeypatch.setattr(mistakes_page, "navigate_to_problem", lambda *a, **kw: None)
    mistakes_page._render_wrong_problems(_Dao(), [_mistake(pid)])
    markdowns = [str(c[1][0]) for c in st.calls if c[0] == "markdown"]
    captions = [str(c[1][0]) for c in st.calls if c[0] == "caption"]
    return markdowns, captions, calls


# ---------- 语义 1：命中不重扫 ----------

def test_命中路径_同键二次调用不再触发_find_problem(monkeypatch):
    topic, problem = object(), object()
    fake_find, calls = _fake_find_problem({("python", "p1"): (topic, problem)})
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find)

    first = mistakes_page._lookup_problem("python", "p1")
    second = mistakes_page._lookup_problem("python", "p1")

    assert calls == [("python", "p1")], f"命中路径不该重扫，实际调用 {calls}"
    assert first == second == (topic, problem)
    assert mistakes_page._problem_lookup_cache[("python", "p1")] == (topic, problem)


def test_复杂度承诺_M道错题各扫一次_三遍渲染只扫M次(monkeypatch):
    """O(M×P) → O(M+P)：M 道题、被查 3 遍，find_problem 总次数必须是 M 而不是 3M。"""
    keys = [("python", f"p{i}") for i in range(6)]
    fake_find, calls = _fake_find_problem({k: (object(), _Problem(k[1])) for k in keys})
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find)

    for _ in range(3):
        for lang, pid in keys:
            mistakes_page._lookup_problem(lang, pid)

    assert len(calls) == 6, f"应恰好扫 6 次（=题数），实得 {len(calls)}（即退化成 O(M×P)）"
    assert len(mistakes_page._problem_lookup_cache) == 6


def test_缓存键含语言_同题号跨语言不串味(monkeypatch):
    py_problem, sql_problem = _Problem("py"), _Problem("sql")
    fake_find, calls = _fake_find_problem({
        ("python", "same_id"): (object(), py_problem),
        ("sql", "same_id"): (object(), sql_problem),
    })
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find)

    a = mistakes_page._lookup_problem("python", "same_id")
    b = mistakes_page._lookup_problem("sql", "same_id")

    assert calls == [("python", "same_id"), ("sql", "same_id")]
    assert a[1] is py_problem and b[1] is sql_problem, "同 pid 不同 lang 必须各自独立缓存"


# ---------- 语义 2：负结论进缓存 ----------

def test_missing负结论也进缓存_二次调用不重扫(monkeypatch):
    fake_find, calls = _fake_find_problem({})  # 任何题都查不到
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find)

    r1 = mistakes_page._lookup_problem("python", "p_gone")
    r2 = mistakes_page._lookup_problem("python", "p_gone")

    assert r1 == r2 == (None, None)
    assert calls == [("python", "p_gone")], (
        "missing 必须走缓存：若 :15 被改成真值判断，这里会重扫，复杂度承诺被打回 O(M×P)"
    )
    assert ("python", "p_gone") in mistakes_page._problem_lookup_cache


# ---------- 语义 2b：missing 回退 pid 展示（完成标准 ① 的第二例） ----------

def test_missing题_回退用problem_id当标题并给忽略提示(monkeypatch):
    markdowns, captions, calls = _render_with(monkeypatch, "p_gone", {})

    assert any("p_gone" in m for m in markdowns), f"missing 题应以题号兜底，实得 {markdowns}"
    assert any("该题已不在题库中" in c for c in captions), captions
    assert calls == [("python", "p_gone")], f"渲染自身只该扫一次，实得 {calls}"


def test_命中题_渲染用题面对象标题且不回退题号(monkeypatch):
    topic = _Problem("列表推导式")
    result_map = {("python", "p_ok"): (topic, _Problem("列表推导式"))}
    markdowns, captions, calls = _render_with(monkeypatch, "p_ok", result_map)

    assert any("列表推导式" in m for m in markdowns), markdowns
    assert not any("该题已不在题库中" in c for c in captions), captions
    assert calls == [("python", "p_ok")]


def test_暖过缓存后渲染全程零find_problem调用(monkeypatch):
    """命中不重扫在页面侧的落地：先查一次暖库，再渲染整行，渲染阶段调用数不增。"""
    fake_find, calls = _fake_find_problem({("python", "p_ok"): (object(), _Problem("热重载前题面"))})
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find)
    st = FakeStreamlit()
    monkeypatch.setattr(mistakes_page, "st", st)
    monkeypatch.setattr(mistakes_page, "navigate_to_problem", lambda *a, **kw: None)

    mistakes_page._lookup_problem("python", "p_ok")
    assert len(calls) == 1

    mistakes_page._render_wrong_problems(_Dao(), [_mistake("p_ok")])
    assert calls == [("python", "p_ok")], f"暖过缓存后渲染不该重扫，实得 {calls}"
    markdowns = [str(c[1][0]) for c in st.calls if c[0] == "markdown"]
    assert any("热重载前题面" in m for m in markdowns), markdowns


# ---------- 已知限制：进程级缓存无失效通道 ----------

def test_已知限制_改题库后仍拿旧对象_需重启进程(monkeypatch):
    """开发模式改 content/ 下 yaml 后页面看不到新值——本例把该限制钉成可执行说明书。

    若将来给缓存加了失效（mtime 进键、或暴露 clear_* 入口），本例会红，
    届时请同步删掉/改写本文件 docstring 的「失效边界」一节。
    """
    old = _Problem("旧题面")
    fake_find_old, _ = _fake_find_problem({("python", "p1"): (object(), old)})
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find_old)
    assert mistakes_page._lookup_problem("python", "p1")[1] is old

    # 模拟开发者改完 yaml：换成返回新对象的实现
    new = _Problem("改过的题面")
    fake_find_new, calls_new = _fake_find_problem({("python", "p1"): (object(), new)})
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find_new)

    stale = mistakes_page._lookup_problem("python", "p1")[1]
    assert stale is old, "现状：缓存不失效，热重载后仍拿到旧题目对象"
    assert calls_new == [], "仍无任何调用 ⇒ 实现侧没有重载感知（要感知就得先失效）"
    assert not hasattr(mistakes_page, "clear_lookup_cache"), (
        "若新增了显式失效入口，请连同本文件 docstring 的失效边界一起更新"
    )


def test_缓存对象是模块级全局且跨调用保持同一实例(monkeypatch):
    """钉「进程级」这件事本身：字典是模块属性，_lookup_problem 不新建局部缓存。"""
    cache_before = mistakes_page._problem_lookup_cache
    fake_find, _ = _fake_find_problem({("python", "p1"): (object(), _Problem("t"))})
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find)

    mistakes_page._lookup_problem("python", "p1")

    assert mistakes_page._problem_lookup_cache is cache_before, "必须是原地写入，不该整体替换"
    assert ("python", "p1") in mistakes_page._problem_lookup_cache
