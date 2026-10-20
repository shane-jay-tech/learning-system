# -*- coding: utf-8 -*-
"""l1007-03：stderr 展示面渲染断言（l1004-02 案3 落地批）。

钉死 stderr_block 新形态：多行 stderr → 摘要首行＋「展开完整 stderr」details＋全文保留；
单行短 stderr → 维持原逐字块（零回归）。零数值口径（渲染结构断言）。
"""
from __future__ import annotations

import streamlit as st_m

import ui.components as comp


class _FakeST:
    """collect st.markdown 调用（避免真 streamlit 运行时）。"""

    def __init__(self):
        self.md = []

    def markdown(self, body, **kw):
        self.md.append(body)


def test_multiline_stderr_gets_summary_and_details():
    st = _FakeST()
    orig = comp.st
    comp.st = st
    try:
        text = "Traceback (most recent call last):\n  File \"x.py\", line 1\nValueError: bad"
        comp.stderr_block(text)
    finally:
        comp.st = orig
    body = st.md[-1]
    assert "展开完整 stderr" in body, "details 展开口缺席"
    assert "ValueError: bad" in body, "全文应保留在 details 内"
    assert "Traceback (most recent call last):" in body
    assert "<details" in body


def test_single_line_short_stderr_stays_plain():
    st = _FakeST()
    orig = comp.st
    comp.st = st
    try:
        comp.stderr_block("short error line")
    finally:
        comp.st = orig
    body = st.md[-1]
    assert "short error line" in body
    assert "<details" not in body, "单行短 stderr 维持原逐字块（零回归面）"
