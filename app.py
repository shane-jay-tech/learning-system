import streamlit as st

from ui.styles import inject as inject_css
from ui.components import LANG_META, navigate_to_problem

from core.version import VERSION as APP_VERSION

# 注意：4 个页面用 lazy import（在 main() 里按路由命中时再 import）。
# 实测 home 之外 3 个页面的 import 链一共 ~2.6 秒（streamlit_ace 等组件初始化）。
# 用户首屏永远是 home，把这 2.6 秒挪到「真正点进去」时再付费，启动看起来快得多。


def _init_state():
    st.session_state.setdefault("route", "home")
    st.session_state.setdefault("selected_lang", None)
    st.session_state.setdefault("selected_topic_idx", 0)
    st.session_state.setdefault("selected_problem_idx", 0)


def _sidebar():
    with st.sidebar:
        st.markdown("### 📚 学习平台")
        lang_names = " · ".join(m["name"] for m in LANG_META.values())
        st.caption(f"v{APP_VERSION} · {lang_names}")
        st.markdown("---")
        if st.button("🏠 主页", use_container_width=True):
            st.session_state.route = "home"
            st.rerun()
        if st.button("🛤️ 学习路径", use_container_width=True):
            st.session_state.route = "paths"
            st.rerun()
        if st.button("🧪 学习诊断", use_container_width=True):
            st.session_state.route = "diagnostic"
            st.rerun()
        st.markdown("**按语言刷题**")
        for lang, meta in LANG_META.items():
            if st.button(f"{meta['icon']}  {meta['name']}", key=f"side_{lang}", use_container_width=True):
                navigate_to_problem(lang)
        st.markdown("---")
        if st.button("📊 学习面板", use_container_width=True):
            st.session_state.route = "dashboard"
            st.rerun()
        if st.button("📒 错题本", use_container_width=True):
            st.session_state.route = "mistakes"
            st.rerun()
        st.markdown("---")
        st.caption("提示：左侧菜单可随时切换语言或回主页。")


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
