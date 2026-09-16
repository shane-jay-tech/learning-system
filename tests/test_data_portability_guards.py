# -*- coding: utf-8 -*-
"""data_portability.py 防御分支补测（d914-67 T3）。

只测 _validate / _insert_rows / import_all 的防御路径（非法类型、缺字段、
未知列名、非 dict 行、空 key），全部走 tmp_path 隔离库，不触碰 data/progress.db。
不改动 core/data_portability.py 与既有 tests/test_data_portability.py。
"""
import pytest

from core.data_portability import FORMAT_NAME, _insert_rows, _validate, import_all
from core.progress import ProgressDAO


@pytest.fixture()
def dao(tmp_path):
    d = ProgressDAO(str(tmp_path / "guard.db"))
    try:
        yield d
    finally:
        d.close()


def _payload() -> dict:
    return {
        "format": FORMAT_NAME,
        "version": 1,
        "exported_at": "2026-09-15T00:00:00+00:00",
        "data": {
            "attempts": [],
            "problems_status": [
                {"lang": "python", "problem_id": "g1", "status": "solved",
                 "last_attempt_ts": "2026-09-15T00:00:00"},
                {"lang": "python", "problem_id": "g2", "status": "attempted",
                 "last_attempt_ts": "2026-09-15T00:00:00"},
                "垃圾行（非 dict）",
            ],
            "review_state": [
                {"lang": "python", "problem_id": "g1", "interval_days": 3, "ease": 2.5,
                 "review_streak": 1, "next_due_date": "2026-09-20", "last_result": "pass",
                 "updated_ts": "2026-09-15T00:00:00"},
                {"lang": "python", "problem_id": "g2", "interval_days": 3, "ease": 2.5,
                 "review_streak": 1, "next_due_date": "2026-09-20", "last_result": "pass",
                 "updated_ts": "2026-09-15T00:00:00"},
                "垃圾行（非 dict）",
            ],
            "rubric_scores": [],
            "learning_events": [],
            "meta": [
                {"key": "k1", "value": "v1", "updated_ts": "2026-09-15T00:00:00"},
                {"key": "k2", "value": "v2", "updated_ts": "2026-09-15T00:00:00"},
                "垃圾行（非 dict）",
                {"key": "", "value": "空 key 应被跳过", "updated_ts": "2026-09-15T00:00:00"},
            ],
        },
    }


# ---- _validate 分支 ----

def test_validate_rejects_non_dict():
    assert _validate(["x"]) == "不是合法的 JSON 对象"


def test_validate_missing_data_field():
    err = _validate({"format": FORMAT_NAME, "version": 1})
    assert isinstance(err, str) and "缺少 data 字段" in err


def test_validate_data_not_dict_reports_missing_data():
    err = _validate({"format": FORMAT_NAME, "version": 1, "data": []})
    assert isinstance(err, str) and "缺少 data 字段" in err


# ---- _insert_rows 分支 ----

def test_insert_rows_empty_returns_zero(dao):
    assert _insert_rows(dao, "attempts", ["lang", "problem_id"], []) == 0


def test_insert_rows_unknown_columns_returns_zero_and_writes_nothing(dao):
    before = dao.total_attempts()
    assert _insert_rows(dao, "attempts", ["nope"], [{"nope": 1}, {"nope": 2}]) == 0
    assert dao.total_attempts() == before


def test_insert_rows_skips_non_dict_and_counts_dict_rows(dao):
    before = dao.total_attempts()
    rows = [
        {"lang": "python", "problem_id": "dp1", "code": "print(1)", "passed": 1,
         "ai_feedback": "", "ts": "2026-09-15T00:00:00"},
        "垃圾行（非 dict）",
        {"lang": "python", "problem_id": "dp2", "code": "print(2)", "passed": 0,
         "ai_feedback": "", "ts": "2026-09-15T00:00:00"},
    ]
    inserted = _insert_rows(dao, "attempts", ["lang", "problem_id", "code", "passed",
                                              "ai_feedback", "ts"], rows)
    assert inserted == 2, "非 dict 行不计入，返回值=已插入的 dict 行数"
    assert dao.total_attempts() == before + 2


# ---- import_all 垃圾行跳过 ----

def test_import_all_skips_garbage_and_counts_valid_rows(dao):
    stats = import_all(dao, _payload())
    assert stats["problems_status"] == 2, "只数有效 dict 行"
    assert stats["review_state"] == 2
    assert stats["meta"] == 2, "非 dict 行与空 key 行都不计入"
    # 有效行确实写进库
    assert dao.get_status("python", "g1") == "solved"
    assert dao.get_meta("k1") == "v1"
    assert dao.get_meta("k2") == "v2"


def test_import_all_meta_empty_key_skipped(dao):
    stats = import_all(dao, _payload())
    assert stats["meta"] == 2
    assert dao.get_meta("") is None, "空 key 行不应被写入"
