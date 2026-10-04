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


def main() -> int:
    # l1002-77（l923-32 遗留）：补 __name__ 守卫——此前模块级直跑，任何 dev 工具 import 本模块
    # 都会触发 9 次子进程调用（E3 结构事实）。守卫后 import 零副作用。
    for name, stmt in MODS:
        code = "import time; t0=time.perf_counter(); " + stmt + "; print('%.2f' % (time.perf_counter()-t0))"
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=180)
        val = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "ERR"
        print(f"{name:34} {val}s")
    return 0

if __name__ == "__main__":
    sys.exit(main())
