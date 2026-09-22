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
    assert ai_review._cache_open_result("python", "p1", "答案", ok) is ok
    assert ai_review._cached_open_result("python", "p1", "答案") == ok
    # llm_ok=False 不落缓存：基础设施失败时学生重试仍会真调
    fail = {"passed": False, "score": None, "feedback": "AI 评判暂时不可用", "llm_ok": False}
    assert ai_review._cache_open_result("python", "p2", "答案", fail) is fail
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
