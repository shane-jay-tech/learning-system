import os
import shutil
import subprocess
import tempfile
import time
from typing import Optional

from core.runners.base import BaseRunner, RunResult
from core.runners.python_runner import _safe_env, _truncate, MAX_STDOUT_BYTES, MAX_STDERR_BYTES


class CppRunner(BaseRunner):
    total_timeout_sec = 10
    compile_timeout_sec = 7

    fallback_paths = [
        r"D:\tools\mingw64\bin\g++.exe",
        r"C:\msys64\mingw64\bin\g++.exe",
        r"C:\MinGW\bin\g++.exe",
    ]

    def _resolve_compiler(self) -> Optional[str]:
        which = shutil.which("g++")
        if which:
            return which
        for p in self.fallback_paths:
            if os.path.exists(p):
                return p
        return None

    def run(self, code: str, stdin: str = "", expected: Optional[dict] = None) -> RunResult:
        blocked = self.check_security()
        if blocked:
            return blocked
        gpp = self._resolve_compiler()
        if not gpp:
            return RunResult(
                ok=False,
                stdout="",
                stderr="未检测到 g++，请先安装 MinGW (https://www.mingw-w64.org) 并把 bin 目录加入 PATH。",
                timed_out=False,
                exit_code=None,
                error_kind="sandbox",
            )

        with tempfile.TemporaryDirectory(prefix="ls_cpp_") as tmpdir:
            src = os.path.join(tmpdir, "main.cpp")
            exe = os.path.join(tmpdir, "main.exe")
            with open(src, "w", encoding="utf-8", newline="\n") as f:
                f.write(code)

            # 编译 / 运行用受限 env：PATH 只含 g++ 自己的目录 + Windows 系统目录
            # 不重用父进程完整 PATH（否则破坏第 1 轮白名单）
            sys_dirs = [os.environ.get("SYSTEMROOT", "C:\\Windows") + r"\System32",
                        os.environ.get("SYSTEMROOT", "C:\\Windows")]
            safe_path = os.pathsep.join([os.path.dirname(gpp)] + sys_dirs)
            env = _safe_env({"PATH": safe_path})
            t0 = time.time()
            try:
                comp = subprocess.run(
                    [gpp, "-std=c++17", "-O0", "-Wall", src, "-o", exe],
                    capture_output=True,
                    timeout=self.compile_timeout_sec,
                    env=env,
                )
            except subprocess.TimeoutExpired:
                return RunResult(
                    ok=False, stdout="", stderr="编译超时（>7 秒）。",
                    timed_out=True, exit_code=None, error_kind="timeout",
                    elapsed_ms=int((time.time() - t0) * 1000),
                )

            if comp.returncode != 0:
                return RunResult(
                    ok=False,
                    stdout="",
                    stderr=_truncate(comp.stderr or b"", MAX_STDERR_BYTES).decode("utf-8", errors="replace"),
                    timed_out=False,
                    exit_code=comp.returncode,
                    error_kind="compile",
                    elapsed_ms=int((time.time() - t0) * 1000),
                )

            remaining = max(1, self.total_timeout_sec - int(time.time() - t0))
            try:
                proc = subprocess.Popen(
                    [exe],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=tmpdir,
                    env=env,
                )
                out_b, err_b = proc.communicate(input=stdin.encode("utf-8"), timeout=remaining)
            except subprocess.TimeoutExpired:
                proc.kill()
                try:
                    out_b, err_b = proc.communicate(timeout=2)
                except subprocess.TimeoutExpired:
                    out_b, err_b = b"", b""
                return RunResult(
                    ok=False,
                    stdout=_truncate(out_b or b"", MAX_STDOUT_BYTES).decode("utf-8", errors="replace"),
                    stderr="程序运行超时。",
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
