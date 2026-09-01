import os
import sys
import subprocess
import tempfile
import time
import logging
from typing import Optional

from core.runners.base import BaseRunner, RunResult


# 沙箱限制
MAX_STDOUT_BYTES = 1_000_000   # 1 MB
MAX_STDERR_BYTES = 100_000     # 100 KB

# subprocess 环境白名单 — 避免父进程 API key 等敏感变量泄漏给学生代码
# 注意：PROCESSOR_ARCHITECTURE 必须放行——缺它时 R 的 rlang/cli 等编译包退出清理会
# 崩溃（0xC0000005），导致 dplyr/tidyverse 题即使答对也因 returncode≠0 被判失败。
# 它是标准 Windows 系统变量（值如 AMD64），非敏感信息。（2026-05-30 二分定位）
_ENV_ALLOWLIST = (
    "SYSTEMROOT", "PATH", "TEMP", "TMP",
    "USERPROFILE", "APPDATA", "LOCALAPPDATA",
    "PYTHONIOENCODING", "PROCESSOR_ARCHITECTURE",
)


def _system_path_dirs() -> list:
    root = os.environ.get("SYSTEMROOT", "C:\\Windows")
    return [root + "\\System32", root]


def _safe_env(extra: Optional[dict] = None) -> dict:
    env = {k: os.environ[k] for k in _ENV_ALLOWLIST if k in os.environ}
    env["PYTHONIOENCODING"] = "utf-8"
    # PATH 收窄：解释器目录 + System32（与 C++ runner 一致）。
    # 此前完整继承父进程 PATH，学生代码可经 PATH 调用任意已装程序；
    # 收窄后只保留运行必需项（本机单人边界仍以 README 的信任模型为准）。
    if os.name == "nt" and "PATH" in env:
        env["PATH"] = os.pathsep.join([os.path.dirname(sys.executable)] + _system_path_dirs())
    if extra:
        env.update(extra)
    return env


def _truncate(data: bytes, limit: int) -> bytes:
    if len(data) <= limit:
        return data
    # 截断点可能落在多字节 UTF-8 字符中间：先丢弃半个字符再截断，避免出现 �
    cut = data[:limit].decode("utf-8", errors="ignore").encode("utf-8")
    return cut + f"\n[... 输出过长，已截断（>{limit} 字节）]".encode("utf-8")


def _kill_tree(proc: subprocess.Popen) -> None:
    """杀掉整棵进程树（含孙进程）。

    学生代码可能 subprocess.Popen 派生子进程：只 kill 直接子进程时，
    孙进程会继续持有 stdout 管道与临时目录，导致 communicate 阻塞、
    TemporaryDirectory 清理失败。
    """
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True, timeout=10,
            )
        else:
            proc.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


_MAX_STDIN_BYTES = 1_000_000  # 1 MB


def _safe_stdin(stdin: str) -> bytes:
    """stdin 编码 + 上限，避免超大输入占满内存 / 孤立代理对抛 UnicodeEncodeError。"""
    data = stdin.encode("utf-8", errors="replace")
    if len(data) > _MAX_STDIN_BYTES:
        data = data[:_MAX_STDIN_BYTES]
    return data


class PythonRunner(BaseRunner):
    timeout_sec = 5

    def run(self, code: str, stdin: str = "", expected: Optional[dict] = None) -> RunResult:
        blocked = self.check_security()
        if blocked:
            return blocked
        with tempfile.TemporaryDirectory(prefix="ls_py_", ignore_cleanup_errors=True) as tmpdir:
            src = os.path.join(tmpdir, "main.py")
            preamble = (
                "import sys\n"
                "try:\n"
                "    sys.stdout.reconfigure(encoding='utf-8')\n"
                "    sys.stderr.reconfigure(encoding='utf-8')\n"
                "except Exception:\n"
                "    pass\n"
            )
            with open(src, "w", encoding="utf-8", newline="\n") as f:
                f.write(preamble + code)

            t0 = time.time()
            proc = subprocess.Popen(
                [sys.executable, "-I", src],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=tmpdir,
                env=_safe_env(),
            )
            try:
                out_b, err_b = proc.communicate(
                    input=_safe_stdin(stdin),
                    timeout=self.timeout_sec,
                )
            except subprocess.TimeoutExpired:
                _kill_tree(proc)
                try:
                    out_b, err_b = proc.communicate(timeout=2)
                except subprocess.TimeoutExpired:
                    out_b, err_b = b"", b""
                return RunResult(
                    ok=False,
                    stdout=_truncate(out_b or b"", MAX_STDOUT_BYTES).decode("utf-8", errors="replace"),
                    stderr="代码运行超过 5 秒，已强制终止（可能存在死循环）。",
                    timed_out=True,
                    exit_code=None,
                    error_kind="timeout",
                    elapsed_ms=int((time.time() - t0) * 1000),
                )

            stdout = _truncate(out_b, MAX_STDOUT_BYTES).decode("utf-8", errors="replace")
            stderr = _truncate(err_b, MAX_STDERR_BYTES).decode("utf-8", errors="replace")
            ok = proc.returncode == 0
            return RunResult(
                ok=ok,
                stdout=stdout,
                stderr=stderr,
                timed_out=False,
                exit_code=proc.returncode,
                error_kind=None if ok else "runtime",
                elapsed_ms=int((time.time() - t0) * 1000),
            )
