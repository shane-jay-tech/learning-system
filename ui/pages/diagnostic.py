"""Diagnostic test UI — 首次诊断 + 路径推荐。"""

import time

import streamlit as st

from core.diagnostic import (
    DIAGNOSTIC_QUESTIONS,
    evaluate_diagnostic,
    get_diagnostic_result,
    save_diagnostic_result,
)
from core.progress import ProgressDAO
from ui.components import hero, render_info_notice, render_notice, render_success_notice

# l923-14（授权出处：docs/insights 之外的信箱档 zcode-bridge/done/l922-112-diag-retake-state.result.md
# 的「改动留授权」出口，由主班派单 l923-14 放行）：
# retake_diagnostic 从「布尔标志」升级为**带时间戳的一次性意图**——点「重新测试」记时间戳，
# 结果页一到手即消费清除，超时（10 分钟）自动失效。修的是「点了重测又中途切走 ⇒ 旧答案已被清、
# 标志无人复位 ⇒ 下次进页直落问卷，看起来像从没测过」这条在册中断残留。
RETAKE_INTENT_TTL_SECONDS = 600.0


def _now() -> float:
    """时间戳源；单独抽一层是为了让超时夹具可 monkeypatch，而不动全局 time 模块。"""
    return time.time()


def _retake_intent_state() -> str:
    """重测意图的现状：none / active / expired / invalid。

    取值口径（四处站点见 tests/test_diagnostic_retake_state.py 的源码形状桩）：
      None / False → none（未点过、或提交后复位过）
      True         → active（**旧布尔协议兼容**：无时间戳可依，放行一次；生产码已不再写 True，
                     只有历史会话与既有测试夹具会造出这形态，结果页一到手即被 pop）
      数值时间戳    → 距 _now() 在 TTL 内为 active，超时为 expired
      其它/不可解析 → invalid（脏值，按无意图处理）
    本函数**只读不写**：清除统一由路由层 `_consume_retake_intent` 做，保证「一处理一次」。
    """
    raw = st.session_state.get("retake_diagnostic")
    if raw is None or raw is False:
        return "none"
    if raw is True:
        return "active"
    try:
        age = _now() - float(raw)
    except (TypeError, ValueError):
        return "invalid"
    return "expired" if age > RETAKE_INTENT_TTL_SECONDS else "active"


def _consume_retake_intent() -> None:
    """结果页已渲染＝意图用完：连 expired/invalid/False 一起清干净，不留陈旧形态。"""
    st.session_state.pop("retake_diagnostic", None)


def render_diagnostic():
    hero("学习诊断", "2 分钟快速测试，帮你找到最适合的学习起点")

    dao = ProgressDAO()
    try:
        existing = get_diagnostic_result(dao)

        if existing and _retake_intent_state() != "active":
            _consume_retake_intent()
            _render_result(existing, dao)
        else:
            _render_quiz(dao)
    finally:
        dao.close()


def _render_quiz(dao):
    render_info_notice("按第一感觉选择即可；结果只用于推荐起点，不会限制后续课程。")

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
                render_notice(f"还有 {len(unanswered)} 题未作答：第 {', '.join(map(str, unanswered))} 题。")
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

    render_success_notice(f"诊断完成！答对 {score}/{total} 题")

    st.markdown("### 推荐学习路径")
    render_info_notice(rec["message"])

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
        # l923-14：写**时间戳**而不是 True —— 一次性意图，超时自动失效，
        # 中途切走不再把用户永久留在问卷页（旧答案已被清，见模块头注）。
        st.session_state["retake_diagnostic"] = _now()
        st.rerun()
