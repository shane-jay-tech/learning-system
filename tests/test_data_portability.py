"""Tests for JSON data portability (export/import roundtrip)."""
import json

import pytest

from core.data_portability import (
    FORMAT_NAME, _validate, export_all, export_json, import_all, import_json,
)
from core.progress import ProgressDAO


def _seed(dao: ProgressDAO):
    dao.record_attempt_and_status("python", "p1", "print(1)", True, "不错")
    dao.record_attempt_and_status("sql", "s1", "SELECT 1", False, "再想想")
    dao.update_review_state("python", "p1", True)
    dao.record_rubric_scores("agent_dev", "a1", 1, [{"name": "清晰度", "score": 80, "comment": ""}])
    dao.emit_event("lesson_viewed", lang="python", topic_id="01_x")
    dao.set_meta("k", "v")


def test_roundtrip_into_empty_db(tmp_path):
    src = ProgressDAO(str(tmp_path / "src.db"))
    try:
        _seed(src)
    finally:
        src.close()

    payload = export_all(ProgressDAO(str(tmp_path / "src.db")))
    assert payload["format"] == FORMAT_NAME
    assert len(payload["data"]["attempts"]) == 2

    dst = ProgressDAO(str(tmp_path / "dst.db"))
    try:
        stats = import_all(dst, payload)
        assert stats["attempts"] == 2
        assert stats["problems_status"] == 2
        assert stats["meta"] == 1
        assert dst.total_attempts() == 2
        assert dst.get_status("python", "p1") == "solved"
        assert dst.get_meta("k") == "v"
        assert len(dst.list_mistakes()) == 1
    finally:
        dst.close()


def test_merge_into_existing_db_does_not_duplicate_or_lose(tmp_path):
    dao = ProgressDAO(str(tmp_path / "m.db"))
    try:
        _seed(dao)
        payload = export_all(dao)
        before = dao.total_attempts()
        stats = import_all(dao, payload)  # 合并回自己
        # append 表会翻倍（by design）；键控表幂等
        assert dao.total_attempts() == before * 2
        assert stats["problems_status"] == 2
        # meta 幂等（ON CONFLICT 更新）
        assert dao.get_meta("k") == "v"
    finally:
        dao.close()


def test_validate_rejects_garbage():
    assert _validate({"format": "other"}) is not None
    assert _validate({"format": FORMAT_NAME, "version": 99}) is not None
    assert _validate({"format": FORMAT_NAME, "version": 1, "data": {}}) is not None
    assert _validate({"format": FORMAT_NAME, "version": 1,
                      "data": {"attempts": [], "problems_status": [], "review_state": [],
                               "rubric_scores": [], "learning_events": [], "meta": []}}) is None


def test_import_rejects_garbage_without_touching_db(tmp_path):
    dao = ProgressDAO(str(tmp_path / "g.db"))
    try:
        dao.record_attempt_and_status("python", "p1", "x", True, "")
        with pytest.raises(ValueError):
            import_json(dao, '{"format": "nope"}')
        with pytest.raises(json.JSONDecodeError):
            import_json(dao, "not json at all")
        assert dao.total_attempts() == 1  # 未受影响
    finally:
        dao.close()


def test_export_json_is_valid_and_serializable(tmp_path):
    dao = ProgressDAO(str(tmp_path / "e.db"))
    try:
        _seed(dao)
        text = export_json(dao)
        parsed = json.loads(text)
        assert parsed["format"] == FORMAT_NAME
    finally:
        dao.close()
