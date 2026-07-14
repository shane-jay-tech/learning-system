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


def _safe_env(extra: Optional[dict] = None) -> dict:
    env = {k: os.environ[k] for k in _ENV_ALLOWLIST if k in os.environ}
    env["PYTHONIOENCODING"] = "utf-8"
    if extra:
        env.update(extra)
    return env


def _truncate(data: bytes, limit: int) -> bytes:
    if len(data) <= limit:
        return data
    return data[:limit] + f"\n[... 输出过长，已截断（>{limit} 字节）]".encode("utf-8")


class PythonRunner(BaseRunner):
    timeout_sec = 5

    def run(self, code: str, stdin: str = "", expected: Optional[dict] = None) -> RunResult:
        blocked = self.check_security()
        if blocked:
            return blocked
        with tempfile.TemporaryDirectory(prefix="ls_py_") as tmpdir:
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
                    input=stdin.encode("utf-8"),
                    timeout=self.timeout_sec,
                )
            except subprocess.TimeoutExpired:
                proc.kill()
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
