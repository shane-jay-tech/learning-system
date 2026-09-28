import hashlib
import html
import logging
from datetime import date, timedelta

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

from core.achievements import check_achievements, get_all_earned, get_all_with_state, get_progress_summary, get_achievement
from core.loader import find_problem
from core.progress import ProgressDAO, format_local_ts
from ui.components import render_empty_state, render_error_notice, render_notice
from core.recommend import cross_recommend, recommend
from core.report import CALIBER_NOTE, generate_report, report_to_html, report_to_markdown
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


def _count_rows(dao, sql: str) -> int:
    """导出缓存键专用的单表 COUNT(*)：一次计数远小于再序列化一遍全库 JSON。

    sql 一律是本模块内写死的字面量（不接外部输入），故直接 execute；
    取不到值时按 0 计，宁可多序列化一次也不能少。
    """
    row = dao.conn.execute(sql).fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def _import_feedback_text(stats: dict) -> str:
    """导入完成文案的**单一来源**。

    成功当场不再直接 st.success——紧接着的 st.rerun() 会把那一帧整体丢掉（l922-105），
    文案改由下一次渲染首行回显，所以抽成函数供两处共用。
    """
    return (f"导入完成：答题 {stats['attempts']} 条 · 事件 {stats['learning_events']} 条 · "
            f"状态 {stats['problems_status']} 题 · 复习 {stats['review_state']} 题 · "
            f"元数据 {stats['meta']} 项")


def _report_file_tag(days: int) -> str:
    """下载文件名的期别标记（l923-11：消化 l922-121 登记的 :244 死局部量 `days`）。

    面板只有两个生成入口，写进 session_state 的 days 只可能是 7（:242）或 30（:251），
    映射成 week/month 让用户在下载目录里一眼分得清周报还是月报；
    其它值（未来若加「自定义区间」，或脚本直接调 generate_report）退回 `d<days>` 原样标数，
    **不静默归类**——把 14 天叫 week 会比不标更坏。
    """
    return {7: "week", 30: "month"}.get(days, f"d{days}")


# 「各语言通过情况」的分行参数（l922-120）：每行最多 3 张卡。
# 取 3 而非 4：5 门语言在每行 4 张下必然排成 4+1，每行 3 张正好 3+2；
# 卡宽也从 1/4 行宽回到 1/3（1366 下更宽松）。上限仍守着 h912-13 修复② 的「每行 ≤4 列」，
# 该意图现由 tests/test_ergo_h912_13.py::test_dashboard_column_cap_and_1280_breakpoint
# 以「扫描所有 st.columns 字面量槽位数 ≤4」的机械断言把守。
_CARDS_PER_ROW = 3


def _lang_card_rows(langs, per_row: int = _CARDS_PER_ROW):
    """按每行最多 per_row 张切块，逐行返回 (st.columns 槽位权重, 首张卡的槽位下标, 该行语言列表)。

    末行不满时左右各补 (per_row - count) / 2 的等宽空槽，把卡片**居中**，同时保证每张卡
    宽度恒为 1/per_row 行宽（左右空槽之和 + count 张卡 = per_row，故归一化后每卡仍是 1/per_row）。
    count == per_row 时不补空槽——st.columns 拒绝权重 ≤ 0。langs 为空则一行都不产。
    """
    for i in range(0, len(langs), per_row):
        chunk = langs[i:i + per_row]
        count = len(chunk)
        if count == per_row:
            yield [1] * per_row, 0, chunk
        else:
            pad = (per_row - count) / 2
            yield [pad] + [1] * count + [pad], 1, chunk


def render_dashboard():
    hero("学习面板", "用趋势与复习状态了解进展，决定下一步学什么")

    dao = ProgressDAO()
    try:
        _render_dashboard_body(dao)
    finally:
        dao.close()


def _render_dashboard_body(dao):
    # 上一次导入成功的反馈：只回显一帧，pop 掉即自动清除（想立刻清就是再触发一次 rerun）。
    _feedback = st.session_state.pop("_import_feedback", None)
    if _feedback:
        st.success(_import_feedback_text(_feedback))

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
        render_empty_state("还没有任何提交记录", "先去做几道题，回来看看学习图")
    else:
        attempts_map, passed_map = _build_chart_data(daily, days=14)
        df = pd.DataFrame({
            "提交": list(attempts_map.values()),
            "通过": list(passed_map.values()),
        }, index=list(attempts_map.keys()))
        st.bar_chart(df, height=240)

    section_title("各语言通过情况")
    # l922-120：旧写法 st.columns(min(n, 4)) ＋ cols[i % len(cols)] 把第 5 张卡塞回第 1 列的
    # 纵向堆叠里——st.columns 一行就是一个 flex 容器、不会自动折行，取模只是复用同一列，
    # 结果是第 5 卡缩在 1/4 行宽、右侧 3/4 留白，1366 下视觉断裂。改为 3 张一行＋末行居中。
    for spec, offset, chunk in _lang_card_rows(list(ALL_LANGS)):
        slots = st.columns(spec)
        for j, lang in enumerate(chunk):
            meta = LANG_META[lang]
            s = summary.get(lang, {"solved": 0, "wrong": 0, "total": 0})
            attempts = lang_counts.get(lang, {}).get("attempts", 0)
            with slots[offset + j]:
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
        # l924-01：本区批级 try 下沉为循环体内 per-item try，与 `_render_cross_recommend`
        # 的记账循环同型（两区 except 语义自此拉齐）。旧形态 `try:` 包整个 for ⇒ 一条
        # emit_event 失败即出循环，本帧**后续条连试都不试**（一条坏项吃掉整区记账）；
        # 现收在单条循环体内 ⇒ 坏一项只掉一项。
        # 🔴 掉的那一项怎么落（=跨路径区那一案，不自创第三案）：**跳过该项、其余照常**，
        #    按项各记一条 DEBUG（带栈、不静默）；不计数、不汇总提示、不在面板上报警告。
        # ⚠️ 写序未动（add → impressions → emit 仍在送达之前，属 A2 裁决域，本单不越界）：
        #    失败那条本地已记账、事件库永无 ⇒ 下次渲染被 shown 门控挡掉。下沉后一次故障帧
        #    的「本地−事件库」差额从固定 1 条变成**本帧失败条数**（每项各丢各的），
        #    试过的条数从「首抛为止」变成全量——推演见 l923-07 结果「证据 3」。
        for rank, it in enumerate(plan, 1):
            pid_key = (it["lang"], it["problem_id"])
            if pid_key not in st.session_state[shown_key]:
                try:
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
                    logger.debug("dashboard: 推荐展示数据异常", exc_info=True)
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
                        # l927-29 写序裁决（方向＝档内 l922-102 遗留问题点名留的那个冲突点）：
                        # **emit_event 送达成功之后才做跳转变更**——上报失败就不跳。
                        # 旧形态 `navigate_to_problem` 在 try 外（l922-102 钉的"断网也能跳"），
                        # 于是事件库写失败那一帧 clicked 永不到库、用户却已被带走 ⇒ 漏斗只掉不补、
                        # 本地 impressions 与事件库从此差额 +1 且无重试入口。现以 `reported` 旗标门控跳转：
                        # 失败帧停在面板，用户可再点一次重试上报（重试会再记一次 attempts）。
                        # 🔴 本裁决**有意**接受的代价：事件库真故障时该按钮变死键且面板零提示
                        #    ——与曝光侧同型的可见反馈要不要加，属另单裁决，见 docs/insights/l927-29-note.md §三。
                        reported = False
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
                            reported = True
                        except Exception:
                            logger.debug("dashboard: 推荐事件上报异常", exc_info=True)
                        if reported:
                            navigate_to_problem(it["lang"], it["topic_slug"], it["problem_id"])

    _render_cross_recommend(dao)
    _render_achievements(dao)
    _render_heatmap(dao)

    section_title("📄 学习报告导出")
    # a-47/c-04：周报卡常驻口径提示（纯文案；p912-40 遗留——任务条数口径随阅读合并规则变更，跨期直比会失真）
    # l923-10：文案改引 core.report.CALIBER_NOTE 单源（与 .md/.html 导出注记同一常量），
    #          面板这一行的字面副本被消灭——两处各写一遍时改一处就漂移（l922-106 当初就是靠
    #          tests/test_report_markdown_contract.py 的正则比同句兜住，现由构造保证）。
    st.caption(CALIBER_NOTE)
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
        # l923-11：上面这行读到的 days 原本整块再没被引用（l922-121 登记的死局部量），
        # 于是周报与月报的下载区四项（文案/文件名/mime/help）逐项相等、用户分不出拿的是哪期。
        # 现把期别并进**文件名**（另一条出口「下载区加 caption 标近 N 天」未选：
        # 文件名会落盘、跨机器跨时间都留痕，caption 只在面板那一帧有效）。
        period_tag = _report_file_tag(days)
        with dl_col1:
            st.download_button(
                "⬇️ 下载报告 (.md)",
                data=st.session_state["last_report_md"],
                file_name=f"learning_report_{period_tag}_{date.today().isoformat()}.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with dl_col2:
            st.download_button(
                "🖨️ 打印版 (.html)",
                data=st.session_state.get("last_report_html", ""),
                file_name=f"learning_report_{period_tag}_{date.today().isoformat()}.html",
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
        # 导出全库 JSON 有成本：按「六张表各自行数」做渲染内缓存，数据没变化时复用上次序列化结果。
        # 键必须覆盖 export_all 导出的每一张表：只数 attempts/learning_events 时，
        # 一个只带 problems_status/review_state 的导入包不改这两个计数，
        # rerun 后立刻导出会拿到合并前的旧快照（l922-104 复现）。
        _exp_key = "_".join(str(n) for n in (
            dao.total_attempts(), dao.event_count(),
            _count_rows(dao, "SELECT COUNT(*) FROM problems_status"),
            _count_rows(dao, "SELECT COUNT(*) FROM review_state"),
            _count_rows(dao, "SELECT COUNT(*) FROM rubric_scores"),
            _count_rows(dao, "SELECT COUNT(*) FROM meta")))
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
                        blob = uploaded.getvalue()
                        raw = blob.decode("utf-8")
                        # l923-09 防重（同一份字节在一次会话里只真正合并一次）：
                        # 导入成功后 file_uploader 的控件态由 key 持久化，那个文件仍在原处，
                        # 「确认导入」还能再按一次；而 attempts / learning_events / rubric_scores
                        # 是只追加表（import_all 对它们不去重，见 test_data_portability.py:46 的
                        # by-design 断言），第二下会把同一批数据原样翻倍（l922-105 遗留问题）。
                        # ⚠️ 任务书首选的「清 uploader 相关键」在 streamlit 里做不到无痕：控件实例化后
                        #    pop/赋值它的 key 会抛 StreamlitAPIException，换 key 重建又会每次导入留下
                        #    一个陈旧 session_state 键（同 §十二 点名的 editor_* 无界增长那类），
                        #    故这里按内容指纹收口，副作用面更小。
                        fp = hashlib.sha256(blob).hexdigest()
                        if st.session_state.get("_import_consumed_fp") == fp:
                            render_notice(
                                "这份文件本次会话已经导入过了，**已跳过重复导入**："
                                "答题记录、学习事件与评分明细是只追加表，再确认一次会把它们原样翻倍。"
                                "确需重导请重新导出一份内容不同的文件（或换一台机器操作）。",
                            )
                        else:
                            stats = import_json(dao, raw)
                            st.session_state["_import_consumed_fp"] = fp
                            # 当场 st.success 会被紧接着的 st.rerun() 整帧丢掉，用户只看到页面闪回
                            # 上传态、五项统计一个字都不露（l922-105）：写进 session_state，
                            # 由下一次渲染首行回显一次。
                            st.session_state["_import_feedback"] = stats
                            dao._clear_memo()
                            # 合并式导入会覆盖同键旧值而**不改任何表的行数**，上面的行数键抓不到这种情形：
                            # 显式作废缓存，rerun 后那次渲染必然重新序列化（l922-104）。
                            st.session_state["_export_cache_key"] = None
                            st.rerun()
                    except Exception as exc:
                        render_error_notice(
                            "导入失败",
                            reason=f"{exc}",
                            next_action="当前数据未受影响，可修正文件后重试导入",
                        )

    section_title("最近活动")
    if not recent:
        render_empty_state("还没有提交记录", "做完第一道题后这里开始统计", compact=True)
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
            # 🔴 l923-07：本区原先整段裸奔——emit 一抛就窜出 _render_cross_recommend，
            # 而 render_dashboard(:94-97) 只 try/finally 不 catch ⇒ 后半页（成就/热力图/
            # 报告导出/学习数据/最近活动）全部不渲染。改成 per-item try 后一条失败只影响一条，
            # 与 dashboard 区 :169-183 同型（含 logger.debug 不静默）。
            # l927-37（A2 落地，设计稿 docs/insights/learn-shown-writeorder-design-20260923.md §三 A2／§七）：
            # 写序由 `add → impressions → emit` 换成 **emit 先、成功后才落本地账**（`add` 成功后再记
            # impressions）。旧写序的后果是「失败那条曝光永久丢失且不自愈」：本地 shown 已记下它，
            # 下一次渲染被上面那道 `not in cross_shown_key` 门控跳过 ⇒ 事件库永远补不回来，
            # 本地口径与 DB 漏斗从此恒差 1（l922-101 实测）。换序后失败那条不进 shown ⇒ 恢复帧会
            # 重试同一条；rid 由 `_make_rec_id` 确定性生成，补报带的是同一个 rid，归因链自动接上。
            # emit 的前置条件（rid 与 payload）在 try 外算齐，失败帧压根不进本地账，
            # 于是点击侧 `imp.get(...)` 回退分支生效 ⇒ **故障帧那一条 clicked 带空 rid/rank=0**，
            # 这是 A2 的已知残余风险（设计稿 §八 待裁决 1，形态＝肉眼可辨的缺口，比旧写序的
            # 「悬空 rid」可查，旧形态的 rid 在事件库里永不出现）。
            # ⚠️ 本单只换跨路径区：今日推荐区 `:191-205` 的曝光写序**未动**（卷宗只点名本区，
            #    w42 §B.1 禁"顺手一致"）⇒ 两区曝光写序自本单起不一致，见
            #    docs/insights/l927-37-writeseq.md §三。拉齐方向别照抄 l924-01——那单在 except
            #    粒度上把今日推荐"照跨路径那一案"改（新向旧看齐），本单方向相反（旧形态该向本区看齐）。
            rec_id = _make_rec_id("cross_path", "cross_path", it["lang"], it["problem_id"], rank)
            payload = {"reason_code": "cross_path", "surface": "cross_path",
                       "rank": rank, "recommendation_id": rec_id}
            try:
                dao.emit_event("recommendation_shown", lang=it["lang"],
                               problem_id=it["problem_id"], payload=payload)
                st.session_state[cross_shown_key].add(pid_key)
                st.session_state[impressions_key][(it["lang"], it["problem_id"], "cross_path")] = {
                    "recommendation_id": rec_id, "reason_code": "cross_path", "rank": rank,
                }
            except Exception:
                logger.debug("dashboard: 跨路径推荐展示异常", exc_info=True)

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
                    # l923-07 名实订正：这个 except 包的是 recommendation_clicked 上报，
                    # 原文案写「展示异常」会把排障指向错误站点（展示侧现在有自己的 except 了）。
                    logger.debug("dashboard: 跨路径推荐点击上报异常", exc_info=True)
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
        render_empty_state("还没有解锁任何成就", "开始做题即可获得第一枚徽章")

    cols_per_row = 4
    # 末行居中：复用 _lang_card_rows（l922-120 语言卡同款修法），余数行左右各补等宽空槽 ⇒ 整行居中且每卡仍 1/4 行宽
    for spec, offset, chunk in _lang_card_rows(all_states, cols_per_row):
        cols = st.columns(spec)
        for j, item in enumerate(chunk):
            a = item["achievement"]
            state = item["state"]
            pct = item["progress"]
            with cols[j + offset]:
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
    """13 周（91 个日格）学习热力图。"""
    section_title("📅 学习热力图（最近 13 周）")

    rows = dao.conn.execute(
        "SELECT DATE(ts, 'localtime') AS d, COUNT(*) AS n, SUM(passed) AS p "
        "FROM attempts WHERE ts >= datetime('now', '-91 days') "
        "GROUP BY d ORDER BY d"
    ).fetchall()
    if not rows:
        render_empty_state("还没有提交记录", "开始做题后这里会展示热力图")
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
        render_empty_state("还没有推荐数据", "做几天题后这里会展示推荐效果漏斗", compact=True)
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
        render_empty_state("还没有进入复习循环的题目", "做对题后会自动加入间隔复习", compact=True)
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
        render_empty_state("还没有开放题维度评分数据", "做几道开放题后这里会展示能力趋势", compact=True)
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
