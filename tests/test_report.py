"""Test learning report generation."""
from core.progress import ProgressDAO
from core.report import generate_report, report_to_markdown


def _dao_with_data():
    dao = ProgressDAO(":memory:")
    dao.record_attempt_and_status("python", "python/01/q1", "print(1)", True, "good")
    dao.record_attempt_and_status("python", "python/01/q2", "x=1", False, "wrong")
    dao.record_attempt_and_status("sql", "sql/01/q1", "SELECT 1", True, "ok")
    return dao


def test_empty_report():
    dao = ProgressDAO(":memory:")
    report = generate_report(dao, days=7)
    assert report["total_attempts"] == 0
    assert report["period_passed"] == 0
    assert report["grand_solved"] == 0
    md = report_to_markdown(report)
    assert "学习报告" in md
    dao.close()


def test_report_with_data():
    dao = _dao_with_data()
    report = generate_report(dao, days=7)
    assert report["total_attempts"] == 3
    assert report["grand_solved"] == 2
    assert report["grand_wrong"] == 1
    dao.close()


def test_report_markdown_format():
    dao = _dao_with_data()
    report = generate_report(dao, days=7)
    md = report_to_markdown(report)
    assert "##" in md
    assert "通过" in md
    dao.close()


def test_report_monthly():
    dao = _dao_with_data()
    report = generate_report(dao, days=30)
    assert report["total_attempts"] >= 3
    dao.close()
