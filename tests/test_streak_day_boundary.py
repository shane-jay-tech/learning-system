"""跨日 / 时区 / 补签 / 连续天数重置 —— daily_streak 与回填/热力图日期口径的模拟时间钉桩。

班：qoder-executor-20260925-2030-learn39 · 单号 20260925-154239-abdf（风险档 B，工作类型 test）

卷宗验收：「以固定时区和模拟时间测试；不修改真实用户连续记录」。

四条落地口径（收窄处均记入 result「证据」）：
  1. **固定时区**：POSIX 用 `time.tzset()` 真设固定 zone；win32 的 `tzset` **不存在**，
     故本文件**不引用他班结论**，而是**现场实测**设 `TZ` 是否改变 SQLite 的 `'localtime'` 偏移，
     再把会话初实测偏移钉成常量（`fixed_offset_seconds`）。
     任何情况下都**不继承环境挂钟**参与期望值计算。
  2. **模拟时间**：`daily_streak` / `emit_event` 每次调用内部现取 `datetime.date.today()`，
     生产码不改 ⇒ 由 `clock` fixture 在**单个调用窗口内**注入模拟今日，退出即还原并断言还原成功。
     注入自带反证：模拟日与任何真实日不同时，注入失效则读数必不同 ⇒ 断言能区分。
  3. **「补签」在本仓不是实体**（`补签`/`补卡`/`make_up`/`retroactive` 代码侧 0 命中）。在世最近邻是
     `scripts/backfill_events.py` ⇒ 回填测试打它的**真生产函数** `_utc_to_local_date()`
     与 `backfill(apply=True)`，数据一律经生产写入器建，**不写任何直接 INSERT**。
  4. 隔离：所有库显式 `:memory:` / `tmp_path`；跑 `backfill()` 用 `LS_PROGRESS_DB` 指开
     （它内部是 `ProgressDAO()` 无参构造，会退回默认生产库＝14 行幽灵数据那次的成因）。
"""
import hashlib
import os
import re
import sqlite3
import sys
import time
from contextlib import contextmanager
import datetime as _dtmod                      # 模块本体：monkeypatch 的目标
from datetime import date as real_date
from datetime import datetime, timedelta, timezone

import pytest

from core.progress import ProgressDAO

UTC_FMT = "%Y-%m-%d %H:%M:%S"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# POSIX 的 TZ 语义反号："UTC-8" 表示 UTC+8
POSIX_TZ = "UTC-8"
POSIX_OFFSET = timedelta(hours=8)


def _probe_sqlite_offset_seconds():
    """现场实测 SQLite 'localtime' 相对 UTC 的秒偏移（独立连接，只看当下）。"""
    c = sqlite3.connect(":memory:")
    try:
        row = c.execute(
            "SELECT (julianday('2026-06-01 12:00:00','localtime') "
            "      - julianday('2026-06-01 12:00:00')) * 86400.0").fetchone()
        return int(round(row[0]))
    finally:
        c.close()


@pytest.fixture(scope="session")
def fixed_offset_seconds():
    """把时区钉成常量，**不继承环境挂钟**。POSIX 真设；win32 先实测 TZ 是否有效再决定。"""
    if os.name == "posix":
        os.environ["TZ"] = POSIX_TZ
        time.tzset()
        off = _probe_sqlite_offset_seconds()
        assert off == int(POSIX_OFFSET.total_seconds()), \
            f"POSIX 下 TZ={POSIX_TZ} 应得偏移 28800s，实得 {off}s ⇒ 固定时区失效"
        return off
    # win32：TZ 无效（下面 clock fixture 会逐次实测自证），取会话初实测值钉住
    os.environ.pop("TZ", None)
    return _probe_sqlite_offset_seconds()


class _FakeDate(real_date):
    """只改 today()；fromisoformat/比较/哈希全部继承真 date。"""
    _sim = None

    @classmethod
    def today(cls):
        return cls._sim


class Clock:
    """模拟时钟：在 with 窗口内让生产码的"今日"等于指定日期。

    🔴 **绝不用 monkeypatch 实现**。本类第一版用 `mp.setattr` + `mp.undo()`，
    而 `undo()` 会回滚该 fixture 实例上**全部**登记项 —— 包括用例自己
    `setenv("LS_PROGRESS_DB")` 那道隔离闸 ⇒ 出窗后环境变量被悄悄清掉，
    随后的 `backfill(apply=True)` 直写生产库（把既有 attempts 又复制了一遍事件，
    事故行数与后续处置记在 outbox/20260925-154239-abdf.result.md，本文件不写死数字）。
    现改为手工属性换入换出，只碰 `datetime.date` 这一个名字，零附带损伤。
    """

    def __init__(self, offset_seconds):
        self.offset = offset_seconds
        self.zone = timezone(timedelta(seconds=offset_seconds))

    @contextmanager
    def at(self, d):
        prev = _dtmod.date
        _FakeDate._sim = real_date(d.year, d.month, d.day)
        _dtmod.date = _FakeDate
        try:
            assert _dtmod.date.today() == d, "时钟未注入"
            yield d
        finally:
            _dtmod.date = prev
            _FakeDate._sim = None
            assert _dtmod.date is real_date, "时钟未还原 ⇒ 会污染同 worker 其它用例"

    def streak_at(self, dao, d):
        with self.at(d):
            dao._clear_memo()          # daily_streak 带 3s memo，读前必须清
            return dao.daily_streak()

    def to_local(self, ts_utc):
        """UTC 字符串 → 固定时区下的本地 ISO 日（期望值纯由常量推导）。"""
        return (datetime.strptime(ts_utc, UTC_FMT)
                .replace(tzinfo=timezone.utc).astimezone(self.zone).date().isoformat())


@pytest.fixture
def clock(fixed_offset_seconds):
    c = Clock(fixed_offset_seconds)
    if os.name != "posix":
        # 一手实测（不引用他班结论）：win32 下设 TZ 到底改不改偏移
        base = _probe_sqlite_offset_seconds()
        saved = os.environ.get("TZ")
        try:
            for tz in ("America/Los_Angeles", "UTC", "Asia/Kolkata"):
                os.environ["TZ"] = tz
                assert _probe_sqlite_offset_seconds() == base == c.offset, \
                    f"本机 TZ={tz} 竟改变了偏移 ⇒ 应改走真设时区分支"
        finally:
            if saved is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = saved
    return c


# --------------------------------------------------------------------------
# 夹具
# --------------------------------------------------------------------------
def _dao(tmp_path=None):
    return (ProgressDAO(":memory:") if tmp_path is None
            else ProgressDAO(str(tmp_path / "abdf_isolated_progress.db")))


def _ts_at_local(dao, target_local, hh=0, mm=30):
    """造 UTC 时间戳，使 DATE(ts,'localtime') 恰为 target_local（入参是模拟日期）。
    默认取本地 00:30 ⇒ 偏移≠0 时其 UTC 日历日≠本地日历日，才谈得上跨日。"""
    off = timedelta(seconds=_sqlite_offset(dao))
    local = datetime(target_local.year, target_local.month, target_local.day,
                     hh, mm, tzinfo=timezone(off))
    return local.astimezone(timezone.utc).strftime(UTC_FMT)


def _sqlite_offset(dao):
    return _probe_sqlite_offset_seconds() if dao is None else int(round(
        dao.conn.execute("SELECT (julianday('2026-06-01 12:00:00','localtime') "
                         "- julianday('2026-06-01 12:00:00')) * 86400.0").fetchone()[0]))


def _submit(dao, pid, passed=True):
    """生产写入路径：judge._record_attempt → record_attempt_and_status + update_review_state
    + emit_event(attempt_submitted / problem_passed|failed)。显式传 dao，绝不触默认库。"""
    from core import judge
    judge._record_attempt("python", pid, "print(1)", passed, "", dao, 2)


def _submit_at(dao, pid, local_day, hh=0, mm=30):
    """建一行"落在指定**模拟**本地日"的作答记录，全程走生产路径，不写裸 INSERT/UPDATE。

    链路：`judge._record_attempt`（生产写入器）在暂存库产生真实行 →
    `data_portability.export_all` 导出 → 改写包内 `attempts.ts`
    （ts 是该生产导入路径的**合法入参列**，用于回放历史数据）→
    `import_all` 落进目标库。
    之所以必须经过这条路径：`attempts.ts` 的 `DEFAULT CURRENT_TIMESTAMP`
    在生产写入器里没有任何指定历史时刻的入口。
    """
    from core.data_portability import export_all, import_all
    staging = ProgressDAO(":memory:")
    _submit(staging, pid)
    payload = export_all(staging)
    for row in payload["data"]["attempts"]:
        row["ts"] = _ts_at_local(staging, local_day, hh, mm)
    import_all(dao, payload)
    staging.close()
    dao._clear_memo()


def _seed(dao, days, prefix="r"):
    for i, d in enumerate(days):
        _submit_at(dao, f"python/abdf_case/{prefix}{i}", d)


def _utc_bucket_days(dao):
    """"错误实现"的归桶面：取 ts 前 10 位（＝按 UTC 日归桶）。"""
    return {r[0][:10] for r in dao.conn.execute("SELECT ts FROM attempts")}


def _local_bucket_days(dao):
    """production 的归桶面（同一条 SQL）。"""
    return {r[0] for r in dao.conn.execute(
        "SELECT DISTINCT DATE(ts, 'localtime') FROM attempts")}


def _streak_ref(days_iso, today):
    """daily_streak 的**同构**参考实现（含"今日缺卡则从昨日起算"的宽限规则）。
    只有同构，"按 UTC 归桶会给出不同读数"才是等价比较。"""
    if not days_iso:
        return 0
    if today.isoformat() not in days_iso and \
               (today - timedelta(days=1)).isoformat() not in days_iso:
        return 0
    cur = today if today.isoformat() in days_iso else today - timedelta(days=1)
    n = 0
    while cur.isoformat() in days_iso:
        n += 1
        cur -= timedelta(days=1)
    return n


# --------------------------------------------------------------------------
# 1. 前提与夹具自证
# --------------------------------------------------------------------------
def test_固定时区常量与两套换算同值(tmp_path, clock):
    """期望值只由 fixed_offset 常量推导；SQLite 与 Python 两侧都必须等于它。"""
    dao = _dao(tmp_path)
    assert clock.offset % 900 == 0, f"偏移 {clock.offset}s 非 15 分钟整倍 ⇒ 实测法失真"
    assert _sqlite_offset(dao) == clock.offset, "SQLite 偏移与会话初固定值不一致（挂钟/时区中途变了）"
    assert int(datetime.now().astimezone().utcoffset().total_seconds()) == clock.offset
    ts = "2026-06-15 16:30:00"
    got = dao.conn.execute("SELECT DATE(?, 'localtime')", (ts,)).fetchone()[0]
    assert got == clock.to_local(ts) == "2026-06-16", f"换算三方不同值：sqlite={got} 期望={clock.to_local(ts)}"
    assert dao.conn.execute("SELECT DATE(?)", (ts,)).fetchone()[0] == "2026-06-15"
    dao.close()


def test_夹具把模拟日期的时间戳落到本地日(tmp_path, clock):
    """夹具判别力自证（全用固定模拟日，不取挂钟）。"""
    dao = _dao(tmp_path)
    for sim in [real_date(2026, 1, 1), real_date(2026, 3, 8), real_date(2026, 11, 1),
                real_date(2027, 12, 31), real_date(2028, 2, 29)]:
        ts = _ts_at_local(dao, sim)
        assert dao.conn.execute("SELECT DATE(?, 'localtime')", (ts,)).fetchone()[0] \
            == sim.isoformat(), f"夹具未落到 {sim}"
        assert clock.to_local(ts) == sim.isoformat(), "期望值推导与夹具不自洽"
        if clock.offset != 0:
            assert dao.conn.execute("SELECT DATE(?)", (ts,)).fetchone()[0] != sim.isoformat()
    dao.close()


def test_模拟时钟注入确实改变生产函数读数且退出即还原(tmp_path, clock):
    """注入自身的有牙自证：模拟日固定为 2026-01-01（过去日），
    若注入失效则读数必为 0（真实挂钟远在别处）⇒ 非 0 即证明"模拟时间在驱动生产码"。"""
    dao = _dao(tmp_path)
    sim = real_date(2026, 1, 1)
    for i, d in enumerate([sim, sim - timedelta(1), sim - timedelta(2)]):
        _submit_at(dao, f"python/abdf_case/s{i}", d)
    assert clock.streak_at(dao, sim) == 3, "模拟时钟注入失效或链算错"
    dao._clear_memo()
    assert dao.daily_streak() == 0, "还原后未走真实挂钟 ⇒ 注入残留"
    dao.close()


# --------------------------------------------------------------------------
# 2. 跨日（含计数级判别力）
# --------------------------------------------------------------------------
@pytest.mark.parametrize("sim,label", [
    (real_date(2026, 1, 1), "跨年"),
    (real_date(2026, 3, 1), "跨月"),
    (real_date(2028, 3, 1), "闰年2月29日后跨月"),
    (real_date(2026, 11, 1), "DST回拨相邻日"),
    (real_date(2026, 3, 8), "DST前拨相邻日"),
    (real_date(2026, 12, 31), "年末日"),
])
def test_跨日_按本地日归桶(tmp_path, clock, sim, label):
    dao = _dao(tmp_path)
    prev = sim - timedelta(1)
    for i, d in enumerate([sim, prev]):
        _submit_at(dao, f"python/abdf_case/{label}{i}", d)
    got = clock.streak_at(dao, sim)
    assert got == 2, f"{label}：跨日归桶漂移，实得 {got}"
    local_days = _local_bucket_days(dao)
    assert local_days == {sim.isoformat(), prev.isoformat()}, f"归桶非预期：{local_days}"
    assert _streak_ref(local_days, sim) == got, "参考实现与真码不同构 ⇒ 判别设计作废"
    dao.close()


def test_跨日_同一本地日的两笔不重复计数(tmp_path, clock):
    """计数级判别力所在：同一模拟本地日的 01:00 与 23:00 两笔，
    本地归桶＝1 天；按 UTC 前 10 位归桶会被拆成两天、配同一条宽限规则读出 2。
    ⇒ 本例是真正能抓出"UTC 归桶"实现错误的夹具。"""
    dao = _dao(tmp_path)
    sim = real_date(2026, 9, 9)
    for i, (hh, mm) in enumerate([(1, 0), (23, 0)]):
        _submit_at(dao, f"python/abdf_case/d{i}", sim, hh, mm)
    got = clock.streak_at(dao, sim)
    assert got == 1, f"同日两笔被算成两天：{got}"
    if clock.offset != 0:
        utc_days = _utc_bucket_days(dao)
        assert len(utc_days) == 2, f"夹具退化：UTC 归桶未拆成两天 {utc_days}"
        assert _streak_ref(utc_days, sim) == 2, "同构参考实现未区分 ⇒ 夹具失去判别力"
    dao.close()


def test_跨日_平移型夹具无计数判别力这一事实钉住(tmp_path, clock):
    """诚实记账：整体 −1 天平移会被宽限规则吸收 ⇒ 平移夹具**不能**当判别力证据。
    本例把该事实钉成断言；若哪天宽限规则变了，本例先红，提示复核上一例的设计说明。"""
    dao = _dao(tmp_path)
    if clock.offset == 0:
        pytest.skip("偏移 0，两种归桶恒同（显式记账，非静默）")
    sim = real_date(2026, 4, 18)
    _seed(dao, [sim - timedelta(i) for i in range(3)], prefix="p")
    assert clock.streak_at(dao, sim) == 3
    assert _streak_ref(_utc_bucket_days(dao), sim) == 3, "宽限规则已不吸收平移 ⇒ 判据需复核"
    dao.close()


def test_跨日_本地午夜前后一小时的两笔算两天(tmp_path, clock):
    dao = _dao(tmp_path)
    sim = real_date(2026, 6, 15)
    a = _ts_at_local(dao, sim - timedelta(1), 23, 30)
    b = _ts_at_local(dao, sim, 0, 30)
    assert datetime.strptime(b, UTC_FMT) - datetime.strptime(a, UTC_FMT) == timedelta(hours=1)
    _submit_at(dao, "python/abdf_case/m0", sim - timedelta(1), 23, 30)
    _submit_at(dao, "python/abdf_case/m1", sim, 0, 30)
    assert clock.streak_at(dao, sim) == 2, "日界未生效：本地 23:30 与 00:30 被并成一天"
    dao.close()


# --------------------------------------------------------------------------
# 3. 连续天数重置（全部模拟日，不取挂钟）
# --------------------------------------------------------------------------
SIM = real_date(2026, 7, 20)


def _seed(dao, days, prefix="r"):
    """批量建模拟日数据 —— 逐行走 `_submit_at`（生产写入器 + 生产移植路径），无裸 SQL。"""
    for i, d in enumerate(days):
        _submit_at(dao, f"python/abdf_case/{prefix}{i}", d)


@pytest.mark.parametrize("sim,deltas,expect,label", [
    (SIM, [0, 1, 3, 4], 2, "中间缺一天即断，只留尾段"),
    (SIM, [1, 2, 3], 3, "模拟今日没打卡走昨日起算宽限"),
    (SIM, [2, 3, 4, 5], 0, "今日与昨日均无则归零"),
    (SIM, [], 0, "空表归零"),
    (real_date(2026, 8, 8), list(range(401)), 400, "LIMIT 400 截断超长连续"),
    (real_date(2026, 12, 31), [0, 1, 2], 3, "跨年尾段连续"),
    (real_date(2026, 2, 28), [0, 1], 2, "闰年前夜跨月"),
])
def test_连续天数重置各形态(tmp_path, clock, sim, deltas, expect, label):
    """`LIMIT 400` 是源码注释明记的刻意设计（高频用户先耗掉窗口）⇒ 把上界钉成断言，不改口径。"""
    dao = _dao(tmp_path)
    _seed(dao, [sim - timedelta(d) for d in deltas])
    assert clock.streak_at(dao, sim) == expect, f"{label}：期望 {expect} 实得 {clock.streak_at(dao, sim)}"
    dao.close()


# --------------------------------------------------------------------------
# 4. 补签（名词无实体）→ 改打最近邻实体的真生产路径
# --------------------------------------------------------------------------
def test_补签实体不存在_全仓代码侧无该字段与函数():
    hits = []
    for base in ("core", "ui", "scripts"):
        for dirpath, _dn, fns in os.walk(os.path.join(ROOT, base)):
            for fn in fns:
                if fn.endswith(".py"):
                    p = os.path.join(dirpath, fn)
                    if re.search(r"补签|补卡|make_up|makeup|retroactive",
                                 open(p, encoding="utf-8").read()):
                        hits.append(os.path.relpath(p, ROOT))
    assert hits == [], f"「补签」已有在世实体，本例前提变了：{hits}"


def test_补签最近邻_回填的日期换算函数在固定时区下的实际读数(clock):
    """回填测试打**真生产函数** `backfill_events._utc_to_local_date`：
    逐例断言它把 UTC 时间戳换算成固定时区偏移下的本地日（不测"两式不同值"这种恒真式）。
    期望值纯由 `clock.offset` 常量推导，不取挂钟、不读环境时区。"""
    from scripts.backfill_events import _utc_to_local_date
    off = timedelta(seconds=clock.offset)
    cases = [
        ("2026-06-15 15:30:00", "同一本地日（日界前 30 分）"),
        ("2026-06-15 16:30:00", "跨到次日（日界后 30 分）"),
        ("2026-01-01 00:30:00", "跨年零点后"),
        ("2026-12-31 23:30:00", "年末跨日"),
        ("2026-02-28 12:00:00", "闰年边界"),
    ]
    for ts, label in cases:
        exp = (datetime.strptime(ts, UTC_FMT) + off).date().isoformat()
        got = _utc_to_local_date(ts)
        assert got == exp, f"{label}：回填换算得 {got}，固定时区推导应为 {exp}"
        assert got == clock.to_local(ts), f"{label}：与 Clock.to_local 不自洽"
    assert _utc_to_local_date("") is None and _utc_to_local_date(None) is None
    assert _utc_to_local_date("bad-ts") is None, "坏时间戳未走容错分支"
    # 有牙：若实现退化成"直接取前 10 位"（源码注释点名的历史 bug），本例必须红
    naive = "2026-06-15"
    assert _utc_to_local_date("2026-06-15 16:30:00") != naive or clock.offset == 0, \
        "换算函数等价于取 UTC 前 10 位 ⇒ 正是它要修的缺陷"


def test_回填换算与daily_streak归桶在模拟时间下同值(tmp_path, clock):
    """回填写 learning_events.local_date、streak 读 attempts 的 DATE(ts,'localtime')
    ——**同一时区口径的两个消费者**。本例要求它们对同一批 UTC 时刻给出同一批本地日。"""
    from scripts.backfill_events import _utc_to_local_date
    dao = _dao(tmp_path)
    sims = [real_date(2026, 3, 8), real_date(2026, 3, 9), real_date(2026, 11, 1)]
    _seed(dao, sims)
    via_streak = _local_bucket_days(dao)
    via_backfill = set()
    for (ts,) in dao.conn.execute("SELECT ts FROM attempts"):
        via_backfill.add(_utc_to_local_date(ts))
    assert via_streak == via_backfill, (
        f"两个消费者的日期口径分叉：streak={sorted(via_streak)} 回填={sorted(via_backfill)}")
    assert via_streak == {d.isoformat() for d in sims}, "归桶结果不等于模拟输入"


def test_回填干跑前先证库隔离且不产生任何写入(tmp_path, clock, monkeypatch):
    """`backfill()` 内部是无参 `ProgressDAO()` ⇒ 只靠 `LS_PROGRESS_DB` 隔离。
    本例的顺序是硬要求：**先证明选中的库在 tmp_path，再干跑（apply=False）**。
    绝不传 `apply=True` —— 真写库属人工闸后动作（本仓已因此出过 14 行幽灵数据，
    本班又因 fixture 误用 `monkeypatch.undo()` 连带写进 30 行，见 result「遗留问题」#1）。"""
    from scripts import backfill_events as B
    db = str(tmp_path / "abdf_backfill.db")
    monkeypatch.setenv("LS_PROGRESS_DB", db)

    probe = ProgressDAO()                       # 与 backfill 内部同一构造方式
    assert probe.db_path == db, f"隔离未生效：无参 ProgressDAO 选中了 {probe.db_path}"
    sim = real_date(2026, 5, 20)
    _seed(probe, [sim, sim - timedelta(1)])
    before = probe.event_count()
    assert before >= 2, f"生产路径未写入事件，夹具空转：{before}"
    try:
        with clock.at(sim):
            B.backfill(apply=False, json_output=True)      # 只读干跑
        assert probe.event_count() == before, "dry-run 竟写了事件 ⇒ apply 语义已变，本例必须停"
        assert clock.streak_at(probe, sim) == 2, "干跑改变了 streak"
    finally:
        probe.close()


def test_回填经生产写入器加emit_event在模拟时间下构造并断言真实落库日(tmp_path, clock, monkeypatch):
    """不跑真 writer 的替代法：用生产写入器 `record_attempt()` + 生产 `emit_event()`
    在模拟时钟下构造数据，断言 `local_date` **确实**落到固定模拟日，
    且与 `_utc_to_local_date()` 的纯函数结果同值。"""
    from scripts.backfill_events import _utc_to_local_date
    db = str(tmp_path / "abdf_emit.db")
    monkeypatch.setenv("LS_PROGRESS_DB", db)
    dao = ProgressDAO(db)
    assert dao.db_path == db
    sim = real_date(2026, 11, 1)
    with clock.at(sim):
        dao.record_attempt_and_status("python", "python/abdf_case/e1", "print(1)", True, "")
        dao.emit_event("attempt_submitted", lang="python", problem_id="python/abdf_case/e1",
                       payload={"passed": True})
    rows = dao.conn.execute("SELECT local_date FROM learning_events").fetchall()
    assert [r[0] for r in rows] == [sim.isoformat()], f"emit_event 未落到模拟日：{rows}"
    ts = dao.conn.execute("SELECT ts FROM attempts").fetchone()[0]
    # 纯函数与生产写入器在同一 UTC 时刻上必须给出同一个本地日
    assert _utc_to_local_date(ts) == clock.to_local(ts), "回填换算与固定时区推导分叉"
    assert clock.streak_at(dao, real_date.fromisoformat(clock.to_local(ts))) == 1
    dao.close()


# --------------------------------------------------------------------------
# 5. 热力图筛选：模拟时间下的真实归属（读回条件实际结果）
# --------------------------------------------------------------------------
def test_热力图筛选在模拟过去日期下的真实归属(tmp_path, clock):
    """固定模拟日 2026-03-15：把窗口开到 4000 天时必须被带回，收到 90 天时必须不带回。
    两个"日"都是**固定模拟值**，窗口 N 也是固定值 ⇒ 不读 `date('now')`、不依赖环境挂钟。"""
    dao = _dao(tmp_path)
    sim = real_date(2026, 3, 15)
    with clock.at(sim):
        _submit(dao, "python/abdf_case/h1")
        _submit(dao, "python/abdf_case/h2", passed=False)
    stored = {r[0] for r in dao.conn.execute("SELECT DISTINCT local_date FROM learning_events")}
    assert stored == {sim.isoformat()}, f"emit_event 在模拟时钟下未写入该固定日：{stored}"
    wide = {r["date"] for r in dao.events_by_date(days=4000)}
    assert wide == {sim.isoformat()}, f"宽窗口未带回模拟日那行：{wide}"
    narrow = {r["date"] for r in dao.events_by_date(days=90)}
    assert narrow == set(), (
        f"行确实存在于表中（{stored}）却被 90 天窗口带回 ⇒ 窗口边界已不锚在 UTC now，本例需复核")
    dao.close()


def test_热力图筛选窗口两侧各放一行读回实际归属(tmp_path, clock):
    """两侧各一行：窗口内那行必须带回、窗口外那行必须不带回（读回实际集合，不比大小）。
    两行日期均为固定模拟值，N 为固定值 ⇒ 全例无环境挂钟参与期望值计算。"""
    dao = _dao(tmp_path)
    inside, outside = real_date(2026, 6, 1), real_date(2020, 1, 2)
    for d, tag in [(inside, "in"), (outside, "out")]:
        with clock.at(d):
            _submit(dao, f"python/abdf_case/w_{tag}")
    got = {r["date"] for r in dao.events_by_date(days=4000)}
    assert inside.isoformat() in got, f"窗口内那行未带回：got={got}"
    assert outside.isoformat() in got, f"4000 天窗口本应含 2020 年那行：got={got}"
    got90 = {r["date"] for r in dao.events_by_date(days=90)}
    assert outside.isoformat() not in got90, f"窗口外那行被错误带回：got90={got90}"
    assert dao.conn.execute("SELECT COUNT(*) FROM learning_events").fetchone()[0] >= 4
    dao.close()


def test_热力图边界表达式与两侧换算的实际读数(tmp_path, clock):
    """源码锚定 production 的 WHERE 用 `date('now', ?)`（不带 localtime），
    并要求边界字符串等于"固定时区推导值 ± 至多一天"的**具体值**，不用 ≤1 含糊。"""
    src = open(os.path.join(ROOT, "core", "progress.py"), encoding="utf-8").read()
    body = src.split("def events_by_date")[1][:600]
    assert re.search(r"WHERE local_date >= date\('now', \?\)", body), "边界表达式已变"
    assert "localtime" not in body, "已改成本地口径 ⇒ 两源问题已修复，本例应删"
    dao = _dao(tmp_path)
    for anchor in ["2026-06-15 12:00:00", "2026-01-01 00:30:00", "2026-11-01 23:30:00"]:
        d0 = datetime.strptime(anchor, UTC_FMT)
        exp_utc = (d0.date() - timedelta(days=90)).isoformat()
        exp_loc = (clock.to_local(anchor) and
                   real_date.fromisoformat(clock.to_local(anchor)) - timedelta(days=90)).isoformat()
        assert dao.conn.execute("SELECT date(?, '-90 days')", (anchor,)).fetchone()[0] == exp_utc
        assert dao.conn.execute("SELECT date(?, 'localtime', '-90 days')",
                               (anchor,)).fetchone()[0] == exp_loc, f"锚点 {anchor} 本地侧边界不符推导"
    dao.close()


# --------------------------------------------------------------------------
# 6. 隔离自证：不触达真实用户连续记录
# --------------------------------------------------------------------------
def _fp(path):
    if not os.path.exists(path):
        return None
    b = open(path, "rb").read()
    return (len(b), hashlib.sha256(b).hexdigest()[:8])


def test_本文件全部用例不触达默认生产库(tmp_path, clock):
    prod = os.path.join(ROOT, "data", "progress.db")
    before = _fp(prod)
    assert os.environ.get("LS_PROGRESS_DB") in (None, "") or \
        os.environ["LS_PROGRESS_DB"].startswith(str(tmp_path)), "环境里残留了指向别处的库变量"
    dao = _dao(tmp_path)
    sim = real_date(2026, 9, 1)
    _seed(dao, [sim, sim - timedelta(1)])
    assert clock.streak_at(dao, sim) == 2
    assert dao.db_path == str(tmp_path / "abdf_isolated_progress.db")
    assert dao.db_path != prod
    dao.close()
    assert _fp(prod) == before, f"生产库被改动！{before} -> {_fp(prod)}"


def test_生产写入器与移植路径都只认显式库(tmp_path, clock, monkeypatch):
    """前置校验补强：
    ① `_submit` 走 `judge._record_attempt` 时**显式传 dao** ⇒ 不触发
       `judge.py:199 d = dao or ProgressDAO()` 的默认库回退（14 行幽灵数据的成因）；
    ② 默认路径确实指向生产库 —— **只断言模块常量与解析式，绝不 `ProgressDAO()` 构造**：
       无参构造会真的读写打开生产库（sqlite3.connect + `PRAGMA journal_mode=WAL`），
       哪怕一行不写也会长出 `-wal`/`-shm` 侧车并在关闭时触发 checkpoint（§十四）。
    ③ `ts` 改写只落在指定库。"""
    from core.data_portability import export_all, import_all
    from core import progress as prog
    prod = os.path.join(ROOT, "data", "progress.db")
    before = _fp(prod)

    # ② 默认路径就是生产库（读常量，不开连接）
    monkeypatch.delenv("LS_PROGRESS_DB", raising=False)
    assert os.path.abspath(prog._DEFAULT_DB) == os.path.abspath(prod), \
        "默认库路径已不再指向生产库 ⇒ 本仓隔离前提变了，请复核全案"
    assert "os.environ.get(\"LS_PROGRESS_DB\")" in \
        open(os.path.join(ROOT, "core", "progress.py"), encoding="utf-8").read(), \
        "LS_PROGRESS_DB 隔离缝已消失 ⇒ 回填类脚本再无只读隔离手段"
    # 显式传参必须优先于默认（用 tmp 库验，不构造默认路径）
    assert ProgressDAO(str(tmp_path / "explicit.db")).db_path == str(tmp_path / "explicit.db")

    # ① 显式 dao 全程可见
    db = str(tmp_path / "abdf_writer.db")
    dao = ProgressDAO(db)
    with clock.at(real_date(2026, 2, 3)):
        _submit(dao, "python/abdf_case/x1")
    assert dao.db_path == db
    payload = export_all(dao)
    assert payload["data"]["attempts"], "生产写入器没产生可导出的 attempts"
    for r in payload["data"]["attempts"]:
        r["ts"] = _ts_at_local(dao, real_date(2026, 2, 3))
    target = ProgressDAO(str(tmp_path / "abdf_target.db"))
    stats = import_all(target, payload)
    assert stats["attempts"] == len(payload["data"]["attempts"])
    assert target.db_path == str(tmp_path / "abdf_target.db")
    assert target.conn.execute("SELECT ts FROM attempts").fetchone()[0] == \
        payload["data"]["attempts"][0]["ts"]
    dao.close()
    target.close()
    assert _fp(prod) == before, f"生产库被改动！{before} -> {_fp(prod)}"
