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

追加（l923-07，2026-09-23）：上面那句"提醒"兑现——`ui/pages/dashboard.py` 跨路径记账循环补
per-item try ＋ 点击侧文案订正为「跨路径推荐点击上报异常」；第五节例 B/例 C 随之改为**修好版**
断言（不再故意红），例 A 的日志文案常量换成新增的 CROSS_CLICK_MSG。
本单**未**动写序（本地先记账、emit 在后）⇒ "失败一条曝光永久丢失"仍在，由例 B 的第 ④ 条断言
继续钉着；解它要走 A2 方案，见 docs/insights/learn-shown-writeorder-design-20260923.md。

追加（l923-08，2026-09-23）：第六节 3 例，把失败注入打在**第三条上报路径的点击侧**
（`dao.emit_event("recommendation_clicked", …)`，现值 `ui/pages/dashboard.py:387`；except 在 :394、
`navigate_to_problem` 在 :398）。l922-101 遗留问题 3 说"这条路径本次未注入失败"，l922-103 已把它
的主面（全条失败 → 渲染/记账/跳转三件不丢）钉成例 A；本节补的是例 A 覆盖不到的三格：
归因链正向面、**部分失败**（第 2 条炸不连坐第 1 条）、以及 impressions 查不到时写空
`recommendation_id`/`rank=0` 的脏事件。仍零改动源码。

追加（l924-01，2026-09-24）：**生产码改了**——`ui/pages/dashboard.py` 今日推荐曝光区的
`try:` 从"包整个 for"下沉为循环体内 per-item try，与 `_render_cross_recommend` 同型
（l923-07 遗留问题 2 交的主班选项）。于是一批断言随之改桩：第一节例 1/例 2、第二节例 3/例 4、
第三节例 6 共 **5 例** 实测转红（l923-07 按当时盘面点名 3 例，那三个行号已随文件增长漂移；
批级形态不止钉在它点名的那几处，本文件只用符号常量定位）。核心变化：一条 emit 失败不再把
本帧后续条踢出循环，"试过几条"从"首抛为止"变成"全量"；而写序 add→impressions→emit 未动
（A2 裁决域），失败那条仍本地有账、事件库永无。
新增第七节 3 例钉拉齐后的规格：坏一项只掉一项（计数面＋渲染面）＋两区同一注入下的形态对照。
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


class _NthBoomer(_Emitter):
    """只让**第 n 次** `kind` 调用抛错（n 可为整数或整数集合），其余照常送达（l924-01 新增）。

    批级 try 时代"首抛即出循环"，选择性注入没有意义；下沉为 per-item 后要钉的恰恰是
    "坏一项只掉一项"⇒ 必须能只弄坏中间那一条（`n` 给 int 或 int 集合皆可）。
    沿用 `_Emitter` 的 attempts/sent 两面记账。
    """

    def __init__(self, n, kind="recommendation_shown", boom="第 N 条上报炸"):
        super().__init__(fail_on=(), boom=boom)
        self.n = n
        self.kind = kind

    def __call__(self, kind, **kw):
        self.attempts.append((kind, kw))
        bad = {self.n} if isinstance(self.n, int) else set(self.n)
        if kind == self.kind and sum(1 for k, _ in self.attempts if k == kind) in bad:
            raise RuntimeError(self.boom)
        self.sent.append((kind, kw))


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
# 一、展示侧：抛错不中断渲染，日志真带栈
#     🔴 l924-01：try 已从"包整个 for"下沉为循环体内 per-item ⇒ 本节的"试过几条"全部改写。
# ---------------------------------------------------------------------------

def test_shown_event_failure_still_renders_all_five_cards(wire, fake_st):
    """emit_event 一上来就抛，五张推荐卡必须照常全部渲染。"""
    plan = _plan(5)
    em = _Emitter(fail_on=("recommendation_shown",))
    wire(plan, em)                                     # 异常没窜到调用方，本身就是断言
    assert _cards_rendered(fake_st, plan) == [it["title"] for it in plan], \
        "展示事件抛错把推荐区整块带走了"
    # l924-01 前：`== ["recommendation_shown"]`，注释写"try 包整个 for：首条抛即出循环"。
    # 下沉后首条抛错不再踢出循环 ⇒ 五条各试一次（连带半径归零），但一条也没送达。
    assert em.kinds() == ["recommendation_shown"] * 5, \
        "per-item 之后坏一条不该再吃掉本帧后续四条的尝试机会"
    assert em.sent == []


def test_shown_event_failure_logs_debug_with_exc_info(wire, caplog):
    """钉「不静默」的行为面：日志真发出、级别 DEBUG、exc_info 真带（源级 count 断言给不了）。

    l924-01 改桩：批级 try 时代 3 条只试 1 条 ⇒ 恰 1 条日志；per-item 后 3 条全试全炸 ⇒
    **每条失败各记一条**。这正是要的语义（不计数、不汇总提示，掉哪条报哪条）。
    """
    em = _Emitter(fail_on=("recommendation_shown",))
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        wire(_plan(3), em)
    hits = [r for r in caplog.records if r.getMessage() == SHOWN_MSG]
    assert len(hits) == 3, f"期望恰三条 {SHOWN_MSG}（每条失败一项一记），实得 {len(hits)}"
    assert all(r.levelno == logging.DEBUG for r in hits)
    assert all(r.name == LOGGER for r in hits)
    assert all(r.exc_info is not None and r.exc_info[0] is RuntimeError for r in hits)
    assert "RuntimeError" in caplog.text               # 栈已渲染，不是只留一句话


# ---------------------------------------------------------------------------
# 二、会话态：add(shown) 与 impressions 都在 emit 之前 —— 失败条目曝光永久丢失
# ---------------------------------------------------------------------------

def test_local_state_is_written_before_emit_so_one_failure_loses_that_impression_forever(wire, fake_st):
    """钉写序：add(shown) → impressions[k]=… → emit_event，三件全在**送达之前**。

    于是「本地认为展示过」与「事件库收到 recommendation_shown」并不等价：emit 抛错时
    shown 与 impressions 都已经记了这条，下一次渲染 `if pid_key not in shown` 直接跳过 →
    该条曝光**永久补不回来**，本地口径与 DB 漏斗口径从此恒差 1。用「先坏后好」两次渲染钉死。

    🔴 l924-01 改桩：注入由"首条就炸"换成"第 2 条炸"。批级 try 下第 3 条压根不会被试，
    本例当时的差额 1 混着两种成因（emit 失败 + 被批级 try 提前踢出循环）；per-item 下
    第 1、3 条正常送达 ⇒ 剩下的那条差额**只可能**来自写序 ⇒ 本例从今往后只钉写序这一件事。
    """
    plan = _plan(3)

    bad = _NthBoomer(2, boom="第 2 条曝光上报炸")
    wire(plan, bad)
    assert len(fake_st.session_state[SHOWN_KEY]) == 3                  # 三条全进 shown（含炸的第 2 条）
    assert len(fake_st.session_state[IMPR_KEY]) == 3                   # 也已全进 impressions
    assert bad.kinds() == ["recommendation_shown"] * 3                 # 试过 3 次（坏项不连坐）
    assert [kw["problem_id"] for _k, kw in bad.sent] == \
        [plan[0]["problem_id"], plan[2]["problem_id"]]                 # 事件库到的正是另两条

    good = _Emitter()                                                  # 故障恢复，再渲染一次
    fake_st.calls.clear()
    wire(plan, good)
    assert good.sent_of("recommendation_shown") == [], \
        "炸那条已被 shown 门控永久挡掉 ⇒ 恢复后一条也补不回来（写序未动的直接后果，A2 才修）"
    assert len(fake_st.session_state[IMPR_KEY]) == 3                   # 本地记 3 条 …
    assert len(bad.sent_of("recommendation_shown")) == 2               # … 事件库只到 2 条


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
    """第 3 次上报抛错：本地五账全记、事件库到 4 条 ⇒ 差的恰好只有坏的那一条。

    任务书问的「shown/impressions 会不会被污染」——答案不变：两处同步污染、与事件库差 1。
    🔴 l924-01 变的是第 4、5 条：批级 try 时代它们连试都没试（旧断言 `n["i"] == 3`、
    旧注释"try 包整个 for，首抛即出循环"），per-item 之后各试一次并全部送达
    ⇒ 本帧未试条数由 2 归零，掉的只剩第 3 条本身。
    """
    plan = _plan(5)
    em = _NthBoomer(3, boom="第 3 条炸")

    wire(plan, em)
    assert em.kinds() == ["recommendation_shown"] * 5                  # 第 4、5 条现在也试了
    assert len(fake_st.session_state[SHOWN_KEY]) == 5
    assert len(fake_st.session_state[IMPR_KEY]) == 5                     # 与 shown 同步（不差在这）
    assert [kw["problem_id"] for _k, kw in em.sent] == \
        [p["problem_id"] for i, p in enumerate(plan) if i != 2]          # 事件库恰少第 3 条
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
    """跨站点后果：展示侧两条全炸 ⇒ 卡片仍渲染、按钮仍可点，事件库 shown=0 / clicked=2。

    漏斗表出现 `clicked > shown` 就是这么产生的。🔴 l924-01 改桩（脏的**形态**变了，脏的
    **事实**没变）：批级 try 时代第 2 条从没被记过 ⇒ 第 2 张卡的 clicked 只能写空
    `recommendation_id`/`rank=0`；per-item 之后两条都记了本地账 ⇒ 两条 clicked 各带一个
    **事件库里永不存在的 rid**（悬空归因）。跨路径侧的空串回退分支没被本单抹掉，
    仍由第六节 l923-08 例 3/例 4（预填 shown 集合构造）钉着。
    """
    plan = _plan(2)
    em = _Emitter(fail_on=("recommendation_shown",))
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        wire(plan, em)

    assert em.kinds() == ["recommendation_shown",            # 第 1 条：抛错
                          "recommendation_shown",            # 第 2 条：也抛错（不再被前者带走）
                          "recommendation_clicked",          # 第 1 张卡被点
                          "recommendation_clicked"]          # 第 2 张卡被点
    assert em.sent_of("recommendation_shown") == []
    clicks = em.sent_of("recommendation_clicked")
    assert len(clicks) == 2
    for idx, it in enumerate(plan):
        local = fake_st.session_state[IMPR_KEY][(it["lang"], it["problem_id"], "dashboard")]
        assert clicks[idx][1]["payload"]["recommendation_id"] == local["recommendation_id"]
        assert clicks[idx][1]["payload"]["rank"] == idx + 1                  # 本地账在、归因照带
        assert clicks[idx][1]["problem_id"] == it["problem_id"]              # 事件库里它从未 shown 过
    assert [r.getMessage() for r in caplog.records if r.name == LOGGER] == [SHOWN_MSG, SHOWN_MSG]


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
# 五、l922-103：跨路径推荐区的两条 except 面
#     l922-103 现场复核结论（当时）：任务书以为「shown 事件上报失败路径有 except、缺的是行为
#     测试」——**不成立**。那次 emit_event 完全不在 try 里（整个 for 体没有异常处理），函数里
#     唯一的 except 包的是**点击**上报，日志文案却写成「跨路径推荐展示异常」。
#     于是本节分两类钉：例 A 是真 except 行为面；例 B/C 是**现状桩**（shown 抛错窜出函数、
#     把整页后半段一起带走），并留话「规划侧补 try 时由它们提醒改桩」。
# 🔴 l923-07（2026-09-23）兑现了那句提醒：给跨路径记账循环补上 per-item try ＋ 把点击侧文案
#     订正为「跨路径推荐点击上报异常」。行号按 l922-103 落桩时的盘面书写（:273-323/:286-296/
#     :294/:321），现值已漂移到 :349-367/:357/:385 一带——本文件只用符号常量，不锁这些行号。
#     例 B/C 已从「故意钉坏」改成「修好版」；写序（本地先记账、emit 在后）**本单未动**，
#     所以"失败那条曝光永久丢失"仍然存在，解它要走 A2 方案：
#     见 docs/insights/learn-shown-writeorder-design-20260923.md（本文件例 B 的第 ④ 条断言）。
# ---------------------------------------------------------------------------

CROSS_MSG = "dashboard: 跨路径推荐展示异常"          # l923-07 起：展示侧专用（新 except 真在用）
CROSS_CLICK_MSG = "dashboard: 跨路径推荐点击上报异常"  # l923-07 名实订正后的点击侧文案
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
    """点击侧 except（l923-07 起文案为「跨路径推荐点击上报异常」）：clicked 上报炸了，
    卡片/记账/跳转三件都不能少。

    补的是 `test_dashboard_page_render.py:105` 只测正常流留下的洞：注入抛错后
    曝光记账（shown 侧）与导航必须各自独立，日志级别 DEBUG 且真带栈。
    l922-103 落桩时本区只有这一个 except（文案还错写成「展示异常」）；l923-07 补上展示侧
    per-item try 后，本例的"展示侧未被牵连"才第一次有了真正的对照物。
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
    # 日志面：一张卡一条、DEBUG、带栈；l923-07 起文案与站点名实相符（点击侧）
    hits = [r for r in caplog.records if r.getMessage() == CROSS_CLICK_MSG]
    assert len(hits) == 2, f"期望恰两条 {CROSS_CLICK_MSG}，实得 {len(hits)}"
    assert all(r.levelno == logging.DEBUG and r.exc_info is not None
               and r.exc_info[0] is RuntimeError for r in hits)
    assert em.sent_of("recommendation_clicked") == []
    # 反向钉文案订正：点击失败不该再冒「展示异常」这条误导文案
    assert [r for r in caplog.records if r.getMessage() == CROSS_MSG] == []


def test_cross_shown_event_failure_is_contained_per_item(wire, monkeypatch, fake_st, caplog):
    """🔴 l923-07 修好版（原例名 `test_cross_shown_event_failure_escapes_the_function_entirely`，
    那是一条故意钉坏的现状桩：shown 抛错直接窜出 `_render_cross_recommend`）。

    改造依据：l923-07 给跨路径记账循环补了 per-item try（`ui/pages/dashboard.py` 现值
    :349-367），与 dashboard 区 :169-183 同型。本例现在钉四件事：
      ① 异常不外窜（函数正常返回）；
      ② 连带半径归零——首条炸了，第 2、3 条仍各上报一次并送达事件库；
      ③ 展示侧日志真发出：DEBUG、带栈、文案「跨路径推荐展示异常」（本区现在配得上这句话）；
      ④ 写序未动（add → impressions → emit 仍在送达之前）⇒ 失败那条**照样永久丢失**、
         本地比事件库多 1。这一格要等 A2 方案才会归零，见
         `docs/insights/learn-shown-writeorder-design-20260923.md`；本断言就是留给那单的靶子。
    """
    items = _cross(3)
    calls, sent = [], []

    def emit_first_only_fails(kind, **kw):
        calls.append(kind)
        if kind == "recommendation_shown" and calls.count("recommendation_shown") == 1:
            raise RuntimeError("首条曝光上报炸")
        sent.append((kind, kw))

    dao = _cross_setup(monkeypatch, items, emit_first_only_fails)
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        dashboard_page._render_cross_recommend(dao)          # 不再 pytest.raises＝断言 ①

    assert calls == ["recommendation_shown"] * 3                              # 断言 ②
    assert [kw["problem_id"] for _k, kw in sent] == [it["problem_id"] for it in items[1:]]
    assert [kw["payload"]["surface"] for _k, kw in sent] == ["cross_path"] * 2
    assert fake_st.session_state[CROSS_SHOWN_KEY] == {(it["lang"], it["problem_id"]) for it in items}
    assert len(fake_st.session_state[IMPR_KEY]) == 3                           # 断言 ④：本地照旧记 3
    assert len(sent) == 2, "写序未动 ⇒ 失败那条本地有账、库里永无（悬空账，A2 才修）"
    assert _cards_rendered(fake_st, items) == [it["title"] for it in items]    # 卡片全渲
    hits = [r for r in caplog.records if r.getMessage() == CROSS_MSG]          # 断言 ③
    assert len(hits) == 1, f"只有失败那条该记展示异常，实得 {len(hits)}"
    assert hits[0].levelno == logging.DEBUG and hits[0].exc_info[0] is RuntimeError


@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_cross_shown_event_failure_no_longer_takes_down_the_sections_below(wire, monkeypatch, fake_st):
    """🔴 l923-07 修好版（原例名 `..._takes_down_every_section_below_it`，现状桩）。

    原来这条是本节最该让规划侧看见的：`_render_cross_recommend` 在 :211 被直调、
    而 `render_dashboard`（:94-97）只 try/finally 不 catch ⇒ 跨路径区一次事件库写入失败＝
    整页后半段（成就/热力图/报告导出/学习数据/最近活动）空白。
    补了 per-item try 之后：异常收在单条循环体内，后半段必须**全部照常渲染**。
    """
    items = _cross(1)
    em = _Emitter(fail_on=("recommendation_shown",))
    monkeypatch.setattr(dashboard_page, "cross_recommend", lambda dao=None, **kw: items)
    wire([], em)                                              # 不抛＝断言：整页跑完了

    joined = " ".join(str(a[0]) for c in fake_st.calls for a in [c[1]] if a)
    assert "总览" in joined, "上半段照常渲染"
    for want in ("🏅 成就徽章", "📅 学习热力图", "📄 学习报告导出", "📦 学习数据", "最近活动"):
        assert want in joined, f"{want} 区不该再被跨路径区的单条失败带走"
    assert any(c[0] == "download_button" for c in fake_st.calls), "导出/下载按钮须仍在"
    assert any(c[0] == "file_uploader" for c in fake_st.calls), "导入器须仍在（导入功能不再整段消失）"
    # 残余脏面（写序未动的直接后果，A2 才修）：曝光没送达，但卡片仍可点、
    # 点击带得上一个事件库里永不存在的 recommendation_id —— 悬空归因，见例 B 第 ④ 条。
    assert em.kinds() == ["recommendation_shown", "recommendation_clicked"]
    assert em.sent_of("recommendation_shown") == []
    clicks = em.sent_of("recommendation_clicked")
    assert len(clicks) == 1 and clicks[0][1]["payload"]["recommendation_id"]


# ---------------------------------------------------------------------------
# 六、l923-08：第三条上报路径**点击侧**的失败注入补面
#     站点现值（本文件只用符号常量，不锁行号）：
#       emit  `ui/pages/dashboard.py:387`  dao.emit_event("recommendation_clicked", …, surface="cross_path")
#       except :394  logger.debug("dashboard: 跨路径推荐点击上报异常", exc_info=True)
#       跳转   :398  navigate_to_problem(...)  ← 在 try 之外
#     为什么还要加例（l922-103 例 A 已注入过 clicked 失败，但它是 fail-all 型）：
#       1) 归因链正向面（clicked 的 recommendation_id/rank 是不是展示时写进 impressions 的那一份）
#          在 dashboard 侧有 `test_click_report_reuses_the_impression_id_written_at_shown_time`，
#          跨路径侧此前**只有**例 C 那句"非空"顺手扫过，没有逐字段对齐；
#       2) 部分失败面：例 A 两条全炸 ⇒ 看不见"第 2 条炸会不会连坐第 1 条的送达"；
#       3) 空归因面：`imp.get("recommendation_id", "")` / `imp.get("rank", 0)` 的回退分支
#          此前零覆盖（dashboard 侧由 l922-101 钉过，跨路径侧没有对应例）。
#     🔴 现状与 l922-101 遗留问题 1 同型（写序 add→impressions→emit 未动），解法属
#        l923-06 的设计稿裁决：docs/insights/learn-shown-writeorder-design-20260923.md（A2 方案）。
#        例 3/例 4 钉的"空 recommendation_id 进事件库"在 l923-07 之后**单次渲染内构造不出来**
#        （per-item try 保证 impressions 先写），但 A2 一旦落地就会变成常态路径 ⇒ 这两例是留给
#        那单的靶子，不是可删的样板断言。
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_cross_click_report_reuses_the_impression_written_at_shown_time(wire, monkeypatch, fake_st):
    """跨路径侧的归因链对照例（l922-101 同名例的跨路径孪生）：无故障时 clicked 的
    recommendation_id / rank / surface 必须逐字段等于展示时写进 `_rec_impressions` 的那一份。

    这条是"上报口径没串号"的正向契约：一旦有人把 impressions 的键从
    (lang, pid, "cross_path") 改成不带 surface 的形态，dashboard 与 cross 两条路径就会互相
    覆盖归因，而本例会当场红。
    """
    items = _cross(2)
    em = _Emitter()
    dao = _cross_setup(monkeypatch, items, em)

    dashboard_page._render_cross_recommend(dao)          # 不外窜＝渲染完成

    assert em.kinds() == ["recommendation_shown"] * 2 + ["recommendation_clicked"] * 2
    shown = em.sent_of("recommendation_shown")
    clicks = em.sent_of("recommendation_clicked")
    impr = fake_st.session_state[IMPR_KEY]
    for idx, it in enumerate(items):
        c_pay = clicks[idx][1]["payload"]
        s_pay = shown[idx][1]["payload"]
        local = impr[(it["lang"], it["problem_id"], "cross_path")]
        assert c_pay["recommendation_id"] == s_pay["recommendation_id"] == local["recommendation_id"]
        assert c_pay["rank"] == s_pay["rank"] == local["rank"] == idx + 1
        assert c_pay["surface"] == c_pay["reason_code"] == "cross_path"
        assert clicks[idx][1]["lang"] == it["lang"] and clicks[idx][1]["problem_id"] == it["problem_id"]
    assert len(em.sent_of("recommendation_clicked")) == 2


@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_second_cross_click_failure_does_not_take_down_the_first_click_report(
        wire, monkeypatch, fake_st, caplog):
    """部分失败面：只有**第 2 条** clicked 抛 RuntimeError ⇒ 第 1 条照样送达、两条照样跳转。

    这是例 A（fail-all 型）看不见的一格：跨路径点击的 try 收在单条 `if st.button` 体内
    （dashboard 区点击侧同型；其曝光记账侧自 l924-01 起也已是 per-item ⇒ 本文件涉及的
    四个上报面两区齐平、再无批级 try 残留），所以连带半径必须是零。
    断言 ①：渲染完成、两张卡全在；②：第 1 条 clicked 落库且归因正确；③：失败那条按钮
    仍完成跳转（rerun 2 次、selection 落在第 2 张卡）；④：日志恰 1 条点击侧文案、
    DEBUG 带栈，且不误报"展示异常"；⑤：本地比事件库多 1 条 clicked（悬空账，A2 才归零）。
    """
    items = _cross(2)
    calls, sent = [], []

    def emit(kind, **kw):
        calls.append(kind)
        if kind == "recommendation_clicked" and calls.count("recommendation_clicked") == 2:
            raise RuntimeError("第 2 条点击上报炸")
        sent.append((kind, kw))

    dao = _cross_setup(monkeypatch, items, emit)
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        dashboard_page._render_cross_recommend(dao)      # 不外窜＝异常收在单条体内

    assert calls == ["recommendation_shown"] * 2 + ["recommendation_clicked"] * 2
    # 展示侧零连坐
    assert [(k, kw["problem_id"]) for k, kw in sent if k == "recommendation_shown"] == \
        [("recommendation_shown", it["problem_id"]) for it in items]
    # 第 1 条 clicked 完整送达、归因取展示时那份
    landed = [kw for k, kw in sent if k == "recommendation_clicked"]
    assert len(landed) == 1, "第 2 条失败不该把第 1 条一起吞掉"
    assert landed[0]["problem_id"] == items[0]["problem_id"]
    assert landed[0]["payload"]["recommendation_id"] == \
        fake_st.session_state[IMPR_KEY][(items[0]["lang"], items[0]["problem_id"], "cross_path")]["recommendation_id"]
    assert len(fake_st.session_state[IMPR_KEY]) == 2, "本地记 2 / 事件库到 1 ⇒ 差 1 条悬空账"
    # 失败那条不是死键
    assert fake_st.rerun_count == 2
    assert fake_st.session_state.selection["problem_id"] == items[1]["problem_id"]
    assert _cards_rendered(fake_st, items) == [it["title"] for it in items]
    hits = [r for r in caplog.records if r.getMessage() == CROSS_CLICK_MSG]
    assert len(hits) == 1 and hits[0].levelno == logging.DEBUG and hits[0].exc_info[0] is RuntimeError
    assert [r for r in caplog.records if r.getMessage() == CROSS_MSG] == []


@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_cross_click_with_no_impression_records_empty_id_and_failure_is_swallowed(
        wire, monkeypatch, fake_st, caplog):
    """现状桩（失败注入版）：impressions 里没有该条时，clicked 写
    `recommendation_id=""` + `rank=0`，注入 emit_event 抛 RuntimeError 后被 :394 吞掉、
    渲染与跳转均不受影响。

    构造方式：预先把 `_cross_rec_shown_ids` 填满 ⇒ 展示循环被门控整批跳过（顺带钉住
    "门控只看 shown 集合、不看 impressions 是否真的落库"这条写序缺陷），
    `_rec_impressions` 留空 ⇒ 点击侧回退分支生效。
    与 l922-101 遗留问题 1 同型；解法待 l923-06 设计稿（A2）裁决，本例只钉现状。
    """
    items = _cross(2)
    fake_st.session_state[CROSS_SHOWN_KEY] = {(it["lang"], it["problem_id"]) for it in items}
    em = _Emitter(fail_on=("recommendation_clicked",))
    dao = _cross_setup(monkeypatch, items, em)
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        dashboard_page._render_cross_recommend(dao)      # 断言 ①：渲染仍完成

    assert em.kinds() == ["recommendation_clicked"] * 2, "shown 被门控整批跳过 ⇒ 一条曝光也补不回来"
    assert em.sent == []
    for idx, (_k, kw) in enumerate(em.attempts):
        pay = kw["payload"]
        assert pay["recommendation_id"] == "" and pay["rank"] == 0, \
            "impressions 缺条时点击归因退化成空串/0（脏事件的本体）"
        assert pay["surface"] == "cross_path" and pay["reason_code"] == "cross_path"
        assert kw["problem_id"] == items[idx]["problem_id"]
    assert fake_st.rerun_count == 2, "上报失败不得把「去做 →」变成死键"
    assert fake_st.session_state.selection["problem_id"] == items[-1]["problem_id"]
    assert _cards_rendered(fake_st, items) == [it["title"] for it in items]
    hits = [r for r in caplog.records if r.getMessage() == CROSS_CLICK_MSG]
    assert len(hits) == 2 and all(r.exc_info[0] is RuntimeError for r in hits)


@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_cross_click_with_no_impression_still_lands_an_unattributable_event(wire, monkeypatch, fake_st):
    """现状桩（无故障版）：同一状态下上报正常时，**空 recommendation_id 的事件会真的进事件库**
    ——漏斗于是收到一条 `clicked` 却查不到对应 `shown`（`clicked > shown` 的产生机制之一）。

    只钉现状、不判对错：修它要动写序/门控（l923-06 设计稿 A2/A3，其中 A3 改漏斗口径属停手项），
    超出执行班授权。本例与上一条配对，是为了让 A2 落地时**两条一起转红**、提醒改桩人
    归因语义已变。
    """
    items = _cross(1)
    fake_st.session_state[CROSS_SHOWN_KEY] = {(it["lang"], it["problem_id"]) for it in items}
    em = _Emitter()
    dao = _cross_setup(monkeypatch, items, em)

    dashboard_page._render_cross_recommend(dao)

    assert em.kinds() == ["recommendation_clicked"] * 1
    assert len(em.sent_of("recommendation_shown")) == 0
    pay = em.sent_of("recommendation_clicked")[0][1]["payload"]
    assert pay["recommendation_id"] == "" and pay["rank"] == 0
    assert pay["surface"] == "cross_path"


# ---------------------------------------------------------------------------
# 七、l924-01：今日推荐曝光区批级 try 下沉 per-item —— 两区 except 语义拉齐
#     改动点（**本单动了生产码**）：`ui/pages/dashboard.py` 今日推荐曝光记账循环的 `try:`
#     由"包整个 for"挪进循环体内，形状与 `_render_cross_recommend` 完全一致；失效模式从
#     "一条坏 → 本帧后续条连试都不试"变成"一条坏 → 只掉这一条"。写序 add→impressions→emit
#     未动（A2 裁决域：docs/insights/learn-shown-writeorder-design-20260923.md）。
#     掉的那一项怎么落（选了跨路径那一案，非本单自创）：**跳过该项、其余照常，按项各记一条
#     DEBUG（带栈）**；不计数、不汇总提示、面板零可见变化——例 3 用「故障帧 vs 全好帧的
#     渲染调用序列逐项相等」把这条钉死，改成"收集后统一提示"或"跳过并计数"当场红。
#     🔴 有牙：把 try 挪回批级（＝本单改动前的实现）时，例 1/例 2 红（主班按字节写回旧实现
#     实测过，读数见 zcode-bridge/outbox/l924-01.result.md「证据」）。
# ---------------------------------------------------------------------------

def test_one_bad_item_only_drops_itself_in_a_five_item_frame(wire, fake_st, caplog):
    """核心规格：5 条里第 3 条 emit 抛错 ⇒ 其余 4 条各上报**并送达**、五张卡全渲染。

    断言按"坏项存在时其余项仍在输出里／计数正确"两条各钉一遍：
      ① 计数面：事件库收到 4 条 recommendation_shown，problem_id 恰为除坏项外的 4 个，
         且 rank 仍是 1/2/4/5（跳过一条不许把后面的号往前挪——归因串号比掉一条更坏）；
      ② 渲染面：五张卡的标题全在 markdown 输出里；
      ③ 连带半径：attempts == 5（每条各试一次，首抛不再踢出循环）；
      ④ 日志面：SHOWN_MSG 恰 1 条、DEBUG、exc_info 真带 RuntimeError；
      ⑤ 记账面：shown/impressions 均 5 条 ⇒ 与事件库差的正好是坏的那 1 条（写序未动的老账）。
    """
    plan = _plan(5)
    em = _NthBoomer(3, boom="第 3 条炸")
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        wire(plan, em)                                          # 不外窜＝异常收在单条体内

    shown = em.sent_of("recommendation_shown")
    assert em.kinds() == ["recommendation_shown"] * 5
    assert [kw["problem_id"] for _k, kw in shown] == \
        [p["problem_id"] for i, p in enumerate(plan) if i != 2]
    assert [kw["payload"]["rank"] for _k, kw in shown] == [1, 2, 4, 5]
    assert {kw["payload"]["surface"] for _k, kw in shown} == {"dashboard"}
    assert _cards_rendered(fake_st, plan) == [it["title"] for it in plan]
    assert len(fake_st.session_state[SHOWN_KEY]) == 5
    assert len(fake_st.session_state[IMPR_KEY]) == 5
    hits = [r for r in caplog.records if r.getMessage() == SHOWN_MSG]
    assert len(hits) == 1, f"只该为坏掉那条记一条展示异常，实得 {len(hits)}"
    assert hits[0].levelno == logging.DEBUG and hits[0].exc_info[0] is RuntimeError


@pytest.mark.parametrize("surface", ["dashboard", "cross_path"])
def test_both_surfaces_share_the_same_per_item_containment_shape(
        wire, monkeypatch, fake_st, caplog, surface):
    """两区拉齐的对照例：同一份"3 条里第 2 条炸"注入打在两个区上，六个读数逐位相等。

    这条就是 l923-07 遗留问题 2「两区 except 语义不一致」的收口断言：改动前 dashboard 支
    attempts 只到第 2 条（批级 try 首抛即出循环）、跨路径支到第 3 条 ⇒ 本例在旧实现下
    红在 dashboard 那一支。断言面：试过的条数 / 送达的 problem_id 序列 / 本地 shown 记账数 /
    impressions 数 / 卡片全渲 / 展示侧日志条数与各自文案。
    """
    em = _NthBoomer(2, boom="第 2 条炸")
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        if surface == "dashboard":
            items = _plan(3)
            wire(items, em)
            shown_key, msg = SHOWN_KEY, SHOWN_MSG
        else:
            items = _cross(3)
            dashboard_page._render_cross_recommend(_cross_setup(monkeypatch, items, em))
            shown_key, msg = CROSS_SHOWN_KEY, CROSS_MSG

    assert em.kinds() == ["recommendation_shown"] * 3, \
        f"{surface} 区：坏一条不该吃掉本帧后续条的尝试机会"
    assert [kw["problem_id"] for _k, kw in em.sent] == \
        [it["problem_id"] for i, it in enumerate(items) if i != 1]
    assert {kw["payload"]["surface"] for _k, kw in em.sent} == {surface}
    assert len(fake_st.session_state[shown_key]) == 3
    assert len(fake_st.session_state[IMPR_KEY]) == 3
    assert _cards_rendered(fake_st, items) == [it["title"] for it in items]
    hits = [r for r in caplog.records if r.getMessage() == msg]
    assert len(hits) == 1 and hits[0].levelno == logging.DEBUG
    assert hits[0].exc_info[0] is RuntimeError


def test_dropped_items_log_one_debug_each_and_change_nothing_on_screen(wire, monkeypatch, caplog):
    """掉项的确切落法：按项各一条 DEBUG，**面板输出与全好帧逐项相同**（不计数、不汇总提示）。

    同一份 5 条计划跑两帧：全好帧 vs 第 2、4 条坏帧。若实现改成「收集后统一提示」或
    「跳过并在面板上标计数」，两帧的渲染调用序列就会分叉 ⇒ 本例红。
    两帧的送达数（5 vs 3）同时钉住"只掉坏的那两条"，日志条数钉住"一项一记"（2 条，
    不是批级时代整区 1 条）。
    """
    plan = _plan(5)
    frames = {}
    for tag, em in (("clean", _Emitter()), ("two_bad", _NthBoomer({2, 4}, boom="第 2、4 条炸"))):
        fake = DashboardFakeStreamlit()                              # 每帧一份全新 session_state
        monkeypatch.setattr(dashboard_page, "st", fake)
        monkeypatch.setattr(components, "st", fake)
        with caplog.at_level(logging.DEBUG, logger=LOGGER):
            wire(plan, em)
        frames[tag] = ([c[0] for c in fake.calls], len(em.sent_of("recommendation_shown")))

    assert frames["clean"][1] == 5 and frames["two_bad"][1] == 3, \
        "全好帧 5 条送达、坏两子的帧只掉这 2 条"
    assert frames["clean"][0] == frames["two_bad"][0], \
        "故障帧的面板输出必须与全好帧逐项相同——本案不给用户加提示"
    hits = [r for r in caplog.records if r.getMessage() == SHOWN_MSG]
    assert len(hits) == 2, f"per-item 那一案是「每项一条 DEBUG」，实得 {len(hits)}"
    assert all(r.levelno == logging.DEBUG and r.exc_info[0] is RuntimeError for r in hits)
