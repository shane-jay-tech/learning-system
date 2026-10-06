import logging
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


_DEFAULT_DB = str(Path(__file__).resolve().parent.parent / "data" / "progress.db")


def _guard_default_db_in_tests(db_path: Optional[str], env_override: Optional[str]) -> None:
    """A5①（2026-09-27 用户授权）：测试态禁开**默认生产库**。

    由来：波次 15 `learn36` 首版测试传 `dao=None`，`core/judge.py:_record_attempt`
    在该分支自开默认路径＝`data/progress.db`，往生产库写出 14 行合成数据
    （事后经用户批准按四条 DELETE 定点清除，现库 sha8 `46647128`→`cd2dbce4`）。
    此前这条防线只写在派单横幅与个别测试文件头（"绝不能传 None"），属**人工约定**；
    本闸把它变成机制：pytest 进程内 + 没有显式 db_path／`LS_PROGRESS_DB` 覆盖时直接拒开。

    例外出口＝`LS_ALLOW_DEFAULT_DB_IN_TESTS=1`（需在档内写明理由）。
    """
    if db_path is not None or env_override:
        return
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        return
    if os.environ.get("LS_ALLOW_DEFAULT_DB_IN_TESTS") == "1":
        return
    raise RuntimeError(
        "测试态禁开默认生产库（A5①闸）：ProgressDAO() 不接受在 pytest 里自开 "
        f"{_DEFAULT_DB}；请显式传 db_path=tmp_path/... 或设 LS_PROGRESS_DB 指向沙盒；"
        "确需例外设 LS_ALLOW_DEFAULT_DB_IN_TESTS=1 并在档内写明理由"
    )


def format_local_ts(ts_str: Optional[str]) -> str:
    """把库里存的 UTC 时间戳转成本地 'YYYY-MM-DD HH:MM'（解析失败原样返回）。

    直接用 UTC 原文展示会差 8 小时，用户看到"昨晚的提交显示成今天下午"，反人类。
    """
    if not ts_str:
        return ""
    if not isinstance(ts_str, str):
        # l1002-79（l924-23 遗留）：非字符串真值（如 int 时间戳）原会 .split 抛
        # AttributeError（except (ValueError, TypeError) 接不住）崩渲染面——归一为
        # str 后走既有解析/兜底链，崩点收口；字符串路径行为零变化。
        ts_str = str(ts_str)
    try:
        from datetime import datetime, timezone
        dt = datetime.strptime(ts_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
        dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone().strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return ts_str


class ProgressDAO:
    def __init__(self, db_path: Optional[str] = None):
        # LS_PROGRESS_DB 环境变量覆盖默认库路径——AppTest 等集成测试用它隔离真实数据
        env_override = os.environ.get("LS_PROGRESS_DB")
        _guard_default_db_in_tests(db_path, env_override)
        self.db_path = db_path or env_override or _DEFAULT_DB
        parent = os.path.dirname(os.path.abspath(self.db_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        # 并发：WAL + 5s busy_timeout 避免 Streamlit 多线程触发 database is locked
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        # 单次渲染内重复查询去重（dashboard 一次渲染会多次调 daily_streak 等）
        self._memo: dict = {}
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
        # 时间列索引：attempts_by_day / 热力图 / rubric 趋势 / 漏斗都按时间过滤，
        # 缺索引时全部 SCAN 全表（EXPLAIN 实测）。逐个容错创建：
        # 老库缺列（如 learning_events.created_at）时跳过而不是崩溃。
        for _index_ddl in (
            "CREATE INDEX IF NOT EXISTS idx_attempts_ts ON attempts(ts)",
            "CREATE INDEX IF NOT EXISTS idx_rubric_ts ON rubric_scores(ts)",
            "CREATE INDEX IF NOT EXISTS idx_events_created ON learning_events(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_status_status_ts ON problems_status(status, last_attempt_ts)",
        ):
            try:
                self.conn.execute(_index_ddl)
            except sqlite3.OperationalError as e:
                logger.warning("skip index (old schema?): %s — %s", _index_ddl, e)
        self.conn.commit()
        self._migrate()

    def _migrate(self):
        """Lightweight migrations for existing databases."""
        cols = {r[1] for r in self.conn.execute("PRAGMA table_info(rubric_scores)").fetchall()}
        if "prompt_version" not in cols:
            self.conn.execute("ALTER TABLE rubric_scores ADD COLUMN prompt_version TEXT")
        if "model" not in cols:
            self.conn.execute("ALTER TABLE rubric_scores ADD COLUMN model TEXT")
        if "dimension_id" not in cols:
            # 能力维度标准化：规范 id（correctness/completeness/…）跨题可比
            self.conn.execute("ALTER TABLE rubric_scores ADD COLUMN dimension_id TEXT")
        cur = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_meta'")
        if not cur.fetchone():
            self.conn.execute(
                "CREATE TABLE schema_meta (key TEXT PRIMARY KEY, value TEXT)")
            self.conn.execute(
                "INSERT OR REPLACE INTO schema_meta VALUES ('schema_version', '2')")
        self.conn.commit()

    def _memoized(self, key: str, fn, ttl: float = 3.0):
        """单次渲染内去重：dashboard 一次渲染会 3 次调用 daily_streak 等，
        TTL 内复用结果；写操作（record/mark_status）会清空 memo。"""
        import time as _time
        hit = self._memo.get(key)
        now = _time.monotonic()
        if hit is not None and now - hit[1] < ttl:
            return hit[0]
        value = fn()
        self._memo[key] = (value, now)
        return value

    def _clear_memo(self) -> None:
        self._memo.clear()

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
            self._clear_memo()
            return cur.lastrowid

    # 兼容旧 API（test_progress 等）
    # l1007-07 守卫告警（l1004-10 遗留 1 ③支，零破坏）：旧双 API 生产调用面=0
    # （l1004-10 取证），现存调用集中在测试。若生产面出现调用 ⇒ 告警（收口①删旧前置观察）。
    def record_attempt(self, lang: str, pid: str, code: str, passed: bool, ai_feedback: str) -> int:
        import logging
        logging.getLogger(__name__).warning(
            "[legacy-api-guard] record_attempt 被调用（lang=%s pid=%s）——旧双 API 收口③观察期，"
            "生产面应走 record_attempt_and_status 单事务正身", lang, pid)
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO attempts (lang, problem_id, code, passed, ai_feedback) VALUES (?,?,?,?,?)",
                (lang, pid, code, 1 if passed else 0, ai_feedback),
            )
            self._clear_memo()
            return cur.lastrowid

    def mark_status(self, lang: str, pid: str, status: str) -> None:
        import logging
        logging.getLogger(__name__).warning(
            "[legacy-api-guard] mark_status 被调用（lang=%s pid=%s status=%s）——旧双 API 收口③观察期，"
            "生产面应走 record_attempt_and_status 单事务正身", lang, pid, status)
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO problems_status (lang, problem_id, status, last_attempt_ts) "
                "VALUES (?,?,?, CURRENT_TIMESTAMP)",
                (lang, pid, status),
            )
        self._clear_memo()

    def get_status(self, lang: str, pid: str) -> str:
        row = self.conn.execute(
            "SELECT status FROM problems_status WHERE lang=? AND problem_id=?",
            (lang, pid),
        ).fetchone()
        return row[0] if row else "unseen"

    def list_mistakes(self) -> List[Dict]:
        def _query():
            rows = self.conn.execute("""
                WITH latest AS (
                  SELECT lang, problem_id, code, ai_feedback,
                         ROW_NUMBER() OVER (PARTITION BY lang, problem_id ORDER BY id DESC) rn
                  FROM attempts
                )
                SELECT ps.lang, ps.problem_id, ps.last_attempt_ts, l.code, l.ai_feedback
                FROM problems_status ps
                LEFT JOIN latest l
                  ON l.lang=ps.lang AND l.problem_id=ps.problem_id AND l.rn=1
                WHERE ps.status='wrong'
                ORDER BY ps.last_attempt_ts DESC
            """).fetchall()
            return [
                {"lang": r[0], "problem_id": r[1], "ts": r[2], "code": r[3] or "", "ai_feedback": r[4] or ""}
                for r in rows
            ]
        # 窗口函数一次扫描替代 2×N 相关子查询（EXPLAIN 实测原版每错题 2 次索引探测）
        return self._memoized("list_mistakes", _query)

    def summary_by_lang(self) -> Dict[str, Dict[str, int]]:
        def _query():
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
        return self._memoized("summary_by_lang", _query)

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
        # ts 存的是 UTC，按本地日期分组（中国用户 UTC+8：本地凌晨提交会
        # 被 UTC 日期归到"昨天"，趋势图错位）
        rows = self.conn.execute(
            "SELECT DATE(ts, 'localtime') AS d, COUNT(*) AS n, SUM(passed) AS p "
            "FROM attempts WHERE ts >= datetime('now', ?) "
            "GROUP BY d ORDER BY d",
            (f"-{int(days)} days",),
        ).fetchall()
        return [{"date": r[0], "attempts": r[1], "passed": r[2] or 0} for r in rows]

    def daily_streak(self) -> int:
        # 去重后的本地日期（LIMIT 400 个日期，足以覆盖 streak_30 成就；
        # 此前 LIMIT 500 行会被高频用户的一天多次提交迅速耗光，streak 被低估）
        from datetime import date, timedelta

        def _query():
            rows = self.conn.execute(
                "SELECT DISTINCT DATE(ts, 'localtime') AS d "
                "FROM attempts ORDER BY d DESC LIMIT 400"
            ).fetchall()
            local_dates = set()
            for (d_str,) in rows:
                if not d_str:
                    continue
                try:
                    local_dates.add(date.fromisoformat(d_str))
                except ValueError:
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
        return self._memoized("daily_streak", _query)

    def all_problems_status(self) -> Dict[tuple, str]:
        """{(lang, problem_id): status}——给 recommend 等模块用。"""
        def _query():
            rows = self.conn.execute(
                "SELECT lang, problem_id, status FROM problems_status"
            ).fetchall()
            return {(r[0], r[1]): r[2] for r in rows}
        return self._memoized("all_status", _query)

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

    def milestone_progress(self, topic_problems: List[Dict],
                           status: Optional[Dict] = None) -> Dict:
        """Calculate progress for a set of problems.

        topic_problems: [{"lang": "python", "problem_id": "01_hello_world"}, ...]
        status: 可传 all_problems_status() 的 {(lang, pid): status} 快照，
                避免逐题回查数据库（推荐/成就/路径页每渲染要算数十个里程碑）。
        Returns: {"total": int, "solved": int, "pct": float}
        """
        total = len(topic_problems)
        if total == 0:
            return {"total": 0, "solved": 0, "pct": 0.0}
        solved = 0
        if status is None:
            status = self.all_problems_status()
        for p in topic_problems:
            if status.get((p["lang"], p["problem_id"])) == "solved":
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

        # l1006-02/l1004-13：值域夹钳护全通道——脏行（手改/损坏导出）在下一次写库时被夹回。
        # ease 严档 2.0＝初值稳态上界（生产库普查 MAX(ease)=None、0 行，零回填成本）；
        # interval/Review streak 与下界夹钳对称补齐，防 ease 失控恒顶格与负 streak 入库。
        interval = min(max(interval, 0), 30)
        ease = min(max(ease, 1.5), 2.0)
        streak = max(streak, 0)

        if passed:
            streak += 1
            interval = min(max(interval + 1, int(interval * ease)), 30)
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

    def due_review_ids(self, limit: int = 1000) -> set:
        """到期复习题目的 (lang, problem_id) 集合——推荐引擎用，只取 id 不拉全字段。"""
        from datetime import date
        today = date.today().isoformat()
        rows = self.conn.execute(
            "SELECT lang, problem_id FROM review_state WHERE next_due_date <= ? LIMIT ?",
            (today, limit),
        ).fetchall()
        return {(r[0], r[1]) for r in rows}

    def review_health_stats(self) -> Dict:
        """Review health v2: overdue bucketing + high-risk problems."""
        from datetime import date
        today = date.today()
        rows = self.conn.execute(
            "SELECT lang, problem_id, next_due_date, last_result, review_streak "
            "FROM review_state WHERE next_due_date <= ? LIMIT 5000",
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
        """Store per-dimension rubric scores for an open question attempt.

        dimension_id 由维度名标准化而来（core.rubric_dims），
        自由文本维度名因此可以跨题聚合比较。
        """
        if not dimensions:
            return
        from core.rubric_dims import canonical_dimension
        rows = []
        for d in dimensions:
            name = str(d.get("name", ""))
            dim_id, _canon = canonical_dimension(name)
            rows.append((lang, pid, attempt_id, name, d.get("score", 0),
                         d.get("comment", ""), prompt_version, model, dim_id))
        with self.conn:
            self.conn.executemany(
                "INSERT INTO rubric_scores "
                "(lang, problem_id, attempt_id, dimension, score, comment, "
                " prompt_version, model, dimension_id) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                rows,
            )

    def rubric_history(self, lang: str, pid: str, limit: int = 10) -> List[Dict]:
        """Get rubric score history for a problem, grouped by attempt."""
        rows = self.conn.execute(
            "SELECT attempt_id, dimension, score, comment, ts, dimension_id "
            "FROM rubric_scores "
            "WHERE lang=? AND problem_id=? ORDER BY id DESC LIMIT ?",
            (lang, pid, limit * 10),
        ).fetchall()
        by_attempt: Dict[int, List] = {}
        for r in rows:
            by_attempt.setdefault(r[0], []).append(
                {"dimension": r[1], "score": r[2], "comment": r[3], "ts": r[4],
                 "dimension_id": r[5]}
            )
        return [{"attempt_id": k, "dimensions": v} for k, v in
                sorted(by_attempt.items(), reverse=True)[:limit]]

    def dimension_averages(self) -> Dict[str, float]:
        """各维度的平均分，key 为规范维度名（dimension_id 映射后，遗留数据用原名）。

        COALESCE(dimension_id, dimension)：老库行没有 id 时回退到自由文本名。
        """
        from core.rubric_dims import canonical_label
        rows = self.conn.execute(
            "SELECT COALESCE(dimension_id, dimension) AS key, AVG(score) "
            "FROM rubric_scores GROUP BY key"
        ).fetchall()
        return {canonical_label(r[0]): round(r[1], 1) for r in rows if r[0]}

    def dimension_trends(self, days: int = 30) -> List[Dict]:
        """最近 N 天各能力维度平均分（规范维度名 + 题数），供 dashboard 趋势区。"""
        from core.rubric_dims import canonical_label
        rows = self.conn.execute(
            "SELECT COALESCE(dimension_id, dimension) AS key, AVG(score), COUNT(*) "
            "FROM rubric_scores WHERE ts >= datetime('now', ?) "
            "GROUP BY key ORDER BY AVG(score) ASC",
            (f"-{int(days)} days",),
        ).fetchall()
        return [
            {"label": canonical_label(r[0]), "avg": r[1], "count": r[2]}
            for r in rows if r[0]
        ]

    def emit_event(self, event_type: str, lang: str = None, topic_id: str = None,
                   problem_id: str = None, path_id: str = None,
                   milestone_id: str = None, payload: Dict = None,
                   dedup_code_hash: str = None) -> int:
        """Record a learning event.
        l1006-03/l1004-07③：dedup_code_hash 非空时，当日同 (event_type, lang, problem_id,
        payload.code_hash) 已存在则跳过不写（报表 1:N→1:1；返回 -1）；attempts/SRS 不动。"""
        import json
        from datetime import date
        if dedup_code_hash is not None:
            local_date = date.today().isoformat()
            rows = self.conn.execute(
                "SELECT payload_json FROM learning_events "
                "WHERE event_type=? AND lang=? AND problem_id IS ? AND local_date=?",
                (event_type, lang, problem_id, local_date)).fetchall()
            for (pj,) in rows:
                try:
                    if json.loads(pj or "{}").get("code_hash") == dedup_code_hash:
                        return -1
                except Exception:
                    continue
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

    def get_due_reviews_total(self) -> int:
        """到期复习的**真总数**（COUNT 无 LIMIT）—— :423 `get_due_reviews` 的伴生查询（l924-09；行号锚 l930-17 现取订正）。

        落地 l922-123 遗留 / l923-20 在册的第二条出口：页侧 `limit=50` 拿到的是页内条数，
        真数在库侧被丢掉 ⇒ 到期 >50 时用户看不到总量。谓词与 get_due_reviews **逐字同源**
        （同 `date.today().isoformat()`、同 `next_due_date <= ?`），只把投影换成 COUNT(*)、
        去掉 ORDER BY/LIMIT ⇒ 两侧不会因口径漂移而不等；`get_due_reviews` 一行未动。

        ⚠ 位置刻意落在类尾（`checkpoint_wal` 之前）：仓内在册锚点最多指到 `progress.py:610`
        （`tests/test_recommend_review_state.py:226` 钉 :429〔l930-17 现取订正，原 :418〕、docs 若干钉 :525-:610），
        插进中段会让那些行号集体失真。找它请按名字，别按 :413（本函数现址 :638——l930-17 订正）。
        """
        from datetime import date
        today = date.today().isoformat()
        row = self.conn.execute(
            "SELECT COUNT(*) FROM review_state WHERE next_due_date <= ?",
            (today,),
        ).fetchone()
        return row[0] if row else 0

    def checkpoint_wal(self, mode: str = "TRUNCATE") -> int:
        """把 WAL 里未合并的数据落盘并截断 WAL 文件。

        WAL 默认会在 1000 页时自动 checkpoint，单机场景足够；本方法供
        备份/清理等维护脚本在需要「此刻完整落盘」时显式调用。
        返回 busy 值（0 = 完全 checkpoint）。
        """
        try:
            row = self.conn.execute(f"PRAGMA wal_checkpoint({mode})").fetchone()
            return row[0] if row else 0
        except sqlite3.OperationalError:
            return 0


    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
