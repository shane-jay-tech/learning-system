# -*- coding: utf-8 -*-
"""诊断页「重测」状态机三态桩（l922-112）。

l922-111 的 tests/test_diagnostic_ui_branches.py 只驱动 _render_quiz 内部的
三条作答分支；本档补它没覆盖的 **路由层三态**（render_diagnostic :22 那个
`if existing and not st.session_state.get("retake_diagnostic")`）：

  态 A 已有结果且未点重测 → 展示结果 _render_result
  态 B 已有结果但 retake_diagnostic=True → 绕过结果直接进问卷 _render_quiz
  态 C 问卷提交成功 → retake_diagnostic 复位 False，下一次渲染回到态 A

中断残留（本档钉的就是这个语义，**按现状钉桩、不修**）：
「重新测试」按钮（:92-97）会一次性清空全部 diag_* 旧答案并把
retake_diagnostic 置 True 后 rerun；但该标志**只由「提交诊断」复位**
（:60）。若用户点了重测后中途切走（改走侧边栏去别页 / 关窗口 / 只答半截就
放弃），retake_diagnostic 会长期残留 True —— 下次再进诊断页时，即使库里
已有诊断结果，也会跳过结果页直落问卷，且旧答案已被清干净（看起来像「从没
测过」）。这是可复现的用户可见行为，登记为在册观察项；任务书明确「仅记录、
不改路由逻辑，改动留授权」，故此处只把它钉进测试：将来若有人给 :22 加
自动复位或改路由优先级，本档会立刻变红并要求说明。

可复跑：python -m pytest tests/test_diagnostic_retake_state.py -q
"""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import ui.pages.diagnostic as diagnostic_page
from core.diagnostic import DIAGNOSTIC_QUESTIONS

import app  # noqa: F401  # 与 test_ui_behavior 同桩模式：app 侧 import 预绑定 st
from tests.test_ui_behavior import FakeStreamlit

DIAG_PY = Path(__file__).resolve().parent.parent / "ui" / "pages" / "diagnostic.py"

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


@pytest.fixture()
def drive_render(monkeypatch):
    """返回 callable(existing)：以给定库内结果渲染一次诊断页，交出渲染序列。"""
    dao = MagicMock()
    monkeypatch.setattr(diagnostic_page, "ProgressDAO", lambda *a, **kw: dao)
    fake = QuizFakeStreamlit()
    monkeypatch.setattr(diagnostic_page, "st", fake)

    def _go(existing):
        seen = _spy_branches(monkeypatch)
        monkeypatch.setattr(diagnostic_page, "get_diagnostic_result", lambda d: existing)
        diagnostic_page.render_diagnostic()
        return seen

    _go.fake = fake
    _go.dao = dao
    return _go


class TestRouteTruthTable:
    """:22 复合条件的真值表——两个操作数各自的假值都要能落到问卷。"""

    @pytest.mark.parametrize("existing,retake,want", [
        (SAVED_RESULT, None, "result"),      # 未设过该键
        (SAVED_RESULT, False, "result"),     # 显式复位后
        (SAVED_RESULT, True, "quiz"),        # 重测中
        (None, None, "quiz"),                # 首次诊断
        (None, True, "quiz"),                # 无结果 + 残留标志
    ])
    def test_branch_matches_condition(self, drive_render, existing, retake, want):
        if retake is not None:
            drive_render.fake.session_state["retake_diagnostic"] = retake
        seen = drive_render(existing)
        assert [s[0] for s in seen] == [want], f"existing={existing} retake={retake}"
        if want == "result":
            assert seen[0][1] is existing, "结果页必须拿到库内原结果对象，不得再造一份"

    def test_dao_closed_even_on_quiz_branch(self, drive_render):
        drive_render(None)
        drive_render.dao.close.assert_called_once()


class TestRetakeButton:
    """:92-97「重新测试」：清全部 diag_* 旧答案 + 置标志 + rerun。"""

    def _click(self, monkeypatch, **preset):
        fake = QuizFakeStreamlit(buttons={"重新测试": True})
        fake.session_state.update(preset)
        monkeypatch.setattr(diagnostic_page, "st", fake)
        diagnostic_page._render_result(dict(SAVED_RESULT), MagicMock())
        return fake

    def test_every_question_key_is_popped(self, monkeypatch):
        preset = {_key(i): i for i in range(len(DIAGNOSTIC_QUESTIONS))}
        preset["last_judge_result"] = "keepme"      # 非 diag_ 前缀，不该被牵连
        fake = self._click(monkeypatch, **preset)

        left = [k for k in fake.session_state if k.startswith("diag_")]
        assert left == [], f"重测后仍残留旧答案键：{left}"
        assert fake.session_state["retake_diagnostic"] is True
        assert fake.session_state["last_judge_result"] == "keepme", "清理范围越界"
        assert fake.rerun_count == 1

    def test_pop_is_tolerant_when_no_stale_answers(self, monkeypatch):
        """库里没旧答案时点重测不得抛 KeyError（pop 带默认值）。"""
        fake = self._click(monkeypatch)
        assert fake.session_state["retake_diagnostic"] is True
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
    """中断残留：点重测后不提交就切走 → 标志长期为 True，结果页再也看不到。

    本类是「现状备案」而非「期望修复」：断言的是当前真实行为。
    """

    def test_abandoned_retake_keeps_bypassing_saved_result(self, monkeypatch):
        fake = QuizFakeStreamlit(buttons={"重新测试": True})
        for i in range(len(DIAGNOSTIC_QUESTIONS)):
            fake.session_state[_key(i)] = 0
        monkeypatch.setattr(diagnostic_page, "st", fake)
        dao = MagicMock()
        monkeypatch.setattr(diagnostic_page, "ProgressDAO", lambda *a, **kw: dao)
        monkeypatch.setattr(diagnostic_page, "get_diagnostic_result",
                            lambda d: SAVED_RESULT)

        diagnostic_page._render_result(SAVED_RESULT, dao)   # 用户点了「重新测试」
        assert fake.session_state["retake_diagnostic"] is True, "按钮未置重测标志？"

        seen = _spy_branches(monkeypatch)                    # 中途切走，再回来
        diagnostic_page.render_diagnostic()
        assert _names(seen) == ["quiz"], (
            "重测标志已复位？若确为有意改动，请连同类注释一起更新本档说明"
        )
        assert [k for k in fake.session_state if k.startswith("diag_")] == [], (
            "旧答案在用户尚未作答前就已被清空——这就是残留态看起来像「没测过」的原因"
        )

    def test_route_module_owns_the_flag_in_three_places(self):
        """钉住 :22/:60/:96 三个站点，防止悄悄新增第四处复位（改动需授权）。"""
        src = DIAG_PY.read_text(encoding="utf-8")
        assert src.count("retake_diagnostic") == 3, (
            f"标志出现 {src.count('retake_diagnostic')} 处，预期 3 处（读/置真/置假）"
        )
        guard = next(ln for ln in src.splitlines() if "if existing and not" in ln)
        assert 'st.session_state.get("retake_diagnostic")' in guard, ":22 判定条件漂移"
        assert 'st.session_state["retake_diagnostic"] = True' in src
        assert 'st.session_state["retake_diagnostic"] = False' in src

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
