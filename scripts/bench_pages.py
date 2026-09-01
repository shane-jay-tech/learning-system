"""Benchmark server-side rerun cost of each page (fake-st harness, real core logic).

Usage: .venv\\Scripts\\python.exe scripts/bench_pages.py
Read-only by design: copies progress.db to a temp file so no real data is touched.
"""
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import core.progress as progress_mod  # noqa: E402

# 裸跑模式没有 Streamlit runtime：把 cache 装饰器换成直通，避免 bare-mode 报错
import streamlit as _st_real  # noqa: E402


def _passthrough(*a, **kw):
    def deco(fn):
        return fn
    return deco


_st_real.cache_data = _passthrough
_st_real.cache_resource = _passthrough


class State(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


class Ctx:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeSt:
    def __init__(self):
        self.session_state = State()

    def set_page_config(self, *a, **kw):
        pass

    def __getattr__(self, name):
        if name == "sidebar":
            return Ctx()
        if name == "tabs":
            return lambda labels, *a, **kw: [Ctx() for _ in labels]
        if name in {"container", "expander", "spinner", "form", "popover"}:
            return lambda *a, **kw: Ctx()
        if name == "columns":
            return lambda spec, *a, **kw: [Ctx() for _ in range(spec if isinstance(spec, int) else len(spec))]
        if name in {"button", "form_submit_button"}:
            return lambda label, *a, **kw: False
        if name == "radio":
            def _radio(label, options, *a, **kw):
                key = kw.get("key")
                if key and key in self.session_state:
                    return self.session_state[key]
                return options[0]
            return _radio
        if name == "text_area":
            def _ta(label, *a, **kw):
                key = kw.get("key")
                if key and key in self.session_state:
                    return self.session_state[key]
                return kw.get("value", "")
            return _ta
        if name == "progress":
            return lambda *a, **kw: None
        if name in {"markdown", "caption", "success", "warning", "info", "error", "code",
                    "metric", "download_button", "bar_chart", "line_chart", "dataframe", "write", "toast"}:
            return lambda *a, **kw: None
        if name == "rerun":
            return lambda: None
        raise AttributeError(name)

    def rerun(self):
        pass


def bench(name, fn, n=5):
    fn()  # warmup
    ts = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        ts.append((time.perf_counter() - t0) * 1000)
    ts.sort()
    print(f"  {name:<28} median={ts[len(ts)//2]:>7.1f}ms  min={ts[0]:>7.1f}ms  max={ts[-1]:>7.1f}ms")
    return ts[len(ts)//2]


def install_fake(module, fake):
    module.st = fake
    return fake


def main():
    # 用临时库副本，避免污染真实 progress.db
    tmp = tempfile.mkdtemp(prefix="ls_bench_")
    db_copy = Path(tmp) / "progress.db"
    src = Path(ROOT) / "data" / "progress.db"
    if src.exists():
        shutil.copy(src, db_copy)
    progress_mod._DEFAULT_DB = str(db_copy)

    import ui.pages.home as home
    import ui.pages.language as language
    import ui.pages.dashboard as dashboard
    import ui.pages.mistakes as mistakes
    import ui.pages.path as path_page

    print("== home ==")
    fake = install_fake(home, FakeSt())
    fake.session_state.setdefault("route", "home")
    bench("render_home (full body)", lambda: home.render_home())

    print("== language (python topic) ==")
    fake2 = install_fake(language, FakeSt())
    fake2.session_state.update({
        "route": "language", "selected_lang": "python",
        "selected_topic_idx": 0, "selected_problem_idx": 0,
        "selection": None, "ai_variants": {},
    })
    bench("render_language (typing rerun)", lambda: language.render_language(), n=3)

    print("== dashboard ==")
    fake3 = install_fake(dashboard, FakeSt())
    bench("render_dashboard (full)", lambda: dashboard.render_dashboard(), n=3)

    print("== mistakes ==")
    fake4 = install_fake(mistakes, FakeSt())
    bench("render_mistakes", lambda: mistakes.render_mistakes(), n=3)

    print("== paths list ==")
    fake5 = install_fake(path_page, FakeSt())
    bench("render_path_list", lambda: path_page.render_path_list(), n=3)


if __name__ == "__main__":
    main()
