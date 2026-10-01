# -*- coding: utf-8 -*-
"""learn path 页两个事件写点的**真库面**去重桩（l923-33，纯补测试，零改生产码）。

🔴 先记一条对卷宗的否证：任务书说"`tests/` 全目录零引用这两个事件"，**不成立**——
`tests/test_ui_behavior.py:185-189` 已经在做去重断言（连调两次 `_emit_path_started`、
再连调两次 `_emit_milestone_completed`，然后 `[e[0] for e in dao.events]` 必须是
`["path_started", "path_milestone_completed"]`）。所以本件不是"零测面钉桩"，
**改判为"真库面补测＋组合矩阵"**，与既有件的分工如下（避免重复计账）：

| 面 | 既有 `test_ui_behavior.py:163-189` | 本件 |
|---|---|---|
| DAO | 类内 dict 假 DAO（`get_meta`/`set_meta` 走内存） | **真 `ProgressDAO` ＋ 真 `meta`/`learning_events` 表**（tmp 库） |
| 覆盖组合 | 同 path ＋ 同 milestone 各重复一次 | path 之间、milestone 之间、**path×milestone 组合**（钉"键含 path_id"） |
| 脏库 | 无 | meta 已有键而事件表为空 ⇒ 零事件（现状不补发） |
| 去重依据 | 测不出"meta 还是进程缓存" | **删掉 meta 行必须重发**（钉 docstring 里 "via meta table" 那半句） |
| 时间戳 | 不锁 | 不锁（完成标准②：计数断言一律不引字面时间戳） |

锚点开工前复核（2026-09-24，全部逐字命中、零漂移）：
  - `ui/pages/path.py:202` def _emit_path_started(...)
  - `ui/pages/path.py:203` docstring 原文 Emit path_started once per path (dedup via meta table)
  - `ui/pages/path.py:216` dao.emit_event("path_milestone_completed", path_id=..., milestone_id=...)
  - meta 键形如 `path_started:{path_id}`、`milestone_done:{path_id}:{milestone_id}`
与 l923-30 的边界：那单出的是 emit_event 全域 census 档，本件只钉 path 页这两写点。

复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_path_event_dedup.py -q
变异自证见 tmp/l923-33-mutate.py（摘掉 `if dao.get_meta(key)` 后 3 例转红，
还原后 target 逐字节相同：sha256 前 12 位 bc1e766f9e53）。
只连 tmp_path 下的一次性库，不碰真实 data/、不触 streamlit 运行时、不联网。
"""
import os

import pytest

import ui.pages.path as path_page
from core.progress import ProgressDAO

EVENT_PATH_STARTED = "path_started"
EVENT_MILESTONE_DONE = "path_milestone_completed"


def _count_events(dao, event_type):
    """按事件类型数行数——**不锁任何时间戳字面量**（完成标准②）。"""
    return dao.conn.execute(
        "SELECT COUNT(*) FROM learning_events WHERE event_type = ?", (event_type,)
    ).fetchone()[0]


def _meta_value(dao, key):
    return dao.conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()


@pytest.fixture
def dao(tmp_path):
    d = ProgressDAO(str(tmp_path / "path-events.db"))
    yield d
    d.conn.close()


# ── ① path_started：首次落 1 行事件并写 meta，同 path 再调不再发 ──────────────
def test_path_started_首次调用发一条事件并写下meta键(dao):
    assert _count_events(dao, EVENT_PATH_STARTED) == 0, "夹具库必须是空的"

    path_page._emit_path_started(dao, "py-basic")

    assert _count_events(dao, EVENT_PATH_STARTED) == 1
    assert _meta_value(dao, "path_started:py-basic") == ("1",), "去重标记必须落到 meta 表"


def test_path_started_同一路径重复调用不再发第二条(dao):
    path_page._emit_path_started(dao, "py-basic")
    for _ in range(3):
        path_page._emit_path_started(dao, "py-basic")

    assert _count_events(dao, EVENT_PATH_STARTED) == 1, "一次性语义被破坏：重复调用又发了"
    assert _meta_value(dao, "path_started:py-basic") == ("1",)


def test_path_started_不同路径互不干扰(dao):
    path_page._emit_path_started(dao, "py-basic")
    path_page._emit_path_started(dao, "sql-basic")
    path_page._emit_path_started(dao, "sql-basic")

    assert _count_events(dao, EVENT_PATH_STARTED) == 2, "两条路径各 1 次"
    assert _meta_value(dao, "path_started:py-basic") == ("1",)
    assert _meta_value(dao, "path_started:sql-basic") == ("1",)


def test_path_started_去重靠meta表而非进程内缓存(dao):
    """🔴 判别力自证：meta 清掉后必须**重新发**一条。

    若实现把一次性记在进程级 memo／@st.cache_data 上而 meta 只是装饰，
    上两条用例照样绿，本条会红 ⇒ 这条断言把 docstring 里"via meta table"
    那半句也钉住，顺带排除"换一个 DAO 连接就重复发"的假安全感。
    """
    path_page._emit_path_started(dao, "py-basic")
    assert _count_events(dao, EVENT_PATH_STARTED) == 1

    with dao.conn:
        dao.conn.execute("DELETE FROM meta WHERE key = ?", ("path_started:py-basic",))

    path_page._emit_path_started(dao, "py-basic")
    assert _count_events(dao, EVENT_PATH_STARTED) == 2, "meta 是唯一的去重依据"


def test_path_started_脏库夹具_meta已存在则零事件(dao):
    """③ 完成标准：meta 键已存在（历史上写过、事件行缺失）时**零事件**。

    这模拟"事件表被清过但 meta 没清"的脏库——现状是不补发，
    本例把该现状钉成断言：真要让 path_started 可重放，改动必连带本例。
    """
    dao.set_meta("path_started:py-basic", "1")
    assert _count_events(dao, EVENT_PATH_STARTED) == 0

    path_page._emit_path_started(dao, "py-basic")

    assert _count_events(dao, EVENT_PATH_STARTED) == 0
    assert _meta_value(dao, "path_started:py-basic") == ("1",), "不该被覆盖成新值以外的东西"


# ── ② milestone_completed：键含 milestone_id，跨 milestone 互不影响 ────────────
def test_milestone_同一milestone重复调用只发一条(dao):
    path_page._emit_milestone_completed(dao, "py-basic", "m1")
    path_page._emit_milestone_completed(dao, "py-basic", "m1")

    assert _count_events(dao, EVENT_MILESTONE_DONE) == 1
    assert _meta_value(dao, "milestone_done:py-basic:m1") == ("1",)


def test_milestone_跨milestone互不干扰且路径不串味(dao):
    path_page._emit_milestone_completed(dao, "py-basic", "m1")
    path_page._emit_milestone_completed(dao, "py-basic", "m2")
    path_page._emit_milestone_completed(dao, "py-basic", "m2")
    path_page._emit_milestone_completed(dao, "sql-basic", "m1")

    assert _count_events(dao, EVENT_MILESTONE_DONE) == 3, "m1/m2/py 与 m1/sql 各自独立"
    rows = dao.conn.execute(
        "SELECT path_id, milestone_id, COUNT(*) FROM learning_events "
        "WHERE event_type = ? GROUP BY path_id, milestone_id ORDER BY path_id, milestone_id",
        (EVENT_MILESTONE_DONE,),
    ).fetchall()
    assert rows == [("py-basic", "m1", 1), ("py-basic", "m2", 1), ("sql-basic", "m1", 1)], (
        "去重键必须是 (path_id, milestone_id) 组合——"
        "若实现漏了 path_id，py-basic/m1 与 sql-basic/m1 会互相吞掉一条"
    )


def test_milestone_脏库夹具_仅milestone键已存在时零事件(dao):
    dao.set_meta("milestone_done:py-basic:m1", "1")

    path_page._emit_milestone_completed(dao, "py-basic", "m1")
    path_page._emit_milestone_completed(dao, "py-basic", "m2")

    assert _count_events(dao, EVENT_MILESTONE_DONE) == 1, "m1 被 meta 挡住，只有 m2 发出"
    assert _meta_value(dao, "milestone_done:py-basic:m2") == ("1",)


def test_两写点事件类型不混用(dao):
    """两个函数各发各的 event_type，且互不消费对方的 meta 键。"""
    path_page._emit_path_started(dao, "py-basic")
    path_page._emit_milestone_completed(dao, "py-basic", "m1")

    assert _count_events(dao, EVENT_PATH_STARTED) == 1
    assert _count_events(dao, EVENT_MILESTONE_DONE) == 1
    # path_started 的键不能被 milestone 复用（否则同路径第二个 milestone 会被吞）
    assert _meta_value(dao, "path_started:py-basic") == ("1",)
    assert _meta_value(dao, "milestone_done:py-basic") is None


def test_桩连的是独立临时库不碰真实data(dao, tmp_path):
    """自证隔离：本件所有写点都落在 tmp_path 下的一次性库里。"""
    assert dao.db_path.startswith(str(tmp_path)), "夹具库必须在 tmp_path 下"
    assert dao.db_path.endswith("path-events.db")
    assert os.sep + "data" + os.sep not in dao.db_path, "绝不连真实 data/"


# ── l930-01：两枚裸 emit 的失败注入桩（甲案守卫回归：emit 抛异常不得炸调用方，meta 不得残留半态）──

class _ExplodingEmitDao:
    """emit_event 必抛、其余透传（真 DAO 包装）。"""

    def __init__(self, dao):
        self._dao = dao
        self.events = []

    def get_meta(self, key):
        return self._dao.get_meta(key)

    def set_meta(self, key, value):
        return self._dao.set_meta(key, value)

    def emit_event(self, event, **kwargs):
        self.events.append(event)
        raise RuntimeError("injected emit failure (l930-01)")


def test_l930_01_emit_failure_does_not_raise_and_leaves_no_meta(tmp_path):
    """emit 抛异常 → 调用方不炸（异常被守卫吞掉转日志），且 meta 键不写入（半态零残留）。"""
    dao = ProgressDAO(str(tmp_path / "probe.db"))
    exploding = _ExplodingEmitDao(dao)
    # 不抛即守卫生效
    path_page._emit_path_started(exploding, "p1")
    path_page._emit_milestone_completed(exploding, "p1", "m1")
    assert dao.get_meta("path_started:p1") is None, "emit 失败后不得写 meta（保持「下次可重发」语义）"
    assert dao.get_meta("milestone_done:p1:m1") is None
    assert exploding.events == ["path_started", "path_milestone_completed"]


def test_l930_01_emit_recovers_on_next_call(tmp_path):
    """失败后下一次（DAO 恢复正常）应成功发出事件并写 meta——守卫不得吞掉后续成功路径。"""
    dao = ProgressDAO(str(tmp_path / "probe2.db"))
    exploding = _ExplodingEmitDao(dao)
    path_page._emit_path_started(exploding, "p1")  # 第一次失败
    path_page._emit_path_started(dao, "p1")        # 第二次换真 DAO 成功
    n = dao.conn.execute("SELECT COUNT(*) FROM learning_events WHERE event_type='path_started'").fetchone()[0]
    assert n == 1, '恢复后应真发一次'
    assert dao.get_meta("path_started:p1") == "1"
    # 第三次再调（真 DAO）→ 去重生效不再发
    path_page._emit_path_started(dao, "p1")
    n2 = dao.conn.execute("SELECT COUNT(*) FROM learning_events WHERE event_type='path_started'").fetchone()[0]
    assert n2 == 1, '去重后不得重发'
