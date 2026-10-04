# -*- coding: utf-8 -*-
"""变式题退回时的六前缀键清扫桩（l924-03）。

钉 `ui/pages/language.py::_retire_variant`，以及 `_retire_variant_state_keys`
降级为薄壳后的**转调关系**。

来龙去脉：`_touch_problem` 对 `AI_VARIANT::` 提前 return（language.py:55），故
`_PROBLEM_STATE_PREFIXES` 六族键 + `editor_<vid>_<epoch>` widget 残键对变式题
一律不受 LRU 逐出管理。l923-15（出口二）在「↩ 回到原题」只清了前缀表里 editor
计数器那一族 + widget 残键，它自己的遗留 2 记下「另外 5 族前缀键仍无界」。
本单把那半边闭成 `_retire_variant(variant_id)`：六前缀 + widget 一次清净。

在册桩的接缝（本档为什么钉这些形状）：
  - `tests/test_editor_variant_keys.py` 的 `test_clear_called_once_in_back_branch`
    与 `test_clear_order_retire_then_clear_then_rerun` 按**源文本字面量**数
    `_retire_variant_state_keys(active_id)` ⇒ 调用点名不可改，只能把实现下沉，
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

追加（l927-40，2026-09-28）：**生产码补了第二终点**——变式题有了自己的有界队列
`_variant_lru`（档内三处上游点名的「出口一：独立有界队列」），刷了变式**从不点「↩ 回到原题」**
直接换题／离开时，超出 `_LRU_CAP` 的最旧变式按 `_retire_variant` 清六族＋widget 残键。
于是本文件翻 1 条在册断言（`test_retire_defined_once_and_called_once`：字面量计数 → AST 点名调用者）、
订正 1 条 docstring、新增 `TestVariantSecondEndState` 7 例（含 1 例判据点名的离开路径用例
＋ 1 例代价面钉子），逐字留痕见文件末尾「🔴 l927-40 改桩记录」。
连带必要改动在 `tests/test_language_lru_eviction.py`（那条「变式自身状态不得被清理」的现状桩
按新语义翻面，同批留痕）。真题侧 `_touch_problem` 的行为与 cap **一字未动**。
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
        """生产路径实际走的是 `_retire_variant_state_keys`。它若仍停留在
        l923-15 的「只清 editor 两族」实现，本条就会红（六族里四族还在）。"""
        _load_all_families(fake.session_state, VID)
        language_page._retire_variant_state_keys(VID)
        assert _pid_keys(fake.session_state, VID) == set(), (
            "薄壳没有转调 _retire_variant，或 _retire_variant 清键面窄于六族"
        )

    def test_retire_defined_once_and_called_once(self):
        """🔴 l927-40 改桩（本单唯一一处动在册断言方向，逐字留痕见文件末尾改桩记录）。

        旧版第二行是 `assert src.count("_retire_variant(") == 2`＝「定义＋薄壳转调」的
        字面量计数代理，注释写"多出来的位置说明它被挂进了别的分支"。第二终点
        （`_touch_variant` 的队列逐出）正是**第三条正当站点**，"多一处就红"这个代理当场过期；
        但把它改回 `== 3` 只是把巧合写成规矩 ⇒ 换成按 AST 点名单：**谁在调**才是判据。
        原意（不得挂进「↺ 重置」/「✨ AI 变式题」分支）由同节的
        `test_not_wired_into_reset_or_generate_branches` 独立钉着，本例不放松，
        反而多钉「每个调用点各只调一次」。
        """
        src = LANG_PY.read_text(encoding="utf-8")
        assert src.count("def _retire_variant(") == 1, "定义处应唯一"
        tree = ast.parse(src)
        callers = [fn.name for fn in tree.body if isinstance(fn, ast.FunctionDef)
                   for sub in ast.walk(fn)
                   if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
                   and sub.func.id == "_retire_variant"]
        assert sorted(callers) == ["_retire_variant_state_keys", "_touch_variant"], (
            f"`_retire_variant` 的调用点漂移（现值 {sorted(callers)}）：只允许薄壳转调 ＋ "
            "l927-40 的变式队列逐出两处；出现在别处＝它被挂进了不该清键的分支")

    def test_shim_body_is_a_single_delegation(self):
        """壳里不得长出新逻辑：只允许一条 `_retire_variant(variant_id)`。"""
        tree = ast.parse(LANG_PY.read_text(encoding="utf-8"))
        fn = next(n for n in tree.body
                  if isinstance(n, ast.FunctionDef) and n.name == "_retire_variant_state_keys")
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
        assert block.count("_retire_variant_state_keys(active_id)") == 1
        assert "_retire_variant(" not in block, (
            "回到原题分支应只经薄壳入口；直调新名会让 test_editor_variant_keys 的在册桩红"
        )

    def test_not_wired_into_reset_or_generate_branches(self):
        src = LANG_PY.read_text(encoding="utf-8")
        reset_block = src[src.index('if st.button("↺ 重置"'):src.index("with ask_col:")]
        gen_block = src[src.index('if st.button("✨ AI 变式题"'):src.index("with back_col:")]
        assert "_retire_variant_state_keys" not in reset_block
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
        """进题本身不清键：清理只发生在退回那一刻、或队列溢出逐出那一刻（l927-40 补的后半句）。

        🔴 l927-40 口径订正：本例旧 docstring 写的是「清理只发生在退回那一刻」——第二终点
        （`_variant_lru` 溢出逐出）落地后那半句不再完整，但**断言面一字未动且仍绿**：
        它要钉的「进题这一帧不清自己、也不进真题侧 `_problem_lru`」两条都还成立。
        """
        _load_all_families(fake.session_state, VID)
        language_page._touch_problem(VID)
        assert "_problem_lru" not in fake.session_state
        assert len(_pid_keys(fake.session_state, VID)) == FULL_COUNT


class TestVariantSecondEndState:
    """l927-40 变式题的**第二生命周期终点**：独立有界队列 `_variant_lru`（档内「出口一」）。

    终点一＝`_retire_variant`（「↩ 回到原题」当场清，l924-03）；终点二＝本组：刷了变式
    **直接换题／离开**（从不点退回）时，六族键原先整场会话无界
    （l923-15 遗留 3／l924-03 遗留 1／learn-editor-key-spec-20260924.md 遗留 C-6）。
    现在按 `_LRU_CAP` 封顶逐出，逐出走的就是 `_retire_variant` ⇒ 清键面与终点一逐字同形。

    五个失效面各钉一条：
      A. 溢出没清（第二终点空转，泄漏面照旧）；
      B. 进题当帧清自己（用户正在写的代码被 starter_code 覆盖）；
      C. 队列被同一个 id 反复 rerun 堆满 ⇒ "有界"退化成"按 rerun 次数逐出"；
      D. 逐出用了 startswith ⇒ 以被逐 id 开头的兄弟变式被连坐；
      E. 逐出时顺手弹 `ai_variants`／动了真题队列 ⇒ 可见行为变更／真题侧逐出时点漂移。
    """

    def test_leaving_variants_without_back_button_evicts_only_beyond_cap(self, fake):
        """判据②「离开路径用例」：刷 cap+2 道变式、一道都不点退回 ⇒ 只有最旧 2 道被清。"""
        cap = language_page._LRU_CAP
        vids = [f"AI_VARIANT::python/01_basics/v{i}" for i in range(cap + 2)]
        for vid in vids:                       # 每刷一道就换题离开：从不点「↩ 回到原题」
            _load_all_families(fake.session_state, vid)
            language_page._touch_problem(vid)

        for vid in vids[:2]:
            assert _pid_keys(fake.session_state, vid) == set(), \
                f"{vid} 早被挤出 cap 窗口却仍留状态键（第二终点空转）"
        for vid in vids[2:]:
            assert len(_pid_keys(fake.session_state, vid)) == FULL_COUNT, \
                f"{vid} 还在窗口内就被清了（逐出时点错到本帧之前）"
        assert len(fake.session_state["_variant_lru"]) == cap, "队列本身必须封顶，不能自己无界"

    def test_entering_a_variant_never_clears_its_own_state(self, fake):
        """失效面 B：当前这道变式永不被本终点清（`keep_ids` 含队尾那一格）。"""
        _load_all_families(fake.session_state, VID)
        for _ in range(3):                     # 同一帧反复进题（Streamlit 每次交互都重跑渲染体）
            language_page._touch_problem(VID)
        assert len(_pid_keys(fake.session_state, VID)) == FULL_COUNT, \
            "进题当帧清了自己的键＝用户代码会被 starter_code 覆盖，比泄漏更重"

    def test_repeated_reruns_of_one_variant_do_not_flood_the_queue(self, fake):
        """失效面 C：先摘再挂 ⇒ 同一 id 只占一格（旧 `_problem_lru` 那套"只看队尾"会堆重复项）。"""
        cap = language_page._LRU_CAP
        _load_all_families(fake.session_state, VID)
        for _ in range(cap + 5):               # 一帧一帧地摸同一道题
            language_page._touch_problem(VID)
        assert fake.session_state["_variant_lru"] == [VID], \
            f"队列被同一个 id 堆满：{fake.session_state['_variant_lru']}"
        assert len(_pid_keys(fake.session_state, VID)) == FULL_COUNT, "去重失败连带把自己逐出"

    def test_back_and_forth_navigation_keeps_one_slot_per_variant(self, fake):
        """来回切题（A↔B 各 cap 次）只占 2 格 ⇒ 逐出时点由**不同变式条数**决定，不由交互数决定。"""
        cap = language_page._LRU_CAP
        a, b = VID, "AI_VARIANT::python/01_basics/p2"
        for _ in range(cap):
            language_page._touch_problem(a)
            language_page._touch_problem(b)
        assert fake.session_state["_variant_lru"] == [a, b], \
            f"来回切题该只占两格，现值 {fake.session_state['_variant_lru']}"

    def test_eviction_is_exact_and_spares_neighbour_and_base(self, fake):
        """失效面 D：队列路径同样按 `prefix + vid` **精确拼键**，兄弟变式与原题零连坐。"""
        cap = language_page._LRU_CAP
        _load_all_families(fake.session_state, VID)
        _load_all_families(fake.session_state, NEIGHBOUR_VID)
        _load_all_families(fake.session_state, BASE)

        language_page._touch_problem(VID)                     # 最旧的一格
        for i in range(cap - 1):                              # 填满窗口（不触发逐出）
            language_page._touch_problem(f"AI_VARIANT::python/01_basics/filler{i}")
        language_page._touch_problem(NEIGHBOUR_VID)            # 最后一进 ⇒ 被挤出的是 VID

        assert _pid_keys(fake.session_state, VID) == set(), "队列逐出没走到 _retire_variant"
        assert len(_pid_keys(fake.session_state, NEIGHBOUR_VID)) == FULL_COUNT, (
            "startswith 粗匹配连坐了以 VID 开头的兄弟变式（它的 epoch 被抹平＝组件重建、代码被覆盖）")
        assert len(_pid_keys(fake.session_state, BASE)) == FULL_COUNT, "原题被变式队列连坐"

    def test_second_end_state_does_not_disturb_the_real_problem_lru(self, fake):
        """失效面 E（两队列独立）：一堆变式不得把真题挤出 `_problem_lru`，也不得混进那张表。"""
        cap = language_page._LRU_CAP
        real = "python/01_basics/p1"
        _load_all_families(fake.session_state, real)
        language_page._touch_problem(real)
        for i in range(cap + 5):
            language_page._touch_problem(f"AI_VARIANT::python/01_basics/v{i}")
        assert fake.session_state["_problem_lru"] == [real], \
            f"变式队列污染了真题队列：{fake.session_state['_problem_lru']}"
        assert len(_pid_keys(fake.session_state, real)) == FULL_COUNT, "变式把真题状态挤掉了"

    def test_evicted_variant_is_left_in_ai_variants_on_purpose(self, fake):
        """登记的**代价面**（不是"应该"，是"本单刻意不扩权"的钉子）：
        队列只清键、不弹 `ai_variants` ⇒ 被逐出后重访那道题，题面仍是变式、题态回初值。
        改成连 `ai_variants` 一起弹＝可见行为变更，交主班裁
        （docs/insights/l927-40-lifecycle2.md §三 代价 1）。
        """
        cap = language_page._LRU_CAP
        fake.session_state["ai_variants"] = {BASE: {"id": VID, "title": "变式题"}}
        _load_all_families(fake.session_state, VID)
        language_page._touch_problem(VID)                     # 最旧的一格
        for i in range(cap):                                  # 填满窗口 ⇒ VID 在溢出那一帧被挤出
            language_page._touch_problem(f"AI_VARIANT::python/01_basics/e{i}")

        assert _pid_keys(fake.session_state, VID) == set(), "前置条件：VID 应已被逐出"
        assert fake.session_state["ai_variants"] == {BASE: {"id": VID, "title": "变式题"}}, (
            "`ai_variants` 被顺手弹掉了——那是可见行为变更（重访会直接回到原题），超本单授权")
        assert language_page._active_problem(
            type("P", (), {"id": BASE, "to_dict": lambda self: {"id": BASE}})())[1] is True, (
            "逐出后重访该题仍应拿到变式题（`ai_variants` 未弹）⇒ 题面是变式、题态是初值，"
            "这正是本形态登记的代价")
        assert language_page._editor_key(VID) == f"editor_{VID}_0", (
            "epoch 计数器被清 ⇒ 重访时 widget key 归 0、组件重建（本形态的已知代价）")


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


# ---------------------------------------------------------------------------
# 🔴 l927-40 改桩记录（2026-09-28）——第二终点（变式独立有界队列）落地，逐字留痕
#
# 裁决来源：`zcode-bridge/inbox/l927-40.task.md`「做什么」＝"补第二终态（离开/换题时清理
# 六族键——按档内设计的第二终点形态），补 1 例离开路径用例"。三处上游都点名同一个修法：
#   - `done/l923-15.result.md` 遗留 3：「用户刷了变式但从不点退回（换专题/换题直接离开）时，
#     该变式题的键不会被本单清掉——这正是卷宗『出口一（独立有界队列）』要解决的问题」
#   - `done/l924-03.result.md` 遗留 1：「要闭它需要第二个终点（出口一『独立有界队列』）」
#   - `docs/insights/learn-editor-key-spec-20260924.md` 遗留 C-6：同一句
# ⇒ 本单落的就是那个「出口一」，形态照本文件早已存在的真题侧 `_touch_problem`（同 cap、
#   同 `_retire_variant` 清键面、同精确拼键），队列另开一把 `_variant_lru`。
#
# 动了哪些在册断言（**只有两处**，其余全是新增）：
#   1. 本文件 `TestShimStillOwnsTheCallSite::test_retire_defined_once_and_called_once`
#      变：`src.count("_retire_variant(") == 2`（字面量计数）→ AST 点名调用者
#        `== ["_retire_variant_state_keys", "_touch_variant"]`。
#      为什么不是放宽：旧判据是"多一处就红"的代理，第二终点恰好就是正当的第三处，
#        代理必然过期；写回 `== 3` 只是把巧合当规矩。AST 版把判据换成**谁在调**，
#        比原来严（挂进任何别的函数体都红），且"不得挂进重置/生成变式分支"那半原意
#        由同节 `test_not_wired_into_reset_or_generate_branches` **一字未动**地继续钉着。
#      判别力：M2 变异（队列里不调 `_retire_variant`）⇒ 本例与另外 4 例同时红。
#   2. 本文件 `TestSharedTableContract::test_touch_problem_still_skips_variants`
#      只改 docstring（旧半句"清理只发生在退回那一刻"已被第二终点否证，补上"或队列溢出逐出"），
#      **断言面一字未动且仍绿**——它钉的"进题当帧不清自己／不进真题 `_problem_lru`"两条都还成立。
#   3. `tests/test_language_lru_eviction.py::TestAiVariantExemption`（连带必要改动）
#      变：`test_crowd_of_variants_cannot_push_real_problems_out` 末段由
#        「`AI_VARIANT::v0` 六族键必须全在（生命周期短，交页面自己管）」
#        → 「`v0` 六族键必须**全空**（第二终点生效）」＋ 新增一格「窗口内最后一道
#          `v{cap+4}` 仍须全在」防"改成一律清光"也绿。
#        类 docstring 的「不触发任何清理」同步订正。
#      没丢：同例前两行（`_problem_lru == [real]`、真题六族不被连坐）逐字照旧；
#        同组 `test_variant_leaves_no_lru_trace` **一字未动**仍绿。
#      ⚠ 这条 2026-09-22 的在册断言正是 l923-15/l924-03 说的"钉现状"那一格，
#        翻面是派单授权的行为变更，不是凑绿。
#
# 新增（本单判据②）：`TestVariantSecondEndState` 7 例——离开路径（cap+2 只逐出最旧 2 道）、
# 进题不清自己、反复 rerun 不堆队列、来回切题只占两格、逐出精确不连坐兄弟变式与原题、
# 不污染真题队列、以及**代价面钉子**（逐出后 `ai_variants` 仍挂着、重访题面是变式而题态回初值）。
# 五组变异读数见 docs/insights/l927-40-lifecycle2.md §四；未删一例、未 xfail、未放宽任何断言。
# ---------------------------------------------------------------------------
