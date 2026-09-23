# -*- coding: utf-8 -*-
"""诊断页「重测」状态机桩（l922-112 建档；l923-14 按授权改成带时间戳的一次性意图语义）。

l922-111 的 tests/test_diagnostic_ui_branches.py 只驱动 _render_quiz 内部的
三条作答分支；本档补它没覆盖的 **路由层状态机**（`render_diagnostic` 里
`if existing and _retake_intent_state() != "active"` 那一步）：

  态 A 已有结果且无重测意图 → 展示结果 _render_result
  态 B 已有结果但意图 active → 绕过结果直接进问卷 _render_quiz
  态 C 问卷提交成功 → 意图复位，下一次渲染回态 A

🔴 l923-14 语义变更（不是「现状备案」了）：l922-112 当时把这行的中断残留**按现状钉桩、不修**，
并在档里预告「真要在代码层收口，最小改法是把标志改成带时间戳的一次性意图（渲染结果页后即消费），
但那属于 :22 路由逻辑改动，改动留授权」。授权已到位（主班派单 l923-14 点名做这条出口），
`ui/pages/diagnostic.py` 现按该改法实现：

  - 置位：「重新测试」按钮写 **时间戳**（`_now()`），不再写 True；
  - 消费：路由走**结果页**分支时 `pop` 掉键（一次性），False/expired/invalid 一并清干净；
  - 失效：距置位超过 `RETAKE_INTENT_TTL_SECONDS`（600s＝10 分钟）自动不再绕过结果页；
  - 兼容：旧布尔 True 仍视为 active（生产码已不写 True，只有历史会话与本档既有真值表会造出
    这形态；结果页一到手同样被 pop）—— tests/test_diagnostic_ui_branches.py 的
    「重测场景进入」用的就是 True，兼容它才不会让两支无关用例平白变红。

⇒ 本档同时保留「防悄悄改路由」的能力：源码形状桩从三站点改钉**四站点**
（读 / 置时间戳 / 提交复位 / 结果页消费），新增第五处即红。

可复跑：python -m pytest tests/test_diagnostic_retake_state.py -q
"""
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import ui.pages.diagnostic as diagnostic_page
from core.diagnostic import DIAGNOSTIC_QUESTIONS

import app  # noqa: F401  # 与 test_ui_behavior 同桩模式：app 侧 import 预绑定 st
from tests.test_ui_behavior import FakeStreamlit

DIAG_PY = Path(__file__).resolve().parent.parent / "ui" / "pages" / "diagnostic.py"

# 冻结时钟用的基准时刻：意图值一律相对它表达，跑测耗时多久都不影响判定。
_T0 = time.mktime(time.strptime("2026-09-23 10:00:00", "%Y-%m-%d %H:%M:%S"))
_TTL = diagnostic_page.RETAKE_INTENT_TTL_SECONDS

SAVED_RESULT = {
    "total_correct": 3,
    "total_questions": len(DIAGNOSTIC_QUESTIONS),
    "recommendation_key": "has_python",
    "recommendation": {"message": "有 Python 基础", "path": "python", "milestone": "m1"},
}


class QuizFakeStreamlit(FakeStreamlit):
    """基类 radio 恒返 options[0]；此处按 key 控制作答，None＝该题未答。"""

    def __init__(self, buttons=None, radios=None):
        super().__init__(buttons=buttons)
        self.radios = radios or {}

    def __getattr__(self, name):
        if name == "radio":
            def call(label, options, *a, key=None, **kw):
                self.calls.append(("radio", (label,), {"key": key}))
                return self.radios.get(key, options[0])
            return call
        return super().__getattr__(name)


def _key(i):
    return f"diag_{DIAGNOSTIC_QUESTIONS[i]['id']}"


def _spy_branches(monkeypatch):
    """把两个渲染函数换成记账桩，返回 [(分支名, 传入结果对象), ...]（调用后增长）。"""
    seen = []
    monkeypatch.setattr(diagnostic_page, "_render_result",
                        lambda result, dao: seen.append(("result", result)))
    monkeypatch.setattr(diagnostic_page, "_render_quiz",
                        lambda dao: seen.append(("quiz", None)))
    return seen


def _names(seen):
    return [s[0] for s in seen]


def _intent_value(kind):
    """把真值表里的意图形态翻译成实际存进 session_state 的值（相对冻结的 _T0）。"""
    if kind == "fresh":
        return _T0 - 60.0                      # 1 分钟前置位
    if kind == "edge":
        return _T0 - _TTL                      # 恰好等于 TTL：判据是 age > TTL ⇒ 仍 active
    if kind == "stale":
        return _T0 - (_TTL + 1.0)              # 超 1 秒：失效
    if kind == "garbage":
        return "昨天点过"                        # 不可解析的脏值
    return kind                                # None / False / True 原样


@pytest.fixture()
def drive_render(monkeypatch):
    """返回 callable(existing)：以给定库内结果渲染一次诊断页，交出渲染序列。"""
    dao = MagicMock()
    monkeypatch.setattr(diagnostic_page, "ProgressDAO", lambda *a, **kw: dao)
    monkeypatch.setattr(diagnostic_page, "_now", lambda: _T0)  # 冻结时钟，超时判定可复算
    fake = QuizFakeStreamlit()
    monkeypatch.setattr(diagnostic_page, "st", fake)

    def _go(existing):
        seen = _spy_branches(monkeypatch)
        monkeypatch.setattr(diagnostic_page, "get_diagnostic_result", lambda d: existing)
        diagnostic_page.render_diagnostic()
        return seen

    _go.fake = fake
    _go.dao = dao
    _go.monkeypatch = monkeypatch
    return _go


class TestRouteTruthTable:
    """路由判定的真值表——两个操作数各自的假值都要能落到问卷（l923-14 起含四种意图形态）。"""

    @pytest.mark.parametrize("existing,retake,want", [
        (SAVED_RESULT, None, "result"),      # 未设过该键
        (SAVED_RESULT, False, "result"),     # 显式复位后（提交诊断写 False）
        (SAVED_RESULT, True, "quiz"),        # 旧布尔协议：无时间戳可依，按 active 放行
        (None, None, "quiz"),                # 首次诊断
        (None, True, "quiz"),                # 无结果 + 残留标志
        (SAVED_RESULT, "fresh", "quiz"),     # 时间戳在 TTL 内 → 绕过结果页
        (SAVED_RESULT, "edge", "quiz"),      # 恰在 TTL 边界 → 仍算 active（> 才失效）
        (SAVED_RESULT, "stale", "result"),   # 🔴 超时 → 回到结果页（这就是修掉的残留）
        (SAVED_RESULT, "garbage", "result"),  # 脏值 → 按无意图处理，不把用户关在问卷里
        (None, "stale", "quiz"),             # 库里没结果：无论意图如何都得走问卷
    ])
    def test_branch_matches_condition(self, drive_render, existing, retake, want):
        if retake is not None:
            drive_render.fake.session_state["retake_diagnostic"] = _intent_value(retake)
        seen = drive_render(existing)
        assert [s[0] for s in seen] == [want], f"existing={existing} retake={retake}"
        if want == "result":
            assert seen[0][1] is existing, "结果页必须拿到库内原结果对象，不得再造一份"

    @pytest.mark.parametrize("retake", [False, True, "stale", "garbage"])
    def test_结果页分支后意图键的状态(self, drive_render, retake):
        """一次性语义：走结果页时 False/脏值/expired 一律被清；True 是旧协议、判 active 所以不经过结果页。"""
        key = "retake_diagnostic"
        fake = drive_render.fake
        if retake is True:                    # True 会把路由引到问卷页，本例只测「进结果页 ⇒ 键被清」
            fake.session_state[key] = True
            assert _names(drive_render(SAVED_RESULT)) == ["quiz"]
            assert fake.session_state[key] is True, "问卷页不得提前消费意图（否则答一半切走就丢）"
            return
        fake.session_state[key] = _intent_value(retake)
        assert _names(drive_render(SAVED_RESULT)) == ["result"]
        assert key not in fake.session_state, f"进结果页后意图键未清（现值 {fake.session_state.get(key)!r}）"

    def test_dao_closed_even_on_quiz_branch(self, drive_render):
        drive_render(None)
        drive_render.dao.close.assert_called_once()


def _assert_active_intent(fake, label="重测意图"):
    """l923-14 后的置位形态：值必须是**正浮点时间戳**且判为 active（旧桩在此断言 is True）。"""
    val = fake.session_state["retake_diagnostic"]
    assert isinstance(val, float) and val > 0, f"{label}应为时间戳，实得 {val!r}"
    assert diagnostic_page._retake_intent_state() == "active", f"{label}未判为 active：{val!r}"
    return val


class TestRetakeButton:
    """:135-142「重新测试」：清全部 diag_* 旧答案 + 置**带时间戳的意图** + rerun。"""

    def _click(self, monkeypatch, **preset):
        fake = QuizFakeStreamlit(buttons={"重新测试": True})
        fake.session_state.update(preset)
        monkeypatch.setattr(diagnostic_page, "st", fake)
        diagnostic_page._render_result(dict(SAVED_RESULT), MagicMock())
        return fake

    def test_every_question_key_is_popped(self, monkeypatch):
        preset = {_key(i): i for i in range(len(DIAGNOSTIC_QUESTIONS))}
        # l923-16：评判结果缓存已改 per-pid 命名空间，这里仍取「非 diag_ 前缀」的真实键形
        preset["last_judge_result::python/t/p1"] = "keepme"   # 非 diag_ 前缀，不该被牵连
        fake = self._click(monkeypatch, **preset)

        left = [k for k in fake.session_state if k.startswith("diag_")]
        assert left == [], f"重测后仍残留旧答案键：{left}"
        _assert_active_intent(fake)
        assert fake.session_state["last_judge_result::python/t/p1"] == "keepme", "清理范围越界"
        assert fake.rerun_count == 1

    def test_pop_is_tolerant_when_no_stale_answers(self, monkeypatch):
        """库里没旧答案时点重测不得抛 KeyError（pop 带默认值）。"""
        fake = self._click(monkeypatch)
        _assert_active_intent(fake)
        assert fake.rerun_count == 1


class TestSubmitResetsFlag:
    """态 C：提交成功后标志复位，页面回到态 A。"""

    @staticmethod
    def _answered_fake(monkeypatch, save_rec):
        fake = QuizFakeStreamlit(
            buttons={"提交诊断": True},
            radios={_key(i): DIAGNOSTIC_QUESTIONS[i]["answer"]
                    for i in range(len(DIAGNOSTIC_QUESTIONS))},
        )
        monkeypatch.setattr(diagnostic_page, "st", fake)
        monkeypatch.setattr(diagnostic_page, "save_diagnostic_result",
                            lambda dao, result: save_rec.update(result=result))
        return fake

    def test_retake_flag_back_to_false(self, monkeypatch):
        rec = {}
        fake = self._answered_fake(monkeypatch, rec)
        fake.session_state["retake_diagnostic"] = True
        for i in range(len(DIAGNOSTIC_QUESTIONS)):
            fake.session_state[_key(i)] = 0          # 重测期间新答出来的键
        diagnostic_page._render_quiz(MagicMock())

        assert rec, "全答分支必须落库"
        assert fake.session_state["retake_diagnostic"] is False
        assert fake.rerun_count == 1

    def test_full_cycle_quiz_then_result(self, monkeypatch):
        rec = {}
        fake = self._answered_fake(monkeypatch, rec)
        fake.session_state["retake_diagnostic"] = True
        diagnostic_page._render_quiz(MagicMock())     # 态 B → 提交 → 复位

        seen = _spy_branches(monkeypatch)
        dao = MagicMock()
        monkeypatch.setattr(diagnostic_page, "ProgressDAO", lambda *a, **kw: dao)
        monkeypatch.setattr(diagnostic_page, "get_diagnostic_result",
                            lambda d: SAVED_RESULT)
        diagnostic_page.render_diagnostic()
        assert _names(seen) == ["result"], "提交后应回到结果页而非再次问卷"
        assert rec, "提交必须已落库，否则回到的结果页是空的"


class TestInterruptionResidue:
    """中断残留：点重测后不提交就切走（l922-112 建档时钉的是**现状**，l923-14 起钉**已修语义**）。

    改造依据（授权出处）：l922-112 结果档预告「真要在代码层收口，最小改法是把标志改成带
    时间戳的一次性意图（渲染结果页后即消费），但那属于 :22 路由逻辑改动，改动留授权」；
    主班派单 l923-14 点名执行该出口 ⇒ 本类从「现状备案」翻成「期望行为」，
    连同类注释与源码形状桩一起改写（旧断言 `_names(seen) == ["quiz"]` 的残留语义已不成立）。
    """

    def _fresh(self, monkeypatch, **buttons):
        fake = QuizFakeStreamlit(buttons=buttons)
        monkeypatch.setattr(diagnostic_page, "st", fake)
        dao = MagicMock()
        monkeypatch.setattr(diagnostic_page, "ProgressDAO", lambda *a, **kw: dao)
        monkeypatch.setattr(diagnostic_page, "get_diagnostic_result", lambda d: SAVED_RESULT)
        return fake, dao

    def test_一次性消费_提交并渲染结果页后不再触发重测(self, monkeypatch):
        fake, dao = self._fresh(monkeypatch, **{"重新测试": True, "提交诊断": True})
        fake.radios = {_key(i): DIAGNOSTIC_QUESTIONS[i]["answer"]
                       for i in range(len(DIAGNOSTIC_QUESTIONS))}
        saved = {}
        monkeypatch.setattr(diagnostic_page, "save_diagnostic_result",
                            lambda d, r: saved.update(result=r))
        real_quiz = diagnostic_page._render_quiz

        # 1) 结果页上点「重新测试」：旧答案被清、意图置位
        diagnostic_page._render_result(dict(SAVED_RESULT), dao)
        _assert_active_intent(fake)
        assert [k for k in fake.session_state if k.startswith("diag_")] == []

        # 2) rerun：意图生效 → 问卷页，且**不得提前消费**（答一半切走还得留着意图重进）
        seen = _spy_branches(monkeypatch)
        stamp = fake.session_state["retake_diagnostic"]
        diagnostic_page.render_diagnostic()
        assert _names(seen) == ["quiz"]
        assert fake.session_state["retake_diagnostic"] == stamp, "问卷页提前吃掉了一次性意图"

        # 3) 真答完提交（走未被 spy 的 _render_quiz）→ 复位 False
        real_quiz(dao)
        assert saved, "全答分支必须落库，否则后面的结果页是空的"
        assert fake.session_state["retake_diagnostic"] is False

        # 4) 下一次渲染：回结果页 ＋ 意图键被消费清除（完成标准 ① 的断言点）
        diagnostic_page.render_diagnostic()
        assert _names(seen) == ["quiz", "result"], "提交后应回到结果页而非再次问卷"
        assert "retake_diagnostic" not in fake.session_state, "结果页未消费清除意图键"

        # 5) 同会话再进页：仍是结果页，永不再被带回问卷
        diagnostic_page.render_diagnostic()
        assert _names(seen) == ["quiz", "result", "result"]

    def test_超时后意图自动失效_中途切走不再把用户带回问卷(self, monkeypatch):
        """完成标准 ②：时间戳过期 ⇒ 意图不再绕过结果页（旧语义里这会永久绕过）。"""
        fake, dao = self._fresh(monkeypatch, **{"重新测试": True})
        clock = {"t": _T0}
        monkeypatch.setattr(diagnostic_page, "_now", lambda: clock["t"])

        diagnostic_page._render_result(dict(SAVED_RESULT), dao)   # 用户点了「重新测试」
        assert fake.session_state["retake_diagnostic"] == _T0

        seen = _spy_branches(monkeypatch)
        clock["t"] = _T0 + _TTL                                  # 边界内（判据是 age > TTL）
        diagnostic_page.render_diagnostic()
        assert _names(seen) == ["quiz"], "TTL 边界内意图应仍生效"
        assert "retake_diagnostic" in fake.session_state

        clock["t"] = _T0 + _TTL + 1.0                            # 越界一格
        diagnostic_page.render_diagnostic()
        assert _names(seen) == ["quiz", "result"], (
            f"超时后仍绕过结果页（旧残留语义复现）：TTL={_TTL}s")
        assert "retake_diagnostic" not in fake.session_state, "过期意图应随结果页一并清除"

    @pytest.mark.parametrize("stored,want", [
        (None, "none"), (False, "none"), (True, "active"),
        ("fresh", "active"), ("edge", "active"), ("stale", "expired"),
        ("garbage", "invalid"),
    ])
    def test_意图状态函数四态且只读不写(self, monkeypatch, stored, want):
        """`_retake_intent_state` 是纯读函数：清除只由路由层做一次，避免同一渲染里状态被改两回。"""
        fake = QuizFakeStreamlit()
        monkeypatch.setattr(diagnostic_page, "st", fake)
        monkeypatch.setattr(diagnostic_page, "_now", lambda: _T0)
        if stored is not None:
            fake.session_state["retake_diagnostic"] = _intent_value(stored)
        assert diagnostic_page._retake_intent_state() == want
        if stored is None:
            assert "retake_diagnostic" not in fake.session_state
        else:
            assert fake.session_state["retake_diagnostic"] == _intent_value(stored), "读函数写了 session_state"

    def test_route_module_owns_the_intent_in_four_places(self):
        """钉住 l923-14 的四个站点（读/置时间戳/提交复位/结果页消费），新增第五处即红。"""
        src = DIAG_PY.read_text(encoding="utf-8")
        code_lines = [ln for ln in src.splitlines() if not ln.lstrip().startswith("#")]
        sites = [ln.strip() for ln in code_lines if "retake_diagnostic" in ln]
        assert len(sites) == 4, (
            f"意图键的字面站点数变了，现 {len(sites)} 处（预期 4：读/置真/置假/消费）：\n  "
            + "\n  ".join(sites))
        assert 'st.session_state.get("retake_diagnostic")' in src, "读站点漂移"
        assert 'st.session_state["retake_diagnostic"] = _now()' in src, "置位已不写时间戳？"
        assert 'st.session_state["retake_diagnostic"] = False' in src, "提交复位站点漂移"
        assert 'st.session_state.pop("retake_diagnostic", None)' in src, "结果页消费清除站点漂移"
        guard = next(ln for ln in src.splitlines() if "if existing and" in ln)
        assert '_retake_intent_state() != "active"' in guard, ":22 路由判定条件漂移"

    def test_reset_happens_after_save_and_before_rerun(self):
        """提交分支顺序：evaluate → save → 复位 → rerun，乱序会让复位丢失。"""
        src = DIAG_PY.read_text(encoding="utf-8")
        body = src[src.index("result = evaluate_diagnostic(answers)"):src.index("with col2:\n        if st.button(\"跳过诊断\"")]
        for frag in ("save_diagnostic_result(dao, result)",
                     'st.session_state["retake_diagnostic"] = False',
                     "st.rerun()"):
            assert frag in body, f"提交分支缺少 {frag}"
        assert (body.index("save_diagnostic_result")
                < body.index('st.session_state["retake_diagnostic"] = False')
                < body.index("st.rerun()")), "提交分支内三步顺序被改动"
