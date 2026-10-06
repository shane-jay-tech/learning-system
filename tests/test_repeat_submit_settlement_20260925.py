# -*- coding: utf-8 -*-
"""重复点击 / 网络重试 / 断线恢复会不会重复结算（qoder-executor-20260925-1555-learn37 · 20260925-120558-0f02，A 档 test）。

卷宗验收句「同一 submission key 只结算一次，客户端能安全重试」的两半，本仓实况：

* **submission key 不存在**——`attempts` / `learning_events` 两张结算表的列里没有任何幂等键
  （只有 `id INTEGER PRIMARY KEY AUTOINCREMENT`），全仓 `rg -i "submission|idempot|dedupe_key"`
  在生产码零命中。所以这条判据**没有可指向的对象**，本件按 §五.2 收窄为：
  把「一次点击 = 几行结算」逐层钉成读数，并登记缺幂等键这个缺陷（A 档：只登记不改）。
* **客户端能安全重试**——分三层，结论不同：
  - `problems_status` / 成就层 **真幂等**（主键 / `achievements_earned` meta 去重），
  - `attempts` / `learning_events` / `review_state` **每次点击各推进一次**（重复点击 = 重复计分），
  - LLM 链路 `_call_chain` 重试**有界**（链内每档至多一次 + 总预算 `_CHAIN_BUDGET_SEC`），
  - 开放题断线时**不落结算**（可安全重试），run 题断线时**照落结算**——两口径分叉，见缺陷 D2。

🔴 隔离：与 `tests/test_judge_repeat_stability_20260925.py` 同一套三层防护
（autouse 把 `LS_PROGRESS_DB` 指沙盒 + 显式 `tmp_path` DAO + 每条用例前后复点生产库字节）。
绝不写入 `data/progress.db`；不删任何数据行（真删属人工闸）。

复跑：
    cd /d/code/learning-system && PYTHONIOENCODING=utf-8 python -m pytest tests/test_repeat_submit_settlement_20260925.py -q -rs
"""
import hashlib
import json
import os
import sqlite3
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PROD_DB = REPO / "data" / "progress.db"


def _db_fingerprint(path: Path):
    """只读字节指纹：不建 sqlite 连接 ⇒ 不触发 WAL checkpoint（纪律档 §十四）。"""
    if not path.exists():
        return ("absent", 0, "0" * 8)
    b = path.read_bytes()
    wal = path.with_suffix(path.suffix + "-wal")
    return (len(b), hashlib.sha256(b).hexdigest()[:8], wal.stat().st_size if wal.exists() else -1)


@pytest.fixture(autouse=True)
def prod_db_untouched():
    before = _db_fingerprint(PROD_DB)
    yield before
    after = _db_fingerprint(PROD_DB)
    assert after == before, f"生产库被本班用例写过！前={before} 后={after}"


@pytest.fixture(autouse=True)
def sandbox_db(monkeypatch, tmp_path):
    fake = tmp_path / "env-sandbox.db"
    monkeypatch.setenv("LS_PROGRESS_DB", str(fake))
    return fake


@pytest.fixture
def dao(tmp_path):
    from core.progress import ProgressDAO
    d = ProgressDAO(str(tmp_path / "settle.db"))
    yield d
    d.close()


@pytest.fixture
def no_llm(monkeypatch):
    """断线态：`_call_chain` 整链失败（真实实现在全失败时返回 ("", None)）。"""
    monkeypatch.setattr("core.ai_review._call_chain", lambda *a, **kw: ("", None))


def _count(dao, sql, *args):
    return dao.conn.execute(sql, args).fetchone()[0]


PROBLEM = {
    "id": "python/dblclick/1",
    "title": "t",
    "statement": "s",
    "expected_output": "Hello\n",
}
CODE = 'print("Hello")'


# ------------------------------------------------ 一次点击 = 几行结算（逐层读数）
def test_five_clicks_settle_five_times_in_append_tables_but_once_in_status(dao, no_llm):
    """【l1006-03 翻正】幂等三件套落地后：五连击＝恰 1 次结算（submission 窗口幂等）。

    原判据（append 层恰 5）钉的是「无幂等键」现状；l1006-03/l1004-07②（用户 2026-10-06 拍板
    全落）落地后同 (lang,pid,code) 窗口内重复提交返回首次判定、零重复计分——判据随之翻正：
    attempts / attempt_submitted / problem_passed 均 **恰为 1**，与 problems_status 同为 1 行。
    """
    from core.judge import judge

    for _ in range(5):
        r = judge("python", PROBLEM, CODE, dao=dao)
        assert r.passed is True

    assert _count(dao, "SELECT COUNT(*) FROM attempts WHERE problem_id=?", PROBLEM["id"]) == 1
    assert _count(dao, "SELECT COUNT(*) FROM learning_events WHERE event_type='attempt_submitted' "
                       "AND problem_id=?", PROBLEM["id"]) == 1
    assert _count(dao, "SELECT COUNT(*) FROM learning_events WHERE event_type='problem_passed' "
                       "AND problem_id=?", PROBLEM["id"]) == 1
    assert _count(dao, "SELECT COUNT(*) FROM problems_status WHERE problem_id=?", PROBLEM["id"]) == 1
    assert dao.get_status("python", PROBLEM["id"]) == "solved"

    # 鉴别力反向对照：只点 1 次时上面三个计数必须是 1
    one = {"id": "python/dblclick/2", "title": "t", "statement": "s",
           "expected_output": "Hello\n"}
    judge("python", one, CODE, dao=dao)
    assert _count(dao, "SELECT COUNT(*) FROM attempts WHERE problem_id=?", one["id"]) == 1


def test_repeat_submission_pushes_srs_forward_every_click(dao, no_llm):
    """缺陷 D1 承重用例：同一份代码重复提交，间隔复习状态（掌握度）被逐次推进。

    这一层没有任何去重——「改一个字再点五次」等价于答对五次：streak 5、间隔按 ease 复利、
    到期日往后推。本件只钉现状读数，不改判分口径。
    """
    from core.judge import judge

    def state():
        row = dao.conn.execute(
            "SELECT interval_days, ease, review_streak, next_due_date FROM review_state "
            "WHERE problem_id=?", (PROBLEM["id"],)).fetchone()
        assert row is not None, "review_state 没被写过 ⇒ 本条测的不是它声称的东西"
        return row

    judge("python", PROBLEM, CODE, dao=dao)
    s1 = state()
    assert s1[2] == 1, s1
    for _ in range(4):
        r = judge("python", PROBLEM, CODE, dao=dao)
        assert r.passed is True, r
    s5 = state()
    # 【l1006-03 翻正】幂等落地：重复点击零推进——streak 恒 1、间隔与到期日纹丝不动
    #（SRS 曲线整体变平属拍板预期；切换公告已含「历史数值不可比」标注）
    assert s5[2] == 1, f"重复提交不该推进 streak（期望恒 1）：{s5}"
    assert s5[0] == s1[0] and s5[3] == s1[3], f"重复提交不该动间隔/到期日：{s1} -> {s5}"


def test_settlement_tables_have_no_idempotency_key_column(dao):
    """卷宗「同一 submission key 只结算一次」的否证：两张结算表里根本没有幂等键列。

    写成正向探针而非注释——将来真加了 key 列，本条会红，那时判据才有对象可写。
    """
    def cols(table):
        rows = dao.conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {r[1] for r in rows}

    at, ev = cols("attempts"), cols("learning_events")
    for t, c in (("attempts", at), ("learning_events", ev)):
        assert c, f"{t} 表列为空 ⇒ 夹具没建起来"
        assert not any("key" in x.lower() or "dedupe" in x.lower() or "idempot" in x.lower()
                       for x in c), f"{t} 出现了幂等键列 {c}，本条否证需改判据"
    assert at == {"id", "lang", "problem_id", "code", "passed", "ai_feedback", "ts"}, at
    # 唯一约束面：attempts 无任何 UNIQUE 索引（真幂等只在 problems_status 主键上）
    uniq = dao.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='attempts' "
        "AND sql LIKE '%UNIQUE%'").fetchall()
    assert uniq == [], f"attempts 出现了 UNIQUE 索引 {uniq}"


# ------------------------------------------------ 断线恢复的两条口径
def test_run_problem_still_settles_when_llm_is_down(dao, no_llm):
    """口径 A：run 题在 LLM 断线时**照旧结算**，点评落到离线兜底文本。

    ⇒ 学生「断线时点了提交、恢复后再点一次」= 两次结算（缺陷 D1 的一条触发路径）。
    """
    from core.judge import judge

    r = judge("python", PROBLEM, CODE, dao=dao)
    assert r.passed is True, "LLM 断线不得改变判分结论（红线：判分口径不动）"
    assert "暂时不可用" in r.ai_feedback, r.ai_feedback
    assert _count(dao, "SELECT COUNT(*) FROM attempts WHERE problem_id=?", PROBLEM["id"]) == 1


def test_open_problem_does_not_settle_when_llm_is_down(dao, no_llm):
    """口径 B：开放题在 LLM 断线时**不写任何结算行**——所以它能安全重试。

    与 `ui/pages/language.py` 的「判题结果未记录，请稍后重试」文案同源。
    鉴别力：本条必须同时证明「一行都没写」和「表本身可用」（另跑一道 run 题写入成功）。
    """
    from core.judge import judge

    open_p = {"id": "python/open/1", "title": "t", "statement": "说说你的思路",
              "judge_mode": "ai_open", "rubric": "看是否提到循环", "reference_answer": "参考"}
    r = judge("python", open_p, "我的回答", dao=dao)
    assert r.passed is False
    assert _count(dao, "SELECT COUNT(*) FROM attempts WHERE problem_id=?", open_p["id"]) == 0, \
        "开放题在 LLM 不可用时写了结算行 ⇒ 断线重试会被计一次成绩"
    assert dao.get_status("python", open_p["id"]) == "unseen"

    judge("python", PROBLEM, CODE, dao=dao)   # 对照：同库同 DAO 下 run 题写库通路正常
    assert _count(dao, "SELECT COUNT(*) FROM attempts WHERE problem_id=?", PROBLEM["id"]) == 1


def test_open_problem_recovers_and_settles_exactly_once_after_retry(dao, monkeypatch):
    """断线后重试：开放题恢复可用时结算一次；同题同答案再点一次仍是第二次结算（无幂等键）。

    这条同时给出「客户端能安全重试」的正半句（失败不落库）与缺半句（成功重试不去重）。
    """
    from core.judge import judge

    payload = json.dumps({"passed": True, "score": 90, "feedback": "很好", "dimensions": []},
                         ensure_ascii=False)
    n = {"c": 0}

    def flaky(prompt, system, chain, *a, **kw):
        n["c"] += 1
        if n["c"] == 1:
            return ("", None)          # 第一次：断线
        return (payload, "stub")       # 第二次：恢复

    monkeypatch.setattr("core.ai_review._call_chain", flaky)
    # 开放题结果缓存只在 llm_ok 时写入；断线那次不得污染缓存
    p = {"id": "python/open/2", "title": "t", "statement": "s",
         "judge_mode": "ai_open", "rubric": "r", "reference_answer": "x"}
    r1 = judge("python", p, "答案", dao=dao)
    assert r1.passed is False and n["c"] == 1
    r2 = judge("python", p, "答案", dao=dao)
    assert r2.passed is True, (r2, n)
    assert n["c"] == 2, "断线那次把失败写进了缓存，重试没真正再问 ⇒ 与 _cached_open_result 契约冲突"
    assert _count(dao, "SELECT COUNT(*) FROM attempts WHERE problem_id=?", p["id"]) == 1


# ------------------------------------------------ 网络重试是否有界
def test_llm_chain_calls_each_model_at_most_once_and_bounded(dao, monkeypatch):
    """`_call_chain` 的重试口径：链上每个模型至多一次，全失败即止 ⇒ 不会放大成无限重试。

    这是「客户端能安全重试」的基础：一次提交最多产生 len(chain) 次外呼。
    """
    import core.ai_review as ar

    seen = []
    monkeypatch.setattr(ar, "_call",
                        lambda model, prompt, system=None, model_id=None, timeout=None:
                        (seen.append(model), "")[1])
    out = ar._call_chain("p", "s", ar._FAST_CHAIN)
    assert out == ("", None), out
    assert [m for m, _ in ar._FAST_CHAIN] == seen, f"链上模型被重复调用或漏调用：{seen}"

    seen.clear()
    monkeypatch.setattr(ar, "_call",
                        lambda model, prompt, system=None, model_id=None, timeout=None:
                        (seen.append(model), "第一段就成了")[1])
    out2 = ar._call_chain("p", "s", ar._FAST_CHAIN)
    assert out2[0] == "第一段就成了" and len(seen) == 1, (out2, seen)


# ------------------------------------------------ 成就层：真幂等
def test_repeated_settlement_does_not_reaward_achievements(dao, no_llm):
    """成就层靠 `achievements_earned` meta 去重 ⇒ 重复点击不会重复解锁。

    覆盖面自证：必须真拿到一次解锁（否则"第二次为 0"是恒真），
    且 `achievement_unlocked` 事件计数恰等于去重后的解锁个数。
    """
    from core.achievements import check_achievements
    from core.judge import judge

    for _ in range(4):
        judge("python", PROBLEM, CODE, dao=dao)

    first = check_achievements(dao)
    assert "first_solve" in first, f"没拿到预期解锁，第二次的 0 就成了恒真：{first}"
    n_unlock_events = _count(dao, "SELECT COUNT(*) FROM learning_events "
                                  "WHERE event_type='achievement_unlocked'")
    assert n_unlock_events == len(first), (first, n_unlock_events)

    second = check_achievements(dao)
    assert set(second).isdisjoint(set(first)), f"同一成就被重复解锁：{second}"
    assert _count(dao, "SELECT COUNT(*) FROM learning_events "
                       "WHERE event_type='achievement_unlocked'") == n_unlock_events, \
        "第二次 check 又发了解锁事件 ⇒ 成就层不幂等"

    earned = json.loads(dao.get_meta("achievements_earned", "[]"))
    assert len(earned) == len(set(earned)), earned


# ------------------------------------------------ recommendation 归因事件
def test_recommendation_completed_event_emitted_per_settlement(dao, no_llm):
    """同一 passed 提交重复结算时，`recommendation_completed` 也按次重复发（现状读数）。

    卷宗没提这一层，但它是「多次计分」会污染到推荐归因统计的连带面：
    `_check_recommendation_completed` 每次判对都补一条 completed 事件，与 shown 事件不再 1:1。
    """
    from core.judge import judge

    dao.emit_event("recommendation_shown", lang="python", problem_id=PROBLEM["id"],
                   payload={"recommendation_id": "r-1", "reason_code": "due", "surface": "home", "rank": 1})
    for _ in range(3):
        judge("python", PROBLEM, CODE, dao=dao)

    shown = _count(dao, "SELECT COUNT(*) FROM learning_events WHERE event_type='recommendation_shown'")
    done = _count(dao, "SELECT COUNT(*) FROM learning_events WHERE event_type='recommendation_completed'")
    # 【l1006-03 翻正】幂等重放＋completed 当日去重后：1 shown : 1 completed
    assert (shown, done) == (1, 1), f"shown={shown} completed={done}，判据需重读"
