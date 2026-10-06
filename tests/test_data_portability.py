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


def _bare_payload(ps_rows=None, rs_rows=None):
    return {"format": FORMAT_NAME, "version": 1, "data": {
        "attempts": [], "learning_events": [], "rubric_scores": [],
        "problems_status": ps_rows or [], "review_state": rs_rows or [], "meta": []}}


# ---------------------------------------------------------------- l1004-13 值域
def test_l1004_13_破坏例脏行被跳过不导入且计数告警(tmp_path, capsys):
    """l1004-13 破坏例翻正：ease=1234.5 + interval=9999 + streak=-7 一击不入库——
    折中案语义＝跳脏行＋计数告警（不整份拒绝、不删数据）。"""
    dao = ProgressDAO(str(tmp_path / "dirty.db"))
    try:
        payload = _bare_payload(rs_rows=[{
            "lang": "python", "problem_id": "dirty/1", "interval_days": 9999,
            "ease": 1234.5, "review_streak": -7, "next_due_date": "2026-01-01", 
            "last_result": "pass", "updated_ts": "2026-10-01T00:00:00"}])
        stats = import_all(dao, payload)
        assert stats["review_state"] == 0 and stats["review_state_skipped"] == 1
        row = dao.conn.execute(
            "SELECT interval_days, ease, review_streak FROM review_state WHERE problem_id='dirty/1'").fetchone()
        assert row is None, row
        assert "跳过 1 行" in capsys.readouterr().out
    finally:
        dao.close()


def test_l1004_13_合法边界行仍可导入(tmp_path):
    dao = ProgressDAO(str(tmp_path / "edge.db"))
    try:
        payload = _bare_payload(rs_rows=[{
            "lang": "python", "problem_id": "edge/1", "interval_days": 30,
            "ease": 2.0, "review_streak": 0, "next_due_date": "2026-01-01", 
            "last_result": "pass", "updated_ts": "2026-10-01T00:00:00"}])
        stats = import_all(dao, payload)
        assert stats["review_state"] == 1 and "review_state_skipped" not in stats
    finally:
        dao.close()


def test_l1004_13_写侧夹钳把脏行在下次写库时夹回(tmp_path):
    """手工插脏行（9999, 1234.5, -7）→ update_review_state 一次 → 三值被夹回值域。"""
    dao = ProgressDAO(str(tmp_path / "clamp.db"))
    try:
        dao.conn.execute(
            "INSERT INTO review_state (lang, problem_id, interval_days, ease, review_streak, "
            "next_due_date, last_result) VALUES ('python','cl/1',9999,1234.5,-7,'2026-01-01','pass')")
        dao.conn.commit()
        dao.update_review_state("python", "cl/1", True, 3)
        row = dao.conn.execute(
            "SELECT interval_days, ease, review_streak FROM review_state WHERE problem_id='cl/1'").fetchone()
        assert row[0] <= 30 and 1.5 <= row[1] <= 2.0 and row[2] == 1, row
        assert row[1] == 2.0, row          # 夹回 2.0 后 d3 通过 ease 不降：clamp→2.0，pass 不触发 -0.1
    finally:
        dao.close()


def test_l1004_13_截断样本_int非round(tmp_path):
    """l1004-13 §四：钉 int() 截断口径——(6, 1.6) ⇒ int(9.6)=9 而非 round 的 10。"""
    dao = ProgressDAO(str(tmp_path / "trunc.db"))
    try:
        dao.conn.execute(
            "INSERT INTO review_state (lang, problem_id, interval_days, ease, review_streak, "
            "next_due_date, last_result) VALUES ('python','tr/1',6,1.6,3,'2026-01-01','pass')")
        dao.conn.commit()
        dao.update_review_state("python", "tr/1", True, 3)
        row = dao.conn.execute(
            "SELECT interval_days FROM review_state WHERE problem_id='tr/1'").fetchone()
        assert row[0] == 9, row            # int(9.6)=9 截断；若被顺手改 round 会变 10
    finally:
        dao.close()


# ---------------------------------------------------------------- l1004-09 归并案①
def test_l1004_09_E4_旧导入不再覆盖新本地(tmp_path):
    """E4 翻正：本地 10-05 新结果 + 导入 09-01 旧作答 ⇒ 保留本地（old-overrides-new=False）。"""
    dao = ProgressDAO(str(tmp_path / "e4.db"))
    try:
        with dao.conn:
            dao.conn.execute("INSERT INTO problems_status(lang, problem_id, status, last_attempt_ts) "
                             "VALUES ('python','demo/p1','solved','2026-10-05T10:00:00')")
        payload = _bare_payload(ps_rows=[{
            "lang": "python", "problem_id": "demo/p1", "status": "wrong", 
            "last_attempt_ts": "2026-09-01T08:00:00"}])
        import_all(dao, payload)
        row = dao.conn.execute(
            "SELECT status, last_attempt_ts FROM problems_status WHERE problem_id='demo/p1'").fetchone()
        assert row == ("solved", "2026-10-05T10:00:00"), row
    finally:
        dao.close()


def test_l1004_09_新导入仍覆盖旧本地(tmp_path):
    dao = ProgressDAO(str(tmp_path / "fwd.db"))
    try:
        with dao.conn:
            dao.conn.execute("INSERT INTO problems_status(lang, problem_id, status, last_attempt_ts) "
                             "VALUES ('python','demo/p2','wrong','2026-09-01T08:00:00')")
        payload = _bare_payload(ps_rows=[{
            "lang": "python", "problem_id": "demo/p2", "status": "solved", 
            "last_attempt_ts": "2026-10-05T10:00:00"}])
        import_all(dao, payload)
        row = dao.conn.execute(
            "SELECT status FROM problems_status WHERE problem_id='demo/p2'").fetchone()
        assert row == ("solved",), row
    finally:
        dao.close()


def test_l1004_09_NULL规_本地空ts被导入覆盖_导入空ts不动本地(tmp_path):
    dao = ProgressDAO(str(tmp_path / "null.db"))
    try:
        with dao.conn:
            dao.conn.execute("INSERT INTO problems_status(lang, problem_id, status, last_attempt_ts) VALUES ('python','n/1','wrong',NULL)")
            dao.conn.execute("INSERT INTO problems_status(lang, problem_id, status, last_attempt_ts) VALUES ('python','n/2','wrong','2026-10-05T10:00:00')")
        payload = _bare_payload(ps_rows=[
            {"lang": "python", "problem_id": "n/1", "status": "solved", "last_attempt_ts": "2026-10-06T09:00:00"},
            {"lang": "python", "problem_id": "n/2", "status": "solved", "last_attempt_ts": None}])
        import_all(dao, payload)
        rows = dict(dao.conn.execute(
            "SELECT problem_id, status FROM problems_status").fetchall())
        assert rows["n/1"] == "solved", rows        # 本地 NULL＝最旧，被有 ts 导入行覆盖
        assert rows["n/2"] == "wrong", rows         # 导入行 ts NULL ⇒ 不覆盖本地现行值
    finally:
        dao.close()


def test_l1004_09_review_state同型ts归并(tmp_path):
    """review_state 同型病同批同改：updated_ts 归并——旧导入不覆盖新本地复习态。"""
    dao = ProgressDAO(str(tmp_path / "rs.db"))
    try:
        with dao.conn:
            dao.conn.execute("INSERT INTO review_state(lang, problem_id, interval_days, ease, review_streak, next_due_date, last_result, updated_ts) VALUES ('python','r/1',12,2.0,4,'2026-10-12','pass','2026-10-05T10:00:00')")
        payload = _bare_payload(rs_rows=[{
            "lang": "python", "problem_id": "r/1", "interval_days": 1,
            "ease": 1.5, "review_streak": 0, "next_due_date": "2026-09-02", 
            "last_result": "fail", "updated_ts": "2026-09-01T08:00:00"}])
        import_all(dao, payload)
        row = dao.conn.execute(
            "SELECT interval_days, updated_ts FROM review_state WHERE problem_id='r/1'").fetchone()
        assert row == (12, "2026-10-05T10:00:00"), row
    finally:
        dao.close()

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
