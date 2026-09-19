# -*- coding: utf-8 -*-
"""home _render_next_action 三区补测（l918-18）。

现有测试整体 monkeypatch 掉 _render_next_action（test_ui_behavior.py:395），三分支零覆盖：
  ①新手区（grand_solved=0）：诊断引导＋「做学习诊断」按钮置 route=diagnostic；
  ②继续学习区 plan 空：「当前课程已全部完成」；
  ③无复习（due+mistakes=0）：「今天没有待复习任务 ✓」；
  ④三区正常态：推荐卡＋复习计数＋进展聚合。
基类 FakeStreamlit 的 button 桩只按 label 返回值不落 calls → 按钮断言走
buttons={label: True}＋副作用（route/navigate）。只加测试不改页面代码。
"""
from unittest.mock import MagicMock

import ui.pages.home as home_page
from tests.test_ui_behavior import FakeStreamlit


class HomeFake(FakeStreamlit):
    EXTRA = {"caption", "metric", "download_button", "page_link", "text_input",
             "number_input", "selectbox", "multiselect", "checkbox", "slider",
             "text_area", "date_input", "toast", "balloons", "file_uploader",
             "image", "table", "bar_chart", "plotly_chart", "altair_chart"}

    def __getattr__(self, name):
        if name in self.EXTRA:
            def call(*a, **kw):
                self.calls.append((name, a, kw))
                return self
            return call
        return super().__getattr__(name)


def _dao(due=0, mistakes=0, streak=5):
    dao = MagicMock()
    dao.get_due_reviews.return_value = [{"id": i} for i in range(due)]
    dao.list_mistakes.return_value = [{"id": i} for i in range(mistakes)]
    dao.daily_streak.return_value = streak
    return dao


def _patch_st(monkeypatch, fake):
    monkeypatch.setattr(home_page, "st", fake)


def test_新手区_grand_solved_0_诊断按钮置route(monkeypatch):
    fake = HomeFake(buttons={"做学习诊断": True})
    _patch_st(monkeypatch, fake)
    home_page._render_next_action(_dao(), grand_solved=0)
    markdowns = [str(c[1][0]) for c in fake.calls if c[0] == "markdown"]
    assert any("学习诊断" in m and "第一次来" in m for m in markdowns), "新手区应显示诊断引导"
    assert fake.session_state["route"] == "diagnostic", "「做学习诊断」按钮应置 route"


def test_新手区_直接开始python_走navigate(monkeypatch):
    fake = HomeFake(buttons={"直接开始 Python": True})
    _patch_st(monkeypatch, fake)
    navigated = []
    monkeypatch.setattr(home_page, "navigate_to_problem", lambda *a, **kw: navigated.append(a))
    home_page._render_next_action(_dao(), grand_solved=0)
    assert navigated and navigated[0][0] == "python", "「直接开始 Python」应导航 python"


def test_继续学习区_plan空_显示全部完成(monkeypatch):
    fake = HomeFake()
    _patch_st(monkeypatch, fake)
    monkeypatch.setattr(home_page, "recommend", lambda n=1, dao=None: [])
    import core.achievements as ach
    monkeypatch.setattr(ach, "get_progress_summary", lambda dao: {"earned": 0, "total": 22})
    home_page._render_next_action(_dao(), grand_solved=10)
    markdowns = [str(c[1][0]) for c in fake.calls if c[0] == "markdown"]
    assert any("当前课程已全部完成" in m for m in markdowns)


def test_复习区_全零显示无任务_非零显示计数(monkeypatch):
    # 全零
    fake = HomeFake()
    _patch_st(monkeypatch, fake)
    monkeypatch.setattr(home_page, "recommend", lambda n=1, dao=None: [])
    import core.achievements as ach
    monkeypatch.setattr(ach, "get_progress_summary", lambda dao: {"earned": 0, "total": 22})
    home_page._render_next_action(_dao(due=0, mistakes=0), grand_solved=10)
    captions = [str(c[1][0]) for c in fake.calls if c[0] == "caption"]
    assert any("今天没有待复习任务" in c for c in captions)
    # 非零：due 3 + mistakes 2 = 5
    fake2 = HomeFake()
    _patch_st(monkeypatch, fake2)
    home_page._render_next_action(_dao(due=3, mistakes=2), grand_solved=10)
    markdowns = [str(c[1][0]) for c in fake2.calls if c[0] == "markdown"]
    assert any("5** 题待复习" in m for m in markdowns), "Zone2 计数=due3+mistakes2"
    caps = [str(c[1][0]) for c in fake2.calls if c[0] == "caption"]
    assert any("错题 2" in c and "到期 3" in c for c in caps)


def test_三区正常态_推荐卡与进展聚合(monkeypatch):
    fake = HomeFake()
    _patch_st(monkeypatch, fake)
    plan = [{"lang": "python", "problem_id": "p1", "title": "两数之和", "difficulty": 2,
             "topic_slug": "loops", "reason": "薄弱"}]
    monkeypatch.setattr(home_page, "recommend", lambda n=1, dao=None: plan)
    import core.achievements as ach
    monkeypatch.setattr(ach, "get_progress_summary", lambda dao: {"earned": 6, "total": 22})
    home_page._render_next_action(_dao(streak=5), grand_solved=10)
    markdowns = [str(c[1][0]) for c in fake.calls if c[0] == "markdown"]
    assert any("两数之和" in m and "难度 2" in m for m in markdowns), "Zone1 应渲染推荐卡"
    assert any("连续 **5** 天" in m for m in markdowns), "streak>=3 显示「连续」"
    assert any("6/22 项成就" in m for m in markdowns)
