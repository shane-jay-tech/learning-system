import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional


_DEFAULT_DB = str(Path(__file__).resolve().parent.parent / "data" / "progress.db")


class ProgressDAO:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _DEFAULT_DB
        parent = os.path.dirname(os.path.abspath(self.db_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        # 并发：WAL + 5s busy_timeout 避免 Streamlit 多线程触发 database is locked
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS attempts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              lang TEXT NOT NULL,
              problem_id TEXT NOT NULL,
              code TEXT NOT NULL,
              passed INTEGER NOT NULL,
              ai_feedback TEXT,
              ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS problems_status (
              lang TEXT NOT NULL,
              problem_id TEXT NOT NULL,
              status TEXT NOT NULL,
              last_attempt_ts TEXT,
              PRIMARY KEY (lang, problem_id)
            );
            CREATE TABLE IF NOT EXISTS meta (
              key TEXT PRIMARY KEY,
              value TEXT NOT NULL,
              updated_ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_attempts_lang_pid ON attempts(lang, problem_id);
            CREATE TABLE IF NOT EXISTS review_state (
              lang TEXT NOT NULL,
              problem_id TEXT NOT NULL,
              interval_days INTEGER NOT NULL DEFAULT 3,
              ease REAL NOT NULL DEFAULT 2.0,
              review_streak INTEGER NOT NULL DEFAULT 0,
              next_due_date TEXT,
              last_result TEXT,
              updated_ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (lang, problem_id)
            );
            CREATE INDEX IF NOT EXISTS idx_review_due ON review_state(next_due_date);
            CREATE TABLE IF NOT EXISTS rubric_scores (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              lang TEXT NOT NULL,
              problem_id TEXT NOT NULL,
              attempt_id INTEGER,
              dimension TEXT NOT NULL,
              score INTEGER NOT NULL,
              comment TEXT,
              prompt_version TEXT,
              model TEXT,
              ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_rubric_lang_pid ON rubric_scores(lang, problem_id);
            CREATE TABLE IF NOT EXISTS learning_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              event_type TEXT NOT NULL,
              lang TEXT,
              topic_id TEXT,
              problem_id TEXT,
              path_id TEXT,
              milestone_id TEXT,
              payload_json TEXT,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              local_date TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_events_type ON learning_events(event_type);
            CREATE INDEX IF NOT EXISTS idx_events_date ON learning_events(local_date);
            CREATE INDEX IF NOT EXISTS idx_events_lang_pid ON learning_events(lang, problem_id);
        """)
        self.conn.commit()
        self._migrate()

    def _migrate(self):
        """Lightweight migrations for existing databases."""
        cols = {r[1] for r in self.conn.execute("PRAGMA table_info(rubric_scores)").fetchall()}
        if "prompt_version" not in cols:
            self.conn.execute("ALTER TABLE rubric_scores ADD COLUMN prompt_version TEXT")
        if "model" not in cols:
            self.conn.execute("ALTER TABLE rubric_scores ADD COLUMN model TEXT")
        cur = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_meta'")
        if not cur.fetchone():
            self.conn.execute(
                "CREATE TABLE schema_meta (key TEXT PRIMARY KEY, value TEXT)")
            self.conn.execute(
                "INSERT OR REPLACE INTO schema_meta VALUES ('schema_version', '2')")
        self.conn.commit()

    def record_attempt_and_status(self, lang: str, pid: str, code: str,
                                  passed: bool, ai_feedback: str) -> int:
        """单事务写入 attempts + problems_status，避免半成功导致两表不一致。"""
        status = "solved" if passed else "wrong"
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO attempts (lang, problem_id, code, passed, ai_feedback) "
                "VALUES (?,?,?,?,?)",
                (lang, pid, code, 1 if passed else 0, ai_feedback),
            )
            self.conn.execute(
                "INSERT OR REPLACE INTO problems_status "
                "(lang, problem_id, status, last_attempt_ts) "
                "VALUES (?,?,?, CURRENT_TIMESTAMP)",
                (lang, pid, status),
            )
            return cur.lastrowid

    # 兼容旧 API（test_progress 等）
    def record_attempt(self, lang: str, pid: str, code: str, passed: bool, ai_feedback: str) -> int:
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO attempts (lang, problem_id, code, passed, ai_feedback) VALUES (?,?,?,?,?)",
                (lang, pid, code, 1 if passed else 0, ai_feedback),
            )
            return cur.lastrowid

    def mark_status(self, lang: str, pid: str, status: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO problems_status (lang, problem_id, status, last_attempt_ts) "
                "VALUES (?,?,?, CURRENT_TIMESTAMP)",
                (lang, pid, status),
            )

    def get_status(self, lang: str, pid: str) -> str:
        row = self.conn.execute(
            "SELECT status FROM problems_status WHERE lang=? AND problem_id=?",
            (lang, pid),
        ).fetchone()
        return row[0] if row else "unseen"

    def list_mistakes(self) -> List[Dict]:
        rows = self.conn.execute("""
            SELECT ps.lang, ps.problem_id, ps.last_attempt_ts,
                   (SELECT a.code FROM attempts a
                      WHERE a.lang=ps.lang AND a.problem_id=ps.problem_id
                      ORDER BY a.id DESC LIMIT 1) AS last_code,
                   (SELECT a.ai_feedback FROM attempts a
                      WHERE a.lang=ps.lang AND a.problem_id=ps.problem_id
                      ORDER BY a.id DESC LIMIT 1) AS last_feedback
            FROM problems_status ps
            WHERE ps.status='wrong'
            ORDER BY ps.last_attempt_ts DESC
        """).fetchall()
        return [
            {"lang": r[0], "problem_id": r[1], "ts": r[2], "code": r[3] or "", "ai_feedback": r[4] or ""}
            for r in rows
        ]

    def summary_by_lang(self) -> Dict[str, Dict[str, int]]:
        out: Dict[str, Dict[str, int]] = {}
        rows = self.conn.execute(
            "SELECT lang, status, COUNT(*) FROM problems_status GROUP BY lang, status"
        ).fetchall()
        for lang, status, n in rows:
            out.setdefault(lang, {"total": 0, "solved": 0, "wrong": 0})
            out[lang]["total"] += n
            if status in ("solved", "wrong"):
                out[lang][status] += n
        return out

    def attempt_count(self, lang: str, pid: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM attempts WHERE lang=? AND problem_id=?",
            (lang, pid),
        ).fetchone()
        return row[0] if row else 0

    def set_meta(self, key: str, value: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO meta (key, value, updated_ts) VALUES (?, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_ts=CURRENT_TIMESTAMP",
                (key, value),
            )

    def get_meta(self, key: str, default: Optional[str] = None) -> Optional[str]:
        row = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def get_meta_ts(self, key: str) -> Optional[str]:
        row = self.conn.execute("SELECT updated_ts FROM meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def recent_attempts(self, limit: int = 20) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT lang, problem_id, passed, ai_feedback, ts FROM attempts "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {"lang": r[0], "problem_id": r[1], "passed": bool(r[2]),
             "ai_feedback": r[3] or "", "ts": r[4]}
            for r in rows
        ]

    def attempts_by_day(self, days: int = 14) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT DATE(ts) AS d, COUNT(*) AS n, SUM(passed) AS p "
            "FROM attempts WHERE ts >= datetime('now', ?) "
            "GROUP BY d ORDER BY d",
            (f"-{int(days)} days",),
        ).fetchall()
        return [{"date": r[0], "attempts": r[1], "passed": r[2] or 0} for r in rows]

    def daily_streak(self) -> int:
        # ts 存储为 UTC (CURRENT_TIMESTAMP)，转换为本地日期后计算连续天数
        from datetime import date, timedelta, datetime, timezone
        rows = self.conn.execute(
            "SELECT ts FROM attempts ORDER BY id DESC LIMIT 500"
        ).fetchall()
        if not rows:
            return 0
        local_dates = set()
        for (ts_str,) in rows:
            if not ts_str:
                continue
            try:
                utc_dt = datetime.strptime(ts_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
                utc_dt = utc_dt.replace(tzinfo=timezone.utc)
                local_dt = utc_dt.astimezone()
                local_dates.add(local_dt.date())
            except (ValueError, TypeError):
                continue
        if not local_dates:
            return 0
        today = date.today()
        cursor = today
        if today not in local_dates and (today - timedelta(days=1)) not in local_dates:
            return 0
        if today not in local_dates:
            cursor = today - timedelta(days=1)
        streak = 0
        while cursor in local_dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def all_problems_status(self) -> Dict[tuple, str]:
        """{(lang, problem_id): status}——给 recommend 等模块用。"""
        rows = self.conn.execute(
            "SELECT lang, problem_id, status FROM problems_status"
        ).fetchall()
        return {(r[0], r[1]): r[2] for r in rows}

    def solved_with_timestamps(self) -> List[Dict]:
        """返回所有 solved 状态的题目及其最后尝试时间，供间隔复习使用。"""
        rows = self.conn.execute(
            "SELECT lang, problem_id, last_attempt_ts FROM problems_status WHERE status='solved'"
        ).fetchall()
        return [{"lang": r[0], "problem_id": r[1], "last_attempt_ts": r[2]} for r in rows]

    def lang_attempt_counts(self) -> Dict[str, Dict[str, int]]:
        rows = self.conn.execute(
            "SELECT lang, COUNT(*) AS n, SUM(passed) AS p FROM attempts GROUP BY lang"
        ).fetchall()
        return {r[0]: {"attempts": r[1], "passed": r[2] or 0} for r in rows}

    def total_attempts(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) FROM attempts").fetchone()
        return row[0] if row else 0

    def milestone_progress(self, topic_problems: List[Dict]) -> Dict:
        """Calculate progress for a set of problems.

        topic_problems: [{"lang": "python", "problem_id": "01_hello_world"}, ...]
        Returns: {"total": int, "solved": int, "pct": float}
        """
        total = len(topic_problems)
        if total == 0:
            return {"total": 0, "solved": 0, "pct": 0.0}
        solved = 0
        for p in topic_problems:
            status = self.get_status(p["lang"], p["problem_id"])
            if status == "solved":
                solved += 1
        return {"total": total, "solved": solved, "pct": solved / total}

    def update_review_state(self, lang: str, pid: str, passed: bool, difficulty: int = 3) -> None:
        """更新间隔复习状态。通过则间隔加长，失败则重置。"""
        from datetime import date, timedelta
        row = self.conn.execute(
            "SELECT interval_days, ease, review_streak FROM review_state WHERE lang=? AND problem_id=?",
            (lang, pid),
        ).fetchone()

        if row:
            interval, ease, streak = row[0], row[1], row[2]
        else:
            interval, ease, streak = 3, 2.0, 0

        if passed:
            streak += 1
            interval = min(int(interval * ease), 30)
            if difficulty >= 4:
                ease = max(1.5, ease - 0.1)
        else:
            streak = 0
            interval = 1
            ease = max(1.5, ease - 0.2)

        next_due = (date.today() + timedelta(days=interval)).isoformat()
        with self.conn:
            self.conn.execute(
                "INSERT INTO review_state (lang, problem_id, interval_days, ease, review_streak, next_due_date, last_result, updated_ts) "
                "VALUES (?,?,?,?,?,?,?,CURRENT_TIMESTAMP) "
                "ON CONFLICT(lang, problem_id) DO UPDATE SET "
                "interval_days=excluded.interval_days, ease=excluded.ease, "
                "review_streak=excluded.review_streak, next_due_date=excluded.next_due_date, "
                "last_result=excluded.last_result, updated_ts=CURRENT_TIMESTAMP",
                (lang, pid, interval, ease, streak, next_due, "pass" if passed else "fail"),
            )

    def get_due_reviews(self, limit: int = 10) -> List[Dict]:
        """获取到期需要复习的题目。"""
        from datetime import date
        today = date.today().isoformat()
        rows = self.conn.execute(
            "SELECT lang, problem_id, interval_days, review_streak, next_due_date "
            "FROM review_state WHERE next_due_date <= ? "
            "ORDER BY next_due_date ASC LIMIT ?",
            (today, limit),
        ).fetchall()
        return [
            {"lang": r[0], "problem_id": r[1], "interval_days": r[2],
             "review_streak": r[3], "next_due_date": r[4]}
            for r in rows
        ]

    def review_health_stats(self) -> Dict:
        """Review health v2: overdue bucketing + high-risk problems."""
        from datetime import date
        today = date.today()
        rows = self.conn.execute(
            "SELECT lang, problem_id, next_due_date, last_result, review_streak "
            "FROM review_state WHERE next_due_date <= ?",
            (today.isoformat(),),
        ).fetchall()
        buckets = {"1_3": 0, "4_7": 0, "7_plus": 0}
        high_risk = []
        for lang, pid, due_date, last_result, streak in rows:
            overdue = (today - date.fromisoformat(due_date)).days
            if overdue <= 3:
                buckets["1_3"] += 1
            elif overdue <= 7:
                buckets["4_7"] += 1
            else:
                buckets["7_plus"] += 1
            if last_result == "fail" and streak == 0:
                high_risk.append({"lang": lang, "problem_id": pid, "overdue_days": overdue})
        total = self.conn.execute("SELECT COUNT(*) FROM review_state").fetchone()[0]
        return {
            "total_pool": total,
            "total_due": len(rows),
            "buckets": buckets,
            "high_risk": high_risk[:10],
        }

    def record_rubric_scores(self, lang: str, pid: str, attempt_id: int,
                             dimensions: List[Dict],
                             prompt_version: str = None, model: str = None) -> None:
        """Store per-dimension rubric scores for an open question attempt."""
        if not dimensions:
            return
        with self.conn:
            for d in dimensions:
                self.conn.execute(
                    "INSERT INTO rubric_scores "
                    "(lang, problem_id, attempt_id, dimension, score, comment, prompt_version, model) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (lang, pid, attempt_id, d.get("name", ""), d.get("score", 0),
                     d.get("comment", ""), prompt_version, model),
                )

    def rubric_history(self, lang: str, pid: str, limit: int = 10) -> List[Dict]:
        """Get rubric score history for a problem, grouped by attempt."""
        rows = self.conn.execute(
            "SELECT attempt_id, dimension, score, comment, ts FROM rubric_scores "
            "WHERE lang=? AND problem_id=? ORDER BY id DESC LIMIT ?",
            (lang, pid, limit * 10),
        ).fetchall()
        by_attempt: Dict[int, List] = {}
        for r in rows:
            by_attempt.setdefault(r[0], []).append(
                {"dimension": r[1], "score": r[2], "comment": r[3], "ts": r[4]}
            )
        return [{"attempt_id": k, "dimensions": v} for k, v in
                sorted(by_attempt.items(), reverse=True)[:limit]]

    def dimension_averages(self) -> Dict[str, float]:
        """Get average scores across all dimensions for the user."""
        rows = self.conn.execute(
            "SELECT dimension, AVG(score) FROM rubric_scores GROUP BY dimension"
        ).fetchall()
        return {r[0]: round(r[1], 1) for r in rows if r[0]}

    def emit_event(self, event_type: str, lang: str = None, topic_id: str = None,
                   problem_id: str = None, path_id: str = None,
                   milestone_id: str = None, payload: Dict = None) -> int:
        """Record a learning event."""
        import json
        from datetime import date
        local_date = date.today().isoformat()
        payload_json = json.dumps(payload, ensure_ascii=False) if payload else None
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO learning_events "
                "(event_type, lang, topic_id, problem_id, path_id, milestone_id, payload_json, local_date) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (event_type, lang, topic_id, problem_id, path_id, milestone_id, payload_json, local_date),
            )
            return cur.lastrowid

    def events_by_date(self, days: int = 90) -> List[Dict]:
        """Get event counts grouped by local_date for heatmap."""
        rows = self.conn.execute(
            "SELECT local_date, event_type, COUNT(*) "
            "FROM learning_events WHERE local_date >= date('now', ?) "
            "GROUP BY local_date, event_type ORDER BY local_date",
            (f"-{days} days",),
        ).fetchall()
        result: Dict[str, Dict] = {}
        for date_str, etype, count in rows:
            result.setdefault(date_str, {}).setdefault(etype, 0)
            result[date_str][etype] += count
        return [{"date": k, **v} for k, v in sorted(result.items())]

    def event_count(self, event_type: str = None) -> int:
        """Count events, optionally filtered by type."""
        if event_type:
            row = self.conn.execute(
                "SELECT COUNT(*) FROM learning_events WHERE event_type=?", (event_type,)
            ).fetchone()
        else:
            row = self.conn.execute("SELECT COUNT(*) FROM learning_events").fetchone()
        return row[0] if row else 0

    def recommendation_funnel(self, days: int = None) -> Dict:
        """Get recommendation funnel counts (shown/clicked/completed).

        Args:
            days: limit to recent N days, or None for all time.
        """
        time_filter = ""
        params: tuple = ()
        if days:
            time_filter = "AND created_at >= datetime('now', ?)"
            params = (f"-{days} days",)
        rows = self.conn.execute(
            f"SELECT event_type, COUNT(*) FROM learning_events "
            f"WHERE event_type IN ('recommendation_shown','recommendation_clicked','recommendation_completed') "
            f"{time_filter} GROUP BY event_type", params
        ).fetchall()
        counts = {r[0]: r[1] for r in rows}
        return {
            "shown": counts.get("recommendation_shown", 0),
            "clicked": counts.get("recommendation_clicked", 0),
            "completed": counts.get("recommendation_completed", 0),
        }

    def recommendation_funnel_by_reason(self, days: int = None) -> Dict[str, Dict]:
        """Get recommendation funnel broken down by reason_code."""
        time_filter = ""
        params: tuple = ()
        if days:
            time_filter = "AND created_at >= datetime('now', ?)"
            params = (f"-{days} days",)
        rows = self.conn.execute(
            f"SELECT json_extract(payload_json, '$.reason_code') as rc, "
            f"event_type, COUNT(*) FROM learning_events "
            f"WHERE event_type IN ('recommendation_shown','recommendation_clicked','recommendation_completed') "
            f"AND payload_json IS NOT NULL {time_filter} "
            f"GROUP BY rc, event_type", params
        ).fetchall()
        result: Dict[str, Dict] = {}
        for rc, etype, cnt in rows:
            if not rc:
                continue
            result.setdefault(rc, {"shown": 0, "clicked": 0, "completed": 0})
            if etype == "recommendation_shown":
                result[rc]["shown"] = cnt
            elif etype == "recommendation_clicked":
                result[rc]["clicked"] = cnt
            elif etype == "recommendation_completed":
                result[rc]["completed"] = cnt
        return result

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
