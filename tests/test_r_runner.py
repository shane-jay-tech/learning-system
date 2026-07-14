import pytest

from core.runners.r_runner import RRunner


def _r_available():
    return RRunner()._resolve_rscript() is not None


pytestmark = pytest.mark.skipif(not _r_available(), reason="Rscript not available; skipping R runner tests")


def test_hello_world():
    r = RRunner().run('cat("Hello, World!\\n")')
    assert r.ok
    assert "Hello, World!" in r.stdout


def test_runtime_error():
    r = RRunner().run('stop("boom")')
    assert not r.ok
    assert r.error_kind == "runtime"


def test_sandbox_when_no_rscript(monkeypatch):
    monkeypatch.setattr("core.runners.r_runner.shutil.which", lambda _: None)
    monkeypatch.setattr(RRunner, "fallback_glob", [])
    r = RRunner().run('cat("x")')
    assert not r.ok
    assert r.error_kind == "sandbox"
