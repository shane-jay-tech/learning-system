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
    # l923-12 收口（2026-09-23）：此处原为 `>= 3` 松下界——README:52 的「3 条学习路径」在
    # 磁盘已是 6 条的情况下存活 68 天无人拦，根因就是这条下界加到 6 不触红
    # （见 docs/insights/learn-readme-numbers-20260922.md 第四节）。现钉等值：
    # 增删 content/paths/*.yaml 必须有意改这里，并同步 README:52
    # （README 侧对账见 tests/test_readme_reconcile.py，同族的代码侧等值副本另见
    # tests/test_paths_order_consistency.py 的 test_覆盖全部path）。
    assert len(paths) == 6, (
        f"学习路径条数漂移（本桩钉 6，现值 {len(paths)}）：{[p.id for p in paths]} "
        "—— 有意变更请同步改这里 + README:52 + tests/test_readme_reconcile.py")
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
