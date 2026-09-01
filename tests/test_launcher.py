import importlib.machinery
import importlib.util
import socket
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture(scope="module")
def launcher():
    sys.modules.setdefault("webview", SimpleNamespace())
    path = Path(__file__).resolve().parents[1] / "launcher.pyw"
    loader = importlib.machinery.SourceFileLoader("launcher_under_test", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_splash_contains_brand_and_safe_static_status(launcher):
    html = launcher.splash_html()
    assert "编程学习平台" in html
    assert 'id="status"' in html
    assert "<script" not in html


def test_find_free_port_skips_busy_port(launcher):
    busy = socket.socket()
    busy.bind(("127.0.0.1", 0))
    busy.listen(1)
    port = busy.getsockname()[1]
    if port == 65535:
        busy.close()
        pytest.skip("no adjacent TCP port available")
    try:
        assert launcher.find_free_port(port, max_tries=2) == port + 1
    finally:
        busy.close()


def test_find_free_port_raises_when_range_is_busy(launcher):
    first = socket.socket()
    second = socket.socket()
    first.bind(("127.0.0.1", 0))
    first.listen(1)
    port = first.getsockname()[1]
    try:
        try:
            second.bind(("127.0.0.1", port + 1))
            second.listen(1)
        except OSError:
            pytest.skip("adjacent port was already unavailable")
        with pytest.raises(RuntimeError):
            launcher.find_free_port(port, max_tries=2)
    finally:
        first.close()
        second.close()


def test_health_probe_success_and_failure(launcher, monkeypatch):
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    response = Response()
    monkeypatch.setattr(launcher.urllib.request, "urlopen", lambda *a, **kw: response)
    assert launcher.is_health_ready(8511)
    # 4xx 不是就绪：把 404 当成功会让 webview 提前切到一个报错页面
    response.status = 404
    assert not launcher.is_health_ready(8511)
    response.status = 503
    assert not launcher.is_health_ready(8511)
    monkeypatch.setattr(launcher.urllib.request, "urlopen", lambda *a, **kw: (_ for _ in ()).throw(OSError()))
    assert not launcher.is_health_ready(8511)


def test_splash_status_json_escapes_text_and_swallows_closed_window(launcher):
    calls = []
    window = SimpleNamespace(evaluate_js=lambda script: calls.append(script))
    launcher._set_splash_status(window, 'quote " and newline\n')
    assert "textContent" in calls[0]
    assert '\\"' in calls[0]
    assert "\\n" in calls[0]

    closed = SimpleNamespace(evaluate_js=lambda script: (_ for _ in ()).throw(RuntimeError()))
    launcher._set_splash_status(closed, "ignored")


def test_non_windows_error_box_and_dpi_are_safe(launcher, monkeypatch, capsys):
    monkeypatch.setattr(launcher.os, "name", "posix")
    launcher.show_error_box("Title", "Message")
    assert "[Title] Message" in capsys.readouterr().err
    assert launcher._enable_dpi_awareness() is None


def test_singleton_lock_acquire_release_and_conflict(launcher):
    assert launcher.acquire_singleton_lock()
    try:
        assert not launcher.acquire_singleton_lock()  # 二次获取失败
    finally:
        if launcher._lock_socket is not None:
            launcher._lock_socket.close()
            launcher._lock_socket = None


def test_start_streamlit_backend_builds_command(launcher, monkeypatch, tmp_path):
    captured = {}
    fake_proc = SimpleNamespace(pid=1234)

    def fake_popen(cmd, cwd=None, stdout=None, stderr=None, creationflags=0):
        captured.update(cmd=cmd, cwd=cwd, stdout=stdout, stderr=stderr,
                        creationflags=creationflags)
        return fake_proc

    monkeypatch.setattr(launcher.subprocess, "Popen", fake_popen)
    # 重定向日志目录，避免测试写入真实 data/
    monkeypatch.setattr(launcher, "LOG_FILE", tmp_path / "launcher.log")
    proc = launcher.start_streamlit_backend(8511)
    assert proc is fake_proc
    assert captured["cmd"][0] == sys.executable
    assert "streamlit" in captured["cmd"]
    assert "8511" in captured["cmd"]
    assert "--server.headless" in captured["cmd"]
    assert "--server.fileWatcherType" in captured["cmd"]
    # 父进程日志句柄已关闭（子进程有自己的副本）
    assert captured["stdout"].closed


def test_terminate_backend_graceful_timeout_kill_and_idempotent(launcher):
    # 正常：terminate + wait 成功
    proc1 = SimpleNamespace(terminate=lambda: None, wait=lambda timeout: 0, kill=lambda: None)
    launcher.terminate_backend(proc1)

    # 超时：wait 抛 TimeoutExpired → kill
    killed = []
    proc2 = SimpleNamespace(
        terminate=lambda: None,
        wait=lambda timeout: (_ for _ in ()).throw(subprocess.TimeoutExpired("x", 4)),
        kill=lambda: killed.append(1),
    )
    launcher.terminate_backend(proc2)
    assert killed

    # 异常进程：terminate 抛错 → 吞掉不外抛
    proc3 = SimpleNamespace(
        terminate=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        wait=lambda timeout: 0, kill=lambda: None,
    )
    launcher.terminate_backend(proc3)

    # None 幂等
    launcher.terminate_backend(None)


def test_show_error_box_windows_messagebox_branch(launcher, monkeypatch):
    calls = []

    class FakeCtypes:
        class windll:
            class user32:
                @staticmethod
                def MessageBoxW(hwnd, message, title, flags):
                    calls.append((message, title, flags))

    monkeypatch.setattr(launcher.os, "name", "nt")
    monkeypatch.setitem(sys.modules, "ctypes", FakeCtypes)
    launcher.show_error_box("T", "M")
    assert calls and calls[0][1] == "T"


def test_enable_dpi_awareness_prefers_per_monitor_v2(launcher, monkeypatch):
    calls = []

    class FakeCtypes:
        @staticmethod
        def c_void_p(x):
            return x

        class windll:
            class user32:
                @staticmethod
                def SetProcessDpiAwarenessContext(ctx):
                    calls.append(("pmv2", ctx))
                    return 1  # 非零 = 成功

    monkeypatch.setattr(launcher.os, "name", "nt")
    monkeypatch.setitem(sys.modules, "ctypes", FakeCtypes)
    launcher._enable_dpi_awareness()
    assert calls and calls[0][0] == "pmv2"
