# -*- coding: utf-8 -*-
"""dashboard 报告生成状态的跨路由持久桩（l922-121）。

钉的是 ui/pages/dashboard.py 的 **报告区**（磁盘实况 :215-259；
任务书锚点写的 :184/:186/:191 已整体漂移 +54 行，按磁盘实况修正）：

- :238 `if st.session_state.get("last_report_md"):` —— 下载区的存在性**只看 session_state**，
  不看本次是否点了按钮 ⇒ 「生成后切走再回，按钮没点也还在」这条语义全靠这里；
- :227/:236 `last_report_days` = 7 / 30 —— 周报与月报共用一个键，后点者覆盖；
- :245/:253 `file_name=f"learning_report_{date.today().isoformat()}.md|html"`
  —— 文件名日期段取**渲染当日**，不是报告生成日。

FakeStreamlit 驱动「点生成月报 → 清空组件调用记录 → 二次渲染（按钮全不点）」，
复现真实的路由切换。只加测试，不改 ui/pages/dashboard.py。
"""
from datetime import date

import pytest

import app  # noqa: F401  # 与 test_ui_behavior 同桩模式：app 侧 import 预绑定 st
import ui.components as components
import ui.pages.dashboard as dashboard_page
from tests.test_dashboard_page_render import DashboardFakeStreamlit, _dao
from tests.test_ui_behavior import Context


def _fake():
    """在既有 DashboardFakeStreamlit 之上补 expander / button 录制（不改既有桩类）。

    - 基类把 expander 当纯上下文管理器、不留标签，「预览报告」就无从断言；
    - 基类 button 只回布尔值、不落 calls，「区里一个按钮都没有」这种假绿无从排除。
    FakeStreamlit.__getattr__ 只在常规属性查找失败时触发，显式挂实例方法即可覆盖。
    """
    fake = DashboardFakeStreamlit()

    def expander(*a, **kw):
        fake.calls.append(("expander", a, kw))
        return Context()

    def button(label, *a, **kw):
        fake.calls.append(("button", (label,), kw))
        return fake.buttons.get(label, False)

    fake.expander = expander
    fake.button = button
    return fake


def _wire(monkeypatch, fake, buttons=None):
    """把 dashboard 的重依赖打桩；报告生成三件套记录 days 入参后返回可辨产物。

    返回的 list 是 generate_report 实际收到的 days 序列（按调用顺序）。
    """
    # 显式覆盖：传空 dict 表示「本轮一个按钮都不点」，不能沿用上一轮的按键态
    fake.buttons = dict(buttons or {})
    monkeypatch.setattr(dashboard_page, "st", fake)
    monkeypatch.setattr(components, "st", fake)
    monkeypatch.setattr(dashboard_page, "ProgressDAO", lambda: _dao())
    monkeypatch.setattr(dashboard_page, "check_achievements", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_progress_summary",
                        lambda dao: {"earned": 2, "total": 22})
    monkeypatch.setattr(dashboard_page, "get_all_with_state", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_achievement", lambda aid: {"name": f"成就{aid}"})
    monkeypatch.setattr(dashboard_page, "recommend", lambda n=5, dao=None: [])
    monkeypatch.setattr(dashboard_page, "cross_recommend", lambda *a, **kw: [])
    import core.loader as _loader
    monkeypatch.setattr(_loader, "load_language", lambda lang: [])
    seen = getattr(fake, "_seen_days", None)
    if seen is None:
        seen = []
        fake._seen_days = seen  # 同一 fake 多次 _wire 共用一条调用流水，便于断言「二次渲染不重生」
    monkeypatch.setattr(dashboard_page, "generate_report",
                        lambda dao, days=7: seen.append(days) or {"days": days})
    monkeypatch.setattr(dashboard_page, "report_to_markdown",
                        lambda report: f"正文#md#{report['days']}")
    monkeypatch.setattr(dashboard_page, "report_to_html",
                        lambda report: f"正文#html#{report['days']}")
    return seen


def _report_downloads(fake):
    """只筛报告区的 download_button（学习数据区也有一个，须按文件名前缀排除）。"""
    return [c for c in fake.calls
            if c[0] == "download_button"
            and str(c[2].get("file_name", "")).startswith("learning_report_")]


def _对外文案(fake):
    """报告下载区里用户可见/落盘可名的部分：按钮文案、文件名、mime、help（不含正文）。"""
    return [(c[1][0], c[2].get("file_name"), c[2].get("mime"), c[2].get("help"))
            for c in _report_downloads(fake)]


def test_未生成报告时下载区整块不出现(monkeypatch):
    """:238 假分支：session_state 为空 ⇒ 一个 learning_report_* 下载按钮都不该有。"""
    fake = _fake()
    _wire(monkeypatch, fake)
    dashboard_page._render_dashboard_body(_dao())
    assert _report_downloads(fake) == []
    assert "last_report_md" not in fake.session_state
    # 对照组：生成入口两个按钮本轮确实渲染到了（否则上面的空集只是「整段没跑」的假绿）
    labels = [c[1][0] for c in fake.calls if c[0] == "button"]
    assert {"生成周报", "生成月报"} <= set(labels), labels


def test_点生成月报_days30_落进session(monkeypatch):
    """:229-236 月报分支：generate_report 收到 days=30，三个 last_report_* 键都写进 session_state。"""
    fake = _fake()
    seen = _wire(monkeypatch, fake, {"生成月报": True})
    dashboard_page._render_dashboard_body(_dao())
    assert seen == [30], f"月报应只调一次 generate_report(days=30)，实为 {seen}"
    assert fake.session_state["last_report_days"] == 30
    assert fake.session_state["last_report_md"] == "正文#md#30"
    assert fake.session_state["last_report_html"] == "正文#html#30"


def test_切走再回未点按钮下载区与预览仍在且days保持30(monkeypatch):
    """核心持久语义：第一次渲染点月报，清空调用记录后二次渲染（按钮全不点）。

    断言下载区两块（.md/.html）+ 预览 expander + 预览正文都还在，days 仍是 30
    —— 证明持久的是 session_state 而不是本次渲染的局部量。
    """
    fake = _fake()
    seen = _wire(monkeypatch, fake, {"生成月报": True})
    dao = _dao()
    dashboard_page._render_dashboard_body(dao)
    fake.calls.clear()

    # 同一 fake（同 session_state），本次不点任何按钮；seen 复用最证明没重复生成
    assert _wire(monkeypatch, fake, {}) is seen
    dashboard_page._render_dashboard_body(dao)

    assert seen == [30], "二次渲染不该重新生成报告（生成只由按钮触发）"
    dl = _report_downloads(fake)
    assert len(dl) == 2, f"应有 .md 与 .html 两个报告下载按钮，实为 {len(dl)}"
    mimes = sorted(str(c[2].get("mime")) for c in dl)
    assert mimes == ["text/html", "text/markdown"], mimes
    assert fake.session_state["last_report_days"] == 30
    exp = [c[1][0] for c in fake.calls if c[0] == "expander"]
    assert "预览报告" in exp, exp
    md_marks = [str(a[0]) for name, a, _ in fake.calls if name == "markdown"]
    assert "正文#md#30" in md_marks, "预览正文应回显 session 里的 md，而非重新生成"


def test_下载文件名日期段为渲染当日(monkeypatch):
    """:245/:253 file_name 含 date.today().isoformat()，且 .md/.html 后缀各就各位。"""
    fake = _fake()
    _wire(monkeypatch, fake, {"生成月报": True})
    dao = _dao()
    dashboard_page._render_dashboard_body(dao)
    fake.calls.clear()
    _wire(monkeypatch, fake, {})
    dashboard_page._render_dashboard_body(dao)

    today = date.today().isoformat()
    names = sorted(str(c[2]["file_name"]) for c in _report_downloads(fake))
    assert names == [f"learning_report_{today}.html", f"learning_report_{today}.md"], names
    assert all(today in n for n in names), names


def test_周报与月报共用days键后点者覆盖(monkeypatch):
    """:227 与 :236 写同一个键：同一帧两个按钮都为真时月报（后段）胜出，days=30。"""
    fake = _fake()
    seen = _wire(monkeypatch, fake, {"生成周报": True, "生成月报": True})
    dashboard_page._render_dashboard_body(_dao())
    assert seen == [7, 30], f"应先周报后月报，实为 {seen}"
    assert fake.session_state["last_report_days"] == 30, "后点者覆盖"
    assert fake.session_state["last_report_md"] == "正文#md#30"


def test_现状桩_days对下载区对外文案零影响(monkeypatch):
    """:240 `days = st.session_state.get("last_report_days", 7)` 是**死局部量**——赋值后整块未再引用。

    口径：周报帧与月报帧的报告下载区「按钮文案/文件名/mime/help」逐项相等，
    只有 session 里的 days 不同 ⇒ 用户无法从下载区分辨自己拿到的是周报还是月报。
    这属体验缺陷（已登记交主班，本单不改码），本例钉住**现状**，
    同时挡住「以为文件名会带 week/month 后缀」这类不存在的契约。
    """
    def capture(btn_label):
        f = _fake()
        _wire(monkeypatch, f, {btn_label: True})
        dao = _dao()
        dashboard_page._render_dashboard_body(dao)
        f.calls.clear()
        _wire(monkeypatch, f, {})
        dashboard_page._render_dashboard_body(dao)
        return f.session_state["last_report_days"], _对外文案(f)

    monthly = capture("生成月报")
    weekly = capture("生成周报")
    assert monthly[0] == 30 and weekly[0] == 7, (monthly[0], weekly[0])
    assert monthly[1] == weekly[1], f"days 意外渗进对外文案：\n月报 {monthly[1]}\n周报 {weekly[1]}"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
