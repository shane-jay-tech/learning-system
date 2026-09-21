# -*- coding: utf-8 -*-
"""SQL 多行题「行序承重」普查桩（l922-129，2026-09-22；只读，零改题面、零改判分）。

判分侧事实（`core/judge.py:96-100` `_rows_equal` 用 `zip()` 逐行逐格比对，`:219` 调用）
与 SQL 侧事实（**无 top-level ORDER BY 的查询，sqlite 不保证行序**）合起来构成一条跨层矛盾：
题面写了排序要求、`expected_rows` 又按位置比对，于是「行序不承重的题」实际是在考
"学员猜中引擎返回序"——学员不写 ORDER BY 也能判对，写了别的等价序反而可能判错。

本桩按 l922-126 的做法**钉现状**：
  · `test_多行SQL题行序全部承重` 标 `xfail(strict=True)`：断言"不写 ORDER BY 也能逐行判对的多行题 == 空集"。
    2026-09-22 @ HEAD 157d201 实测命中 7 题 ⇒ 断言必红 ⇒ 记为 xfail。
    **任何一侧改齐（题面把顺序变成真承重 / 判分改行集合比较 / 补 reference_answer 后重新核账）
    都会让命中集合变化，清空即转 XPASS＝报错**，届时请回来删桩并更新普查档，
    不许把 strict 摘掉、更不许放宽成永绿断言。
  · `test_机验口径未失效` 是普通断言：钉"可机验子集非空"，防止 hints 形态变化后上一条静默假绿。

清单与三类计数、三条出口见 `docs/insights/learn-sql-roworder-census-20260922.md`。
只读题库（`core.loader` 取 yaml、`core.runners.sql_runner` 走真 sqlite3 内存库），零写库、零网络。
复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_sql_roworder_fragile.py -q
"""
import pytest

from core.loader import load_language
from core.runners.sql_runner import SQLRunner


def _top_level_positions(sql, keyword):
    """返回 keyword 在**括号深度 0 且不在单引号串内**的出现位置。

    必须做深度判断：窗口函数 `RANK() OVER (ORDER BY score DESC)` 里的 ORDER BY
    剥掉会改行集，不是本桩关心的对象。
    """
    depth = 0
    in_str = False
    hits = []
    upper = sql.upper()
    i = 0
    while i < len(sql):
        ch = sql[i]
        if ch == "'":
            in_str = not in_str
        elif not in_str:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif depth == 0 and upper.startswith(keyword, i):
                before_ok = i == 0 or not (sql[i - 1].isalnum() or sql[i - 1] == "_")
                j = i + len(keyword)
                after_ok = j >= len(sql) or not (sql[j].isalnum() or sql[j] == "_")
                if before_ok and after_ok:
                    hits.append(i)
        i += 1
    return hits


def _strip_toplevel_order(sql):
    """剥掉 top-level ORDER BY（尾部整段）。含 top-level LIMIT 时返回 None（剥了会换行集，不可比）。"""
    orders = _top_level_positions(sql, "ORDER BY")
    if not orders:
        return None
    if _top_level_positions(sql, "LIMIT"):
        return None
    return sql[: orders[0]].rstrip().rstrip(";")


def _multi_row_sql_problems():
    out = []
    for topic in load_language("sql"):
        for p in topic.problems:
            if len(p.expected_rows or []) >= 2:
                out.append(p)
    return out


def _norm(rows):
    """单元格宽松面交给判分器口径，本桩只比"行序列是否相同"，故统一 stringify。"""
    return [[str(c) for c in r] for r in rows]


def _execute(runner, sql, setup_sql):
    res = runner.run(sql, expected={"setup_sql": setup_sql})
    if not getattr(res, "ok", False) or res.rows is None:
        return None
    return _norm(res.rows)


def _measure():
    """(可机验题 id 集, 行序不承重题 id 集)。

    可机验 = hints 里存在一条能整条执行且**逐行等于 expected_rows** 的 SELECT/WITH 语句
    （sql 题的 `reference_answer` 实测 54/54 为空，参考解只散落在 hints 文本里）。
    """
    runner = SQLRunner()
    checkable, fragile = set(), set()
    for p in _multi_row_sql_problems():
        expected = _norm(p.expected_rows)
        refs = [
            h.strip()
            for h in (p.hints or [])
            if h.strip().upper().startswith(("SELECT", "WITH"))
        ]
        matched = None
        for ref in refs:
            if _execute(runner, ref.rstrip(";"), p.setup_sql) == expected:
                matched = ref
                break
        if matched is None:
            continue
        checkable.add(p.id)
        stripped = _strip_toplevel_order(matched)
        if stripped is None:
            continue
        if _execute(runner, stripped, p.setup_sql) == expected:
            fragile.add(p.id)
    return checkable, fragile


def test_机验口径未失效():
    """可机验子集必须非空，否则下一条桩会因"什么都没测到"而假绿。"""
    problems = _multi_row_sql_problems()
    assert len(problems) >= 2, f"未取到 expected_rows>=2 的 sql 题（{len(problems)} 题），普查口径可能已失效"
    checkable, _ = _measure()
    assert checkable, (
        f"{len(problems)} 道多行题里没有一条 hints 参考解可整条执行并对上期望行"
        "⇒ 本桩退化为永假，请回来改取数口径（如改用 reference_answer 字段）"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "跨层矛盾（l922-129 钉，2026-09-22 @ 157d201）：判分按 expected_rows 位置逐行比对，"
        "而无 top-level ORDER BY 的查询 sqlite 不保证行序；实测有多道多行题"
        "「剥掉 ORDER BY 后仍逐行等于期望」⇒ 题面排序要求不承重、判分依赖引擎返回序。"
        "清单与三条出口见 docs/insights/learn-sql-roworder-census-20260922.md；"
        "命中集合清空即 XPASS＝本例转红，届时请删桩并回写普查档，勿放宽断言。"
    ),
)
def test_多行SQL题行序全部承重():
    """现状桩：断言"行序不承重的多行 SQL 题"为空集（实测非空 ⇒ 记 xfail）。"""
    _, fragile = _measure()
    assert fragile == set(), f"以下多行题不写 ORDER BY 也能逐行判对（行序不承重）：{sorted(fragile)}"
