from datetime import datetime, timezone

import streamlit as st

from core.loader import load_language
from core.paths import load_all_paths
from core.progress import ProgressDAO
from core.recommend import recommend
from ui.components import ALL_LANGS, LANG_META, hero, lang_card_html, metric_tile, navigate_to_problem, section_title


@st.cache_data(ttl=300)  # 题库 5 分钟缓存——首次扫 5 个 lang 后续秒响应
def _load_totals():
    return {lang: sum(len(t.problems) for t in load_language(lang)) for lang in ALL_LANGS}


def render_home():
    hero("编程学习工作台", "继续上次进度，或选择一条清晰路径开始今天的学习")

    dao = ProgressDAO()
    try:
        _render_home_body(dao)
    finally:
        dao.close()


def _render_security_notice(dao):
    """首次启动或公开模式时显示安全提示。"""
    from core.config import is_public_deploy

    if is_public_deploy():
        st.error(
            "**当前为公开部署模式** — 代码执行已禁用。\n\n"
            "如需在本机单人使用，请移除环境变量 `RUNNER_SECURITY_MODE=public` 后重启。"
        )
        return

    seen = dao.get_meta_ts("security_notice_seen")
    if not seen:
        with st.container(border=True):
            st.info(
                "**安全提示（仅显示一次）**\n\n"
                "本系统的代码执行器使用 subprocess 隔离，适合本机单人学习。\n"
                "- 不要暴露到公网或校园网共享服务器\n"
                "- 不要在多人共用环境运行\n\n"
                "如需了解详情，请参阅 README.md 的「安全边界」章节。"
            )
            if st.button("我知道了，不再提示", key="dismiss_security"):
                dao.set_meta("security_notice_seen", "done")
                st.rerun()


def _render_home_body(dao):
    _render_security_notice(dao)
    summary = dao.summary_by_lang()
    totals = _load_totals()

    grand_problems = sum(totals.values())
    grand_solved = sum(summary.get(l, {}).get("solved", 0) for l in ALL_LANGS)
    grand_wrong = sum(summary.get(l, {}).get("wrong", 0) for l in ALL_LANGS)
    grand_attempted = sum(summary.get(l, {}).get("total", 0) for l in ALL_LANGS)

    _render_next_action(dao, grand_solved)
    _render_path_cards()

    section_title("总览")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(metric_tile(grand_problems, "题库总题数"), unsafe_allow_html=True)
    with m2:
        st.markdown(metric_tile(grand_solved, "已通过"), unsafe_allow_html=True)
    with m3:
        st.markdown(metric_tile(grand_wrong, "错题待改"), unsafe_allow_html=True)
    with m4:
        st.markdown(metric_tile(grand_attempted, "已尝试"), unsafe_allow_html=True)

    section_title("按语言练习")
    for i in range(0, len(ALL_LANGS), 2):
        chunk = ALL_LANGS[i:i + 2]
        cols = st.columns(2)
        for j, lang in enumerate(chunk):
            with cols[j]:
                stats = summary.get(lang, {})
                solved = stats.get("solved", 0)
                wrong = stats.get("wrong", 0)
                total = totals.get(lang, 0)
                attempted = stats.get("total", 0)
                st.markdown(lang_card_html(lang, attempted, solved, wrong), unsafe_allow_html=True)
                if total:
                    pct = solved / total
                    st.progress(pct, text=f"进度 {solved}/{total}")
                else:
                    st.caption("(暂无题目)")
                if st.button(f"进入 {LANG_META[lang]['name']}", key=f"enter_{lang}", use_container_width=True):
                    # 统一走 navigate_to_problem：同时重置 topic/problem 索引
                    # 并清掉专题选择状态（否则旧值会把索引反压回旧专题）
                    navigate_to_problem(lang)

    section_title("错题与复习")
    mistakes = dao.list_mistakes()
    if mistakes:
        st.warning(f"你还有 {len(mistakes)} 道错题等着复习。")
    else:
        st.info("暂无错题。")
    if st.button("打开错题本 →", use_container_width=False):
        st.session_state.route = "mistakes"
        st.rerun()

    _render_ai_pulse(dao)


def _detect_pulse_event(dao, days_since_monthly: int) -> str:
    """检测事件型触发条件，返回提示文案（无事件返回空串）。"""
    from core.paths import load_all_paths

    # 事件 1：里程碑刚完成（今天有里程碑进度从 <100% 变为 100%）
    paths = load_all_paths()
    for p in paths:
        for m in p.milestones:
            from ui.pages.path import _get_milestone_problems
            problems = _get_milestone_problems(m)
            progress = dao.milestone_progress(problems)
            if progress["pct"] >= 1.0 and progress["total"] > 0:
                last_ts = dao.get_meta_ts(f"milestone_done_{p.id}_{m.id}")
                if not last_ts:
                    dao.set_meta(f"milestone_done_{p.id}_{m.id}", "done")
                    return f"🎉 恭喜完成里程碑「{m.title}」！趁这个节点看看 AI 领域有没有新工具值得学。"

    # 事件 2：连续学习恢复（streak 从 0 变为 ≥ 1，且上次月度扫描已超 14 天）
    streak = dao.daily_streak()
    if streak == 1 and days_since_monthly >= 14:
        return "👋 欢迎回来！休息期间 AI 领域可能有更新，建议顺手看一眼月度浅扫。"

    # 事件 3：错题全清
    mistakes = dao.list_mistakes()
    if not mistakes:
        cleared_ts = dao.get_meta_ts("all_mistakes_cleared")
        if not cleared_ts:
            summary = dao.summary_by_lang()
            total_attempted = sum(s.get("total", 0) for s in summary.values())
            if total_attempted >= 10:
                dao.set_meta("all_mistakes_cleared", "done")
                return "✨ 错题全部清空！学有余力的话，可以看看 AI 最新进展，给自己加点新题。"

    return ""


def _render_ai_pulse(dao):
    """事件驱动 + 时间兜底的 AI 进展提醒。

    优先用里程碑完成、连续学习恢复、错题清空等事件触发；
    无事件命中时退回原有的 30 天 / 90 天时间周期。
    """
    def _days_since(ts_str):
        if not ts_str:
            return 9999
        try:
            ts = datetime.strptime(ts_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
            ts = ts.replace(tzinfo=timezone.utc)
            delta_days = (datetime.now(timezone.utc) - ts).days
            return max(0, delta_days)
        except Exception:
            return 9999

    days_monthly = _days_since(dao.get_meta_ts("ai_pulse_monthly"))
    days_quarterly = _days_since(dao.get_meta_ts("ai_pulse_quarterly"))

    section_title("AI 进展自查")

    # 事件触发：里程碑刚完成 / 连续学习恢复 / 错题全清
    event_msg = _detect_pulse_event(dao, days_monthly)
    if event_msg:
        st.info(event_msg)

    def _label(days: int) -> str:
        return "从未做过" if days >= 9999 else f"距上次 {days} 天"

    if days_quarterly >= 90:
        st.error(
            f"⏰ **该做季度深查了**（{_label(days_quarterly)}）"
            "——4 问自检 + 5 个信息源全过一遍，约 30 分钟"
        )
    elif days_monthly >= 30:
        st.warning(
            f"📅 **该做月度浅扫了**（{_label(days_monthly)}）"
            "——5 分钟看一眼，确认大版本没变"
        )
    else:
        next_monthly = max(0, 30 - days_monthly)
        next_quarterly = max(0, 90 - days_quarterly)
        st.success(
            f"✓ AI 进展已跟上。下次月度浅扫还有 {next_monthly} 天，季度深查还有 {next_quarterly} 天。"
        )

    tab_m, tab_q, tab_r = st.tabs(["📅 月度浅扫（5 分钟）", "🔍 季度深查（30 分钟）", "📰 信息源"])

    with tab_m:
        st.markdown("""
**5 分钟流程**：
1. 打开 [Anthropic News](https://anthropic.com/news) — 看是不是出了 Claude 新大版本
2. 打开 [OpenAI Blog](https://openai.com/blog) — 看是不是出了 GPT 新大版本
3. 浏览 [Simon Willison's Weblog](https://simonwillison.net) 过去 30 天 — 实战派博主过滤虚假繁荣很准

**判断标准**：
- 没大变化 → 点下面"已完成"按钮，下个月见
- 看到值得学的 → 告诉我，我加进 `agent_dev/06_frontier`
""")
        if st.button("✓ 我已完成本月浅扫", key="done_monthly", type="primary"):
            dao.set_meta("ai_pulse_monthly", "done")
            st.rerun()

    with tab_q:
        st.markdown("""
**30 分钟流程 — 4 问自检**：

1. 我用的 LLM 大版本变了吗？（Claude / GPT 这季度有大改没？）
2. 我常用的库（Anthropic SDK / langchain / 其他）API 变了吗？
3. 有没有冒出陌生新概念？（如 2024 年的 MCP、2025 年的某个）
4. 学习系统的 `agent_dev/06_frontier` 有没有过时？

**完成后**：把"应该加 / 应该删 / 应该改"的清单告诉我，我更新 `06_frontier`。
""")
        if st.button("✓ 我已完成本季度深查", key="done_quarterly", type="primary"):
            dao.set_meta("ai_pulse_quarterly", "done")
            dao.set_meta("ai_pulse_monthly", "done")
            st.rerun()

    with tab_r:
        st.markdown("""
| 来源 | 看什么 | 频率 |
|---|---|---|
| **[Anthropic News](https://anthropic.com/news)** | Claude / API 大版本、Tool Use 新能力 | 月看 |
| **[OpenAI Blog](https://openai.com/blog)** | GPT 大版本、新能力 | 月看 |
| **[Simon Willison's Weblog](https://simonwillison.net)** | 实战派博主，**过滤虚假繁荣最准** | 周看 |
| **[Hacker News](https://news.ycombinator.com)** | 业界正在讨论的工具（看 AI 标签） | 季看 |
| **[Hugging Face Daily Papers](https://huggingface.co/papers)** | 学术前沿 | 季看 |

⚠️ **避坑**：营销号、震惊体测评、夸张演示——80% 的「新东西」3 个月就死。
**判断真东西**：3 个月后 Simon Willison 还在写它 / Hacker News 还有讨论 / Anthropic 或 OpenAI 抄了 = 真值得学。
""")


def _render_next_action(dao, grand_solved: int):
    """Three-zone action center: 继续学习 / 今日复习 / 能力进展."""
    if grand_solved == 0:
        with st.container(border=True):
            st.markdown(
                "### 开始学习\n"
                "第一次来？推荐先做 **学习诊断**（6 道快速题，约 2 分钟），帮你找到最适合的起点。"
            )
            c1, c2, _ = st.columns([1, 1, 2])
            with c1:
                if st.button("做学习诊断", key="home_diag", type="primary", use_container_width=True):
                    st.session_state.route = "diagnostic"
                    st.rerun()
            with c2:
                if st.button("直接开始 Python", key="home_py", use_container_width=True):
                    navigate_to_problem("python")
        return

    col_a, col_b, col_c = st.columns(3)

    # Zone 1: Continue learning
    plan = recommend(n=1, dao=dao)
    with col_a:
        with st.container(border=True):
            if plan:
                it = plan[0]
                meta = LANG_META.get(it["lang"], {"icon": "·", "name": it["lang"]})
                reason = it.get("reason", "推荐")
                st.markdown(
                    f"### 继续学习\n"
                    f"**{meta['icon']} {it['title']}**\n\n"
                    f"难度 {it['difficulty']} · {reason}"
                )
                if st.button("立即开始 →", key="home_next_action", type="primary", use_container_width=True):
                    navigate_to_problem(it["lang"], it["topic_slug"], it["problem_id"])
            else:
                st.markdown("### 继续学习\n当前课程已全部完成。")

    # Zone 2: Today's review
    due_reviews = dao.get_due_reviews(limit=5)
    mistakes = dao.list_mistakes()
    with col_b:
        with st.container(border=True):
            review_count = len(due_reviews) + len(mistakes)
            st.markdown(f"### 今日复习\n**{review_count}** 题待复习")
            if mistakes:
                st.caption(f"错题 {len(mistakes)} · 到期 {len(due_reviews)}")
            if review_count > 0:
                if st.button("去复习 →", key="home_review", use_container_width=True):
                    st.session_state.route = "mistakes"
                    st.rerun()
            else:
                st.caption("今天没有待复习任务 ✓")

    # Zone 3: Progress snapshot
    from core.achievements import get_progress_summary
    ach_progress = get_progress_summary(dao)
    streak = dao.daily_streak()
    with col_c:
        with st.container(border=True):
            flame = "连续" if streak >= 3 else "已学习"
            st.markdown(
                f"### 学习进展\n"
                f"{flame} **{streak}** 天 · "
                f"{ach_progress['earned']}/{ach_progress['total']} 项成就"
            )
            if st.button("看面板 →", key="home_dashboard", use_container_width=True):
                st.session_state.route = "dashboard"
                st.rerun()


def _render_path_cards():
    """Show learning path cards at the top of home page."""
    paths = load_all_paths()
    if not paths:
        return

    section_title("学习路径")
    cols = st.columns(len(paths))
    for i, p in enumerate(paths):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"**{p.icon} {p.title}**")
                st.caption(f"{p.subtitle} · 约 {p.estimated_hours} 小时")
                if st.button("进入路径", key=f"home_path_{p.id}", use_container_width=True):
                    st.session_state.route = "path_detail"
                    st.session_state.selected_path_id = p.id
                    st.rerun()
