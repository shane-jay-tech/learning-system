"""Test recommend() integration with review_state table."""
from datetime import date, timedelta
from unittest.mock import patch
from core.progress import ProgressDAO
from core.recommend import recommend

FAKE_PROBLEMS = [
    {"lang": "python", "topic_slug": "t1", "topic_title": "T1", "problem_id": "python/t1/q1", "title": "Q1", "difficulty": 1},
    {"lang": "python", "topic_slug": "t1", "topic_title": "T1", "problem_id": "python/t1/q2", "title": "Q2", "difficulty": 2},
    {"lang": "python", "topic_slug": "t1", "topic_title": "T1", "problem_id": "python/t1/q3", "title": "Q3", "difficulty": 3},
    {"lang": "python", "topic_slug": "t2", "topic_title": "T2", "problem_id": "python/t2/q4", "title": "Q4", "difficulty": 1},
    {"lang": "python", "topic_slug": "t2", "topic_title": "T2", "problem_id": "python/t2/q5", "title": "Q5", "difficulty": 2},
]


def _setup_dao():
    dao = ProgressDAO(":memory:")
    dao.record_attempt_and_status("python", "python/t1/q1", "x=1", True, "")
    dao.update_review_state("python", "python/t1/q1", True, 1)
    dao.record_attempt_and_status("python", "python/t1/q2", "x=2", True, "")
    dao.update_review_state("python", "python/t1/q2", True, 2)
    dao.record_attempt_and_status("python", "python/t1/q3", "x=3", False, "")
    dao.update_review_state("python", "python/t1/q3", False, 3)
    return dao


@patch("core.recommend._path_next_problems", return_value=set())
@patch("core.recommend._path_blocking_wrong", return_value=set())
@patch("core.recommend.all_problems", return_value=FAKE_PROBLEMS)
def test_due_review_comes_from_review_state(mock_ap, mock_pb, mock_pn):
    dao = _setup_dao()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    dao.conn.execute(
        "UPDATE review_state SET next_due_date=? WHERE problem_id='python/t1/q1'",
        (yesterday,),
    )
    dao.conn.commit()
    future = (date.today() + timedelta(days=10)).isoformat()
    dao.conn.execute(
        "UPDATE review_state SET next_due_date=? WHERE problem_id='python/t1/q2'",
        (future,),
    )
    dao.conn.commit()

    results = recommend(n=10, dao=dao)
    dao.close()

    ids = [r["problem_id"] for r in results]
    reasons = {r["problem_id"]: r["reason"] for r in results}
    assert "python/t1/q3" in ids
    assert reasons["python/t1/q3"] == "错题复习"
    assert "python/t1/q1" in ids
    assert reasons["python/t1/q1"] == "到期复习"
    if "python/t1/q2" in reasons:
        assert reasons["python/t1/q2"] != "到期复习"


@patch("core.recommend._path_next_problems", return_value=set())
@patch("core.recommend._path_blocking_wrong", return_value=set())
@patch("core.recommend.all_problems", return_value=FAKE_PROBLEMS)
def test_wrong_included_in_recommendations(mock_ap, mock_pb, mock_pn):
    dao = _setup_dao()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    dao.conn.execute(
        "UPDATE review_state SET next_due_date=? WHERE problem_id='python/t1/q1'",
        (yesterday,),
    )
    dao.conn.commit()

    results = recommend(n=5, dao=dao)
    dao.close()

    reasons = [r["reason"] for r in results]
    assert "错题复习" in reasons
    assert "到期复习" in reasons


@patch("core.recommend.all_problems", return_value=FAKE_PROBLEMS)
def test_failed_attempt_resets_review_state(mock_ap):
    dao = ProgressDAO(":memory:")
    dao.record_attempt_and_status("python", "python/t1/q1", "x=1", True, "")
    dao.update_review_state("python", "python/t1/q1", True, 2)
    row = dao.conn.execute(
        "SELECT interval_days, review_streak FROM review_state WHERE problem_id='python/t1/q1'"
    ).fetchone()
    assert row[0] > 1
    assert row[1] >= 1

    dao.update_review_state("python", "python/t1/q1", False, 2)
    row = dao.conn.execute(
        "SELECT interval_days, review_streak FROM review_state WHERE problem_id='python/t1/q1'"
    ).fetchone()
    assert row[0] == 1
    assert row[1] == 0
    dao.close()


@patch("core.recommend._path_next_problems", return_value=set())
@patch("core.recommend._path_blocking_wrong", return_value=set())
@patch("core.recommend.all_problems", return_value=FAKE_PROBLEMS)
def test_recommend_has_reason_field(mock_ap, mock_pb, mock_pn):
    dao = ProgressDAO(":memory:")
    results = recommend(n=3, dao=dao)
    dao.close()
    valid_reasons = {"错题复习", "弱项巩固", "到期复习", "探索新题", "路径阻塞错题", "路径下一题"}
    for r in results:
        assert "reason" in r
        assert r["reason"] in valid_reasons


@patch("core.recommend._path_next_problems", return_value=set())
@patch("core.recommend._path_blocking_wrong", return_value=set())
@patch("core.recommend.all_problems", return_value=FAKE_PROBLEMS)
def test_unseen_not_due_shows_as_new(mock_ap, mock_pb, mock_pn):
    dao = ProgressDAO(":memory:")
    results = recommend(n=5, dao=dao)
    dao.close()
    for r in results:
        assert r["reason"] in ("探索新题", "弱项巩固")


# ---------------------------------------------------------------------------
# l922-08：两个私有纯函数的直钉补测（本文件此前只从 recommend() 顶层打，
# `grep -rn "_topic_weakness|_due_reviews_from_state" tests/` 实测 0 命中）。
# 落点说明：任务书把产出标成"新建 tests/test_recommend_review_state.py"，
# 但该文件在本单开工前已存在且被 git 跟踪（119 行，d914-?? 的 recommend 集成测），
# 故按"同文件加例"而非覆盖写 —— 覆盖会清掉上面 5 条既有用例。
# 弱项公式（core/recommend.py:40-60）：weakness = fail_rate*2 + (1 - pass_rate)
#   全对 0.0 / 全错 3.0 / 未作答 1.0 / 半对半错 1.5，值域 [0, 3]。
# ---------------------------------------------------------------------------


def _item(lang, slug, pid):
    return {"lang": lang, "topic_slug": slug, "topic_title": slug.upper(),
            "problem_id": pid, "title": pid, "difficulty": 2}


def test_weakness_空items返回空dict():
    """四态之一：空库/零题 → {} —— recommend() 的 .get(..., 0) 兜底不能掩盖这里返回 None。"""
    from core.recommend import _topic_weakness
    out = _topic_weakness([], {})
    assert isinstance(out, dict)
    assert out == {}
    # status 里有数据但 items 为空同样不得产出键（排序键读的是 weakness）
    assert _topic_weakness([], {("python", "python/t1/q1"): "solved"}) == {}


def test_weakness_全对态钉0且不含隐式弱项():
    from core.recommend import _topic_weakness
    items = [_item("python", "t1", "python/t1/q1"), _item("python", "t1", "python/t1/q2")]
    status = {("python", "python/t1/q1"): "solved", ("python", "python/t1/q2"): "solved"}
    out = _topic_weakness(items, status)
    assert out == {"python/t1": 0.0}, out


def test_weakness_全错态钉上界3():
    """fail_rate=1 → 2.0；pass_rate=0 → +1.0 ⇒ 3.0 是该函数的值域上界。"""
    from core.recommend import _topic_weakness
    items = [_item("python", "t1", "python/t1/q1"), _item("r", "t9", "r/t9/q1")]
    status = {("python", "python/t1/q1"): "wrong", ("r", "r/t9/q1"): "wrong"}
    out = _topic_weakness(items, status)
    assert out == {"python/t1": 3.0, "r/t9": 3.0}, out


def test_weakness_混合态精确值与单调序():
    from core.recommend import _topic_weakness
    items = [
        _item("python", "mix", "python/mix/a"), _item("python", "mix", "python/mix/b"),
        _item("python", "unseen", "python/unseen/a"), _item("python", "unseen", "python/unseen/b"),
        _item("python", "half", "python/half/a"), _item("python", "half", "python/half/b"),
        _item("python", "odd", "python/odd/a"),
    ]
    status = {
        ("python", "python/mix/a"): "solved", ("python", "python/mix/b"): "wrong",
        # python/unseen/* 完全不在 status 里
        ("python", "python/half/a"): "solved",          # b 未作答
        ("python", "python/odd/a"): "in_progress",      # 既非 solved 也非 wrong
    }
    out = _topic_weakness(items, status)
    assert out["python/mix"] == 1.5, out       # 0.5*2 + (1-0.5)
    assert out["python/unseen"] == 1.0, out    # 0 + (1-0)：未作答 == 中等弱项，不是 0
    assert out["python/half"] == 0.5, out      # 1 对 1 未答 → 0 + (1-0.5)
    assert out["python/odd"] == 1.0, out       # 未知状态既不计对也不计错，与"未作答"同值
    # 排序契约（recommend 用 -weakness 做降序）：全错 > 半对半错 > 未作答/未知状态 > 半对 > 全对
    assert out["python/mix"] > out["python/unseen"] == out["python/odd"] > out["python/half"] > 0.0
    assert all(0.0 <= v <= 3.0 for v in out.values()), out


def test_weakness_键形状与逐topic隔离():
    from core.recommend import _topic_weakness
    items = [_item("python", "t1", "python/t1/q1"), _item("python", "t2", "python/t2/q1"),
             _item("sql", "t1", "sql/t1/q1")]
    status = {("python", "python/t1/q1"): "wrong", ("sql", "sql/t1/q1"): "wrong"}
    out = _topic_weakness(items, status)
    assert set(out) == {"python/t1", "python/t2", "sql/t1"}, out
    # "<lang>/<slug>" 恰一个斜杠，且同名 slug 不跨语言串味（python/t1 与 sql/t1 各自独立）
    assert all(k.count("/") == 1 for k in out), out
    assert out["python/t1"] == out["sql/t1"] == 3.0
    assert out["python/t2"] == 1.0   # t2 未作答


class _SpyDAO:
    """内存桩：只记调用契约，不碰 sqlite —— 钉 _due_reviews_from_state 的 limit 透传。"""

    def __init__(self, ret):
        self._ret = ret
        self.calls = []

    def due_review_ids(self, limit=None):
        self.calls.append(limit)
        return self._ret


def test_due_reviews_空库返回空set():
    from core.recommend import _due_reviews_from_state
    dao = ProgressDAO(":memory:")
    try:
        out = _due_reviews_from_state(dao)
        assert isinstance(out, set)
        assert out == set()
    finally:
        dao.close()


def test_due_reviews_到期边界含今天():
    """SQL 判据是 `next_due_date <= today`（core/progress.py:418）⇒ 今天这条必须在里面。
    写成 < 的"顺手优化"会每天少推一批题且没有任何上层用例会红，故在此钉住。"""
    from core.recommend import _due_reviews_from_state
    dao = ProgressDAO(":memory:")
    today = date.today().isoformat()
    yest = (date.today() - timedelta(days=1)).isoformat()
    tomb = (date.today() + timedelta(days=1)).isoformat()
    try:
        for pid, due in (("due_yesterday", yest), ("due_today", today), ("due_tomorrow", tomb)):
            dao.conn.execute(
                "INSERT INTO review_state (lang, problem_id, interval_days, ease, review_streak, next_due_date, last_result) "
                "VALUES ('python', ?, 3, 2.0, 1, ?, 'pass')", (f"python/t1/{pid}", due))
        dao.conn.commit()
        out = _due_reviews_from_state(dao)
        assert ("python", "python/t1/due_yesterday") in out
        assert ("python", "python/t1/due_today") in out, "今天到期被判未到期（边界写成 < 了）"
        assert ("python", "python/t1/due_tomorrow") not in out
        assert len(out) == 2, out
    finally:
        dao.close()


def test_due_reviews_透传limit1000且原样返回集合():
    from core.recommend import _due_reviews_from_state
    ret = {("python", "python/t1/q1"), ("r", "r/t9/q1")}
    spy = _SpyDAO(ret)
    out = _due_reviews_from_state(spy)
    assert spy.calls == [1000], spy.calls
    assert out == ret
    assert all(isinstance(x, tuple) and len(x) == 2 for x in out), out
    # 同一 problem_id 跨语言不得被 set 去重吞掉
    spy2 = _SpyDAO({("python", "x"), ("sql", "x")})
    assert len(_due_reviews_from_state(spy2)) == 2


def test_due_reviews_走真实间隔算法而非手工插行():
    """答对后由 update_review_state 推进 next_due_date；此刻不应被判为到期。
    与 test_failed_attempt_resets_review_state 互补：那条查 interval，这条查"到期集合"这一消费面。"""
    from core.recommend import _due_reviews_from_state
    dao = ProgressDAO(":memory:")
    try:
        dao.record_attempt_and_status("python", "python/t1/q1", "x=1", True, "")
        dao.update_review_state("python", "python/t1/q1", True, 3)
        assert _due_reviews_from_state(dao) == set()
        row = dao.conn.execute(
            "SELECT next_due_date FROM review_state WHERE problem_id='python/t1/q1'").fetchone()
        assert row[0] > date.today().isoformat(), row
    finally:
        dao.close()
