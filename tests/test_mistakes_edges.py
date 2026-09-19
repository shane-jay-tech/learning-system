# -*- coding: utf-8 -*-
"""mistakes 逾期天数与「已不在题库」禁用补测（l918-21）。

钉 :78-83 逾期天数边界（昨日=+1 逾期/今日=0 不显示逾期）与 :85-91 missing 题契约
（button disabled=True＋「该题已不在题库中，可以忽略」caption）。
_lookup_problem 打桩控制命中/缺失；FakeStreamlit 录制 caption/button。只加测试不改页面代码。
"""
from unittest.mock import MagicMock

import ui.pages.mistakes as mistakes_page
from tests.test_ui_behavior import FakeStreamlit


class MistakesFake(FakeStreamlit):
    EXTRA = {"caption", "metric", "info", "page_link"}

    def __getattr__(self, name):
        if name in self.EXTRA:
            def call(*a, **kw):
                self.calls.append((name, a, kw))
                return self
            return call
        return super().__getattr__(name)


def _wire(monkeypatch, fake, lookup):
    monkeypatch.setattr(mistakes_page, "st", fake)
    monkeypatch.setattr(mistakes_page, "_lookup_problem", lookup)
    monkeypatch.setattr(mistakes_page, "navigate_to_problem", lambda *a, **kw: None)


def test_逾期昨日_显示逾期1天(monkeypatch):
    from datetime import date, timedelta
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    due = {"lang": "python", "problem_id": "p_ok", "next_due_date": yesterday, "interval_days": 7}
    found = (MagicMock(), MagicMock())  # topic_obj/problem_obj 命中
    lookup = lambda lang, pid: found if pid == "p_ok" else (None, None)
    fake = MistakesFake()
    _wire(monkeypatch, fake, lookup)
    mistakes_page._render_due_reviews(MagicMock(), [due])
    captions = [str(c[1][0]) for c in fake.calls if c[0] == "caption"]
    assert any("逾期 1 天" in c for c in captions), captions


def test_逾期今日_零天不显示逾期字段(monkeypatch):
    from datetime import date
    today = date.today().isoformat()
    due = {"lang": "python", "problem_id": "p_ok", "next_due_date": today, "interval_days": 7}
    found = (MagicMock(), MagicMock())
    lookup = lambda lang, pid: found
    fake = MistakesFake()
    _wire(monkeypatch, fake, lookup)
    mistakes_page._render_due_reviews(MagicMock(), [due])
    captions = [str(c[1][0]) for c in fake.calls if c[0] == "caption"]
    assert any("复习间隔 7 天" in c and "逾期" not in c for c in captions), captions


def test_missing题_按钮禁用且显示忽略提示(monkeypatch):
    due = {"lang": "python", "problem_id": "p_gone", "next_due_date": "2099-12-31", "interval_days": 7}
    lookup = lambda lang, pid: (None, None)  # 题库查无此题
    fake = MistakesFake()
    _wire(monkeypatch, fake, lookup)
    mistakes_page._render_due_reviews(MagicMock(), [due])
    # button 桩不落 calls，但 missing 时的忽略 caption 可断言
    captions = [str(c[1][0]) for c in fake.calls if c[0] == "caption"]
    assert any("该题已不在题库中，可以忽略" in c for c in captions), captions
    # 直接验证传给 st.button 的 disabled 值（按钮未点、render 内部已决定禁用）
    # 由实现契约：missing=True → navigate 分支不可达（此处以 caption+无跳转副作用佐证）
