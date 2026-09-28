import html

import logging
import streamlit as st

from core.ai_generate import generate_variant
from core.ai_review import follow_up, ask_lesson
from core.judge import judge
from core.loader import load_language
from core.progress import ProgressDAO
from ui.components import (
    LANG_META, ai_feedback_block, code_editor, drop_shown_judge_result, hero, io_block,
    judge_result_key, lesson_box, navigate_to_problem, render_empty_state, render_error_notice, render_notice, section_title, stderr_block, verdict_banner,
)


logger = logging.getLogger(__name__)


def _ensure_state():
    st.session_state.setdefault("selected_topic_idx", 0)
    st.session_state.setdefault("selected_problem_idx", 0)
    st.session_state.setdefault("ai_variants", {})
    # Unified selection state: other pages write here to navigate
    st.session_state.setdefault("selection", None)


def _problem_key(pid: str) -> str:
    return f"code::{pid}"


def _editor_key(active_id: str) -> str:
    """编辑器 widget key（带 epoch 计数）。

    ACE/text_area 是带 key 的 widget：其内部状态优先级高于 value 参数，
    直接改 session_state["code::..."] 不会让编辑器视觉重置（前端未受控、
    下次 rerun 还会把旧值写回）。重置时把 epoch+1 → key 变化 → 组件重建，
    starter_code 才能真正生效。
    """
    epoch = st.session_state.setdefault(f"editor_epoch::{active_id}", 0)
    return f"editor_{active_id}_{epoch}"


_PROBLEM_STATE_PREFIXES = ("code::", "chat_ctx::", "chat_history::", "preask_hist::",
                           "show_preask::", "editor_epoch::")
_LRU_CAP = 30  # 只保留最近访问的 30 道题的状态，防止长会话 session_state 无界累积


def _touch_problem(active_id: str) -> None:
    """记录访问并回收过期的题目状态（代码/对话/编辑器）。

    每道题的 code::/chat::/editor 状态常驻 session_state，长会话刷几百道题
    会无界累积。用 LRU 队列保留最近 30 道题，其余按前缀清理。
    """
    if active_id.startswith("AI_VARIANT::"):
        # l927-40：变式题不再「完全豁免」，改走自己的有界队列（第二终点，见 _touch_variant）。
        # 旧形态是这里直接 return ⇒ 从不点「↩ 回到原题」的变式题六族键整场会话无界
        #（l923-15 遗留 3 ／ l924-03 遗留 1 ／ l924-04 遗留 C-6 点名的那半边）。
        _touch_variant(active_id)
        return
    lru = st.session_state.setdefault("_problem_lru", [])
    if not lru or lru[-1] != active_id:
        lru.append(active_id)
    keep_ids = set(lru[-_LRU_CAP:]) | {active_id}
    for pid in list(lru[:-_LRU_CAP]):
        if pid in keep_ids:
            continue
        for prefix in _PROBLEM_STATE_PREFIXES:
            st.session_state.pop(prefix + pid, None)
        # 编辑器 widget 状态 key：editor_<pid>_<epoch>（pid 本身可能含下划线，
        # 精确按 pid 匹配：去掉前缀后从最后一个 _ 切分）
        for k in list(st.session_state.keys()):
            if not k.startswith("editor_"):
                continue
            body = k[len("editor_"):]
            if "_" in body and body.rsplit("_", 1)[0] == pid:
                st.session_state.pop(k, None)
    st.session_state["_problem_lru"] = lru[-_LRU_CAP:]


def _retire_variant(variant_id: str) -> None:
    """变式题生命周期终点：六族题目状态键 + editor widget 残键一次清净（l924-03）。

    `_touch_problem` 对 `AI_VARIANT::` 提前 return（:55），所以
    `_PROBLEM_STATE_PREFIXES` 那六族键与 `editor_<vid>_<epoch>` widget 键
    都不受 LRU 逐出管理。l923-15 在「↩ 回到原题」只认领了前缀表里 editor 计数器
    那一族 + widget 残键，另外五族（code / chat_ctx / chat_history /
    preask_hist / show_preask）对变式题仍旧无界增长（l923-15 遗留 2），
    本函数把那半边补齐。

    为什么「退回原题」是唯一终点：`core/ai_generate.py:105` 把变式题 id 拼成
    确定性的 `AI_VARIANT::<原题 id>`，一旦从 `ai_variants` 弹出就再也不会被渲染；
    重刷变式拿到的还是同一个 id，题面、代码、对话历史若留着反而会串到下一道
    变式上（用户看到的是旧代码/旧聊天记录，而题面是新的）。

    只清被退回的那一道题：作用域按 `prefix + variant_id` **精确拼键**，不用
    startswith —— 变式题 id 之间互为前缀（`AI_VARIANT::p1` 与 `AI_VARIANT::p1_deep`），
    粗匹配会把仍开着的兄弟变式的用户代码连同 epoch 计数器一起抹掉，下次
    `_editor_key` 退回 0 → widget key 变化 → 组件重建 → 用户已写代码被 starter_code
    覆盖，那是比泄漏更重的用户可见缺陷。同理，对非 `AI_VARIANT::` 的 id 直接拒绝。

    键名一律用「表项 + variant_id」拼接，本函数体内（连注释与 docstring）都不出现
    「epoch 计数器前缀紧跟左花括号」那种字面量形态 —— 它的站点数被
    `tests/test_language_editor_epoch.py` 钉成恰 2 处（读侧 :40 / 写侧自增处），
    造出第三处就会把那条在册桩弄红（l923-15 实测踩过）。
    """
    if not variant_id.startswith("AI_VARIANT::"):
        return
    for prefix in _PROBLEM_STATE_PREFIXES:
        st.session_state.pop(prefix + variant_id, None)
    # 编辑器 widget 状态 key：editor_<pid>_<epoch>（pid 自身可能含下划线，
    # 故去掉前缀后按最后一个 _ 切分来精确匹配 pid —— 与 _touch_problem 同一判据）
    for k in list(st.session_state.keys()):
        if not k.startswith("editor_"):
            continue
        body = k[len("editor_"):]
        if "_" in body and body.rsplit("_", 1)[0] == variant_id:
            st.session_state.pop(k, None)


def _touch_variant(variant_id: str) -> None:
    """变式题的**第二生命周期终点**：独立有界队列（l927-40，档内「出口一」）。

    终点一（l924-03 的 `_retire_variant`）只覆盖「用户点了 ↩ 回到原题」那半边；
    刷了变式**直接换题／离开**的那半边今天没有任何终点——`_touch_problem` 早年对
    `AI_VARIANT::` 直接 return，六族状态键与 widget 残键就按「每刷一道变式 +1」无界增长
    （l923-15 遗留 3、l924-03 遗留 1、`docs/insights/learn-editor-key-spec-20260924.md`
    遗留 C-6 三处都登记过，指定的修法就是「给变式题一个独立有界队列」）。

    形态与本文件的真题侧 `_touch_problem` 同型，三点照抄不另创：
      1. 队列独立（`_variant_lru` 与 `_problem_lru` 两把），因为两边粒度不同：真题按题、
         变式也按题，但**变式 id 与原 id 会重叠展示**（`ai_variants` 里挂着），混进一张表
         会让真题侧的 keep_ids 判断把变式算进 30 个名额里，逐出时点从此不可推；
      2. 封顶沿用 `_LRU_CAP`（30），不自造第二个阈值——「保留最近 N 道题」的口径全仓只有一处，
         要调就调那一个数；
      3. 逐出动作只调 `_retire_variant`，**不硬列前缀、不写任何 epoch 字面量形态**：
         六族与 widget 残键的判据由 `_retire_variant` 遍历共享表 `_PROBLEM_STATE_PREFIXES`
         给出（在册桩 `test_retire_iterates_the_shared_table` 钉着这条同源约束）。

    与终点一的分工：终点一在「退回」那一刻**立即**清；本函数只在队列**溢出**时清最旧那条。
    为什么不在离开/换题的那一刻立即清：`ai_variants` 并不会因换题而弹出，用户切回来看到的
    还是那道变式题（`_active_problem` 直接取），当场清键等于把他刚写的代码换成 starter_code
    ——那是比泄漏更重的用户可见缺陷，与 l924-03「只清被退回的那一道」同一判断。

    🔴 本形态有意接受的代价（如实登记，不粉饰）：被队列逐出的变式**仍留在 `ai_variants` 里**，
    用户 30 道变式之后切回那道题，题面还是变式、但代码/对话/提示都退回初值（与真题侧被 LRU
    逐出后重访同形）。要连 `ai_variants` 一起弹（重访直接回到原题）是可见行为变更，超本单授权。

    队列去重（与真题侧 `_touch_problem` 的「只看队尾」不同，这里是**先摘再挂**）：
    变式题在每次 rerun 都会被 `_touch_problem` 摸一次，来回切题会让旧形态那样把同一个 id
    反复堆进队列，30 个名额被重复项吃满 ⇒ 「有界」退化成「按 rerun 次数逐出」。
    """
    queue = st.session_state.setdefault("_variant_lru", [])
    while variant_id in queue:
        queue.remove(variant_id)
    queue.append(variant_id)
    keep_ids = set(queue[-_LRU_CAP:])
    for vid in list(queue[:-_LRU_CAP]):
        if vid in keep_ids:
            continue
        _retire_variant(vid)          # 逐出＝走终点，清键面与「↩ 回到原题」完全一致
    st.session_state["_variant_lru"] = queue[-_LRU_CAP:]


def _clear_variant_editor_keys(variant_id: str) -> None:
    """薄壳：职责已全部下沉到 `_retire_variant`（l924-03 同批改法）。

    保留这个名字是因为 l923-15 的在册桩按**源文本字面量**钉了「↩ 回到原题」
    分支里的调用式与顺序（`tests/test_editor_variant_keys.py` 的
    `test_clear_called_once_in_back_branch` / `test_clear_order_retire_then_clear_then_rerun`
    各数一次 `_clear_variant_editor_keys(active_id)`），改名会让那两条红——
    而那属别的单的账。故此处只做转调，清键面由「editor 两族」扩到「六族 + widget」。
    """
    _retire_variant(variant_id)


def _active_problem(base_problem):
    """返回当前展示的题（base 或 AI 变式题）+ is_variant 标志。"""
    variants = st.session_state.get("ai_variants", {})
    v = variants.get(base_problem.id)
    if v is None:
        return base_problem.to_dict(), False
    return v, True


def render_language():
    _ensure_state()
    lang = st.session_state.get("selected_lang")
    if not lang:
        render_notice("请先在主页选择一门语言。")
        return

    if lang not in LANG_META:
        render_error_notice(
            "未知语言",
            reason=f"语言标识 {lang} 不在语言表（LANG_META）中",
            next_action="返回主页重新选择一门已支持的语言",
        )
        return

    meta = LANG_META[lang]
    topics = load_language(lang)
    if not topics:
        render_error_notice(
            "题库内容未找到",
            reason=f"{meta['name']} 尚无可用的题库内容",
            next_action="先在内容目录生成该语言题库，或另选一门语言",
        )
        return

    # Resolve selection state from unified selection dict
    sel = st.session_state.pop("selection", None)
    target_slug = None
    target_problem_id = None
    if sel and sel.get("lang") == lang:
        target_slug = sel.get("topic_slug")
        target_problem_id = sel.get("problem_id")

    if target_slug:
        for i, t in enumerate(topics):
            if t.slug == target_slug:
                st.session_state.selected_topic_idx = i
                st.session_state.selected_problem_idx = 0
                drop_shown_judge_result()
                st.session_state[f"topic_select_{lang}"] = i
                if target_problem_id:
                    for j, p in enumerate(t.problems):
                        if p.id == target_problem_id:
                            st.session_state.selected_problem_idx = j
                            st.session_state[f"problem_select_{lang}_{t.slug}"] = j
                            break
                break

    if st.session_state.selected_topic_idx >= len(topics):
        st.session_state.selected_topic_idx = 0
    topic = topics[st.session_state.selected_topic_idx]
    if not topic.problems:
        render_empty_state("该专题暂无题目", "换个专题，或用 AI 出题生成一组")
        return
    if st.session_state.selected_problem_idx >= len(topic.problems):
        st.session_state.selected_problem_idx = 0

    hero(f"{meta['name']} 练习", f"{meta['tagline']} · 选择专题与题目，完成后立即获得反馈")

    # 整段用 try/finally 保证 dao 在 st.rerun() 抛 StopException 时也释放
    dao = ProgressDAO()
    try:
        _render_body(lang, topics, topic, dao)
    finally:
        dao.close()


def _render_body(lang, topics, topic, dao):
    # 顶部：醒目的返回主页 / 换语言入口（不必去翻侧栏）
    top_l, _ = st.columns([1, 5])
    with top_l:
        if st.button("← 返回首页", use_container_width=True, key=f"back_home_{lang}"):
            st.session_state.route = "home"
            st.rerun()

    # 专题 / 题目是当前任务的核心控制项，放在正文顶部，避免被全局侧栏挤到折叠区下方。
    nav_topic, nav_problem = st.columns([3, 2], gap="medium")
    with nav_topic:
        topic_titles = [t.title for t in topics]
        select_key = f"topic_select_{lang}"
        if select_key not in st.session_state:
            st.session_state[select_key] = st.session_state.selected_topic_idx
        new_topic_idx = st.selectbox(
            "选择专题",
            options=list(range(len(topics))),
            format_func=lambda i: topic_titles[i],
            key=select_key,
        )
        if new_topic_idx != st.session_state.selected_topic_idx:
            st.session_state.selected_topic_idx = new_topic_idx
            st.session_state.selected_problem_idx = 0
            drop_shown_judge_result()
            st.rerun()

    with nav_problem:
        problem_options = []
        for p in topic.problems:
            status = dao.get_status(lang, p.id)
            badge = {"solved": "已通过", "wrong": "待改", "unseen": "未尝试"}.get(status, "未尝试")
            problem_options.append(f"{p.title} · {badge}")
        problem_key = f"problem_select_{lang}_{topic.slug}"
        if problem_key not in st.session_state:
            st.session_state[problem_key] = st.session_state.selected_problem_idx
        new_problem_idx = st.selectbox(
            "选择题目",
            options=list(range(len(topic.problems))),
            format_func=lambda i: problem_options[i],
            key=problem_key,
        )
        if new_problem_idx != st.session_state.selected_problem_idx:
            st.session_state.selected_problem_idx = new_problem_idx
            drop_shown_judge_result()
            st.rerun()

    base_problem = topic.problems[st.session_state.selected_problem_idx]
    active, is_variant = _active_problem(base_problem)
    active_id = active["id"]
    _touch_problem(active_id)  # LRU 回收：防止长会话 session_state 无界累积

    _viewed_key = f"_lesson_viewed_{lang}_{topic.slug}"
    if _viewed_key not in st.session_state:
        st.session_state[_viewed_key] = True
        try:
            dao.emit_event("lesson_viewed", lang=lang, topic_id=topic.slug)
        except Exception:
            logger.debug("language: lesson_viewed 事件上报失败", exc_info=True)

    # 双栏布局：左侧题面/讲解，右侧编辑器/结果
    left_col, right_col = st.columns([38, 62], gap="medium")

    is_open = active.get("judge_mode") == "ai_open"
    key = _problem_key(active_id)
    if key not in st.session_state:
        st.session_state[key] = active.get("starter_code", "")

    with left_col:
        if is_variant:
            st.markdown(
                '<div style="background:#FEF3C7;border-left:4px solid #F59E0B;'
                'padding:10px 14px;border-radius:8px;margin-bottom:10px;">'
                '<b>🤖 AI 出的变式题</b>　基于上一题改编。'
                '</div>',
                unsafe_allow_html=True,
            )
        with st.container(border=True):
            st.markdown(f"**{active['title']}**")
            st.markdown(active.get("statement", ""))
        if active.get("hints"):
            with st.expander("💡 不会做？看提示", expanded=False):
                for h in active["hints"]:
                    st.markdown(f"- {h}")

        with st.expander("📖 知识点讲解", expanded=False):
            lesson_box(topic.lesson_md or "(本节暂无讲解)")
            _render_lesson_chat(lang, topic)

        gen_col, back_col = st.columns(2)
        with gen_col:
            if st.button("✨ AI 变式题", key=f"gen_{base_problem.id}", use_container_width=True):
                with st.spinner("AI 正在出题（最长约 45 秒）..."):
                    variant = generate_variant(lang, base_problem.to_dict())
                if variant:
                    st.session_state.ai_variants[base_problem.id] = variant
                    st.session_state.pop(judge_result_key(active_id), None)
                    st.rerun()
                else:
                    render_error_notice(
                        "AI 出题失败",
                        reason="模型调用暂不可用或超时",
                        next_action="请稍后再试；可先用原题继续练习",
                    )
        with back_col:
            if is_variant:
                if st.button("↩ 回到原题", key=f"back_{base_problem.id}", use_container_width=True):
                    st.session_state.ai_variants.pop(base_problem.id, None)
                    _clear_variant_editor_keys(active_id)
                    st.session_state.pop(judge_result_key(active_id), None)
                    st.rerun()

    with right_col:
        section_title("你的回答" if is_open else "代码编辑器")
        if is_open:
            code = st.text_area(
                "answer", value=st.session_state[key], height=320,
                key=_editor_key(active_id), label_visibility="collapsed",
                placeholder="用你自己的话作答……AI 老师会按评分标准给你点评。",
            )
        else:
            code = code_editor(st.session_state[key], lang=lang, key=_editor_key(active_id))
        if code is not None:
            st.session_state[key] = code

        run_col, reset_col, ask_col = st.columns([2, 1, 2])
        with run_col:
            btn_label = "📝 提交给 AI 评判" if is_open else "▶ 提交运行"
            run_clicked = st.button(btn_label, type="primary", use_container_width=True, key=f"run_{active_id}")
        with reset_col:
            if st.button("↺ 重置", use_container_width=True, key=f"reset_{active_id}"):
                st.session_state[key] = active.get("starter_code", "")
                # epoch+1 → 编辑器 key 变化 → 组件重建，重置真正生效
                epoch_key = f"editor_epoch::{active_id}"
                st.session_state[epoch_key] = st.session_state.get(epoch_key, 0) + 1
                st.session_state.pop(judge_result_key(active_id), None)
                st.rerun()
        with ask_col:
            if st.button("💬 做题中问 AI", use_container_width=True, key=f"preask_{active_id}"):
                st.session_state[f"show_preask::{active_id}"] = True
                st.rerun()

        # 做题中问 AI：渲染在右栏按钮下方，紧邻触发按钮（此前在左栏，点击后要跨栏找输入框）
        if st.session_state.get(f"show_preask::{active_id}"):
            _render_pre_submit_chat(lang, topic, active, active_id, st.session_state.get(key, ""))

        if run_clicked:
            spinner_msg = ("⏳ AI 老师正在评判你的回答（通常几秒，网络慢时最长约 45 秒）..."
                           if is_open else "⏳ 正在运行代码并请 AI 点评（通常几秒，网络慢时最长约 45 秒）...")
            with st.spinner(spinner_msg):
                judge_dao = None if is_variant else dao
                result = judge(lang, active, code or "", dao=judge_dao)
            st.session_state[judge_result_key(active_id)] = result
            st.session_state.last_judge_pid = active_id
            # 判定完成即时提示：结果区在编辑器下方，rerun 后页面回顶，用户容易看不到
            st.toast("✅ 已判定，结果在下方" if result.passed else "❌ 未通过，看下方对比与点评")
            st.session_state[f"chat_ctx::{active_id}"] = {
                "code": code or "",
                "run_result": result.run_result,
                "passed": result.passed,
                "review": result.ai_feedback,
            }
            st.session_state[f"chat_history::{active_id}"] = []

        if (
            st.session_state.get(judge_result_key(active_id)) is not None
            and st.session_state.get("last_judge_pid") == active_id
        ):
            r = st.session_state[judge_result_key(active_id)]
            if is_open:
                verdict_banner(r.passed, 0)
                if r.expected_display and r.expected_display != "（开放题，无标准答案）":
                    with st.expander("📖 参考答案（写完再看）", expanded=False):
                        st.markdown(r.expected_display)
                if "暂时不可用" in (r.ai_feedback or ""):
                    render_notice("⚠️ AI 评判服务暂时不可用。判题结果未记录，请稍后重试。")
                else:
                    ai_feedback_block(r.ai_feedback)
                _render_chat(lang, active, active_id)
            else:
                elapsed = getattr(r.run_result, "elapsed_ms", 0) if r.run_result else 0
                verdict_banner(r.passed, elapsed)
                cmp_left, cmp_right = st.columns(2)
                with cmp_left:
                    section_title("期望输出")
                    io_block(r.expected_display, kind="expected")
                with cmp_right:
                    section_title("你的输出")
                    io_block(r.actual_display, kind="actual")
                if r.diff_hint:
                    st.caption(f"💡 {r.diff_hint}")
                if r.run_result and r.run_result.stderr:
                    section_title("错误信息")
                    stderr_block(r.run_result.stderr)
                if "暂时不可用" in (r.ai_feedback or ""):
                    # l919-03：notice 档位统一——st.info 改走 render_notice 统一形态（降级说明+下一步）。
                    render_notice("AI 点评暂时不可用（不影响判题结果）。下一步：稍后重新提交即可获得点评。")
                else:
                    ai_feedback_block(r.ai_feedback)
                _render_chat(lang, active, active_id)

    # 底部：上一个 / 下一个知识点切换
    _render_topic_nav(lang, topics)


def _render_topic_nav(lang, topics):
    """底部：切换上一个 / 下一个知识点（专题）。边界处自动隐藏对应按钮。"""
    idx = st.session_state.selected_topic_idx
    total = len(topics)
    st.markdown("---")
    prev_col, mid_col, next_col = st.columns([1, 2, 1])
    with prev_col:
        if idx > 0:
            if st.button("← 上一个知识点", use_container_width=True, key=f"prev_topic_{lang}"):
                navigate_to_problem(lang, topic_slug=topics[idx - 1].slug)
    with mid_col:
        st.markdown(
            f"<div style='text-align:center;color:#64748B;font-size:13px;padding-top:8px;'>"
            f"第 {idx + 1} / {total} 个知识点 · {html.escape(topics[idx].title)}</div>",
            unsafe_allow_html=True,
        )
    with next_col:
        if idx < total - 1:
            if st.button("下一个知识点 →", use_container_width=True, key=f"next_topic_{lang}"):
                navigate_to_problem(lang, topic_slug=topics[idx + 1].slug)


def _render_chat(lang: str, active: dict, active_id: str):
    """评语下方的多轮追问 chat。判题完成后默认展开（提高可发现性）。"""
    ctx_key = f"chat_ctx::{active_id}"
    history_key = f"chat_history::{active_id}"
    if ctx_key not in st.session_state:
        return
    ctx = st.session_state[ctx_key]
    history = st.session_state.setdefault(history_key, [])

    with st.expander("💬 不懂？继续问 AI 老师（多轮对话）", expanded=True):
        if history:
            st.markdown('<div class="section-title" style="margin-top:0">对话历史</div>', unsafe_allow_html=True)
            for msg in history:
                if msg["role"] == "user":
                    safe_text = html.escape(msg["text"])
                    st.markdown(
                        f'<div style="background:#EEF2FF;border-radius:10px;padding:10px 14px;margin:6px 0;">'
                        f'<b>🧑 你</b>　{safe_text}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    # AI 消息：标签栏 HTML + 内容用 st.markdown 渲染（保留 Markdown 格式）
                    st.markdown(
                        '<div style="background:#FEF3C7;border-radius:10px 10px 0 0;padding:8px 14px 4px;margin:6px 0 0;">'
                        '<b>🤖 AI 老师</b></div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(msg["text"])

        question = st.text_area(
            "在这里写你的问题",
            key=f"chat_input_{active_id}",
            placeholder="例如：你说的「list comprehension」具体是什么写法？为什么我这道题用不了？",
            height=80,
        )

        ask_col, clear_col, _ = st.columns([1, 1, 3])
        with ask_col:
            ask_clicked = st.button("发送提问", key=f"chat_ask_{active_id}", type="primary", use_container_width=True)
        with clear_col:
            if st.button("清空对话", key=f"chat_clear_{active_id}", use_container_width=True):
                st.session_state[history_key] = []
                st.rerun()

        if ask_clicked and question.strip():
            statement = active.get("statement", "")
            # 开放题：把评分标准带进追问上下文，避免 AI 老师的解答与判定标准打架
            if active.get("judge_mode") == "ai_open" and active.get("rubric"):
                statement = f"{statement}\n\n【本题评分标准 rubric】\n{active.get('rubric')}"
            problem_dict = {
                "title": active.get("title", ""),
                "statement": statement,
            }
            with st.spinner("AI 老师在想…（最长约 45 秒）"):
                answer = follow_up(
                    lang=lang,
                    problem=problem_dict,
                    code=ctx["code"],
                    run_result=ctx["run_result"],
                    passed=ctx["passed"],
                    initial_review=ctx["review"],
                    history=history,
                    user_question=question.strip(),
                )
            history.append({"role": "user", "text": question.strip()})
            history.append({"role": "ai", "text": answer})
            st.session_state[history_key] = history
            # 发送后清空输入框（发完问题文字还留着，用户得手动删，反人类）
            st.session_state.pop(f"chat_input_{active_id}", None)
            st.rerun()


def _render_pre_submit_chat(lang: str, topic, active: dict, active_id: str, code: str):
    """做题过程中问 AI（无需先提交）。"""
    hist_key = f"preask_hist::{active_id}"
    history = st.session_state.setdefault(hist_key, [])

    with st.expander("💬 做题中问 AI 老师", expanded=True):
        if history:
            for msg in history:
                if msg["role"] == "user":
                    safe = html.escape(msg["text"])
                    st.markdown(
                        f'<div style="background:#EEF2FF;border-radius:10px;padding:10px 14px;margin:6px 0;">'
                        f'<b>🧑 你</b>　{safe}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div style="background:#FEF3C7;border-radius:10px 10px 0 0;padding:8px 14px 4px;margin:6px 0 0;">'
                        '<b>🤖 AI 老师</b></div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(msg["text"])

        question = st.text_area(
            "做题中有疑问？随时问",
            key=f"preask_input_{active_id}",
            placeholder="例如：题目里说的'返回值'是什么意思？我不确定该用 for 还是 while……",
            height=80,
            label_visibility="collapsed",
        )
        ask_col2, close_col, _ = st.columns([1, 1, 3])
        with ask_col2:
            ask_clicked = st.button("发送", key=f"preask_send_{active_id}", type="primary", use_container_width=True)
        with close_col:
            if st.button("收起", key=f"preask_close_{active_id}", use_container_width=True):
                st.session_state[f"show_preask::{active_id}"] = False
                st.rerun()

        if ask_clicked and question.strip():
            with st.spinner("AI 老师在想…（最长约 45 秒）"):
                answer = ask_lesson(
                    lang=lang,
                    topic_title=topic.title,
                    lesson_md=(topic.lesson_md or "") + f"\n\n当前题目：{active.get('title', '')}\n题面：{active.get('statement', '')}\n学生当前代码：\n```\n{code[:2000]}\n```",
                    history=history,
                    user_question=question.strip(),
                )
            history.append({"role": "user", "text": question.strip()})
            history.append({"role": "ai", "text": answer})
            st.session_state[hist_key] = history
            st.session_state.pop(f"preask_input_{active_id}", None)
            st.rerun()


def _render_lesson_chat(lang: str, topic):
    """知识点讲解下方的随问随答。按 语言+专题 各自记历史，和题目追问互不干扰。"""
    hist_key = f"lesson_chat::{lang}::{topic.slug}"
    history = st.session_state.setdefault(hist_key, [])

    with st.expander("💬 读知识点有不懂的？随时问 AI 老师", expanded=False):
        if history:
            for msg in history:
                if msg["role"] == "user":
                    safe = html.escape(msg["text"])
                    st.markdown(
                        f'<div style="background:#EEF2FF;border-radius:10px;padding:10px 14px;margin:6px 0;">'
                        f'<b>🧑 你</b>　{safe}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div style="background:#FEF3C7;border-radius:10px 10px 0 0;padding:8px 14px 4px;margin:6px 0 0;">'
                        '<b>🤖 AI 老师</b></div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(msg["text"])

        question = st.text_area(
            "问 AI 老师关于这节知识点",
            key=f"lesson_q_{lang}_{topic.slug}",
            placeholder="例如：这里说的『向量化』到底是什么意思？为什么比 for 循环快？",
            height=80,
            label_visibility="collapsed",
        )
        ask_col, clear_col, _ = st.columns([1, 1, 3])
        with ask_col:
            ask_clicked = st.button("发送提问", key=f"lesson_ask_{lang}_{topic.slug}",
                                    type="primary", use_container_width=True)
        with clear_col:
            if st.button("清空", key=f"lesson_clear_{lang}_{topic.slug}", use_container_width=True):
                st.session_state[hist_key] = []
                st.rerun()

        if ask_clicked and question.strip():
            with st.spinner("AI 老师在想…（最长约 45 秒）"):
                answer = ask_lesson(
                    lang=lang,
                    topic_title=topic.title,
                    lesson_md=topic.lesson_md or "",
                    history=history,
                    user_question=question.strip(),
                )
            history.append({"role": "user", "text": question.strip()})
            history.append({"role": "ai", "text": answer})
            st.session_state[hist_key] = history
            st.session_state.pop(f"lesson_q_{lang}_{topic.slug}", None)
            st.rerun()
