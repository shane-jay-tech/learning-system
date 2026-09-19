# -*- coding: utf-8 -*-
"""judge SQL 行比较纯函数 characterization（l918-24，内容审计外判题区钉桩）。

直调 core/judge 的 _rows_equal（行数不等→False、单元格宽松相等、None 只与 None 相等）
与 _first_diff_cell（首差定位 (行,列,实际,期望)，行/列缺失用 None 表示，全等→None）。
judge.py 零改动（characterization＝钉现状）。
"""
from core.judge import _cell_eq, _first_diff_cell, _rows_equal


def test_行数不等直接False():
    actual = [[1, "a"], [2, "b"], [3, "c"]]
    expected = [[1, "a"], [2, "b"]]
    assert _rows_equal(actual, expected) is False


def test_空表与空表相等_空表对非空False():
    assert _rows_equal([], []) is True
    assert _rows_equal([], [[1]]) is False
    assert _rows_equal([[1]], []) is False


def test_列数不等的行_判False():
    actual = [[1, 2, 3]]
    expected = [[1, 2]]
    assert _rows_equal(actual, expected) is False


def test_宽松单元格语义():
    # 数值 int/float 等值
    assert _cell_eq(1, 1.0) is True
    # bool 按真值比较：True 与 1 相等（反直觉点，已显式化）
    assert _cell_eq(True, 1) is True
    # None 只与 None 相等
    assert _cell_eq(None, None) is True
    assert _cell_eq(None, 0) is False
    # 字符串严格含空白差异："1 " 与 "1" 不等（上游 _normalize 责任）
    assert _cell_eq("1 ", "1") is False


def test_全等表True():
    actual = [[1, "x", None], [2.0, "y", None]]
    expected = [[1.0, "x", None], [2, "y", None]]
    assert _rows_equal(actual, expected) is True


def test_首差定位_值不同():
    actual = [[1, "a"], [2, "X"]]
    expected = [[1, "a"], [2, "b"]]
    assert _first_diff_cell(actual, expected) == (2, 2, "X", "b")


def test_首差定位_行缺失_以None表示():
    actual = [[1, "a"]]
    expected = [[1, "a"], [2, "b"]]
    assert _first_diff_cell(actual, expected) == (2, 1, None, 2), "actual 缺行→实际值 None"


def test_首差定位_列缺失_以None表示():
    actual = [[1, "a"]]
    expected = [[1, "a", "extra"]]
    assert _first_diff_cell(actual, expected) == (1, 3, None, "extra"), "actual 缺列→实际值 None"


def test_无差异返回None():
    assert _first_diff_cell([[1, 2], [3, 4]], [[1, 2], [3, 4]]) is None
