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
