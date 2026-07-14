from core.runners.sql_runner import SQLRunner


def test_select_one():
    r = SQLRunner().run("SELECT 1")
    assert r.ok
    assert r.rows == [[1]]


def test_setup_and_select():
    setup = (
        "CREATE TABLE students(id INTEGER, name TEXT, score INTEGER);"
        "INSERT INTO students VALUES (1,'Alice',92),(2,'Bob',60);"
    )
    r = SQLRunner().run("SELECT name FROM students WHERE score >= 80", expected={"setup_sql": setup})
    assert r.ok
    assert r.rows == [["Alice"]]


def test_non_query_rejected_with_friendly_message():
    r = SQLRunner().run("SELEC 1")
    assert not r.ok
    assert r.error_kind == "runtime"
    assert "只允许查询" in r.stderr


def test_real_syntax_error_in_select():
    r = SQLRunner().run("SELECT FROM")
    assert not r.ok
    assert r.error_kind == "runtime"


def test_no_result_query():
    setup = "CREATE TABLE t(x INTEGER); INSERT INTO t VALUES (1);"
    r = SQLRunner().run("SELECT * FROM t WHERE x = 999", expected={"setup_sql": setup})
    assert r.ok
    assert r.rows == []
