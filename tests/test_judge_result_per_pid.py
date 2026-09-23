# -*- coding: utf-8 -*-
"""最近评判结果的 per-pid 命名空间桩（l923-16）。

钉 `ui/components.py::judge_result_key` / `drop_shown_judge_result` 与
`ui/pages/language.py` 读写两侧的同步。

改的是什么：`last_judge_result` 以前是一个**裸全局键**（容量 1），language 页六个
清理点（切专题／切题目／跨页 selection 导航／生成变式／回到原题／↺ 重置）pop 的都是
同一格，于是 A 题的任何动作会把 B 题刚拿到的结果一起抹掉（l922-114 遗留问题 1 原话：
「A 题点重置会连带抹掉 B 题的最近评判结果缓存」）。现在每道题各占一格
`last_judge_result::<pid>`，pop 只作用于自己那一格。

两侧定位规则（本档反复用到）：
  · 拿得到 active_id 的站点（生成变式／回到原题／重置）→ `pop(judge_result_key(active_id), None)`
  · 拿不到的切换站点（切专题／切题目／selection／navigate_to_problem）→ `drop_shown_judge_result()`，
    它按 `last_judge_pid`（每次判题与结果一起写）指认「正要离开的那道题」
  · `last_judge_pid` **本身仍是全局键**且刻意保留：它是「屏幕上现在展示的是谁的结论」这一
    全局 UI 事实的唯一载体，也是切换点唯一能拿到的定位凭据。

三个失效面本档各钉一条：
  A. 字面量跨模块漂移 —— 键名在 ui/components 与 ui/pages/language 两处各写一份，
     任何一边改名都会「写在一格、读在另一格」⇒ 判题结果区永久不出现，而全量测试全绿；
  B. 清理越界 —— 切换点若退化成「扫掉全部 last_judge_result::*」，per-pid 就白改了；
  C. 展示门被顺手放宽 —— 读侧的 `last_judge_pid == active_id` 这一条若被删，
     回访上一题会把它很久以前的结论当成刚判的（判题展示面，红线相邻，不得放宽）。

可复跑：python -m pytest tests/test_judge_result_per_pid.py -q
"""
import re
from pathlib import Path

import pytest

import ui.components as components
import ui.pages.language as language_page
from tests.test_ui_behavior import FakeStreamlit

PID_A = "python/01_basics/p1"
PID_B = "python/01_basics/p2"
VAR = "AI_VARIANT::python/01_basics/p1"

REPO_ROOT = Path(__file__).resolve().parents[1]
PROD_SRC = sorted(list((REPO_ROOT / "ui").rglob("*.py")) + list((REPO_ROOT / "core").rglob("*.py")))
# 带命名空间的形：last_judge_result::<…>
_NAMESPACED = re.compile(r"last_judge_result::")
# 裸全局键字面量：引号里正好是 last_judge_result（后面不跟 ::）
_BARE = re.compile(r"""(["'])last_judge_result\1(?!:)""")


@pytest.fixture()
def fake(monkeypatch):
    f = FakeStreamlit()
    monkeypatch.setattr(components, "st", f)
    monkeypatch.setattr(language_page, "st", f)
    return f


class TestKeyShape:
    def test_key_is_prefix_plus_pid(self):
        assert components.judge_result_key(PID_A) == "last_judge_result::" + PID_A
        assert components.JUDGE_RESULT_PREFIX == "last_judge_result::"

    def test_two_problems_get_two_distinct_slots(self):
        """数据模型层的正面判据：容量不再是 1。"""
        assert components.judge_result_key(PID_A) != components.judge_result_key(PID_B)
        assert components.judge_result_key(PID_A) != components.judge_result_key(VAR)

    def test_slot_names_cannot_swallow_each_other(self):
        """扫尾清扫类改法（startswith 前缀）会牵连别人：键形要保证可精确回指。"""
        fake_keys = {components.judge_result_key(p) for p in (PID_A, PID_B, VAR)}
        assert len(fake_keys) == 3
        assert all(k.startswith(components.JUDGE_RESULT_PREFIX) for k in fake_keys)


class TestNoBareGlobalKeyLeft:
    """完成标准 ①：全仓生产码裸全局键读写清零（磁盘实取，不写死文件名清单）。"""

    def test_production_sources_have_no_bare_key(self):
        offenders = []
        for src in PROD_SRC:
            for n, line in enumerate(src.read_text(encoding="utf-8").splitlines(), 1):
                if _BARE.search(line):
                    offenders.append(f"{src.relative_to(REPO_ROOT).as_posix()}:{n}: {line.strip()}")
        assert offenders == [], (
            "生产码里又出现了裸全局键 `\"last_judge_result\"` 读写点，per-pid 命名空间被破：\n"
            + "\n".join(offenders)
        )

    def test_prefix_defined_exactly_once_repo_wide(self):
        """失效面 A：字面量只能有一处定义，其余全走 judge_result_key()。"""
        hits = []
        for src in PROD_SRC:
            text = src.read_text(encoding="utf-8")
            for n, line in enumerate(text.splitlines(), 1):
                if _NAMESPACED.search(line) and "=" in line and '"' in line:
                    hits.append(f"{src.relative_to(REPO_ROOT).as_posix()}:{n}: {line.strip()}")
        assert len(hits) == 1, f"键前缀定义应恰 1 处（ui/components.py），实得 {hits}"

    def test_language_page_reads_and_writes_only_via_helper(self):
        src = Path(language_page.__file__).read_text(encoding="utf-8")
        # 6 处 = 1 写（:335）+ 2 读（:348 判空 / :351 取值）+ 3 清（:279/:292/:318）
        assert src.count("judge_result_key(active_id)") == 6, (
            "language.py 里按 active_id 取键的站点数变了：读写必须同源于 "
            "ui.components.judge_result_key，任何一处自己拼字面量都会「写在一格、读在另一格」"
        )
        assert 'st.session_state.get("last_judge_pid") == active_id' in src, (
            "失效面 C：展示门被放宽——回访上一题会把旧结论当刚判的显示"
        )


class TestCoexistThenResetOnlyKillsOwnSlot:
    """完成标准 ②：置 A/B 两题结果 → 重置 A → B 结果仍在。"""

    def test_two_results_coexist_and_reset_a_leaves_b(self, fake):
        fake.session_state[components.judge_result_key(PID_A)] = "resultA"
        fake.session_state[components.judge_result_key(PID_B)] = "resultB"
        fake.session_state["last_judge_pid"] = PID_A

        # 「↺ 重置」分支的实际动作（与 language.py 重置站点同一表达式）
        fake.session_state.pop(components.judge_result_key(PID_A), None)

        assert components.judge_result_key(PID_A) not in fake.session_state
        assert fake.session_state[components.judge_result_key(PID_B)] == "resultB", (
            "A 题的重置又连带抹掉 B 题的结果：连坐回归"
        )

    def test_variant_and_base_have_separate_slots(self, fake):
        """生成变式题清的是当前展示题那一格，原题很久以前的结果不受连坐。"""
        fake.session_state[components.judge_result_key(PID_A)] = "baseResult"
        fake.session_state[components.judge_result_key(VAR)] = "variantResult"
        fake.session_state.pop(components.judge_result_key(VAR), None)   # 「↩ 回到原题」站点
        assert fake.session_state[components.judge_result_key(PID_A)] == "baseResult"
        assert components.judge_result_key(VAR) not in fake.session_state

    def test_pop_is_tolerant_when_slot_missing(self, fake):
        fake.session_state.pop(components.judge_result_key(PID_A), None)   # 不得 KeyError


class TestDropShownUsesPidPointer:
    """切换类站点：手上没有 active_id，只能由 last_judge_pid 指认「正要离开的那道题」。"""

    def test_only_the_shown_slot_is_dropped(self, fake):
        fake.session_state[components.judge_result_key(PID_A)] = "resultA"
        fake.session_state[components.judge_result_key(PID_B)] = "resultB"
        fake.session_state["last_judge_pid"] = PID_B
        components.drop_shown_judge_result()
        assert components.judge_result_key(PID_B) not in fake.session_state
        assert fake.session_state[components.judge_result_key(PID_A)] == "resultA", (
            "失效面 B：清理越界——切换点应当只清「展示中」那一格"
        )

    def test_no_pid_pointer_is_a_noop(self, fake):
        """从没判过题就切：无凭据可定位，不得抛错、也不得乱清。"""
        fake.session_state[components.judge_result_key(PID_A)] = "resultA"
        components.drop_shown_judge_result()
        assert fake.session_state[components.judge_result_key(PID_A)] == "resultA"

    def test_empty_pid_pointer_is_a_noop(self, fake):
        fake.session_state["last_judge_pid"] = ""
        fake.session_state[components.judge_result_key(PID_A)] = "resultA"
        components.drop_shown_judge_result()
        assert fake.session_state[components.judge_result_key(PID_A)] == "resultA"

    def test_navigate_to_problem_routes_through_the_helper(self):
        src = Path(components.__file__).read_text(encoding="utf-8")
        block = src[src.index("def navigate_to_problem"):src.index("def code_highlight_lang")]
        assert "drop_shown_judge_result()" in block, "跨页导航没走统一清理口：清键口径会两处漂移"
        assert _BARE.search(block) is None


class TestLanguageSiteCensus:
    """六个清理点的归属：3 个切换点走 pid 定位，3 个原地动作点走 active_id。"""

    def _sites(self, src):
        drop = [n for n, ln in enumerate(src.splitlines(), 1) if ln.strip() == "drop_shown_judge_result()"]
        own = [n for n, ln in enumerate(src.splitlines(), 1)
               if ln.strip() == "st.session_state.pop(judge_result_key(active_id), None)"]
        return drop, own

    def test_three_plus_three_sites(self):
        src = Path(language_page.__file__).read_text(encoding="utf-8")
        drop, own = self._sites(src)
        assert len(drop) == 3, f"切换型清理点应恰 3 处（selection/切专题/切题目），实得 {drop}"
        assert len(own) == 3, f"原地动作清理点应恰 3 处（生成变式/回到原题/重置），实得 {own}"

    def test_reset_chain_order_still_five_steps(self):
        """l922-114 的五步顺序桩换了键形但没换语义（完成标准 ③）。"""
        src = Path(language_page.__file__).read_text(encoding="utf-8")
        block = src[src.index('if st.button("↺ 重置"'):src.index("with ask_col:")]
        order = [
            'st.session_state[key] = active.get("starter_code", "")',
            'epoch_key = f"editor_epoch::{active_id}"',
            'st.session_state[epoch_key] = st.session_state.get(epoch_key, 0) + 1',
            "st.session_state.pop(judge_result_key(active_id), None)",
            "st.rerun()",
        ]
        for frag in order:
            assert frag in block, f"重置分支缺 {frag}"
        idx = [block.index(f) for f in order]
        assert idx == sorted(idx), f"重置分支五步顺序被打乱：{idx}"

    def test_read_side_guard_still_pairing_pid(self):
        src = Path(language_page.__file__).read_text(encoding="utf-8")
        assert 'st.session_state.get(judge_result_key(active_id)) is not None' in src
        assert "r = st.session_state[judge_result_key(active_id)]" in src
        assert "st.session_state.last_judge_result" not in src, "属性式裸全局读写复活"

    def test_write_side_writes_namespaced_slot(self):
        src = Path(language_page.__file__).read_text(encoding="utf-8")
        assert "st.session_state[judge_result_key(active_id)] = result" in src
