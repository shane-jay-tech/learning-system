# -*- coding: utf-8 -*-
"""statement 数值 vs expected_output 一致性启发式（l918-15，内容审计②）。

落实 content-quality-sample-20260905.md:39 的建议（提出 14 天未落实）。

启发式分两级（控制误报）：
  强模式（本用例钉桩）——题干自陈期望值（「应该约 X」「期望：X」）而 expected_output
  数值不含 X → 语义矛盾，逐条列名。2026-09-19 全量 399 题实测 3 条（python 统计题族）：
    13_scipy_stats/01_one_sample_t（0.0254 vs 0.0612）／13_scipy_stats/04_chi2（0.1453 vs 0.1821）
    ／15_ab_text/01_ab_chi2（0.1370 vs 0.2167）
  宽模式（计数量词，误报高）——仅作清单输出不判定，见报告段。
修复该题（改 expected 或改题干）会让钉桩红＝有意翻桩，提醒同步更新本用例白名单。
"""
import re

import pytest

from core.loader import load_language

LANGS = ("python", "sql", "cpp", "r", "agent_dev")
ASSERT_PAT = re.compile(r"(?:应该约|应约为|期望约|期望：?)\s*([0-1]\.\d{2,4})")
OUT_NUM = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])")


def _known_conflicts():
    conflicts = []
    for lang in LANGS:
        for topic in load_language(lang):
            for p in topic.problems:
                eo = (p.expected_output or "").strip()
                if not eo:
                    continue
                for value in ASSERT_PAT.findall(p.statement or ""):
                    if value not in OUT_NUM.split(eo) and value not in eo:
                        conflicts.append((p.id, value))
    return sorted(conflicts)


def test_题干自陈期望值与expected_output一致():
    conflicts = _known_conflicts()
    # 白名单：2026-09-19 全量 399 题实测 3 条真矛盾（#13 语义矛盾家族：题干自陈期望值
    # 与 expected_output 数值不一致）。逐条修复后请同步更新白名单。
    assert conflicts == [
        ("python/13_scipy_stats/01_one_sample_t", "0.0254"),   # expected=0.0612
        ("python/13_scipy_stats/04_chi2", "0.1453"),           # expected=0.1821
        ("python/15_ab_text/01_ab_chi2", "0.1370"),            # expected=0.2167
    ], f"题干自陈期望值与 expected_output 矛盾面变化：{conflicts}"


def test_矛盾判定对良性样本不误报():
    """无自陈期望值的题（如 decorator 输出 3 行 hi、feature_importance 输出 4 行）不得入清单。"""
    assert not any(pid.endswith("05_param_decorator") or pid.endswith("02_feature_importance")
                   for pid, _ in _known_conflicts()), "宽语义误报混入强模式清单"
