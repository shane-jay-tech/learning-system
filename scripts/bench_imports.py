"""Measure import cost of each app-level module in a fresh interpreter."""
import subprocess
import sys

MODS = [
    ("streamlit", "import streamlit"),
    ("ui.styles", "import ui.styles"),
    ("ui.components (ace lazy)", "import ui.components"),
    ("core.progress", "import core.progress"),
    ("core.loader", "import core.loader"),
    ("core.recommend", "import core.recommend"),
    ("core.judge (ai chain)", "import core.judge"),
    ("ui.pages.language", "import ui.pages.language"),
    ("ui.pages.dashboard (pandas)", "import ui.pages.dashboard"),
]
for name, stmt in MODS:
    code = "import time; t0=time.perf_counter(); " + stmt + "; print('%.2f' % (time.perf_counter()-t0))"
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=180)
    val = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "ERR"
    print(f"{name:34} {val}s")
