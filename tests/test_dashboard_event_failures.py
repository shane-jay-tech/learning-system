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

追加（l927-29，2026-09-28）：**生产码改了写序**——今日推荐点击侧由「emit 抛错照样跳」翻成
「emit 送达成功才跳（失败不跳）」。本文件第三／第四节共 **3 例**的跳转断言随之翻转
（翻面逐条明细见文件末尾「🔴 l927-29 改桩记录」），并新增第八节 2 例钉新规格。
第五／第六节（跨路径区）**一字未动** ⇒ 两区点击语义自本单起**不一致**，交主班裁。
本文件不假装一致，也不删桩凑绿。

追加（l927-37，2026-09-28）：**生产码又改了写序，这回是跨路径区的曝光侧**——
`_render_cross_recommend` 的记账循环由 `add → impressions → emit` 换成
`emit（前置条件先算齐）→ add 成功 → 记 impressions`（＝设计稿 A2 案，
docs/insights/learn-shown-writeorder-design-20260923.md §三／§七；A3 幂等键属改漏斗口径，本单没碰）。
于是本文件翻 3 处：§五 例 B 的第 ④ 组、§五 例 C 的末段，以及被**连坐**的 §七 例 2
（两区对照桩里"本地记账数"那两格自此按表面分叉，改逐表面钉值不放宽）——逐字明细见文末
「🔴 l927-37 改桩记录」。新增 §九 1 例钉自愈面（故障帧没送达的那条，恢复帧补报同一个 rid）。
今日推荐区（`:191-205`）的曝光写序**本单未动** ⇒ 两区曝光写序自本单起**不一致**（与 l927-29
留下的点击侧不一致是两格，各自交主班裁）。仍然零真库、零写盘。
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

def test_emit_failure_leaves_no_local_trace_and_self_heals_on_recovery(wire, fake_st):
    """l930-02 改桩（写序拉齐 A2：旧向新看齐）——本例原名
    test_local_state_is_written_before_emit_so_one_failure_loses_that_impression_forever，
    钉旧形态 `add → impressions → emit`（失败那条永久丢失）。今日推荐区换成与跨路径区
    逐字同型的 `emit 先、成功后才落本地账` 后，断言全部翻转：

    第 2 条炸 ⇒ 本地 shown/impressions 各 2（失败条**零残留**）、事件库 2；
    恢复帧重试第 2 条 ⇒ 事件库 3、本地 3——「本地−事件库」差额自愈归零（不再恒差 1）。
    rid 由 _make_rec_id 确定性生成 ⇒ 补报带同一 rid，归因链接上（跨路径区同款，:447 注释）。
    """
    plan = _plan(3)

    bad = _NthBoomer(2, boom="第 2 条曝光上报炸")
    wire(plan, bad)
    assert len(fake_st.session_state[SHOWN_KEY]) == 2                  # 失败条不进 shown（可重试前提）
    assert len(fake_st.session_state[IMPR_KEY]) == 2                   # impressions 同步零残留
    assert bad.kinds() == ["recommendation_shown"] * 3                 # 仍试满 3 次（坏项不连坐）
    assert [kw["problem_id"] for _k, kw in bad.sent] == \
        [plan[0]["problem_id"], plan[2]["problem_id"]]                 # 事件库到的正是另两条

    good = _Emitter()                                                  # 故障恢复，再渲染一次
    fake_st.calls.clear()
    wire(plan, good)
    retried = good.sent_of("recommendation_shown")
    assert [kw["problem_id"] for _k, kw in retried] == [plan[1]["problem_id"]], \
        "恢复帧重试的恰是炸掉的那条（自愈，A2 的核心收益）"
    assert len(fake_st.session_state[IMPR_KEY]) == 3                   # 本地 3 …
    assert len(bad.sent_of("recommendation_shown")) == 2               # … 事件库 2+1=3，差额归零


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
    # l930-02：写序 A2 后失败条不进本地账 ⇒ shown/impressions 各 4（差的就是坏的第 3 条）
    assert len(fake_st.session_state[SHOWN_KEY]) == 4
    assert len(fake_st.session_state[IMPR_KEY]) == 4
    assert [kw["problem_id"] for _k, kw in em.sent] == \
        [p["problem_id"] for i, p in enumerate(plan) if i != 2]          # 事件库恰少第 3 条
    assert _cards_rendered(fake_st, plan) == [it["title"] for it in plan]


# ---------------------------------------------------------------------------
# 三、点击侧：上报失败 ⇒ **不跳转**（l927-29 翻面；旧语义「炸了照样跳」见文件末尾改桩记录）
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_click_event_failure_still_navigates_and_logs(wire, fake_st, caplog):
    """l930-03 翻面（旧向新看齐，与跨路径 :490-497 同型）：clicked 抛错 → 日志照落 DEBUG 带栈，
    **跳转照常**（用户意图不被事件库故障劫持，两区死键面自此归零）。

    本例三代史：l922-101 原名钉「失败仍跳」→ l927-29 翻成 `..._now_stops_navigation`
    （rerun_count==0＋路由三键 not in）→ l930-03 拉齐翻回本名（rerun_count==2＋路由三键
    落最后一张卡）。日志面与「展示侧未被牵连」面逐条照旧，只有跳转面来回翻了两次——
    每次翻面都有裁决记录（l927-29 note §三 / l930-03 note），不是回退是拉齐。
    """
    plan = _plan(2)
    em = _Emitter(fail_on=("recommendation_clicked",))
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        wire(plan, em)

    hits = [r for r in caplog.records if r.getMessage() == CLICK_MSG]
    assert len(hits) == 2, f"两张卡各一条点击异常日志，实得 {len(hits)}"
    assert all(r.levelno == logging.DEBUG and r.exc_info is not None for r in hits)
    # 失败仍跳：两张卡各一次 rerun，路由三键落在最后一张卡（跨路径同款断言，:495）
    assert fake_st.rerun_count == 2, "l930-03：上报失败不得把「去做 →」变成死键（与跨路径拉齐）"
    assert fake_st.session_state.route == "language"
    assert fake_st.session_state.selection["problem_id"] == plan[-1]["problem_id"]
    # 展示侧未被牵连：两处 except 各自独立
    assert em.kinds() == ["recommendation_shown", "recommendation_shown",
                          "recommendation_clicked", "recommendation_clicked"]
    assert len(em.sent_of("recommendation_shown")) == 2
    assert em.sent_of("recommendation_clicked") == []
    # 卡片仍在（用户停在面板上才能重试点击：掉的是跳转，不是整区）
    assert _cards_rendered(fake_st, plan) == [it["title"] for it in plan]



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
    # l930-02：写序 A2 后两条都炸 ⇒ 本地账**零残留**，点击侧走 `imp.get(...)` 回退分支
    # （空 rid/rank=0——跨路径侧注释里「已知残余风险」的 dashboard 侧同款，形态肉眼可辨）。
    clicks = em.sent_of("recommendation_clicked")
    assert len(clicks) == 2
    for idx, it in enumerate(plan):
        assert (it["lang"], it["problem_id"], "dashboard") not in fake_st.session_state[IMPR_KEY], \
            "A2 下失败条不得有本地账"
        assert clicks[idx][1]["payload"].get("recommendation_id") in (None, ""), "回退分支：空 rid"
        assert clicks[idx][1]["payload"].get("rank") in (None, 0), "回退分支：rank 0/缺省"
        assert clicks[idx][1]["problem_id"] == it["problem_id"]              # 事件库里它从未 shown 过
    assert [r.getMessage() for r in caplog.records if r.name == LOGGER] == [SHOWN_MSG, SHOWN_MSG]


# ---------------------------------------------------------------------------
# 四、l922-102 的两格顺序面 —— l927-29 按裁决翻面（逐条改桩记录见文件末尾）
#     旧语义：emit 在 try 内、navigate 在 try 外 ⇒ 炸了也跳（"断网也能跳"）。
#     新语义：navigate 只在 emit **送达成功**之后发生 ⇒ 失败不跳、成功照跳且实参完整。
#     与上一节的分工不变：§三用 rerun_count 侧面看「没跳」，这里直接数 navigate 的次数与实参。
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_click_emit_failure_still_navigates_with_full_route(wire, fake_st, monkeypatch):
    """单卡：`recommendation_clicked` 抛错 → navigate **恰 1 次**且实参为完整路由三元组。

    本例三代史：l922-102 原名 `..._called_exactly_once`（守「别把 navigate 收进 try」）
    → l927-29 翻成 `..._leaves_navigate_never_called`（==0＋三键 not in）→ l930-03 拉齐翻回
    「恰 1 次＋实参完整」——与跨路径区同型。上报没送达这件事仍被下面 attempts/sent 两格钉着
    （裁决翻的是跳转面，不是把上报失败洗白成成功）。
    """
    plan = _plan(1)
    em = _Emitter(fail_on=("recommendation_clicked",))
    nav_calls = []

    def spy(lang, topic_slug, problem_id):
        nav_calls.append((lang, topic_slug, problem_id))

    monkeypatch.setattr(dashboard_page, "navigate_to_problem", spy)
    wire(plan, em)                                                     # 异常没窜出来＝except 生效

    assert nav_calls == [(it["lang"], it["topic_slug"], it["problem_id"]) for it in plan], \
        "l930-03：失败帧照跳且实参完整（与跨路径拉齐）"
    # （l930-03 注：本例 spy 只记录不转发，路由三键面由 §五/§六 的转发桩例钉。）
    assert em.kinds("attempts") == ["recommendation_shown", "recommendation_clicked"]
    assert em.sent_of("recommendation_clicked") == []                   # 事件确实没送达（跳转≠上报成功）


@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_navigate_runs_after_the_delivered_emit_not_instead_of_it(wire, fake_st, monkeypatch):
    """顺序桩（l927-29 版）：navigate 发生时 clicked 必须**既已尝试、也已送达**。

    原名 `test_navigate_runs_after_the_failed_emit_not_instead_of_it`：旧语义钉的是
    「先试上报（哪怕炸了）再跳」；新语义把门控条件从「试过」抬到「送到」，于是本例的注入
    由「clicked 必炸」换成「clicked 送达」，而**先后**这一格一格没少：
      · 实现若改成 emit 在 navigate 之后 → 跳转时刻 `sent_of(clicked)` 仍为 0 ⇒ 本例红；
      · 实现若退化为旧语义（试过没送到也跳）→ 本例用成功注入看不出，
        由 §三／§四 例 1／§八 例 2 三处各自转红（这就是"每格都留了反向钉"的分工）。
    """
    plan = _plan(1)
    em = _Emitter()                                       # 全送达：只有成功路径才谈得上先后
    seen_at_nav = []

    def spy(lang, topic_slug, problem_id):
        seen_at_nav.append((len(em.attempts), len(em.sent_of("recommendation_clicked"))))
        # 故意不打真 navigate：本例只钉调用点的先后，路由面在 §八 例 1 钉死

    monkeypatch.setattr(dashboard_page, "navigate_to_problem", spy)
    wire(plan, em)

    assert seen_at_nav == [(2, 1)]          # shown(1)+clicked(1) 都在跳转前，且 clicked 已落库
    assert em.kinds("attempts")[-1] == "recommendation_clicked"



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
    

    l930-03 注：今日推荐区点击语义已拉齐为本形态（失败仍跳），`rerun_count == 2` 由
    「跨路径特有残存形态」升格为「两区统一契约」；本例断言不变，只登记语义迁移。"""
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
      ④ 🔴 **l927-37 翻面**：写序已由 `add → impressions → emit` 换成 `emit → add → impressions`
         （A2，设计稿 docs/insights/learn-shown-writeorder-design-20260923.md §三 A2／§七）。
         旧断言钉的是"失败那条本地有账、库里永无 ⇒ 本地比事件库多 1"（悬空账），
         新断言钉的是"本地账与事件库**齐平**、失败那条**没进** shown ⇒ 恢复帧还会重试它"
         （自愈面由 §九 例 1 独立钉）。⚠ 翻面明细见文件末尾「🔴 l927-37 改桩记录」1。
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
    # ---- 断言 ④（l927-37 翻面）：本地账不再跑在送达前面 ----
    assert fake_st.session_state[CROSS_SHOWN_KEY] == \
        {(it["lang"], it["problem_id"]) for it in items[1:]}, \
        "emit 失败那条不该进 shown——进了就被门控永久挡掉，这条曝光再也补不回来"
    assert len(fake_st.session_state[IMPR_KEY]) == 2
    assert len(fake_st.session_state[IMPR_KEY]) == len(sent), \
        "写序换完 ⇒ 本地 impressions 与事件库送达数齐平（旧写序恒差 1，就是本例原来钉的那格）"
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

    🔴 l927-37 改末段（整页渲染面一字未动）：写序换 A2 后本区那条「残余脏面」的**形态**变了——
    旧：曝光没送达、本地却已记账 ⇒ 点击带得上一个事件库里**永不存在的 rid**（悬空归因，看着完整、
    实则断裂）；新：曝光没送达、本地也没记 ⇒ 点击走 `imp.get(...)` 回退分支，事件库里落一条
    **空 rid / rank=0** 的 clicked（肉眼可辨的缺口，且下一帧补报的是同一个 rid，可事后闭合）。
    旧断言 `payload["recommendation_id"]` 为真值 ⇒ 新实现下它红；翻面明细见文件末尾
    「🔴 l927-37 改桩记录」2，代价登记见 docs/insights/l927-37-writeseq.md §三。
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
    # 末段（l927-37 翻面）：故障帧的脏 clicked 由「悬空 rid」换成「空 rid」，
    # 并且本地账必须与送达同步为 0——旧写序那格（本地 1 / 库里 0）现在该红。
    assert em.kinds() == ["recommendation_shown", "recommendation_clicked"]
    assert em.sent_of("recommendation_shown") == []
    assert CROSS_SHOWN_KEY not in fake_st.session_state or \
        fake_st.session_state[CROSS_SHOWN_KEY] == set(), "失败那条不得进本地 shown"
    assert fake_st.session_state.get(IMPR_KEY, {}) == {}, "失败那条不得进本地 impressions"
    clicks = em.sent_of("recommendation_clicked")
    assert len(clicks) == 1, "曝光失败不连坐点击上报：这一条 clicked 照样送达"
    assert clicks[0][1]["payload"]["recommendation_id"] == "" \
        and clicks[0][1]["payload"]["rank"] == 0, \
        "A2 的已知残余风险＝故障帧最多 1 条空 rid 点击（设计稿 §八 待裁决 1）；" \
        "此处若出现非空 rid，说明有人把本地账又挪回送达之前"


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
    

    l930-03 注：今日推荐区点击语义已拉齐为本形态（失败仍跳），`rerun_count == 2` 由
    「跨路径特有残存形态」升格为「两区统一契约」；本例断言不变，只登记语义迁移。"""
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
    

    l930-03 注：今日推荐区点击语义已拉齐为本形态（失败仍跳），`rerun_count == 2` 由
    「跨路径特有残存形态」升格为「两区统一契约」；本例断言不变，只登记语义迁移。"""
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
    # l930-02：写序 A2 后失败条不进本地账 ⇒ 各 4（旧写序时代这里是 5，差的正是坏的那条）
    assert len(fake_st.session_state[SHOWN_KEY]) == 4
    assert len(fake_st.session_state[IMPR_KEY]) == 4
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

    🔴 l927-37 改桩（本例自此**只合比四面、记账面分表面钉**）：跨路径区写序换成 A2（emit 先、
    成功后落本地账）后，"本地 shown 记账数 / impressions 数"这两格**不再两区相等**——
    dashboard 支仍 3/3（旧写序，本地跑在送达前面），cross_path 支变 2/2（失败那条不进本地账）。
    原来那两行 `== 3` 是给两区共用的，留着就是把新写序判红；直接放宽成"两区各自 <=3"又会让
    本例失去判别力。⇒ 改成逐表面给期望值：**哪一区自己挪了写序而没同步这里，哪一支当场红**
    （按字节把跨路径区写回旧写序 ⇒ 只有 cross_path 支红；把今日推荐区也换成 A2 ⇒ 只有
    dashboard 支红）。两区写序自此不一致是**事实**，本例不假装它不存在，交主班裁的方向见
    docs/insights/l927-37-writeseq.md §三（⚠ 别照抄 l924-01 的拉齐方向，那次是"新向旧看齐"）。
    """
    em = _NthBoomer(2, boom="第 2 条炸")
    # 逐表面的本地记账期望：dashboard＝旧写序（本地 3 / 库里 2），cross_path＝A2（本地 2 / 库里 2）
    expected_local = 2  # l930-02：两区写序已拉齐为 A2（emit 先成功后记账），失败条都不进本地账
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
    assert len(fake_st.session_state[shown_key]) == expected_local, \
        f"{surface} 区的本地 shown 记账数该是 {expected_local}（本区写序形态见 docstring）"
    assert len(fake_st.session_state[IMPR_KEY]) == expected_local
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


# ---------------------------------------------------------------------------
# 八、l927-29：写序翻面后的**新规格**两例（成功路径照跳 ＋ 部分失败不连坐跳转）
#     §三／§四 翻面后各自钉住「失败帧不跳」，本节补的是那两个方向都看不见的一格：
#     门控**只该挡失败帧**。把 `reported` 旗标写反（成功也不跳）时 §三／§四 反而全绿——
#     只有例 1 会红；把门控写成批级共享（一条炸则整区都不跳）时例 2 会红。
#     这两例合起来才是「emit 送达成功之后才做跳转变更」的完整规格。
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_l927_29_click_emit_success_navigates_with_full_route(wire, fake_st, monkeypatch):
    """成功跳（判据②例一）：两张卡的 clicked 都送达 → navigate 恰两次、实参逐卡完整、路由真切换。

    这条同时把 l922-102 原例里「navigate 实参为完整路由三元组」那格接了过来——
    翻面时那格没有被丢掉，只是从失败路径搬到了成功路径（失败路径现在压根不该有实参）。
    """
    plan = _plan(2)
    em = _Emitter()                                             # 无故障：shown 与 clicked 全送达
    nav_calls = []
    real_navigate = components.navigate_to_problem

    def spy(lang, topic_slug, problem_id):
        nav_calls.append((lang, topic_slug, problem_id))
        return real_navigate(lang, topic_slug, problem_id)       # 转发真函数，不架空路由面

    monkeypatch.setattr(dashboard_page, "navigate_to_problem", spy)
    wire(plan, em)

    assert nav_calls == [(it["lang"], it["topic_slug"], it["problem_id"]) for it in plan], \
        "上报送达成功时门控不得挡跳转：两张卡各导航一次、按渲染顺序"
    assert len(em.sent_of("recommendation_clicked")) == 2
    assert fake_st.session_state.route == "language"
    assert fake_st.session_state.selected_lang == "python"
    assert fake_st.session_state.selection == {
        "lang": "python", "topic_slug": "01_x", "problem_id": plan[-1]["problem_id"]}
    assert fake_st.rerun_count == 2                              # 每次真导航各一 rerun
    # 曝光侧照常两笔送达，写序（add→impressions→emit）本单未动
    assert len(em.sent_of("recommendation_shown")) == 2


@pytest.mark.parametrize("fake_st", [{GO: True}], indirect=True)
def test_second_click_failure_drops_only_its_own_click_report(wire, fake_st, monkeypatch, caplog):
    """l930-03 改桩（判据②例二，部分失败面）：只有**第 2 张卡**的 clicked 抛错
    → l930-03 拉齐后两张卡**都导航**（失败仍跳）；本例改钉点击上报的连带半径归零

    （第 1 张照常送达）。🔴 三代有牙史：l922-102 旧实现本例红在两张都跳；l927-29 时代
    钉「第 1 张不被连坐」；l930-03 拉齐后跳转面回归跨路径同型 ⇒ 旧跳转断言整体过期，
    上报面分工断言保留（与 §七例 1 对曝光侧的分工同型）。
    """
    plan = _plan(2)
    em = _NthBoomer(2, kind="recommendation_clicked", boom="第 2 张卡点击上报炸")
    nav_calls = []
    real_navigate = components.navigate_to_problem

    def spy(lang, topic_slug, problem_id):
        nav_calls.append((lang, topic_slug, problem_id))
        return real_navigate(lang, topic_slug, problem_id)

    monkeypatch.setattr(dashboard_page, "navigate_to_problem", spy)
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        wire(plan, em)                                           # 异常不外窜＝except 仍收在单条体内

    assert nav_calls == [(it["lang"], it["topic_slug"], it["problem_id"]) for it in plan], \
        "l930-03：两区拉齐后失败也照跳 ⇒ 两张各跳一次、selection 落第 2 张"
    assert fake_st.session_state.selection["problem_id"] == plan[1]["problem_id"]
    assert fake_st.rerun_count == 2
    assert em.kinds("attempts") == ["recommendation_shown", "recommendation_shown",
                                    "recommendation_clicked", "recommendation_clicked"]
    assert [kw["problem_id"] for _k, kw in em.sent_of("recommendation_clicked")] == \
        [plan[0]["problem_id"]]
    hits = [r for r in caplog.records if r.getMessage() == CLICK_MSG]
    assert len(hits) == 1 and hits[0].levelno == logging.DEBUG and hits[0].exc_info[0] is RuntimeError


# ---------------------------------------------------------------------------
# 九、l927-37：跨路径区曝光写序换 A2（emit 先、成功后落本地账）后的**自愈面**
#     设计稿 §七 落地批次②原话：「新增一条『故障帧失败、恢复帧补报同一 rid』的自愈例
#     （今天这条线只有"钉坏"没有"钉好"）」——本节就是那条"钉好"。
#     只打跨路径区（今日推荐区 :191-205 的写序本单未动，两区形态差异见 §七 例 2 的逐表面期望）。
# ---------------------------------------------------------------------------

def test_l927_37_failed_cross_exposure_is_retried_next_frame_with_same_rec_id(
        wire, monkeypatch, fake_st, caplog):
    """故障帧没送达的第 2 条，恢复帧补报，且带的还是**同一个** recommendation_id。

    A2 换序的全部收益就在这一格：失败那条不进 `_cross_rec_shown_ids` ⇒ 门控不挡它 ⇒ 下一帧重试；
    rid 由 `_make_rec_id` 确定性生成 ⇒ 补报的 rid 与故障帧**尝试**时报的那个逐字相同 ⇒ 归因链
    事后可闭合（设计稿 §七 推荐理由 2，也是它判 A2 优于 B 案的那一格）。
    🔴 有牙：把写序换回 `add → impressions → emit`（＝本单前的形态）时，故障帧已把那条写进
    shown，恢复帧被门控整条跳过 ⇒ `recovered` 变空、本例当场红（与例 B ④ 的红互为正反两面）。
    """
    items = _cross(3)

    first = _NthBoomer(2, boom="第 2 条曝光上报炸")
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        dashboard_page._render_cross_recommend(_cross_setup(monkeypatch, items, first))
    attempted_rids = [kw["payload"]["recommendation_id"] for _k, kw in first.attempts]
    assert len(first.attempts) == 3 and len(first.sent) == 2
    assert fake_st.session_state[CROSS_SHOWN_KEY] == \
        {(it["lang"], it["problem_id"]) for it in items if it is not items[1]}, \
        "故障那条不得进 shown（进了＝永久丢失，本单的靶子）"

    second = _Emitter()
    dashboard_page._render_cross_recommend(_cross_setup(monkeypatch, items, second))   # 故障恢复帧

    recovered = [kw for _k, kw in second.sent_of("recommendation_shown")]
    assert second.attempts and len(second.attempts) == 1, "只有没送达的那一条该被重试"
    assert [kw["problem_id"] for kw in recovered] == [items[1]["problem_id"]], \
        "恢复帧只该补报故障那一条，而且必须补得回来（旧写序这里一条也补不了）"
    assert recovered[0]["payload"]["recommendation_id"] == attempted_rids[1], \
        "补报带的必须是同一个 rid，归因链才接得上（rid 若含随机量本例会红）"
    assert len(fake_st.session_state[CROSS_SHOWN_KEY]) == 3
    assert len(fake_st.session_state[IMPR_KEY]) == 3
    # 两帧合计：事件库 3 条 / 本地 3 条 ⇒ 旧写序那笔「本地恒比库里多 1」的悬空账在本区不复存在
    assert len(first.sent) + len(second.sent) == 3


class _BoomSet(set):
    """`add` 一调就抛的 shown 集合（l927-37 §九 例 2 专用，模拟会话态写不进去那一格）。"""

    def add(self, *a, **kw):
        raise RuntimeError("shown 集合写不进去")


def test_l927_37_impressions_are_written_only_after_shown_add_succeeded(
        wire, monkeypatch, fake_st, caplog):
    """钉换序的**第三格**：`emit` 成功后还要 `add` 成功，才轮得到记 impressions。

    卷宗「做什么」写的是"add 成功后再记 impressions"，前两处翻面只钉住了「emit 在前、本地账在后」，
    **钉不住 add 与 impressions 谁先谁后**（把它俩对调，例 B／例 C／§七 例 2／§九 例 1 全绿）。
    本例把这一格单独钉住：注入 `shown.add` 抛错（会话态写不进）⇒ 事件库已经收到那条 shown，
    本地 impressions **必须还是空的**；若实现把 impressions 挪到 `add` 之前，这里就会留下
    一条"本地有归因、shown 门控却没记下"的错位账，下一帧重发同一条 ⇒ 漏斗吃到重复曝光。
    🔴 这一格的代价也如实登记：**送达之后才失败的项在事件库里有一条、本地没账**（反方向悬空），
    它比旧写序好的地方在于「下一帧重试」而不是「下一帧永久跳过」——见 §九 例 1 与
    docs/insights/l927-37-writeseq.md §三。
    """
    items = _cross(1)
    fake_st.session_state[CROSS_SHOWN_KEY] = _BoomSet()
    em = _Emitter()
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        dashboard_page._render_cross_recommend(_cross_setup(monkeypatch, items, em))

    assert len(em.sent_of("recommendation_shown")) == 1, "emit 已成功：这一条确实在库里"
    assert fake_st.session_state[IMPR_KEY] == {}, \
        "add 失败 ⇒ impressions 不得写入（本例只钉 add 与 impressions 的先后）"
    assert _cards_rendered(fake_st, items) == [it["title"] for it in items]
    hits = [r for r in caplog.records if r.getMessage() == CROSS_MSG]
    assert len(hits) == 1 and hits[0].levelno == logging.DEBUG \
        and hits[0].exc_info[0] is RuntimeError


# ---------------------------------------------------------------------------
# 十、l927-49：畸形推荐项（字典缺 lang／problem_id）的预检收口面
#     改前那一格在 try 外（`pid_key = (it["lang"], it["problem_id"])`），坏一项吃掉整区；
#     本节钉「不崩 ＋ 跳过该项 ＋ 按项记一条 DEBUG」，并顺手钉住 rank 取原序不重编号。
# ---------------------------------------------------------------------------

def test_malformed_recommendation_item_is_skipped_without_killing_the_region(wire, fake_st, caplog):
    """畸形项（缺 `problem_id`）不崩、跳过、记一条 DEBUG，其余四条照常（l927-49 判据②）。

    改前现证：`ui/pages/dashboard.py` 的 `pid_key = (it["lang"], it["problem_id"])` 落在
    per-item `try` **外**（l924-01 遗留问题 1 点名的那一格），本例会以 KeyError 直接窜出
    `_render_dashboard_body`（上层 `render_dashboard` 只 try/finally 不 catch）⇒
    整张面板后半段一起掉，一条坏项吃掉四条正常项的记账与渲染。
    现按卷宗许可的「预检形态」收：缺键项在两循环之前就被挡掉，只掉它自己。
    🔴 顺带钉住本单的实现选择：**rank 取 `enumerate` 原序、坏项不重新编号**
    （⇒ 幸存四条的 rank 是 [1,3,4,5] 而非 [1,2,3,4]）。理由是 `_make_rec_id` 把 rank 编进 rid，
    重编号会让"同一条推荐在坏项出现的帧与不出现的帧"拿到两个 rid，跨帧归因链断裂；
    代价＝rank 与卡片视觉序在坏项帧里不等。要改这一格请连同本例一起改，见
    docs/insights/l927-49-note.md §四。
    """
    base = _plan(4)
    malformed = {k: v for k, v in base[1].items() if k != "problem_id"}
    malformed["title"] = "畸形项（缺 problem_id）"
    plan = [base[0], malformed] + base[1:]          # 畸形项插在 rank 2

    em = _Emitter()
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        wire(plan, em)                               # 异常没窜到调用方，本身就是判据②的前半

    # 不连坐：四条正常项照常尝试并送达，畸形项一次都没试
    assert em.kinds() == ["recommendation_shown"] * 4, "坏项不该吃掉其余条的尝试，也不该自己被试"
    sent = [kw for _k, kw in em.sent_of("recommendation_shown")]
    assert [kw["problem_id"] for kw in sent] == [it["problem_id"] for it in base]
    assert [kw["payload"]["rank"] for kw in sent] == [1, 3, 4, 5], "rank 取原序（见 docstring 的 🔴）"
    # 渲染面：三张正常卡在，畸形卡不在（改前此处压根渲染不到）
    assert _cards_rendered(fake_st, plan) == [it["title"] for it in base]
    assert "畸形项（缺 problem_id）" not in " ".join(
        str(c[1][0]) for c in fake_st.calls if c[0] == "markdown")
    # 本地账：shown 只收四条，畸形项没进去（它连 pid_key 都取不出来）
    assert fake_st.session_state[SHOWN_KEY] == {
        (it["lang"], it["problem_id"]) for it in base}
    # 不静默：恰一条 DEBUG，报出缺的是哪个键
    hits = [r for r in caplog.records if r.getMessage().startswith("dashboard: 推荐项缺 ")]
    assert len(hits) == 1, f"每条畸形项各记一条、正常项零记，实得 {len(hits)} 条"
    assert hits[0].levelno == logging.DEBUG and "problem_id" in hits[0].getMessage()
    assert [r.getMessage() for r in caplog.records
            if r.name == LOGGER and r.levelno == logging.DEBUG] == [hits[0].getMessage()], \
        "本帧除预检那一条外不该再产生任何 DEBUG（正常项照常 ⇒ SHOWN_MSG 零条）"


# ---------------------------------------------------------------------------
# 🔴 l927-29 改桩记录（2026-09-28）——本文件第一次按裁决翻转断言方向（第二次见文末 l927-37），逐字留痕
#
# 裁决来源：`zcode-bridge/inbox/l927-29.task.md`「做什么」＝"修写序：emit_event 成功后再写
# 跳转变更（或按档内裁决方向——上报失败就不跳）"。方向取自 `l922-102` 结果「遗留问题」第 2 条
# 原话："若规划侧将来要把语义改成「上报失败就不跳」，例 1 会首先转红——那是**有意**留下的
# 冲突点，请在裁决时一并决定桩的去留，不要静默改桩。" ⇒ 本单就是那句"将来"的兑现。
# **不是**为了让盘子变绿而改桩：三处旧例每一处都保留了原有的至少一条判别钉，只是方向翻了。
#
# 翻面明细（旧例名 → 新例名 → 哪格变了／哪格没丢）：
#   1. §三 `test_click_event_failure_still_navigates_to_problem`
#      → `test_click_event_failure_now_stops_navigation`
#        变：`rerun_count == 2` ＋ `route == "language"` ＋ `selection` 落最后一张卡
#          → `rerun_count == 0` ＋ `route`/`selected_lang`/`selection` 三键**根本不存在**
#            （用「不写」而不是「写成别的值」，后者更难发现）。
#        没丢：CLICK_MSG 恰 2 条＋DEBUG＋exc_info 真带；`em.kinds()` 四条全试序列；
#          `sent_of(shown)==2`、`sent_of(clicked)==[]`；新增 `_cards_rendered` 一条（掉的是
#          跳转，不是整区——用户得停在面板上才可能重试）。
#   2. §四 例 1 `test_click_emit_failure_leaves_navigate_called_exactly_once`
#      → `test_click_emit_failure_leaves_navigate_never_called`
#        变：`nav_calls == [(lang, slug, pid)]` → `== []`；spy 不再转发真 navigate（旧实现下
#          它会多写一次路由，掩盖门控失效）。
#        没丢：`em.kinds("attempts")` 仍钉「上报真试过」＋「clicked 未送达」。
#        搬走：「navigate 实参为完整路由三元组」整格搬进 §八 例 1 的成功路径继续钉。
#   3. §四 例 2 `test_navigate_runs_after_the_failed_emit_not_instead_of_it`
#      → `test_navigate_runs_after_the_delivered_emit_not_instead_of_it`
#        变：注入由「clicked 必炸」换成「clicked 送达」；跳转时刻的读数由 `(尝试数 == 2)`
#          抬成 `(尝试数, 送达数) == (2, 1)`。
#        没丢：钉的仍是**先后**（emit 在 navigate 之前）——实现把 emit 挪到跳转之后照样红。
#   4. §五／§六／§七 **一字未动**：跨路径区（现值 `ui/pages/dashboard.py:447-458`，
#      `except` :454 ／ `navigate_to_problem` :458）的
#      `except` 之后 `navigate_to_problem` 仍在 try 外 ⇒ 两区点击语义自本单起**不一致**
#      （今日推荐＝失败不跳；跨路径＝失败仍跳）。本文件不假装一致；不一致面见
#      `docs/insights/l927-29-note.md` §三 与 `l927-29.result.md`「遗留问题」1（属人工裁决）。
#   5. 写序缺陷的另一半（曝光侧 `add → impressions → emit` 仍在送达之前）**本单未动**，
#      仍由 §二 例 3 的第 ④ 组断言与 §七 例 1 的记账面钉着；解它走 A2/A3 设计稿
#      `docs/insights/learn-shown-writeorder-design-20260923.md`。
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 🔴 l927-37 改桩记录（2026-09-28）——跨路径区**曝光写序**翻面（emit 先、成功后落本地账），逐字留痕
#
# 裁决来源：`zcode-bridge/inbox/l927-37.task.md`「做什么」＝"按档内预置断言（例B④／例C）换序：
# add 成功后再记 impressions、emit 前置条件齐备，两断言翻绿"。这两格正是 l923-07 结果「遗留问题」1
# 原话点名的靶子：「`add → impressions → emit` 未换序 ⇒ 失败一条曝光永久丢失＋点击带悬空 rid
# 两件事没修（例 B ④、例 C 末段两条断言就是留给 A2 的靶子）」⇒ 本单是那句"留给"的兑现，
# 实现面＝设计稿 §三 A2 案（emit 成功 → `shown.add` → `impressions[k]`），A3（幂等唯一索引、
# 改漏斗计数口径）**没做也不该由执行班做**——`core/progress.py` 与题件本单一字未碰。
#
# 翻面明细（旧断言 → 新断言 → 哪格没丢）：
#   1. §五 例 B `test_cross_shown_event_failure_is_contained_per_item` 的第 ④ 组
#      变：`CROSS_SHOWN_KEY == 全部 3 条` ＋ `len(IMPR_KEY) == 3` ＋
#          `len(sent) == 2  # 写序未动 ⇒ 本地有账、库里永无（悬空账）`
#        → `CROSS_SHOWN_KEY == items[1:]（失败那条不在）` ＋ `len(IMPR_KEY) == 2` ＋
#          新增 `len(IMPR_KEY) == len(sent)`（本地与送达齐平＝悬空账归零的正写）。
#      没丢：① 不外窜、② `calls == shown*3`（连带半径）、③ 日志恰 1 条 DEBUG 带栈、卡片全渲
#        ——三格逐字照旧，本例仍区分有 try / 无 try。
#      补：自愈面独立成 §九 例 1（设计稿 §七 批次② 点名的"钉好"），不在这里合钉。
#   2. §五 例 C `test_cross_shown_event_failure_no_longer_takes_down_the_sections_below` 末段
#      变：`len(clicks) == 1 and payload["recommendation_id"]`（悬空 rid 为真值）
#        → `len(clicks) == 1` ＋ `recommendation_id == ""` ＋ `rank == 0`
#          ＋ 新增两条「失败那条不进本地账」（`CROSS_SHOWN_KEY` 空集、`IMPR_KEY` 空 dict）。
#      没丢：整页后半段五个区块标题、`download_button`／`file_uploader` 在位——**全部一字未动**，
#        本例的本体（l922-103 例 C）钉的是"爆炸半径"，与写序无关，翻面只碰末段那三行。
#      脏事实没被抹掉，只换了形态：旧＝库里永不出现的 rid（对账看着完整、实则断裂），
#        新＝肉眼可辨的空串（rid 确定 ⇒ 恢复帧补报同一个 rid 可闭合）。设计稿 §八 待裁决 1
#        登记的正是这条残余，本单把它写成"该红就红"。
#   3. §七 例 2 `test_both_surfaces_share_the_same_per_item_containment_shape`（**连坐面，如实登记**）
#      变：两区共用的 `len(shown_key) == 3`／`len(IMPR_KEY) == 3` 两行 → 逐表面期望
#        （dashboard 支 3/3 旧写序、cross_path 支 2/2 新写序）。
#      为什么不是"改松凑绿"：四面合比（尝试数 / 送达 problem_id / 卡片 / 日志）原样保留，
#        只有真分叉的那两格改成逐表面钉值 ⇒ 任一区自己挪了写序而没同步这里，对应那支当场红
#        （变异实测：跨路径区写回旧写序 ⇒ 只 cross_path 支红；把 dashboard 区也换成 A2 ⇒ 只
#         dashboard 支红，读数见 docs/insights/l927-37-writeseq.md §四）。
#      ⚠ 这条是 l924-01「两区 except 语义拉齐」的对照桩，本单把它的**记账面**拆开：拉齐方向别默认
#        ——l924-01 是"今日推荐照跨路径那一案改"（新向旧看齐），本单是跨路径区自己走向 A2（旧形态
#         该向新形态看齐），两案相反，是否把今日推荐区一并换过来属主班裁决（l927-37-writeseq.md §三）。
#   4. §一／§二／§三／§四／§六／§八 **一字未动**（今日推荐区曝光写序、两区点击语义、l927-29 翻的
#      跳转面全部保持原样）⇒ 本单没把兄弟单已经翻面的断言又翻回去。§六 例 3/例 4 那两例
#      空 rid 桩靠「预填 shown 集合」构造，换序后仍绿；它们 docstring 预言"A2 落地时两条一起转红"
#      **没兑现**（预填门控的路径不经失败注入），属当年推演偏差，如实登记不改桩。
#   5. 本文件由 23 例增至 24 例（新增 §九 自愈例），未删一例、未 xfail 一例、未放宽任何恒真断言。
# ---------------------------------------------------------------------------



# ---------------------------------------------------------------------------
# 八、l930-02 自愈例：失败帧零残留 ⇒ 恢复帧重试同一条（今日推荐区 A2 后的专属钉，
#     跨路径区的同款自愈由 l927-37 §九 例在册；本例补齐 dashboard 支）
# ---------------------------------------------------------------------------
def test_dashboard_impression_failure_self_heals_on_next_frame(wire, fake_st):
    """第 2 条炸 → 恢复帧只补报那一条、rid 与首次注入的确定性 rid 一致（归因链自动接上）。"""
    plan = _plan(3)
    bad = _NthBoomer(2, boom="第 2 条曝光上报炸")
    wire(plan, bad)
    assert len(fake_st.session_state[SHOWN_KEY]) == 2

    good = _Emitter()
    fake_st.calls.clear()
    wire(plan, good)
    retried = good.sent_of("recommendation_shown")
    assert len(retried) == 1, "恢复帧只补报炸掉那一条（其余两条 shown 门控挡住不重发）"
    _k, kw = retried[0]
    assert kw["problem_id"] == plan[1]["problem_id"]
    expected_rid = dashboard_page._make_rec_id("dashboard", plan[1].get("reason_code", ""),
                                               plan[1]["lang"], plan[1]["problem_id"], 2)
    assert kw["payload"]["recommendation_id"] == expected_rid, "补报 rid＝确定性 rid（归因链接上）"
    assert kw["payload"]["rank"] == 2
    # 本地账此时补齐 3 条（含刚重试的那条）
    assert len(fake_st.session_state[SHOWN_KEY]) == 3
    assert len(fake_st.session_state[IMPR_KEY]) == 3


# ---------------------------------------------------------------------------
# 九、l930-04：跨路径区畸形项预检（l927-49 note §五-1 半件收口）——与今日推荐区
#     l927-49 段同型：缺 lang/problem_id 的项按项记 DEBUG 跳过，渲染循环同吃预检结果
#     （A2 写序与 rec_id/payload try 外先算不动）。
# ---------------------------------------------------------------------------
def test_cross_path_malformed_item_is_skipped_not_blown_up(wire, monkeypatch, fake_st, caplog):
    """一条缺 problem_id 的畸形项混进 cross(3) ⇒ 不窜出、其余两条照常展示+渲染，
    日志一条 DEBUG 带缺键名（与今日推荐区 l927-49 段同判据）。"""
    items = _cross(3)
    del items[1]["problem_id"]                                   # 中位项畸形
    em = _Emitter()
    dao = _cross_setup(monkeypatch, items, em)
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        dashboard_page._render_cross_recommend(dao)

    hits = [r for r in caplog.records if r.name == LOGGER
            and "跨路径推荐项缺" in r.getMessage()]
    assert len(hits) == 1 and hits[0].levelno == logging.DEBUG
    assert "problem_id" in hits[0].getMessage()
    # 好的两条照常送达 shown（渲染循环同吃预检结果 ⇒ 不再在 LANG_META 裸奔）
    assert [kw["problem_id"] for _k, kw in em.sent_of("recommendation_shown")] == \
        [it["problem_id"] for it in items if "problem_id" in it]
    assert _cards_rendered(fake_st, items[:1] + items[2:]) == \
        [it["title"] for it in items if "problem_id" in it]


# ---------------------------------------------------------------------------
# 十、l930-05：推荐项预检键域扩展（l927-49 遗留「未点名残面」三类收口）
#     渲染必需四键缺口／lang 不在 LANG_META／非 dict 项——三类各一例注入，
#     全部按项 DEBUG 跳过、不窜出不带炸整区；rank 保持原序不重编号。
# ---------------------------------------------------------------------------
def test_dashboard_precheck_extended_key_domain(wire, fake_st, caplog):
    """plan(4) 里混三类畸形（缺 topic_slug／lang 不在 LANG_META／非 dict）＋一条好项
    ⇒ 好项照常展示渲染，三条畸形各一条 DEBUG（缺键名/LANG_META/非 dict 各自可辨）。"""
    plan = _plan(4)
    plan[1].pop("topic_slug")                     # 缺渲染必需键
    plan[2]["lang"] = "klingon"                   # 不在 LANG_META
    plan[3] = "not-a-dict"                        # 非 dict
    em = _Emitter()
    with caplog.at_level(logging.DEBUG, logger=LOGGER):
        wire(plan, em)

    dbg = [r.getMessage() for r in caplog.records if r.name == LOGGER and "推荐项" in r.getMessage()]
    assert any("topic_slug" in m for m in dbg), "缺渲染键应有专属 DEBUG"
    assert any("klingon" in m and "LANG_META" in m for m in dbg), "LANG_META 成员校验应有专属 DEBUG"
    assert any("非 dict" in m for m in dbg), "非 dict 应有专属 DEBUG"
    # 好项（第 1 条）照常：1 条 shown、1 张卡渲染
    assert len(em.sent_of("recommendation_shown")) == 1
    renderable = [it for it in plan if isinstance(it, dict) and "title" in it]
    assert _cards_rendered(fake_st, renderable) == [plan[0]["title"]]
    # rank 保持原序不重编号：好项的 rank 仍是 1（坏项占掉自己的序号）
    stored = fake_st.session_state[IMPR_KEY][(plan[0]["lang"], plan[0]["problem_id"], "dashboard")]
    assert stored["rank"] == 1
