import core.ai_review as ar


class _FakeRun:
    stdout = "Hello"
    stderr = ""


def test_follow_up_calls_subprocess(monkeypatch):
    captured = {}

    class FakeProc:
        returncode = 0
        stdout = "AI 的具体回答".encode("utf-8")
        stderr = b""

    def fake_run(cmd, capture_output, timeout, env=None):
        captured["cmd"] = cmd
        return FakeProc()

    monkeypatch.setattr(ar.subprocess, "run", fake_run)
    out = ar.follow_up(
        lang="python",
        problem={"title": "T", "statement": "..."},
        code="print(1)",
        run_result=_FakeRun(),
        passed=True,
        initial_review="原评语",
        history=[],
        user_question="什么是 list comprehension？",
    )
    assert "AI" in out
    assert "--system" in captured["cmd"]
    sys_idx = captured["cmd"].index("--system") + 1
    assert "追问" in captured["cmd"][sys_idx]


def test_follow_up_includes_history(monkeypatch):
    captured = {"prompt": ""}

    class FakeProc:
        returncode = 0
        stdout = b"OK"
        stderr = b""

    def fake_run(cmd, capture_output, timeout, env=None):
        idx = cmd.index("--prompt") + 1
        captured["prompt"] = cmd[idx]
        return FakeProc()

    monkeypatch.setattr(ar.subprocess, "run", fake_run)
    history = [
        {"role": "user", "text": "前一个问题"},
        {"role": "ai", "text": "前一次回答"},
    ]
    ar.follow_up(
        lang="python",
        problem={"title": "T", "statement": "..."},
        code="print(1)",
        run_result=_FakeRun(),
        passed=True,
        initial_review="原评语",
        history=history,
        user_question="新问题",
    )
    p = captured["prompt"]
    assert "前一个问题" in p
    assert "前一次回答" in p
    assert "新问题" in p
    assert "原评语" in p


def test_follow_up_falls_back_to_deepseek(monkeypatch):
    """首选模型失败时 fallback 到链中第二个模型（快档：flash 失败退到 kimi）。"""
    calls = {"n": 0}

    class FakeProc:
        def __init__(self, ok):
            self.returncode = 0 if ok else 1
            self.stdout = b"deepseek answer" if ok else b""
            self.stderr = b""

    def fake_run(cmd, capture_output, timeout, env=None):
        calls["n"] += 1
        return FakeProc(calls["n"] == 2)

    monkeypatch.setattr(ar.subprocess, "run", fake_run)
    out = ar.follow_up(
        lang="python", problem={}, code="", run_result=_FakeRun(),
        passed=True, initial_review="r", history=[], user_question="q",
    )
    assert "deepseek answer" in out
    assert calls["n"] == 2


def test_follow_up_returns_fallback_when_all_fail(monkeypatch):
    class FakeProc:
        returncode = 1
        stdout = b""
        stderr = b""
    monkeypatch.setattr(ar.subprocess, "run", lambda *a, **kw: FakeProc())
    out = ar.follow_up(
        lang="python", problem={}, code="", run_result=_FakeRun(),
        passed=True, initial_review="r", history=[], user_question="q",
    )
    assert "AI" in out and "稍后" in out
