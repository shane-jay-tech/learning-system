import html
import streamlit as st

# streamlit_ace 的 import 链实测 ~0.5s：惰性加载，把成本挪到第一次
# 真正渲染编辑器时（语言页），首页/首屏不再替它付费。
_HAS_ACE = False
_ACE_LOADED = False
st_ace = None


def _ensure_ace():
    global _HAS_ACE, _ACE_LOADED, st_ace
    if _ACE_LOADED:
        return
    _ACE_LOADED = True
    try:
        from streamlit_ace import st_ace as _ace
        st_ace = _ace
        _HAS_ACE = True
    except Exception:
        st_ace = None
        _HAS_ACE = False


# 5 个语言的元数据——所有 UI 都从这里取
LANG_META = {
    "python":    {"name": "Python",    "icon": "🐍",  "tagline": "通用编程入门首选",                          "ace": "python"},
    "sql":       {"name": "SQL",       "icon": "🗃️", "tagline": "和数据库对话的语言",                        "ace": "sql"},
    "cpp":       {"name": "C++",       "icon": "⚙️", "tagline": "高性能的编译型语言",                        "ace": "c_cpp"},
    "r":         {"name": "R",         "icon": "📊",  "tagline": "统计分析与数据可视化",                      "ace": "r"},
    "agent_dev": {"name": "Agent 开发", "icon": "🤖", "tagline": "用 Claude Code 这类 agent 高效开发个人工具", "ace": "python"},
}

# 单一真实来源——所有页面 import 这个，避免列表多处定义不一致
ALL_LANGS = list(LANG_META.keys())


def navigate_to_problem(lang: str, topic_slug: str | None = None, problem_id: str | None = None):
    """Unified navigation helper — all pages use this to jump to a problem.

    不带 topic_slug（如侧栏「按语言刷题」）时重置专题/题目索引：
    否则残留的旧索引 + 持久化选择状态会把用户带回上一语言的任意位置。
    """
    st.session_state.route = "language"
    st.session_state.selected_lang = lang
    if topic_slug is None:
        st.session_state.selected_topic_idx = 0
        st.session_state.selected_problem_idx = 0
        # 清掉该语言的专题控件持久状态，让它按 selected_topic_idx=0 重建
        st.session_state.pop(f"topic_radio_{lang}", None)  # 清理旧版本遗留状态
        st.session_state.pop(f"topic_select_{lang}", None)
        for state_key in list(st.session_state.keys()):
            if state_key.startswith(f"problem_select_{lang}_"):
                st.session_state.pop(state_key, None)
    st.session_state.selection = {
        "lang": lang,
        "topic_slug": topic_slug,
        "problem_id": problem_id,
    }
    st.session_state.pop("last_judge_result", None)
    st.rerun()


def code_highlight_lang(lang: str) -> str:
    """st.code(...) / Pygments 用的语言名（和 ace 体系不同）。"""
    return {
        "python": "python",
        "sql": "sql",
        "cpp": "cpp",
        "r": "r",
        "agent_dev": "python",
    }.get(lang, "text")


def code_editor(value: str, lang: str, key: str, height: int = 540) -> str:
    _ensure_ace()
    if _HAS_ACE:
        ace_lang = LANG_META.get(lang, {}).get("ace", "text")
        return st_ace(
            value=value,
            language=ace_lang,
            theme="tomorrow_night",
            keybinding="vscode",
            font_size=15,
            tab_size=4,
            wrap=False,
            show_gutter=True,
            show_print_margin=False,
            auto_update=True,
            min_lines=20,
            max_lines=36,
            key=key,
        )
    return st.text_area("code", value=value, height=height, key=key, label_visibility="collapsed")


def hero(title: str, subtitle: str = ""):
    st.markdown(
        f'<div class="hero" role="banner"><h1>{html.escape(title)}</h1>'
        f'<p>{html.escape(subtitle)}</p></div>',
        unsafe_allow_html=True,
    )


def lang_card_html(lang: str, total: int, solved: int, wrong: int) -> str:
    meta = LANG_META[lang]
    pct = int(round(solved / total * 100)) if total else 0
    return (
        f'<div class="lang-card">'
        f'<div class="head"><div class="icon">{meta["icon"]}</div>'
        f'<div class="title">{html.escape(meta["name"])}</div></div>'
        f'<div class="subtitle">{html.escape(meta["tagline"])}</div>'
        f'<div class="stat-row">'
        f'<span>已通过 <b>{solved}</b></span>'
        f'<span>错题 <b>{wrong}</b></span>'
        f'<span>已尝试 <b>{total}</b></span>'
        f'<span>完成率 <b>{pct}%</b></span>'
        f'</div></div>'
    )


def metric_tile(num, lbl: str) -> str:
    return (
        f'<div class="metric-tile"><div class="num">{html.escape(str(num))}</div>'
        f'<div class="lbl">{html.escape(lbl)}</div></div>'
    )


def section_title(text: str):
    st.markdown(f'<div class="section-title">{html.escape(text)}</div>', unsafe_allow_html=True)


def lesson_box(md: str):
    """讲解框：用 streamlit container（带 border）+ 内部 markdown，CSS 真正包住内容。"""
    with st.container(border=True):
        st.markdown(md)


def verdict_banner(passed: bool, elapsed_ms: int = 0):
    if passed:
        timing = f" 用时 {elapsed_ms} 毫秒。" if elapsed_ms > 0 else ""
        st.markdown(
            f'<div class="verdict pass"><span class="ico">✅</span>'
            f'<div><b>通过！</b>{timing}继续保持～</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="verdict fail"><span class="ico">❌</span>'
            f'<div><b>未通过</b> 别灰心，看下面的对比和点评，再试一次。</div></div>',
            unsafe_allow_html=True,
        )


def io_block(content: str, kind: str = "actual"):
    safe = html.escape(content) if content else "(空)"
    cls = "io-box expected" if kind == "expected" else "io-box"
    st.markdown(f'<div class="{cls}">{safe}</div>', unsafe_allow_html=True)


def ai_feedback_block(text: str):
    """AI 评语用 st.markdown 渲染——保留 **加粗**、`代码`、列表等 Markdown 格式。"""
    if not text:
        return
    st.markdown(
        '<div class="ai-feedback"><span class="label">AI 老师点评</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(text)


def stderr_block(text: str):
    safe = html.escape(text)
    st.markdown(f'<div class="io-box" style="background:#7F1D1D;">{safe}</div>', unsafe_allow_html=True)


def render_error_notice(title: str, reason: str = "", next_action: str = ""):
    """统一错误提示（plan.md 固化目标第 3 条）：标题＋原因＋下一步动作三要素。

    所有页面级 st.error 收口到此；触发条件与事实内容由调用方保留，
    本函数只负责三要素的排版结构。
    """
    parts = [f"**{title}**"]
    if reason:
        parts.append(f"原因：{reason}")
    if next_action:
        parts.append(f"下一步：{next_action}")
    st.error("\n\n".join(parts))


def render_empty_state(message: str, next_action: str = "", compact: bool = False):
    """统一空态（plan.md 固化目标）：一句话说明＋下一步动作。

    compact=False 用 st.info 档（页面级空态），True 用 st.caption 档（卡片内微空态）；
    色号与间距沿用设计系统对 st.info/st.caption 的既有主题，不引入新常量。
    """
    text = f"{message} 下一步：{next_action}" if next_action else message
    if compact:
        st.caption(text)
    else:
        st.info(text)


def nav_is_active(current_route: str, routes: "str | set[str] | list[str]", extra_condition: bool = True) -> bool:
    """导航当前项高亮判定单源（d913c-09）：routes 支持单路由或别名集合，
    extra_condition 承载语言项等附加条件（route 命中 + 语言匹配）。"""
    if isinstance(routes, str):
        routes = {routes}
    return bool(extra_condition) and current_route in set(routes)


def nav_button(label: str, *, key: str | None = None, active: bool, on_activate) -> None:
    """侧栏导航项渲染：active 决定 primary/secondary，点击触发 on_activate。
    高亮判定一律先经 nav_is_active，勿在本函数外再写 type 三元式。"""
    if st.button(label, key=key, use_container_width=True,
                 type="primary" if active else "secondary"):
        on_activate()


def render_notice(message: str):
    """统一通知条（d914-21，循 c-07 render_error_notice 范式）：st.warning 单形态收口。

    通知类（提醒/等待/复核类提示）用本函数；强调性决策提示（需用户当场取舍、
    带动态枚举清单）仍留页面内联，见各调用点注释。文案语义由调用方保留。
    """
    st.warning(message)
