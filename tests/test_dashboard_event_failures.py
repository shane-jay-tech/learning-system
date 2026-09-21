# -*- coding: utf-8 -*-
"""dashboard 推荐展示两处 except 的**运行时行为**桩（l922-101-dash-event-fail）。

为什么还要这一档：`tests/test_ergo_h912_13.py:40` 只做源码级计数
（`assert src.count("logger.debug(") >= 3`），它证明「不静默」四个字**写在源文件里**，
但 emit_event 抛错时推荐区到底还渲不渲染、shown/impressions 会话态会不会被污染、
exc_info 有没有真带上——一件都没钉。本文件用 FakeStreamlit + MagicMock DAO 注入抛错，
把 h912-13 修复③从「文本契约」升级为「行为契约」。

锚点（开工前复核，2026-09-22，两处行号均未漂移）：
  - `ui/pages/dashboard.py:129` logger.debug("dashboard: 推荐展示数据异常", exc_info=True)
  - `ui/pages/dashboard.py:154` logger.debug("dashboard: 推荐事件上报异常", exc_info=True)
  - `tests/test_ergo_h912_13.py:40` 源级断言（本文件不改动它，只补运行时面）
零改动 `ui/pages/dashboard.py`；不触真实 Streamlit、不连库、不联网。
复跑：python -m pytest tests/test_dashboard_event_failures.py -q

追加（l922-102-dash-click-nav，2026-09-22）：第四节 2 例，钉 :153 except 之后 :155
`navigate_to_problem` 仍在 try 外——上报失败不得让「去做 →」按钮变成死键。仍零改动源码。

追加（l922-103-dash-cross-except，2026-09-22）：第五节 3 例，覆盖跨路径推荐区（:273-323）。
现场复核推翻了任务书前提：:294 的 shown 上报**根本没有 try**（唯一的 except 在 :321，包的是点击上报），
故其中 2 例按现状钉（异常窜出函数＋整页后半段不渲染），等规划侧补 try 时由它们提醒改桩。仍零改动源码。
"""
import logging

import pytest

import ui.components as components
import ui.pages.dashboard as dashboard_page

import app  # noqa: F401  # 与 test_dashboard_page_render 同桩模式：app 侧 import 预绑定 st
from tests.test_dashboard_page_render import DashboardFakeStreamlit, _dao

SHOWN_MSG = "dashboard: 推荐展示数据异常"
CLICK_MSG = "dashboard: 推荐事件上报异常"
SHOWN_KEY = "_rec_shown_ids"
IMPR_KEY = "_rec_impressions"
LOGGER = "ui.pages.dashboard"
GO = "去做 →"


def _plan(n=5, lang="python"):
    return [{
        "lang": lang,
        "problem_id": f"{lang}/01_x/{i:02d}_p",
        "title": f"推荐题{i}号",
        "topic_slug": "01_x",
        "topic_title": "基础",
        "difficulty": 2,
        "reason_code": "mistake_first",
    } for i in range(1, n + 1)]


class _Emitter:
    """emit_event 替身。attempts = 每一次尝试（含抛错那次）；sent = 真正送达事件库的。
    两者之差就是「本地记了、事件库没有」的那批——本文件的主轴。"""

    def __init__(self, fail_on=(), boom="事件库写入失败"):
        self.fail_on = tuple(fail_on)
        self.boom = boom
        self.attempts = []
        self.sent = []

    def __call__(self, kind, **kw):
        self.attempts.append((kind, kw))
        if kind in self.fail_on:
            raise RuntimeError(self.boom)
        self.sent.append((kind, kw))

    def sent_of(self, kind):
        return [(k, kw) for k, kw in self.sent if k == kind]

    def kinds(self, box="attempts"):
        return [k for k, _kw in getattr(self, box)]


def _cards_rendered(fake, plan):
    md = " ".join(str(c[1][0]) for c in fake.calls if c[0] == "markdown")
    return [it["title"] for it in plan if it["title"] in md]


@pytest.fixture()
def fake_st(request):
    buttons = getattr(request, "param", None) or {}
    return DashboardFakeStreamlit(buttons=buttons)


@pytest.fixture()
def wire(monkeypatch, fake_st):
    """把渲染体需要的周边全打桩，只留 recommend 与 emit_event 给用例控制。"""
    monkeypatch.setattr(dashboard_page, "st", fake_st)
    monkeypatch.setattr(components, "st", fake_st)
    monkeypatch.setattr(dashboard_page, "check_achievements", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_progress_summary",
                        lambda dao: {"earned": 2, "total": 22})
    monkeypatch.setattr(dashboard_page, "get_all_with_state", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_achievement", lambda aid: {"name": f"成就{aid}"})
    monkeypatch.setattr(dashboard_page, "cross_recommend", lambda dao, **kw: [])
    import core.loader as _loader
    monkeypatch.setattr(_loader, "load_language", lambda lang: [])

    def run(plan, emitter):
        monkeypatch.setattr(dashboard_page, "recommend", lambda n=5, dao=None: plan)
        dao = _dao()
        dao.emit_event = emitter
        dashboard_page._render_dashboard_body(dao)
        return dao
    return run


# ---------------------------------------------------------------------------
# 一、展示侧（:129）：抛错不中断渲染，日志真带栈
# ---------------------------------------------------------------------------

def test_shown_event_failure_still_renders_all_five_cards(wire, fake_st):
    """emit_event 一上来就抛，五张推荐卡必须照常全部渲染。"""
    plan = _plan(5)
    em = _Emitter(fail_on=("recommendation_shown",))
    wire(plan, em)                                     # 异常没窜到调用方，本身就是断言
    assert _cards_rendered(fake_st, plan) == [it["title"] for it in plan], \
        "展示事件抛错把推荐区整块带走了"
    assert em.kinds() == ["recommendation_shown"]      # try 包整个 for：首条抛即出循环
    assert em.sent == []


def test_shown_event_failure_logs_debug_with_exc_info(wire, caplog):
    """钉「不静默」的行为面：日志真发出、级别 DEBUG、exc_info 真带（源级 count 断言给不了）。"""
    em = _Emitter(fail_on=("recommendation_shown",))
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        wire(_plan(3), em)
    hits = [r for r in caplog.records if r.getMessage() == SHOWN_MSG]
    assert len(hits) == 1, f"期望恰一条 {SHOWN_MSG}，实得 {len(hits)}"
    assert hits[0].levelno == logging.DEBUG
    assert hits[0].name == LOGGER
    assert hits[0].exc_info is not None and hits[0].exc_info[0] is RuntimeError
    assert "RuntimeError" in caplog.text               # 栈已渲染，不是只留一句话


# ---------------------------------------------------------------------------
# 二、会话态：add(shown) 与 impressions 都在 emit 之前 —— 失败条目曝光永久丢失
# ---------------------------------------------------------------------------

def test_local_state_is_written_before_emit_so_one_failure_loses_that_impression_forever(wire, fake_st):
    """钉 :118-127 写序：add(shown) → impressions[k]=… → emit_event，三件全在送达之前。

    于是「本地认为展示过」与「事件库收到 recommendation_shown」并不等价：emit 抛错时
    shown 与 impressions 都已经记了这条，下一次渲染 `if pid_key not in shown` 直接跳过 →
    该条曝光**永久补不回来**，本地口径与 DB 漏斗口径从此恒差 1。用「先坏后好」两次渲染钉死。
    """
    plan = _plan(3)

    bad = _Emitter(fail_on=("recommendation_shown",))
    wire(plan, bad)
    assert len(fake_st.session_state[SHOWN_KEY]) == 1                   # 炸的那条已进 shown
    assert len(fake_st.session_state[IMPR_KEY]) == 1                    # 也已进 impressions
    assert bad.kinds() == ["recommendation_shown"]                      # 试过 1 次
    assert bad.sent == []                                               # 事件库一条都没有

    good = _Emitter()                                                   # 故障恢复，再渲染一次
    fake_st.calls.clear()
    wire(plan, good)
    assert [kw["problem_id"] for _k, kw in good.sent_of("recommendation_shown")] == \
        [p["problem_id"] for p in plan[1:]], "恢复后应补第 2、3 条；第 1 条已被 shown 永久挡掉"
    assert len(fake_st.session_state[IMPR_KEY]) == 3                    # 本地记 3 条 …
    assert len(good.sent_of("recommendation_shown")) == 2               # … 事件库只到 2 条


def test_local_impression_state_and_emitted_events_match_when_nothing_fails(wire, fake_st):
    """对照组：全成功时 shown / impressions / 事件一一对应，
    证明上一条的「本地比事件库多 1」由失败注入造成，不是常态。"""
    plan = _plan(4)
    em = _Emitter()
    wire(plan, em)
    assert len(fake_st.session_state[SHOWN_KEY]) == 4
    assert len(fake_st.session_state[IMPR_KEY]) == 4
    shown_ev = em.sent_of("recommendation_shown")
    assert len(shown_ev) == 4
    assert [kw["payload"]["rank"] for _k, kw in shown_ev] == [1, 2, 3, 4]
    assert {kw["payload"]["surface"] for _k, kw in shown_ev} == {"dashboard"}
    assert [kw["problem_id"] for _k, kw in shown_ev] == [p["problem_id"] for p in plan]
    for rank, (_k, kw) in enumerate(shown_ev, 1):
        stored = fake_st.session_state[IMPR_KEY][(kw["lang"], kw["problem_id"], "dashboard")]
        assert stored["rank"] == rank
        assert stored["recommendation_id"] == kw["payload"]["recommendation_id"]


def test_failure_on_third_item_leaves_local_state_ahead_of_events_by_one(wire, fake_st):
    """第 3 次上报抛错：前 2 条完整入账，第 3 条「本地有、事件库没有」，
    第 4-5 条连试都没试（try 包整个 for，首抛即出循环），但五张卡全部渲染。
    任务书问的「shown/impressions 会不会被污染」——答案是两处同步污染，且与事件库差 1。"""
    plan = _plan(5)
    n = {"i": 0}

    def emit(kind, **kw):
        n["i"] += 1
        if n["i"] == 3:
            raise RuntimeError("第 3 条炸")

    wire(plan, emit)
    assert n["i"] == 3                                                   # 第 4、5 条没再试
    assert len(fake_st.session_state[SHOWN_KEY]) == 3
    assert len(fake_st.session_state[IMPR_KEY]) == 3                     # 与 shown 同步（不差在这）
    assert _cards_rendered(fake_st, plan) == [it["title"] for it in plan]


# ---------------------------------------------------------------------------
# 三、点击侧（:154）：上报炸了不能挡住跳转
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_click_event_failure_still_navigates_to_problem(wire, fake_st, caplog):
    """按钮按下后 recommendation_clicked 抛错：跳转照常发生，日志照常落 DEBUG 且带栈。"""
    plan = _plan(2)
    em = _Emitter(fail_on=("recommendation_clicked",))
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        wire(plan, em)

    hits = [r for r in caplog.records if r.getMessage() == CLICK_MSG]
    assert len(hits) == 2, f"两张卡各一条点击异常日志，实得 {len(hits)}"
    assert all(r.levelno == logging.DEBUG and r.exc_info is not None for r in hits)
    # 跳转没有被 except 吞掉：两张卡各导航一次（navigate_to_problem 真跑，未打桩）
    assert fake_st.rerun_count == 2
    assert fake_st.session_state.route == "language"
    assert fake_st.session_state.selected_lang == "python"
    assert fake_st.session_state.selection["problem_id"] == plan[-1]["problem_id"]
    # 展示侧未被牵连：两处 except 各自独立
    assert em.kinds() == ["recommendation_shown", "recommendation_shown",
                          "recommendation_clicked", "recommendation_clicked"]
    assert len(em.sent_of("recommendation_shown")) == 2
    assert em.sent_of("recommendation_clicked") == []


@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_click_report_reuses_the_impression_id_written_at_shown_time(wire, fake_st):
    """点击上报的 recommendation_id / rank 取自展示时写入的 impressions。
    钉住这条归因链——展示侧一旦漏发事件，点击侧仍会带着「本该有曝光」的 id 上报。"""
    plan = _plan(1)
    em = _Emitter()
    wire(plan, em)
    shown_id = em.sent_of("recommendation_shown")[0][1]["payload"]["recommendation_id"]
    _k, click = em.sent_of("recommendation_clicked")[0]
    assert click["payload"]["recommendation_id"] == shown_id
    assert click["payload"]["surface"] == "dashboard"
    assert click["payload"]["rank"] == 1


@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_shown_side_failure_yields_clicked_events_with_no_matching_shown_event(wire, fake_st, caplog):
    """跨站点后果（本单最有价值的一条）：展示侧第 1 条就炸 → shown/impressions 只记第 1 条，
    但卡片仍渲染 2 张、按钮仍可点 → 第 2 张卡的 recommendation_clicked 在 impressions 里查不到，
    recommendation_id 退化成空串。事件库最终 shown=0 / clicked=2 ——
    漏斗表出现 clicked > shown 就是这么产生的。钉现状，不改（结论写进 result 遗留问题）。
    """
    plan = _plan(2)
    em = _Emitter(fail_on=("recommendation_shown",))
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        wire(plan, em)

    assert em.kinds() == ["recommendation_shown",            # 第 1 条：抛错
                          "recommendation_clicked",          # 第 1 张卡被点（id 有）
                          "recommendation_clicked"]          # 第 2 张卡被点（id 空）
    assert em.sent_of("recommendation_shown") == []
    clicks = em.sent_of("recommendation_clicked")
    assert len(clicks) == 2
    assert clicks[0][1]["payload"]["recommendation_id"] == \
        fake_st.session_state[IMPR_KEY][(plan[0]["lang"], plan[0]["problem_id"], "dashboard")]["recommendation_id"]
    assert clicks[1][1]["payload"]["recommendation_id"] == ""          # 空串兜底，归因链断在这里
    assert clicks[1][1]["payload"]["rank"] == 0                        # imp.get("rank", 0)
    assert clicks[1][1]["problem_id"] == plan[1]["problem_id"]         # 事件库里它从未 shown 过
    assert [r.getMessage() for r in caplog.records if r.name == LOGGER] == [SHOWN_MSG]


# ---------------------------------------------------------------------------
# 四、l922-102：点击上报炸了之后，:155 的 navigate 仍在 try 外——「断网也能跳」
#     回归把 navigate_to_problem 挪进 try（或挪到 emit 之前），本节两例立刻转红。
#     与上一节的分工：那里用 rerun_count 侧面看「跳了」，这里直接数 navigate 的调用次数与实参。
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_click_emit_failure_leaves_navigate_called_exactly_once(wire, fake_st, monkeypatch):
    """:142-155 单卡：recommendation_clicked 抛错 → navigate 调用次数 ==1，且 route 真切换。

    这条顺序（emit 在 try 内、navigate 在 try 外）此前无测试保护：
    一旦有人「顺手」把 navigate 收进 try 想统一兜异常，断网/事件库写失败时点「去做 →」
    就会变成按钮没反应，而页面渲染测试全绿——只有这里会红。
    """
    plan = _plan(1)
    em = _Emitter(fail_on=("recommendation_clicked",))
    real_navigate = components.navigate_to_problem
    nav_calls = []

    def spy(lang, topic_slug, problem_id):
        nav_calls.append((lang, topic_slug, problem_id))
        return real_navigate(lang, topic_slug, problem_id)

    monkeypatch.setattr(dashboard_page, "navigate_to_problem", spy)
    wire(plan, em)                                                     # 异常没窜出来＝except 生效

    assert nav_calls == [(plan[0]["lang"], plan[0]["topic_slug"], plan[0]["problem_id"])], \
        "上报失败后 navigate 必须仍被调用恰一次、且带完整路由三参数"
    assert fake_st.session_state.route == "language"
    assert fake_st.session_state.selected_lang == "python"
    assert fake_st.session_state.selection == {
        "lang": "python", "topic_slug": "01_x", "problem_id": plan[0]["problem_id"]}
    assert em.kinds("attempts") == ["recommendation_shown", "recommendation_clicked"]
    assert em.sent_of("recommendation_clicked") == []                   # 事件确实没送达


@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_navigate_runs_after_the_failed_emit_not_instead_of_it(wire, fake_st, monkeypatch):
    """:145-155 顺序桩：navigate 发生时，clicked 上报已经**尝试过**一次（emit 尝试计数 ==1）。

    钉的是「先试上报、炸了照样跳」这条时序，而不是「跳了就算对」：
    若实现改成 emit 在 navigate 之后，跳转触发的 rerun 会把上报整条丢掉，本例即红。
    """
    plan = _plan(1)
    em = _Emitter(fail_on=("recommendation_clicked",))
    attempts_at_nav = []

    def spy(lang, topic_slug, problem_id):
        attempts_at_nav.append(len(em.attempts))
        # 故意不打真 navigate：本例只关心调用点先后，路由断言在上一条已钉死

    monkeypatch.setattr(dashboard_page, "navigate_to_problem", spy)
    wire(plan, em)

    assert attempts_at_nav == [2]                                       # shown(1) + clicked(1) 都发生在跳转前
    assert em.kinds("attempts")[-1] == "recommendation_clicked"
    assert len(em.sent_of("recommendation_clicked")) == 0               # 尝试了、但一条没送到


# ---------------------------------------------------------------------------
# 五、l922-103：跨路径推荐区（:273-323）的两条 except 面
#     现场复核结论（写桩前先看磁盘）：任务书以为「_render_cross_recommend 的 shown 事件
#     上报失败路径有 except、缺的是行为测试」——**不成立**。:294 那次 emit_event 完全不在
#     try 里（:286-296 整个 for 体没有异常处理），函数里唯一的 except 在 :321，包的是
#     **点击**上报（:311-320），日志文案却写成「跨路径推荐展示异常」。
#     于是本节分两类钉：例 A 是真正的 except 行为面（可点、能跳、带栈）；
#     例 B/C 是**现状桩**——shown 抛错会窜出函数、把整页后半段一起带走。
#     规划侧若给 :294 补 try（本就该补），B/C 会转红：那是有意的提醒，改桩与改码请同一批做。
# ---------------------------------------------------------------------------

CROSS_MSG = "dashboard: 跨路径推荐展示异常"
CROSS_SHOWN_KEY = "_cross_rec_shown_ids"


def _cross(n=2, lang="sql"):
    return [{
        "lang": lang,
        "problem_id": f"{lang}/02_y/{i:02d}_q",
        "title": f"跨路径题{i}号",
        "topic_slug": "02_y",
        "topic_title": "进阶",
        "difficulty": 3,
        "cross_reason": "互补内容",
    } for i in range(1, n + 1)]


def _cross_setup(monkeypatch, items, emitter):
    """把跨路径区单独拎出来跑：wire 夹具默认把 cross_recommend 打桩成 []，这里覆盖它。"""
    monkeypatch.setattr(dashboard_page, "cross_recommend", lambda dao=None, **kw: items)
    dao = _dao()
    dao.emit_event = emitter
    return dao


@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_cross_click_failure_still_renders_records_navigates_and_logs(wire, monkeypatch, fake_st, caplog):
    """唯一真 except（:321）：clicked 上报炸了，卡片/记账/跳转三件都不能少。

    补的是 `test_dashboard_page_render.py:105` 只测正常流留下的洞：注入抛错后
    曝光记账（shown 侧）与导航必须各自独立，日志级别 DEBUG 且真带栈。
    """
    items = _cross(2)
    em = _Emitter(fail_on=("recommendation_clicked",))
    dao = _cross_setup(monkeypatch, items, em)
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        dashboard_page._render_cross_recommend(dao)

    # 展示侧未被牵连：两条 recommendation_shown 正常送达
    assert len(em.sent_of("recommendation_shown")) == 2
    assert [kw["payload"]["surface"] for _k, kw in em.sent_of("recommendation_shown")] == \
        ["cross_path", "cross_path"]
    # 卡片照常渲染、去重集合照常记账
    assert _cards_rendered(fake_st, items) == [it["title"] for it in items]
    assert fake_st.session_state[CROSS_SHOWN_KEY] == {(it["lang"], it["problem_id"]) for it in items}
    assert len(fake_st.session_state[IMPR_KEY]) == 2
    # 按钮仍可点：navigate 真跑（未被打桩），最后一次落在第二张卡
    assert fake_st.rerun_count == 2
    assert fake_st.session_state.route == "language"
    assert fake_st.session_state.selected_lang == "sql"
    assert fake_st.session_state.selection["problem_id"] == items[-1]["problem_id"]
    # 日志面：一张卡一条、DEBUG、带栈；文案「展示异常」其实记的是点击上报炸了（见本节抬头）
    hits = [r for r in caplog.records if r.getMessage() == CROSS_MSG]
    assert len(hits) == 2, f"期望恰两条 {CROSS_MSG}，实得 {len(hits)}"
    assert all(r.levelno == logging.DEBUG and r.exc_info is not None
               and r.exc_info[0] is RuntimeError for r in hits)
    assert em.sent_of("recommendation_clicked") == []


def test_cross_shown_event_failure_escapes_the_function_entirely(wire, monkeypatch, fake_st):
    """现状桩：:294 的 shown emit 没有 try 包——抛错直接窜出 `_render_cross_recommend`。

    与 dashboard 推荐区（:115-129 有 try）不同，这里连「丢一条曝光」都算不上：
    shown 记账已经写了（add 在 emit 之前，同一类写序问题），卡片却一张没渲。
    """
    items = _cross(2)
    em = _Emitter(fail_on=("recommendation_shown",))
    dao = _cross_setup(monkeypatch, items, em)
    with pytest.raises(RuntimeError, match="事件库写入失败"):
        dashboard_page._render_cross_recommend(dao)

    assert em.kinds() == ["recommendation_shown"]                       # 第 1 条就炸，第 2 条没再试
    assert fake_st.session_state[CROSS_SHOWN_KEY] == {(items[0]["lang"], items[0]["problem_id"])}
    assert list(fake_st.session_state[IMPR_KEY]) == \
        [(items[0]["lang"], items[0]["problem_id"], "cross_path")]      # 本地记了、事件库没有
    md = " ".join(str(c[1][0]) for c in fake_st.calls if c[0] == "markdown")
    assert all(it["title"] not in md for it in items), "抛错在渲染循环之前，跨路径卡应一张都没出"


@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_cross_shown_event_failure_takes_down_every_section_below_it(wire, monkeypatch, fake_st):
    """整页爆炸半径：`_render_cross_recommend` 在 :157 被直调（render 体只 try/finally 不 catch），
    所以它一抛，下面成就/热力图/报告导出/学习数据（导出按钮＋导入器）/最近活动**全部不渲染**。

    这条是本节最该让规划侧看见的：跨路径区一次事件库写入失败＝用户整页后半段空白。
    """
    items = _cross(1)
    em = _Emitter(fail_on=("recommendation_shown",))
    monkeypatch.setattr(dashboard_page, "cross_recommend", lambda dao=None, **kw: items)
    with pytest.raises(RuntimeError):
        wire([], em)                                                    # 今日推荐留空，只让跨路径区炸

    joined = " ".join(str(a[0]) for c in fake_st.calls for a in [c[1]] if a)
    assert "总览" in joined, "上半段确实渲染过（证明是中途断的，不是没跑）"
    for missing in ("🏅 成就徽章", "📅 学习热力图", "📄 学习报告导出", "📦 学习数据", "最近活动"):
        assert missing not in joined, f"{missing} 区被跨路径区的未捕获异常带走了"
    assert not any(c[0] == "download_button" for c in fake_st.calls), "导出/下载按钮全没机会渲染"
    assert not any(c[0] == "file_uploader" for c in fake_st.calls), "导入器也没机会渲染（导入功能整段消失）"
