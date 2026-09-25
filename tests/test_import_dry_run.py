# -*- coding: utf-8 -*-
"""导入 dry-run 体检器的桩（20260925-120605-f1d8，风险档 B / 工作类型 import）。

两条主线，正好对上卷宗的两句验收：
  ① 「导入前能列出新增/更新/冲突」——正向桩：合成载荷里**每种命运各放一条**，
     体检器必须把它们分别归到 新增 / 更新 / 冲突，且数目逐字对平。
  ② 「dry-run 后原库校验和不变」——只读桩：跑完 size＋mtime_ns＋sha256 **三值逐位不变**，
     并正面自证写句柄被拒（真试一次 INSERT 必须抛）。
  ③ 有牙自检（负控）：六个面各自的坏样本必须**全被点亮**，并钉住一条
     "正常数据不得被报成缺陷"的反假阳性（learning_events 的 NULL 是设计，见脚本注释）。

全程只用 `tmp_path` 上的临时库；生产库 `data/progress.db` 只以 mode=ro 被读，零写。
复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_import_dry_run.py -q
"""
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from scripts.import_dry_run import (
    BUSINESS_KEYS, ROOT, assert_write_refused, db_fingerprint, inspect_payload,
    open_ro, self_export_payload,
)


@pytest.fixture
def tmp_db(tmp_path):
    """在临时目录里造一个与生产库同构的库（结构从真库的 schema 现取，不抄字面量）。"""
    prod = ROOT / "data" / "progress.db"
    src = sqlite3.connect(f"file:{prod.as_posix()}?mode=ro", uri=True)
    try:
        ddl = "".join(r[0] + ";\n" for r in src.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL "
            "AND name != 'sqlite_sequence'"))   # 内部表不能自建，executescript 会当场拒
    finally:
        src.close()
    path = tmp_path / "dry.db"
    con = sqlite3.connect(str(path))
    con.executescript(ddl)
    con.execute("INSERT INTO attempts (lang,problem_id,code,passed,ts) "
                "VALUES ('python','python/01_x/01_a','print(1)',1,'2026-01-01 00:00:00')")
    con.execute("INSERT INTO problems_status (lang,problem_id,status,last_attempt_ts) "
                "VALUES ('python','python/01_x/01_a','solved','2026-01-01 00:00:00')")
    con.execute("INSERT INTO review_state (lang,problem_id,interval_days,ease,review_streak,"
                "next_due_date,last_result,updated_ts) VALUES ('python','python/01_x/01_a',3,2.0,1,"
                "'2026-01-04','ok','2026-01-01 00:00:00')")
    con.execute("INSERT INTO meta (key,value,updated_ts) VALUES ('k','old','t')")
    con.commit()
    con.close()
    return path


def _payload(*, attempts=(), status=(), review=(), meta=(), events=(), rubric=()):
    return {"format": "learning-system-export", "version": 1, "exported_at": "x",
            "data": {"attempts": list(attempts), "problems_status": list(status),
                     "review_state": list(review), "rubric_scores": list(rubric),
                     "learning_events": list(events), "meta": list(meta)}}


def _merge(rep):
    return {t: (m["insert_new"], m["overwrite_same_key"], m["conflict_value_differs"])
            for t, m in rep["merge"].items()}


# --------------------------------------------------------------- ① 三态可列出
def test_三态分得开_新增_更新_冲突(tmp_db):
    content_idx = {"python": {"python/01_x/01_a"}, "sql": set(), "cpp": set(),
                   "r": set(), "agent_dev": set()}
    con = open_ro(tmp_db)
    try:
        rep = inspect_payload(_payload(
            # 全新题（库里没有这道题的作答）→ 纯追加
            attempts=[{"lang": "python", "problem_id": "python/01_x/01_b", "code": "x",
                       "passed": 1, "ts": "2026-02-02 00:00:00"},
                      # 与现库同业务键 → append 表判"冲突/会翻倍"
                      {"lang": "python", "problem_id": "python/01_x/01_a", "code": "x",
                       "passed": 1, "ts": "2026-01-01 00:00:00"},
                      # passed 不是 0/1 → 非法答案面
                      {"lang": "python", "problem_id": "python/01_x/01_c", "code": "x",
                       "passed": "maybe", "ts": "2026-03-03 00:00:00"}],
            # 同键同值 → 更新（覆盖但内容一致，不算冲突）
            status=[{"lang": "python", "problem_id": "python/01_x/01_a", "status": "solved",
                     "last_attempt_ts": "2026-01-01 00:00:00"},
                    # 同键不同值 → 冲突（覆盖会把 solved 改成 wrong）
                    {"lang": "python", "problem_id": "python/01_x/01_a", "status": "wrong",
                     "last_attempt_ts": "2026-01-01 00:00:00"},
                    # 库里没有的题 → 新增
                    {"lang": "python", "problem_id": "python/02_y/01_b", "status": "solved",
                     "last_attempt_ts": "t"}],
            meta=[{"key": "k", "value": "new", "updated_ts": "t2"},          # 同键 → 更新＋冲突
                  {"key": "", "value": "x", "updated_ts": "t"}],              # 空 key → 缺键
            review=[{"lang": "python", "problem_id": "python/01_x/01_a", "interval_days": -5,
                     "ease": 0, "review_streak": -1, "next_due_date": None,
                     "last_result": None, "updated_ts": None}],
            events=[{"event_type": "lesson_viewed", "lang": "python", "topic_id": None,
                     "problem_id": None, "path_id": None, "milestone_id": None,
                     "payload_json": None, "created_at": "t", "local_date": "d"}],
            rubric=[{"lang": "python", "problem_id": "python/01_x/01_a", "attempt_id": 9999,
                     "dimension": "d", "dimension_id": "d", "score": "high",
                     "comment": "c", "prompt_version": "p", "model": "m", "ts": "t"}],
        ), con, content_idx)
        refused = assert_write_refused(con)
    finally:
        con.close()

    m = _merge(rep)
    assert m["attempts"] == (2, 0, 1), f"append 表应报 新增2/冲突1，实为 {m['attempts']}"
    assert m["problems_status"] == (1, 2, 1), f"键控表应报 新增1/更新2/冲突1，实为 {m['problems_status']}"
    # meta 两行：k→覆盖且值不同（冲突），空 key 行生产侧 `import_all` 会丢 ⇒ 不进更新数
    assert m["meta"] == (0, 1, 1), f"meta 应报 更新1/冲突1，实为 {m['meta']}"
    assert rep["merge"]["meta"]["skipped_by_import_all"] == 1, "空 key 行须被单列为『生产侧会丢』"
    assert refused.startswith("写句柄被拒")


def test_六个面各自都有牙_坏样本必被点亮(tmp_db):
    content_idx = {"python": {"python/01_x/01_a"}, "sql": set(), "cpp": set(),
                   "r": set(), "agent_dev": set()}
    con = open_ro(tmp_db)
    try:
        rep = inspect_payload(_payload(
            attempts=[{"lang": "python", "problem_id": "python/zz/99", "code": "bad\x00code",
                       "passed": "maybe", "ts": "t", "unexpected_col": 1}],
            status=[{"lang": "python", "problem_id": "python/01_x/01_a", "status": "banana"},
                    {"lang": "cobol", "problem_id": "python/01_x/01_a", "status": "solved"}],
            review=[{"lang": "python", "problem_id": "python/01_x/01_a", "interval_days": -5,
                     "ease": 0, "review_streak": -1}],
            meta=[{"key": "", "value": "x"}],
            rubric=[{"lang": "python", "problem_id": "python/01_x/01_a", "attempt_id": 9999,
                     "score": "high", "dimension_id": "d", "ts": "t"}],
        ), con, content_idx)
    finally:
        con.close()
    flat = json.dumps(rep, ensure_ascii=False)
    assert rep["fields"], "未知列/缺键没被抓到"
    assert any("unexpected_col" in str(x) for x in rep["fields"]), rep["fields"]
    assert any("NUL" in str(x) for x in rep["encoding"]), rep["encoding"]
    assert any("passed_not_boolean_like" in str(x) for x in rep["illegal"]), rep["illegal"]
    assert any("status_illegal_will_silently_vanish" in str(x) for x in rep["illegal"])
    assert any("banana" in str(x) for x in rep["illegal"]), "非法 status 的具体值要能列出来"
    assert any("negative_or_zero_bounds" in str(x) for x in rep["illegal"])
    assert any("score_not_numeric" in str(x) for x in rep["illegal"])
    assert any("unknown_lang" in str(x) for x in rep["references"]), rep["references"]
    assert any("problem_id_not_in_content" in str(x) for x in rep["references"])
    assert any("attempt_id_will_dangle_or_shift" in str(x) for x in rep["references"])
    assert any(d["inner_duplicate_keys"] or d["already_in_db_rows"] for d in rep["duplicates"])
    assert "cobol" in flat and "python/zz/99" in flat, "样例得能被人工顺着查下去"


def test_正常NULL不得被报成缺陷_反假阳性(tmp_db):
    """learning_events 的 topic_id/path_id/payload_json 对多数事件类型设计为 NULL。"""
    con = open_ro(tmp_db)
    try:
        rep = inspect_payload(_payload(events=[
            {"event_type": "lesson_viewed", "lang": "python", "topic_id": "python/01_x",
             "problem_id": None, "path_id": None, "milestone_id": None,
             "payload_json": None, "created_at": "t", "local_date": "d"},
            {"event_type": "achievement_unlocked", "lang": None, "topic_id": None,
             "problem_id": None, "path_id": None, "milestone_id": None,
             "payload_json": None, "created_at": "t", "local_date": None}]), con,
            {"python": set(), "sql": set(), "cpp": set(), "r": set(), "agent_dev": set()})
    finally:
        con.close()
    assert rep["fields"] == [], f"正常事件被误报为缺键：{rep['fields']}"
    assert rep["encoding"] == []


def test_结构不合法直接拒(tmp_db):
    con = open_ro(tmp_db)
    try:
        rep = inspect_payload({"format": "别的系统", "version": 1, "data": {}}, con, {})
    finally:
        con.close()
    assert rep["errors"] and not rep["merge"], "非本系统导出件必须短路"


# ------------------------------------------------------ ② dry-run 后原库不变
def test_体检全程不改库_三值逐位不变(tmp_db):
    before = db_fingerprint(tmp_db)
    con = open_ro(tmp_db)
    try:
        payload = self_export_payload(con)          # 现库导出件回灌现库＝最坏重叠态
        rep = inspect_payload(payload, con, {"python": {"python/01_x/01_a"}, "sql": set(),
                                             "cpp": set(), "r": set(), "agent_dev": set()})
        with pytest.raises(sqlite3.OperationalError):
            con.execute("INSERT INTO meta (key,value,updated_ts) VALUES ('x','y','z')")
    finally:
        con.close()
    after = db_fingerprint(tmp_db)
    assert before == after, f"只读体检改动了库文件：{before} → {after}"
    assert after["sha256"] == before["sha256"]
    # 自检态应当"全表都是重叠面"，这才叫把新增/更新/冲突列全了
    assert all(v["insert_new"] == 0 for v in rep["merge"].values()), rep["merge"]
    assert sum(v["overwrite_same_key"] + v["conflict_value_differs"]
               for v in rep["merge"].values()) > 0


def test_真库只读面_不动生产库一字():
    """对**真** data/progress.db 跑一次完整体检，前后 sha256 必须逐位相同。"""
    prod = ROOT / "data" / "progress.db"
    if not prod.is_file():
        pytest.skip("生产库不在盘上（全新检出），本例无从取证")
    before = hashlib.sha256(prod.read_bytes()).hexdigest()
    mtime_ns = prod.stat().st_mtime_ns
    con = open_ro(prod)
    try:
        rep = inspect_payload(self_export_payload(con), con,
                              {"python": set(), "sql": set(), "cpp": set(),
                               "r": set(), "agent_dev": set()})
    finally:
        con.close()
    assert hashlib.sha256(prod.read_bytes()).hexdigest() == before
    assert prod.stat().st_mtime_ns == mtime_ns, "只读连接把 mtime 刷了——本例口径失效"
    assert rep["merge"], "真库都没扫出行来，说明载荷构造有问题"


def test_业务键覆盖每张被检表():
    assert set(BUSINESS_KEYS) == {"attempts", "learning_events", "rubric_scores",
                                  "problems_status", "review_state", "meta"}
