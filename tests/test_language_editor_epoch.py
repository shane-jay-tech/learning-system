# -*- coding: utf-8 -*-
"""编辑器 epoch 换 key 重建机制桩（l922-114，钉 ui/pages/language.py::_editor_key :32-41）。

机制自述（docstring :34-38）：ACE / text_area 都是**带 key 的 widget**，其内部
状态优先级高于 value 参数——所以「重置本题」光把 `code::<pid>` 写成 starter_code
是没用的（前端未受控，下次 rerun 还会把旧值写回）。唯一生效手段是
epoch+1 → widget key 变化 → 组件重建。这个「换 key 骗重建」的写法没有任何
测试保护，本档补上。

两个键的分工（本档反复用到，务必分清）：
  code::<pid>              状态存储键（_problem_key），存用户当前代码
  editor_<pid>_<epoch>     widget 键（_editor_key），只为让 Streamlit 认出新组件
  editor_epoch::<pid>      epoch 计数器本身

与 LRU 单的边界互链（勿在本档重复钉清理断言）：
旧 epoch 留下的 `editor_<pid>_<0..n>` 残键**不在本档职责内**，由
tests/test_language_lru_eviction.py 的 rsplit 精确匹配清理负责；本档只钉
「key 是怎么生成的」以及「生成侧与自增侧的键名字面量必须一致」。
最真实的失效模式就是**两处字面量漂移**：:40 读 `editor_epoch::{active_id}`，
:285-286 写同名键；任何一边改名都会让 epoch 加了但 `_editor_key` 仍读旧值
→ 组件不重建 → 重置静默失效，且现有测试全绿。故 TestResetKeyContract 里
的「计数站点恰 2 处」不是洁癖，是这条链的保险丝。

源码零改动。可复跑：python -m pytest tests/test_language_editor_epoch.py -q
"""
from pathlib import Path

import pytest

import ui.pages.language as language_page
from tests.test_ui_behavior import FakeStreamlit

LANG_PY = Path(language_page.__file__)
EPOCH_KEY = "editor_epoch::{}"


@pytest.fixture()
def fake(monkeypatch):
    f = FakeStreamlit()
    monkeypatch.setattr(language_page, "st", f)
    return f


class TestKeyStability:
    """幂等与初值：读操作不得推进 epoch，否则每次 rerun 都在重建组件。"""

    def test_same_problem_same_key_twice(self, fake):
        k1 = language_page._editor_key("python/topic/p1")
        k2 = language_page._editor_key("python/topic/p1")
        assert k1 == k2 == "editor_python/topic/p1_0"
        assert fake.session_state[EPOCH_KEY.format("python/topic/p1")] == 0, (
            "取 key 的副作用把 epoch 推进了：下一次 rerun 会白重建一次编辑器"
        )

    def test_ten_reads_still_one_epoch(self, fake):
        for _ in range(10):
            language_page._editor_key("p")
        assert fake.session_state["editor_epoch::p"] == 0

    def test_key_is_scoped_per_problem(self, fake):
        assert language_page._editor_key("pA") != language_page._editor_key("pB")
        fake.session_state["editor_epoch::pA"] = 4
        assert language_page._editor_key("pA") == "editor_pA_4"
        assert language_page._editor_key("pB") == "editor_pB_0", "pA 的重置串扰了 pB"


class TestEpochBumpChangesKey:
    """docstring 自述的机制本体：epoch+1 ⇒ key 变 ⇒ 组件重建。"""

    def test_bump_then_key_changes(self, fake):
        before = language_page._editor_key("p1")
        fake.session_state[EPOCH_KEY.format("p1")] = fake.session_state.get(
            EPOCH_KEY.format("p1"), 0) + 1
        after = language_page._editor_key("p1")
        assert before == "editor_p1_0" and after == "editor_p1_1"
        assert before != after, "换 key 机制失效：重置不会重建编辑器"

    def test_repeated_bumps_monotonic(self, fake):
        keys = []
        for _ in range(3):
            keys.append(language_page._editor_key("p1"))
            fake.session_state["editor_epoch::p1"] = fake.session_state.get("editor_epoch::p1", 0) + 1
        assert keys == ["editor_p1_0", "editor_p1_1", "editor_p1_2"]
        assert len(set(keys)) == 3, "三次重置拿到同一个 widget key"

    def test_missing_counter_starts_from_zero(self, fake):
        """session_state 里没有该键（LRU 刚把它清掉）时不得抛错，从 0 起。"""
        assert language_page._editor_key("fresh") == "editor_fresh_0"
        assert fake.session_state["editor_epoch::fresh"] == 0


class TestResetKeyContract:
    """重置按钮（:280-288）与本函数的字面量必须同源，且三步顺序不得乱。"""

    def test_epoch_counter_sites_are_exactly_two(self):
        src = LANG_PY.read_text(encoding="utf-8")
        sites = [ln.strip() for ln in src.splitlines() if 'editor_epoch::{' in ln]
        assert len(sites) == 2, (
            f"`editor_epoch::{{active_id}}` 字面量应恰 2 处（:40 读 / :285 写），实际 {len(sites)} 处：{sites}"
        )

    def test_reset_writes_starter_then_bumps_then_reruns(self):
        src = LANG_PY.read_text(encoding="utf-8")
        block = src[src.index('if st.button("↺ 重置"'):src.index('with ask_col:')]
        order = [
            'st.session_state[key] = active.get("starter_code", "")',
            'epoch_key = f"editor_epoch::{active_id}"',
            'st.session_state[epoch_key] = st.session_state.get(epoch_key, 0) + 1',
            'st.session_state.pop(judge_result_key(active_id), None)',
            "st.rerun()",
        ]
        for frag in order:
            assert frag in block, f"重置分支缺少 {frag}：换 key 链已断，本档需随实现重写"
        idx = [block.index(f) for f in order]
        assert idx == sorted(idx), f"重置分支三步顺序被打乱：{idx}"
        assert "editor_epoch::" in block and "_editor_key" not in block, (
            "重置分支不应自己拼 widget key（拼接职责在 _editor_key，:41）"
        )

    def test_reading_side_and_writing_side_use_same_name_shape(self):
        """生成侧读的是 f"editor_epoch::{active_id}"，必须与自增侧同一形态。"""
        src = LANG_PY.read_text(encoding="utf-8")
        assert 'st.session_state.setdefault(f"editor_epoch::{active_id}", 0)' in src
        assert 'f"editor_epoch::{active_id}"' in src
        assert src.count('f"editor_epoch::{active_id}"') == 2

    def test_key_format_is_underscore_joined_not_prefixed(self):
        src = LANG_PY.read_text(encoding="utf-8")
        assert 'return f"editor_{active_id}_{epoch}"' in src, (
            "widget key 形态变了：LRU 档的 rsplit(\"_\", 1) 精确匹配也要同步改"
        )


class TestCrossTalkWithLruEviction:
    """与 LRU 单的接缝：epoch 记账键被清后重访，行为自洽且无脏残键可读。"""

    def test_revisit_after_eviction_restarts_at_epoch_zero(self, fake):
        cap = language_page._LRU_CAP
        pid = "py_mid"
        fake.session_state[f"editor_epoch::{pid}"] = 5
        assert language_page._editor_key(pid) == "editor_py_mid_5"
        fake.session_state[f"editor_{pid}_5"] = "half-written"
        fake.session_state[f"code::{pid}"] = "half-written"
        language_page._touch_problem(pid)                       # 先让它进 LRU 队列

        for i in range(cap + 1):                                # 再把 pid 挤出窗口
            language_page._touch_problem(f"z{i}")
        assert f"editor_epoch::{pid}" not in fake.session_state
        assert [k for k in fake.session_state if k.startswith(f"editor_{pid}_")] == [], (
            "旧 epoch 残键应由 LRU 的 rsplit 清扫带走（清理断言见 test_language_lru_eviction）"
        )
        assert language_page._editor_key(pid) == f"editor_{pid}_0", "重访后 epoch 未回到 0"

    def test_epoch_bookkeeping_key_is_not_a_widget_key(self, fake):
        """editor_epoch::<pid> 与 editor_<pid>_<epoch> 不得互相命中。"""
        assert language_page._editor_key("pX") != EPOCH_KEY.format("pX")
        body = EPOCH_KEY.format("pX")[len("editor_"):]
        assert "_" not in body, "记账键名里出现了 `_`：LRU 的 sweep 会把它当 widget 键切"

    def test_variant_ids_get_own_key_and_are_not_lru_managed(self, fake):
        """AI 变式题（AI_VARIANT:: 前缀）走同一拼 key 规则，但它不进 LRU。

        登记面：变式题的 editor_* 与 editor_epoch::* 都不受 :49-74 逐出管理，
        长会话里刷很多变式题时这部分是无界增长——现状如此，本档只钉桩不修。
        """
        vid = "AI_VARIANT::python/topic/p0"
        assert language_page._editor_key(vid) == f"editor_{vid}_0"
        language_page._touch_problem(vid)
        assert "_problem_lru" not in fake.session_state, "变式题不该进 LRU（:55 提前 return）"
