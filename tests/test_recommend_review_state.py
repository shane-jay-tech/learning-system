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
