"""Tests for cross-path recommendation engine."""
import pytest

from core.progress import ProgressDAO
from core.recommend import cross_recommend, _detect_completed_milestones


@pytest.fixture
def dao(tmp_path):
    db = tmp_path / "test.db"
    d = ProgressDAO(str(db))
    yield d
    d.close()


def test_cross_recommend_empty_when_no_progress(dao):
    """No recommendations when user hasn't completed any milestone."""
    result = cross_recommend(n=3, dao=dao)
    assert result == []


def test_detect_completed_milestones_empty(dao):
    """No milestones completed initially."""
    completed = _detect_completed_milestones(dao)
    assert len(completed) == 0


def test_cross_recommend_returns_items_with_reason(dao):
    """After completing a milestone, cross-recommend returns items with cross_reason."""
    from core.loader import load_language

    # Complete all problems in agent_mastery a2 milestone topics
    # a2 topics: agent_dev/02_debug_read, agent_dev/08_read_code
    for topic_slug in ("02_debug_read", "08_read_code"):
        topics = load_language("agent_dev")
        for t in topics:
            if t.slug == topic_slug:
                for p in t.problems:
                    dao.record_attempt_and_status("agent_dev", p.id, "x=1", True, "good")
                break

    # Also need a0 and a1 completed for a2 to count (prereqs in path),
    # but _detect_completed_milestones checks topic completion not prereq chain
    # So let's also complete a0 topics
    for topic_slug in ("01_hello_and_vars", "02_conditionals", "03_loops", "04_functions", "05_lists"):
        topics = load_language("python")
        for t in topics:
            if t.slug == topic_slug:
                for p in t.problems:
                    dao.record_attempt_and_status("python", p.id, "x=1", True, "good")
                break

    # Complete a1 topics
    topics = load_language("agent_dev")
    for t in topics:
        if t.slug == "01_git_basics":
            for p in t.problems:
                dao.record_attempt_and_status("agent_dev", p.id, "x=1", True, "good")
            break

    completed = _detect_completed_milestones(dao)
    # Should have at least a0, a1, a2 completed
    assert ("agent_mastery", "a0") in completed
    assert ("agent_mastery", "a1") in completed
    assert ("agent_mastery", "a2") in completed

    # Now cross_recommend should suggest python/07_dicts_sets (linked from a2)
    results = cross_recommend(n=5, dao=dao)
    assert len(results) > 0
    assert all("cross_reason" in r for r in results)
    # Should suggest dicts/files topics (linked from a2 completion)
    suggested_topics = {r["topic_slug"] for r in results}
    assert "07_dicts_sets" in suggested_topics or "08_files_exceptions" in suggested_topics


def test_cross_recommend_respects_limit(dao):
    """cross_recommend returns at most n items."""
    result = cross_recommend(n=1, dao=dao)
    assert len(result) <= 1


def test_cross_recommend_skips_already_solved(dao):
    """Problems already solved are not recommended."""
    from core.loader import load_language

    # Complete a2 milestone
    for topic_slug in ("02_debug_read", "08_read_code", "01_git_basics"):
        topics = load_language("agent_dev")
        for t in topics:
            if t.slug == topic_slug:
                for p in t.problems:
                    dao.record_attempt_and_status("agent_dev", p.id, "x=1", True, "good")
                break
    for topic_slug in ("01_hello_and_vars", "02_conditionals", "03_loops", "04_functions", "05_lists"):
        topics = load_language("python")
        for t in topics:
            if t.slug == topic_slug:
                for p in t.problems:
                    dao.record_attempt_and_status("python", p.id, "x=1", True, "good")
                break

    # Also solve all problems in 07_dicts_sets and 08_files_exceptions
    for topic_slug in ("07_dicts_sets", "08_files_exceptions"):
        topics = load_language("python")
        for t in topics:
            if t.slug == topic_slug:
                for p in t.problems:
                    dao.record_attempt_and_status("python", p.id, "x=1", True, "good")
                break

    results = cross_recommend(n=5, dao=dao)
    # Should not suggest 07_dicts_sets or 08_files_exceptions since all are solved
    for r in results:
        assert r["topic_slug"] not in ("07_dicts_sets", "08_files_exceptions")


def test_cross_recommend_default_dao_no_crash():
    """Default call (no dao arg) must not raise closed-database error."""
    result = cross_recommend(n=1)
    assert isinstance(result, list)
