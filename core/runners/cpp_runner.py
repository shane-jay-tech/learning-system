import os
import shutil
import subprocess
import tempfile
import time
from typing import Optional

from core.runners.base import BaseRunner, RunResult
from core.runners.error_feedback import friendly_hint, timeout_message
from core.runners.python_runner import (_safe_env, _truncate, _kill_tree, _safe_stdin,
                                        MAX_STDOUT_BYTES, MAX_STDERR_BYTES)


def _cpp_friendly_error(stderr_text: str) -> str:
    """g++ 报错是英文原文，给零基础学生附一句中文提示（LLM 离线时也有兜底）。

    词表与匹配口径已收进 `core/runners/error_feedback`（四语言共用一张表，
    统一大小写不敏感）——这里只保留 SQL/C++ 的既有调用面与既有输出形态。
    """
    return friendly_hint("cpp", stderr_text)


class CppRunner(BaseRunner):
    total_timeout_sec = 10
    compile_timeout_sec = 7

    fallback_paths = [
        r"D:\tools\mingw64\bin\g++.exe",
        r"C:\msys64\mingw64\bin\g++.exe",
        r"C:\MinGW\bin\g++.exe",
    ]

    # l923-31：与 RRunner.fallback_glob 同型的通配兜底。多版本并存的发行版目录
    # （winlibs 解出来的 mingw13.1.0、msys2 的 mingw64、TDM-GCC-64 等）此前完全看不见，
    # 只有三个写死的盘符路径命中才行。优先级严格在 which 与 fallback_paths 之后。
    # ⚠️ 排序键沿用 RRunner._version_key（整路径抽数字）⇒ 跨根目录比较时数字可能来自
    #    "msys64/mingw64" 这类架构后缀而非版本号，该局限与 R 侧同源，未在本单扩大范围修。
    fallback_glob = [
        r"D:\tools\mingw*\bin\g++.exe",
        r"D:\tools\gcc*\bin\g++.exe",
        r"C:\msys64\mingw*\bin\g++.exe",
        r"C:\mingw*\bin\g++.exe",
        r"C:\TDM-GCC-*\bin\g++.exe",
    ]

    @staticmethod
    def _version_key(path: str) -> tuple:
        """从路径中提取 (major, minor, patch...) 数字元组，用于数值排序
        （字典序会把 4.9 排在 4.10 之后）。与 RRunner._version_key 同款。"""
        import re as _re
        nums = _re.findall(r"\d+", path)
        return tuple(int(n) for n in nums) or (0,)

    def _resolve_compiler(self) -> Optional[str]:
        which = shutil.which("g++")
        if which:
            return which
        for p in self.fallback_paths:
            if os.path.exists(p):
                return p
        import glob
        best = None
        best_key = None
        for pat in self.fallback_glob:
            for p in glob.glob(pat):
                key = self._version_key(p)
                if best_key is None or key > best_key:
                    best_key = key
                    best = p
        return best

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

        with tempfile.TemporaryDirectory(prefix="ls_cpp_", ignore_cleanup_errors=True) as tmpdir:
            src = os.path.join(tmpdir, "main.cpp")
            exe = os.path.join(tmpdir, "main.exe")
            with open(src, "w", encoding="utf-8", newline="\n") as f:
                f.write(code)

            # 编译 / 运行用受限 env：PATH 只含 g++ 自己的目录 + Windows 系统目录
            # 不重用父进程完整 PATH（否则破坏第 1 轮白名单）
            from core.runners.python_runner import _system_path_dirs
            safe_path = os.pathsep.join([os.path.dirname(gpp)] + _system_path_dirs())
            env = _safe_env({"PATH": safe_path})
            t0 = time.time()
            # 用 Popen + communicate 而非 subprocess.run：超时时可以整棵进程树
            # 杀掉（subprocess.run 只杀直接子进程，MinGW 的 cc1plus 孙进程
            # 会继续持有管道导致 communicate 永久阻塞）
            try:
                comp = subprocess.Popen(
                    [gpp, "-std=c++17", "-O0", "-Wall", src, "-o", exe],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                )
            except OSError as e:
                return RunResult(
                    ok=False, stdout="", stderr=f"编译器启动失败：{e}",
                    timed_out=False, exit_code=None, error_kind="sandbox",
                    elapsed_ms=int((time.time() - t0) * 1000),
                )
            try:
                comp_out, comp_err = comp.communicate(timeout=self.compile_timeout_sec)
            except subprocess.TimeoutExpired:
                _kill_tree(comp)
                try:
                    comp_out, comp_err = comp.communicate(timeout=2)
                except subprocess.TimeoutExpired:
                    comp_out, comp_err = b"", b""
                return RunResult(
                    ok=False, stdout="", stderr=timeout_message("编译", self.compile_timeout_sec),
                    timed_out=True, exit_code=None, error_kind="timeout",
                    elapsed_ms=int((time.time() - t0) * 1000),
                )

            if comp.returncode != 0:
                stderr_text = _truncate(comp_err or b"", MAX_STDERR_BYTES).decode("utf-8", errors="replace")
                return RunResult(
                    ok=False,
                    stdout="",
                    stderr=_cpp_friendly_error(stderr_text),
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
                out_b, err_b = proc.communicate(input=_safe_stdin(stdin), timeout=remaining)
            except subprocess.TimeoutExpired:
                _kill_tree(proc)
                try:
                    out_b, err_b = proc.communicate(timeout=2)
                except subprocess.TimeoutExpired:
                    out_b, err_b = b"", b""
                return RunResult(
                    ok=False,
                    stdout=_truncate(out_b or b"", MAX_STDOUT_BYTES).decode("utf-8", errors="replace"),
                    stderr=timeout_message("程序运行", remaining,
                                           "编译通过后运行超时，检查循环与输入规模"),
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
