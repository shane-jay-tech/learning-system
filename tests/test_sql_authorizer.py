"""Test SQL authorizer blocks dangerous operations."""
import pytest
from core.runners.sql_runner import SQLRunner


@pytest.fixture
def runner():
    return SQLRunner()


def test_select_allowed(runner):
    result = runner.run("SELECT 1 + 1 AS result",
                       expected={"setup_sql": "CREATE TABLE t(id INTEGER); INSERT INTO t VALUES(1);"})
    assert result.ok


def test_select_from_setup_table(runner):
    result = runner.run("SELECT * FROM employees",
                       expected={"setup_sql": "CREATE TABLE employees(id INTEGER, name TEXT); INSERT INTO employees VALUES(1, 'Alice');"})
    assert result.ok
    assert result.rows == [[1, "Alice"]]


def test_with_cte_select_allowed(runner):
    sql = "WITH nums AS (SELECT 1 AS n UNION ALL SELECT 2) SELECT * FROM nums"
    result = runner.run(sql, expected={"setup_sql": "CREATE TABLE dummy(x INTEGER);"})
    assert result.ok


def test_attach_database_blocked(runner):
    result = runner.run("ATTACH DATABASE ':memory:' AS db2",
                       expected={"setup_sql": "CREATE TABLE t(x INTEGER);"})
    assert not result.ok
    assert "只允许查询" in result.stderr


def test_create_table_blocked_in_student_sql(runner):
    result = runner.run("CREATE TABLE hack(x INTEGER)",
                       expected={"setup_sql": "CREATE TABLE t(x INTEGER);"})
    assert not result.ok
    assert "只允许查询" in result.stderr


def test_insert_blocked_in_student_sql(runner):
    result = runner.run("INSERT INTO t VALUES(99)",
                       expected={"setup_sql": "CREATE TABLE t(x INTEGER); INSERT INTO t VALUES(1);"})
    assert not result.ok
    assert "只允许查询" in result.stderr


def test_drop_table_blocked(runner):
    result = runner.run("DROP TABLE t",
                       expected={"setup_sql": "CREATE TABLE t(x INTEGER);"})
    assert not result.ok
    assert "只允许查询" in result.stderr


def test_pragma_blocked(runner):
    result = runner.run("PRAGMA table_info(t)",
                       expected={"setup_sql": "CREATE TABLE t(x INTEGER);"})
    assert not result.ok
    assert "只允许查询" in result.stderr


def test_delete_blocked(runner):
    result = runner.run("DELETE FROM t WHERE x = 1",
                       expected={"setup_sql": "CREATE TABLE t(x INTEGER); INSERT INTO t VALUES(1);"})
    assert not result.ok
    assert "只允许查询" in result.stderr


def test_update_blocked(runner):
    result = runner.run("UPDATE t SET x = 99 WHERE x = 1",
                       expected={"setup_sql": "CREATE TABLE t(x INTEGER); INSERT INTO t VALUES(1);"})
    assert not result.ok
    assert "只允许查询" in result.stderr
