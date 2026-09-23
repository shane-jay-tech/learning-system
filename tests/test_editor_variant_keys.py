# -*- coding: utf-8 -*-
"""AI 变式题 editor 侧键的显式清键桩（l923-15）。

钉 `ui/pages/language.py::_clear_variant_editor_keys` 及其在「↩ 回到原题」分支的接线。

来龙去脉（l922-113 遗留 2 / l922-114 遗留 2 同族，本单按**出口二**结案）：
`_touch_problem` 对 `AI_VARIANT::` 前缀提前 return，变式题的
`editor_<vid>_<epoch>` 与 `editor_epoch::<vid>` 都不进 LRU 逐出队列 ——
在变式题上每点一次「↺ 重置」epoch+1，就多留一个 widget 残键，长会话刷变式
无界累积。l922-114 只把这写成「登记现状不修」（其
`test_variant_ids_get_own_key_and_are_not_lru_managed`），本单把它翻成行为：
「↩ 回到原题」＝变式题从 `ai_variants` 弹出＝其生命周期终点，那一刻清干净。

四个失效面本档各钉一条：
  A. 清不彻底 —— 只删 epoch 计数器、漏 `editor_<vid>_<旧 epoch>` 残键，
     或反过来只扫 widget 键漏掉计数器 ⇒ 计数仍 >0；
  B. 越界清理 —— 把还在 `ai_variants` 里的其它变式题、或**原题自身**的 editor
     状态一起清掉 ⇒ epoch 计数器归零 → 下次 `_editor_key` 退回 0 → widget key
     变化 → 组件重建 → 用户已写代码被 starter_code 覆盖。这比泄漏更重，
     所以「只清被退回的那一题」是硬要求，不是保守；
  C. 接线漂移 —— 清键调用没挂在「↩ 回到原题」分支里，或挂到了 `with right_col:`
     之后（那时变式题的 editor widget 已实例化，真 Streamlit 对已实例化
     widget 的 session_state 键再写入会当场抛异常）；
  D. 与 l922-113/114 在册桩的接缝 —— 变式题豁免 LRU 的语义**不得**因为本单
     被反过来改成「LRU 清扫顺手吃变式键」（那会在变式题还开着时清掉它的 epoch）。

可复跑：python -m pytest tests/test_editor_variant_keys.py -q
"""
from pathlib import Path

import pytest

import ui.pages.language as language_page
from tests.test_ui_behavior import FakeStreamlit

BASE = "python/01_basics/p1"                    # 原题 id（含下划线，兼测 rsplit 精确匹配）
VID = "AI_VARIANT::" + BASE                     # 变式题 id：core/ai_generate.py:105 的拼法
NEIGHBOUR_VID = VID + "_deep"                   # 相似前缀的另一道变式题
EPOCH_OF = "editor_epoch::"                     # 计数器键前缀

LANG_PY = Path(language_page.__file__)


def _accumulate(fake, vid, times):
    """在变式题上连点 N 次「↺ 重置」：每次落一个 editor widget 残键并把 epoch+1。

    等价于真会话里 `_editor_key(vid)` 被渲染 N 次（epoch 0..N-1 各留一键）。
    """
    for _ in range(times):
        fake.session_state[language_page._editor_key(vid)] = "user code"
        fake.session_state[EPOCH_OF + vid] = fake.session_state.get(EPOCH_OF + vid, 0) + 1


def _widget_keys(fake, vid):
    """① 的第一路计数：`editor_AI_VARIANT::*`（不含 epoch 计数器键）。"""
    return sorted(k for k in fake.session_state if k.startswith("editor_" + vid))


def _epoch_keys(fake, vid):
    """① 的第二路计数：`editor_epoch::AI_VARIANT::*`。"""
    return sorted(k for k in fake.session_state if k.startswith(EPOCH_OF + vid))


@pytest.fixture()
def fake(monkeypatch):
    f = FakeStreamlit()
    monkeypatch.setattr(language_page, "st", f)
    return f


class TestRetirementClearsVariantEditorKeys:
    """完成标准 ①：连刷 5 个变式后退回原题，两路计数归零。"""

    def test_five_variant_rounds_accumulate_keys_first(self, fake):
        """前置条件（不成立则 ① 的归零断言是空转）。"""
        _accumulate(fake, VID, 5)
        assert len(_widget_keys(fake, VID)) == 5, _widget_keys(fake, VID)
        assert _epoch_keys(fake, VID) == [EPOCH_OF + VID]
        assert fake.session_state[EPOCH_OF + VID] == 5

    def test_back_to_original_zeroes_both_key_families(self, fake):
        _accumulate(fake, VID, 5)
        language_page._clear_variant_editor_keys(VID)
        assert _widget_keys(fake, VID) == [], "退回原题后仍残留变式 editor widget 键"
        assert _epoch_keys(fake, VID) == [], "退回原题后仍残留变式 editor_epoch 计数器键"

    def test_clear_is_idempotent_and_tolerates_missing_counter(self, fake):
        """第二次点「回到原题」（或计数器本就未建）不得抛 KeyError。"""
        language_page._clear_variant_editor_keys(VID)
        assert EPOCH_OF + VID not in fake.session_state
        _accumulate(fake, VID, 2)
        language_page._clear_variant_editor_keys(VID)
        language_page._clear_variant_editor_keys(VID)
        assert _widget_keys(fake, VID) == []
        assert _epoch_keys(fake, VID) == []

    def test_regenerated_variant_starts_at_epoch_zero(self, fake):
        """清完再刷同一道变式（id 由原题决定，故必然同名）应从 0 起、无旧残键。"""
        _accumulate(fake, VID, 3)
        language_page._clear_variant_editor_keys(VID)
        assert language_page._editor_key(VID) == f"editor_{VID}_0"
        assert _widget_keys(fake, VID) == [], "只取 key 就留下残键，说明上一轮的没清干净"
        fake.session_state[language_page._editor_key(VID)] = "new code"
        assert _widget_keys(fake, VID) == [f"editor_{VID}_0"]


class TestNoCollateralDamage:
    """失效面 B：只清被退回的那一题。"""

    def test_other_variants_keep_their_keys_and_epoch_value(self, fake):
        """另一道仍开着的变式题：键全在、计数器数值不变（否则重渲染会退回 epoch 0）。"""
        other = "AI_VARIANT::python/01_basics/p2"
        _accumulate(fake, VID, 4)
        _accumulate(fake, other, 2)
        language_page._clear_variant_editor_keys(VID)

        assert _widget_keys(fake, VID) == []
        assert len(_widget_keys(fake, other)) == 2, "别的变式题被连坐了"
        assert fake.session_state[EPOCH_OF + other] == 2, "epoch 计数器被抹平＝重渲染时组件重建"
        assert language_page._editor_key(other) == f"editor_{other}_2", (
            "仍开着的变式题 epoch 回退了：用户已写代码会被 starter_code 覆盖"
        )

    def test_base_problem_editor_state_survives(self, fake):
        """原题（BASE）是 VID 的后缀子串 —— rsplit 精确匹配必须区分开。"""
        _accumulate(fake, VID, 3)
        fake.session_state[f"editor_{BASE}_0"] = "base code"
        fake.session_state[EPOCH_OF + BASE] = 7
        fake.session_state[f"code::{BASE}"] = "base code"
        language_page._clear_variant_editor_keys(VID)

        assert fake.session_state[f"editor_{BASE}_0"] == "base code"
        assert fake.session_state[EPOCH_OF + BASE] == 7
        assert fake.session_state[f"code::{BASE}"] == "base code"
        assert _widget_keys(fake, VID) == []

    def test_similar_variant_id_not_collateral_damaged(self, fake):
        """NEIGHBOUR_VID 以 VID 开头：只能按整段 pid 匹配，不得 startswith 误伤。"""
        _accumulate(fake, VID, 2)
        _accumulate(fake, NEIGHBOUR_VID, 2)
        language_page._clear_variant_editor_keys(VID)
        for e in (0, 1):
            assert f"editor_{VID}_{e}" not in fake.session_state, f"VID 自己的 epoch {e} 残键没清掉"
        assert len(_widget_keys(fake, NEIGHBOUR_VID)) == 2, (
            f"相似变式 id 的 epoch 键被误删：{[k for k in fake.session_state if k.startswith('editor_AI_')]}"
        )
        assert fake.session_state[EPOCH_OF + NEIGHBOUR_VID] == 2

    def test_non_variant_id_is_refused(self, fake):
        """防御侧：调用点若误传真题 id，一个键都不许动（清键只对 AI_VARIANT:: 生效）。"""
        fake.session_state[f"editor_{BASE}_1"] = "keep"
        fake.session_state[EPOCH_OF + BASE] = 1
        language_page._clear_variant_editor_keys(BASE)
        assert fake.session_state[f"editor_{BASE}_1"] == "keep"
        assert fake.session_state[EPOCH_OF + BASE] == 1


class TestBackButtonWiring:
    """失效面 C：清键必须挂在「↩ 回到原题」分支内，且在 right_col 建 widget 之前。"""

    def _back_block(self, src):
        start = src.index('if st.button("↩ 回到原题"')
        end = src.index("with right_col:")
        assert start < end, "回到原题分支已不在 left_col 区段内（右栏位置漂移）"
        return src[start:end]

    def test_clear_called_once_in_back_branch(self):
        src = LANG_PY.read_text(encoding="utf-8")
        block = self._back_block(src)
        assert block.count("_clear_variant_editor_keys(active_id)") == 1, (
            "「↩ 回到原题」分支里的清键调用不在/不唯一：变式键泄漏回归"
        )

    def test_clear_order_retire_then_clear_then_rerun(self):
        src = LANG_PY.read_text(encoding="utf-8")
        block = self._back_block(src)
        order = [
            "st.session_state.ai_variants.pop(base_problem.id, None)",
            "_clear_variant_editor_keys(active_id)",
            "st.session_state.pop(judge_result_key(active_id), None)",
            "st.rerun()",
        ]
        for frag in order:
            assert frag in block, f"回到原题分支缺 {frag}"
        idx = [block.index(f) for f in order]
        assert idx == sorted(idx), f"回到原题分支顺序被打乱（先弹出再清键）：{idx}"

    def test_clear_is_not_wired_into_reset_button(self):
        """「↺ 重置」不得清变式键：清掉 epoch 计数器等于把用户代码冲回 starter_code。"""
        src = LANG_PY.read_text(encoding="utf-8")
        reset_block = src[src.index('if st.button("↺ 重置"'):src.index("with ask_col:")]
        assert "_clear_variant_editor_keys" not in reset_block

    def test_helper_does_not_add_third_epoch_brace_literal(self):
        """l922-114 钉了 `editor_epoch::{` 字面量恰 2 处（:40 读 / :285 写）；
        本档的清键函数用字符串拼接，不得把那条在册桩弄红。"""
        src = LANG_PY.read_text(encoding="utf-8")
        sites = [ln.strip() for ln in src.splitlines() if "editor_epoch::{" in ln]
        assert len(sites) == 2, f"epoch 字面量站点漂移：{sites}"
        assert 'return f"editor_{active_id}_{epoch}"' in src, "widget key 形态变了：rsplit 匹配要同步改"


class TestLruExemptionStillHolds:
    """完成标准 ②：l922-113/114 在册的「变式题豁免 LRU」语义不回归。"""

    def test_touch_problem_still_skips_variants(self, fake):
        """进题本身不清键 —— 清理只发生在退回原题那一刻。"""
        _accumulate(fake, VID, 3)
        language_page._touch_problem(VID)
        assert "_problem_lru" not in fake.session_state, "变式题被记进了 LRU 队列"
        assert len(_widget_keys(fake, VID)) == 3, "变式题自身状态被 LRU 提前清了（它还开着）"
        assert fake.session_state[EPOCH_OF + VID] == 3

    def test_real_problem_sweep_leaves_open_variant_keys_alone(self, fake):
        """真题被逐出时不得顺手吃掉「同一原题的变式题」的键（VID 以 BASE 结尾）。"""
        _accumulate(fake, VID, 3)
        fake.session_state[f"code::{BASE}"] = "x"
        language_page._touch_problem(BASE)
        for i in range(language_page._LRU_CAP + 2):
            pid = f"python/01_basics/evict{i}"
            fake.session_state[f"code::{pid}"] = "x"
            fake.session_state[f"editor_{pid}_0"] = "x"
            language_page._touch_problem(pid)

        assert f"code::{BASE}" not in fake.session_state, "前置条件：原题应已被 LRU 逐出"
        assert len(_widget_keys(fake, VID)) == 3, "原题被逐出时变式题的 editor 键被连坐"
        assert fake.session_state[EPOCH_OF + VID] == 3

    def test_variant_prefix_table_untouched(self):
        """六前缀表是本档与 l922-113 的共享契约：本单只加清键函数，不改表。"""
        assert language_page._PROBLEM_STATE_PREFIXES == (
            "code::", "chat_ctx::", "chat_history::", "preask_hist::",
            "show_preask::", "editor_epoch::")
        assert language_page._LRU_CAP == 30
