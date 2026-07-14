"""Test AI review prompt strategy selection by difficulty."""
from unittest.mock import patch, MagicMock

from core.ai_review import (
    _build_review_system_prompt,
    _SYSTEM_PROMPT_STRICT,
    _SYSTEM_PROMPT_BEGINNER_PASS,
    _SYSTEM_PROMPT_BEGINNER_FAIL,
)


def test_beginner_pass_uses_encouragement():
    prompt = _build_review_system_prompt(difficulty=1, passed=True, lang="python")
    assert prompt == _SYSTEM_PROMPT_BEGINNER_PASS
    assert "自信心" in prompt
    assert "做对了什么" in prompt


def test_beginner_fail_uses_gentle_correction():
    prompt = _build_review_system_prompt(difficulty=2, passed=False, lang="python")
    assert prompt == _SYSTEM_PROMPT_BEGINNER_FAIL
    assert "变量追踪" in prompt
    assert "一个最关键的问题" in prompt


def test_advanced_uses_strict_review():
    prompt = _build_review_system_prompt(difficulty=3, passed=True, lang="python")
    assert prompt == _SYSTEM_PROMPT_STRICT
    assert "代码品质" in prompt


def test_difficulty_4_uses_strict():
    prompt = _build_review_system_prompt(difficulty=4, passed=False, lang="cpp")
    assert prompt == _SYSTEM_PROMPT_STRICT


def test_difficulty_5_uses_strict():
    prompt = _build_review_system_prompt(difficulty=5, passed=True, lang="sql")
    assert prompt == _SYSTEM_PROMPT_STRICT


def test_beginner_pass_no_mandatory_critique():
    prompt = _build_review_system_prompt(difficulty=1, passed=True, lang="python")
    assert "即使代码完全正确，也要给至少 1 条可改进点" not in prompt
    assert "肯定" in prompt or "鼓励" in prompt


def test_beginner_fail_limits_code_examples():
    prompt = _build_review_system_prompt(difficulty=2, passed=False, lang="r")
    assert "不贴超过 2 行" in prompt
