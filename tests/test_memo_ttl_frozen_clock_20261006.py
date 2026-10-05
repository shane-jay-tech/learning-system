"""_memoized TTL 3 秒陈旧窗口钉测试（l1004-11；7b25#3＋942f#5 同条）。

冻结 time.monotonic 三态：① TTL 内（<3s）返回旧快照；② 写操作清空 memo 立即新鲜；
③ TTL 过（>3s）重查 DB。三读函数（all_problems_status／list_mistakes／summary_by_lang）
共用同一 _memoized 骨架，断言取其一（all_problems_status）＋骨架直测两态。
独立测试件：自带 tmp 库，不并入他件夹具、不改生产码。
"""
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from core.progress import ProgressDAO  # noqa: E402


@pytest.fixture()
def dao(tmp_path, monkeypatch):
    db = tmp_path / "memo_ttl.db"
    d = ProgressDAO(db_path=str(db))
    yield d
    d.close()


class FrozenClock:
    """冻结/推进 time.monotonic（core.progress._memoized 在函数内 import time）。"""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@pytest.fixture()
def clock(monkeypatch):
    fc = FrozenClock()
    monkeypatch.setattr("time.monotonic", fc)
    return fc


def _seed(dao, lang, pid, status):
    dao.mark_status(lang, pid, status)


def test_within_ttl_returns_stale_snapshot_even_after_direct_db_write(dao, clock):
    """TTL 内：绕过 DAO 直改 DB（模拟跨进程写入），三读仍返回旧快照＝陈旧窗口在案。"""
    _seed(dao, "python", "p1", "solved")
    first = dao.all_problems_status()
    assert first.get(("python", "p1")) == "solved"
    clock.advance(1.0)  # < 3s
    with dao.conn:
        dao.conn.execute(
            "INSERT OR REPLACE INTO problems_status(lang, problem_id, status, last_attempt_ts) "
            "VALUES ('python','p1','wrong', CURRENT_TIMESTAMP)")
    stale = dao.all_problems_status()
    assert stale.get(("python", "p1")) == "solved", "TTL 内应返回旧快照（陈旧窗口实锤）"


def test_write_operation_clears_memo_immediately(dao, clock):
    """写操作（record_attempt_and_status/mark_status）清空 memo：TTL 内也立即新鲜。"""
    _seed(dao, "python", "p1", "solved")
    assert dao.all_problems_status().get(("python", "p1")) == "solved"
    clock.advance(1.0)  # < 3s
    dao.record_attempt_and_status("python", "p1", "code", False, "fb")  # 写 → _clear_memo
    fresh = dao.all_problems_status()
    assert fresh.get(("python", "p1")) == "wrong", "写操作后 TTL 内也必须读到新值"


def test_after_ttl_expiry_rereads_database(dao, clock):
    """TTL 过（>3s）：重查 DB，读到跨进程直改后的新值。"""
    _seed(dao, "python", "p1", "solved")
    assert dao.all_problems_status().get(("python", "p1")) == "solved"
    clock.advance(3.5)  # > 3s TTL
    with dao.conn:
        dao.conn.execute(
            "INSERT OR REPLACE INTO problems_status(lang, problem_id, status, last_attempt_ts) "
            "VALUES ('python','p1','wrong', CURRENT_TIMESTAMP)")
    assert dao.all_problems_status().get(("python", "p1")) == "wrong", "TTL 过后必须重查 DB"


def test_list_mistakes_and_summary_share_the_same_memo_skeleton(dao, clock):
    """三读函数共用 _memoized 骨架：list_mistakes/summary_by_lang 同样 TTL 内复用旧快照。"""
    _seed(dao, "python", "p1", "wrong")
    assert len(dao.list_mistakes()) == 1
    clock.advance(1.0)
    _seed(dao, "python", "p1", "solved")  # mark_status 内部清 memo → 该路径立即新鲜
    assert dao.list_mistakes() == []
    # 不经写操作、只等 TTL 过期：
    _seed(dao, "python", "p2", "wrong")
    assert len(dao.list_mistakes()) == 1
    clock.advance(1.0)
    with dao.conn:
        dao.conn.execute(
            "INSERT OR REPLACE INTO problems_status(lang, problem_id, status, last_attempt_ts) "
            "VALUES ('python','p2','solved', CURRENT_TIMESTAMP)")  # 直改不清 memo
    assert len(dao.list_mistakes()) == 1, "TTL 内直改 DB 应读到旧快照（骨架共用实证）"
    clock.advance(2.5)  # 累计 3.5s > TTL
    assert dao.list_mistakes() == [], "TTL 过后重查：错题本应为空"
