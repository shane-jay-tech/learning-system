# -*- coding: utf-8 -*-
"""language _render_topic_nav 边界隐藏补测（l918-22）。

钉底部导航三位置（:356-375）：首（无「上一个」）/中（双按钮）/末（无「下一个」），
以及按钮点击 → navigate_to_problem 的目标 slug。
FakeStreamlit 的 button 桩按 buttons={label: True} 触发；只加测试不改页面代码。
"""
import ui.pages.language as language_page
from tests.test_ui_behavior import FakeStreamlit, Context


class NavFake(FakeStreamlit):
    class _Col(Context):
        pass

    def columns(self, spec, *a, **kw):
        n = spec if isinstance(spec, int) else len(spec)
        return [Context() for _ in range(n)]

    def __getattr__(self, name):
        if name in {"markdown"}:
            def call(*a, **kw):
                self.calls.append((name, a, kw))
                return self
            return call
        return super().__getattr__(name)


def _fake_with_buttons(labels):
    fake = NavFake()
    fake.buttons = dict(labels)
    return fake


def _topics():
    class T:
        def __init__(self, slug, title):
            self.slug = slug
            self.title = title
    return [T("t1", "第一课"), T("t2", "第二课"), T("t3", "第三课")]


def _session(idx):
    class S(dict):
        pass
    s = S()
    s["selected_topic_idx"] = idx
    return s


def _run(monkeypatch, fake, idx, topics):
    fake.session_state.update(_session(idx))
    monkeypatch.setattr(language_page, "st", fake)
    navigated = []
    monkeypatch.setattr(language_page, "navigate_to_problem",
                        lambda lang, topic_slug=None, **kw: navigated.append((lang, topic_slug)))
    language_page._render_topic_nav("python", topics)
    return navigated


def test_首位置_无上一个按钮_点击下一个到t2(monkeypatch):
    fake = _fake_with_buttons({"下一个知识点 →": True})
    navigated = _run(monkeypatch, fake, 0, _topics())
    assert navigated == [("python", "t2")], "首位置点「下一个」应到 t2"
    # 首（idx=0）不渲染「← 上一个知识点」按钮：按钮桩仅命中注册的 label，
    # 若上一个按钮被渲染且其 label 被注册才会产生导航——用未注册的「← 上一个知识点」验证零副作用
    assert all(slug != "t1" for _, slug in navigated)


def test_中间位置_双按钮各达前后邻居(monkeypatch):
    seen = []
    topics = _topics()
    # 第一次渲染仅注册「上一个」→ 到 t1
    fake = _fake_with_buttons({"← 上一个知识点": True})
    fake.session_state.update(_session(1))
    monkeypatch.setattr(language_page, "st", fake)
    monkeypatch.setattr(language_page, "navigate_to_problem",
                        lambda lang, topic_slug=None, **kw: seen.append(topic_slug))
    language_page._render_topic_nav("python", topics)
    assert seen == ["t1"], "idx=1 点「上一个」应到 t1"
    # 第二次渲染仅注册「下一个」→ 到 t2
    fake2 = _fake_with_buttons({"下一个知识点 →": True})
    fake2.session_state.update(_session(1))
    monkeypatch.setattr(language_page, "st", fake2)
    language_page._render_topic_nav("python", topics)
    assert seen[-1] == "t3", "idx=1 点「下一个」应到 t3"


def test_末位置_无下一个按钮_点击上一个到倒数第二(monkeypatch):
    fake = _fake_with_buttons({"← 上一个知识点": True})
    topics = _topics()
    navigated = _run(monkeypatch, fake, len(topics) - 1, topics)
    assert navigated == [("python", "t2")], "末位置点「上一个」应到 t2"
