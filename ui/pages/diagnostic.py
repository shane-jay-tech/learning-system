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
    st.markdown("回答以下问题（不确定就选最接近的，不影响后续学习）：")
    st.markdown("---")

    answers = {}
    for i, q in enumerate(DIAGNOSTIC_QUESTIONS):
        st.markdown(f"**第 {i+1} 题**")
        st.markdown(q["question"])
        key = f"diag_{q['id']}"
        choice = st.radio(
            "选择答案",
            options=list(range(len(q["options"]))),
            format_func=lambda x, opts=q["options"]: opts[x],
            key=key,
            label_visibility="collapsed",
        )
        answers[q["id"]] = choice
        st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("提交诊断", type="primary", use_container_width=True):
            result = evaluate_diagnostic(answers)
            save_diagnostic_result(dao, result)
            st.session_state["retake_diagnostic"] = False
            st.rerun()
    with col2:
        if st.button("跳过诊断", use_container_width=True):
            st.session_state["page"] = "paths"
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
            st.session_state["page"] = "path_detail"
            st.session_state["selected_path_id"] = rec["path"]
            st.rerun()
    with col2:
        if st.button("我自己选路径", use_container_width=True):
            st.session_state["page"] = "paths"
            st.rerun()

    st.markdown("---")
    if st.button("重新测试"):
        st.session_state["retake_diagnostic"] = True
        st.rerun()
