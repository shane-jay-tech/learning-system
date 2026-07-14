"""Tests for heatmap data aggregation and local date handling."""
import pytest
from datetime import date, timedelta, datetime, timezone
from core.progress import ProgressDAO


@pytest.fixture
def dao(tmp_path):
    db = tmp_path / "test.db"
    d = ProgressDAO(str(db))
    yield d
    d.close()


class TestHeatmapAggregation:
    def test_empty_db_returns_empty(self, dao):
        rows = dao.conn.execute(
            "SELECT DATE(ts) AS d, COUNT(*) AS n, SUM(passed) AS p "
            "FROM attempts WHERE ts >= datetime('now', '-90 days') "
            "GROUP BY d ORDER BY d"
        ).fetchall()
        assert rows == []

    def test_single_day_aggregation(self, dao):
        dao.record_attempt("python", "p1", "x=1", True, "")
        dao.record_attempt("python", "p2", "x=2", False, "")
        dao.record_attempt("python", "p3", "x=3", True, "")
        rows = dao.conn.execute(
            "SELECT DATE(ts) AS d, COUNT(*) AS n, SUM(passed) AS p "
            "FROM attempts WHERE ts >= datetime('now', '-90 days') "
            "GROUP BY d ORDER BY d"
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][1] == 3  # count
        assert rows[0][2] == 2  # passed

    def test_multi_day_with_manual_timestamps(self, dao):
        today = date.today()
        yesterday = today - timedelta(days=1)
        dao.conn.execute(
            "INSERT INTO attempts (lang, problem_id, code, passed, ai_feedback, ts) VALUES (?,?,?,?,?,?)",
            ("python", "p1", "x", 1, "", f"{yesterday} 10:00:00")
        )
        dao.conn.execute(
            "INSERT INTO attempts (lang, problem_id, code, passed, ai_feedback, ts) VALUES (?,?,?,?,?,?)",
            ("python", "p2", "x", 1, "", f"{today} 09:00:00")
        )
        dao.conn.commit()
        rows = dao.conn.execute(
            "SELECT DATE(ts) AS d, COUNT(*) AS n FROM attempts "
            "WHERE ts >= datetime('now', '-90 days') GROUP BY d ORDER BY d"
        ).fetchall()
        assert len(rows) == 2


class TestLocalDateHandling:
    def test_daily_streak_uses_local_dates(self, dao):
        today = date.today()
        for i in range(3):
            d = today - timedelta(days=i)
            dao.conn.execute(
                "INSERT INTO attempts (lang, problem_id, code, passed, ai_feedback, ts) VALUES (?,?,?,?,?,?)",
                ("python", f"p{i}", "x", 1, "", f"{d} 12:00:00")
            )
        dao.conn.commit()
        streak = dao.daily_streak()
        assert streak >= 3

    def test_streak_broken_by_gap(self, dao):
        today = date.today()
        dao.conn.execute(
            "INSERT INTO attempts (lang, problem_id, code, passed, ai_feedback, ts) VALUES (?,?,?,?,?,?)",
            ("python", "p1", "x", 1, "", f"{today} 10:00:00")
        )
        day_before_yesterday = today - timedelta(days=2)
        dao.conn.execute(
            "INSERT INTO attempts (lang, problem_id, code, passed, ai_feedback, ts) VALUES (?,?,?,?,?,?)",
            ("python", "p2", "x", 1, "", f"{day_before_yesterday} 10:00:00")
        )
        dao.conn.commit()
        streak = dao.daily_streak()
        assert streak == 1

    def test_empty_streak_returns_zero(self, dao):
        assert dao.daily_streak() == 0


class TestHeatmapColorLevels:
    """Verify the color level thresholds are stable."""

    def test_color_thresholds(self):
        def color_for_count(count):
            if count == 0:
                return "#EBEDF0"
            elif count <= 2:
                return "#C6E48B"
            elif count <= 5:
                return "#7BC96F"
            elif count <= 10:
                return "#239A3B"
            else:
                return "#196127"

        assert color_for_count(0) == "#EBEDF0"
        assert color_for_count(1) == "#C6E48B"
        assert color_for_count(2) == "#C6E48B"
        assert color_for_count(3) == "#7BC96F"
        assert color_for_count(5) == "#7BC96F"
        assert color_for_count(6) == "#239A3B"
        assert color_for_count(10) == "#239A3B"
        assert color_for_count(11) == "#196127"
