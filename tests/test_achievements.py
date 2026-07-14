"""Tests for the achievement system — trigger logic, idempotency, progress tracking."""
import pytest
from core.progress import ProgressDAO
from core.achievements import (
    ACHIEVEMENTS, check_achievements, get_all_earned, get_progress_summary, get_achievement
)


@pytest.fixture
def dao(tmp_path):
    db = tmp_path / "test.db"
    d = ProgressDAO(str(db))
    yield d
    d.close()


def _solve(dao, lang, pid):
    dao.record_attempt_and_status(lang, pid, "x=1", True, "good")


def _fail(dao, lang, pid):
    dao.record_attempt_and_status(lang, pid, "x=1", False, "wrong")


class TestAchievementDefinitions:
    def test_all_have_unique_ids(self):
        ids = [a.id for a in ACHIEVEMENTS]
        assert len(ids) == len(set(ids))

    def test_count_is_22(self):
        assert len(ACHIEVEMENTS) == 22

    def test_all_have_category(self):
        valid_cats = {"streak", "language", "path", "special"}
        for a in ACHIEVEMENTS:
            assert a.category in valid_cats

    def test_get_achievement_found(self):
        a = get_achievement("first_solve")
        assert a is not None
        assert a.title == "初窥门径"

    def test_get_achievement_missing(self):
        assert get_achievement("nonexistent") is None


class TestFirstSolve:
    def test_first_solve_triggers(self, dao):
        _solve(dao, "python", "p1")
        newly = check_achievements(dao)
        assert "first_solve" in newly
        assert "python_first" in newly

    def test_no_double_trigger(self, dao):
        _solve(dao, "python", "p1")
        check_achievements(dao)
        _solve(dao, "python", "p2")
        newly2 = check_achievements(dao)
        assert "first_solve" not in newly2
        assert "python_first" not in newly2


class TestStreakAchievements:
    def test_streak_3_not_triggered_at_2(self, dao):
        from unittest.mock import patch
        with patch.object(dao, "daily_streak", return_value=2):
            _solve(dao, "python", "p1")
            newly = check_achievements(dao)
            assert "streak_3" not in newly

    def test_streak_3_triggers(self, dao):
        from unittest.mock import patch
        with patch.object(dao, "daily_streak", return_value=3):
            _solve(dao, "python", "p1")
            newly = check_achievements(dao)
            assert "streak_3" in newly

    def test_streak_7_triggers(self, dao):
        from unittest.mock import patch
        with patch.object(dao, "daily_streak", return_value=7):
            _solve(dao, "python", "p1")
            newly = check_achievements(dao)
            assert "streak_7" in newly


class TestLanguageAchievements:
    def test_sql_first(self, dao):
        _solve(dao, "sql", "s1")
        newly = check_achievements(dao)
        assert "sql_first" in newly

    def test_agent_first(self, dao):
        _solve(dao, "agent_dev", "a1")
        newly = check_achievements(dao)
        assert "agent_first" in newly


class TestMultiLang:
    def test_multi_lang_needs_3(self, dao):
        _solve(dao, "python", "p1")
        _solve(dao, "sql", "s1")
        newly = check_achievements(dao)
        assert "multi_lang" not in newly

    def test_multi_lang_triggers_at_3(self, dao):
        _solve(dao, "python", "p1")
        _solve(dao, "sql", "s1")
        _solve(dao, "cpp", "c1")
        newly = check_achievements(dao)
        assert "multi_lang" in newly


class TestNoMistakes:
    def test_needs_10_solved_and_no_wrong(self, dao):
        for i in range(10):
            _solve(dao, "python", f"p{i}")
        newly = check_achievements(dao)
        assert "no_mistakes" in newly

    def test_not_triggered_with_wrong(self, dao):
        for i in range(10):
            _solve(dao, "python", f"p{i}")
        _fail(dao, "python", "p_bad")
        newly = check_achievements(dao)
        assert "no_mistakes" not in newly


class TestSolveMilestones:
    def test_solve_10(self, dao):
        for i in range(10):
            _solve(dao, "python", f"p{i}")
        newly = check_achievements(dao)
        assert "solve_10" in newly

    def test_solve_50(self, dao):
        for i in range(50):
            _solve(dao, "python", f"p{i}")
        newly = check_achievements(dao)
        assert "solve_50" in newly


class TestProgressSummary:
    def test_empty(self, dao):
        s = get_progress_summary(dao)
        assert s["earned"] == 0
        assert s["total"] == 22
        assert s["pct"] == 0.0

    def test_after_earning(self, dao):
        _solve(dao, "python", "p1")
        check_achievements(dao)
        s = get_progress_summary(dao)
        assert s["earned"] >= 1


class TestGetAllEarned:
    def test_returns_achievement_objects(self, dao):
        _solve(dao, "python", "p1")
        check_achievements(dao)
        earned = get_all_earned(dao)
        assert len(earned) >= 1
        assert earned[0].id in {"first_solve", "python_first"}
