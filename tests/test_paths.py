"""Test learning path definitions and progress."""
import pytest
from core.paths import load_all_paths, load_path
from core.progress import ProgressDAO


def test_agent_path_has_a0_milestone():
    path = load_path("agent_mastery")
    assert path is not None
    milestone_ids = [m.id for m in path.milestones]
    assert "a0" in milestone_ids


def test_agent_a1_depends_on_a0():
    path = load_path("agent_mastery")
    a1 = next(m for m in path.milestones if m.id == "a1")
    assert "a0" in a1.prereqs


def test_agent_a0_has_python_topics():
    path = load_path("agent_mastery")
    a0 = next(m for m in path.milestones if m.id == "a0")
    assert len(a0.topics) >= 3
    assert any("python" in t for t in a0.topics)


def test_all_paths_load():
    paths = load_all_paths()
    assert len(paths) >= 3
    names = [p.id for p in paths]
    assert "agent_mastery" in names


def test_milestone_progress_empty():
    dao = ProgressDAO(":memory:")
    progress = dao.milestone_progress([
        {"lang": "python", "problem_id": "python/01/q1"},
        {"lang": "python", "problem_id": "python/01/q2"},
    ])
    assert progress["total"] == 2
    assert progress["solved"] == 0
    assert progress["pct"] == 0.0
    dao.close()


def test_milestone_progress_partial():
    dao = ProgressDAO(":memory:")
    dao.record_attempt_and_status("python", "python/01/q1", "code", True, "ok")
    progress = dao.milestone_progress([
        {"lang": "python", "problem_id": "python/01/q1"},
        {"lang": "python", "problem_id": "python/01/q2"},
    ])
    assert progress["solved"] == 1
    assert progress["pct"] == 0.5
    dao.close()
