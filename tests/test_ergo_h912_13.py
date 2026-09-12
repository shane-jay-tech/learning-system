"""h912-13 人体工学修复批断言（布局常量/断点/异常不再静默——源级机械断言）。"""

from __future__ import annotations

import re
from pathlib import Path

PAGES = Path(__file__).resolve().parents[1] / "ui" / "pages"
STYLES = Path(__file__).resolve().parents[1] / "ui" / "styles.py"


def test_home_overview_renders_before_hero_blocks():
    """修复①：总览区块先于 hero/下一步/路径卡渲染（首屏优先露数据）。"""
    src = (PAGES / "home.py").read_text(encoding="utf-8")
    overview = src.index('section_title("总览")')
    next_action = src.index("_render_next_action(dao")
    path_cards = src.index("_render_path_cards()")
    assert overview < next_action < path_cards


def test_dashboard_column_cap_and_1280_breakpoint():
    """修复②：列数上限 4（弃 min(n,5)），styles 增加 1280px 中间断点。"""
    src = (PAGES / "dashboard.py").read_text(encoding="utf-8")
    assert "st.columns(min(n, 4))" in src
    assert "min(n, 5)" not in src
    styles = STYLES.read_text(encoding="utf-8")
    assert "@media (max-width: 1280px)" in styles
    assert styles.index("@media (max-width: 1280px)") < styles.index("@media (max-width: 900px)")


def test_dashboard_no_silent_except():
    """修复③：dashboard 三处 except Exception: pass 全部改为 logger 记录，不再静默。"""
    src = (PAGES / "dashboard.py").read_text(encoding="utf-8")
    silent = re.findall(r"except Exception:\s*\n\s*pass", src)
    assert silent == [], f"仍有静默 except: {len(silent)} 处"
    assert "logger = logging.getLogger(__name__)" in src
    assert src.count("logger.debug(") >= 3


def test_home_days_since_exception_logged(caplog):
    """p912-39 遗留核销：home._days_since 异常分支不再静默（logger.debug＋哨兵 9999）。

    用通用 __getattr__ 桩一次补齐 DAO 面（逐属性补桩已证明是无底洞——render 链会
    连续触达 list_mistakes/daily_streak 等）；只关心 debug 日志是否发出。
    """
    import ui.pages.home as home_mod

    class _BoomDAO:
        logged = []

        def __getattr__(self, name):  # 任意 DAO 方法 → 返回空安全值
            def _any(*a, **k):
                _BoomDAO.logged.append(name)
                return []
            return _any

        def get_meta_ts(self, _k):
            _BoomDAO.logged.append("get_meta_ts")
            return "not-a-date"  # strptime 失败 → 走 _days_since 异常分支

    dao = _BoomDAO()
    with caplog.at_level("DEBUG", logger="ui.pages.home"):
        try:
            home_mod._render_ai_pulse(dao)
        except Exception:
            pass  # 渲染链后续依赖 streamlit 上下文，与本断言无关
    assert "时间戳解析失败" in caplog.text


