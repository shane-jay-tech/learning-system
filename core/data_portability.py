"""学习数据可移植导出/导入（JSON 格式，跨机器迁移用）。

与 backup_data.py 的整库 zip 备份互补：zip 用于同机恢复，JSON 用于
换机器/换目录迁移（不依赖 sqlite 文件格式，导入时按业务键合并）。

格式：
{
  "format": "learning-system-export",
  "version": 1,
  "exported_at": "2026-08-15T...",
  "data": {
    "attempts": [{lang, problem_id, code, passed, ai_feedback, ts}, ...],
    "problems_status": [{lang, problem_id, status, last_attempt_ts}, ...],
    "review_state": [...], "rubric_scores": [...], "learning_events": [...],
    "meta": [{key, value, updated_ts}, ...]
  }
}
"""
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from core.progress import ProgressDAO

FORMAT_NAME = "learning-system-export"
FORMAT_VERSION = 1


def export_all(dao: ProgressDAO) -> dict:
    """导出全部学习数据为可序列化 dict。"""
    def rows(sql):
        cols = [d[0] for d in dao.conn.execute(sql).description or []]
        return [dict(zip(cols, r)) for r in dao.conn.execute(sql).fetchall()]

    return {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data": {
            "attempts": rows("SELECT lang, problem_id, code, passed, ai_feedback, ts FROM attempts ORDER BY id"),
            "problems_status": rows("SELECT lang, problem_id, status, last_attempt_ts FROM problems_status"),
            "review_state": rows("SELECT lang, problem_id, interval_days, ease, review_streak, "
                                 "next_due_date, last_result, updated_ts FROM review_state"),
            "rubric_scores": rows("SELECT lang, problem_id, attempt_id, dimension, dimension_id, score, "
                                  "comment, prompt_version, model, ts FROM rubric_scores ORDER BY id"),
            "learning_events": rows("SELECT event_type, lang, topic_id, problem_id, path_id, milestone_id, "
                                    "payload_json, created_at, local_date FROM learning_events ORDER BY id"),
            "meta": rows("SELECT key, value, updated_ts FROM meta"),
        },
    }


def _validate(payload: dict) -> Optional[str]:
    """校验导出文件结构，返回错误描述（None = 通过）。"""
    if not isinstance(payload, dict):
        return "不是合法的 JSON 对象"
    if payload.get("format") != FORMAT_NAME:
        return f"不是本系统的导出文件（format={payload.get('format')!r}）"
    if int(payload.get("version", 0)) > FORMAT_VERSION:
        return f"导出文件版本过新（{payload.get('version')} > {FORMAT_VERSION}），请升级系统"
    data = payload.get("data")
    if not isinstance(data, dict):
        return "缺少 data 字段"
    for table in ("attempts", "problems_status", "review_state",
                  "rubric_scores", "learning_events", "meta"):
        if table not in data or not isinstance(data[table], list):
            return f"缺少表数据: {table}"
    return None


def _insert_rows(dao: ProgressDAO, table: str, columns: List[str], rows: List[dict]) -> int:
    """按列名批量插入（列名来自导出文件的 key，防御性过滤未知列）。"""
    if not rows:
        return 0
    # table_info 返回 (cid, name, ...)：列名在索引 1
    known = {d[1] for d in dao.conn.execute(f"PRAGMA table_info({table})").fetchall()}
    cols = [c for c in columns if c in known]
    if not cols:
        return 0
    placeholders = ",".join("?" for _ in cols)
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
    prepared = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        prepared.append(tuple(r.get(c) for c in cols))
    if prepared:
        with dao.conn:
            dao.conn.executemany(sql, prepared)
    return len(prepared)


def import_all(dao: ProgressDAO, payload: dict) -> dict:
    """把导出数据合并进当前库。返回导入统计。"""
    err = _validate(payload)
    if err:
        raise ValueError(err)
    data = payload["data"]
    stats = {"attempts": 0, "learning_events": 0, "rubric_scores": 0,
             "problems_status": 0, "review_state": 0, "meta": 0}

    # append-only 表：直接插入（id 自增，不会与现有数据冲突）
    stats["attempts"] = _insert_rows(
        dao, "attempts",
        ["lang", "problem_id", "code", "passed", "ai_feedback", "ts"],
        data["attempts"])
    stats["learning_events"] = _insert_rows(
        dao, "learning_events",
        ["event_type", "lang", "topic_id", "problem_id", "path_id",
         "milestone_id", "payload_json", "created_at", "local_date"],
        data["learning_events"])
    stats["rubric_scores"] = _insert_rows(
        dao, "rubric_scores",
        ["lang", "problem_id", "attempt_id", "dimension", "dimension_id",
         "score", "comment", "prompt_version", "model", "ts"],
        data["rubric_scores"])

    # 键控表：INSERT OR REPLACE 合并（导入方数据覆盖同键旧值）
    for r in data["problems_status"]:
        if not isinstance(r, dict):
            continue
        with dao.conn:
            dao.conn.execute(
                "INSERT OR REPLACE INTO problems_status (lang, problem_id, status, last_attempt_ts) "
                "VALUES (?,?,?,?)",
                (r.get("lang"), r.get("problem_id"), r.get("status"), r.get("last_attempt_ts")))
        stats["problems_status"] += 1
    for r in data["review_state"]:
        if not isinstance(r, dict):
            continue
        with dao.conn:
            dao.conn.execute(
                "INSERT OR REPLACE INTO review_state "
                "(lang, problem_id, interval_days, ease, review_streak, next_due_date, "
                " last_result, updated_ts) VALUES (?,?,?,?,?,?,?,?)",
                (r.get("lang"), r.get("problem_id"), r.get("interval_days", 3),
                 r.get("ease", 2.0), r.get("review_streak", 0),
                 r.get("next_due_date"), r.get("last_result"), r.get("updated_ts")))
        stats["review_state"] += 1
    for r in data["meta"]:
        if not isinstance(r, dict) or not r.get("key"):
            continue
        with dao.conn:
            dao.conn.execute(
                "INSERT INTO meta (key, value, updated_ts) VALUES (?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_ts=excluded.updated_ts",
                (r.get("key"), r.get("value"), r.get("updated_ts")))
        stats["meta"] += 1
    return stats


def export_json(dao: ProgressDAO) -> str:
    return json.dumps(export_all(dao), ensure_ascii=False, indent=2)


def import_json(dao: ProgressDAO, text: str) -> dict:
    return import_all(dao, json.loads(text))
