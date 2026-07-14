"""Tests for ai_review offline fallback via shared friendly_errors (2026-06-17)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import ai_review


def test_offline_fallback_base_message_when_passed():
    msg = ai_review._offline_fallback(passed=True, stderr="")
    assert "AI 点评暂时不可用" in msg
    assert "离线提示" not in msg  # nothing to explain on a pass


def test_offline_fallback_translates_known_error():
    msg = ai_review._offline_fallback(passed=False,
                                      stderr="ZeroDivisionError: division by zero")
    assert "AI 点评暂时不可用" in msg
    if ai_review._fe is not None:
        assert "除以了零" in msg  # friendly translation appended


def test_offline_fallback_unknown_error_no_noise():
    msg = ai_review._offline_fallback(passed=False, stderr="SomethingTotallyWeird: zzz")
    # unknown -> generic fallback title -> we suppress the extra line to avoid noise
    assert "离线提示" not in msg


def test_offline_fallback_handles_empty_stderr():
    msg = ai_review._offline_fallback(passed=False, stderr="")
    assert "AI 点评暂时不可用" in msg
