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


def test_sql_error_gets_chinese_hint():
    from core.runners.sql_runner import _friendly_sql_error
    hint = _friendly_sql_error("no such table: students")
    assert "中文提示" in hint and "students" in hint
    assert "表名拼写" in hint

    hint2 = _friendly_sql_error("ambiguous column name: id")
    assert "表名前缀" in hint2

    # 无匹配模式时原样返回
    assert _friendly_sql_error("unknown weird error") == "unknown weird error"

    # 端到端：真实 SQLite 报错也带中文提示
    r = SQLRunner().run("SELECT * FROM nonexistent_table")
    assert not r.ok
    assert "中文提示" in r.stderr


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


def test_trailing_comment_is_allowed():
    from core.runners.sql_runner import _split_sql_statements
    stmts = _split_sql_statements("SELECT 1; -- note\nSELECT 2 /* mid */ ;")
    assert stmts == ["SELECT 1", "SELECT 2"]
    r = SQLRunner().run("SELECT 1; -- 说明")
    assert r.ok
    assert r.rows == [[1]]


def test_empty_code_gets_friendly_message():
    r = SQLRunner().run("   ")
    assert not r.ok
    assert "请输入" in r.stderr


def test_result_row_cap_prevents_runaway_result_sets():
    r = SQLRunner().run(
        "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM c WHERE x<20000) "
        "SELECT * FROM c"
    )
    assert r.ok
    assert len(r.rows) == SQLRunner()._MAX_ROWS
    assert "结果集过大" in r.stdout
