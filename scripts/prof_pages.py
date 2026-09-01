"""Profile the heavy pages to find hotspots.

Usage: .venv\\Scripts\\python.exe scripts/prof_pages.py [dashboard|home|paths]
"""
import cProfile
import pstats
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core.progress as progress_mod  # noqa: E402

import streamlit as _st_real  # noqa: E402


def _passthrough(*a, **kw):
    def deco(fn):
        return fn
    return deco


_st_real.cache_data = _passthrough
_st_real.cache_resource = _passthrough

sys.path.insert(0, str(ROOT / "scripts"))
from bench_pages import FakeSt, install_fake  # noqa: E402


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "dashboard"

    tmp = tempfile.mkdtemp(prefix="ls_prof_")
    db_copy = Path(tmp) / "progress.db"
    src = Path(ROOT) / "data" / "progress.db"
    if src.exists():
        shutil.copy(src, db_copy)
    progress_mod._DEFAULT_DB = str(db_copy)

    import ui.pages.dashboard as dashboard
    import ui.pages.home as home
    import ui.pages.path as path_page

    if target == "dashboard":
        mod, fn = dashboard, lambda: dashboard.render_dashboard()
    elif target == "home":
        mod, fn = home, lambda: home.render_home()
    else:
        mod, fn = path_page, lambda: path_page.render_path_list()

    install_fake(mod, FakeSt())
    fn()  # warmup
    prof = cProfile.Profile()
    prof.enable()
    fn()
    prof.disable()
    stats = pstats.Stats(prof)
    stats.sort_stats("cumulative")
    stats.print_stats(30)


if __name__ == "__main__":
    main()
