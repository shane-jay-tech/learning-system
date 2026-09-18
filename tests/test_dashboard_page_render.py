# -*- coding: utf-8 -*-
"""dashboard.py 渲染主路径补测（916p-a2 覆盖缺口：9% → 目标 ≥25%）。

复用 tests/test_ui_behavior.py 的 FakeStreamlit 桩（State/Context/组件录制），
DAO 用 MagicMock 兜底未知方法；不触真实 Streamlit，不改 ui/pages/dashboard.py。
可复跑：python -m pytest tests/test_dashboard_page_render.py -q
"""
from unittest.mock import MagicMock

import pytest

import ui.components as components
import ui.pages.dashboard as dashboard_page

import app  # noqa: F401  # app 侧 import 预绑定 st（与 test_ui_behavior 同桩模式）
from tests.test_ui_behavior import FakeStreamlit


def _dao():
    """MagicMock DAO：常用方法配真值；未知方法/上下文协议由 MagicMock 兜底。"""
    dao = MagicMock()
    dao.daily_streak.return_value = 3
    dao.summary_by_lang.return_value = {"python": {"attempts": 5, "solved": 4}}
    dao.total_attempts.return_value = 42
    dao.lang_attempt_counts.return_value = {"python": {"attempts": 30}, "sql": {"attempts": 12}}
    dao.attempts_by_day.return_value = [{"date": "2026-09-01", "attempts": 2, "passed": 1}]
    dao.recent_attempts.return_value = [
        {"id": 1, "lang": "python", "problem_id": "p1", "topic": "loops", "passed": 1, "created_at": "2026-09-01", "ts": "2026-09-01 12:00"}
    ]
    dao.all_problems_status.return_value = []
    dao.get_due_reviews.return_value = []
    dao.dimension_trends.return_value = [
        {"label": "逻辑推理", "avg": 72.0, "count": 4},
        {"label": "概念理解", "avg": 45.0, "count": 2},
    ]
    dao.recommendation_funnel.return_value = {"shown": 10, "clicked": 4, "completed": 2}
    dao.recommendation_funnel_by_reason.return_value = {}
    dao.review_health_stats.return_value = {
        "total_pool": 12, "total_due": 3, "high_risk": [],
        "buckets": {"1_3": 2, "4_7": 1, "7_plus": 0},
    }
    conn = MagicMock()
    conn.execute.return_value.fetchone.return_value = (6.5,)
    dao.conn = conn
    dao.get_meta.return_value = None
    dao.close.return_value = None
    return dao


class DashboardFakeStreamlit(FakeStreamlit):
    """扩展 FakeStreamlit：补 dashboard.py 用到而基类未录制的组件名（不改既有文件）。"""

    EXTRA = {"bar_chart", "plotly_chart", "altair_chart", "table", "image", "text_input",
             "number_input", "selectbox", "multiselect", "checkbox", "slider",
             "text_area", "date_input", "toast", "balloons", "file_uploader",
             "download_button", "page_link"}

    def __getattr__(self, name):
        if name in self.EXTRA:
            def call(*a, **kw):
                self.calls.append((name, a, kw))
                return self
            return call
        return super().__getattr__(name)


@pytest.fixture()
def fake_st(monkeypatch):
    fake = DashboardFakeStreamlit()
    monkeypatch.setattr(dashboard_page, "st", fake)
    monkeypatch.setattr(components, "st", fake)
    return fake


def test_render_dashboard_full_flow(fake_st, monkeypatch):
    """覆盖 :44-53 render_dashboard 入口＋:54-265 主渲染体（派生列/热力图/成就/推荐）。"""
    dao = _dao()
    monkeypatch.setattr(dashboard_page, "ProgressDAO", lambda: dao)
    monkeypatch.setattr(dashboard_page, "check_achievements", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_progress_summary", lambda dao: {"earned": 2, "total": 22})
    monkeypatch.setattr(dashboard_page, "get_all_with_state", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_achievement", lambda aid: {"name": f"成就{aid}"})
    monkeypatch.setattr(dashboard_page, "recommend", lambda n=5, dao=None: [])
    monkeypatch.setattr(dashboard_page, "cross_recommend", lambda dao, **kw: [])
    import core.loader as _loader
    monkeypatch.setattr(_loader, "load_language", lambda lang: [])
    dashboard_page.render_dashboard()
    assert any(c[0] in ("markdown", "header", "metric") for c in fake_st.calls)


def test_render_dashboard_body_smoke(fake_st, monkeypatch):
    """覆盖 :54-265 _render_dashboard_body 主路径（summary 汇总＋最近作答＋图表）。"""
    monkeypatch.setattr(dashboard_page, "check_achievements", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_progress_summary", lambda dao: {"earned": 2, "total": 22})
    monkeypatch.setattr(dashboard_page, "get_all_with_state", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_achievement", lambda aid: {"name": f"成就{aid}"})
    monkeypatch.setattr(dashboard_page, "recommend", lambda n=5, dao=None: [])
    monkeypatch.setattr(dashboard_page, "cross_recommend", lambda dao, **kw: [])
    import core.loader as _loader
    monkeypatch.setattr(_loader, "load_language", lambda lang: [])
    dashboard_page._render_dashboard_body(_dao())
    assert fake_st.calls


def test_render_cross_recommend(fake_st, monkeypatch):
    """覆盖 :273-325 跨路径推荐渲染（cross_recommend 打桩返回一条推荐 → 展示＋曝光事件）。"""
    recs = [{"lang": "sql", "problem_id": "p9", "title": "JOIN 入门", "topic": "joins",
             "topic_title": "连接查询", "difficulty": 3, "cross_reason": "互补内容"}]
    monkeypatch.setattr(dashboard_page, "cross_recommend", lambda dao, **kw: recs)
    dashboard_page._render_cross_recommend(_dao())
    assert any(c[0] == "markdown" for c in fake_st.calls)


def test_render_achievements(fake_st, monkeypatch):
    """覆盖 :326-376 成就渲染（领域函数打桩，零真实数据）。"""
    monkeypatch.setattr(dashboard_page, "check_achievements", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_progress_summary", lambda dao: {"earned": 2, "total": 22})
    monkeypatch.setattr(dashboard_page, "get_all_with_state", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_achievement", lambda aid: {"name": f"成就{aid}"})
    dashboard_page._render_achievements(_dao())
    assert fake_st.calls


def test_render_heatmap(fake_st):
    """覆盖 :377-436 热力图渲染。"""
    dashboard_page._render_heatmap(_dao())
    assert fake_st.calls


def test_render_recommendation_funnel(fake_st):
    """覆盖 :437-477 推荐漏斗渲染。"""
    dashboard_page._render_recommendation_funnel(_dao())
    assert fake_st.calls


def test_render_review_health(fake_st):
    """覆盖 :478-513 复习健康度渲染。"""
    dashboard_page._render_review_health(_dao())
    assert fake_st.calls


def test_render_rubric_trends(fake_st):
    """覆盖 :514-536 rubric 趋势渲染。"""
    dashboard_page._render_rubric_trends(_dao())
    assert fake_st.calls


# ---------------------------------------------------------------------------
# k918-04：:109-155 推荐计划渲染体补测（impression 记账/事件上报/空计划 info/按钮导航）
# ---------------------------------------------------------------------------

def _plan():
    return [
        {"lang": "python", "problem_id": "p1", "title": "两数之和", "difficulty": 2,
         "topic_title": "循环", "topic_slug": "loops", "reason_code": "weak_topic"},
        {"lang": "sql", "problem_id": "p9", "title": "联接入门", "difficulty": 3,
         "topic_title": "联接", "topic_slug": "joins", "reason_code": "due_review"},
    ]


def _wire_full_render(monkeypatch, dao, plan):
    monkeypatch.setattr(dashboard_page, "ProgressDAO", lambda: dao)
    monkeypatch.setattr(dashboard_page, "check_achievements", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_progress_summary", lambda dao: {"earned": 2, "total": 22})
    monkeypatch.setattr(dashboard_page, "recommend", lambda n=5, dao=None: plan)
    monkeypatch.setattr(dashboard_page, "cross_recommend", lambda n=3, dao=None: [])


def test_render_dashboard_recommend_plan_impressions_and_events(fake_st, monkeypatch):
    """:109-155 正常态：展示去重记账＋recommendation_shown 事件＋卡片渲染。"""
    dao = _dao()
    _wire_full_render(monkeypatch, dao, _plan())
    dashboard_page.render_dashboard()
    imps = fake_st.session_state["_rec_impressions"]
    assert len(imps) == 2, "两个推荐项都应写入 impression 记账"
    assert imps[("python", "p1", "dashboard")]["rank"] == 1
    assert imps[("sql", "p9", "dashboard")]["rank"] == 2
    assert imps[("python", "p1", "dashboard")]["recommendation_id"] == "20260919_dashboard_weak_topic_python_p1_1"
    shown = [c for c in dao.emit_event.call_args_list if c.args and c.args[0] == "recommendation_shown"]
    assert len(shown) == 2, "每个新展示项各上报一次 recommendation_shown"
    assert shown[0].kwargs["payload"]["surface"] == "dashboard"
    assert shown[0].kwargs["payload"]["reason_code"] == "weak_topic"


def test_render_dashboard_recommend_empty_plan_shows_info(fake_st, monkeypatch):
    """:110-111 空计划分支：st.info 提示且不写 impression。"""
    dao = _dao()
    _wire_full_render(monkeypatch, dao, [])
    dashboard_page.render_dashboard()
    assert fake_st.session_state.get("_rec_impressions", {}) == {} or "_rec_impressions" not in fake_st.session_state
    labels = [c[0] for c in fake_st.calls]
    assert "info" in labels, "空计划应 st.info 引导文案"


def test_render_dashboard_recommend_button_click_emits_clicked_and_navigates(monkeypatch):
    """:147-155 按钮分支：clicked 事件携带 impression 字段＋navigate_to_problem 调用。"""
    dao = _dao()
    fake = DashboardFakeStreamlit(buttons={"去做 →": True})
    monkeypatch.setattr(dashboard_page, "st", fake)
    monkeypatch.setattr(components, "st", fake)
    _wire_full_render(monkeypatch, dao, _plan())
    navigated = []
    monkeypatch.setattr(dashboard_page, "navigate_to_problem",
                        lambda lang, slug, pid: navigated.append((lang, slug, pid)))
    dashboard_page.render_dashboard()
    clicked = [c for c in dao.emit_event.call_args_list if c.args and c.args[0] == "recommendation_clicked"]
    assert len(clicked) == 2, "两个推荐卡按钮都被按下，各上报一次 clicked"
    payload = clicked[0].kwargs["payload"]
    assert payload["reason_code"] == "weak_topic" and payload["rank"] == 1
    assert navigated[0] == ("python", "loops", "p1")


def test_render_dashboard_recommend_second_run_no_duplicate_shown(fake_st, monkeypatch):
    """:117-120 展示去重：第二次渲染同一 plan 不再重复上报 shown。"""
    dao = _dao()
    _wire_full_render(monkeypatch, dao, _plan())
    dashboard_page.render_dashboard()
    first = len([c for c in dao.emit_event.call_args_list if c.args and c.args[0] == "recommendation_shown"])
    dashboard_page.render_dashboard()
    second = len([c for c in dao.emit_event.call_args_list if c.args and c.args[0] == "recommendation_shown"])
    assert first == 2 and second == first, "session_state 去重后第二次渲染不再新增 shown 事件"
