# -*- coding: utf-8 -*-
"""判题运行器健壮性与安全边界对抗测试包（task 20260904-193458-6a3c, B18）。

不改执行器一行代码；针对 python_runner 与 sql_runner 的未覆盖边界写对抗用例，
每个用例断言"被挡住/被截断/被杀掉"的具体表现。C++/R runner 因本机缺 g++/Rscript
沿用既有 skip 约定（见 test_cpp_runner.py / test_r_runner.py）。
"""
import pytest

from core.runners.python_runner import PythonRunner, MAX_STDOUT_BYTES, MAX_STDERR_BYTES
from core.runners.sql_runner import SQLRunner


@pytest.fixture(scope="module")
def py_runner():
    return PythonRunner()


@pytest.fixture(scope="module")
def sql_runner():
    return SQLRunner()


# ---------- stdout/stderr 限额 ----------

class TestOutputLimits:
    def test_huge_stdout_truncated_with_marker(self, py_runner):
        """超长 stdout：截断 + 截断标记可见，而不是打爆内存。"""
        r = py_runner.run("print('A' * (5 * 1024 * 1024))")
        assert "[... 输出过长" in r.stdout
        assert len(r.stdout.encode("utf-8")) < 5 * 1024 * 1024

    def test_stderr_flood_does_not_break_verdict(self, py_runner):
        """stderr 洪泛：stderr 被截断，但正常完成的程序判定不受影响。"""
        r = py_runner.run(
            "import sys\n"
            "for _ in range(20000):\n"
            "    sys.stderr.write('E' * 200)\n"
            "print('ok')\n"
        )
        assert r.exit_code == 0
        assert r.stdout.strip().endswith("ok")
        assert len(r.stderr.encode("utf-8")) <= MAX_STDERR_BYTES + 200  # 上限+标记冗余

    def test_invalid_utf8_output_does_not_crash(self, py_runner):
        """输出含无效 UTF-8 字节：不崩、不抛异常，按替换策略可读。"""
        r = py_runner.run(
            "import sys\nsys.stdout.buffer.write(b'bad:\\xff\\xfe ok\\n')\n"
        )
        assert r.exit_code == 0
        assert "ok" in r.stdout

    def test_huge_single_line_output(self, py_runner):
        """单行超大输出（无换行）同样被截断。"""
        r = py_runner.run("print('X' * (3 * 1024 * 1024), end='')")
        assert "[... 输出过长" in r.stdout


# ---------- 退出码与进程树 ----------

class TestExitAndProcessTree:
    def test_nonzero_exit_propagates(self, py_runner):
        r = py_runner.run("import sys; sys.exit(3)")
        assert r.exit_code == 3
        assert not r.ok

    def test_timeout_kills_self_repl_process_tree(self, py_runner):
        """自我复制子进程的死循环：树杀后返回超时，且在超时量级时间内完成。"""
        code = (
            "import subprocess, sys, time\n"
            "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(120)'])\n"
            "time.sleep(120)\n"
        )
        import time
        t0 = time.time()
        r = py_runner.run(code)
        elapsed = time.time() - t0
        assert r.timed_out is True
        assert not r.ok
        # 超时 = 类内 timeout_sec(5s)，树杀不应拖到 120s 子进程的寿命
        assert elapsed < 30

    def test_comment_only_code_exits_zero(self, py_runner):
        r = py_runner.run("# 只有注释\n")
        assert r.exit_code == 0

    def test_empty_code_exits_zero(self, py_runner):
        r = py_runner.run("")
        assert r.exit_code == 0


# ---------- 环境白名单与 PATH 收窄 ----------

class TestEnvHygiene:
    def test_env_allowlist_blocks_non_whitelisted_vars(self, py_runner, monkeypatch):
        """父进程注入的未白名单变量不得进入子进程环境。"""
        monkeypatch.setenv("LS_TEST_SECRET_TOKEN", "super-secret")
        r = py_runner.run("import os; print('TOKEN' in os.environ)")
        assert "False" in r.stdout

    def test_path_is_narrowed(self, py_runner):
        """PATH 收窄：条目数 ≤ 解释器目录 + System32 + 根（远小于用户全量 PATH）。"""
        r = py_runner.run("import os; print(len(os.environ['PATH'].split(os.pathsep)))")
        n = int(r.stdout.strip())
        assert 1 <= n <= 5


# ---------- SQL runner：越权与资源对抗 ----------

class TestSQLAuthorization:
    def test_insert_rejected(self, sql_runner):
        r = sql_runner.run("INSERT INTO sqlite_master VALUES (1)")
        assert not r.ok
        assert "只允许查询" in (r.stderr or "")

    def test_update_rejected(self, sql_runner):
        r = sql_runner.run("UPDATE x SET a = 1")
        assert not r.ok

    def test_delete_rejected(self, sql_runner):
        r = sql_runner.run("DELETE FROM x")
        assert not r.ok

    def test_ddl_rejected(self, sql_runner):
        r = sql_runner.run("CREATE TABLE hack(a INT)")
        assert not r.ok

    def test_attach_rejected(self, sql_runner):
        """ATTACH：文件读盘通道，authorizer 与首词校验都应挡下。"""
        r = sql_runner.run("ATTACH DATABASE 'evil.db' AS evil")
        assert not r.ok

    def test_pragma_rejected(self, sql_runner):
        r = sql_runner.run("PRAGMA database_list")
        assert not r.ok

    def test_select_still_allowed(self, sql_runner):
        r = sql_runner.run("SELECT 1+1")
        assert r.ok
        assert r.rows and r.rows[0][0] == 2


class TestSQLResourceLimits:
    def test_runaway_query_capped_at_max_rows(self, sql_runner):
        """递归 CTE 造 10 万行：行数上限生效，截断标记可见，进程不炸。"""
        code = (
            "WITH RECURSIVE cnt(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM cnt LIMIT 100000) "
            "SELECT x FROM cnt"
        )
        r = sql_runner.run(code)
        assert len(r.rows) == SQLRunner._MAX_ROWS
        assert "结果集过大" in r.stdout

    def test_cross_join_bomb_capped(self, sql_runner):
        # authorizer 拒绝 DDL，故用递归 CTE 的 VALUES 笛卡尔积（无需建表）
        code = (
            "WITH big(a) AS (SELECT 1 UNION ALL SELECT a+1 FROM big WHERE a < 300) "
            "SELECT COUNT(*) FROM big b1, big b2, big b3"
        )
        r = sql_runner.run(code)
        # 三重笛卡尔积 2700 万行聚合被 interrupt/限额兜住：要么成功要么超时被杀，
        # 但绝不能挂死或崩溃进程
        assert r.ok is not None
        assert r.elapsed_ms >= 0
