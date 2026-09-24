# -*- coding: utf-8 -*-
"""l924-32：成就墙末行居中的两轨断言（13/14/15 枚 = 余数 1/2/3 三夹具）。

背景：`_render_achievements` 旧写法每行恒 `st.columns(4)`，末行不满 4 时徽章从最左格
起填 ⇒ 右侧整段留白（靠左贴边），与卡片自身 text-align:center 的观感冲突。现改为复用
`_lang_card_rows`（l922-120 语言卡同款修法）：余数行左右各补 (4-n)/2 的等宽空槽。

**两轨互证，都不起 dev server、不截图**：
  A `test_last_row_centered_in_real_dom`：走 `streamlit.testing.v1.AppTest` 真渲染，
    从 element_tree 读回每行 `Column.weight`（浏览器里真正决定左右留白的量）。
    居中的充要读数是「徽章列左侧空槽权重和 == 右侧空槽权重和」，且每枚徽章权重恒 1/4
    （居中不以牺牲卡宽为代价）。
  B `test_last_row_centered_via_recording_double`：本仓在册失明面——
    `tests/test_ui_behavior.py::FakeStreamlit` 的 `columns` 桩是
    `lambda spec, *a, **kw: [Context() for _ in range(...)]`，**既不记录 spec 也不记录
    槽位下标**（`tabs`/`button`/`expander` 同样丢参），靠它断言"补了等宽空槽"会恒过。
    主班裁决＝多班共用基类**不改**，故本件对自己 new 出来的那个实例做 **实例级覆盖**
    （`setattr` 挂录制版 `columns`/`markdown`），把入参和下标取回来钉同一件事。

C/D 两条守住卷宗的"三态样式与 pct 提示行原样保留"（色值零改动）。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

pytest.importorskip("streamlit.testing")
from streamlit.testing.v1 import AppTest  # noqa: E402

import ui.components as components  # noqa: E402
import ui.pages.dashboard as dashboard_page  # noqa: E402
from core.achievements import ACHIEVEMENTS  # noqa: E402
from tests.test_ui_behavior import FakeStreamlit  # noqa: E402

PER_ROW = 4
# 三态样式现值（卷宗 :466-478，本单零改动；此处只读比对，不新色值）
STATE_STYLE = {
    "earned": ("#FAFAFA", "#5B5BD6", "1"),
    "approaching": ("#FFFBEB", "#F59E0B", "0.85"),
    "locked": ("#F1F5F9", "#E2E8F0", "0.4"),
}
STATE_CYCLE = ("earned", "approaching", "locked")
CARD_MARK = "text-align:center"


def _states(n: int) -> list[dict]:
    """前 n 枚在册成就（真 Achievement 对象，不新增不改内容），三态轮转。"""
    out = []
    for i, a in enumerate(ACHIEVEMENTS[:n]):
        state = STATE_CYCLE[i % 3]
        pct = 0.75 if state == "approaching" else 1.0
        out.append({"achievement": a, "state": state, "progress": pct})
    return out


def _patch_dom(monkeypatch, n: int) -> None:
    monkeypatch.setattr(dashboard_page, "check_achievements", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_progress_summary",
                        lambda dao: {"earned": n, "total": len(ACHIEVEMENTS)})
    monkeypatch.setattr(dashboard_page, "get_all_with_state", lambda dao: _states(n))


def _rows(at) -> list[list]:
    """AppTest 树里逐行的 Column 列表（文档序，只取 st.columns 产的 flex_container）。"""
    return [list(child.columns) for child in at.main.children.values()
            if getattr(child, "type", None) == "flex_container"]


def _badge_slots(cols: list) -> list[int]:
    """一行的哪些槽位真的落了徽章卡（空槽里没有 markdown 卡片）。"""
    return [k for k, c in enumerate(cols)
            if any(CARD_MARK in m.value for m in c.markdown)]


@pytest.mark.parametrize("n", [13, 14, 15])
def test_last_row_centered_in_real_dom(n, monkeypatch):
    """余数 1/2/3 三夹具：末行徽章两侧空槽权重和对齐，且每枚卡宽恒为 1/4 行宽。"""
    _patch_dom(monkeypatch, n)
    at = AppTest.from_string(
        "import ui.pages.dashboard as d\nd._render_achievements(None)\n",
        default_timeout=60,
    )
    at.run()
    assert not at.exception

    rows = _rows(at)
    assert len(rows) == -(-n // PER_ROW), f"行数应为向上取整(n/{PER_ROW})：{len(rows)}"
    full_rows, last = rows[:-1], rows[-1]
    for r in full_rows:
        assert [c.weight for c in r] == [1 / PER_ROW] * PER_ROW, "满行不该被动过"

    weights = [c.weight for c in last]
    assert sum(weights) == pytest.approx(1.0), f"行权重须归一：{weights}"
    slots = _badge_slots(last)
    assert slots == list(range(slots[0], slots[0] + n % PER_ROW)), f"徽章须连续占位：{slots}"
    assert all(abs(w - 1 / PER_ROW) < 1e-6 for w in weights[slots[0]:slots[-1] + 1]), (
        f"每张徽章仍须 1/{PER_ROW} 行宽（居中不许收窄）：{weights}"
    )
    left = sum(weights[:slots[0]])
    right = sum(weights[slots[-1] + 1:])
    assert left == pytest.approx(right), f"末行未居中：左留白 {left} != 右留白 {right}"
    assert n % PER_ROW == len(slots), f"末行徽章数应为余数：{n % PER_ROW} vs {len(slots)}"


@pytest.mark.parametrize("n,expected", [
    (13, [[1] * 4, [1] * 4, [1] * 4, [1.5, 1, 1.5]]),
    (14, [[1] * 4, [1] * 4, [1] * 4, [1, 1, 1, 1]]),
    (15, [[1] * 4, [1] * 4, [1] * 4, [0.5, 1, 1, 1, 0.5]]),
])
def test_last_row_centered_via_recording_double(n, expected, monkeypatch):
    """实例级覆盖共用假件的失明面，把 st.columns 的 spec 与徽章落位下标取回来。"""
    _patch_dom(monkeypatch, n)
    fake = FakeStreamlit()
    specs: list = []
    placed: list = []
    active = {"slot": None}

    class _Slot:
        def __init__(self, idx):
            self.idx = idx

        def __enter__(self):
            active["slot"] = self.idx
            return self

        def __exit__(self, *exc):
            active["slot"] = None
            return False

    def recording_columns(spec, *a, **kw):
        specs.append(list(spec))
        return [_Slot(k) for k in range(spec if isinstance(spec, int) else len(spec))]

    def recording_markdown(*a, **kw):
        if a and isinstance(a[0], str) and CARD_MARK in a[0]:
            placed.append(active["slot"])
        fake.calls.append(("markdown", a, kw))

    # 只覆盖这个实例（多班共用基类禁改，见模块 docstring）
    setattr(fake, "columns", recording_columns)
    setattr(fake, "markdown", recording_markdown)
    monkeypatch.setattr(dashboard_page, "st", fake)
    monkeypatch.setattr(components, "st", fake)

    dashboard_page._render_achievements(None)

    assert specs == expected, f"逐行 spec 不符（末行须左右补等宽空槽）：{specs}"
    assert len(placed) == n, f"应有 {n} 张徽章卡，实得 {len(placed)}"
    last_row_slots = placed[-(n % PER_ROW):]
    assert last_row_slots == list(range(1, 1 + n % PER_ROW)) or n % PER_ROW == PER_ROW, (
        f"末行徽章须落在居中后的槽位（0 号位是空槽）：{last_row_slots}"
    )
    assert placed[:n - (n % PER_ROW)] == [0, 1, 2, 3] * (n // PER_ROW), "满行落位不得漂移"


@pytest.mark.parametrize("n", [13, 14, 15])
def test_three_state_styles_and_pct_line_unchanged(n, monkeypatch):
    """卷宗判据④：三态 bg/border/opacity 与 approaching 的 pct 提示行原样保留。"""
    _patch_dom(monkeypatch, n)
    at = AppTest.from_string(
        "import ui.pages.dashboard as d\nd._render_achievements(None)\n",
        default_timeout=60,
    )
    at.run()
    cards = [m.value for row in _rows(at) for c in row for m in c.markdown
             if CARD_MARK in m.value]
    assert len(cards) == n
    seen = {"earned": 0, "approaching": 0, "locked": 0}
    for i, html in enumerate(cards):
        state = STATE_CYCLE[i % 3]
        bg, border, opacity = STATE_STYLE[state]
        assert f"background:{bg}" in html and f"border:2px solid {border}" in html \
            and f"opacity:{opacity}" in html, f"{state} 态样式漂移：{html[:160]}"
        if state == "approaching":
            assert "75%" in html, f"pct 提示行丢失：{html[:160]}"
            assert "color:#D97706" in html
        else:
            assert "font-size:10px" not in html, "非 approaching 不该冒出 pct 行"
        seen[state] += 1
    assert all(v > 0 for v in seen.values()), f"三态未全覆盖：{seen}"
