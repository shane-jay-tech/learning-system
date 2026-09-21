"""未知路由兜底的 AppTest 真渲染回归（l922-115）。

**为什么还要再写一份**：任务书「此兜底无测试、grep 无『未知路由』」这句锚点已过期——
`tests/test_ui_behavior.py` 的 `test_app_initial_state_sidebar_and_unknown_route`
早就用**假 st** 覆盖了「未知路由 → 有一条 error 含『未知路由』」。假件抓不到的是真渲染层的三件事，
本档补的正是这三件（详见 result 的锚点漂移留痕）：
  ① `render_error_notice` 经真 `st.error` 后，三要素（标题／原因／下一步）是否**完整**落到正文；
  ② 兜底之后点侧栏导航能否**真的恢复**——假件里 `st.rerun` 只是计数器，真件会重跑整棵脚本树；
  ③ 首屏 `route=home` 只有在真跑一遍脚本时才验证得到「默认路由不报错」。
另加一条源码级漂移哨兵（第 4 例）：侧栏能设进去的路由必须都在 app.py 的分发链里，
否则新加导航项忘了配渲染器，用户只会看到一张「未知路由」错误页——本仓已发生过同型问题
（`test_app_flow.py:65` 注释的「曾写错成 session_state.page」）。

全程 `LS_PROGRESS_DB` 指到 tmp_path，不碰真实 progress.db。
"""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

pytest.importorskip("streamlit.testing")
from streamlit.testing.v1 import AppTest  # noqa: E402

import app  # noqa: E402
import ui.components as components  # noqa: E402


def _app(tmp_path, monkeypatch):
    monkeypatch.setenv("LS_PROGRESS_DB", str(tmp_path / "route.db"))
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)


def test_first_screen_defaults_to_home_without_error(tmp_path, monkeypatch):
    """默认路由钉 home：首屏不得出现任何 error 横幅（setdefault 的真跑验证）。"""
    at = _app(tmp_path, monkeypatch)
    at.run()
    assert not at.exception
    assert at.session_state["route"] == "home"
    assert len(at.error) == 0


def test_unknown_route_renders_three_part_error_and_keeps_route(tmp_path, monkeypatch):
    """未知路由走 error 兜底：三要素齐、不抛异常、且**不吞掉**原 route 值。"""
    at = _app(tmp_path, monkeypatch)
    at.run()
    at.session_state["route"] = "bogus"
    at.run()

    assert not at.exception, "兜底段不得抛异常"
    assert len(at.error) == 1, f"应恰有一条 error 横幅，实得 {len(at.error)}"
    text = at.error[0].value
    assert "未知路由" in text
    assert "route=bogus" in text, f"原因要素要回显真实 route 值，正文：{text!r}"
    assert "从侧边栏导航重新选择页面" in text, "下一步动作是兜底的可恢复出口"
    # 兜底不擅自改路由：route 仍是 bogus（由用户点导航来改，而不是渲染侧偷偷复位）
    assert at.session_state["route"] == "bogus"


def test_unknown_route_recovers_via_sidebar_nav(tmp_path, monkeypatch):
    """兜底提示的「从侧栏重选」必须真能恢复：点🏠主页 → error 消失、route 回 home。"""
    at = _app(tmp_path, monkeypatch)
    at.run()
    at.session_state["route"] = "no_such_page"
    at.run()
    assert len(at.error) == 1

    home_btn = [b for b in at.button if b.label == "🏠 主页"]
    assert home_btn, "未知路由页仍须渲染出侧栏导航，否则用户没有出口"
    home_btn[0].click().run()

    assert not at.exception
    assert at.session_state["route"] == "home"
    assert len(at.error) == 0, "恢复后不得残留上一屏的未知路由横幅"


def _route_literals(source: str) -> set[str]:
    """从源码里抠出 app 用到的路由字面量（三种写法：分发比较、setattr 赋值、下标赋值）。"""
    found = set()
    patterns = (
        r'route\s*==\s*"([a-z_]+)"',
        r'st\.session_state\.route\s*=\s*"([a-z_]+)"',
        r'setattr\(st\.session_state,\s*"route",\s*"([a-z_]+)"\)',
        r'st\.session_state\[\s*"route"\s*\]\s*=\s*"([a-z_]+)"',
    )
    for pat in patterns:
        found.update(re.findall(pat, source))
    return found


def test_every_sidebar_route_is_dispatched():
    """漂移哨兵：侧栏（含 navigate_to_problem）能设进去的路由，必须都在 main 的分发链里。"""
    app_src = Path(app.__file__).read_text(encoding="utf-8")
    sidebar_routes = _route_literals(app_src.split("def main(")[0])
    navigate_routes = _route_literals(
        Path(components.__file__).read_text(encoding="utf-8")
        .split("def navigate_to_problem")[1]
        .split("\ndef ")[0]
    )
    dispatch_routes = _route_literals(app_src.split("def main(")[1])
    assert sidebar_routes, "哨兵自身失效：没从 _sidebar 段抠到任何路由字面量"
    assert "language" in navigate_routes
    missing = (sidebar_routes | navigate_routes) - dispatch_routes
    assert not missing, (
        f"这些路由能被设进去但没有渲染器，会落到未知路由兜底页：{sorted(missing)}"
    )
    # 未知路由分支的存在性也钉住：删掉 else 分支 = 静默白屏，比报错更糟
    assert "未知路由" in app_src
