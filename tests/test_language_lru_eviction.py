# -*- coding: utf-8 -*-
"""语言页题目状态 LRU 逐出桩（l922-113，钉 ui/pages/language.py::_touch_problem）。

现状盘点（任务书称「这套逐出含精细逻辑，目前零直接测试」——**该表述已过期**）：
tests/test_ui_behavior.py::test_problem_state_lru_prunes_old_problems 已有一份粗覆盖
（40 道题 → 前 10 道的 code::/chat_history::/editor 键消失、队列有界、AI 变式豁免）。
真正从未被断言的四个空白，本档补齐：

  A. 六个前缀里的 chat_ctx:: / preask_hist:: / show_preask:: / editor_epoch::
     ——删掉前缀表中任一项，老测试都不会红；
  B. rsplit("_", 1)[0] == pid 的**精确匹配**语义——老测试的 pid 不含下划线，
     没有「相似 pid 不被误删」的反例，也没有同一题多 epoch 残键；
  C. 窗口边界 -_LRU_CAP 的 off-by-one（32 题恰好逐出最旧 2 道，第 3 道必须活）；
  D. `if pid in keep_ids: continue` 这行——重访一道已被挤出窗口的题时，
     它在 lru[:-CAP] 里出现两次，其状态必须保留。这行最容易改错。

源码零改动；只新增测试。可复跑：
python -m pytest tests/test_language_lru_eviction.py -q
"""
from pathlib import Path

import pytest

import ui.pages.language as language_page
from tests.test_ui_behavior import FakeStreamlit

SIX_PREFIXES = ("code::", "chat_ctx::", "chat_history::", "preask_hist::",
                "show_preask::", "editor_epoch::")


def _seed(fake, pid, epochs=(0, 1)):
    """给一道题种满六类状态键 + 若干 editor widget epoch 键。"""
    for prefix in SIX_PREFIXES:
        fake.session_state[prefix + pid] = f"v:{prefix}"
    for e in epochs:
        fake.session_state[f"editor_{pid}_{e}"] = f"code:{e}"


def _survivors(fake, pid):
    return [p for p in SIX_PREFIXES if p + pid in fake.session_state]


@pytest.fixture()
def fake(monkeypatch):
    f = FakeStreamlit()
    monkeypatch.setattr(language_page, "st", f)
    return f


class TestSixPrefixCensus:
    def test_all_six_prefixes_cleared_for_evicted_problem(self, fake):
        cap = language_page._LRU_CAP
        ids = [f"lang/topic/p{i}" for i in range(cap + 2)]     # 32 道
        for pid in ids:
            _seed(fake, pid)
            language_page._touch_problem(pid)

        for pid in ids[:2]:                                     # 最旧 2 道
            assert _survivors(fake, pid) == [], f"{pid} 仍有前缀键未回收：{_survivors(fake, pid)}"
            assert [k for k in fake.session_state if k.startswith(f"editor_{pid}_")] == []
        for pid in ids[2:]:                                     # 其余 30 道（含当前题）
            assert _survivors(fake, pid) == list(SIX_PREFIXES), f"{pid} 被误清理"

    def test_prefix_table_itself_pinned(self):
        """前缀表增删都要显式过本档：六项、与 :44-45 字面一致；上限与注释同数字。"""
        assert set(language_page._PROBLEM_STATE_PREFIXES) == set(SIX_PREFIXES), (
            "_PROBLEM_STATE_PREFIXES 与本档清点不一致：新增前缀要补清理断言，"
            "删除前缀要确认无状态泄漏"
        )
        assert len(language_page._PROBLEM_STATE_PREFIXES) == 6
        assert language_page._LRU_CAP == 30
        src = Path(language_page.__file__).read_text(encoding="utf-8")
        cap_line = next(ln for ln in src.splitlines() if ln.startswith("_LRU_CAP"))
        assert f"= {language_page._LRU_CAP} " in cap_line, (
            f"上限改了但 :46 行内注释没跟上：{cap_line}"
        )
        assert f"最近访问的 {language_page._LRU_CAP} 道题" in cap_line


class TestWindowBoundary:
    def test_cap_plus_one_evicts_exactly_one_oldest(self, fake):
        cap = language_page._LRU_CAP
        ids = [f"p{i}" for i in range(cap + 1)]                 # 31 道
        for pid in ids:
            _seed(fake, pid)
            language_page._touch_problem(pid)
        assert _survivors(fake, "p0") == []
        assert _survivors(fake, "p1") == list(SIX_PREFIXES), "31 道时第 2 旧不该出局"

    def test_queue_is_bounded_and_ordered_tail_is_current(self, fake):
        cap = language_page._LRU_CAP
        for i in range(cap + 5):
            language_page._touch_problem(f"q{i}")
        lru = fake.session_state["_problem_lru"]
        assert len(lru) == cap
        assert lru == [f"q{i}" for i in range(5, cap + 5)]
        assert len(set(lru)) == cap, "队列内不得出现重复题 id"


class TestEditorEpochKeyPrecision:
    """editor_<pid>_<epoch> 的 rsplit 切分：pid 可含下划线，必须按 pid 精确匹配。"""

    def test_similar_pid_not_collateral_damaged(self, fake):
        cap = language_page._LRU_CAP
        victim = "py_mid"
        neighbour = "py_mid_deep"
        filler = [f"f{i}" for i in range(cap)]                  # 先把 victim 挤出窗口
        for pid in [victim] + filler + [neighbour]:
            _seed(fake, pid)
            language_page._touch_problem(pid)
        language_page._touch_problem("tail")                    # 再推一格，victim 必出局

        victim_keys = [f"editor_{victim}_{e}" for e in (0, 1)]
        assert not [k for k in victim_keys if k in fake.session_state], (
            f"victim 的多 epoch 残键应全清，实际仍在：{victim_keys}"
        )
        # 本例的意义所在：startswith 无法区分 py_mid 与 py_mid_deep，
        # 只有 :72 的 rsplit("_", 1)[0] == pid 能做到精确匹配。
        ambiguous = [k for k in fake.session_state if k.startswith(f"editor_{victim}_")]
        assert ambiguous == [f"editor_{neighbour}_0", f"editor_{neighbour}_1"], (
            f"相似 pid 的 epoch 键被误删或集合意外：{ambiguous}"
        )
        for e in (0, 1):
            assert f"editor_{neighbour}_{e}" in fake.session_state
        assert _survivors(fake, neighbour) == list(SIX_PREFIXES)

    def test_epoch_bookkeeping_key_cleared_via_prefix_only(self, fake):
        """editor_epoch::<pid> 归前缀循环管；widget 清扫循环对它不得命中。"""
        cap = language_page._LRU_CAP
        ids = [f"e{i}" for i in range(cap + 2)]
        for pid in ids:
            _seed(fake, pid)
            language_page._touch_problem(pid)
        assert f"editor_epoch::{ids[0]}" not in fake.session_state
        assert f"editor_epoch::{ids[-1]}" in fake.session_state

    def test_undiscussed_editor_widget_keys_are_left_alone(self, fake):
        """无 epoch 后缀的 editor 键（body 里不含 `_` 一类）不属本机制，不得被扫走。"""
        cap = language_page._LRU_CAP
        ids = [f"u{i}" for i in range(cap + 2)]
        for pid in ids:
            _seed(fake, pid)
        fake.session_state["editor_theme"] = "light"            # 全局 UI 键，非题目态
        for pid in ids:
            language_page._touch_problem(pid)
        assert fake.session_state["editor_theme"] == "light", "清扫越界动了全局编辑器键"


class TestCurrentProblemNeverEvicted:
    """`if pid in keep_ids: continue`——重访已被挤出窗口的题，其状态必须活着。"""

    def test_revisit_of_out_of_window_problem_keeps_its_state(self, fake):
        cap = language_page._LRU_CAP
        first = "first"
        _seed(fake, first)
        language_page._touch_problem(first)
        for i in range(cap + 1):                                # 把 first 挤出窗口
            _seed(fake, f"x{i}")
            language_page._touch_problem(f"x{i}")
        assert _survivors(fake, first) == [], "前置条件：first 应已被逐出"

        language_page._touch_problem(first)                     # 重新访问它
        assert _survivors(fake, "x1") == [], "x1 仍应是最旧的那一个（被逐出）"
        lru = fake.session_state["_problem_lru"]
        assert lru[-1] == first, "重访的题必须回到队尾"
        assert lru.count(first) == 1, "队列里不该留旧的那一份"

    def test_repeat_visit_does_not_append_duplicate(self, fake):
        for pid in ("a", "a", "b", "b", "b"):
            language_page._touch_problem(pid)
        assert fake.session_state["_problem_lru"] == ["a", "b"]


class TestAiVariantExemption:
    """AI_VARIANT:: 走 :55 提前 return，不进 LRU、不触发任何清理。"""

    def test_variant_leaves_no_lru_trace(self, fake):
        _seed(fake, "AI_VARIANT::python/topic/p0")
        language_page._touch_problem("AI_VARIANT::python/topic/p0")
        assert "_problem_lru" not in fake.session_state, "变式题被记进了 LRU 队列"
        assert _survivors(fake, "AI_VARIANT::python/topic/p0") == list(SIX_PREFIXES)

    def test_crowd_of_variants_cannot_push_real_problems_out(self, fake):
        cap = language_page._LRU_CAP
        real = "python/topic/real"
        _seed(fake, real)
        language_page._touch_problem(real)
        for i in range(cap + 5):                                # 刷一堆变式题
            pid = f"AI_VARIANT::v{i}"
            _seed(fake, pid)
            language_page._touch_problem(pid)
        assert fake.session_state["_problem_lru"] == [real]
        assert _survivors(fake, real) == list(SIX_PREFIXES), "变式题把真题状态挤掉了"
        assert _survivors(fake, "AI_VARIANT::v0") == list(SIX_PREFIXES), (
            "变式题自身状态不得被 LRU 清理（生命周期短，交页面自己管）"
        )
