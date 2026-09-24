import os

import streamlit as st

from core import loader as content_loader
from core.loader import find_problem, load_language
from core.progress import ProgressDAO, format_local_ts
from ui.components import render_empty_state
from ui.components import ALL_LANGS, LANG_META, ai_feedback_block, code_highlight_lang, hero, navigate_to_problem, section_title

# find_problem 每次全量线性扫描该语言题库；错题本里每道错题都会调一次。
# 缓存查找结果：100 道错题从 O(M×P) 降为 O(M+P)。
# l923-19：缓存键第三元是题面 yaml 的 mtime ⇒ 改了题面、下一帧就取新值，
# 不必重启进程；mtime 取不到（题已删、pid 形态不符）时该格退化成旧语义
# （一次写入、进程内不再失效）。陈旧窗口由 2 秒（core/loader 的签名 memo
# TTL）封顶，不再是「进程级永不失效」。详见 tests/test_mistakes_lookup_cache.py。
_problem_lookup_cache: dict = {}


def _problem_yaml_mtime(lang: str, pid: str):
    """题面 yaml 的 mtime；任何一环取不到都返回 None（退化，不抛错）。

    pid 形如 `<lang>/<slug>/<stem>`（core/loader.py 的 `_build_problem` 是单源），
    故题面文件 = 内容根/<lang>/<slug>/<stem>.yaml，直接 stat、不扫全表。
    内容根单源取 core.loader 的默认目录，避免本文件再硬编码一份 content/ 路径。
    """
    parts = pid.split("/")
    if len(parts) != 3 or parts[0] != lang:
        return None
    base = getattr(content_loader, "_DEFAULT_CONTENT", None)
    if not base:
        return None
    try:
        return os.path.getmtime(os.path.join(base, *parts) + ".yaml")
    except OSError:
        return None


def _drop_stale_entries(key) -> None:
    """同题只留最新 mtime 那一格。

    mtime 进键后若不剪旧格，每改一次题就多一格，开发模式反复改题会让字典
    无界增长。剪完之后仍是「每题至多一次扫表」，O(M+P) 的复杂度承诺不变。
    """
    lang, pid = key[0], key[1]
    for stale in [k for k in _problem_lookup_cache
                  if k[0] == lang and k[1] == pid and k != key]:
        del _problem_lookup_cache[stale]


def _lookup_problem(lang: str, pid: str):
    key = (lang, pid, _problem_yaml_mtime(lang, pid))
    if key not in _problem_lookup_cache:
        _problem_lookup_cache[key] = find_problem(lang, pid)
        _drop_stale_entries(key)
    return _problem_lookup_cache[key]


def render_mistakes():
    hero("错题与复习", "集中处理到期复习、错题重做与薄弱专题")

    dao = ProgressDAO()
    try:
        _render_mistakes_body(dao)
    finally:
        dao.close()


def _render_mistakes_body(dao: ProgressDAO):
    mistakes = dao.list_mistakes()
    # limit=50 ⇒ 到期侧拿到的是**页内条数**（core/progress.py 的那条 SQL 带 LIMIT，
    # 真数在库侧就被丢掉），错题侧 list_mistakes() 无 LIMIT ⇒ 全量真数。
    # 汇总行文案按这个不对称标出下限语义（l923-20）；「加 COUNT(*) 伴生查询」出口 l924-09
    # 已实装为**下方净新增的一行**（get_due_reviews_total），汇总行与 limit=50 未换口径。
    due_reviews = dao.get_due_reviews(limit=50)
    overdue_count = len(due_reviews)
    wrong_count = len(mistakes)

    st.markdown(f"**错题 {wrong_count} 道 · 最近 50 条内到期复习 {overdue_count} 道**")
    # l924-09：上面那句的 COUNT(*) 伴生出口落地（l922-123 遗留 / l923-20 在册的第二条出口）。
    # 只在「页打满」时才多问一次真数——未打满时真数恒等于页内条数，那一行纯属重复。
    # 真数确实更大才提示；相等时不提示（此时「最近 50 条内」已是完整事实）。
    # 汇总行的文案与 :75 的 limit=50 实参一律未动：这一行是**净新增**，不改任何既有读数。
    if overdue_count == 50:  # 50 与 :75 的 limit 同源，跨源一致性由 test_mistakes_tabs_contract 钉
        due_total = dao.get_due_reviews_total()
        if due_total > overdue_count:
            st.caption(f"实际到期共 {due_total} 道 · 上面只列出最先到期的 {overdue_count} 道")

    if wrong_count == 0 and overdue_count == 0:
        st.success("没有错题也没有到期复习，做得不错！")
        return

    tab_labels = []
    if overdue_count:
        tab_labels.append(f"到期复习 ({overdue_count} · 至多)")
    if wrong_count:
        tab_labels.append(f"错题重做 ({wrong_count})")
    tab_labels.append("弱项专练")

    tabs = st.tabs(tab_labels)
    tab_idx = 0

    if overdue_count:
        with tabs[tab_idx]:
            _render_due_reviews(dao, due_reviews)
        tab_idx += 1

    if wrong_count:
        with tabs[tab_idx]:
            _render_wrong_problems(dao, mistakes)
        tab_idx += 1

    with tabs[tab_idx]:
        _render_weak_topics(dao, mistakes)


def _render_due_reviews(dao, reviews):
    section_title("到期复习")
    st.caption("这些题你之前做对了，但间隔复习算法认为该重新巩固了。")
    for r in reviews:
        meta = LANG_META.get(r["lang"], {"name": r["lang"], "icon": "·"})
        topic_obj, problem_obj = _lookup_problem(r["lang"], r["problem_id"])
        title = problem_obj.title if problem_obj else r["problem_id"]
        with st.container(border=True):
            col_l, col_r = st.columns([4, 1])
            with col_l:
                st.markdown(f"**{meta['icon']} {meta['name']} · {title}**")
                days_overdue = ""
                if r.get("next_due_date"):
                    from datetime import date
                    delta = (date.today() - date.fromisoformat(r["next_due_date"])).days
                    if delta > 0:
                        days_overdue = f" · 逾期 {delta} 天"
                st.caption(f"复习间隔 {r.get('interval_days', '?')} 天{days_overdue}")
            with col_r:
                missing = not (topic_obj and problem_obj)
                if st.button("复习 →", key=f"review_{r['lang']}_{r['problem_id']}",
                             type="primary", use_container_width=True,
                             disabled=missing):
                    navigate_to_problem(r["lang"], topic_obj.slug, r["problem_id"])
            if missing:
                st.caption("该题已不在题库中，可以忽略。")


def _render_wrong_problems(dao, mistakes):
    section_title("错题重做")
    st.caption("做错的题在这里汇总，重做通过后就能移除。")
    for m in mistakes:
        meta = LANG_META.get(m["lang"], {"name": m["lang"], "icon": "·"})
        topic_obj, problem_obj = _lookup_problem(m["lang"], m["problem_id"])
        title = problem_obj.title if problem_obj else m["problem_id"]
        with st.container(border=True):
            col_l, col_r = st.columns([4, 1])
            with col_l:
                st.markdown(f"**{meta['icon']} {meta['name']} · {title}**")
                st.caption(f"上次提交：{format_local_ts(m['ts'])}")
            with col_r:
                missing = not (topic_obj and problem_obj)
                if st.button("再做 →", key=f"redo_{m['problem_id']}",
                             type="primary", use_container_width=True,
                             disabled=missing):
                    navigate_to_problem(m["lang"], topic_obj.slug, m["problem_id"])
            if missing:
                st.caption("该题已不在题库中，可以忽略。")
            with st.expander("上次代码与点评"):
                st.code(m["code"], language=code_highlight_lang(m["lang"]))
                if m["ai_feedback"]:
                    ai_feedback_block(m["ai_feedback"])


def _render_weak_topics(dao, mistakes):
    section_title("弱项专练")
    st.caption("按专题分组，集中攻克薄弱环节。")

    topic_stats = {}
    for m in mistakes:
        topic_obj, _ = _lookup_problem(m["lang"], m["problem_id"])
        if topic_obj:
            key = f"{m['lang']}/{topic_obj.slug}"
            if key not in topic_stats:
                topic_stats[key] = {"lang": m["lang"], "slug": topic_obj.slug,
                                    "title": topic_obj.title, "count": 0}
            topic_stats[key]["count"] += 1

    if not topic_stats:
        render_empty_state("暂无可分组的弱项", "再多积累几道错题，智能分组会自动出现")
        return

    sorted_topics = sorted(topic_stats.values(), key=lambda x: -x["count"])
    for t in sorted_topics:
        meta = LANG_META.get(t["lang"], {"name": t["lang"], "icon": "·"})
        with st.container(border=True):
            col_l, col_r = st.columns([4, 1])
            with col_l:
                st.markdown(f"**{meta['icon']} {t['title']}**")
                st.caption(f"{t['count']} 道错题")
            with col_r:
                if st.button("练习 →", key=f"weak_{t['lang']}_{t['slug']}",
                             use_container_width=True):
                    # 走统一导航：语言页只认 selected_lang + selection
                    navigate_to_problem(t["lang"], topic_slug=t["slug"])
