"""Test daily_streak timezone handling."""
import sqlite3
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from core.progress import ProgressDAO


def _make_dao_with_attempts(timestamps):
    """Create a DAO with attempts at specific UTC timestamps."""
    dao = ProgressDAO(":memory:")
    for i, ts in enumerate(timestamps):
        dao.conn.execute(
            "INSERT INTO attempts(lang, problem_id, code, passed, ai_feedback, ts) VALUES(?,?,?,?,?,?)",
            ("python", f"python/test/q{i}", "code", 1, "", ts)
        )
    dao.conn.commit()
    return dao


def test_streak_same_local_day():
    now = datetime.now(timezone.utc)
    ts1 = now.strftime("%Y-%m-%d %H:%M:%S")
    ts2 = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    dao = _make_dao_with_attempts([ts1, ts2])
    streak = dao.daily_streak()
    assert streak >= 1
    dao.close()


def test_streak_consecutive_days():
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d 12:00:00")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d 12:00:00")
    day_before = (now - timedelta(days=2)).strftime("%Y-%m-%d 12:00:00")
    dao = _make_dao_with_attempts([today, yesterday, day_before])
    streak = dao.daily_streak()
    assert streak >= 3
    dao.close()


def test_streak_gap_breaks():
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d 12:00:00")
    three_days_ago = (now - timedelta(days=3)).strftime("%Y-%m-%d 12:00:00")
    dao = _make_dao_with_attempts([today, three_days_ago])
    streak = dao.daily_streak()
    assert streak == 1
    dao.close()


def test_streak_zero_when_no_attempts():
    dao = ProgressDAO(":memory:")
    streak = dao.daily_streak()
    assert streak == 0
    dao.close()


def test_streak_includes_yesterday_if_no_today():
    from datetime import date
    # Use local "yesterday" and "day before" to avoid UTC/local date mismatch
    local_today = date.today()
    local_yesterday = local_today - timedelta(days=1)
    local_day_before = local_today - timedelta(days=2)
    # Store as UTC noon equivalent — what matters is they map to the correct local dates
    yesterday_ts = local_yesterday.strftime("%Y-%m-%d 04:00:00")  # UTC morning → still same local date for UTC+N
    day_before_ts = local_day_before.strftime("%Y-%m-%d 04:00:00")
    dao = _make_dao_with_attempts([yesterday_ts, day_before_ts])
    streak = dao.daily_streak()
    assert streak >= 2
    dao.close()
