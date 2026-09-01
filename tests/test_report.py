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


def test_report_html_is_self_contained_and_escaped():
    from core.report import report_to_html
    dao = _dao_with_data()
    report = generate_report(dao, days=7)
    report["weak_topics"] = [["python/01_<script>alert(1)</script>", 2.5]]
    html = report_to_html(report)
    assert html.strip().startswith("<!DOCTYPE html>")
    assert "<style>" in html and "@media print" in html
    assert "编程学习报告" in html
    assert "Python" in html
    # 动态内容必须转义：恶意字符串不得原样进入 HTML
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    # 打印提示
    assert "Ctrl+P" in html
    # 单大括号 CSS 合法（不是 {{ }}）
    assert "{{" not in html
    dao.close()


def test_report_monthly():
    dao = _dao_with_data()
    report = generate_report(dao, days=30)
    assert report["total_attempts"] >= 3
    dao.close()
