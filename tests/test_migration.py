"""Schema migration tests — verify ProgressDAO handles old database states."""
import os
import sqlite3
import tempfile

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def tmp_db(tmp_path):
    """Return a temp DB path."""
    return str(tmp_path / "test_migrate.db")


class TestEmptyDatabase:
    """Brand new database — all tables created from scratch."""

    def test_creates_all_tables(self, tmp_db):
        from core.progress import ProgressDAO
        dao = ProgressDAO(tmp_db)
        try:
            tables = {r[0] for r in dao.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            assert "attempts" in tables
            assert "problems_status" in tables
            assert "meta" in tables
            assert "review_state" in tables
            assert "rubric_scores" in tables
            assert "learning_events" in tables
            assert "schema_meta" in tables
        finally:
            dao.close()

    def test_schema_version_set(self, tmp_db):
        from core.progress import ProgressDAO
        dao = ProgressDAO(tmp_db)
        try:
            ver = dao.conn.execute(
                "SELECT value FROM schema_meta WHERE key='schema_version'"
            ).fetchone()
            assert ver is not None
            assert ver[0] == "2"
        finally:
            dao.close()


class TestOldDatabaseMissingColumns:
    """Simulate v0.5.0 DB: rubric_scores exists but lacks prompt_version/model."""

    def test_adds_missing_columns(self, tmp_db):
        conn = sqlite3.connect(tmp_db)
        conn.executescript("""
            CREATE TABLE attempts (id INTEGER PRIMARY KEY, lang TEXT, problem_id TEXT,
                code TEXT, passed INTEGER, ai_feedback TEXT, ts TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE problems_status (lang TEXT, problem_id TEXT, status TEXT,
                last_attempt_ts TEXT, PRIMARY KEY(lang, problem_id));
            CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE review_state (lang TEXT NOT NULL, problem_id TEXT NOT NULL,
                interval_days INTEGER DEFAULT 3, ease REAL DEFAULT 2.0,
                review_streak INTEGER DEFAULT 0, next_due_date TEXT,
                last_result TEXT, updated_ts TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(lang, problem_id));
            CREATE TABLE rubric_scores (id INTEGER PRIMARY KEY AUTOINCREMENT,
                lang TEXT NOT NULL, problem_id TEXT NOT NULL, attempt_id INTEGER,
                dimension TEXT NOT NULL, score INTEGER NOT NULL, comment TEXT,
                ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE learning_events (id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL, lang TEXT, topic_id TEXT, problem_id TEXT,
                path_id TEXT, milestone_id TEXT, payload_json TEXT, local_date TEXT NOT NULL);
        """)
        conn.execute("INSERT INTO attempts VALUES (1,'python','p1','code',1,'fb','2026-01-01')")
        conn.commit()
        conn.close()

        from core.progress import ProgressDAO
        dao = ProgressDAO(tmp_db)
        try:
            cols = {r[1] for r in dao.conn.execute("PRAGMA table_info(rubric_scores)").fetchall()}
            assert "prompt_version" in cols
            assert "model" in cols
            assert "dimension_id" in cols  # 能力维度标准化列（v0.6.5）
            # Original data preserved
            count = dao.conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
            assert count == 1
        finally:
            dao.close()

    def test_schema_meta_created(self, tmp_db):
        conn = sqlite3.connect(tmp_db)
        conn.executescript("""
            CREATE TABLE attempts (id INTEGER PRIMARY KEY, lang TEXT, problem_id TEXT,
                code TEXT, passed INTEGER, ai_feedback TEXT, ts TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE problems_status (lang TEXT, problem_id TEXT, status TEXT,
                last_attempt_ts TEXT, PRIMARY KEY(lang, problem_id));
            CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE review_state (lang TEXT NOT NULL, problem_id TEXT NOT NULL,
                interval_days INTEGER DEFAULT 3, ease REAL DEFAULT 2.0,
                review_streak INTEGER DEFAULT 0, next_due_date TEXT,
                last_result TEXT, updated_ts TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(lang, problem_id));
            CREATE TABLE rubric_scores (id INTEGER PRIMARY KEY AUTOINCREMENT,
                lang TEXT, problem_id TEXT, attempt_id INTEGER,
                dimension TEXT, score INTEGER, comment TEXT,
                ts TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE learning_events (id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT, lang TEXT, topic_id TEXT, problem_id TEXT,
                path_id TEXT, milestone_id TEXT, payload_json TEXT, local_date TEXT);
        """)
        conn.commit()
        conn.close()

        from core.progress import ProgressDAO
        dao = ProgressDAO(tmp_db)
        try:
            ver = dao.conn.execute(
                "SELECT value FROM schema_meta WHERE key='schema_version'"
            ).fetchone()
            assert ver is not None
        finally:
            dao.close()


class TestIdempotentMigration:
    """Running migration twice doesn't error or duplicate."""

    def test_double_init_no_error(self, tmp_db):
        from core.progress import ProgressDAO
        dao1 = ProgressDAO(tmp_db)
        dao1.close()
        dao2 = ProgressDAO(tmp_db)
        try:
            cols = {r[1] for r in dao2.conn.execute("PRAGMA table_info(rubric_scores)").fetchall()}
            assert "prompt_version" in cols
            assert "model" in cols
        finally:
            dao2.close()

    def test_data_preserved_after_double_open(self, tmp_db):
        from core.progress import ProgressDAO
        dao = ProgressDAO(tmp_db)
        dao.record_attempt("python", "p1", "code", True, "good")
        dao.close()

        dao2 = ProgressDAO(tmp_db)
        try:
            count = dao2.conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]
            assert count == 1
        finally:
            dao2.close()
