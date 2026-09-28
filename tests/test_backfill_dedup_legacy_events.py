# -*- coding: utf-8 -*-
"""l927-13：learning_events 回填去重缺陷的回归用例（154239 §D 方案落地）。

缺陷（原文见 `zcode-bridge/done/20260925-154239-abdf.result.md` §D）：
`scripts/backfill_events.py` 的 `already_backfilled` 以 payload 里的 `attempt_id`
为**唯一**去重键。但历史事件行有两类都不带 attempt_id：
  ① 2026-07 年代那次 `--apply` 留下的行（`attempt_submitted` 的 payload 只有
     `{"passed": true}`，`problem_passed`/`problem_failed` 的 payload 为 NULL）；
  ② 生产实时写入的同型行（`core/judge.py:203-206` 的 `emit_event` 至今不带 attempt_id）。
⇒ 键缺失 ⇒ 这类行**永远判不出重复** ⇒ 任何人再跑一次 `--apply` 就把既有 attempts
整批再复制一遍事件（2026-09-25 的 +30 行／`local_date='2026-05-30'` 变成 60 行即此）。

修复口径（分层双键，本文件钉的就是它）：
  ① 带 attempt_id 的行 → 精确键 `(event_type, lang, problem_id, attempt_id)`；
  ② 不带 attempt_id 的老行 → 退化键 `(event_type, lang, problem_id, local_date)` 的
     **计数额度**（一行一条额度，命中即消费）。
为什么是"额度"而不是"按日期判重"：老库同题同天多次提交在旧口径下是**多行**，
直接按日期去重会把它们误判成重复、少补记录（源码原注释的诉求）；配额度后
老行覆盖不到的那几次提交照样补插，且补插的行带 attempt_id，下轮走精确键。

隔离硬口径（本仓 2026-09-25 出过 +30 行生产库事故，见上述 result 置顶节）：
  * 每个用例都**显式传 `db_path=tmp_path/...`**，`backfill()` 不再有"默认库"这条暗道；
  * 不使用 `monkeypatch.undo()` 型 fixture，也不靠 `LS_PROGRESS_DB` 那道缝
    （当年事故就是 fixture 的 `undo()` 把 env 连带撤掉 ⇒ 无参 `ProgressDAO()` 退回生产库）；
  * 本文件的 `apply=True` 只会落在 tmp_path 下的临时库；
    `core/progress.py:_guard_default_db_in_tests`（A5① 闸）会拒掉 pytest 态下的无参构造，
    本文件用一条用例当场钉住这条闸（`test_回填必须显式指库且pytest态拒开默认库`）。

复跑：
    cd D:/code/learning-system
    PYTHONIOENCODING=utf-8 python -m pytest tests/test_backfill_dedup_legacy_events.py -q
"""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.progress import ProgressDAO            # noqa: E402
from scripts import backfill_events as B         # noqa: E402

PROD_DB = str((ROOT / "data" / "progress.db").resolve())

# 三条 attempt：id 1/2 同题同天（本地日相同）——这是"按日期去重会丢记录"的那位乘客
ATTEMPTS = [
    (1, "python", "python/l92713/a", True, "2026-07-04 21:11:00"),
    (2, "python", "python/l92713/a", False, "2026-07-04 22:05:00"),
    (3, "sql", "sql/l92713/b", True, "2026-07-05 02:00:00"),
]


def _db(tmp_path, name="l92713.db"):
    """建一份一次性库并把 attempts 铺好（显式路径，绝不走默认库）。"""
    path = str(tmp_path / name)
    dao = ProgressDAO(path)
    assert os.path.abspath(path) != PROD_DB, "夹具库路径撞上了生产库"
    with dao.conn:
        for _id, lang, pid, passed, ts in ATTEMPTS:
            dao.conn.execute(
                "INSERT INTO attempts(id, lang, problem_id, code, passed, ai_feedback, ts) "
                "VALUES(?,?,?,?,?,?,?)",
                (_id, lang, pid, "print(1)", 1 if passed else 0, "", ts))
    return dao


def _add_legacy(dao, rows):
    """按 §D 的**老行形态**直接造历史事件：payload 不带 attempt_id、结果事件 payload 为 NULL。

    这里刻意绕开生产写入器——要复现的就是"payload 还没有 attempt_id 的年代"写下的行形状，
    生产码今天已经不再产出它（`emit_event` 仍不带 attempt_id，见文件头 ②），
    用直插才能把这一形态钉死。落库日 `local_date` 走生产函数 `_utc_to_local_date`，
    与当年回填的换算口径一致。
    """
    with dao.conn:
        for _id, lang, pid, passed, ts in rows:
            local_date = B._utc_to_local_date(ts)
            dao.conn.execute(
                "INSERT INTO learning_events"
                "(event_type, lang, topic_id, problem_id, path_id, milestone_id, payload_json, local_date)"
                " VALUES(?,?,?,?,?,?,?,?)",
                ("attempt_submitted", lang, None, pid, None, None,
                 json.dumps({"passed": bool(passed)}, ensure_ascii=False), local_date))
            dao.conn.execute(
                "INSERT INTO learning_events"
                "(event_type, lang, topic_id, problem_id, path_id, milestone_id, payload_json, local_date)"
                " VALUES(?,?,?,?,?,?,?,?)",
                ("problem_passed" if passed else "problem_failed",
                 lang, None, pid, None, None, None, local_date))


# ---------------------------------------------------------------------------
# 判据①：缺陷形态（老行不带 attempt_id 时，重跑必须**不再**复制行）
# ---------------------------------------------------------------------------
def test_老行不带attempt_id时重跑回填不再复制(tmp_path):
    """§D 主案：库里 6 行老式回填产物（3 attempt × 2 事件），payload 全无 attempt_id。

    修复前实测：`duplicate_skipped=0`、`events_to_create=6`、`created=6` ⇒ 6 行变 12 行
    （一次性复现器 `tmp/qoder-executor-20260928-0145-learn50/w40_repro_dedup.py`
    在 HEAD 版代码上跑出 6→12，`local_date='2026-07-05'` 由 6 行变 12 行）。
    修复后：0 新增行、行数不变。
    """
    dao = _db(tmp_path)
    _add_legacy(dao, ATTEMPTS)
    before = dao.event_count()
    assert before == 6, f"夹具没铺出老行：{before}"
    assert dao.conn.execute(
        "SELECT COUNT(*) FROM learning_events WHERE payload_json LIKE '%attempt_id%'").fetchone()[0] == 0, \
        "夹具铺出的行带了 attempt_id ⇒ 不是在复现 §D 形态"

    try:
        s1 = B.backfill(apply=True, json_output=True, db_path=dao.db_path)
        after1 = dao.event_count()
        assert s1["events_before"] == 6
        assert s1["legacy_events_without_attempt_id"] == 6, "老行没被识别为退化键"
        assert s1["events_to_create"] == 0, f"仍打算复制 {s1['events_to_create']} 行"
        assert s1["created"] == 0
        assert after1 == before, f"重跑复制了行：{before} -> {after1}"
    finally:
        dao.close()


def test_干跑同样不复制且一行不写(tmp_path):
    """dry-run 的读判据要与 apply 一致（`events_to_create=0`），且 dry-run 绝不写库。

    这一条是给"回填前先看看"的常规操作兜底的：修复前 dry-run 就自报要建 6 行，
    操作员看见 6 才敢 --apply，于是翻倍——dry-run 与 apply 口径必须同时修好。
    """
    dao = _db(tmp_path)
    _add_legacy(dao, ATTEMPTS)
    try:
        dry = B.backfill(apply=False, json_output=True, db_path=dao.db_path)
        assert dry["mode"] == "dry_run"
        assert dry["events_to_create"] == 0, f"dry-run 仍报要建 {dry['events_to_create']} 行"
        assert dry["created"] == 0
        assert dao.event_count() == 6, "dry-run 写了库"
    finally:
        dao.close()


# ---------------------------------------------------------------------------
# 判据③：幂等复跑零新增行（连续多轮 + 混合新老两代行）
# ---------------------------------------------------------------------------
def test_连续三轮回填幂等且第二轮起零新增(tmp_path):
    dao = _db(tmp_path)
    _add_legacy(dao, ATTEMPTS)
    try:
        counts = [dao.event_count()]
        for _ in range(3):
            s = B.backfill(apply=True, json_output=True, db_path=dao.db_path)
            counts.append(dao.event_count())
            assert s["created"] == 0, f"第 {len(counts)-1} 轮新增了 {s['created']} 行"
        assert len(set(counts)) == 1, f"行数发生漂移：{counts}"
        assert counts[0] == 6
    finally:
        dao.close()


def test_混合两代行的库幂等(tmp_path):
    """库里同时有：① 新代行（attempt 1 已回填，payload 带 attempt_id）
    ② 老代行（attempt 2 只有一行 attempt_submitted 不带 attempt_id）
    ③ 完全没回填过的 attempt 3。

    期望不重不漏：attempt 1 的两行已存在 ⇒ 跳过（走精确键）；
    attempt 2 的 attempt_submitted 被老行额度吃掉，problem_passed/failed 没有对应老行 ⇒ 补 1 行；
    attempt 3 缺两行 ⇒ 补 2 行。共补 3 行；再跑一轮补 0 行。
    """
    dao = _db(tmp_path)
    ld1 = B._utc_to_local_date(ATTEMPTS[0][4])
    with dao.conn:
        dao.conn.executemany(
            "INSERT INTO learning_events"
            "(event_type, lang, topic_id, problem_id, path_id, milestone_id, payload_json, local_date)"
            " VALUES(?,?,?,?,?,?,?,?)",
            [("attempt_submitted", "python", None, "python/l92713/a", None, None,
              json.dumps({"passed": True, "attempt_id": 1}), ld1),
             ("problem_passed", "python", None, "python/l92713/a", None, None,
              json.dumps({"attempt_id": 1}), ld1),
             # 老代：只有提交行，没有结果行
             ("attempt_submitted", "python", None, "python/l92713/a", None, None,
              json.dumps({"passed": True}), ld1)])
    assert dao.event_count() == 3
    try:
        s = B.backfill(apply=True, json_output=True, db_path=dao.db_path)
        # attempt 2 的结果行（problem_failed）+ attempt 3 的两行
        assert s["duplicate_skipped"] == 3, f"应跳过 3 笔（2 精确 + 1 老行额度）：{s}"
        assert s["dedup_exact_keys"] == 2
        assert s["legacy_events_without_attempt_id"] == 1
        assert s["events_to_create"] == 3, f"补插笔数不对：{s}"
        assert s["created"] == 3
        assert dao.event_count() == 6
        again = B.backfill(apply=True, json_output=True, db_path=dao.db_path)
        assert again["events_to_create"] == 0 and again["created"] == 0
        assert dao.event_count() == 6, f"第二轮复制了行：{dao.event_count()}"
    finally:
        dao.close()


# ---------------------------------------------------------------------------
# 反向护栏：修 §D 不能把"同题同天多次提交"的记录丢掉（旧注释的诉求）
# ---------------------------------------------------------------------------
def test_同题同天多次提交不被日期口径吞掉(tmp_path):
    """只有 1 行老行（代表 3 次同日提交里的第 1 次）时，另两次必须补插。

    判据①的另一半：把去重键**整体**退化成 `(event_type, lang, problem_id, local_date)`
    （§D 建议的字面写法）会让这一例红——它会吞掉 attempt 2/3 的提交记录。
    所以实现取"额度"而不是"按日期判重"，本例就是那枚额度存在的理由。
    """
    dao = _db(tmp_path)
    _add_legacy(dao, ATTEMPTS[:1])          # 只铺 attempt 1 的两行老行
    assert dao.event_count() == 2
    try:
        s = B.backfill(apply=True, json_output=True, db_path=dao.db_path)
        assert s["created"] == 4, f"同题同天的另两次提交被吞了：{s}"
        assert dao.event_count() == 6
        per_key = dao.conn.execute(
            "SELECT problem_id, COUNT(*) FROM learning_events "
            "WHERE problem_id='python/l92713/a' GROUP BY 1").fetchall()
        assert dict(per_key)["python/l92713/a"] == 4, (
            f"python/l92713/a 有 2 次提交应落 4 行：{per_key}")
        assert B.backfill(apply=True, json_output=True,
                          db_path=dao.db_path)["created"] == 0, "补齐后第二轮又复制了"
        assert dao.event_count() == 6
    finally:
        dao.close()


def test_坏payload与NULLpayload都算老行额度(tmp_path):
    """`payload_json` 是 NULL（生产 `emit_event` 的结果事件）还是坏 JSON（`{"passed": true`）
    都得进退化键——漏掉坏 JSON 那一支，重跑就会把那一行再复制一遍。
    """
    dao = _db(tmp_path)
    ld = B._utc_to_local_date(ATTEMPTS[2][4])
    with dao.conn:
        dao.conn.executemany(
            "INSERT INTO learning_events"
            "(event_type, lang, topic_id, problem_id, path_id, milestone_id, payload_json, local_date)"
            " VALUES(?,?,?,?,?,?,?,?)",
            [("attempt_submitted", "sql", None, "sql/l92713/b", None, None,
              '{"passed": true', ld),                      # 坏 JSON ⇒ 读不出 attempt_id
             ("problem_passed", "sql", None, "sql/l92713/b", None, None, None, ld)])  # NULL
    assert dao.event_count() == 2
    try:
        s = B.backfill(apply=True, json_output=True, db_path=dao.db_path)
        assert s["legacy_events_without_attempt_id"] == 2
        # 这两行只代表 attempt 3；attempt 1/2（python 同题同天两次）仍须各补 2 行 ⇒ 补 4 行。
        # 若坏 JSON 那一支没进退化键，这里会是 6 行（sql/b 那两行被再复制一遍 ⇒ 热力图虚高）。
        assert s["created"] == 4, f"补插笔数不对（6 说明老行被复制了）：{s}"
        assert s["duplicate_skipped"] == 2
        sql_rows = dao.conn.execute(
            "SELECT COUNT(*) FROM learning_events WHERE problem_id='sql/l92713/b'").fetchone()[0]
        assert sql_rows == 2, f"sql/b 的两行老行被复制成 {sql_rows} 行"
        assert dao.event_count() == 6
        again = B.backfill(apply=True, json_output=True, db_path=dao.db_path)
        assert again["created"] == 0, f"第二轮复制了 {again['created']} 行：{again}"
        assert dao.event_count() == 6
    finally:
        dao.close()


def test_非回填事件类型不参与去重(tmp_path):
    """`achievement_unlocked` 之类不在回填管辖内：它的行数与 payload 形态不得影响结果，
    也不能被回填吃掉/复制。"""
    dao = _db(tmp_path)
    with dao.conn:
        dao.conn.execute(
            "INSERT INTO learning_events"
            "(event_type, lang, topic_id, problem_id, path_id, milestone_id, payload_json, local_date)"
            " VALUES(?,?,?,?,?,?,?,?)",
            ("achievement_unlocked", None, None, None, None, None,
             json.dumps({"achievement_id": "first_blood"}),
             B._utc_to_local_date(ATTEMPTS[0][4])))
    try:
        s = B.backfill(apply=True, json_output=True, db_path=dao.db_path)
        assert s["created"] == 6, f"6 条事件（3 attempt × 2）应全建：{s}"
        kinds = {r[0] for r in dao.conn.execute(
            "SELECT DISTINCT event_type FROM learning_events")}
        assert kinds == {"achievement_unlocked", "attempt_submitted",
                         "problem_passed", "problem_failed"}
        assert dao.conn.execute("SELECT COUNT(*) FROM learning_events WHERE event_type="
                               "'achievement_unlocked'").fetchone()[0] == 1
        assert B.backfill(apply=True, json_output=True,
                          db_path=dao.db_path)["created"] == 0
        assert dao.event_count() == 7
    finally:
        dao.close()


# ---------------------------------------------------------------------------
# 隔离自证：本文件所有写都落在 tmp_path，pytest 态下默认库根本开不了
# ---------------------------------------------------------------------------
def test_回填必须显式指库且pytest态拒开默认库(tmp_path):
    """① `backfill(db_path=...)` 确实按传入路径建库（新参数生效）；
    ② 不传库、又想用无参构造时，A5① 闸必须当场抛错——这是"判据③只能在临时库上跑"
       这条硬约束的机制保障，不是口头约定；
    ③ 生产库路径只**读模块常量**核对，绝不构造无参 ProgressDAO 去探它
       （20260925-154239 就为了读一个 `.db_path` 而读写打开了生产库、长出侧车）。"""
    # ② 无参构造在 pytest 态被拒（先把 env 覆盖摘干净，确认拒的是"默认库"而不是别的）
    saved = os.environ.pop("LS_PROGRESS_DB", None)
    try:
        with pytest.raises(RuntimeError, match="测试态禁开默认生产库"):
            ProgressDAO()
        # 显式指向 tmp 则放行——证明本文件的每一处 apply 都走的是这条路
        assert os.path.abspath(
            ProgressDAO(str(tmp_path / "guard_probe.db")).db_path) == \
            os.path.abspath(str(tmp_path / "guard_probe.db"))
    finally:
        if saved is not None:
            os.environ["LS_PROGRESS_DB"] = saved

    # ①③ 显式 db_path 生效，且落库确实只在这一份文件里
    path = str(tmp_path / "explicit_only.db")
    seed = _db(tmp_path, name="explicit_only.db")
    seed.close()
    s = B.backfill(apply=True, json_output=True, db_path=path)
    assert s["created"] == 6 and s["events_after"] == 6
    assert os.path.abspath(path) != PROD_DB
    probe = ProgressDAO(path)
    try:
        assert os.path.abspath(probe.db_path) == os.path.abspath(path)
        assert probe.conn.execute("SELECT COUNT(*) FROM learning_events").fetchone()[0] == 6
    finally:
        probe.close()


def test_默认库常量仍指向生产路径_本文件隔离论证的前提():
    """把"我们没碰生产库"钉成一条断言而非口头承诺：
    只读 `core.progress._DEFAULT_DB` 这个模块常量、不建立任何连接。
    若哪天默认库不再指向 `data/progress.db`，本文件"临时库＝唯一落点"的前提就变了，先在这里红。"""
    import core.progress as prog
    assert os.path.abspath(prog._DEFAULT_DB) == PROD_DB

