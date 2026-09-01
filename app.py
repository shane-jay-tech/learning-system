import streamlit as st

from ui.styles import inject as inject_css
from ui.components import LANG_META, navigate_to_problem

from core.version import VERSION as APP_VERSION

# 注意：4 个页面用 lazy import（在 main() 里按路由命中时再 import）。
# 实测 home 之外 3 个页面的 import 链一共 ~2.6 秒（streamlit_ace 等组件初始化）。
# 用户首屏永远是 home，把这 2.6 秒挪到「真正点进去」时再付费，启动看起来快得多。
# ui/components 里的 streamlit_ace 同样做了惰性加载（~0.5s 挪到首次渲染编辑器时）。


def _init_state():
    st.session_state.setdefault("route", "home")
    st.session_state.setdefault("selected_lang", None)
    st.session_state.setdefault("selected_topic_idx", 0)
    st.session_state.setdefault("selected_problem_idx", 0)


def _sidebar():
    with st.sidebar:
        route = st.session_state.get("route", "home")
        st.markdown(
            '<div class="sidebar-brand">'
            '<div class="sidebar-brand-mark">L</div>'
            '<div><div class="sidebar-brand-name">学习工作台</div>'
            f'<div class="sidebar-brand-meta">v{APP_VERSION} · 5 门课程</div></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown('<div class="sidebar-label">学习导航</div>', unsafe_allow_html=True)
        if st.button("🏠 主页", use_container_width=True,
                     type="primary" if route == "home" else "secondary"):
            st.session_state.route = "home"
            st.rerun()
        if st.button("🛤️ 学习路径", use_container_width=True,
                     type="primary" if route in {"paths", "path_detail"} else "secondary"):
            st.session_state.route = "paths"
            st.rerun()
        if st.button("🧪 学习诊断", use_container_width=True,
                     type="primary" if route == "diagnostic" else "secondary"):
            st.session_state.route = "diagnostic"
            st.rerun()
        st.markdown('<div class="sidebar-label">按语言练习</div>', unsafe_allow_html=True)
        selected_lang = st.session_state.get("selected_lang")
        for lang, meta in LANG_META.items():
            is_active = route == "language" and selected_lang == lang
            if st.button(
                f"{meta['icon']}  {meta['name']}", key=f"side_{lang}",
                use_container_width=True, type="primary" if is_active else "secondary",
            ):
                navigate_to_problem(lang)
        st.markdown("---")
        st.markdown('<div class="sidebar-label">复盘与巩固</div>', unsafe_allow_html=True)
        if st.button("📊 学习面板", use_container_width=True,
                     type="primary" if route == "dashboard" else "secondary"):
            st.session_state.route = "dashboard"
            st.rerun()
        if st.button("📒 错题本", use_container_width=True,
                     type="primary" if route == "mistakes" else "secondary"):
            st.session_state.route = "mistakes"
            st.rerun()
        st.markdown("---")
        st.markdown(
            '<div class="sidebar-foot">本地单人学习模式<br>进度会自动保存在当前设备</div>',
            unsafe_allow_html=True,
        )


def main():
    st.set_page_config(
        page_title="编程学习平台",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()
    _init_state()
    _sidebar()

    route = st.session_state.route
    if route == "home":
        from ui.pages.home import render_home
        render_home()
    elif route == "paths":
        from ui.pages.path import render_path_list
        render_path_list()
    elif route == "path_detail":
        from ui.pages.path import render_path_detail
        render_path_detail()
    elif route == "language":
        from ui.pages.language import render_language
        render_language()
    elif route == "mistakes":
        from ui.pages.mistakes import render_mistakes
        render_mistakes()
    elif route == "diagnostic":
        from ui.pages.diagnostic import render_diagnostic
        render_diagnostic()
    elif route == "dashboard":
        from ui.pages.dashboard import render_dashboard
        render_dashboard()
    else:
        st.error(f"未知路由：{route}")


if __name__ == "__main__":
    main()
