"""Smoke test: boot streamlit headless, poll health, then kill."""
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

proc = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
     "--server.port", "8599", "--server.headless", "true",
     "--browser.gatherUsageStats", "false", "--server.fileWatcherType", "none"],
    stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, cwd=str(ROOT),
)
t0 = time.perf_counter()
ready = False
try:
    for _ in range(150):
        if proc.poll() is not None:
            print("streamlit exited early rc=%s" % proc.returncode)
            break
        try:
            with urllib.request.urlopen("http://127.0.0.1:8599/_stcore/health", timeout=1) as r:
                if r.status < 500:
                    ready = True
                    break
        except Exception:
            pass
        time.sleep(0.2)
    elapsed = time.perf_counter() - t0
    print("health ready: %s (%.1fs)" % (ready, elapsed))
finally:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
