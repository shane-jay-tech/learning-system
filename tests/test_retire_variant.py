# -*- coding: utf-8 -*-
"""变式题退回时的六前缀键清扫桩（l924-03）。

钉 `ui/pages/language.py::_retire_variant`，以及 `_clear_variant_editor_keys`
降级为薄壳后的**转调关系**。

来龙去脉：`_touch_problem` 对 `AI_VARIANT::` 提前 return（language.py:55），故
`_PROBLEM_STATE_PREFIXES` 六族键 + `editor_<vid>_<epoch>` widget 残键对变式题
一律不受 LRU 逐出管理。l923-15（出口二）在「↩ 回到原题」只清了前缀表里 editor
计数器那一族 + widget 残键，它自己的遗留 2 记下「另外 5 族前缀键仍无界」。
本单把那半边闭成 `_retire_variant(variant_id)`：六前缀 + widget 一次清净。

在册桩的接缝（本档为什么钉这些形状）：
  - `tests/test_editor_variant_keys.py` 的 `test_clear_called_once_in_back_branch`
    与 `test_clear_order_retire_then_clear_then_rerun` 按**源文本字面量**数
    `_clear_variant_editor_keys(active_id)` ⇒ 调用点名不可改，只能把实现下沉，
    所以 :291 处仍是旧名、旧名成为薄壳（本档第 2 组钉「薄壳确实清到六族」）。
  - `tests/test_language_editor_epoch.py` 的 `test_epoch_counter_sites_are_exactly_two`
    按行数「epoch 前缀紧跟左花括号」的字面量站点，**注释与 docstring 也算一行**
    （l923-15 实测被这条弄红过一次）⇒ 第 4 组自钉一遍，防后续改动造出第三处形态。

四个失效面各钉一条：
  A. 清不彻底 —— 漏掉六族里的任意一族（「只清 editor」是最现实的回归形态）；
  B. 越界清理 —— 变式题 id 互为前缀（`AI_VARIANT::p1` / `AI_VARIANT::p1_deep`），
     startswith 粗匹配会把仍开着的兄弟变式一起抹掉 ⇒ 用户代码被 starter_code
     覆盖，比泄漏更重；
  C. 接线漂移 —— 薄壳不再转调，或 `_retire_variant` 被误挂进「↺ 重置」/「✨ AI 变式题」
     分支（那两处清 epoch 计数器等于冲掉用户正在写的代码）；
  D. 实现漂移 —— 不遍历共享表 `_PROBLEM_STATE_PREFIXES` 而是自己硬列一族，
     表与清扫从此各长各的（真题侧改了、变式侧没跟）。

可复跑：python -m pytest tests/test_retire_variant.py -q
"""
import ast
import inspect
from pathlib import Path

import pytest

import ui.pages.language as language_page
from tests.test_ui_behavior import FakeStreamlit

BASE = "python/01_basics/p1"          # 原题 id（含下划线，兼测 rsplit 精确匹配）
VID = "AI_VARIANT::" + BASE           # core/ai_generate.py:105 的确定性拼法
NEIGHBOUR_VID = VID + "_deep"         # 以 VID 开头的兄弟变式：startswith 粗匹配会误伤
EPOCH_OF = "editor_epoch::"

SIX_PREFIXES = ("code::", "chat_ctx::", "chat_history::", "preask_hist::",
                "show_preask::", "editor_epoch::")
WIDGET_EPOCHS = 3                     # 每题摆 3 个 epoch 残键 ⇒ 全清后每题 6+3=9 键
FULL_COUNT = len(SIX_PREFIXES) + WIDGET_EPOCHS

LANG_PY = Path(language_page.__file__)


def _load_all_families(session, pid, widget_epochs=WIDGET_EPOCHS):
    """把 pid 的六族键 + N 个 epoch 的 widget 残键全摆满（不留空断言）。"""
    for prefix in SIX_PREFIXES:
        session[prefix + pid] = "state-" + prefix
    for e in range(widget_epochs):
        session[f"editor_{pid}_{e}"] = f"code-{e}"
    session[EPOCH_OF + pid] = widget_epochs


def _pid_keys(session, pid):
    """该 pid 名下**归本函数管辖**的键：六族精确键 + editor widget 残键。"""
    hits = {p + pid for p in SIX_PREFIXES}
    hits &= set(session)
    hits |= {k for k in session
             if k.startswith("editor_")
             and "_" in k[len("editor_"):]
             and k[len("editor_"):].rsplit("_", 1)[0] == pid}
    return hits


def _fn_src(fn):
    return inspect.getsource(fn)


@pytest.fixture()
def fake(monkeypatch):
    f = FakeStreamlit()
    monkeypatch.setattr(language_page, "st", f)
    return f


class TestRetirementClearsSixFamilies:
    """完成标准 ③：造 AI_VARIANT:: pid 的六前缀 + editor_ 键，调用后全空。"""

    def test_every_family_is_populated_first(self, fake):
        """前置条件：不成立则下面的归零断言全是空转。"""
        _load_all_families(fake.session_state, VID)
        assert sorted(_pid_keys(fake.session_state, VID)) == sorted(
            set(p + VID for p in SIX_PREFIXES) | {f"editor_{VID}_{e}" for e in range(WIDGET_EPOCHS)}
        ), "夹具没把六族 + widget 摆满，归零断言不可信"
        assert len(_pid_keys(fake.session_state, VID)) == FULL_COUNT

    @pytest.mark.parametrize("prefix", SIX_PREFIXES)
    def test_each_family_cleared_independently(self, fake, prefix):
        """逐族参数化：只漏一族也要被抓到（本单最现实的回归）。"""
        fake.session_state[prefix + VID] = "x"
        language_page._retire_variant(VID)
        assert prefix + VID not in fake.session_state, f"{prefix} 未被清：六族遍历漏项"

    def test_retire_variant_empties_all_six_prefixes_and_widgets(self, fake):
        _load_all_families(fake.session_state, VID)
        language_page._retire_variant(VID)
        leftovers = sorted(_pid_keys(fake.session_state, VID))
        assert leftovers == [], f"退回原题后仍残留变式题状态键：{leftovers}"

    def test_widget_sweep_clears_every_stale_epoch(self, fake):
        _load_all_families(fake.session_state, VID, widget_epochs=5)
        language_page._retire_variant(VID)
        assert [k for k in fake.session_state if k.startswith("editor_" + VID)] == []

    def test_retire_is_idempotent_and_tolerates_absent_keys(self, fake):
        """第二次退回（或某族从未建过）不得抛 KeyError。"""
        language_page._retire_variant(VID)
        _load_all_families(fake.session_state, VID, widget_epochs=1)
        language_page._retire_variant(VID)
        language_page._retire_variant(VID)
        assert _pid_keys(fake.session_state, VID) == set()

    def test_regenerated_variant_starts_clean(self, fake):
        """变式题 id 由原题决定 ⇒ 重刷必然同名；清完要从 epoch 0 起且无旧残键。"""
        _load_all_families(fake.session_state, VID, widget_epochs=4)
        language_page._retire_variant(VID)
        assert language_page._editor_key(VID) == f"editor_{VID}_0"
        assert [k for k in fake.session_state if k.startswith("editor_" + VID)] == [], (
            "只取 key 就留下残键，说明上一轮的没清干净"
        )
        fake.session_state[language_page._editor_key(VID)] = "new code"
        assert [k for k in fake.session_state if k.startswith("editor_" + VID)] == [
            f"editor_{VID}_0"]


class TestShimStillOwnsTheCallSite:
    """失效面 C：调用点名被在册桩钉死 ⇒ 旧名只能做薄壳，而壳必须真转调。"""

    def test_shim_clears_all_six_families_too(self, fake):
        """生产路径实际走的是 `_clear_variant_editor_keys`。它若仍停留在
        l923-15 的「只清 editor 两族」实现，本条就会红（六族里四族还在）。"""
        _load_all_families(fake.session_state, VID)
        language_page._clear_variant_editor_keys(VID)
        assert _pid_keys(fake.session_state, VID) == set(), (
            "薄壳没有转调 _retire_variant，或 _retire_variant 清键面窄于六族"
        )

    def test_retire_defined_once_and_called_once(self):
        src = LANG_PY.read_text(encoding="utf-8")
        assert src.count("def _retire_variant(") == 1, "定义处应唯一"
        assert src.count("_retire_variant(") == 2, (
            "`_retire_variant(` 应恰 2 处 = 定义 + 薄壳内 1 次转调；"
            "多出来的位置说明它被挂进了别的分支（重置/生成变式都不该清键）"
        )

    def test_shim_body_is_a_single_delegation(self):
        """壳里不得长出新逻辑：只允许一条 `_retire_variant(variant_id)`。"""
        tree = ast.parse(LANG_PY.read_text(encoding="utf-8"))
        fn = next(n for n in tree.body
                  if isinstance(n, ast.FunctionDef) and n.name == "_clear_variant_editor_keys")
        body = [s for s in fn.body
                if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)
                        and isinstance(s.value.value, str))]
        assert len(body) == 1, f"薄壳语句数应为 1（纯转调）：{ast.dump(fn.body[0]) if body else '空'}"
        call = body[0]
        assert isinstance(call, ast.Expr) and isinstance(call.value, ast.Call)
        assert call.value.func.id == "_retire_variant"
        assert [a.id for a in call.value.args] == ["variant_id"], "转调串错了参数"

    def test_back_button_branch_still_calls_the_shim(self):
        src = LANG_PY.read_text(encoding="utf-8")
        block = src[src.index('if st.button("↩ 回到原题"'):src.index("with right_col:")]
        assert block.count("_clear_variant_editor_keys(active_id)") == 1
        assert "_retire_variant(" not in block, (
            "回到原题分支应只经薄壳入口；直调新名会让 test_editor_variant_keys 的在册桩红"
        )

    def test_not_wired_into_reset_or_generate_branches(self):
        src = LANG_PY.read_text(encoding="utf-8")
        reset_block = src[src.index('if st.button("↺ 重置"'):src.index("with ask_col:")]
        gen_block = src[src.index('if st.button("✨ AI 变式题"'):src.index("with back_col:")]
        assert "_clear_variant_editor_keys" not in reset_block
        assert "_retire_variant" not in reset_block
        assert "_retire_variant" not in gen_block, (
            "生成新变式时清键会把上一道变式的用户代码连同状态一起抹掉（超授权）"
        )


class TestNoCollateralDamage:
    """失效面 B：只清被退回的那一题 —— 精确拼键，不是 startswith。"""

    def test_neighbour_variant_keeps_all_six_families(self, fake):
        """NEIGHBOUR_VID 以 VID 开头：startswith 版实现会连坐它。"""
        _load_all_families(fake.session_state, VID)
        _load_all_families(fake.session_state, NEIGHBOUR_VID)
        language_page._retire_variant(VID)

        assert _pid_keys(fake.session_state, VID) == set()
        kept = sorted(_pid_keys(fake.session_state, NEIGHBOUR_VID))
        assert len(kept) == FULL_COUNT, f"兄弟变式题被误伤，现存：{kept}"
        assert fake.session_state[EPOCH_OF + NEIGHBOUR_VID] == WIDGET_EPOCHS, (
            "兄弟变式 epoch 被抹平＝重渲染时组件重建、用户代码被覆盖")

    def test_base_problem_state_survives(self, fake):
        """BASE 是 VID 的子串、VID 以 BASE 结尾 —— 两个方向都不能连坐。"""
        _load_all_families(fake.session_state, VID)
        _load_all_families(fake.session_state, BASE)
        language_page._retire_variant(VID)
        assert len(_pid_keys(fake.session_state, BASE)) == FULL_COUNT, "原题状态被变式清键连坐"
        assert fake.session_state["code::" + BASE] == "state-code::"

    def test_non_variant_id_is_refused(self, fake):
        """调用点误传真题 id：一个键都不许动。"""
        _load_all_families(fake.session_state, BASE)
        fake.session_state["last_judge_pid"] = BASE
        before = sorted(fake.session_state)
        language_page._retire_variant(BASE)
        language_page._retire_variant("python/01_basics/p1_deep")
        assert sorted(fake.session_state) == before, "被拒绝的入参仍然动了 session_state"

    def test_other_variants_epoch_counters_untouched(self, fake):
        """仍开着的第三道变式：widget 残键与计数器逐位不变。"""
        other = "AI_VARIANT::python/01_basics/p2"
        _load_all_families(fake.session_state, VID)
        _load_all_families(fake.session_state, other)
        language_page._retire_variant(VID)
        assert len(_pid_keys(fake.session_state, other)) == FULL_COUNT
        assert language_page._editor_key(other) == f"editor_{other}_{WIDGET_EPOCHS}"


class TestRedLineOnEpochBraceLiteral:
    """l922-114 的字面量站点保险丝：本单新增代码不得造出第三种形态。"""

    def test_brace_literal_sites_stay_exactly_two(self):
        src = LANG_PY.read_text(encoding="utf-8")
        sites = [ln.strip() for ln in src.splitlines() if "editor_epoch::{" in ln]
        assert len(sites) == 2, f"epoch 花括号字面量站点漂移（在册桩钉 2 处）：{sites}"

    def test_retire_variant_never_repeats_the_epoch_prefix_literal(self):
        """本函数必须靠遍历共享前缀表覆盖那一族，而不是自己再拼一次键名。"""
        src = _fn_src(language_page._retire_variant)
        assert EPOCH_OF not in src, (
            "_retire_variant 内出现 epoch 计数器前缀字面量＝与在册桩抢站点；改走共享表"
        )


class TestSharedTableContract:
    """失效面 D：变式侧与真题侧共用同一张前缀表与同一 rsplit 判据。"""

    def test_prefix_table_is_the_single_source_of_truth(self):
        assert language_page._PROBLEM_STATE_PREFIXES == SIX_PREFIXES
        assert len(language_page._PROBLEM_STATE_PREFIXES) == 6
        assert language_page._LRU_CAP == 30

    def test_retire_iterates_the_shared_table(self):
        src = _fn_src(language_page._retire_variant)
        assert "_PROBLEM_STATE_PREFIXES" in src, (
            "变式侧硬编码前缀＝表改了它不跟，六族清扫会静默退化成子集"
        )
        assert 'rsplit("_", 1)' in src, "widget 残键判据与 _touch_problem 不同源"

    def test_lru_sweep_covers_the_same_key_shapes(self, fake):
        """同一批键：真题被 LRU 逐出 与 变式被退回 清的是同一形状。"""
        _load_all_families(fake.session_state, VID)
        _load_all_families(fake.session_state, BASE)
        language_page._touch_problem(BASE)
        for i in range(language_page._LRU_CAP + 2):
            pid = f"python/01_basics/evict{i}"
            fake.session_state["code::" + pid] = "x"
            language_page._touch_problem(pid)

        assert "code::" + BASE not in fake.session_state, "前置条件：原题应已被 LRU 逐出"
        assert len(_pid_keys(fake.session_state, VID)) == FULL_COUNT, (
            "原题被逐出时变式题的六族键被连坐（它还开着）—— 豁免语义回归")

    def test_touch_problem_still_skips_variants(self, fake):
        """进题本身不清键：清理只发生在退回那一刻。"""
        _load_all_families(fake.session_state, VID)
        language_page._touch_problem(VID)
        assert "_problem_lru" not in fake.session_state
        assert len(_pid_keys(fake.session_state, VID)) == FULL_COUNT


class TestKnownBlindSpotPinned:
    """把 l922-113 遗留 2 的形态盲区钉成**可见的现状**，而不是悄悄扩权。

    缺 epoch 后缀的 `editor_<pid>`（去掉前缀后末段无 `_`）在 rsplit 判据下清不掉，
    因为它无法与全局 UI 键（如 `editor_theme`）区分开 —— 那是 key 规范问题，
    属 l924-04 设计稿范围。本档只钉「本单没有扩权去清它」。
    """

    def test_suffixless_editor_key_still_survives(self, fake):
        fake.session_state["editor_" + VID] = "legacy shape"
        language_page._retire_variant(VID)
        assert "editor_" + VID in fake.session_state, (
            "清掉了无 epoch 后缀的 editor_ 键＝需要先落 key 规范（l924-04），本单不扩权"
        )
