import os
import subprocess
from types import SimpleNamespace

import pytest

import core.runners.cpp_runner as cpp_mod
import core.runners.r_runner as r_mod
from core.runners.cpp_runner import CppRunner
from core.runners.r_runner import RRunner


class FakeProcess:
    def __init__(self, outputs=None, returncode=0):
        self.outputs = list(outputs or [(b"ok\n", b"")])
        self.returncode = returncode
        self.killed = False
        self.inputs = []

    def communicate(self, input=None, timeout=None):
        self.inputs.append((input, timeout))
        item = self.outputs.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    def kill(self):
        self.killed = True


def test_cpp_compiler_resolution_uses_path_then_fallback(monkeypatch):
    runner = CppRunner()
    monkeypatch.setattr(cpp_mod.shutil, "which", lambda name: r"C:\bin\g++.exe")
    assert runner._resolve_compiler() == r"C:\bin\g++.exe"

    monkeypatch.setattr(cpp_mod.shutil, "which", lambda name: None)
    monkeypatch.setattr(cpp_mod.os.path, "exists", lambda p: p == runner.fallback_paths[1])
    assert runner._resolve_compiler() == runner.fallback_paths[1]


def test_cpp_missing_compiler_returns_actionable_sandbox_error(monkeypatch):
    monkeypatch.setattr(CppRunner, "_resolve_compiler", lambda self: None)
    result = CppRunner().run("int main(){}")
    assert not result.ok
    assert result.error_kind == "sandbox"
    assert "g++" in result.stderr


def test_cpp_compile_timeout(monkeypatch):
    monkeypatch.setattr(CppRunner, "_resolve_compiler", lambda self: r"C:\bin\g++.exe")
    compile_proc = FakeProcess([subprocess.TimeoutExpired("g++", 7), (b"", b"")])
    monkeypatch.setattr(cpp_mod.subprocess, "Popen", lambda *a, **kw: compile_proc)
    killed = []
    monkeypatch.setattr(cpp_mod, "_kill_tree", lambda p: killed.append(p))
    result = CppRunner().run("int main(){}")
    assert result.timed_out
    assert result.error_kind == "timeout"
    assert "编译超时" in result.stderr
    assert killed == [compile_proc]  # 编译超时也走整棵进程树清理


def test_cpp_compile_error_is_decoded_and_truncated(monkeypatch):
    monkeypatch.setattr(CppRunner, "_resolve_compiler", lambda self: r"C:\bin\g++.exe")
    compile_proc = FakeProcess([(b"", "编译失败".encode("utf-8"))], returncode=1)
    monkeypatch.setattr(cpp_mod.subprocess, "Popen", lambda *a, **kw: compile_proc)
    result = CppRunner().run("broken")
    assert result.error_kind == "compile"
    assert result.exit_code == 1
    assert result.stderr == "编译失败"


def test_cpp_compile_error_gets_chinese_hint(monkeypatch):
    monkeypatch.setattr(CppRunner, "_resolve_compiler", lambda self: r"C:\bin\g++.exe")
    compile_proc = FakeProcess([(b"", b"main.cpp:3: error: expected ';' before '}'")], returncode=1)
    monkeypatch.setattr(cpp_mod.subprocess, "Popen", lambda *a, **kw: compile_proc)
    result = CppRunner().run("broken")
    assert "中文提示" in result.stderr
    assert "分号" in result.stderr


def test_cpp_success_uses_restricted_environment_and_stdin(monkeypatch):
    monkeypatch.setattr(CppRunner, "_resolve_compiler", lambda self: r"C:\tool\g++.exe")
    compile_proc = FakeProcess([(b"", b"")], returncode=0)
    proc = FakeProcess([(b"hello\n", b"warn")], returncode=0)
    procs = iter([compile_proc, proc])
    captured = {}

    def fake_popen(*args, **kwargs):
        captured.update(kwargs)
        return next(procs)

    monkeypatch.setattr(cpp_mod.subprocess, "Popen", fake_popen)
    result = CppRunner().run("int main(){}", stdin="input")
    assert result.ok
    assert result.stdout == "hello\n"
    assert result.stderr == "warn"
    assert proc.inputs[0][0] == b"input"
    assert captured["env"]["PATH"].split(os.pathsep)[0].lower().endswith("tool")


def test_cpp_runtime_timeout_kills_process(monkeypatch):
    monkeypatch.setattr(CppRunner, "_resolve_compiler", lambda self: r"C:\tool\g++.exe")
    compile_proc = FakeProcess([(b"", b"")], returncode=0)
    timeout = subprocess.TimeoutExpired("main.exe", 1)
    proc = FakeProcess([timeout, (b"partial", b"ignored")])
    procs = iter([compile_proc, proc])
    monkeypatch.setattr(cpp_mod.subprocess, "Popen", lambda *a, **kw: next(procs))
    monkeypatch.setattr(cpp_mod, "_kill_tree", lambda p: p.kill())
    result = CppRunner().run("int main(){}")
    assert result.timed_out
    assert result.stdout == "partial"
    assert proc.killed


def test_rscript_resolution_uses_path(monkeypatch):
    runner = RRunner()
    monkeypatch.setattr(r_mod.shutil, "which", lambda name: r"C:\R\Rscript.exe")
    assert runner._resolve_rscript() == r"C:\R\Rscript.exe"


def test_rscript_fallback_chooses_highest_numeric_version(monkeypatch):
    runner = RRunner()
    monkeypatch.setattr(r_mod.shutil, "which", lambda name: None)
    monkeypatch.setattr("glob.glob", lambda pattern: [r"C:\R\4.9\Rscript.exe", r"C:\R\4.10\Rscript.exe"] if pattern == runner.fallback_glob[0] else [])
    assert runner._resolve_rscript() == r"C:\R\4.10\Rscript.exe"


def test_r_missing_runtime_returns_sandbox_error(monkeypatch):
    monkeypatch.setattr(RRunner, "_resolve_rscript", lambda self: None)
    result = RRunner().run("print(1)")
    assert not result.ok
    assert result.error_kind == "sandbox"
    assert "Rscript" in result.stderr


def test_r_success_selects_highest_numeric_user_library(monkeypatch, tmp_path):
    monkeypatch.setattr(RRunner, "_resolve_rscript", lambda self: r"C:\R\Rscript.exe")
    monkeypatch.delenv("R_LIBS_USER", raising=False)
    monkeypatch.setattr(r_mod.os.path, "expandvars", lambda value: str(tmp_path))
    (tmp_path / "4.9").mkdir()
    (tmp_path / "4.10").mkdir()
    proc = FakeProcess([(b"[1] 2\n", b"")], returncode=0)
    captured = {}

    def fake_popen(*args, **kwargs):
        captured.update(kwargs)
        return proc

    monkeypatch.setattr(r_mod.subprocess, "Popen", fake_popen)
    result = RRunner().run("print(1+1)", stdin="x")
    assert result.ok
    assert result.stdout == "[1] 2\n"
    assert captured["env"]["R_LIBS_USER"].endswith("4.10")
    assert proc.inputs[0][0] == b"x"


def test_r_runtime_failure_and_timeout(monkeypatch):
    monkeypatch.setattr(RRunner, "_resolve_rscript", lambda self: r"C:\R\Rscript.exe")
    failed = FakeProcess([(b"", b"boom")], returncode=2)
    monkeypatch.setattr(r_mod.subprocess, "Popen", lambda *a, **kw: failed)
    result = RRunner().run("stop('boom')")
    assert not result.ok
    assert result.error_kind == "runtime"
    assert result.exit_code == 2

    timeout = subprocess.TimeoutExpired("Rscript", 5)
    hung = FakeProcess([timeout, timeout])
    monkeypatch.setattr(r_mod.subprocess, "Popen", lambda *a, **kw: hung)
    result = RRunner().run("repeat {}")
    assert result.timed_out
    assert result.error_kind == "timeout"
    assert hung.killed
