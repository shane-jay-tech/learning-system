import importlib.machinery
import importlib.util
import socket
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
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    response = Response()
    monkeypatch.setattr(launcher.urllib.request, "urlopen", lambda *a, **kw: response)
    assert launcher.is_health_ready(8511)
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
