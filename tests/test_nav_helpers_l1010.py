"""ui/components nav_is_active + nav_button 首测（l1010-40）。

d913c-09 导航当前项高亮判定单源的首测钉桩：nav_is_active 纯函数行为测
（str/set/list 三形态收编 + extra_condition 短路 + 空集），nav_button 走
monkeypatch st.button 双形态（active→type 传参核对 + 回调触发语义）。
与 test_ui_behavior.py 不共笔（本件自含，只触导航双函数）。
"""
import types

import pytest

import ui.components as components


class TestNavIsActive:
    def test_str_form(self):
        assert components.nav_is_active("home", "home") is True
        assert components.nav_is_active("home", "diagnostic") is False

    def test_set_form(self):
        aliases = {"english", "english_home"}
        assert components.nav_is_active("english", aliases) is True
        assert components.nav_is_active("english_home", aliases) is True
        assert components.nav_is_active("math", aliases) is False

    def test_list_form(self):
        assert components.nav_is_active("review", ["review", "review_hub"]) is True
        assert components.nav_is_active("plan", ["review", "review_hub"]) is False

    def test_extra_condition_false_short_circuits(self):
        # route 命中但附加条件不成立（如语言项语言不匹配）→ 必须 False
        assert components.nav_is_active("english", {"english"}, extra_condition=False) is False

    def test_extra_condition_default_true(self):
        assert components.nav_is_active("home", {"home"}) is True

    def test_empty_routes(self):
        assert components.nav_is_active("home", set()) is False
        assert components.nav_is_active("home", []) is False


class TestNavButton:
    @staticmethod
    def _fake_st(called):
        def fake_button(label, key=None, use_container_width=None, type=None):
            called.update(label=label, key=key, type=type, width=use_container_width)
            return called.get("clicked", False)
        return types.SimpleNamespace(button=fake_button)

    def test_active_uses_primary_and_fires_callback(self, monkeypatch):
        called = {"clicked": True}
        fired = []
        monkeypatch.setattr(components, "st", self._fake_st(called))
        components.nav_button("首页", key="nav-home", active=True,
                              on_activate=lambda: fired.append("go"))
        assert called["type"] == "primary"
        assert called["key"] == "nav-home"
        assert called["width"] is True
        assert fired == ["go"]

    def test_inactive_uses_secondary_and_fires_callback(self, monkeypatch):
        called = {"clicked": True}
        fired = []
        monkeypatch.setattr(components, "st", self._fake_st(called))
        components.nav_button("诊断", key="nav-diag", active=False,
                              on_activate=lambda: fired.append("go"))
        assert called["type"] == "secondary"
        assert fired == ["go"]

    def test_not_clicked_does_not_fire(self, monkeypatch):
        called = {"clicked": False}
        fired = []
        monkeypatch.setattr(components, "st", self._fake_st(called))
        components.nav_button("首页", key="nav-home", active=True,
                              on_activate=lambda: fired.append("go"))
        assert called["type"] == "primary"
        assert fired == []
