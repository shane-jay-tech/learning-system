"""Learning path UI — shows milestones, progress, and navigation."""

import streamlit as st

from core.loader import load_language
from core.paths import LearningPath, Milestone, get_milestone_topics_flat, load_all_paths, load_path
from core.progress import ProgressDAO
from ui.components import hero, navigate_to_problem


@st.cache_data(ttl=300)
def _cached_load_language(lang: str):
    return load_language(lang)


def render_path_list():
    """Render the path selection page."""
    hero("学习路径", "按阶段推进，每次只关注一个清晰的里程碑")

    paths = load_all_paths()
    if not paths:
        st.warning("暂无学习路径定义。")
        return

    dao = ProgressDAO()
    try:
        _render_diagnostic_prompt(dao)
        for p in paths:
            _render_path_card(p, dao)
    finally:
        dao.close()

    st.markdown("---")
    st.caption("也可以从侧栏「按语言刷题」自由练习，不受路径约束。")


def _render_diagnostic_prompt(dao: ProgressDAO):
    """首次用户显示诊断入口；老用户显示诊断结果摘要。"""
    from core.diagnostic import get_diagnostic_result
    result = get_diagnostic_result(dao)
    if result:
        rec = result["recommendation"]
        st.success(f"📋 诊断推荐：{rec['message']}")
    else:
        with st.container(border=True):
            st.markdown("**不确定从哪开始？** 做个 2 分钟诊断，帮你找到最适合的路径。")
            if st.button("开始诊断", type="primary"):
                st.session_state.route = "diagnostic"
                st.rerun()


def _render_path_card(path: LearningPath, dao: ProgressDAO):
    """Render a single path as an expandable card."""
    total_problems, solved_problems = _path_overall_progress(path, dao)
    pct = solved_problems / total_problems if total_problems else 0

    status_emoji = "✅" if pct >= 1.0 else ("🔄" if pct > 0 else "⬜")

    with st.container(border=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### {path.icon} {path.title}")
            st.caption(f"{path.subtitle} · 预计 {path.estimated_hours}h · {len(path.milestones)} 个里程碑")
        with col2:
            st.markdown(f"**{status_emoji} {solved_problems}/{total_problems}**")

        if total_problems:
            st.progress(pct, text=f"总进度 {solved_problems}/{total_problems} 题")

        if st.button(f"进入 {path.title}", key=f"enter_path_{path.id}", use_container_width=True):
            st.session_state.route = "path_detail"
            st.session_state.selected_path_id = path.id
            st.rerun()

def render_path_detail():
    """Render a single path's milestone list with progress."""
    path_id = st.session_state.get("selected_path_id")
    if not path_id:
        st.session_state.route = "paths"
        st.rerun()
        return

    path = load_path(path_id)
    if not path:
        st.error(f"路径 {path_id} 不存在。")
        return

    if st.button("← 返回路径列表", use_container_width=False):
        st.session_state.route = "paths"
        st.rerun()

    hero(f"{path.icon} {path.title}", path.subtitle)

    dao = ProgressDAO()
    try:
        _emit_path_started(dao, path_id)
        for i, milestone in enumerate(path.milestones):
            _render_milestone(path, milestone, i, dao)
    finally:
        dao.close()


def _render_milestone(path: LearningPath, milestone: Milestone, idx: int, dao: ProgressDAO):
    """Render a single milestone with its progress and topics."""
    topic_problems = _get_milestone_problems(milestone)
    progress = dao.milestone_progress(topic_problems)

    is_complete = progress["pct"] >= 1.0
    is_started = progress["pct"] > 0
    status_icon = "✅" if is_complete else ("🔄" if is_started else f"**{idx + 1}**")

    if is_complete:
        _emit_milestone_completed(dao, path.id, milestone.id)

    prereqs_met = _check_prereqs(path, milestone, dao)

    # 诊断推荐跳转时定位到指定里程碑（默认展开它）
    focus_id = st.session_state.get("selected_milestone_id", "")
    if focus_id == milestone.id:
        st.session_state.pop("selected_milestone_id", None)  # 一次性定位，下次进入恢复正常
    with st.expander(
        f"{status_icon} {milestone.title} — {progress['solved']}/{progress['total']} 题 · ~{milestone.estimated_hours}h",
        expanded=(focus_id == milestone.id) or (not is_complete and prereqs_met),
    ):
        st.markdown(milestone.description)

        if not prereqs_met:
            prereq_names = [m.title for m in path.milestones if m.id in milestone.prereqs]
            st.info(f"建议先完成：{', '.join(prereq_names)}（可跳过）")

        if progress["total"]:
            st.progress(progress["pct"])

        # Show topics as links to the language page
        st.markdown("**包含的知识点：**")
        topics_by_lang = {}
        for lang, topic_slug in get_milestone_topics_flat(milestone):
            topics_by_lang.setdefault(lang, []).append(topic_slug)

        for lang, slugs in topics_by_lang.items():
            for slug in slugs:
                if st.button(f"→ {lang}/{slug}", key=f"goto_{path.id}_{milestone.id}_{lang}_{slug}"):
                    _navigate_to_topic(lang, slug)

        if milestone.graduation_project:
            st.markdown(f"**毕业项目：** {milestone.graduation_project}")


def _navigate_to_topic(lang: str, topic_slug: str):
    """Navigate to a specific topic in the language page."""
    navigate_to_problem(lang, topic_slug=topic_slug)


def _get_milestone_problems(milestone: Milestone):
    """Get all problems in a milestone as [{lang, problem_id}, ...]"""
    problems = []
    for lang, topic_slug in get_milestone_topics_flat(milestone):
        try:
            topics = _cached_load_language(lang)
        except (FileNotFoundError, OSError):
            continue
        for t in topics:
            if t.slug == topic_slug:
                for p in t.problems:
                    problems.append({"lang": lang, "problem_id": p.id})
                break
    return problems


def _check_prereqs(path: LearningPath, milestone: Milestone, dao: ProgressDAO) -> bool:
    """Check if all prerequisite milestones are complete."""
    if not milestone.prereqs:
        return True
    for prereq_id in milestone.prereqs:
        prereq_m = next((m for m in path.milestones if m.id == prereq_id), None)
        if prereq_m:
            problems = _get_milestone_problems(prereq_m)
            progress = dao.milestone_progress(problems)
            if progress["pct"] < 1.0:
                return False
    return True


def _path_overall_progress(path: LearningPath, dao: ProgressDAO):
    """Get total and solved problem counts for an entire path."""
    total = 0
    solved = 0
    for m in path.milestones:
        problems = _get_milestone_problems(m)
        progress = dao.milestone_progress(problems)
        total += progress["total"]
        solved += progress["solved"]
    return total, solved


def _emit_path_started(dao: ProgressDAO, path_id: str):
    """Emit path_started once per path (dedup via meta table)."""
    key = f"path_started:{path_id}"
    if dao.get_meta(key):
        return
    dao.emit_event("path_started", path_id=path_id)
    dao.set_meta(key, "1")


def _emit_milestone_completed(dao: ProgressDAO, path_id: str, milestone_id: str):
    """Emit path_milestone_completed once per milestone (dedup via meta table)."""
    key = f"milestone_done:{path_id}:{milestone_id}"
    if dao.get_meta(key):
        return
    dao.emit_event("path_milestone_completed", path_id=path_id, milestone_id=milestone_id)
    dao.set_meta(key, "1")
