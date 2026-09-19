from datetime import date, timedelta

import pytest

from core.progress import ProgressDAO
from core.recommend import recommend


@pytest.fixture
def dao(tmp_path):
    d = ProgressDAO(str(tmp_path / "d.db"))
    yield d
    d.close()


def test_recent_attempts_order(dao):
    dao.record_attempt("python", "p1", "a", True, "")
    dao.record_attempt("python", "p2", "b", False, "")
    dao.record_attempt("sql", "s1", "c", True, "")
    recent = dao.recent_attempts(limit=10)
    assert len(recent) == 3
    assert recent[0]["problem_id"] == "s1"
    assert recent[2]["problem_id"] == "p1"
    assert recent[1]["passed"] is False


def test_recent_attempts_limit(dao):
    for i in range(7):
        dao.record_attempt("python", f"p{i}", "x", True, "")
    assert len(dao.recent_attempts(limit=3)) == 3


def test_attempts_by_day_counts(dao):
    dao.record_attempt("python", "p1", "x", True, "")
    dao.record_attempt("python", "p2", "y", False, "")
    daily = dao.attempts_by_day(days=14)
    assert len(daily) == 1
    assert daily[0]["attempts"] == 2
    assert daily[0]["passed"] == 1


def test_daily_streak_today(dao):
    dao.record_attempt("python", "p1", "x", True, "")
    assert dao.daily_streak() == 1


def test_daily_streak_zero_when_empty(dao):
    assert dao.daily_streak() == 0


def test_lang_attempt_counts(dao):
    dao.record_attempt("python", "a", "", True, "")
    dao.record_attempt("python", "b", "", False, "")
    dao.record_attempt("sql", "c", "", True, "")
    counts = dao.lang_attempt_counts()
    assert counts["python"]["attempts"] == 2
    assert counts["python"]["passed"] == 1
    assert counts["sql"]["attempts"] == 1


def test_total_attempts(dao):
    assert dao.total_attempts() == 0
    dao.record_attempt("python", "p", "x", True, "")
    dao.record_attempt("python", "p", "y", False, "")
    assert dao.total_attempts() == 2


def test_recommend_includes_wrong(dao, monkeypatch):
    fake_problems = [
        {"lang": "python", "topic_slug": "01_t", "topic_title": "t", "problem_id": "python/01_t/p1", "title": "T1", "difficulty": 1},
        {"lang": "python", "topic_slug": "01_t", "topic_title": "t", "problem_id": "python/01_t/p2", "title": "T2", "difficulty": 1},
        {"lang": "sql", "topic_slug": "01_t", "topic_title": "t", "problem_id": "sql/01_t/q1", "title": "Q1", "difficulty": 1},
    ]
    monkeypatch.setattr("core.recommend.all_problems", lambda: fake_problems)
    monkeypatch.setattr("core.recommend._path_next_problems", lambda d, s: set())
    monkeypatch.setattr("core.recommend._path_blocking_wrong", lambda d, w: set())
    dao.record_attempt("python", "python/01_t/p1", "x", False, "")
    dao.mark_status("python", "python/01_t/p1", "wrong")
    plan = recommend(n=3, dao=dao)
    assert len(plan) == 3
    ids = {p["problem_id"] for p in plan}
    assert "python/01_t/p1" in ids
    assert {p["problem_id"] for p in plan} == {"python/01_t/p1", "python/01_t/p2", "sql/01_t/q1"}


def test_recommend_falls_back_to_unseen(dao, monkeypatch):
    fake_problems = [
        {"lang": "python", "topic_slug": "01_t", "topic_title": "t", "problem_id": "python/01_t/p1", "title": "T1", "difficulty": 1},
        {"lang": "python", "topic_slug": "01_t", "topic_title": "t", "problem_id": "python/01_t/p2", "title": "T2", "difficulty": 2},
    ]
    monkeypatch.setattr("core.recommend.all_problems", lambda: fake_problems)
    plan = recommend(n=3, dao=dao)
    assert len(plan) == 2
    assert plan[0]["difficulty"] == 1


def test_recommendation_funnel_uses_created_at(dao):
    """Funnel queries must use created_at, not ts (which doesn't exist in learning_events)."""
    dao.emit_event("recommendation_shown", lang="python", problem_id="p1",
                   payload={"reason_code": "review_due", "surface": "dashboard"})
    dao.emit_event("recommendation_clicked", lang="python", problem_id="p1",
                   payload={"reason_code": "review_due", "surface": "dashboard"})
    result = dao.recommendation_funnel(days=7)
    assert result["shown"] == 1
    assert result["clicked"] == 1
    assert result["completed"] == 0


def test_recommendation_funnel_all_time(dao):
    """Funnel with days=None returns all-time counts."""
    dao.emit_event("recommendation_shown", lang="python", problem_id="p1",
                   payload={"reason_code": "explore", "surface": "dashboard"})
    dao.emit_event("recommendation_completed", lang="python", problem_id="p1",
                   payload={"reason_code": "explore"})
    result = dao.recommendation_funnel(days=None)
    assert result["shown"] == 1
    assert result["completed"] == 1


def test_recommendation_funnel_by_reason(dao):
    """reason_code grouping returns per-strategy counts."""
    dao.emit_event("recommendation_shown", lang="python", problem_id="p1",
                   payload={"reason_code": "review_due", "surface": "dashboard"})
    dao.emit_event("recommendation_shown", lang="python", problem_id="p2",
                   payload={"reason_code": "explore", "surface": "dashboard"})
    dao.emit_event("recommendation_clicked", lang="python", problem_id="p1",
                   payload={"reason_code": "review_due", "surface": "dashboard"})
    by_reason = dao.recommendation_funnel_by_reason(days=7)
    assert by_reason["review_due"]["shown"] == 1
    assert by_reason["review_due"]["clicked"] == 1
    assert by_reason["explore"]["shown"] == 1
    assert by_reason["explore"]["clicked"] == 0


def test_recommendation_completed_carries_full_attribution(dao):
    """recommendation_completed must copy recommendation_id/surface/rank from shown."""
    from core.judge import _check_recommendation_completed
    dao.emit_event("recommendation_shown", lang="python", problem_id="p1",
                   payload={"reason_code": "review_due", "surface": "dashboard",
                            "rank": 2, "recommendation_id": "20260705_dashboard_review_due_python_p1_2"})
    _check_recommendation_completed(dao, "python", "p1")
    import json
    row = dao.conn.execute(
        "SELECT payload_json FROM learning_events WHERE event_type='recommendation_completed'"
    ).fetchone()
    assert row is not None
    payload = json.loads(row[0])
    assert payload["recommendation_id"] == "20260705_dashboard_review_due_python_p1_2"
    assert payload["surface"] == "dashboard"
    assert payload["rank"] == 2
    assert payload["reason_code"] == "review_due"


def test_recommendation_completed_no_shown_no_event(dao):
    """If problem was never shown as recommendation, no completed event is emitted."""
    from core.judge import _check_recommendation_completed
    _check_recommendation_completed(dao, "python", "p_never_shown")
    count = dao.conn.execute(
        "SELECT COUNT(*) FROM learning_events WHERE event_type='recommendation_completed'"
    ).fetchone()[0]
    assert count == 0


def test_review_health_stats_empty(dao):
    """review_health_stats returns zeros when no reviews exist."""
    stats = dao.review_health_stats()
    assert stats["total_pool"] == 0
    assert stats["total_due"] == 0
    assert stats["buckets"] == {"1_3": 0, "4_7": 0, "7_plus": 0}
    assert stats["high_risk"] == []


def test_review_health_stats_overdue_bucketing(dao):
    """Overdue reviews are bucketed correctly."""
    from datetime import date, timedelta
    today = date.today()
    with dao.conn:
        dao.conn.execute(
            "INSERT INTO review_state (lang, problem_id, interval_days, ease, review_streak, next_due_date, last_result) "
            "VALUES (?,?,?,?,?,?,?)",
            ("python", "p1", 3, 2.0, 1, (today - timedelta(days=2)).isoformat(), "pass"),
        )
        dao.conn.execute(
            "INSERT INTO review_state (lang, problem_id, interval_days, ease, review_streak, next_due_date, last_result) "
            "VALUES (?,?,?,?,?,?,?)",
            ("python", "p2", 3, 2.0, 0, (today - timedelta(days=5)).isoformat(), "fail"),
        )
        dao.conn.execute(
            "INSERT INTO review_state (lang, problem_id, interval_days, ease, review_streak, next_due_date, last_result) "
            "VALUES (?,?,?,?,?,?,?)",
            ("python", "p3", 3, 2.0, 0, (today - timedelta(days=10)).isoformat(), "fail"),
        )
    stats = dao.review_health_stats()
    assert stats["total_pool"] == 3
    assert stats["total_due"] == 3
    assert stats["buckets"]["1_3"] == 1
    assert stats["buckets"]["4_7"] == 1
    assert stats["buckets"]["7_plus"] == 1
    assert len(stats["high_risk"]) == 2
    risk_pids = {hr["problem_id"] for hr in stats["high_risk"]}
    assert "p2" in risk_pids
    assert "p3" in risk_pids


# ---------------------------------------------------------------------------
# l918-05：异常分支补测（坏数据 fixture 打 39-40 / 78 / 230->250 分支）
# 复用 tests/test_dashboard_page_render.py 的 FakeStreamlit 桩；不改 ui/pages/dashboard.py。
# ---------------------------------------------------------------------------
from tests.test_ui_behavior import FakeStreamlit
import ui.components as components
import ui.pages.dashboard as dashboard_page
from unittest.mock import MagicMock


class _DashFake(FakeStreamlit):
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


def _wire_page(monkeypatch, fake, dao):
    monkeypatch.setattr(dashboard_page, "st", fake)
    monkeypatch.setattr(components, "st", fake)
    monkeypatch.setattr(dashboard_page, "ProgressDAO", lambda: dao)
    monkeypatch.setattr(dashboard_page, "check_achievements", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_progress_summary", lambda dao: {"earned": 0, "total": 22})
    monkeypatch.setattr(dashboard_page, "recommend", lambda n=5, dao=None: [])
    monkeypatch.setattr(dashboard_page, "cross_recommend", lambda n=3, dao=None: [])


def test_build_chart_data_坏行缺passed键_锁定现行为(monkeypatch):
    """:39-40 分支——daily 行缺 passed 键时现行实现直接 KeyError（无 try/except）。
    用例锁定该现行为：坏数据会在此暴露而非静默吞掉（若日间改成容错，此用例即红=提醒更新）。"""
    import pytest as _pytest
    today = date.today().isoformat()
    with _pytest.raises(KeyError, match="passed"):
        dashboard_page._build_chart_data([{"date": today, "attempts": 3}])
    # 正常行仍走赋值分支
    series, pass_series = dashboard_page._build_chart_data(
        [{"date": today, "attempts": 3, "passed": 2}])
    assert series[today] == 3 and pass_series[today] == 2


def test_build_chart_data_未知日期行_被忽略(monkeypatch):
    """:38 if row["date"] in series 分支——窗口外日期不污染 zero-fill 字典。"""
    series, pass_series = dashboard_page._build_chart_data(
        [{"date": "2001-01-01", "attempts": 9, "passed": 9}])
    assert "2001-01-01" not in series
    assert all(v == 0 for v in series.values())


def test_render_dashboard_total_attempts_zero_走空状态(monkeypatch):
    """:78 分支——total_attempts=0 → render_empty_state 引导文案，不画趋势图。"""
    dao = MagicMock()
    dao.daily_streak.return_value = 0
    dao.total_attempts.return_value = 0
    dao.attempts_by_day.return_value = []
    dao.summary_by_lang.return_value = {}
    dao.lang_attempt_counts.return_value = {}
    dao.all_problems_status.return_value = []
    dao.get_due_reviews.return_value = []
    dao.recent_attempts.return_value = []
    dao.recommendation_funnel.return_value = {"shown": 0, "clicked": 0, "completed": 0}
    dao.recommendation_funnel_by_reason.return_value = {}
    dao.review_health_stats.return_value = {"total_pool": 0, "total_due": 0, "high_risk": [], "buckets": {}}
    dao.dimension_trends.return_value = []
    dao.milestone_progress.return_value = []
    fake = _DashFake()
    _wire_page(monkeypatch, fake, dao)
    empty_calls = []
    monkeypatch.setattr(dashboard_page, "render_empty_state",
                        lambda title, sub, **kw: empty_calls.append((title, sub)))
    dashboard_page.render_dashboard()
    assert any("还没有任何提交记录" in t for t, _ in empty_calls), "total=0 应走空状态引导"
    assert not any(c[0] == "bar_chart" for c in fake.calls), "空数据不得渲染趋势图"


def test_render_dashboard_import_坏json_走错误提示不清库(monkeypatch):
    """:230->250 分支——导入坏 JSON → import_json 抛错 → render_error_notice，DAO 未清。"""
    dao = MagicMock()
    dao.total_attempts.return_value = 1
    dao.daily_streak.return_value = 1
    dao.summary_by_lang.return_value = {"python": {"attempts": 1, "solved": 1}}
    dao.lang_attempt_counts.return_value = {}
    dao.attempts_by_day.return_value = []
    dao.all_problems_status.return_value = []
    dao.get_due_reviews.return_value = []
    dao.recent_attempts.return_value = []
    dao.recommendation_funnel.return_value = {"shown": 0, "clicked": 0, "completed": 0}
    dao.recommendation_funnel_by_reason.return_value = {}
    dao.review_health_stats.return_value = {"total_pool": 0, "total_due": 0, "high_risk": [], "buckets": {}}
    dao.dimension_trends.return_value = []
    dao.milestone_progress.return_value = []
    fake = _DashFake()
    _wire_page(monkeypatch, fake, dao)

    class _BadUpload:
        @staticmethod
        def getvalue():
            return b"not-json"

    uploads = iter([_BadUpload()])
    monkeypatch.setattr(fake, "file_uploader",
                        lambda *a, **kw: next(uploads, None), raising=False)
    monkeypatch.setattr(fake, "button", lambda label, *a, **kw: label == "确认导入")
    notices = []
    monkeypatch.setattr(dashboard_page, "render_error_notice",
                        lambda title, **kw: notices.append((title, kw)))
    import core.data_portability as _dp
    monkeypatch.setattr(_dp, "import_json",
                        lambda dao_, raw: (_ for _ in ()).throw(ValueError("坏 JSON：缺少 attempts 键")))
    dashboard_page.render_dashboard()
    assert notices and "导入失败" in notices[0][0], "坏 JSON 应触发导入失败提示"
    assert "坏 JSON" in notices[0][1]["reason"], "提示应携带异常原因"
    dao._clear_memo.assert_not_called(), "失败导入不得清缓存"
