import os
import shutil
import subprocess
import tempfile
import time
from typing import Optional

from core.runners.base import BaseRunner, RunResult
from core.runners.python_runner import _safe_env, _truncate, MAX_STDOUT_BYTES, MAX_STDERR_BYTES


class RRunner(BaseRunner):
    timeout_sec = 5

    fallback_glob = [
        r"C:\Program Files\R\R-*\bin\Rscript.exe",
        r"C:\Program Files\R\R-*\bin\x64\Rscript.exe",
        r"D:\Program Files\R\R-*\bin\Rscript.exe",
        r"D:\tools\R\R-*\bin\Rscript.exe",
    ]

    def _resolve_rscript(self) -> Optional[str]:
        which = shutil.which("Rscript")
        if which:
            return which
        import glob
        for pat in self.fallback_glob:
            matches = sorted(glob.glob(pat), reverse=True)
            if matches:
                return matches[0]
        return None

    def run(self, code: str, stdin: str = "", expected: Optional[dict] = None) -> RunResult:
        blocked = self.check_security()
        if blocked:
            return blocked
        rscript = self._resolve_rscript()
        if not rscript:
            return RunResult(
                ok=False,
                stdout="",
                stderr="未检测到 Rscript，请先双击 D:\\tools\\install_R.bat 安装 R。",
                timed_out=False,
                exit_code=None,
                error_kind="sandbox",
            )

        with tempfile.TemporaryDirectory(prefix="ls_r_") as tmpdir:
            src = os.path.join(tmpdir, "main.R")
            with open(src, "w", encoding="utf-8", newline="\n") as f:
                f.write(code)

            # R 用户库：动态查找 win-library 下任意 R-x.y 版本
            # 不覆盖用户已有的 R_LIBS_USER（renv 等场景）
            extra = {}
            if not os.environ.get("R_LIBS_USER"):
                import glob as _g
                import re as _re
                lib_root = os.path.expandvars(r"%LOCALAPPDATA%\R\win-library")
                if os.path.isdir(lib_root):
                    candidates = []
                    for p in _g.glob(os.path.join(lib_root, "*")):
                        if not os.path.isdir(p):
                            continue
                        # 用 (major, minor) 数字元组排序，正确处理 4.10 > 4.9
                        m = _re.match(r"^(\d+)\.(\d+)", os.path.basename(p))
                        ver = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
                        candidates.append((ver, p))
                    if candidates:
                        candidates.sort(reverse=True)
                        extra["R_LIBS_USER"] = candidates[0][1]

            t0 = time.time()
            try:
                proc = subprocess.Popen(
                    [rscript, "--no-save", "--no-restore", "--no-init-file", src],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=tmpdir,
                    env=_safe_env(extra),
                )
                out_b, err_b = proc.communicate(input=stdin.encode("utf-8"), timeout=self.timeout_sec)
            except subprocess.TimeoutExpired:
                proc.kill()
                try:
                    out_b, err_b = proc.communicate(timeout=2)
                except subprocess.TimeoutExpired:
                    out_b, err_b = b"", b""
                return RunResult(
                    ok=False,
                    stdout=_truncate(out_b or b"", MAX_STDOUT_BYTES).decode("utf-8", errors="replace"),
                    stderr="R 脚本运行超过 5 秒。",
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
