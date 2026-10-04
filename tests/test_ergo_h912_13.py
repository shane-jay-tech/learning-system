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
    """修复②：每行列数上限（弃 min(n, 5)）＋ styles 的 1280px 中间断点。

    l922-120 语义调整（改断言不改实现）：本例原本钉的是字面量
    `st.columns(min(n, 4))` 在位，那等于把 h912-13 的**意图**（每行 ≤4 列、不许退回
    5 列挤压）钉死成**一个具体写法**。「各语言通过情况」一节改成 3+2 居中分行后，
    该字面量必然消失。现用三条等价把守替它：
      a) `min(n, 5)` 依旧不得回归（原意图的正面表述，保留）；
      b) 机械扫描 dashboard.py 里所有**字面量入参**的 st.columns 调用，槽位数必须 ≤4
         （`st.columns(spec)` 这类变量入参扫不到，交给 c) 的纯函数断言兜住）；
      c) 直接跑分行助手 `_lang_card_rows`：5 门语言排成 3+2，末行左右补等宽空槽居中，
         每行权重和恒为 3 ⇒ 每张卡恰好 1/3 行宽（比旧的 1/4 更宽松）。
    另加一条防回归：取模叠卡 `i % len(cols)` 不得再出现（它正是 4+1 断裂的成因）。
    1280/900 两个断点的原有断言逐字保留。
    """
    src = (PAGES / "dashboard.py").read_text(encoding="utf-8")
    assert "min(n, 5)" not in src
    # 取模叠卡（i % len(cols)）会把末行卡片塞回首列、造成 4+1 断裂，不得回归。
    # 只扫代码行：解释本处历史的整行注释会原文引用那个写法，不能算违规；
    # 同一行尾注释里的 # 不出现该写法，无需再剥。
    code = [ln for ln in src.splitlines() if not ln.lstrip().startswith("#")]
    assert all("i % len(cols)" not in ln for ln in code), "取模叠卡写法回归"

    literal_specs = re.findall(r"st\.columns\((\[[^\]]*\]|[0-9]+)\)", src)
    assert literal_specs, "dashboard.py 应仍有可静态扫描的字面量 st.columns 调用"
    for spec in literal_specs:
        slots = len(spec.split(",")) if spec.startswith("[") else int(spec)
        assert slots <= 4, f"每行列数超上限：st.columns({spec})"

    import ui.pages.dashboard as dashboard_page
    langs = [f"l{i}" for i in range(1, 8)]
    rows = list(dashboard_page._lang_card_rows(langs))
    assert [r[2] for r in rows[:2]] == [langs[:3], langs[3:6]]
    five = list(dashboard_page._lang_card_rows(langs[:5]))
    assert [r[2] for r in five] == [langs[:3], langs[3:5]], f"5 门语言应排 3+2：{five}"
    assert five[0][0] == [1, 1, 1] and five[0][1] == 0, "满行不补空槽（权重 ≤0 会被 st.columns 拒）"
    assert five[1][0] == [0.5, 1, 1, 0.5] and five[1][1] == 1, "末行须左右补等宽空槽才能居中"
    for spec, offset, chunk in five:
        assert sum(spec) == 3, f"行权重和须恒为 3（每卡 1/3 行宽）：{spec}"
        assert spec[offset:offset + len(chunk)] == [1] * len(chunk)
    assert list(dashboard_page._lang_card_rows([])) == [], "空语言表不该渲染出任何行"

    styles = STYLES.read_text(encoding="utf-8")
    # d913c-10：断点数值收敛为常量单源（_BP_MID/_BP_NARROW），占位符经 inject() 注入；
    # 断言常量定义与相对次序（保护意图不变：中间断点先于窄窗断点）。
    assert "_BP_MID = 1280" in styles
    assert "_BP_NARROW = 900" in styles
    assert styles.index("_BP_MID = 1280") < styles.index("_BP_NARROW = 900")
    styles = STYLES.read_text(encoding="utf-8")
    # d913c-10：断点数值收敛为常量单源（_BP_MID/_BP_NARROW），占位符经 inject() 注入；
    # 断言常量定义与相对次序（保护意图不变：中间断点先于窄窗断点）。
    assert "_BP_MID = 1280" in styles
    assert "_BP_NARROW = 900" in styles
    assert styles.index("_BP_MID = 1280") < styles.index("_BP_NARROW = 900")


def test_dashboard_no_silent_except():
    """修复③：dashboard 三处 except Exception: pass 全部改为 logger 记录，不再静默。

    l1002-63（l922-101 遗留降级）：原 `src.count("logger.debug(") >= 3` 源级计数断言
    已移除——该计数对异常路径的行为退化零判别力（只守历史事实）；异常路径覆盖由
    tests/test_dashboard_event_failures.py 的 28 例行为用例接管（含
    test_shown_event_failure_logs_debug_with_exc_info / test_click_event_failure_still_navigates_and_logs
    等直接断言 debug 日志的用例）。本测试保留"无静默 except＋logger 在册"两条结构断言。
    """
    src = (PAGES / "dashboard.py").read_text(encoding="utf-8")
    silent = re.findall(r"except Exception:\s*\n\s*pass", src)
    assert silent == [], f"仍有静默 except: {len(silent)} 处"
    assert "logger = logging.getLogger(__name__)" in src


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


