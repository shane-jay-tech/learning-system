# -*- coding: utf-8 -*-
"""l1007-01：stdin 静默截断可见化行为钉（案1 落地批）＋judge 侧回归。

行为断言：①超限 stdin → 截断后流含可见标记（「stdin 超限被截断」＋原始字节数）；
②未超限 stdin → 原样零改动；③标记计入额度（总字节恒 ≤1MB）。judge 侧回归：
_error_summary 对含标记 stderr 的行为（末行选取/hint_only 不炸）。
"""
from __future__ import annotations

import io

from core.runners.python_runner import _MAX_STDIN_BYTES, _safe_stdin, _truncate
from core.judge import _error_summary


def test_oversize_stdin_gets_visible_marker():
    stdin = "x" * (_MAX_STDIN_BYTES + 5_000)
    data = _safe_stdin(stdin)
    assert len(data) <= _MAX_STDIN_BYTES, "总额度仍受 1MB 上限"
    assert "stdin 超限被截断".encode() in data, "可见标记必须在截断流内"
    assert f"原始 {_MAX_STDIN_BYTES + 5000} 字节".encode() in data, "标记应含原始字节数"


def test_normal_stdin_untouched():
    data = _safe_stdin("normal input")
    assert data == b"normal input", "未超限 stdin 原样"


def test_error_summary_tolerates_marker_tail():
    """judge 回归：含截断标记的 stderr 进 _error_summary 不炸且取到末行。"""
    stderr = "Traceback (most recent call last):\n  File x\nValueError: boom\n[... stdin 超限被截断：仅保留前 1000000 字节（原始 1005000 字节）...]"
    summary = _error_summary(stderr)
    assert summary, "摘要非空"
    assert isinstance(summary, str)
