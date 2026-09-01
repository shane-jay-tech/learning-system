import importlib
from contextlib import nullcontext
from datetime import date
from types import SimpleNamespace

import pytest

import app
import ui.components as components
import ui.pages.dashboard as dashboard_page
import ui.pages.diagnostic as diagnostic_page
import ui.pages.home as home_page
import ui.pages.language as language_page
import ui.pages.mistakes as mistakes_page
import ui.pages.path as path_page
import ui.styles as styles
from core.paths import LearningPath, Milestone


class State(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


class Context:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeStreamlit:
    def __init__(self, buttons=None):
        self.session_state = State()
        self.buttons = buttons or {}
        self.calls = []
        self.sidebar = Context()
        self.rerun_count = 0

    def __getattr__(self, name):
        if name in {"container", "expander", "spinner"}:
            return lambda *a, **kw: Context()
        if name == "columns":
            return lambda spec, *a, **kw: [Context() for _ in range(spec if isinstance(spec, int) else len(spec))]
        if name == "tabs":
            return lambda labels: [Context() for _ in labels]
        if name == "button":
            return lambda label, *a, **kw: self.buttons.get(label, False)
        if name == "radio":
            return lambda label, options, *a, **kw: options[0]
        if name == "text_area":
            return lambda label, value="", *a, **kw: value
        if name == "progress":
            return lambda *a, **kw: self.calls.append((name, a, kw))
        if name in {
            "markdown", "caption", "success", "warning", "info", "error", "code",
            "set_page_config", "download_button", "metric", "line_chart", "dataframe",
        }:
            return lambda *a, **kw: self.calls.append((name, a, kw))
        raise AttributeError(name)

    def rerun(self):
        self.rerun_count += 1


def test_navigation_and_language_helpers(monkeypatch):
    fake = FakeStreamlit()
    fake.session_state["last_judge_result"] = "old"
    monkeypatch.setattr(components, "st", fake)
    components.navigate_to_problem("python", "loops", "p1")
    assert fake.session_state.route == "language"
    assert fake.session_state.selected_lang == "python"
    assert fake.session_state.selection == {"lang": "python", "topic_slug": "loops", "problem_id": "p1"}
    assert "last_judge_result" not in fake.session_state
    assert fake.rerun_count == 1

    assert components.code_highlight_lang("cpp") == "cpp"
    assert components.code_highlight_lang("agent_dev") == "python"
    assert components.code_highlight_lang("unknown") == "text"


def test_component_html_escapes_user_content_and_renders_states(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(components, "st", fake)
    components.hero("<title>", "a & b")
    assert "&lt;title&gt;" in fake.calls[-1][1][0]
    assert "a &amp; b" in fake.calls[-1][1][0]

    card = components.lang_card_html("python", total=4, solved=1, wrong=2)
    assert "25%" in card
    assert "Python" in card
    assert "0%" in components.lang_card_html("python", total=0, solved=0, wrong=0)
    assert "&lt;x&gt;" in components.metric_tile(1, "<x>")

    components.section_title("<section>")
    components.lesson_box("**lesson**")
    components.verdict_banner(True, 12)
    components.verdict_banner(False)
    components.io_block("<script>", kind="expected")
    components.ai_feedback_block("")
    components.ai_feedback_block("**feedback**")
    components.stderr_block("<bad>")
    joined = "\n".join(str(call) for call in fake.calls)
    assert "&lt;script&gt;" in joined
    assert "&lt;bad&gt;" in joined


def test_code_editor_ace_and_fallback(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(components, "st", fake)
    # 惰性加载已发生：直接用假 st_ace 验证编辑器参数透传
    monkeypatch.setattr(components, "_ACE_LOADED", True)
    monkeypatch.setattr(components, "_HAS_ACE", True)
    monkeypatch.setattr(components, "st_ace", lambda **kw: f"ace:{kw['language']}:{kw['value']}")
    assert components.code_editor("x", "python", "k") == "ace:python:x"

    monkeypatch.setattr(components, "_HAS_ACE", False)
    assert components.code_editor("fallback", "unknown", "k") == "fallback"


def test_styles_injects_css(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(styles, "st", fake)
    styles.inject()
    assert fake.calls and fake.calls[0][0] == "markdown"
    assert "<style>" in fake.calls[0][1][0]


def _milestone(mid, topics=None, prereqs=None):
    return Milestone(mid, mid.title(), "desc", topics or [], 1.0, prereqs=prereqs or [])


def _path(milestones):
    return LearningPath("path", "Path", "subtitle", "icon", 2.0, milestones)


def test_path_problem_lookup_prereqs_progress_and_event_dedup(monkeypatch):
    topic = SimpleNamespace(slug="loops", problems=[SimpleNamespace(id="p1"), SimpleNamespace(id="p2")])
    monkeypatch.setattr(path_page, "_cached_load_language", lambda lang: [topic])
    milestone = _milestone("m1", ["python/loops", "sql/missing"])
    assert path_page._get_milestone_problems(milestone) == [
        {"lang": "python", "problem_id": "p1"},
        {"lang": "python", "problem_id": "p2"},
    ]

    monkeypatch.setattr(path_page, "_cached_load_language", lambda lang: (_ for _ in ()).throw(OSError()))
    assert path_page._get_milestone_problems(milestone) == []

    first = _milestone("first")
    second = _milestone("second", prereqs=["first"])
    learning_path = _path([first, second])

    class DAO:
        def __init__(self):
            self.meta = {}
            self.events = []

        def milestone_progress(self, problems):
            return {"total": len(problems), "solved": len(problems), "pct": 1.0 if problems else 0.0}

        def get_meta(self, key):
            return self.meta.get(key)

        def set_meta(self, key, value):
            self.meta[key] = value

        def emit_event(self, event_type, **kwargs):
            self.events.append((event_type, kwargs))

    dao = DAO()
    monkeypatch.setattr(path_page, "_get_milestone_problems", lambda milestone: [{"lang": "python", "problem_id": milestone.id}])
    assert path_page._check_prereqs(learning_path, second, dao)
    assert path_page._path_overall_progress(learning_path, dao) == (2, 2)

    path_page._emit_path_started(dao, "path")
    path_page._emit_path_started(dao, "path")
    path_page._emit_milestone_completed(dao, "path", "first")
    path_page._emit_milestone_completed(dao, "path", "first")
    assert [e[0] for e in dao.events] == ["path_started", "path_milestone_completed"]


def test_path_prerequisite_failure(monkeypatch):
    first = _milestone("first")
    second = _milestone("second", prereqs=["first", "missing"])
    learning_path = _path([first, second])
    monkeypatch.setattr(path_page, "_get_milestone_problems", lambda milestone: [{"lang": "python", "problem_id": "p"}])
    dao = SimpleNamespace(milestone_progress=lambda problems: {"pct": 0.5})
    assert not path_page._check_prereqs(learning_path, second, dao)
    assert path_page._check_prereqs(learning_path, first, dao)


def test_dashboard_helpers_zero_fill_and_streak_badges():
    today = date.today().isoformat()
    series, passed = dashboard_page._build_chart_data([{"date": today, "attempts": 3, "passed": 2}], days=3)
    assert len(series) == 3
    assert series[today] == 3
    assert passed[today] == 2
    assert "🔥" in dashboard_page._streak_html(3)
    assert "⭐" in dashboard_page._streak_html(1)
    assert "·" in dashboard_page._streak_html(0)
    rec_id = dashboard_page._make_rec_id("dashboard", "review_due", "python", "topic/p1", 2)
    assert rec_id.endswith("dashboard_review_due_python_p1_2")


def test_home_pulse_events(monkeypatch):
    milestone = SimpleNamespace(id="m1", title="First")
    path = SimpleNamespace(id="p", milestones=[milestone])
    monkeypatch.setattr("core.paths.load_all_paths", lambda: [path])
    monkeypatch.setattr(path_page, "_get_milestone_problems", lambda m: [{"lang": "python", "problem_id": "x"}])

    class DAO:
        def __init__(self, complete=True, streak=0, mistakes=None, total=0):
            self.complete = complete
            self.streak = streak
            self.mistakes = [1] if mistakes is None else mistakes
            self.total = total
            self.meta = {}

        def milestone_progress(self, problems):
            return {"pct": 1.0 if self.complete else 0.0, "total": 1}

        def get_meta_ts(self, key):
            return self.meta.get(key)

        def set_meta(self, key, value):
            self.meta[key] = value

        def daily_streak(self):
            return self.streak

        def list_mistakes(self):
            return self.mistakes

        def summary_by_lang(self):
            return {"python": {"total": self.total}}

    assert "里程碑" in home_page._detect_pulse_event(DAO(), 0)
    assert "欢迎回来" in home_page._detect_pulse_event(DAO(complete=False, streak=1), 14)
    assert "错题全部清空" in home_page._detect_pulse_event(DAO(complete=False, mistakes=[], total=10), 0)
    assert home_page._detect_pulse_event(DAO(complete=False, mistakes=[], total=2), 0) == ""


def test_problem_state_lru_prunes_old_problems(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(language_page, "st", fake)
    # 访问 40 道题，每道题留下一堆状态 key
    for i in range(40):
        pid = f"python/topic/p{i}"
        fake.session_state[f"code::{pid}"] = "x"
        fake.session_state[f"chat_history::{pid}"] = ["old"]
        fake.session_state[f"editor_{pid}_0"] = "x"
        language_page._touch_problem(pid)
    # 旧题（前 10 道）状态被回收
    for i in range(10):
        pid = f"python/topic/p{i}"
        assert f"code::{pid}" not in fake.session_state
        assert f"editor_{pid}_0" not in fake.session_state
    # 最近 30 道题状态保留
    for i in range(10, 40):
        pid = f"python/topic/p{i}"
        assert fake.session_state[f"code::{pid}"] == "x"
    # LRU 队列自身有界
    assert len(fake.session_state["_problem_lru"]) == language_page._LRU_CAP
    # AI 变式题不参与 LRU
    fake2 = FakeStreamlit()
    monkeypatch.setattr(language_page, "st", fake2)
    language_page._touch_problem("AI_VARIANT::python/topic/p0")
    assert "_problem_lru" not in fake2.session_state


def test_language_state_and_active_variant(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(language_page, "st", fake)
    language_page._ensure_state()
    assert fake.session_state.selected_topic_idx == 0
    assert fake.session_state.ai_variants == {}
    assert language_page._problem_key("p1") == "code::p1"

    problem = SimpleNamespace(id="p1", to_dict=lambda: {"id": "p1", "base": True})
    assert language_page._active_problem(problem) == ({"id": "p1", "base": True}, False)
    fake.session_state.ai_variants = {"p1": {"id": "variant"}}
    assert language_page._active_problem(problem) == ({"id": "variant"}, True)


def test_mistakes_empty_and_ungroupable_states(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(mistakes_page, "st", fake)
    dao = SimpleNamespace(list_mistakes=lambda: [], get_due_reviews=lambda limit: [])
    mistakes_page._render_mistakes_body(dao)
    assert any(call[0] == "success" for call in fake.calls)

    monkeypatch.setattr(mistakes_page, "section_title", lambda *a, **kw: None)
    monkeypatch.setattr(mistakes_page, "find_problem", lambda *a, **kw: (None, None))
    mistakes_page._render_weak_topics(dao, [{"lang": "python", "problem_id": "missing"}])
    assert any(call[0] == "info" for call in fake.calls)


@pytest.mark.parametrize(
    ("route", "module_name", "function_name"),
    [
        ("home", "ui.pages.home", "render_home"),
        ("paths", "ui.pages.path", "render_path_list"),
        ("path_detail", "ui.pages.path", "render_path_detail"),
        ("language", "ui.pages.language", "render_language"),
        ("mistakes", "ui.pages.mistakes", "render_mistakes"),
        ("diagnostic", "ui.pages.diagnostic", "render_diagnostic"),
        ("dashboard", "ui.pages.dashboard", "render_dashboard"),
    ],
)
def test_app_routes_to_expected_page(monkeypatch, route, module_name, function_name):
    fake = FakeStreamlit()
    fake.session_state.route = route
    called = []
    module = importlib.import_module(module_name)
    monkeypatch.setattr(module, function_name, lambda: called.append(route))
    monkeypatch.setattr(app, "st", fake)
    monkeypatch.setattr(app, "inject_css", lambda: None)
    app.main()
    assert called == [route]


def test_app_initial_state_sidebar_and_unknown_route(monkeypatch):
    fake = FakeStreamlit(buttons={"📊 学习面板": True})
    monkeypatch.setattr(app, "st", fake)
    monkeypatch.setattr(app, "navigate_to_problem", lambda lang: None)
    app._init_state()
    assert fake.session_state.route == "home"
    app._sidebar()
    assert fake.session_state.route == "dashboard"
    assert fake.rerun_count == 1

    fake = FakeStreamlit()
    fake.session_state.route = "unknown"
    monkeypatch.setattr(app, "st", fake)
    monkeypatch.setattr(app, "inject_css", lambda: None)
    app.main()
    assert any(call[0] == "error" and "未知路由" in call[1][0] for call in fake.calls)


def test_diagnostic_skip_uses_global_route_key(monkeypatch):
    fake = FakeStreamlit(buttons={"跳过诊断": True})
    monkeypatch.setattr(diagnostic_page, "st", fake)
    diagnostic_page._render_quiz(SimpleNamespace())
    assert fake.session_state.route == "paths"


def test_diagnostic_wrapper_and_result_render(monkeypatch):
    fake = FakeStreamlit()
    original_render_result = diagnostic_page._render_result
    monkeypatch.setattr(diagnostic_page, "st", fake)
    monkeypatch.setattr(diagnostic_page, "hero", lambda *a, **kw: None)

    class DAO:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    dao = DAO()
    monkeypatch.setattr(diagnostic_page, "ProgressDAO", lambda: dao)
    monkeypatch.setattr(diagnostic_page, "get_diagnostic_result", lambda d: {"saved": True})
    rendered = []
    monkeypatch.setattr(diagnostic_page, "_render_result", lambda result, d: rendered.append((result, d)))
    diagnostic_page.render_diagnostic()
    assert rendered and dao.closed

    result = {
        "total_correct": 4,
        "total_questions": 6,
        "recommendation": {"message": "start here", "path": "agent_mastery"},
    }
    original_render_result(result, dao)
    assert any(call[0] == "success" and "4/6" in call[1][0] for call in fake.calls)


def test_home_wrapper_security_notice_and_body(monkeypatch):
    fake = FakeStreamlit(buttons={"我知道了，不再提示": True})
    monkeypatch.setattr(home_page, "st", fake)
    monkeypatch.setattr(home_page, "hero", lambda *a, **kw: None)
    monkeypatch.setattr(home_page, "section_title", lambda *a, **kw: None)
    monkeypatch.setattr(home_page, "metric_tile", lambda n, label: f"{label}:{n}")
    monkeypatch.setattr(home_page, "lang_card_html", lambda *a, **kw: "card")
    monkeypatch.setattr(home_page, "_render_next_action", lambda *a, **kw: None)
    monkeypatch.setattr(home_page, "_render_path_cards", lambda: None)
    monkeypatch.setattr(home_page, "_render_ai_pulse", lambda dao: None)
    monkeypatch.setattr(home_page, "_load_totals", lambda: {lang: (0 if lang == "r" else 2) for lang in components.ALL_LANGS})
    monkeypatch.setattr("core.config.is_public_deploy", lambda: False)

    class DAO:
        def __init__(self):
            self.meta = {}
            self.closed = False

        def get_meta_ts(self, key):
            return self.meta.get(key)

        def set_meta(self, key, value):
            self.meta[key] = value

        def summary_by_lang(self):
            return {"python": {"total": 2, "solved": 1, "wrong": 1}}

        def list_mistakes(self):
            return [{"problem_id": "p1"}]

        def close(self):
            self.closed = True

    dao = DAO()
    home_page._render_security_notice(dao)
    assert dao.meta["security_notice_seen"] == "done"
    home_page._render_home_body(dao)
    assert any(call[0] == "warning" and "1 道错题" in call[1][0] for call in fake.calls)

    monkeypatch.setattr(home_page, "ProgressDAO", lambda: dao)
    monkeypatch.setattr(home_page, "_render_home_body", lambda d: None)
    home_page.render_home()
    assert dao.closed

    public_fake = FakeStreamlit()
    monkeypatch.setattr(home_page, "st", public_fake)
    monkeypatch.setattr("core.config.is_public_deploy", lambda: True)
    home_page._render_security_notice(dao)
    assert any(call[0] == "error" for call in public_fake.calls)


def test_language_render_guardrails_and_selection(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(language_page, "st", fake)
    language_page.render_language()
    assert any(call[0] == "warning" for call in fake.calls)

    fake.session_state.selected_lang = "unknown"
    language_page.render_language()
    assert any(call[0] == "error" and "未知语言" in call[1][0] for call in fake.calls)

    fake.session_state.selected_lang = "python"
    monkeypatch.setattr(language_page, "load_language", lambda lang: [])
    language_page.render_language()
    assert any(call[0] == "error" and "题库内容" in call[1][0] for call in fake.calls)

    p1, p2 = SimpleNamespace(id="p1"), SimpleNamespace(id="p2")
    topics = [SimpleNamespace(slug="first", problems=[p1]), SimpleNamespace(slug="target", problems=[p1, p2])]
    fake.session_state.selection = {"lang": "python", "topic_slug": "target", "problem_id": "p2"}
    fake.session_state.selected_topic_idx = 99
    fake.session_state.selected_problem_idx = 99
    monkeypatch.setattr(language_page, "load_language", lambda lang: topics)
    monkeypatch.setattr(language_page, "hero", lambda *a, **kw: None)
    rendered = []
    monkeypatch.setattr(language_page, "_render_body", lambda lang, topics, topic, dao: rendered.append((lang, topic.slug)))
    dao = SimpleNamespace(close=lambda: rendered.append(("closed", "")))
    monkeypatch.setattr(language_page, "ProgressDAO", lambda: dao)
    language_page.render_language()
    assert rendered[0] == ("python", "target")
    assert fake.session_state.selected_problem_idx == 1

    empty_topic = [SimpleNamespace(slug="empty", problems=[])]
    monkeypatch.setattr(language_page, "load_language", lambda lang: empty_topic)
    fake.session_state.selected_topic_idx = 0
    language_page.render_language()
    assert any(call[0] == "warning" and "暂无题目" in call[1][0] for call in fake.calls)


def test_path_page_rendering_branches(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(path_page, "st", fake)
    monkeypatch.setattr(path_page, "hero", lambda *a, **kw: None)
    monkeypatch.setattr(path_page, "load_all_paths", lambda: [])
    path_page.render_path_list()
    assert any(call[0] == "warning" and "暂无学习路径" in call[1][0] for call in fake.calls)

    milestone = _milestone("m1", ["python/loops"])
    learning_path = _path([milestone])

    class DAO:
        def __init__(self):
            self.closed = False

        def milestone_progress(self, problems):
            return {"total": 1, "solved": 1, "pct": 1.0}

        def close(self):
            self.closed = True

    dao = DAO()
    monkeypatch.setattr(path_page, "load_all_paths", lambda: [learning_path])
    monkeypatch.setattr(path_page, "ProgressDAO", lambda: dao)
    monkeypatch.setattr(path_page, "_render_diagnostic_prompt", lambda d: None)
    cards = []
    monkeypatch.setattr(path_page, "_render_path_card", lambda p, d: cards.append(p.id))
    path_page.render_path_list()
    assert cards == ["path"] and dao.closed

    fake.session_state.clear()
    path_page.render_path_detail()
    assert fake.session_state.route == "paths"
    fake.session_state.selected_path_id = "missing"
    monkeypatch.setattr(path_page, "load_path", lambda pid: None)
    path_page.render_path_detail()
    assert any(call[0] == "error" and "不存在" in call[1][0] for call in fake.calls)

    fake.session_state.selected_path_id = "path"
    monkeypatch.setattr(path_page, "load_path", lambda pid: learning_path)
    monkeypatch.setattr(path_page, "_emit_path_started", lambda *a: None)
    rendered = []
    monkeypatch.setattr(path_page, "_render_milestone", lambda p, m, i, d: rendered.append((m.id, i)))
    path_page.render_path_detail()
    assert rendered == [("m1", 0)]


def test_path_prompt_card_and_milestone_render(monkeypatch):
    fake = FakeStreamlit(buttons={"开始诊断": True})
    monkeypatch.setattr(path_page, "st", fake)
    monkeypatch.setattr("core.diagnostic.get_diagnostic_result", lambda dao: None)
    path_page._render_diagnostic_prompt(SimpleNamespace())
    assert fake.session_state.route == "diagnostic"

    monkeypatch.setattr("core.diagnostic.get_diagnostic_result", lambda dao: {"recommendation": {"message": "go"}})
    path_page._render_diagnostic_prompt(SimpleNamespace())
    assert any(call[0] == "success" and "go" in call[1][0] for call in fake.calls)

    monkeypatch.setattr(path_page, "_path_overall_progress", lambda path, dao: (2, 1))
    fake.buttons = {"进入 Path": True}
    path_page._render_path_card(_path([]), SimpleNamespace())
    assert fake.session_state.route == "path_detail"

    milestone = _milestone("m1", ["python/loops"])
    learning_path = _path([milestone])
    monkeypatch.setattr(path_page, "_get_milestone_problems", lambda m: [{"lang": "python", "problem_id": "p1"}])
    monkeypatch.setattr(path_page, "_check_prereqs", lambda *a: False)
    completed = []
    monkeypatch.setattr(path_page, "_emit_milestone_completed", lambda *a: completed.append(True))
    dao = SimpleNamespace(milestone_progress=lambda problems: {"total": 1, "solved": 1, "pct": 1.0})
    fake.buttons = {}
    path_page._render_milestone(learning_path, milestone, 0, dao)
    assert completed
    assert any(call[0] == "info" and "建议先完成" in call[1][0] for call in fake.calls)


def test_mistakes_wrapper_and_nonempty_tabs(monkeypatch):
    fake = FakeStreamlit()
    monkeypatch.setattr(mistakes_page, "st", fake)
    monkeypatch.setattr(mistakes_page, "hero", lambda *a, **kw: None)

    class DAO:
        def __init__(self):
            self.closed = False

        def list_mistakes(self):
            return [{"problem_id": "p1"}]

        def get_due_reviews(self, limit):
            return [{"problem_id": "p2"}]

        def close(self):
            self.closed = True

    dao = DAO()
    monkeypatch.setattr(mistakes_page, "ProgressDAO", lambda: dao)
    sections = []
    monkeypatch.setattr(mistakes_page, "_render_due_reviews", lambda d, rows: sections.append("due"))
    monkeypatch.setattr(mistakes_page, "_render_wrong_problems", lambda d, rows: sections.append("wrong"))
    monkeypatch.setattr(mistakes_page, "_render_weak_topics", lambda d, rows: sections.append("weak"))
    mistakes_page.render_mistakes()
    assert sections == ["due", "wrong", "weak"]
    assert dao.closed
