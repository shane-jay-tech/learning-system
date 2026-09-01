import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.progress import ProgressDAO
from scripts import audit_content, backfill_events, generate_system_report, health_check, perf_baseline


def test_content_audit_real_repository_is_clean():
    errors, warnings = audit_content.audit()
    unaccepted = [w for w in warnings if not any(t in w for t in audit_content.ACCEPTED_TOPICS)]
    assert errors == []
    assert unaccepted == []


def test_content_audit_reports_problem_and_path_failures(monkeypatch):
    bad_problem = SimpleNamespace(
        id="python/bad/1",
        statement="",
        starter_code="",
        difficulty=7,
        judge_mode="run",
        expected_output=None,
        expected_rows=None,
        setup_sql="",
        tests=[],
        rubric=[],
    )
    bad_topic = SimpleNamespace(slug="bad", lesson_md="short", problems=[bad_problem] * 3)
    empty_topic = SimpleNamespace(slug="empty", lesson_md="", problems=[])

    def fake_load(lang, content_dir):
        return [bad_topic, empty_topic] if lang == "python" else []

    milestone = SimpleNamespace(id="m1", topics=["python/missing"])
    path = SimpleNamespace(id="agent_mastery", milestones=[milestone])
    monkeypatch.setattr("core.loader.load_language", fake_load)
    monkeypatch.setattr("core.paths.load_all_paths", lambda: [path])

    errors, warnings = audit_content.audit()
    assert any("Missing statement" in e for e in errors)
    assert any("difficulty=7" in e for e in errors)
    assert any("run-mode" in e for e in errors)
    assert any("non-existent topic" in e for e in errors)
    assert any("Topic has no problems" in w for w in warnings)
    assert any("Lesson too short" in w for w in warnings)
    assert any("same difficulty" in w for w in warnings)


def test_content_audit_rejects_topic_ref_without_language_prefix(monkeypatch):
    """路径里程碑的 topic 引用缺语言前缀（如 "01_demo"）必须报错——此前是死代码漏检。"""
    milestone = SimpleNamespace(id="m1", topics=["no_prefix_topic"])
    path = SimpleNamespace(id="agent_mastery", milestones=[milestone])
    monkeypatch.setattr("core.loader.load_language", lambda lang, content_dir: [])
    monkeypatch.setattr("core.paths.load_all_paths", lambda: [path])
    errors, _ = audit_content.audit()
    assert any("缺语言前缀" in e for e in errors)

    # 未知语言前缀也要报错
    milestone2 = SimpleNamespace(id="m2", topics=["brainfuck/01_x"])
    path2 = SimpleNamespace(id="agent_mastery", milestones=[milestone2])
    monkeypatch.setattr("core.paths.load_all_paths", lambda: [path2])
    errors, _ = audit_content.audit()
    assert any("未知语言" in e for e in errors)


def test_content_audit_open_question_requires_rubric(monkeypatch):
    problem = SimpleNamespace(
        id="agent/open/1", statement="q", starter_code="", difficulty=2,
        judge_mode="ai_open", expected_output=None, expected_rows=None,
        setup_sql="", tests=[], rubric=[],
    )
    topic = SimpleNamespace(slug="open", lesson_md="x" * 250, problems=[problem])
    monkeypatch.setattr("core.loader.load_language", lambda lang, content_dir: [topic] if lang == "agent_dev" else [])
    monkeypatch.setattr("core.paths.load_all_paths", lambda: [])
    errors, _ = audit_content.audit()
    assert errors == ["[agent/open/1] ai_open problem without rubric"]


def test_audit_main_strict_and_non_strict(monkeypatch, capsys):
    monkeypatch.setattr(audit_content, "audit", lambda: ([], ["ordinary warning", "cpp/12_file_io accepted"]))
    monkeypatch.setattr("sys.argv", ["audit_content.py"])
    assert audit_content.main() == 0
    assert "PASS" in capsys.readouterr().out

    monkeypatch.setattr("sys.argv", ["audit_content.py", "--strict"])
    assert audit_content.main() == 1
    assert "FAIL" in capsys.readouterr().out


def test_backfill_dry_run_apply_and_idempotency(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "events.db"
    seed = ProgressDAO(str(db_path))
    seed.record_attempt("python", "p1", "x", True, "")
    seed.record_attempt("sql", "s1", "x", False, "")
    seed.close()

    real_cls = ProgressDAO
    monkeypatch.setattr("core.progress.ProgressDAO", lambda: real_cls(str(db_path)))

    dry = backfill_events.backfill(apply=False)
    assert dry["attempts_seen"] == 2
    assert dry["events_to_create"] == 4
    assert dry["created"] == 0
    assert "Dry run" in capsys.readouterr().out

    applied = backfill_events.backfill(apply=True, json_output=True)
    assert applied["created"] == 4
    assert json.loads(capsys.readouterr().out)["events_after"] == 4

    again = backfill_events.backfill(apply=True)
    assert again["events_to_create"] == 0
    assert again["created"] == 0


def test_backfill_skips_attempt_without_timestamp(tmp_path, monkeypatch):
    db_path = tmp_path / "missing-ts.db"
    dao = ProgressDAO(str(db_path))
    with dao.conn:
        dao.conn.execute(
            "INSERT INTO attempts(lang, problem_id, code, passed, ai_feedback, ts) VALUES(?,?,?,?,?,?)",
            ("python", "p1", "x", 1, "", ""),
        )
    dao.close()
    real_cls = ProgressDAO
    monkeypatch.setattr("core.progress.ProgressDAO", lambda: real_cls(str(db_path)))
    assert backfill_events.backfill()["events_to_create"] == 0


def test_checkpoint_wal_truncates(tmp_path):
    from core.progress import ProgressDAO
    db_path = tmp_path / "wal.db"
    dao = ProgressDAO(str(db_path))
    try:
        for i in range(200):
            dao.record_attempt_and_status("python", f"p{i}", "x", True, "")
        # WAL 模式下未 checkpoint 前，wal 文件非空
        wal = tmp_path / "wal.db-wal"
        assert wal.exists()
        size_before = wal.stat().st_size
        busy = dao.checkpoint_wal()
        assert busy == 0
        assert wal.stat().st_size <= size_before
    finally:
        dao.close()


def test_backup_script_roundtrip(tmp_path, monkeypatch):
    from scripts import backup_data
    from core.progress import ProgressDAO
    # 把备份目录与数据库都指向 tmp，避免污染真实 data/
    db = tmp_path / "progress.db"
    backup_dir = tmp_path / "backups"
    dao = ProgressDAO(str(db))
    try:
        dao.record_attempt_and_status("python", "p1", "print(1)", True, "")
    finally:
        dao.close()
    monkeypatch.setattr(backup_data, "DB", db)
    monkeypatch.setattr(backup_data, "BACKUP_DIR", backup_dir)

    out = backup_data.create_backup()
    assert Path(out).exists()

    # 破坏库后恢复
    import sqlite3
    conn = sqlite3.connect(str(db))
    conn.execute("DROP TABLE attempts")
    conn.commit()
    conn.close()

    backup_data.restore_backup(out)
    dao2 = ProgressDAO(str(db))
    try:
        assert dao2.total_attempts() == 1
    finally:
        dao2.close()
    # 旧库保留 .bak
    assert Path(str(db) + ".bak").exists()


def test_prune_old_data_dry_run_and_apply(tmp_path, monkeypatch):
    from scripts import prune_old_data
    db_path = tmp_path / "prune.db"
    dao = ProgressDAO(str(db_path))
    with dao.conn:
        # p1：5 次旧作答（400 天前）→ 保留每题最近 3 次，删 2 次
        for i in range(5):
            dao.conn.execute(
                "INSERT INTO attempts(lang, problem_id, code, passed, ai_feedback, ts) "
                "VALUES(?,?,?,?,?, datetime('now','-400 days'))",
                ("python", "p1", "x", 1, ""),
            )
        # p2：1 次旧作答 → 每题保留策略下不删
        dao.conn.execute(
            "INSERT INTO attempts(lang, problem_id, code, passed, ai_feedback, ts) "
            "VALUES(?,?,?,?,?, datetime('now','-400 days'))",
            ("sql", "p2", "x", 1, ""),
        )
        # p3：今天的作答 → 时间策略下不删
        dao.conn.execute(
            "INSERT INTO attempts(lang, problem_id, code, passed, ai_feedback, ts) "
            "VALUES(?,?,?,?,?, datetime('now'))",
            ("cpp", "p3", "x", 1, ""),
        )
        # events：2 旧 + 1 新
        for _ in range(2):
            dao.conn.execute(
                "INSERT INTO learning_events(event_type, created_at, local_date) "
                "VALUES(?, datetime('now','-400 days'), 'x')",
                ("attempt_submitted",),
            )
        dao.conn.execute(
            "INSERT INTO learning_events(event_type, created_at, local_date) "
            "VALUES('attempt_submitted', datetime('now'), 'y')",
        )
    dao.close()
    real_cls = ProgressDAO
    monkeypatch.setattr("core.progress.ProgressDAO", lambda: real_cls(str(db_path)))

    dry = prune_old_data.prune(days=365, keep_per_problem=3, apply=False)
    assert dry["learning_events_to_delete"] == 2
    assert dry["attempts_to_delete"] == 2  # p1 的 rn 4,5

    applied = prune_old_data.prune(days=365, keep_per_problem=3, apply=True)
    assert applied["attempts_to_delete"] == 2
    check = ProgressDAO(str(db_path))
    try:
        n_attempts = check.conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
        n_events = check.conn.execute("SELECT COUNT(*) FROM learning_events").fetchone()[0]
        assert n_attempts == 5  # 3(p1 保留) + 1(p2) + 1(p3)
        assert n_events == 1
        # p1 的最新一次（id 最大）必须还在（错题本依赖最近一次作答）
        latest = check.conn.execute(
            "SELECT COUNT(*) FROM attempts WHERE lang='python' AND problem_id='p1'"
        ).fetchone()[0]
        assert latest == 3
    finally:
        check.close()


def test_deep_content_audit_real_repository_clean():
    from scripts import audit_content_deep
    errors, _warnings = audit_content_deep.deep_audit()
    assert errors == []


def test_deep_content_audit_flags_syntax_setup_and_stdin_gaps(monkeypatch):
    from scripts import audit_content_deep
    bad_py = SimpleNamespace(
        id="python/deep/bad_syntax", title="bad", topic="deep", difficulty=1,
        statement="输出 1", starter_code="def broken(:\n    pass",
        expected_output="1", expected_rows=None, setup_sql=None, tests=None,
        hints=[], judge_mode="run", rubric=None, reference_answer=None,
    )
    bad_sql = SimpleNamespace(
        id="sql/deep/bad_setup", title="bad", topic="deep", difficulty=1,
        statement="查表", starter_code="", expected_output=None,
        expected_rows=[[1]], setup_sql="CREATE TABLE t(x INTEGER); INVALID SYNTAX;",
        tests=None, hints=[], judge_mode="run", rubric=None, reference_answer=None,
    )
    stdin_gap = SimpleNamespace(
        id="python/deep/stdin_gap", title="gap", topic="deep", difficulty=1,
        statement="输出结果", starter_code="print(1)", expected_output="1",
        expected_rows=None, setup_sql=None,
        tests=[{"stdin": "5\n", "expected_output": "1\n"}],
        hints=[], judge_mode="run", rubric=None, reference_answer=None,
    )
    topics = {
        "python": [SimpleNamespace(slug="deep", lesson_md="# 标题\n内容",
                                   problems=[bad_py, stdin_gap])],
        "sql": [SimpleNamespace(slug="deep", lesson_md="# 标题\n内容",
                                problems=[bad_sql])],
        "cpp": [], "r": [], "agent_dev": [],
    }
    monkeypatch.setattr(
        "core.loader.load_language",
        lambda lang, content_dir=None: topics.get(lang, []),
    )
    monkeypatch.setattr("core.paths.load_all_paths", lambda: [])
    errors, warnings = audit_content_deep.deep_audit()
    assert any("starter_code 语法错误" in e for e in errors)
    assert any("setup_sql" in e for e in errors)
    assert any("未提及输入方式" in w for w in warnings)


def test_deep_audit_brace_balance_ignores_comments_and_strings(monkeypatch):
    from scripts import audit_content_deep
    # 注释/字符串里的括号不算数：cpp file_io 的 "(1)" 注释、R 的 "{r setup}" 字符串
    cpp_starter = "int main() {\n  // 1) ofstream 写到 note.txt\n  string s = \"a)b\";\n  return 0;\n}\n"
    assert audit_content_deep._brace_balance_error(cpp_starter, "cpp") is None
    r_starter = 'rmd <- "```{r setup}"\ncat(mean(1:3))\n'
    assert audit_content_deep._brace_balance_error(r_starter, "r") is None

    # 真实不平衡 → 报错
    bad = "int main() {\n  return 0;\n"
    err = audit_content_deep._brace_balance_error(bad, "cpp")
    assert err and "大括号" in err
    bad2 = "cat(mean(1:3)\n"
    assert audit_content_deep._brace_balance_error(bad2, "r")


def test_system_metrics_cover_repository_shape():
    metrics = generate_system_report.generate_metrics()
    assert metrics["total_problems"] >= 400
    assert metrics["total_topics"] > 50
    assert metrics["paths"] >= 3
    assert metrics["lessons"] > 50
    assert metrics["tests"] >= 1
    assert metrics["lines"]["core"] > 0
    assert set(metrics["by_lang"]) == {"python", "sql", "cpp", "r", "agent_dev"}


def test_system_report_checks_good_and_bad_files(tmp_path, capsys):
    metrics = {
        "total_problems": 12,
        "total_topics": 3,
        "version": "1.2.3",
        "by_lang": {"python": {"problems": 12, "topics": 3}},
        "paths_detail": {"agent": {"title": "Agent 主线", "milestones": 4}},
    }
    good_report = tmp_path / "good.md"
    good_report.write_text("12 problems, 3 topics\nAgent 4\n", encoding="utf-8")
    assert generate_system_report.check_report(good_report, metrics)

    bad_report = tmp_path / "bad.md"
    bad_report.write_text("outdated", encoding="utf-8")
    assert not generate_system_report.check_report(bad_report, metrics)
    assert "FAIL" in capsys.readouterr().out

    readme = tmp_path / "README.md"
    readme.write_text("# v1.2.3\n12 problems and 3 topics\nroadmap v1.2.3", encoding="utf-8")
    assert generate_system_report.check_readme(readme, metrics)
    readme.write_text("# old", encoding="utf-8")
    assert not generate_system_report.check_readme(readme, metrics)


def test_count_tests_strict_and_fallback(monkeypatch, tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_one.py").write_text("def test_a(): pass\ndef test_b(): pass\n", encoding="utf-8")
    monkeypatch.setattr(generate_system_report, "ROOT", tmp_path)
    monkeypatch.setattr(
        generate_system_report.subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(stdout="42 tests collected\n"),
    )
    assert generate_system_report.count_tests(strict=True) == 42

    monkeypatch.setattr(
        generate_system_report.subprocess,
        "run",
        lambda *a, **kw: (_ for _ in ()).throw(subprocess.TimeoutExpired("pytest", 30)),
    )
    assert generate_system_report.count_tests(strict=True) == 2


def test_health_check_output_and_public_mode(monkeypatch, capsys):
    monkeypatch.setattr(health_check, "LLM_SCRIPT", "Z:/missing/llm_call.py")
    monkeypatch.setattr("core.runners.cpp_runner.CppRunner._resolve_compiler", lambda self: None)
    monkeypatch.setattr("core.runners.r_runner.RRunner._resolve_rscript", lambda self: None)
    monkeypatch.setattr("core.config.get_runner_security_mode", lambda: "public")
    monkeypatch.setattr("core.config.is_public_deploy", lambda: True)
    # llm_call 缺失只是降级（判题不受影响），不是致命失败
    assert health_check.main() == 0
    output = capsys.readouterr().out
    assert "learning-system health check" in output
    assert "missing: Z:/missing/llm_call.py" in output
    assert "PUBLIC - code execution DISABLED" in output


def test_health_check_fails_on_core_dependency_missing(monkeypatch, capsys):
    """核心依赖（python/sqlite3/streamlit/pyyaml）缺失时退出码应为 1，可作门禁。"""
    monkeypatch.setattr(health_check, "LLM_SCRIPT", "Z:/missing/llm_call.py")
    monkeypatch.setattr(health_check.sys, "version_info", (3, 8))
    monkeypatch.setattr("core.runners.cpp_runner.CppRunner._resolve_compiler", lambda self: None)
    monkeypatch.setattr("core.runners.r_runner.RRunner._resolve_rscript", lambda self: None)
    assert health_check.main() == 1
    assert "FAILED" in capsys.readouterr().out


def test_health_check_marker(capsys):
    assert health_check._check("thing", True, "detail") is True
    assert "[OK]" in capsys.readouterr().out
    assert health_check._check("thing", False) is False
    assert "[--]" in capsys.readouterr().out


def test_perf_measurements_classify_fast_and_slow(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(perf_baseline, "WARMUP", 1)
    values = iter([0.0, 0.001, 0.001, 0.004, 0.004, 0.006])
    monkeypatch.setattr(perf_baseline.time, "perf_counter", lambda: next(values))
    perf_baseline._quiet = False
    median, status, p95 = perf_baseline.measure_multi("op", lambda: calls.append(1), 2, samples=3)
    assert len(calls) == 4
    assert median == pytest.approx(2.0)
    assert p95 == pytest.approx(3.0)
    assert status == "OK"
    assert "[OK]" in capsys.readouterr().out

    values = iter([0.0, 0.010])
    monkeypatch.setattr(perf_baseline.time, "perf_counter", lambda: next(values))
    elapsed, status, p95 = perf_baseline.measure_once("slow", lambda: None, 5)
    assert elapsed == pytest.approx(10.0)
    assert status == "SLOW"
    assert p95 is None


def _patch_perf_main_dependencies(monkeypatch):
    import core.loader as loader
    import core.progress as progress
    import core.recommend as recommend_mod
    import core.report as report_mod

    monkeypatch.setattr(loader, "load_language", lambda lang: [])
    monkeypatch.setattr(recommend_mod, "recommend", lambda n=5: [])
    monkeypatch.setattr(report_mod, "generate_report", lambda dao, days=7: {})
    monkeypatch.setattr(generate_system_report, "generate_metrics", lambda: {})

    class FakeDAO:
        def close(self):
            return None

    monkeypatch.setattr(progress, "ProgressDAO", FakeDAO)


def test_perf_main_quick_json_and_markdown_modes(monkeypatch, capsys):
    _patch_perf_main_dependencies(monkeypatch)

    def fake_once(name, fn, target_ms):
        fn()
        return 1.0, "OK", None

    def fake_multi(name, fn, target_ms, samples=5):
        fn()
        return 2.0, "OK", 3.0

    monkeypatch.setattr(perf_baseline, "measure_once", fake_once)
    monkeypatch.setattr(perf_baseline, "measure_multi", fake_multi)

    monkeypatch.setattr("sys.argv", ["perf_baseline.py", "--quick", "--json"])
    assert perf_baseline.main() == 0
    records = json.loads(capsys.readouterr().out)
    assert len(records) == 5
    assert all(record["status"] == "OK" for record in records)

    monkeypatch.setattr("sys.argv", ["perf_baseline.py", "--markdown"])
    assert perf_baseline.main() == 0
    markdown = capsys.readouterr().out
    assert "| 操作 |" in markdown
    assert "load_language cold" in markdown


def test_perf_main_reports_slow_operation(monkeypatch, capsys):
    _patch_perf_main_dependencies(monkeypatch)
    results = iter([
        (20.0, "SLOW", None),
        (1.0, "OK", None),
        (1.0, "OK", None),
        (1.0, "OK", None),
        (1.0, "OK", None),
    ])

    def fake_once(name, fn, target_ms):
        fn()
        return next(results)

    monkeypatch.setattr(perf_baseline, "measure_once", fake_once)
    monkeypatch.setattr("sys.argv", ["perf_baseline.py", "--quick"])
    assert perf_baseline.main() == 1
    assert "WARNING: 1 operation" in capsys.readouterr().out
