import streamlit as st

from core.loader import find_problem, load_language
from core.progress import ProgressDAO, format_local_ts
from ui.components import ALL_LANGS, LANG_META, ai_feedback_block, code_highlight_lang, hero, navigate_to_problem, section_title

# find_problem 每次全量线性扫描该语言题库；错题本里每道错题都会调一次。
# 缓存查找结果：100 道错题从 O(M×P) 降为 O(M+P)。
_problem_lookup_cache: dict = {}


def _lookup_problem(lang: str, pid: str):
    key = (lang, pid)
    if key not in _problem_lookup_cache:
        _problem_lookup_cache[key] = find_problem(lang, pid)
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
    due_reviews = dao.get_due_reviews(limit=50)
    overdue_count = len(due_reviews)
    wrong_count = len(mistakes)

    st.markdown(f"**错题 {wrong_count} 道 · 到期复习 {overdue_count} 道**")

    if wrong_count == 0 and overdue_count == 0:
        st.success("没有错题也没有到期复习，做得不错！")
        return

    tab_labels = []
    if overdue_count:
        tab_labels.append(f"到期复习 ({overdue_count})")
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
        st.info("没有可分组的弱项。")
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
