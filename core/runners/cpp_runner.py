import os
import shutil
import subprocess
import tempfile
import time
from typing import Optional

from core.runners.base import BaseRunner, RunResult
from core.runners.python_runner import (_safe_env, _truncate, _kill_tree, _safe_stdin,
                                        MAX_STDOUT_BYTES, MAX_STDERR_BYTES)

_CPP_FRIENDLY_HINTS = [
    (r"error: expected ';'", "漏了分号 ;（看报错指出的行）"),
    (r"error: expected '}'", "少了一个 }（检查大括号配对）"),
    (r"error: '(\w+)' was not declared in this scope", "「{0}」未定义——检查拼写与作用域"),
    (r"undefined reference", "函数只有声明没有定义（或没把对应源文件一起编译）"),
    (r"error: no match for 'operator", "运算符不匹配——检查操作数类型"),
    (r"error: '([^']+)' undeclared", "「{0}」未声明——是否漏了头文件 #include？"),
]


def _cpp_friendly_error(stderr_text: str) -> str:
    """g++ 报错是英文原文，给零基础学生附一句中文提示（LLM 离线时也有兜底）。"""
    import re
    for pat, tmpl in _CPP_FRIENDLY_HINTS:
        m = re.search(pat, stderr_text)
        if m:
            hint = tmpl.format(*m.groups()) if m.groups() else tmpl
            return f"{stderr_text}\n\n💡 中文提示：{hint}"
    return stderr_text


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
                    ok=False, stdout="", stderr="编译超时（>7 秒）。",
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
