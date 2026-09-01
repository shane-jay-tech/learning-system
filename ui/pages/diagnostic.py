"""Diagnostic test UI — 首次诊断 + 路径推荐。"""

import streamlit as st

from core.diagnostic import (
    DIAGNOSTIC_QUESTIONS,
    evaluate_diagnostic,
    get_diagnostic_result,
    save_diagnostic_result,
)
from core.progress import ProgressDAO
from ui.components import hero


def render_diagnostic():
    hero("学习诊断", "2 分钟快速测试，帮你找到最适合的学习起点")

    dao = ProgressDAO()
    try:
        existing = get_diagnostic_result(dao)

        if existing and not st.session_state.get("retake_diagnostic"):
            _render_result(existing, dao)
        else:
            _render_quiz(dao)
    finally:
        dao.close()


def _render_quiz(dao):
    st.info("按第一感觉选择即可；结果只用于推荐起点，不会限制后续课程。")

    answers = {}
    for i, q in enumerate(DIAGNOSTIC_QUESTIONS):
        with st.container(border=True):
            st.caption(f"第 {i+1} / {len(DIAGNOSTIC_QUESTIONS)} 题")
            st.markdown(f"**{q['question']}**")
            key = f"diag_{q['id']}"
            choice = st.radio(
                "选择答案",
                options=list(range(len(q["options"]))),
                format_func=lambda x, opts=q["options"]: opts[x],
                key=key,
                label_visibility="collapsed",
                index=None,  # 不预选第一项，避免用户没看题就误提交
            )
        answers[q["id"]] = choice

    unanswered = [i + 1 for i, q in enumerate(DIAGNOSTIC_QUESTIONS)
                  if answers.get(q["id"]) is None]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("提交诊断", type="primary", use_container_width=True):
            if unanswered:
                st.warning(f"还有 {len(unanswered)} 题未作答：第 {', '.join(map(str, unanswered))} 题。")
            else:
                result = evaluate_diagnostic(answers)
                save_diagnostic_result(dao, result)
                st.session_state["retake_diagnostic"] = False
                st.rerun()
    with col2:
        if st.button("跳过诊断", use_container_width=True):
            st.session_state.route = "paths"
            st.rerun()


def _render_result(result, dao):
    score = result["total_correct"]
    total = result["total_questions"]
    rec = result["recommendation"]

    st.success(f"诊断完成！答对 {score}/{total} 题")

    st.markdown("### 推荐学习路径")
    st.info(rec["message"])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("按推荐开始学习", type="primary", use_container_width=True):
            st.session_state.route = "path_detail"
            st.session_state.selected_path_id = rec["path"]
            # 定位到推荐的里程碑，路径页会自动展开它
            st.session_state.selected_milestone_id = rec.get("milestone", "")
            st.rerun()
    with col2:
        if st.button("我自己选路径", use_container_width=True):
            st.session_state.route = "paths"
            st.rerun()

    st.markdown("---")
    if st.button("重新测试"):
        # 清空旧答案，避免重测时旧选项仍是选中态
        for q in DIAGNOSTIC_QUESTIONS:
            st.session_state.pop(f"diag_{q['id']}", None)
        st.session_state["retake_diagnostic"] = True
        st.rerun()
