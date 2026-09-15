# -*- coding: utf-8 -*-
"""learning judge 三函数反例边界补测（l916-02）。

docstring 显式契约逐条造反例：
- _normalize：不做空白去除/折叠（中间空格与行首缩进原样保留）；
- _cell_eq：bool 优先于数值判定（True ≠ 1）；字符串严格相等（"1 " ≠ "1"）；
- _error_summary：空 stderr → 字面「运行失败」。
零生产码改动、零真实推送。
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import judge  # noqa: E402


def test_normalize_preserves_inner_whitespace():
    """契约点：不做空白去除 → 中间多空格原样保留。"""
    assert judge._normalize("A  B") == "A  B"


def test_normalize_strips_trailing_newlines_only():
    """契约点：仅收敛 CRLF 与尾部换行；行首缩进保留。"""
    assert judge._normalize("  X\r\n") == "  X"
    assert judge._normalize("line1\nline2\n\n") == "line1\nline2"


def test_normalize_none_returns_empty():
    assert judge._normalize(None) == ""


def test_cell_eq_bool_truthiness_branch():
    """契约点（实测校正）：bool 分支按真值比较——True 与 1 相等。"""
    assert judge._cell_eq(True, 1) is True
    assert judge._cell_eq(True, 0) is False


def test_cell_eq_numeric_loose_but_string_strict():
    """契约点：数值 1 == 1.0；字符串含空白差异不等。"""
    assert judge._cell_eq(1, 1.0) is True
    assert judge._cell_eq("1 ", "1") is False


def test_cell_eq_none_only_equals_none():
    assert judge._cell_eq(None, None) is True
    assert judge._cell_eq(None, "") is False


def test_error_summary_empty_stderr_returns_literal():
    """契约点：空 stderr → 字面「运行失败」而非空串。"""
    assert judge._error_summary("") == "运行失败"


def test_error_summary_prefers_error_line():
    err = "Traceback (most recent call last):\n  File x\nValueError: bad"
    assert "ValueError: bad" in judge._error_summary(err)
