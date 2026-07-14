import pytest

from core.progress import ProgressDAO


@pytest.fixture
def dao(tmp_path):
    d = ProgressDAO(str(tmp_path / "test.db"))
    yield d
    d.close()


def test_record_attempt_and_status(dao):
    aid = dao.record_attempt("python", "py/01", "print(1)", True, "good")
    assert aid > 0
    dao.mark_status("python", "py/01", "solved")
    assert dao.get_status("python", "py/01") == "solved"
    assert dao.attempt_count("python", "py/01") == 1


def test_status_default_unseen(dao):
    assert dao.get_status("sql", "missing") == "unseen"


def test_list_mistakes_only_wrong(dao):
    dao.record_attempt("python", "p1", "x", False, "bad")
    dao.mark_status("python", "p1", "wrong")
    dao.record_attempt("python", "p2", "y", True, "ok")
    dao.mark_status("python", "p2", "solved")
    items = dao.list_mistakes()
    assert len(items) == 1
    assert items[0]["lang"] == "python"
    assert items[0]["problem_id"] == "p1"
    assert items[0]["code"] == "x"


def test_summary_by_lang(dao):
    dao.record_attempt("python", "a", "", True, "")
    dao.mark_status("python", "a", "solved")
    dao.record_attempt("python", "b", "", False, "")
    dao.mark_status("python", "b", "wrong")
    dao.record_attempt("sql", "x", "", True, "")
    dao.mark_status("sql", "x", "solved")
    s = dao.summary_by_lang()
    assert s["python"] == {"total": 2, "solved": 1, "wrong": 1}
    assert s["sql"] == {"total": 1, "solved": 1, "wrong": 0}


def test_status_transitions_wrong_to_solved(dao):
    dao.record_attempt("python", "p", "wrong", False, "")
    dao.mark_status("python", "p", "wrong")
    assert dao.get_status("python", "p") == "wrong"
    dao.record_attempt("python", "p", "right", True, "")
    dao.mark_status("python", "p", "solved")
    assert dao.get_status("python", "p") == "solved"
    assert dao.list_mistakes() == []
