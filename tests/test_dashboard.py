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
