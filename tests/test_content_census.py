# -*- coding: utf-8 -*-
"""399 题字段完整性普查钉桩（l918-14，内容审计①）。

全量加载 5 语言题库（core.loader.load_language，399 题），断言：
  ① statement/答案字段（expected_output|expected_rows|tests|rubric 按键集）非空；
  ② difficulty 落在 1-5；
  ③ 缺 hints 的题数 == 4（精确钉 2026-09-19 现状——翻桩须有意：任何第 5 题丢 hints
     或现状 4 题被补齐都会让本用例红，强制内容审计知悉）。
只读题库文件，零写库零源码改动。
"""
import pytest

from core.loader import load_language

LANGS = ("python", "sql", "cpp", "r", "agent_dev")

def _all_problems():
    for lang in LANGS:
        for topic in load_language(lang):
            yield lang, topic.slug, topic.problems

def test_总数_399_且每题statement非空():
    total = 0
    for lang, slug, problems in _all_problems():
        for p in problems:
            total += 1
            assert p.statement and p.statement.strip(), f"{lang}/{slug}/{p.id} 题干为空"
    assert total == 399, f"题库总量漂移：{total} != 399（README 官方口径，变更须有意）"

def test_答案字段按键集非空():
    for lang, slug, problems in _all_problems():
        for p in problems:
            has_answer = any(
                getattr(p, key, None) for key in ("expected_output", "expected_rows", "tests", "rubric")
            )
            assert has_answer, f"{lang}/{slug}/{p.id} 四类答案字段全空"

def test_difficulty_落1到5():
    for lang, slug, problems in _all_problems():
        for p in problems:
            d = getattr(p, "difficulty", None)
            assert d is not None and 1 <= d <= 5, f"{lang}/{slug}/{p.id} difficulty={d!r} 越界"

def test_hints缺失数_精确钉4():
    missing = []
    for lang, slug, problems in _all_problems():
        for p in problems:
            if not getattr(p, "hints", None):
                missing.append(f"{lang}/{p.id}")
    expected = sorted([
        "agent_dev/07_write_spec/agent_dev/07_write_spec/05_spec_for_bugfix",
        "agent_dev/09_decompose/agent_dev/09_decompose/05_decompose_simple",
        "r/06_mixed_apa/r/06_mixed_apa/06_interpret_output",
        "r/16_mediation/r/16_mediation/05_explain_mediation",
    ])
    assert sorted(missing) == expected, f"缺 hints 名单漂移：{sorted(missing)}"
