import html
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from core.achievements import check_achievements, get_all_earned, get_all_with_state, get_progress_summary, get_achievement
from core.loader import find_problem
from core.progress import ProgressDAO, format_local_ts
from core.recommend import cross_recommend, recommend
from core.report import generate_report, report_to_html, report_to_markdown
from ui.components import ALL_LANGS, LANG_META, hero, metric_tile, navigate_to_problem, section_title


def _make_rec_id(surface: str, reason_code: str, lang: str, pid: str, rank: int) -> str:
    today = date.today().isoformat().replace("-", "")
    return f"{today}_{surface}_{reason_code}_{lang}_{pid.split('/')[-1]}_{rank}"


def _streak_html(streak: int) -> str:
    flame = "🔥" if streak >= 3 else ("⭐" if streak >= 1 else "·")
    return (
        f'<div class="metric-tile streak"><div class="num">{flame} {streak}</div>'
        f'<div class="lbl">连续打卡（天）</div></div>'
    )


def _build_chart_data(daily, days: int = 14):
    """覆盖最近 N 天的 zero-fill 字典。"""
    today = date.today()
    series = {(today - timedelta(days=i)).isoformat(): 0 for i in range(days - 1, -1, -1)}
    pass_series = dict(series)
    for row in daily:
        if row["date"] in series:
            series[row["date"]] = row["attempts"]
            pass_series[row["date"]] = row["passed"]
    return series, pass_series


def render_dashboard():
    hero("学习面板", "用趋势与复习状态了解进展，决定下一步学什么")

    dao = ProgressDAO()
    try:
        _render_dashboard_body(dao)
    finally:
        dao.close()


def _render_dashboard_body(dao):
    streak = dao.daily_streak()
    summary = dao.summary_by_lang()
    total_attempts = dao.total_attempts()
    lang_counts = dao.lang_attempt_counts()
    daily = dao.attempts_by_day(days=14)
    recent = dao.recent_attempts(limit=15)

    grand_solved = sum(s.get("solved", 0) for s in summary.values())
    grand_wrong = sum(s.get("wrong", 0) for s in summary.values())

    section_title("总览")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(_streak_html(streak), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_tile(total_attempts, "累计提交次数"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_tile(grand_solved, "已通过题数"), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_tile(grand_wrong, "错题待复习"), unsafe_allow_html=True)

    section_title("最近 14 天提交趋势")
    if total_attempts == 0:
        st.info("还没有任何提交记录。先去做几道题，回来看看图～")
    else:
        attempts_map, passed_map = _build_chart_data(daily, days=14)
        df = pd.DataFrame({
            "提交": list(attempts_map.values()),
            "通过": list(passed_map.values()),
        }, index=list(attempts_map.keys()))
        st.bar_chart(df, height=240)

    section_title("各语言通过情况")
    n = len(ALL_LANGS)
    cols = st.columns(min(n, 5))
    for i, lang in enumerate(ALL_LANGS):
        meta = LANG_META[lang]
        s = summary.get(lang, {"solved": 0, "wrong": 0, "total": 0})
        attempts = lang_counts.get(lang, {}).get("attempts", 0)
        with cols[i % len(cols)]:
            with st.container(border=True):
                st.markdown(f"### {meta['icon']} {meta['name']}")
                st.metric("通过", s.get("solved", 0))
                st.caption(f"错题 {s.get('wrong', 0)} · 提交 {attempts} 次")

    _render_recommendation_funnel(dao)
    _render_review_health(dao)
    _render_rubric_trends(dao)

    section_title("今日推荐（优先错题，再做新题）")
    plan = recommend(n=5, dao=dao)  # 复用当前连接，不再内部另开 DAO
    if not plan:
        st.info("题库还没加载到推荐项；试着进入语言主页直接选题。")
    else:
        shown_key = "_rec_shown_ids"
        impressions_key = "_rec_impressions"
        if shown_key not in st.session_state:
            st.session_state[shown_key] = set()
        if impressions_key not in st.session_state:
            st.session_state[impressions_key] = {}
        try:
            for rank, it in enumerate(plan, 1):
                pid_key = (it["lang"], it["problem_id"])
                if pid_key not in st.session_state[shown_key]:
                    st.session_state[shown_key].add(pid_key)
                    rc = it.get("reason_code", "")
                    rec_id = _make_rec_id("dashboard", rc, it["lang"], it["problem_id"], rank)
                    st.session_state[impressions_key][(it["lang"], it["problem_id"], "dashboard")] = {
                        "recommendation_id": rec_id, "reason_code": rc, "rank": rank,
                    }
                    dao.emit_event("recommendation_shown", lang=it["lang"], problem_id=it["problem_id"],
                                   payload={"reason_code": rc, "surface": "dashboard",
                                            "rank": rank, "recommendation_id": rec_id})
        except Exception:
            pass
        for it in plan:
            meta = LANG_META[it["lang"]]
            with st.container(border=True):
                cols2 = st.columns([3, 1])
                with cols2[0]:
                    st.markdown(
                        f"**{meta['icon']} {meta['name']} · {html.escape(it['title'])}**"
                        f"  <span style='color:#64748B;'>难度 {it['difficulty']} · {html.escape(it['topic_title'])}</span>",
                        unsafe_allow_html=True,
                    )
                with cols2[1]:
                    if st.button("去做 →", key=f"reco_{it['problem_id']}", type="primary", use_container_width=True):
                        try:
                            imp = st.session_state.get(impressions_key, {}).get(
                                (it["lang"], it["problem_id"], "dashboard"), {})
                            dao.emit_event("recommendation_clicked", lang=it["lang"],
                                           problem_id=it["problem_id"],
                                           payload={
                                               "recommendation_id": imp.get("recommendation_id", ""),
                                               "reason_code": it.get("reason_code", ""),
                                               "surface": "dashboard",
                                               "rank": imp.get("rank", 0),
                                           })
                        except Exception:
                            pass
                        navigate_to_problem(it["lang"], it["topic_slug"], it["problem_id"])

    _render_cross_recommend(dao)
    _render_achievements(dao)
    _render_heatmap(dao)

    section_title("📄 学习报告导出")
    rpt_col1, rpt_col2, _ = st.columns([1, 1, 3])
    with rpt_col1:
        if st.button("生成周报", use_container_width=True, key="gen_weekly"):
            with st.spinner("正在生成报告…"):
                report = generate_report(dao, days=7)
                md = report_to_markdown(report)
                html_report = report_to_html(report)
            st.session_state["last_report_md"] = md
            st.session_state["last_report_html"] = html_report
            st.session_state["last_report_days"] = 7
    with rpt_col2:
        if st.button("生成月报", use_container_width=True, key="gen_monthly"):
            with st.spinner("正在生成报告…"):
                report = generate_report(dao, days=30)
                md = report_to_markdown(report)
                html_report = report_to_html(report)
            st.session_state["last_report_md"] = md
            st.session_state["last_report_html"] = html_report
            st.session_state["last_report_days"] = 30

    if st.session_state.get("last_report_md"):
        dl_col1, dl_col2, _ = st.columns([1, 1, 3])
        days = st.session_state.get("last_report_days", 7)
        with dl_col1:
            st.download_button(
                "⬇️ 下载报告 (.md)",
                data=st.session_state["last_report_md"],
                file_name=f"learning_report_{date.today().isoformat()}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with dl_col2:
            st.download_button(
                "🖨️ 打印版 (.html)",
                data=st.session_state.get("last_report_html", ""),
                file_name=f"learning_report_{date.today().isoformat()}.html",
                mime="text/html",
                use_container_width=True,
                help="下载后用浏览器打开，Ctrl+P 即可打印或另存为 PDF",
            )
        with st.expander("预览报告", expanded=False):
            st.markdown(st.session_state["last_report_md"])

    section_title("📦 学习数据")
    exp_col, imp_col = st.columns([1, 2])
    with exp_col:
        from core.data_portability import export_json
        # 导出全库 JSON 有成本：按「答题数+事件数」做渲染内缓存，
        # 数据没变化时复用上次序列化结果
        _exp_key = f"{dao.total_attempts()}_{dao.event_count()}"
        if st.session_state.get("_export_cache_key") != _exp_key:
            st.session_state["_export_cache_json"] = export_json(dao)
            st.session_state["_export_cache_key"] = _exp_key
        st.download_button(
            "⬇️ 导出全部学习数据 (.json)",
            data=st.session_state["_export_cache_json"],
            file_name=f"learning_data_{date.today().isoformat()}.json",
            mime="application/json",
            use_container_width=True,
            help="包含答题记录、错题、复习状态、成就与事件——可导入到另一台机器",
        )
    with imp_col:
        with st.expander("📥 导入学习数据（换机器迁移）", expanded=False):
            st.caption("导入会**合并**进当前数据：状态/复习按题覆盖，答题记录追加。建议先做一次备份。")
            uploaded = st.file_uploader("选择之前导出的 .json 文件", type=["json"],
                                        key="data_import_uploader")
            if uploaded is not None:
                if st.button("确认导入", type="primary", key="data_import_confirm"):
                    from core.data_portability import import_json
                    try:
                        raw = uploaded.getvalue().decode("utf-8")
                        stats = import_json(dao, raw)
                        st.success(
                            f"导入完成：答题 {stats['attempts']} 条 · 事件 {stats['learning_events']} 条 · "
                            f"状态 {stats['problems_status']} 题 · 复习 {stats['review_state']} 题 · "
                            f"元数据 {stats['meta']} 项"
                        )
                        dao._clear_memo()
                        st.rerun()
                    except Exception as exc:
                        st.error(f"导入失败：{exc}（当前数据未受影响）")

    section_title("最近活动")
    if not recent:
        st.caption("还没有提交记录。")
    else:
        # 一次性建 (lang, pid) -> title 字典，避免每行都跑 find_problem 全表扫描
        from core.loader import load_language
        title_map = {}
        for lang in {r["lang"] for r in recent}:
            for t in load_language(lang):
                for p in t.problems:
                    title_map[(lang, p.id)] = p.title
        for r in recent:
            meta = LANG_META.get(r["lang"], {"name": r["lang"], "icon": "·"})
            badge = "✅" if r["passed"] else "❌"
            title = title_map.get((r["lang"], r["problem_id"]), r["problem_id"])
            st.markdown(
                f'<div style="padding:8px 12px;border-bottom:1px solid #E2E8F0;display:flex;justify-content:space-between;">'
                f'<span>{badge} {meta["icon"]} {meta["name"]} · {html.escape(title)}</span>'
                f'<span style="color:#64748B;font-size:12px;">{format_local_ts(r["ts"])}</span></div>',
                unsafe_allow_html=True,
            )


def _render_cross_recommend(dao):
    """跨路径推荐区：完成某里程碑后，推荐其他路径的互补内容。"""
    cross = cross_recommend(n=3, dao=dao)  # 复用当前连接
    if not cross:
        return

    section_title("🔀 跨路径推荐（拓宽视野）")
    impressions_key = "_rec_impressions"
    if impressions_key not in st.session_state:
        st.session_state[impressions_key] = {}
    cross_shown_key = "_cross_rec_shown_ids"
    if cross_shown_key not in st.session_state:
        st.session_state[cross_shown_key] = set()
    for rank, it in enumerate(cross, 1):
        pid_key = (it["lang"], it["problem_id"])
        if pid_key not in st.session_state[cross_shown_key]:
            st.session_state[cross_shown_key].add(pid_key)
            rec_id = _make_rec_id("cross_path", "cross_path", it["lang"], it["problem_id"], rank)
            st.session_state[impressions_key][(it["lang"], it["problem_id"], "cross_path")] = {
                "recommendation_id": rec_id, "reason_code": "cross_path", "rank": rank,
            }
            dao.emit_event("recommendation_shown", lang=it["lang"], problem_id=it["problem_id"],
                           payload={"reason_code": "cross_path", "surface": "cross_path",
                                    "rank": rank, "recommendation_id": rec_id})

    for it in cross:
        meta = LANG_META[it["lang"]]
        cols2 = st.columns([3, 1])
        with cols2[0]:
            with st.container(border=True):
                st.markdown(
                    f"**{meta['icon']} {meta['name']} · {html.escape(it['title'])}**"
                    f"  <span style='color:#64748B;'>难度 {it['difficulty']} · {html.escape(it['topic_title'])}</span>"
                    f"<br><span style='color:#5B5BD6;font-size:13px;'>💡 {html.escape(it['cross_reason'])}</span>",
                    unsafe_allow_html=True,
                )
        with cols2[1]:
            if st.button("去做 →", key=f"cross_{it['problem_id']}", type="secondary", use_container_width=True):
                try:
                    imp = st.session_state.get(impressions_key, {}).get(
                        (it["lang"], it["problem_id"], "cross_path"), {})
                    dao.emit_event("recommendation_clicked", lang=it["lang"], problem_id=it["problem_id"],
                                   payload={
                                       "recommendation_id": imp.get("recommendation_id", ""),
                                       "reason_code": "cross_path",
                                       "surface": "cross_path",
                                       "rank": imp.get("rank", 0),
                                   })
                except Exception:
                    pass
                navigate_to_problem(it["lang"], it["topic_slug"], it["problem_id"])


def _render_achievements(dao):
    """成就徽章展示区：已获得 / 接近达成 / 未获得三态。"""
    newly = check_achievements(dao)
    progress = get_progress_summary(dao)
    all_states = get_all_with_state(dao)

    section_title(f"🏅 成就徽章（{progress['earned']}/{progress['total']}）")

    if newly:
        for aid in newly:
            a = get_achievement(aid)
            if a:
                st.success(f"🎉 解锁新成就：**{a.icon} {a.title}** — {a.description}")

    if progress["earned"] == 0:
        st.info("还没有解锁任何成就。开始做题就能获得第一枚徽章！")

    cols_per_row = 4
    for i in range(0, len(all_states), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, item in enumerate(all_states[i:i + cols_per_row]):
            a = item["achievement"]
            state = item["state"]
            pct = item["progress"]
            with cols[j]:
                if state == "earned":
                    bg = "#FAFAFA"
                    border = "#5B5BD6"
                    opacity = "1"
                    extra = ""
                elif state == "approaching":
                    bg = "#FFFBEB"
                    border = "#F59E0B"
                    opacity = "0.85"
                    extra = f'<div style="font-size:10px;color:#D97706;margin-top:2px;">{int(pct*100)}%</div>'
                else:
                    bg = "#F1F5F9"
                    border = "#E2E8F0"
                    opacity = "0.4"
                    extra = ""
                st.markdown(
                    f'<div style="text-align:center;padding:12px;border:2px solid {border};'
                    f'border-radius:12px;background:{bg};opacity:{opacity};">'
                    f'<div style="font-size:28px;">{a.icon}</div>'
                    f'<div style="font-size:13px;font-weight:600;margin-top:4px;">{html.escape(a.title)}</div>'
                    f'<div style="font-size:12px;color:#475569;">{html.escape(a.description)}</div>'
                    f'{extra}</div>',
                    unsafe_allow_html=True,
                )


def _render_heatmap(dao):
    """90天学习热力图。"""
    section_title("📅 学习热力图（最近 90 天）")

    rows = dao.conn.execute(
        "SELECT DATE(ts, 'localtime') AS d, COUNT(*) AS n, SUM(passed) AS p "
        "FROM attempts WHERE ts >= datetime('now', '-90 days') "
        "GROUP BY d ORDER BY d"
    ).fetchall()
    if not rows:
        st.info("还没有提交记录，热力图将在你开始做题后展示。")
        return

    activity = {r[0]: {"attempts": r[1], "passed": r[2] or 0} for r in rows}
    today = date.today()

    weeks_html = []
    for week_offset in range(12, -1, -1):
        week_cells = []
        for dow in range(7):
            d = today - timedelta(days=week_offset * 7 + (6 - dow))
            ds = d.isoformat()
            count = activity.get(ds, {}).get("attempts", 0)
            if count == 0:
                color = "#EBEDF0"
            elif count <= 2:
                color = "#C6E48B"
            elif count <= 5:
                color = "#7BC96F"
            elif count <= 10:
                color = "#239A3B"
            else:
                color = "#196127"
            week_cells.append(
                f'<div title="{ds}: {count}次提交" style="width:12px;height:12px;'
                f'background:{color};border-radius:2px;margin:1px;"></div>'
            )
        weeks_html.append(
            '<div style="display:flex;flex-direction:column;">' + "".join(week_cells) + '</div>'
        )

    legend = (
        '<div style="display:flex;align-items:center;gap:4px;margin-top:8px;font-size:12px;color:#475569;">'
        '<span>少</span>'
        '<div style="width:12px;height:12px;background:#EBEDF0;border-radius:2px;"></div>'
        '<div style="width:12px;height:12px;background:#C6E48B;border-radius:2px;"></div>'
        '<div style="width:12px;height:12px;background:#7BC96F;border-radius:2px;"></div>'
        '<div style="width:12px;height:12px;background:#239A3B;border-radius:2px;"></div>'
        '<div style="width:12px;height:12px;background:#196127;border-radius:2px;"></div>'
        '<span>多</span></div>'
    )

    st.markdown(
        '<div style="display:flex;gap:2px;overflow-x:auto;">'
        + "".join(weeks_html)
        + '</div>' + legend,
        unsafe_allow_html=True,
    )


def _render_recommendation_funnel(dao):
    """推荐效果漏斗：shown → clicked → completed，含 reason_code 分组。"""
    section_title("📈 推荐效果")

    window_options = {"7 天": 7, "30 天": 30, "全部": None}
    sel = st.radio("时间窗口", list(window_options.keys()), horizontal=True, key="_rec_window", label_visibility="collapsed")
    days = window_options[sel]

    funnel = dao.recommendation_funnel(days=days)
    shown, clicked, completed = funnel["shown"], funnel["clicked"], funnel["completed"]

    if shown == 0:
        st.caption("还没有推荐数据，做几天题后这里会展示推荐效果漏斗。")
        return

    ctr = (clicked / shown * 100) if shown else 0
    completion = (completed / shown * 100) if shown else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("曝光", shown)
    with c2:
        st.metric("点击", clicked, f"{ctr:.0f}%")
    with c3:
        st.metric("完成", completed, f"{completion:.0f}%")
    with c4:
        click_to_complete = (completed / clicked * 100) if clicked else 0
        st.metric("点击→完成", f"{click_to_complete:.0f}%")

    rc_data = dao.recommendation_funnel_by_reason(days=days)
    if rc_data:
        with st.expander("按推荐策略分组"):
            header = "| 策略 | 曝光 | 点击 | 完成 | CTR |\n|---|---|---|---|---|\n"
            rows_md = []
            for rc, d in sorted(rc_data.items(), key=lambda x: -x[1]["shown"]):
                s, cl, co = d["shown"], d["clicked"], d["completed"]
                r_ctr = f"{cl/s*100:.0f}%" if s else "—"
                rows_md.append(f"| {rc} | {s} | {cl} | {co} | {r_ctr} |")
            st.markdown(header + "\n".join(rows_md))


def _render_review_health(dao):
    """复习健康度 v2：逾期分桶、高风险题、平均间隔。"""
    section_title("💊 复习健康度")
    stats = dao.review_health_stats()
    if stats["total_pool"] == 0:
        st.caption("还没有进入复习循环的题目。做对题后会自动加入间隔复习。")
        return

    avg_interval = dao.conn.execute(
        "SELECT AVG(interval_days) FROM review_state"
    ).fetchone()[0] or 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("复习池", stats["total_pool"])
    with c2:
        color = "🟢" if stats["total_due"] == 0 else ("🟡" if stats["total_due"] < 5 else "🔴")
        st.metric(f"{color} 到期待复习", stats["total_due"])
    with c3:
        st.metric("高风险题", len(stats["high_risk"]))
    with c4:
        st.metric("平均间隔", f"{avg_interval:.0f} 天")

    if stats["total_due"] > 0:
        b = stats["buckets"]
        st.markdown(
            f"逾期分桶：**1-3天** {b['1_3']} · **4-7天** {b['4_7']} · **>7天** {b['7_plus']}"
        )
        st.caption(f"有 {stats['total_due']} 道题已到期待复习，去「错题本 → 到期复习」页面集中练习。")

    if stats["high_risk"]:
        with st.expander(f"⚠️ 高风险题（上次失败且逾期，共 {len(stats['high_risk'])} 题）"):
            for hr in stats["high_risk"]:
                st.markdown(f"- `{hr['problem_id']}` — 逾期 {hr['overdue_days']} 天")


def _render_rubric_trends(dao):
    """能力维度趋势：最近 30 天各维度平均分（按规范维度聚合，跨题可比）。"""
    section_title("🎯 能力维度趋势（近 30 天）")
    rows = dao.dimension_trends(days=30)
    if not rows:
        st.caption("还没有开放题维度评分数据。做几道开放题后这里会展示能力趋势。")
        return

    for item in rows:
        label, avg, cnt = item["label"], item["avg"], item["count"]
        pct = min(avg / 100.0, 1.0)
        bar_color = "#EF4444" if avg < 50 else ("#F59E0B" if avg < 70 else "#10B981")
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
            f'<span style="min-width:80px;font-size:13px;">{html.escape(label)}</span>'
            f'<div style="flex:1;background:#E2E8F0;border-radius:4px;height:14px;">'
            f'<div style="width:{pct*100:.0f}%;background:{bar_color};border-radius:4px;height:14px;"></div></div>'
            f'<span style="min-width:60px;font-size:13px;color:#475569;">{avg:.0f} 分 ({cnt}题)</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    weakest = rows[0]
    st.caption(f"最薄弱维度：**{weakest['label']}**（{weakest['avg']:.0f} 分），建议针对性练习。")
