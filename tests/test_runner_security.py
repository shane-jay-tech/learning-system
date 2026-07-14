"""Test that runners refuse execution in public deploy mode."""
import os
import pytest
from unittest.mock import patch

from core.runners.python_runner import PythonRunner
from core.runners.sql_runner import SQLRunner
from core.runners.base import RunResult


@pytest.fixture
def public_mode():
    with patch.dict(os.environ, {"RUNNER_SECURITY_MODE": "public"}):
        yield


@pytest.fixture
def public_deploy():
    with patch.dict(os.environ, {"PUBLIC_DEPLOY": "1"}):
        yield


def test_python_runner_blocked_in_public_mode(public_mode):
    runner = PythonRunner()
    result = runner.run("print('hello')")
    assert not result.ok
    assert result.error_kind == "sandbox"
    assert "公开部署" in result.stderr


def test_sql_runner_blocked_in_public_mode(public_mode):
    runner = SQLRunner()
    result = runner.run("SELECT 1")
    assert not result.ok
    assert result.error_kind == "sandbox"


def test_python_runner_blocked_via_public_deploy_env(public_deploy):
    runner = PythonRunner()
    result = runner.run("print('hello')")
    assert not result.ok
    assert result.error_kind == "sandbox"


def test_runners_work_in_local_mode():
    with patch.dict(os.environ, {"RUNNER_SECURITY_MODE": "local_only"}, clear=False):
        runner = PythonRunner()
        result = runner.run("print('hello')")
        assert result.ok
        assert "hello" in result.stdout


class TestEnvironmentIsolation:
    """Verify that sensitive env vars don't leak into runner subprocess."""

    def test_api_key_not_accessible(self):
        code = "import os; print(os.environ.get('DEEPSEEK_API_KEY', 'NOT_FOUND'))"
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "sk-secret-123"}, clear=False):
            runner = PythonRunner()
            result = runner.run(code)
            assert "sk-secret-123" not in result.stdout

    def test_openai_key_not_accessible(self):
        code = "import os; print(os.environ.get('OPENAI_API_KEY', 'NOT_FOUND'))"
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-openai-secret"}, clear=False):
            runner = PythonRunner()
            result = runner.run(code)
            assert "sk-openai-secret" not in result.stdout

    def test_kimi_key_not_accessible(self):
        code = "import os; print(os.environ.get('KIMI_API_KEY', 'NOT_FOUND'))"
        with patch.dict(os.environ, {"KIMI_API_KEY": "sk-kimi-secret"}, clear=False):
            runner = PythonRunner()
            result = runner.run(code)
            assert "sk-kimi-secret" not in result.stdout


class TestOutputTruncation:
    """Verify that large outputs don't crash the system."""

    def test_large_stdout_is_bounded(self):
        code = "print('x' * 2000000)"
        runner = PythonRunner()
        result = runner.run(code)
        assert len(result.stdout) <= 2100000

    def test_infinite_loop_times_out(self):
        code = "while True: pass"
        runner = PythonRunner()
        result = runner.run(code)
        assert not result.ok


class TestSQLSecurity:
    """SQL runner specific security checks."""

    def test_attach_blocked(self):
        runner = SQLRunner()
        result = runner.run("ATTACH DATABASE ':memory:' AS other")
        assert not result.ok

    def test_write_blocked(self):
        runner = SQLRunner()
        result = runner.run("CREATE TABLE hack(id INT); INSERT INTO hack VALUES(1)")
        assert not result.ok
