import re
import sqlite3
import threading
import time
from typing import Optional

from core.runners.base import BaseRunner, RunResult


# setup_sql 只允许这几种语句（防 ATTACH / PRAGMA 文件读盘等）
_SETUP_ALLOWED_RE = re.compile(
    r"^\s*(CREATE\s+TABLE|INSERT\s+INTO|CREATE\s+INDEX|CREATE\s+VIEW)\b",
    re.IGNORECASE,
)


def _split_sql_statements(sql: str) -> list:
    """按分号切 SQL 语句，忽略字符串字面量和方括号引用内的分号。"""
    out, buf = [], []
    in_single = False
    in_double = False
    in_bracket = False
    i = 0
    n = len(sql)
    while i < n:
        ch = sql[i]
        if not in_single and not in_double and not in_bracket:
            if ch == "'":
                in_single = True; buf.append(ch)
            elif ch == '"':
                in_double = True; buf.append(ch)
            elif ch == '[':
                in_bracket = True; buf.append(ch)
            elif ch == ";":
                out.append("".join(buf)); buf = []
            else:
                buf.append(ch)
        elif in_single:
            if ch == "'":
                if i + 1 < n and sql[i+1] == "'":
                    buf.append("''"); i += 2; continue
                in_single = False; buf.append(ch)
            else:
                buf.append(ch)
        elif in_double:
            if ch == '"':
                in_double = False; buf.append(ch)
            else:
                buf.append(ch)
        elif in_bracket:
            if ch == ']':
                in_bracket = False; buf.append(ch)
            else:
                buf.append(ch)
        i += 1
    if buf:
        out.append("".join(buf))
    return [s.strip() for s in out if s.strip()]


def _validate_setup_sql(setup_sql: str) -> Optional[str]:
    """检查 setup_sql 只含白名单语句。返回错误描述（None = 通过）。"""
    for s in _split_sql_statements(setup_sql):
        if not _SETUP_ALLOWED_RE.match(s):
            return f"setup_sql 含不允许的语句：{s[:50]}..."
    return None


_QUERY_FIRST_WORD_RE = re.compile(r"^\s*(SELECT|WITH|EXPLAIN)\b", re.IGNORECASE)

_AUTHORIZER_DENY_MSG = (
    "本练习只允许查询（SELECT），不允许修改数据库结构或数据、"
    "访问本机文件或执行管理命令。请检查你的 SQL 是否为 SELECT 查询。"
)


class SQLRunner(BaseRunner):
    timeout_sec = 2

    def run(self, code: str, stdin: str = "", expected: Optional[dict] = None) -> RunResult:
        blocked = self.check_security()
        if blocked:
            return blocked
        t0 = time.time()

        # 检测多语句（识别字符串字面量内的分号，避免误判）
        if len(_split_sql_statements(code)) > 1:
            return RunResult(
                ok=False, stdout="", stderr="本练习只支持一条 SQL 语句，请去掉多余的分号。",
                timed_out=False, exit_code=None, error_kind="runtime",
                elapsed_ms=int((time.time() - t0) * 1000),
            )

        # 首词预检：明显非查询语句提前拒绝，给更友好的错误
        if not _QUERY_FIRST_WORD_RE.match(code):
            return RunResult(
                ok=False, stdout="", stderr=_AUTHORIZER_DENY_MSG,
                timed_out=False, exit_code=None, error_kind="runtime",
                elapsed_ms=int((time.time() - t0) * 1000),
            )

        # 验证 setup_sql 白名单
        if expected and expected.get("setup_sql"):
            err = _validate_setup_sql(expected["setup_sql"])
            if err:
                return RunResult(
                    ok=False, stdout="", stderr=err,
                    timed_out=False, exit_code=None, error_kind="sandbox",
                    elapsed_ms=int((time.time() - t0) * 1000),
                )

        conn = sqlite3.connect(":memory:")
        try:
            # SQLite authorizer：学生 SQL 只允许 SELECT/读操作
            def _authorizer(action, arg1, arg2, db_name, trigger):
                _ALLOWED = {
                    sqlite3.SQLITE_SELECT,
                    sqlite3.SQLITE_READ,
                    sqlite3.SQLITE_FUNCTION,
                }
                if action in _ALLOWED:
                    return sqlite3.SQLITE_OK
                return sqlite3.SQLITE_DENY

            timer = threading.Timer(self.timeout_sec, conn.interrupt)
            timer.daemon = True
            timer.start()
            try:
                cur = conn.cursor()
                if expected and expected.get("setup_sql"):
                    cur.executescript(expected["setup_sql"])
                # setup 完成后启用 authorizer，限制学生 SQL 只能 SELECT
                conn.set_authorizer(_authorizer)
                cur.execute(code)
                rows = []
                headers = []
                if cur.description:
                    headers = [d[0] for d in cur.description]
                    rows = [list(r) for r in cur.fetchall()]
                stdout = _render_table(headers, rows) if headers else "(查询执行成功，无返回行)"
                return RunResult(
                    ok=True,
                    stdout=stdout,
                    stderr="",
                    timed_out=False,
                    exit_code=None,
                    error_kind=None,
                    rows=rows,
                    elapsed_ms=int((time.time() - t0) * 1000),
                )
            finally:
                timer.cancel()
        except sqlite3.OperationalError as e:
            msg = str(e)
            if "interrupt" in msg.lower():
                return RunResult(
                    ok=False, stdout="", stderr="SQL 执行超过 2 秒，已中断。",
                    timed_out=True, exit_code=None, error_kind="timeout",
                    elapsed_ms=int((time.time() - t0) * 1000),
                )
            if "not authorized" in msg.lower():
                return RunResult(
                    ok=False, stdout="", stderr=_AUTHORIZER_DENY_MSG,
                    timed_out=False, exit_code=None, error_kind="runtime",
                    elapsed_ms=int((time.time() - t0) * 1000),
                )
            return RunResult(
                ok=False, stdout="", stderr=msg,
                timed_out=False, exit_code=None, error_kind="runtime",
                elapsed_ms=int((time.time() - t0) * 1000),
            )
        except sqlite3.Error as e:
            return RunResult(
                ok=False, stdout="", stderr=str(e),
                timed_out=False, exit_code=None, error_kind="runtime",
                elapsed_ms=int((time.time() - t0) * 1000),
            )
        finally:
            conn.close()


def _render_table(headers, rows) -> str:
    if not headers:
        return ""
    widths = [len(str(h)) for h in headers]
    for r in rows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(str(c)))
    def fmt_row(cells):
        return "| " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(cells)) + " |"
    sep = "|" + "|".join("-" * (w + 2) for w in widths) + "|"
    lines = [fmt_row(headers), sep]
    for r in rows:
        lines.append(fmt_row(r))
    return "\n".join(lines)
