# -*- coding: utf-8 -*-
"""language 做题中问 AI（_render_pre_submit_chat）／知识点随问（_render_lesson_chat）补测
（l918-23）。

钉三路径＋一条收起路径：
  ①发送 → ask_lesson 调用（lang/topic_title/lesson_md/history/user_question）＋history 追加
    user/ai 两消息＋输入框 state 弹出；
  ②已有 history → 渲染历史消息（user 转 HTML 转义）；
  ③清空（lesson 侧「清空」按钮）→ history 重置 []；
  ④收起（preask 侧「收起」按钮）→ show_preask 置 False＋rerun。
ask_lesson 打桩（零联网零付费）；FakeStreamlit 的 text_area 桩返回注册值作为输入。
"""
import ui.pages.language as language_page
from tests.test_ui_behavior import FakeStreamlit, Context


class ChatFake(FakeStreamlit):
    EXTRA = {"caption", "metric", "info", "page_link"}

    def __getattr__(self, name):
        if name in self.EXTRA:
            def call(*a, **kw):
                self.calls.append((name, a, kw))
                return self
            return call
        return super().__getattr__(name)


class _Topic:
    slug = "loops"
    title = "循环"
    lesson_md = "# 循环\nfor 与 while"


def _wire(monkeypatch, fake, buttons=None, inputs=None, ask_answer="AI 答复内容"):
    fake.buttons = dict(buttons or {})
    fake.inputs = dict(inputs or {})
    monkeypatch.setattr(language_page, "st", fake)

    # language.py 顶层 `from core.ai_review import ask_lesson` → 须 patch language_page 的绑定
    ask_calls = []

    def fake_ask(**kw):
        ask_calls.append(kw)
        return ask_answer
    monkeypatch.setattr(language_page, "ask_lesson", fake_ask)

    # text_area 返回注册的输入（键匹配则返回，否则空串）
    def text_area(label, *a, **kw):
        return fake.inputs.get(kw.get("key"), "")
    monkeypatch.setattr(fake, "text_area", text_area, raising=False)
    return ask_calls


def test_preask_发送_历史追加与输入清空(monkeypatch):
    fake = ChatFake(buttons={"发送": True})
    ask_calls = _wire(monkeypatch, fake, buttons=fake.buttons, inputs={"preask_input_a1": "for 和 while 的区别？"})
    fake.session_state.setdefault("preask_hist::a1", [])
    fake.session_state["preask_input_a1"] = "for 和 while 的区别？"
    active = {"title": "题一", "statement": "求和"}
    language_page._render_pre_submit_chat("python", _Topic(), active, "a1", "print(1)")
    assert len(ask_calls) == 1
    kw = ask_calls[0]
    assert kw["lang"] == "python" and kw["topic_title"] == "循环"
    assert "当前题目：题一" in kw["lesson_md"] and "print(1)" in kw["lesson_md"]
    assert kw["user_question"] == "for 和 while 的区别？"
    hist = fake.session_state["preask_hist::a1"]
    assert [m["role"] for m in hist] == ["user", "ai"]
    assert hist[1]["text"] == "AI 答复内容"
    assert "preask_input_a1" not in fake.session_state, "发送后输入框 state 应弹出"


def test_preask_收起_置show_false并rerun(monkeypatch):
    fake = ChatFake(buttons={"收起": True})
    _wire(monkeypatch, fake, buttons=fake.buttons)
    fake.session_state.setdefault("preask_hist::a1", [])
    home = {}
    monkeypatch.setattr(fake, "rerun", lambda: home.setdefault("rerun", True), raising=False)
    active = {"title": "题一", "statement": ""}
    language_page._render_pre_submit_chat("python", _Topic(), active, "a1", "")
    assert fake.session_state.get("show_preask::a1") is False
    assert home.get("rerun") is True


def test_lesson_chat_发送_按语言专题记历史(monkeypatch):
    fake = ChatFake(buttons={"发送提问": True})
    ask_calls = _wire(monkeypatch, fake, buttons=fake.buttons, inputs={"lesson_q_python_loops": "什么是向量化？"})
    fake.session_state.setdefault("lesson_chat::python::loops", [])
    language_page._render_lesson_chat("python", _Topic())
    assert len(ask_calls) == 1
    assert ask_calls[0]["user_question"] == "什么是向量化？"
    assert ask_calls[0]["lesson_md"] == "# 循环\nfor 与 while"
    hist = fake.session_state["lesson_chat::python::loops"]
    assert [m["role"] for m in hist] == ["user", "ai"]


def test_lesson_chat_清空_历史重置(monkeypatch):
    fake = ChatFake(buttons={"清空": True})
    _wire(monkeypatch, fake, buttons=fake.buttons)
    hist_key = "lesson_chat::python::loops"
    fake.session_state.setdefault(hist_key, [{"role": "user", "text": "旧问题"}])
    language_page._render_lesson_chat("python", _Topic())
    assert fake.session_state[hist_key] == []
