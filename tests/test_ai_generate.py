import json
import pytest

import core.ai_generate as ai_gen


def test_strip_fences_basic():
    assert ai_gen._strip_fences('```json\n{"a":1}\n```') == '{"a":1}'
    assert ai_gen._strip_fences('```{"a":1}```') == '{"a":1}'
    assert ai_gen._strip_fences('{"a":1}') == '{"a":1}'


def test_parse_json_recovers_from_extra_text():
    text = '这是一段废话\n```json\n{"title":"t","expected_output":"x"}\n```\n好了'
    data = ai_gen._parse_json(text)
    assert data is not None
    assert data["title"] == "t"


def test_parse_json_returns_none_on_no_required_fields():
    assert ai_gen._parse_json('{"foo": 1}') is None


def test_generate_variant_uses_subprocess(monkeypatch):
    captured = {}

    class FakeProc:
        returncode = 0
        stdout = json.dumps({
            "title": "新题",
            "statement": "解释 ...",
            "starter_code": "# code",
            "expected_output": "8\n",
            "hints": ["提示一", "提示二"],
        }).encode("utf-8")
        stderr = b""

    def fake_run(cmd, capture_output, timeout):
        captured["cmd"] = cmd
        return FakeProc()

    monkeypatch.setattr(ai_gen.subprocess, "run", fake_run)
    out = ai_gen.generate_variant("python", {
        "id": "python/01_t/p1", "title": "原题", "statement": "...",
        "expected_output": "8\n", "difficulty": 1,
    })
    assert out is not None
    assert out["title"] == "新题"
    assert out["id"].startswith("AI_VARIANT::")
    assert "--model" in captured["cmd"]


def test_generate_variant_returns_none_on_failure(monkeypatch):
    """v0.3：单机单人删了 deepseek fallback；失败直接返回 None。"""
    class FakeProc:
        returncode = 1
        stdout = b""
        stderr = b""

    monkeypatch.setattr(ai_gen.subprocess, "run", lambda *a, **kw: FakeProc())
    assert ai_gen.generate_variant("python", {"id": "p", "title": "T", "expected_output": "y"}) is None


def test_generate_variant_returns_none_on_timeout(monkeypatch):
    def raise_timeout(*a, **kw):
        raise ai_gen.subprocess.TimeoutExpired(cmd="x", timeout=1)

    monkeypatch.setattr(ai_gen.subprocess, "run", raise_timeout)
    assert ai_gen.generate_variant("python", {"id": "p", "title": "T", "expected_output": "y"}) is None
