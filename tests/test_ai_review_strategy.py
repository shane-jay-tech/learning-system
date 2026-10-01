"""Test AI review prompt strategy selection by difficulty."""
import hashlib
from collections import OrderedDict

import pytest

from unittest.mock import patch, MagicMock

import core.ai_review as ai_review
from core.ai_review import (
    _build_review_system_prompt,
    _SYSTEM_PROMPT_STRICT,
    _SYSTEM_PROMPT_BEGINNER_PASS,
    _SYSTEM_PROMPT_BEGINNER_FAIL,
)


def test_beginner_pass_uses_encouragement():
    prompt = _build_review_system_prompt(difficulty=1, passed=True, lang="python")
    assert prompt == _SYSTEM_PROMPT_BEGINNER_PASS
    assert "自信心" in prompt
    assert "做对了什么" in prompt


def test_beginner_fail_uses_gentle_correction():
    prompt = _build_review_system_prompt(difficulty=2, passed=False, lang="python")
    assert prompt == _SYSTEM_PROMPT_BEGINNER_FAIL
    assert "变量追踪" in prompt
    assert "一个最关键的问题" in prompt


def test_advanced_uses_strict_review():
    prompt = _build_review_system_prompt(difficulty=3, passed=True, lang="python")
    assert prompt == _SYSTEM_PROMPT_STRICT
    assert "代码品质" in prompt


def test_difficulty_4_uses_strict():
    prompt = _build_review_system_prompt(difficulty=4, passed=False, lang="cpp")
    assert prompt == _SYSTEM_PROMPT_STRICT


def test_difficulty_5_uses_strict():
    prompt = _build_review_system_prompt(difficulty=5, passed=True, lang="sql")
    assert prompt == _SYSTEM_PROMPT_STRICT


def test_beginner_pass_no_mandatory_critique():
    prompt = _build_review_system_prompt(difficulty=1, passed=True, lang="python")
    assert "即使代码完全正确，也要给至少 1 条可改进点" not in prompt
    assert "肯定" in prompt or "鼓励" in prompt


def test_beginner_fail_limits_code_examples():
    prompt = _build_review_system_prompt(difficulty=2, passed=False, lang="r")
    assert "不贴超过 2 行" in prompt


# ===========================================================================
# 缓存层补测（l922-10-learn-aireview-cache，2026-09-22 追加）
# 直钉 core/ai_review.py:54/64/69/73/83/90 六个私有符号：
#   _cache_feedback / _cached_feedback / _open_key / _cache_open_result /
#   _cached_open_result / _trim
# 为什么打在函数对上而不是只走 review()/grade_open_answer()：顶层入口每次
# 先 _feedback_cache.clear() 再各喂自己那一类，会抹平三件真实语义——
# 容量截断的确切边界、两类缓存共挤同一只 OrderedDict、读写两侧的复制不对称。
# 全程离线：不碰 _call/_call_chain，零 LLM、零子进程、零网络。
# 上面 7 例（_build_review_system_prompt）未改动、未删除。
# ---------------------------------------------------------------------------
# l923-05（2026-09-23 追加）：① 注释口径订正为 FIFO（core/ai_review.py 缓存段头注释，零行为变更）；
# ② "读写两侧的复制不对称"被修掉了——新增第 7 个私有符号 _copy_open_result，写侧与读侧都过它，
#    故 l922-10 那条"浅复制现状桩"改为修好版断言，另加 1 例钉 append/sort 不串改缓存。
#    容量截断/FIFO 顺位/跨类挤占三例语义未动、仍绿。
# ===========================================================================


@pytest.fixture
def cache(monkeypatch):
    """换一只干净的 OrderedDict 承接缓存用例，跑完自动还原，不污染其他测试。"""
    fresh = OrderedDict()
    monkeypatch.setattr(ai_review, "_feedback_cache", fresh)
    return fresh


def test_cache_feedback_write_read_roundtrip_and_miss_never_raises(cache):
    text = "【思路】通过。\n【代码品质】命名清晰。"
    assert ai_review._cache_feedback("python", "p1", "print(1)", text) == text  # 原样回传
    assert ai_review._cached_feedback("python", "p1", "print(1)") == text
    # 未写入的邻接键全部 None（未命中不抛、不回落到空串）
    assert ai_review._cached_feedback("python", "p2", "print(1)") is None
    assert ai_review._cached_feedback("cpp", "p1", "print(1)") is None
    assert ai_review._cached_feedback("python", "p1", "print(2)") is None
    assert len(cache) == 1


def test_cache_feedback_skips_all_three_unusable_inputs(cache):
    """钉住 :55 的三个短路条件各自独立生效，且短路时仍原样返回文本。"""
    cases = [
        ("python", "p1", "c", ""),                          # not text
        ("python", "p1", "c", "AI 点评暂时不可用，请稍后再试。"),  # 兜底文案
        ("python", "", "c", "正常点评"),                     # not pid
    ]
    for lang, pid, code, text in cases:
        assert ai_review._cache_feedback(lang, pid, code, text) == text
    assert len(cache) == 0
    assert ai_review._cached_feedback("python", "p1", "c") is None
    assert ai_review._cached_feedback("python", "", "c") is None


def test_cache_feedback_key_shape_is_lang_pid_sha1_of_code(cache):
    ai_review._cache_feedback("python", "p1", "print(1)", "点评")
    assert list(cache) == [("python", "p1", hashlib.sha1(b"print(1)").hexdigest())]
    # 代码含非 ASCII 时走 errors="replace"，不因编码炸键
    weird = "打印🙂"
    ai_review._cache_feedback("python", "p1", weird, "点评2")
    assert list(cache)[1] == ("python", "p1",
                              hashlib.sha1(weird.encode("utf-8", errors="replace")).hexdigest())


def test_cache_feedback_trim_boundary_is_strictly_over_capacity(cache):
    """截断边界：恰好 _FEEDBACK_CACHE_MAX 条一条不丢，第 MAX+1 条才淘汰最旧。"""
    n = ai_review._FEEDBACK_CACHE_MAX
    for i in range(n):
        ai_review._cache_feedback("python", f"p{i}", "c", "点评")
    assert len(cache) == n
    assert ai_review._cached_feedback("python", "p0", "c") == "点评"
    ai_review._cache_feedback("python", "p-new", "c", "点评")
    assert len(cache) == n                                   # 只截不回涨
    assert ai_review._cached_feedback("python", "p0", "c") is None        # 最旧出局
    assert ai_review._cached_feedback("python", "p1", "c") == "点评"      # 次旧仍在
    assert ai_review._cached_feedback("python", "p-new", "c") == "点评"   # 最新在场


def test_cache_feedback_reinsert_updates_value_but_not_eviction_rank(cache):
    """钉现状：重复写同键只改值、不刷新顺位（OrderedDict 赋值不 move_to_end），
    所以这是 FIFO 而非真 LRU。将来若改成真 LRU，本例转红=一次可见的行为决策。"""
    n = ai_review._FEEDBACK_CACHE_MAX
    for i in range(n):
        ai_review._cache_feedback("python", f"p{i}", "c", "旧")
    for _ in range(3):
        ai_review._cache_feedback("python", "p0", "c", "新")
    assert list(cache)[0] == ("python", "p0", hashlib.sha1(b"c").hexdigest())
    assert cache[list(cache)[0]] == "新"                     # 值改了，位置没动
    ai_review._cache_feedback("python", "p-extra", "c", "新")
    assert ai_review._cached_feedback("python", "p0", "c") is None   # 被踢的仍是 p0


def test_open_key_is_stable_and_discriminates_every_argument():
    key = ai_review._open_key("python", "p1", "答案")
    assert key == ai_review._open_key("python", "p1", "答案")   # 进程内可复现
    assert key[0] == "open" and len(key) == 4
    assert key[1:3] == ("python", "p1")
    assert key[3] == hashlib.sha1("答案".encode("utf-8", errors="replace")).hexdigest()
    variants = {
        ai_review._open_key("python", "p1", "答案"),
        ai_review._open_key("python", "p2", "答案"),            # 换题
        ai_review._open_key("cpp", "p1", "答案"),               # 换语言
        ai_review._open_key("python", "p1", "答案。"),           # 换答案（只差标点）
        ai_review._open_key("python", "p1", ""),                # 空答案
    }
    assert len(variants) == 5


def test_open_result_cache_roundtrip_miss_and_llm_failure_guard(cache):
    ok = {"passed": True, "score": 88, "feedback": "不错", "llm_ok": True}
    # l930-13：返回值改交副本（不再把活字典交回调用方）——相等但非同一对象。
    ret = ai_review._cache_open_result("python", "p1", "答案", ok)
    assert ret == ok and ret is not ok, "返回值应为内容相等的副本"
    assert ai_review._cached_open_result("python", "p1", "答案") == ok
    # llm_ok=False 不落缓存：基础设施失败时学生重试仍会真调（返回值同副本契约）
    fail = {"passed": False, "score": None, "feedback": "AI 评判暂时不可用", "llm_ok": False}
    ret_fail = ai_review._cache_open_result("python", "p2", "答案", fail)
    assert ret_fail == fail and ret_fail is not fail
    assert ai_review._cached_open_result("python", "p2", "答案") is None
    assert ai_review._cached_open_result("python", "p1", "别的答案") is None
    assert ai_review._cached_open_result("cpp", "p1", "答案") is None
    assert len(cache) == 1


def test_open_result_cache_isolates_dimensions_on_both_sides(cache):
    """🔴 l923-05 改造例（原名 test_open_result_cache_copy_is_shallow_on_both_sides）：
    l922-10 当时钉的是"两侧都只 dict() 浅复制 ⇒ dimensions 那只列表共享"这个**缺陷现状**。
    现写侧与读侧都过 _copy_open_result（顶层浅复制 + dimensions 逐元素复制），本例改为修好版断言：
    缓存之后对调用方手里那份、或对读出来的那份做任何就地改动，都不再串改缓存。
    顶层键原本就隔离，语义未变。"""
    result = {"passed": True, "score": 80, "dimensions": [{"name": "正确性"}], "llm_ok": True}
    ai_review._cache_open_result("python", "p1", "答案", result)
    result["score"] = 0
    stored = ai_review._cached_open_result("python", "p1", "答案")
    assert stored["score"] == 80                                 # 顶层：写侧隔离（原本就有）
    result["dimensions"].append({"name": "污染"})                 # 写侧漏点：调用方就地 append
    assert len(stored["dimensions"]) == 1, stored["dimensions"]
    result["dimensions"][0]["name"] = "被改"                      # 元素级也不共享
    assert stored["dimensions"][0]["name"] == "正确性"
    stored["passed"] = False                                     # 读侧漏点：改返回值
    assert ai_review._cached_open_result("python", "p1", "答案")["passed"] is True
    assert len(ai_review._cached_open_result("python", "p1", "答案")["dimensions"]) == 1


def test_取缓存结果后就地_append_sort_dimensions_再取缓存不变(cache):
    """l923-05 完成标准②：读出来的结果被就地 append/sort/reverse 后，再取缓存仍原样；
    且两次读出是不同对象（谁都改不动谁）。淘汰/容量语义不在本例范围（上面几例仍钉 FIFO）。"""
    dims = [{"name": "正确性", "score": 90}, {"name": "风格", "score": 60}]
    ai_review._cache_open_result("python", "p1", "答案",
                                 {"passed": True, "score": 75, "dimensions": dims, "llm_ok": True})
    first = ai_review._cached_open_result("python", "p1", "答案")
    snapshot = [dict(d) for d in first["dimensions"]]
    first["dimensions"].append({"name": "污染"})
    first["dimensions"].sort(key=lambda d: d["name"])
    first["dimensions"].reverse()
    dims.append({"name": "写侧也污染"})                            # 调用方手里那只同样不相连
    again = ai_review._cached_open_result("python", "p1", "答案")
    assert again["dimensions"] == snapshot, again["dimensions"]
    assert len(again["dimensions"]) == 2
    assert again is not first
    assert again["dimensions"] is not first["dimensions"]


def test_code_and_open_caches_share_one_trim_budget(cache):
    """两类缓存同挤一只 _feedback_cache：open 结果灌进来会把代码点评挤掉。
    顶层用例各喂一类，看不出这条争用。"""
    n = ai_review._FEEDBACK_CACHE_MAX
    ai_review._cache_feedback("python", "code-p", "c", "点评")
    for i in range(n):                                           # 1 + MAX 条 = 溢出 1
        ai_review._cache_open_result("python", f"o{i}", "a", {"llm_ok": True})
    assert len(cache) == n
    assert ai_review._cached_feedback("python", "code-p", "c") is None           # 跨类挤占
    assert ai_review._cached_open_result("python", "o0", "a") == {"llm_ok": True}
    ai_review._cache_open_result("python", f"o{n}", "a", {"llm_ok": True})       # 再溢 1
    assert len(cache) == n
    assert ai_review._cached_open_result("python", "o0", "a") is None            # 同侧淘汰
    assert ai_review._cached_open_result("python", f"o{n - 1}", "a") == {"llm_ok": True}
    assert ai_review._cached_open_result("python", f"o{n}", "a") == {"llm_ok": True}


def test_open_and_code_cache_namespaces_never_collide(cache):
    """同一 (lang, pid, 原文) 在两处各存一份：键元数 4 vs 3，天然不串台。"""
    ai_review._cache_feedback("python", "p1", "同一份文本", "代码点评")
    ai_review._cache_open_result("python", "p1", "同一份文本", {"score": 70, "llm_ok": True})
    assert ai_review._cached_feedback("python", "p1", "同一份文本") == "代码点评"
    assert ai_review._cached_open_result("python", "p1", "同一份文本")["score"] == 70
    assert len(cache) == 2


# ---------------------------------------------------------------------------
# l927-56（2026-09-28 追加）：FIFO 断言面补齐＝现状钉桩，不是升级。
#   裁决状态：l927-35（FIFO 升 LRU 裁决材料）卷宗仍在 inbox 未执行；`l924-20` 的
#   两案稿 `docs/insights/learn-review-cache-lru-verdict-20260924.md` §六 明写「选案交人工」，
#   待人工台账 `D:\code\docs\insights\drain-20260923-pending-human.md` 现点 LRU 命中 0 行，
#   `D:\code\docs\decisions\` 零授权件 ⇒ **未拍板** ⇒ 本段只把现状钉住，不改语义、不放宽任何在册断言。
#   上游只钉了一条顺位桩（:134，且只覆盖代码点评写路径），"读命中不续命""open 写路径复写
#   不刷新顺位""两类共用同一只顺位"三格全空 ⇒ 按 l924-20 §二 的三态口径（FIFO／LRU-w／LRU-rw）补平。
#   断言一律「动作可经生产读路径，顺位判定不经读路径」＝直接看 `list(cache)`，
#   这是 §三 点名的修法形状（在册 :120 用读来探淘汰对象，本身是 lru-rw 下会误伤的那一格，故本段不仿它）。
#   将来真升级时本段每一例转红都是**一次可见的行为决策**，逐例归因见 docstring 与 note 档。
#   全程离线：零 LLM、零子进程、零网络、零写盘；只用 fixture 换上的干净 OrderedDict。
# ---------------------------------------------------------------------------


def _ck(pid, code="c", lang="python"):
    """代码点评键形（core/ai_review.py:62 的拼法，测试侧只用于比对键序，不写缓存）。"""
    return (lang, pid, hashlib.sha1(code.encode("utf-8", errors="replace")).hexdigest())


def _ok(pid, answer="a", lang="python"):
    """开放题键形＝直接调被测函数，避免在测试里重抄一遍 sha1 拼法。"""
    return ai_review._open_key(lang, pid, answer)


def test_cache_read_hit_does_not_refresh_eviction_rank(cache):
    """钉现状（LRU-rw 那一格）：**命中读不续命**。
    `_cached_feedback` 走 `_feedback_cache.get(key)`（:71），get 不 move_to_end ⇒
    反复读最旧那条也不会把它挪到队尾，超容量时被淘汰的仍是它。
    真 LRU（读也刷新）下本例当场红在第 1 条断言（读三下之后队首已经不是 p0）。
    在册 :120 只把"读"当探针用、顺带碰到这格语义，从未以"读命中"为动作对象钉过。"""
    n = ai_review._FEEDBACK_CACHE_MAX
    for i in range(n):
        ai_review._cache_feedback("python", f"p{i}", "c", "点评")
    oldest = _ck("p0")
    for _ in range(3):
        assert ai_review._cached_feedback("python", "p0", "c") == "点评"   # 命中：读得到
    assert list(cache)[0] == oldest, "读命中把条目挪位了 ⇒ 已是 LRU-rw 而非现状 FIFO"
    assert len(cache) == n                                                 # 读不新增条目
    ai_review._cache_feedback("python", "p-new", "c", "点评")
    assert oldest not in cache, "被踢的应仍是 p0（读命中不救它）"
    assert _ck("p1") in cache and _ck("p-new") in cache


def test_open_result_reinsert_updates_value_but_not_eviction_rank(cache):
    """钉现状（LRU-w 在 open 写路径那一格）：:134 只钉了 `_cache_feedback`，
    而 `_cache_open_result`（:95-101）是同形码的第二份拷贝（各自 `_feedback_cache[key] = ...`
    ＋各自 `while ... popitem(last=False)`），此前**无任何顺位桩**。
    本例＝:134 在开放题侧的孪生：复写同键只换值、不动位置，超容量时被踢的仍是它。"""
    n = ai_review._FEEDBACK_CACHE_MAX
    for i in range(n):
        ai_review._cache_open_result("python", f"o{i}", "a", {"score": i, "llm_ok": True})
    oldest = _ok("o0")
    for i in range(3):
        ai_review._cache_open_result("python", "o0", "a", {"score": 900 + i, "llm_ok": True})
    assert list(cache)[0] == oldest, "复写同键把它挪到队尾了 ⇒ 写路径已是 LRU-w"
    assert cache[oldest]["score"] == 902              # 值改了（最后一次写生效）
    assert len(cache) == n                            # 复写不涨条目
    ai_review._cache_open_result("python", "o-extra", "a", {"score": 1, "llm_ok": True})
    assert oldest not in cache, "被踢的应仍是 o0（复写不刷新顺位）"
    assert _ok("o1") in cache and _ok("o-extra") in cache


def test_both_write_paths_share_one_insertion_rank(cache):
    """钉现状（共用一只缓存＝共用一条顺位）：两类写路径交替灌、各自复写队首若干次后，
    `list(cache)` 仍逐位等于**首次插入序**。
    在册 :216 钉的是"共用一只**预算**"（容量争用），本例钉的是"共用一条**顺位**"——
    这是另一格：分池方案（l924-20 案 A）若只做容量分池而保留 FIFO，本例仍绿；
    任何一侧偷偷加 `move_to_end`（LRU-w）都会让本例在第 1 条断言红，且红侧能指出是哪一族键。"""
    n = ai_review._FEEDBACK_CACHE_MAX
    insert_order = []
    for i in range(n // 2):
        ai_review._cache_feedback("python", f"c{i}", "c", "点评")
        insert_order.append(_ck(f"c{i}"))
        ai_review._cache_open_result("python", f"o{i}", "a", {"llm_ok": True})
        insert_order.append(_ok(f"o{i}"))
    assert len(insert_order) == n and len(cache) == n
    # 两类各复写队首 2 次（值变、位置不许变）
    ai_review._cache_feedback("python", "c0", "c", "点评2")
    ai_review._cache_open_result("python", "o0", "a", {"llm_ok": True, "score": 7})
    ai_review._cache_feedback("python", "c0", "c", "点评3")
    ai_review._cache_open_result("python", "o0", "a", {"llm_ok": True, "score": 8})
    assert list(cache) == insert_order, "交替灌＋复写后的键序不等于首次插入序"
    assert cache[_ck("c0")] == "点评3" and cache[_ok("o0")]["score"] == 8   # 值确实被复写过
    ai_review._cache_feedback("python", "c-overflow", "c", "点评")
    assert list(cache)[0] == insert_order[1]           # 淘汰的仍是最先插入的 c0
    assert insert_order[0] not in cache
    assert list(cache) == insert_order[1:] + [_ck("c-overflow")]
    assert len(cache) == n                             # 只截不回涨（:120 已钉，此处钉混合流下同一条）


def test_variant_pid_entries_are_evicted_by_same_fifo_rank(cache):
    """钉现状（卷宗标题"变式题缓存"的落点）：盘上**没有第二只**变式题缓存，
    变式题点评与真题点评同挤 `core/ai_review.py:55` 那一只是 OrderedDict，
    键形只是把 pid 换成 `AI_VARIANT::<原题 id>`（`core/ai_generate.py:105` 的拼法）。
    ⇒ 变式题条目**不享有任何淘汰豁免**，FIFO⇄LRU 一次升级的爆炸半径必然含它。
    （对照：真题侧会话状态键有 `_LRU_CAP=30` 那套、变式走 `_variant_lru`，那是**另一件事**，
    在 ui/pages/language.py，与本只 LLM 点评缓存无关，勿串案。）"""
    n = ai_review._FEEDBACK_CACHE_MAX
    variant = "AI_VARIANT::python/01_basics/p1"
    insert_order = []
    for i in range(n // 2):
        ai_review._cache_feedback("python", f"p{i}", "c", "真题点评")
        insert_order.append(_ck(f"p{i}"))
        ai_review._cache_feedback("python", f"{variant}_{i}", "c", "变式点评")
        insert_order.append(_ck(f"{variant}_{i}"))
    assert list(cache) == insert_order
    # 复写最旧那条变式条目：只改值、不刷新顺位
    ai_review._cache_feedback("python", f"{variant}_0", "c", "变式点评改")
    assert list(cache)[0] == insert_order[0]
    assert cache[insert_order[1]] == "变式点评改"
    # 读命中同样不救它
    assert ai_review._cached_feedback("python", f"{variant}_0", "c") == "变式点评改"
    assert list(cache)[0] == insert_order[0]
    # 挤两条：出局顺序严格按首次插入序，先真题 p0、再变式那条 ⇒ 无淘汰豁免
    ai_review._cache_feedback("python", "p-extra1", "c", "挤一条")
    assert insert_order[0] not in cache and insert_order[1] in cache
    assert len(cache) == n
    ai_review._cache_feedback("python", "p-extra2", "c", "挤两条")
    assert insert_order[1] not in cache, "变式条目被豁免／真题条目被多踢 ⇒ 顺位口径已变"
    assert cache[insert_order[2]] == "真题点评"           # 第三顺位（真题）仍在场
    assert cache[_ck("p-extra2")] == "挤两条"
    assert len(cache) == n


def test_feedback_cache_capacity_constant_is_pinned_at_current_value(cache):
    """钉现状（容量与容器）：:120/:134/:216 全部动态读 `ai_review._FEEDBACK_CACHE_MAX`
    ⇒ 把 64 改成 192（l924-20 案 A 的容量半段）**不会让任何在册用例红**，这是断言面的真空格。
    本例把现值钉死，并钉"全仓只有一只点评缓存容器"（案 A 分池会当场红在这里＝一次可见决策）。
    🔴 这不是"容量应该是 64"的技术结论——命中率与容量的数值裁决属 l924-20 §四／§五，交人工。"""
    assert ai_review._FEEDBACK_CACHE_MAX == 64
    assert isinstance(ai_review._feedback_cache, OrderedDict)
    containers = [n for n in dir(ai_review) if n.endswith("_cache") or n.endswith("_CACHE")]
    assert containers == ["_feedback_cache"], f"点评缓存容器出现第二只：{containers}"
    # 现值自洽：容量常量与头注释里的"64 条"口径同源（注释若改数而常量没改＝口径漂移）
    with open(ai_review.__file__, encoding="utf-8") as f:
        src = f.read()
    assert "64 条容量" in src or "共用 64 条容量" in src, "缓存段头注释的容量口径已漂离常量"


def test_cache_section_comment_still_self_describes_fifo(cache):
    """钉现状（注释⇄实现口径一致，防 l922-10 那次"注释说 LRU、实现是 FIFO"的漂移复发）：
    缓存段头注释必须仍明示 FIFO，且不得再次出现把现状说成 LRU 的字样。
    🔴 只跑测试时读源码（非 import 期），编码写死 utf-8（本仓 autocrlf=true ⇒ 工作树是 CRLF，
    子串判定不受行尾影响，但别拿字节数比对）。"""
    with open(ai_review.__file__, encoding="utf-8") as f:
        src = f.read()
    head = src.split("def _cache_feedback", 1)[0]
    assert len(head) > 0
    assert "淘汰语义是 FIFO" in head, "头注释不再明示 FIFO ⇒ 语义或注释已改动，本段钉桩需同步定夺"
    # LRU 二字只允许以"曾被否证的历史指涉"出现（l923-05 保留的那句），不许变成现役口径
    assert "不是注释曾写的「LRU 上限 64 条」" in head, "历史指涉句式被改写 ⇒ 需复核 LRU 二字是否被当现役口径"
    assert "改成真 LRU 是一次行为决策" in head
    fifo_line = next(ln for ln in head.splitlines() if "淘汰语义是 FIFO" in ln)
    assert "popitem" in head and "move_to_end" in head, "钉桩依据（实现侧两行自述）被摘掉 ⇒ 本段失去可追溯性"
    assert fifo_line.lstrip().startswith("#"), f"明示 FIFO 的那行不再是注释：{fifo_line[:40]}"


def test_trim_default_limit_and_exact_boundary():
    """_trim 是 core.utils.trim_text 的薄包装：默认档 _MAX_FIELD，边界在 len<=n。"""
    from core.utils import trim_text
    n = ai_review._MAX_FIELD
    assert ai_review._trim("x" * n) == "x" * n                  # 恰好上限：原样返回
    cut = ai_review._trim("x" * (n + 1))
    assert cut != "x" * (n + 1) and cut.startswith("x" * n)
    assert "已截断" in cut and f">{n} 字符" in cut
    assert len(cut) > n                                         # 标记本身另占位，输出不受 n 硬约束
    assert ai_review._trim("abc", 10) == "abc"
    assert ai_review._trim("", 10) == ""
    assert ai_review._trim(None, 10) == ""
    assert ai_review._trim("abcdef", 4) == "abcd\n[... 已截断（>4 字符）]"
    long_s = "y" * (n + 500)
    assert ai_review._trim(long_s) == trim_text(long_s, n)       # 与底层同义，无额外加工
