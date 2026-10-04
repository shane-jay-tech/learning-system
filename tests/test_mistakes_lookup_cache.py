# -*- coding: utf-8 -*-
"""错题本 _lookup_problem 模块级缓存桩的语义钉（l922-119 立桩，l923-19 随 mtime 失效改版）。

钉两条此前无测试、但确实是 :17/:54 那几行存在理由的语义：
1. **命中不重扫**：同 (lang, pid, mtime) 的第二次调用不再触发 find_problem——这是「100 道错题
   从 O(M×P) 降为 O(M+P)」的全部依据；若哪天有人把 :53 的 `if key not in
   _problem_lookup_cache` 改成真值判断，本文件立刻红。
2. **负结论同样进缓存**：find_problem 查无此题返回 (None, None)，该假值元组照样被存进
   字典并复用（判据是 `key not in`，不是 `not cached_value`），所以 missing 题也只扫
   一遍；页面侧 :115/:143 再用 `problem_obj.title if problem_obj else <problem_id>`
   回退成「拿题号当标题」。missing 回退展示这条一并钉住。

失效边界（**l923-19 已按「键里并 mtime」实装，本节从「无失效通道」改写为新语义**）：
- `_problem_lookup_cache` 仍是进程级可变全局，但键的**第三元是题面 yaml 的 mtime**
  （`_problem_yaml_mtime`）⇒ 改了 content/ 下那道题的 yaml，mtime 变、键 miss、
  **下一帧就拿到新对象，不必重启 streamlit 进程**。写新格时顺手剪掉同题的旧 mtime 格
  （`_drop_stale_entries`），字典不随改题次数无界增长。
- 两个**刻意保留**的退化面，各由一条例钉住：
  ① mtime 取不到（题面文件已删／pid 不是 `<lang>/<slug>/<stem>` 三段式／内容根目录缺失）
     时键退化为 `(lang, pid, None)`，语义回到旧版「一次写入、进程内不失效」，且**不抛错**；
  ② 本层 miss 之后还要过 `core/loader.py` 的签名 memo（`_SIG_TTL_SEC = 2.0`），
     故端到端陈旧窗口是「至多 2 秒」而不是 0。本文件把 find_problem 整体打桩，
     因此 ② 不在本层的断言范围内（要钉它得去 loader 侧，属另一单）。
- 若将来再改成「暴露 clear_lookup_cache() 给热重载钩子」，本文件的 mtime 例应随之改写。
- 缓存无上限这条已收窄：同一题至多留 1 格（旧格被剪），键数量级仍 = 题库题目总数。

测试间隔离（完成标准 ③）：autouse fixture 每例前后清空 `_problem_lookup_cache`。
它是模块级全局，本文件内例与例之间必然互相污染；tests/test_mistakes_edges.py 走的是
打桩 `_lookup_problem`（不碰这个字典），故本 fixture 对那 3 例无副作用。
"""
import os

import pytest

import core.loader as content_loader
import ui.pages.mistakes as mistakes_page
from tests.test_ui_behavior import FakeStreamlit


class _Problem:
    """替身题目对象：页面只读 .title（现读 :115/:143），不碰别的属性。"""

    def __init__(self, title):
        self.title = title


class _Dao:
    """l1002-69 同批：dao 死形参已从 _render_wrong_problems 签名移除。
    本桩降级为「显式 None 传入」形态的占位调用实参（签名清理后调用点不再需要任何实参，
    保留类体只为文档化该前提的演变史；两调用点已改为不传 DAO）。"""

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
    mistakes_page._render_wrong_problems([_mistake(pid)])
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
    # 键的第三元是题面 yaml 的 mtime；"p1" 不是三段式 pid ⇒ 取不到 mtime，退化为 None。
    assert mistakes_page._problem_lookup_cache[("python", "p1", None)] == (topic, problem)


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
    assert ("python", "p_gone", None) in mistakes_page._problem_lookup_cache


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

    mistakes_page._render_wrong_problems([_mistake("p_ok")])
    assert calls == [("python", "p_ok")], f"暖过缓存后渲染不该重扫，实得 {calls}"
    markdowns = [str(c[1][0]) for c in st.calls if c[0] == "markdown"]
    assert any("热重载前题面" in m for m in markdowns), markdowns


# ---------- l923-19：mtime 进键 ⇒ 改题面即失效（本节原名「已知限制：无失效通道」） ----------

def _content_root(monkeypatch, tmp_path):
    """把内容根指到 tmp_path，并造一道真实的 `<lang>/<slug>/<stem>.yaml`。

    返回 (yaml 路径, 三段式 pid)。mtime 由实现自己 stat 真文件得来，夹具不伪装时间戳。
    ⚠️ 这里只把 `core.loader._DEFAULT_CONTENT` 换掉：`_problem_yaml_mtime` 每次调用都现取
    该属性，所以补丁必须打在 loader 模块上而不是 mistakes_page 上（本仓内容根是单源）。
    """
    yaml_path = tmp_path / "python" / "01_x" / "01_p.yaml"
    yaml_path.parent.mkdir(parents=True)
    yaml_path.write_text("title: 旧题面\n", encoding="utf-8")
    monkeypatch.setattr(content_loader, "_DEFAULT_CONTENT", str(tmp_path))
    return yaml_path, "python/01_x/01_p"


def _bump_mtime(path, delta: float = 1.0) -> None:
    """显式把 mtime 前进 delta 秒：不靠"改内容顺带改时间戳"，避开文件系统时间粒度撞车。"""
    st = path.stat()
    os.utime(path, (st.st_atime + delta, st.st_mtime + delta))


def test_mtime辅助_三段式pid映射到题面yaml_其余三类取不到(monkeypatch, tmp_path):
    """mtime 来源自身的边界：能算的算、不能算的返回 None（这是「退化」的入口条件）。"""
    yaml_path, pid = _content_root(monkeypatch, tmp_path)
    assert mistakes_page._problem_yaml_mtime("python", pid) == yaml_path.stat().st_mtime
    assert mistakes_page._problem_yaml_mtime("python", "p1") is None, "非三段式 pid 无从定位文件"
    assert mistakes_page._problem_yaml_mtime("sql", pid) is None, "lang 与 pid 首段不符 ⇒ 不猜路径"
    yaml_path.unlink()
    assert mistakes_page._problem_yaml_mtime("python", pid) is None, "文件已删 ⇒ OSError 被吞成 None"


def test_mtime进键_改题面yaml后下一帧取新值(monkeypatch, tmp_path):
    """l922-119 预告的那条例（原名 `test_已知限制_改题库后仍拿旧对象_需重启进程`）。

    该例当时钉的是「缓存没有任何失效通道，开发模式改题面必须重启进程」，并写明
    「若将来实装了 mtime 进键，本例会红，届时同步删改 docstring 的失效边界节」。
    l923-19 落地的正是 mtime 进键 ⇒ 本例按预告**翻转成新语义**并改名，docstring 已同步。
    """
    yaml_path, pid = _content_root(monkeypatch, tmp_path)
    old = _Problem("旧题面")
    fake_find_old, calls_old = _fake_find_problem({("python", pid): (object(), old)})
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find_old)

    assert mistakes_page._lookup_problem("python", pid)[1] is old
    assert calls_old == [("python", pid)], "首帧必扫一次"
    assert ("python", pid, yaml_path.stat().st_mtime) in mistakes_page._problem_lookup_cache

    # 开发者改完题面：实现换成返回新对象，并把 yaml 的 mtime 前进 1 秒
    new = _Problem("改过的题面")
    fake_find_new, calls_new = _fake_find_problem({("python", pid): (object(), new)})
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find_new)
    _bump_mtime(yaml_path)

    assert mistakes_page._lookup_problem("python", pid)[1] is new, (
        "mtime 变了还拿旧对象 ⇒ 键里没并上 mtime，失效通道没接上")
    assert calls_new == [("python", pid)], "mtime 变更后应重扫恰好一次"


def test_mtime未变_同键仍命中缓存不重扫(monkeypatch, tmp_path):
    """反向守卫（变异有牙用）：mtime 没动就不该重扫——否则「每次都扫表」也能让上一条绿。"""
    _yaml_path, pid = _content_root(monkeypatch, tmp_path)
    fake_find, calls = _fake_find_problem({("python", pid): (object(), _Problem("题面"))})
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find)

    first = mistakes_page._lookup_problem("python", pid)
    for _ in range(5):
        assert mistakes_page._lookup_problem("python", pid) == first

    assert calls == [("python", pid)], f"mtime 未变仍重扫，复杂度承诺被打回 O(M×P)：{calls}"


def test_mtime进键后旧格被剪_反复改题不让字典无界增长(monkeypatch, tmp_path):
    """mtime 进键的副作用收口：同题只留最新那一格（每改一次题就多一格的写法等于漏）。"""
    yaml_path, pid = _content_root(monkeypatch, tmp_path)
    for round_no in range(4):
        fake_find, _ = _fake_find_problem(
            {("python", pid): (object(), _Problem(f"第{round_no}版"))})
        monkeypatch.setattr(mistakes_page, "find_problem", fake_find)
        _bump_mtime(yaml_path, 1.0)
        mistakes_page._lookup_problem("python", pid)

    same_pid = [k for k in mistakes_page._problem_lookup_cache if k[1] == pid]
    assert len(same_pid) == 1, f"同题残留 {len(same_pid)} 格（应为 1）：{same_pid}"
    assert len(mistakes_page._problem_lookup_cache) == 1, mistakes_page._problem_lookup_cache


def test_退化路径_题面yaml不存在时行为回到旧版且不抛错(monkeypatch, tmp_path):
    """完成标准 ②：拿不到 mtime ⇒ 键退化为 `(lang, pid, None)`，仍是「一次写入、进程内不失效」。

    这条不是"顺手加的"：题被删掉但错题表里还留着 problem_id 是真实场景（页面 :115/:143
    正是为此才写 `problem_obj.title if problem_obj else problem_id` 的回退）。
    若把 None 当成"永远 miss"，每次渲染都会重扫全表 ⇒ O(M×P) 回归。
    """
    yaml_path, pid = _content_root(monkeypatch, tmp_path)
    yaml_path.unlink()
    fake_find, calls = _fake_find_problem({("python", pid): (object(), _Problem("孤儿题"))})
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find)

    r1 = mistakes_page._lookup_problem("python", pid)
    r2 = mistakes_page._lookup_problem("python", pid)

    assert r1 == r2, "退化路径应稳定复用同一结果"
    assert calls == [("python", pid)], "mtime 取不到时不得每次重扫（那会把复杂度打回 O(M×P)）"
    assert ("python", pid, None) in mistakes_page._problem_lookup_cache


def test_缓存对象是模块级全局且跨调用保持同一实例(monkeypatch):
    """钉「进程级」这件事本身：字典是模块属性，_lookup_problem 不新建局部缓存。"""
    cache_before = mistakes_page._problem_lookup_cache
    fake_find, _ = _fake_find_problem({("python", "p1"): (object(), _Problem("t"))})
    monkeypatch.setattr(mistakes_page, "find_problem", fake_find)

    mistakes_page._lookup_problem("python", "p1")

    assert mistakes_page._problem_lookup_cache is cache_before, "必须是原地写入，不该整体替换"
    assert ("python", "p1", None) in mistakes_page._problem_lookup_cache
