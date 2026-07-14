"""Quick environment probe for the learning system.

Checks: Python version, sqlite3, llm_call.py, g++ (C++), Rscript (R).
Prints ASCII-only output (Windows GBK consoles cannot render emoji).
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


LLM_SCRIPT = os.environ.get("LLM_SCRIPT", "D:/code/scripts/llm_call.py")


def _check(name: str, ok: bool, detail: str = "") -> bool:
    mark = "[OK] " if ok else "[--] "
    line = f"{mark}{name:<20}"
    if detail:
        line += " " + detail
    print(line)
    return ok


def main() -> int:
    print("learning-system health check")
    print("-" * 40)

    py_ok = sys.version_info >= (3, 10)
    _check("python >= 3.10", py_ok, f"got {sys.version.split()[0]}")

    try:
        import sqlite3  # noqa: F401
        _check("sqlite3 module", True)
    except ImportError:
        _check("sqlite3 module", False, "stdlib import failed")

    llm_ok = Path(LLM_SCRIPT).exists()
    _check("llm_call.py", llm_ok, LLM_SCRIPT if llm_ok else f"missing: {LLM_SCRIPT}")

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        from core.runners.cpp_runner import CppRunner
        from core.runners.r_runner import RRunner
        gpp = CppRunner()._resolve_compiler()
        rscript = RRunner()._resolve_rscript()
    except Exception:
        gpp = shutil.which("g++")
        rscript = shutil.which("Rscript")
    _check("g++ (for C++)", bool(gpp), gpp or "install MinGW and add to PATH to enable C++ problems")
    _check("Rscript (for R)", bool(rscript), rscript or "install R and add bin/ to PATH to enable R problems")

    try:
        import streamlit  # noqa: F401
        _check("streamlit", True, getattr(streamlit, "__version__", ""))
    except ImportError:
        _check("streamlit", False, "run: pip install -r requirements.txt")

    try:
        import yaml  # noqa: F401
        _check("pyyaml", True)
    except ImportError:
        _check("pyyaml", False, "run: pip install -r requirements.txt")

    # Security mode display
    from core.config import get_runner_security_mode, is_public_deploy
    mode = get_runner_security_mode()
    public = is_public_deploy()
    _check("runner security mode", True, f"{mode}" + (" (PUBLIC - code execution DISABLED)" if public else " (local - code execution enabled)"))

    print("-" * 40)
    print("Tip: missing g++/Rscript only blocks the corresponding language; Python and SQL still work.")
    if not public:
        print("Security: running in LOCAL mode. DO NOT expose to public network.")
        print("          Set RUNNER_SECURITY_MODE=public to disable code execution.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
