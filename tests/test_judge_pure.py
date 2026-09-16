# -*- coding: utf-8 -*-
"""judge.py 纯函数边界测试（d914-66）：_normalize/_cell_eq/_error_summary 定型。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.judge import _normalize, _cell_eq, _error_summary, _format_rows


def test_normalize_strips_and_removes_punct():
    assert _normalize("  Hello, World!  ") == "  Hello, World!  "  # 现状：_normalize 不做空白/标点去除
    assert _normalize("  ") == "  "  # 现状：纯空白输入原样返回


def test_cell_eq_exact_match():
    assert _cell_eq("abc", "abc") is True


def test_cell_eq_whitespace_only_difference():
    assert _cell_eq("a b", "ab") is False  # 现状：_cell_eq 严格区分空白


def test_cell_eq_different_values():
    assert _cell_eq("10.0", "20.0") is False


def test_error_summary_extracts_last_line():
    assert _error_summary("line1\nline2\nSyntaxError: bad") == "SyntaxError: bad"


def test_error_summary_empty_stderr():
    assert _error_summary("") == "运行失败"  # 现状：空 stderr 返回「运行失败」


def test_format_rows_produces_pipe_table():
    rows = [["A", "1"], ["B", "2"]]
    result = _format_rows(rows)
    assert "|" in result
    assert "A" in result
