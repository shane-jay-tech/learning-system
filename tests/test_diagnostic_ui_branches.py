# -*- coding: utf-8 -*-
"""诊断页 _render_quiz 分支行为桩（l922-111）。

test_diagnostic.py 只测 evaluate/存取纯函数层；本档用 FakeStreamlit
（复用 tests/test_ui_behavior.py 的桩基类，同 test_dashboard_page_render 模式）
驱动 UI 层三条分支：
①部分未答 → warning 列出题号串、不调 save、不 rerun；
②全部作答 → evaluate 真算、save 被调、retake_diagnostic 复位 False、rerun；
③跳过诊断 → route="paths" + rerun，不触发作答校验。
另钉 :45 radio index=None（不预选防误提交）源码锚。
可复跑：python -m pytest tests/test_diagnostic_ui_branches.py -q
"""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import ui.pages.diagnostic as diagnostic_page
from core.diagnostic import DIAGNOSTIC_QUESTIONS

import app  # noqa: F401  # app 侧 import 预绑定 st（与 test_ui_behavior 同桩模式）
from tests.test_ui_behavior import FakeStreamlit

DIAG_PY = Path(__file__).resolve().parent.parent / "ui" / "pages" / "diagnostic.py"


class DiagnosticFakeStreamlit(FakeStreamlit):
    """基类 radio 恒返 options[0]；此处按 key 控制选项，None＝该题未答。"""

    def __init__(self, radios=None, buttons=None):
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


@pytest.fixture()
def fake(monkeypatch):
    """默认：提交按钮按下。radio 结果与按钮由用例经 fake.radios/fake.buttons 调。"""
    f = DiagnosticFakeStreamlit(buttons={"提交诊断": True})
    monkeypatch.setattr(diagnostic_page, "st", f)
    return f


@pytest.fixture()
def save_spy(monkeypatch):
    rec = {}
    def _spy(dao, result):
        rec["dao"] = dao
        rec["result"] = result
    monkeypatch.setattr(diagnostic_page, "save_diagnostic_result", _spy)
    return rec


def _warnings(fake):
    return [c[1][0] for c in fake.calls if c[0] == "warning"]


class TestPartialUnanswered:
    def test_warning_lists_numbers_and_no_save(self, fake, save_spy):
        # 第 2、4 题未答（radio 返回 None），其余答对
        fake.radios = {_key(1): None, _key(3): None}
        for i in (0, 2):
            fake.radios[_key(i)] = DIAGNOSTIC_QUESTIONS[i]["answer"]
        dao = MagicMock()
        diagnostic_page._render_quiz(dao)

        ws = _warnings(fake)
        assert len(ws) == 1, f"warning 应恰好一条: {ws}"
        assert "第 2, 4 题" in ws[0] and "2 题未作答" in ws[0], ws[0]
        assert save_spy == {}, "未答分支不得落库"
        assert fake.rerun_count == 0, "warning 分支不应 rerun"


class TestAllAnswered:
    def test_saves_result_and_resets_retake(self, fake, save_spy):
        fake.radios = {
            _key(i): DIAGNOSTIC_QUESTIONS[i]["answer"]
            for i in range(len(DIAGNOSTIC_QUESTIONS))
        }
        fake.session_state["retake_diagnostic"] = True  # 重测场景进入
        dao = MagicMock()
        diagnostic_page._render_quiz(dao)

        assert save_spy, "全答分支必须调 save_diagnostic_result"
        assert save_spy["dao"] is dao
        assert save_spy["result"]["total_correct"] == len(DIAGNOSTIC_QUESTIONS)
        assert fake.session_state["retake_diagnostic"] is False
        assert fake.rerun_count == 1
        assert _warnings(fake) == []


class TestSkipNavigation:
    def test_skip_sets_route_paths_without_save(self, monkeypatch):
        fake = DiagnosticFakeStreamlit(buttons={"跳过诊断": True})
        fake.radios = {_key(i): None for i in range(len(DIAGNOSTIC_QUESTIONS))}
        monkeypatch.setattr(diagnostic_page, "st", fake)
        rec = {}
        monkeypatch.setattr(diagnostic_page, "save_diagnostic_result",
                            lambda *a, **kw: rec.setdefault("called", True))
        diagnostic_page._render_quiz(MagicMock())

        assert fake.session_state.route == "paths"
        assert fake.rerun_count == 1
        assert "called" not in rec
        assert _warnings(fake) == [], "跳过分支不该触发未答 warning"


class TestSourcePins:
    def test_radio_preselect_disabled(self):
        """钉 :45 语义：radio 不预选第一项（index=None），防没看题就误提交。"""
        src = DIAG_PY.read_text(encoding="utf-8")
        quiz = src[src.index("def _render_quiz"):src.index("def _render_result")]
        assert "st.radio(" in quiz, "quiz 不再用 radio？本钉桩需随实现重写"
        assert "index=None" in quiz, "index=None 丢失：第一项将被预选，未看题即可误提交"
