"""进度一致性（信箱单 20260925-120559-7b25 · B 档 test）。

判据（卷宗「任务／验收」两行逐句改写）：
  任务：验证**完成、跳过、重做**和**跨设备恢复**的进度一致。
  验收：**刷新、重新登录和离线恢复**后状态符合**事件顺序**。

本仓是单机 Streamlit 应用，没有账号体系 ⇒ 「重新登录 / 刷新 / 离线恢复」
在可复现层面对应的是**换一条数据库连接重开 ProgressDAO**（进程内 session_state
全部丢掉，只剩落盘的 attempts / problems_status）；「跨设备恢复」对应
`core.data_portability.export_all → import_all` 落到另一条库。

一致性口径取「事件顺序」：把 `attempts` 按自增 id 升序重放，
每题**最后一个事件**的 passed 就是它应有的状态（无事件 = unseen）。
断言 = 落盘的 problems_status 与这个重放结果**逐题相等**。

覆盖面自证（不是"读现值等于现值"的恒真式）：
  * 合成反例 `test_oracle_detects_a_desync_stale_status_row` —— 绕过生产写入口、
    直接用 SQL 把 problems_status 钉成与最后一个事件相反的值，断言**必然报不一致**；
  * 反向对照 —— 同一个 oracle 在生产写入口 `_record_attempt` 的真实序列上判一致。
两向都能给出预期读数，才说明这条断言有牙。
"""
import json

import pytest

from core.data_portability import export_all, import_all
from core.judge import _record_attempt
from core.progress import ProgressDAO

LANG = "python"
P_SKIP = "python/01_skip_me"
P_DONE = "python/02_done"
P_REDO_TO_SOLVED = "python/03_redo_to_solved"
P_REDO_TO_WRONG = "python/04_redo_to_wrong"


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "progress_recovery.db")


@pytest.fixture
def dao(db_path):
    d = ProgressDAO(db_path)
    yield d
    d.close()


# ---------------------------------------------------------------- 读库的两个视图

def status_by_event_order(conn):
    """按 attempts.id 升序**重放事件**推出的状态（最后一件事说了算）。"""
    out = {}
    for lang, pid, passed in conn.execute(
        "SELECT lang, problem_id, passed FROM attempts ORDER BY id ASC"
    ).fetchall():
        out[(lang, pid)] = "solved" if passed else "wrong"
    return out


def persisted_status(conn):
    """problems_status 里**实际落盘**的状态。"""
    return {
        (lang, pid): status
        for lang, pid, status in conn.execute(
            "SELECT lang, problem_id, status FROM problems_status"
        ).fetchall()
    }


def assert_progress_matches_event_order(conn):
    """一致性主断言：落盘状态 == 事件重放状态，逐题相等（两侧键集也要相等）。"""
    expected = status_by_event_order(conn)
    actual = persisted_status(conn)
    assert actual == expected, {
        "only_in_db": {k: v for k, v in actual.items() if expected.get(k) != v},
        "only_in_events": {k: v for k, v in expected.items() if k not in actual},
    }


# ---------------------------------------------------------------- 真实写事件序列

def replay_user_session(d):
    """走完卷宗点名的三态：完成 / 跳过 / 重做（两个方向都重做）。

    全部经 `core.judge._record_attempt`——这是页面「提交运行」唯一的生产写入口，
    它同时写 attempts、problems_status、review_state 和 learning_events。
    """
    # 跳过：只看题面 / 上报 lesson_viewed，一道题都没交
    d.emit_event("lesson_viewed", lang=LANG, topic_id="t01")

    # 完成：一次通过
    _record_attempt(LANG, P_DONE, "print(1)", True, "ok", d)

    # 重做（错 → 对）
    _record_attempt(LANG, P_REDO_TO_SOLVED, "bad", False, "no", d)
    _record_attempt(LANG, P_REDO_TO_SOLVED, "good", True, "yes", d)

    # 重做（对 → 错）：重做也能把已通过题打回待改
    _record_attempt(LANG, P_REDO_TO_WRONG, "good", True, "yes", d)
    _record_attempt(LANG, P_REDO_TO_WRONG, "bad", False, "no", d)


# ---------------------------------------------------------------- 用例

def test_skip_writes_no_progress_row(db_path):
    """「跳过」不许留下任何进度痕迹——否则未做过的题会在错题本/汇总里凭空出现。"""
    d = ProgressDAO(db_path)
    try:
        d.emit_event("lesson_viewed", lang=LANG, topic_id="t01")
        assert d.get_status(LANG, P_SKIP) == "unseen"
        assert persisted_status(d.conn) == {}
        assert status_by_event_order(d.conn) == {}
        assert d.attempt_count(LANG, P_SKIP) == 0
        assert d.total_attempts() == 0
    finally:
        d.close()


def test_complete_and_two_way_redo_match_event_order_then_reopen(db_path):
    """完成 + 双向重做：当场一致；**重开连接（刷新／重登／离线恢复）后仍一致**。"""
    d = ProgressDAO(db_path)
    try:
        replay_user_session(d)
        assert_progress_matches_event_order(d.conn)
        # 钉住"重做确实把状态打过两次"，防止整件因写入口静默失败而退化成恒真
        assert persisted_status(d.conn) == {
            (LANG, P_DONE): "solved",
            (LANG, P_REDO_TO_SOLVED): "solved",
            (LANG, P_REDO_TO_WRONG): "wrong",
        }
    finally:
        d.close()

    # 换连接重开 = 进程内 session_state 全丢，只剩盘上的库
    d2 = ProgressDAO(db_path)
    try:
        assert_progress_matches_event_order(d2.conn)
        assert d2.get_status(LANG, P_REDO_TO_SOLVED) == "solved"
        assert d2.get_status(LANG, P_REDO_TO_WRONG) == "wrong"
        assert d2.get_status(LANG, P_SKIP) == "unseen"
        # 重做过的题在 attempts 里必须留着完整事件链（进度可追溯，不是覆盖丢事件）
        assert d2.attempt_count(LANG, P_REDO_TO_SOLVED) == 2
        assert d2.attempt_count(LANG, P_REDO_TO_WRONG) == 2
        # 错题本恢复后与事件顺序同构：只含"最后是错"的那道
        assert [m["problem_id"] for m in d2.list_mistakes()] == [P_REDO_TO_WRONG]
    finally:
        d2.close()


def test_second_open_connection_sees_same_order(db_path):
    """离线恢复形态：一条连接在写、另一条同时打开的连接的读数必须同序。"""
    writer = ProgressDAO(db_path)
    reader = ProgressDAO(db_path)
    try:
        _record_attempt(LANG, P_DONE, "x", False, "", reader)  # reader 先落一个"错"
        reader.conn.commit()
        assert reader.get_status(LANG, P_DONE) == "wrong"

        _record_attempt(LANG, P_DONE, "y", True, "", writer)   # writer 重做通过
        writer.conn.commit()

        # reader 立刻重开语句读：状态与事件顺序都得跟上，不能停在旧值
        assert reader.get_status(LANG, P_DONE) == "solved"
        assert_progress_matches_event_order(reader.conn)
    finally:
        writer.close()
        reader.close()


def test_cross_device_roundtrip_restores_event_order_into_empty_device(db_path, tmp_path):
    """跨设备恢复：导出→导入空库，重开后进度仍与事件顺序一致，事件链不失真。"""
    src = ProgressDAO(db_path)
    try:
        replay_user_session(src)
        assert_progress_matches_event_order(src.conn)
        payload = export_all(src)
        src_events = [
            (r[0], r[1], r[2]) for r in src.conn.execute(
                "SELECT lang, problem_id, passed FROM attempts ORDER BY id"
            ).fetchall()
        ]
        src_status = persisted_status(src.conn)
    finally:
        src.close()

    other_device = str(tmp_path / "device_b" / "progress.db")
    dst = ProgressDAO(other_device)
    try:
        stats = import_all(dst, payload)
        assert stats["attempts"] == len(src_events)
        assert stats["problems_status"] == 3
        assert_progress_matches_event_order(dst.conn)
        # 两台设备的进度必须逐题相同（跨设备恢复的"一致"就是这个等式）
        assert persisted_status(dst.conn) == src_status
    finally:
        dst.close()

    # 再重开一次（换设备后的"首帧刷新"）
    again = ProgressDAO(other_device)
    try:
        assert_progress_matches_event_order(again.conn)
        assert [
            (r[0], r[1], bool(r[2])) for r in again.conn.execute(
                "SELECT lang, problem_id, passed FROM attempts ORDER BY id"
            ).fetchall()
        ] == [(l, p, bool(v)) for l, p, v in src_events]
        assert again.get_status(LANG, P_SKIP) == "unseen"
    finally:
        again.close()


def test_attempt_events_are_emitted_in_the_same_order_as_attempts(db_path):
    """learning_events 的 attempt_submitted 序列必须与 attempts 同序同值。

    进度"符合事件顺序"如果只看一张表是自证不了的：埋点流和明细流是两条写入路径，
    漂移会让错题本/热力图/漏斗互相打脸。
    """
    d = ProgressDAO(db_path)
    try:
        replay_user_session(d)
        from_events = [
            (lang, pid, bool(json.loads(payload).get("passed")))
            for lang, pid, payload in d.conn.execute(
                "SELECT lang, problem_id, payload_json FROM learning_events "
                "WHERE event_type='attempt_submitted' ORDER BY id"
            ).fetchall()
        ]
        from_attempts = [
            (lang, pid, bool(passed)) for lang, pid, passed in d.conn.execute(
                "SELECT lang, problem_id, passed FROM attempts ORDER BY id"
            ).fetchall()
        ]
        assert from_events == from_attempts
        assert len(from_attempts) == 5
    finally:
        d.close()


# ---------------------------------------------------------------- 覆盖面自证（有牙）

def test_oracle_detects_a_desync_stale_status_row(db_path):
    """合成反例：绕过生产写入口、把状态钉成与最后一个事件相反 ⇒ 主断言必须报不一致。

    这条是前面所有 `assert_progress_matches_event_order` 的**判别力证明**：
    如果那个 helper 是恒真式，这里就会绿——它必须红。
    """
    d = ProgressDAO(db_path)
    try:
        _record_attempt(LANG, P_DONE, "x", False, "", d)
        _record_attempt(LANG, P_DONE, "y", True, "", d)   # 最后一个事件 = solved
        assert status_by_event_order(d.conn)[(LANG, P_DONE)] == "solved"
        with d.conn:
            d.conn.execute(
                "INSERT OR REPLACE INTO problems_status (lang, problem_id, status) "
                "VALUES (?,?,?)", (LANG, P_DONE, "wrong"))
        assert persisted_status(d.conn)[(LANG, P_DONE)] == "wrong"
        with pytest.raises(AssertionError):
            assert_progress_matches_event_order(d.conn)
    finally:
        d.close()


def test_oracle_detects_a_missing_status_row(db_path):
    """合成反例 2：有事件却没有状态行（半成功写入）⇒ 同样必须报不一致。"""
    d = ProgressDAO(db_path)
    try:
        _record_attempt(LANG, P_DONE, "x", True, "", d)
        with d.conn:
            d.conn.execute("DELETE FROM problems_status WHERE problem_id=?", (P_DONE,))
        with pytest.raises(AssertionError):
            assert_progress_matches_event_order(d.conn)
    finally:
        d.close()


def test_record_attempt_ignores_ai_variant_ids(db_path):
    """反向对照：变式题（AI_VARIANT::）按设计不落库，主断言在这种序列上仍成立。"""
    d = ProgressDAO(db_path)
    try:
        _record_attempt(LANG, "AI_VARIANT::" + P_DONE, "x", True, "", d)
        assert d.total_attempts() == 0
        assert persisted_status(d.conn) == {}
        assert_progress_matches_event_order(d.conn)
    finally:
        d.close()
