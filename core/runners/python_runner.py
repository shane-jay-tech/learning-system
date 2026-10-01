import os
import shutil
import stat
import sys
import subprocess
import tempfile
import time
import logging
from typing import Optional

from core.runners.base import BaseRunner, RunResult
from core.runners.error_feedback import (
    PREAMBLE as _PREAMBLE,
    classify as _classify_error,
    timeout_message,
)


def _error_kind_for(stderr: str) -> str:
    """r5 B3（2026-09-27 用户裁决）：把编译期错误从"一律 runtime"里分出来。

    复用本仓既有的 `error_feedback.classify` 词表（syntax／runtime／none／timeout），
    不另造第二套判据。**判题结论一字不改**（`ok`／`exit_code` 与有无 preamble 的判定
    全部照旧），只让 `error_kind` 这一列如实区分"解释器拒收"与"跑起来才炸"。
    非 syntax／runtime 的返回值退化为 runtime——超时另有更早的返回分支。
    """
    kind = _classify_error("python", stderr)
    return kind if kind in ("syntax", "runtime") else "runtime"


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

    @staticmethod
    def _make_tree_readonly(root: str) -> None:
        """目录树整树去写位（Windows/POSIX 通用）：文件 0o444、目录 0o555。
        沙箱护栏而非安全边界——临时目录整体随 TemporaryDirectory 退出删除，
        ignore_cleanup_errors 已容忍只读位残留（Windows 只读位不阻止删除）。"""
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                try:
                    os.chmod(os.path.join(dirpath, name), stat.S_IREAD)
                except OSError:
                    pass
            try:
                os.chmod(dirpath, stat.S_IREAD | stat.S_IEXEC)
            except OSError:
                pass

    def run(self, code: str, stdin: str = "", expected: Optional[dict] = None) -> RunResult:
        blocked = self.check_security()
        if blocked:
            return blocked
        with tempfile.TemporaryDirectory(prefix="ls_py_", ignore_cleanup_errors=True) as tmpdir:
            src = os.path.join(tmpdir, "main.py")
            # 引导段常量来自 core.runners.error_feedback（单一来源）——
            # 它同时是学生行号折算的偏移量，写在这里会让行级反馈打歪。
            with open(src, "w", encoding="utf-8", newline="\n") as f:
                f.write(_PREAMBLE + code)
            # l930-07（l927-19 遗留最小可批形状 a）：content/datasets/ 只读复制挂载进 tmpdir——
            # 引用数据集的题面（hr_* 族）在学生代码里 read_csv('datasets/…') 才有落点。
            # 护栏：①复制而非符号链接（Windows 符号链接需特权且可能被沙箱内代码顺链写入
            # 真目录——复制件天然只读）；②单点白名单式只挂数据集目录，不扩大其它仓内
            # 路径可见性；③源目录缺失时静默跳过（零题面依赖路径不受影响）。
            datasets_src = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), "content", "datasets")
            if os.path.isdir(datasets_src):
                shutil.copytree(datasets_src, os.path.join(tmpdir, "datasets"))
                self._make_tree_readonly(os.path.join(tmpdir, "datasets"))

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
                    stderr=timeout_message("代码运行", self.timeout_sec,
                                           "已强制终止，可能存在死循环"),
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
                error_kind=None if ok else _error_kind_for(stderr),
                elapsed_ms=int((time.time() - t0) * 1000),
            )
