# -*- coding: utf-8 -*-
"""错题本页 tab 计数标签与空态文案的契约桩（l922-123 立桩，l923-20 随下限语义文案改版）。

钉 ui/pages/mistakes.py 的 `_render_mistakes_body`（磁盘实况 :69-114；**锚点整体后移过**——
l923-19 在同文件上方插入了缓存 mtime 助手、l923-20 又加了 4 行说明注释、l924-09 再在汇总行
下方插了真数提示段，本档按当前磁盘重取，不再照抄 l922-123 当时的 :30-63）。
这套「计数 → 汇总行 → tab 标签」联动此前无 UI 桩
（`tests/test_mistakes_edges.py` 只测 `_render_due_reviews` 的行内细节）：

- :79 `st.markdown(f"**错题 {wrong_count} 道 · 最近 50 条内到期复习 {overdue_count} 道**")`
      —— 汇总行无条件先出；**到期侧文案自 l923-20 起显式标下限语义**（原名「到期复习 N 道」）
- :84-87 打满 50 且 COUNT 真数更大时**净新增**一行真数提示（l924-09，见文件末段）
- :89-91 双零 ⇒ 整页 `st.success` 空态并 **return**（一个 tab 都不建）
- :93-98 标签按 `if overdue_count:` / `if wrong_count:` 条件追加，`"弱项专练"` 恒在且排最后
- :100 `st.tabs(tab_labels)` 的返回下标靠 :101-114 的 `tab_idx` 手动对齐 —— 标签与索引是**两处独立推导**，
  任一侧改条件而另一侧没跟上就会串 tab（本桩用「标签序列 == 期望序列」整序断言把它锁住）

DAO 与 `_lookup_problem` 全部打桩，**不触真实题库**（`_problem_lookup_cache` 的失效通道
已由 l923-19 实装为「键里并 yaml mtime」，本单也不依赖它）。
本文件的例只加测试；**页面侧那一行文案改动属 l923-20 的授权范围**（零行为变更，`limit=50` 未动）。

l924-08 续笔：l923-20 留给裁量的「标签要不要一起标」已采纳，页面侧仍只改 `mistakes.py:87` 一行
（`到期复习 (N)` → `到期复习 (N · 至多)`），本文件随之同步 3 处标签字面断言＋联动契约例里的
标签解析式。**汇总行三组数、`page_cap == 50` 跨源断言、`limit=50` 调用实参一律未动**——
本单动的是字面，不是计数口径。

l924-09 续笔：COUNT(*) 伴生查询（`ProgressDAO.get_due_reviews_total`）已实装 —— 页面在
「打满 50」且真数更大时**净新增**一行 `st.caption` 真数提示。本文件因此：
① 既有各例的**期望值集合一字未改**（汇总行 / 标签 / `page_cap` / `call_args` 全部原样），
   只在 `_body` 的桩上补了伴生查询的默认返回值（未打满时真数==页内条数，纯桩件补全）；
② 新增页面例与 DAO 真库例（见文件末「COUNT(*) 伴生查询」段）。
   ⇒ 本单是 §五.4 里"纯增量"那一支，不是改计数口径。
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import app  # noqa: F401  # 与 test_ui_behavior 同桩模式：app 侧 import 预绑定 st
import ui.components as components
import ui.pages.mistakes as mistakes_page
from tests.test_ui_behavior import Context, FakeStreamlit

SUMMARY_PREFIX = "**错题 "
DUE_TOTAL_HINT_PREFIX = "实际到期共"   # l924-09：页面真数提示行的字面锚，页面侧改文案本档即红


class TabsFake(FakeStreamlit):
    """补 tabs / expander / button 录制。

    基类 `tabs` 只回上下文列表、不留标签 —— 不补录就断言不到本单要钉的标签序列；
    基类 `button` 只回布尔、`expander` 不留标签，同理。
    """

    def __init__(self):
        super().__init__()

        def tabs(labels):
            self.calls.append(("tabs", (labels,), {}))
            return [Context() for _ in labels]

        def expander(*a, **kw):
            self.calls.append(("expander", a, kw))
            return Context()

        def button(label, *a, **kw):
            self.calls.append(("button", (label,), kw))
            return self.buttons.get(label, False)

        self.tabs = tabs
        self.expander = expander
        self.button = button


def _mk(n, kind):
    """造 n 条假记录；字段覆盖 `_render_due_reviews`（现读 :117-142）与
    `_render_wrong_problems`（:145-169）实际读到的键。"""
    out = []
    for i in range(n):
        pid = f"{kind}_{i}"
        if kind == "due":
            out.append({"lang": "python", "problem_id": pid,
                        "interval_days": 7, "next_due_date": "2099-12-31"})
        else:
            out.append({"lang": "python", "problem_id": pid,
                        "last_attempt_ts": "2026-09-01 12:00:00", "ts": "2026-09-01 12:00:00",
                        "code": "print(1)", "ai_feedback": ""})
    return out


def _body(monkeypatch, mistakes, reviews, due_total=None):
    """渲染 `_render_mistakes_body`，返回 (fake, 汇总行文本, tab 标签序列或 None)。

    l924-09 加了第三个桩参 `due_total`：**缺省即「真数==页内条数」**（未打满时的恒等事实），
    所以既有各例的断言面一字未改，只是 DAO 桩补全到新调用点。
    """
    fake = TabsFake()
    monkeypatch.setattr(mistakes_page, "st", fake)
    monkeypatch.setattr(components, "st", fake)
    # 恒定命中题库：避开 _lookup_problem 的真实全表扫描与模块级缓存（l922-119 在册待裁决）
    topic = SimpleNamespace(slug="loops", title="循环")
    problem = SimpleNamespace(slug="loops", title="两数之和")
    monkeypatch.setattr(mistakes_page, "_lookup_problem", lambda lang, pid: (topic, problem))
    monkeypatch.setattr(mistakes_page, "navigate_to_problem", lambda *a, **kw: None)
    dao = MagicMock()
    dao.list_mistakes.return_value = mistakes
    dao.get_due_reviews.return_value = reviews
    dao.get_due_reviews_total.return_value = len(reviews) if due_total is None else due_total
    dao.close.return_value = None
    fake.dao = dao  # 供「取数口径」类断言回看调用实参
    mistakes_page._render_mistakes_body(dao)
    summary = [str(a[0]) for name, a, _ in fake.calls if name == "markdown"
               and str(a[0]).startswith(SUMMARY_PREFIX)]
    assert len(summary) == 1, f"汇总行应恰好一条，实为 {summary}"
    labels = [c[1][0] for c in fake.calls if c[0] == "tabs"]
    assert len(labels) <= 1, f"tabs 至多调一次，实为 {len(labels)}"
    return fake, summary[0], (labels[0] if labels else None)


def _due_total_hints(fake):
    """l924-09：页面新出的「实际到期共 N 道」提示行（st.caption），按字面锚筛出全部命中。"""
    return [str(a[0]) for name, a, _ in fake.calls
            if name == "caption" and str(a[0]).startswith(DUE_TOTAL_HINT_PREFIX)]


# --- 三场景（任务书点名）+ 第四场景（只有到期）------------------------------------------------

def test_双零_整页走success空态且不建任何tab(monkeypatch):
    fake, summary, labels = _body(monkeypatch, [], [])
    assert summary == "**错题 0 道 · 最近 50 条内到期复习 0 道**", summary
    assert labels is None, ":38-40 双零分支必须 return，不能走到 st.tabs"
    succ = [str(a[0]) for name, a, _ in fake.calls if name == "success"]
    assert succ == ["没有错题也没有到期复习，做得不错！"], succ
    assert not [c for c in fake.calls if c[0] == "markdown"
                and "弱项专练" in str(c[1][0])], "空态下不该渲染任何分区"


def test_只有错题_标签两级且无到期复习项(monkeypatch):
    _, summary, labels = _body(monkeypatch, _mk(2, "wrong"), [])
    assert labels == ["错题重做 (2)", "弱项专练"], labels
    assert summary == "**错题 2 道 · 最近 50 条内到期复习 0 道**", summary


def test_双有_到期复习在前错题在后弱项收尾(monkeypatch):
    _, summary, labels = _body(monkeypatch, _mk(3, "wrong"), _mk(5, "due"))
    assert labels == ["到期复习 (5 · 至多)", "错题重做 (3)", "弱项专练"], labels
    assert summary == "**错题 3 道 · 最近 50 条内到期复习 5 道**", summary


def test_只有到期_标签两级且无错题项(monkeypatch):
    _, summary, labels = _body(monkeypatch, [], _mk(4, "due"))
    assert labels == ["到期复习 (4 · 至多)", "弱项专练"], labels
    assert summary == "**错题 0 道 · 最近 50 条内到期复习 4 道**", summary


# --- 计数-标签联动契约（跨场景泛化）--------------------------------------------------------------

@pytest.mark.parametrize("n_wrong,n_due", [(0, 1), (1, 0), (1, 1), (7, 13), (0, 50), (1, 2)])
def test_汇总行数字与tab标签数字逐值相等(monkeypatch, n_wrong, n_due):
    r""":79 汇总行与 :95/:97 标签里的数字必须同源 —— 两处各写一遍，是最容易漂的一对。

    l923-20 起汇总行多了一段字面下限标记（「最近 50 条内」），旧的
    `re.findall(r"\d+")` 只认"恰好两个数"，会把 50 也捞进来 ⇒ 解包炸。
    现改成整条形态匹配：三组数各归各位（错题数／标记里的页大小／到期数），
    并**新增**一条"标记里的 50 必须等于页面写死的 limit=50"的跨源断言——
    即文案与查询参数不同源时本例主动红。判据没放宽，是收紧。

    l924-08 起标签侧也带了一段字面下限标记（`到期复习 (5 · 至多)`），标签解析式
    因此加了一个**可选**捕获组去接它：计数位仍只认 `\((\d+)…\)$`，没退化成
    `\d+.*`（那样"数字被文案挤走"也会被读成合法）。同时新增两条"标记只准出现在
    到期侧"的双向断言 ⇒ 这一例对本单是**收紧**，不是为了让它绿而放宽。
    """
    import re
    fake, summary, labels = _body(monkeypatch, _mk(n_wrong, "wrong"), _mk(n_due, "due"))
    shape = re.fullmatch(r"\*\*错题 (\d+) 道 · 最近 (\d+) 条内到期复习 (\d+) 道\*\*", summary)
    assert shape, f"汇总行形态变了，本例解析式要先跟上：{summary}"
    s_wrong, page_cap, s_due = (int(x) for x in shape.groups())
    assert page_cap == 50, f"文案标的页大小与页面 limit=50 不同源：{page_cap}"
    assert (s_wrong, s_due) == (n_wrong, n_due), summary
    tag = {}
    mark = {}
    for lb in labels:
        m = re.match(r"(.+) \((\d+)( · 至多)?\)$", lb)
        if m is None:
            assert lb == "弱项专练", f"唯一不带计数的标签应是弱项专练，实为 {lb}"
            continue
        tag[m.group(1)] = int(m.group(2))
        mark[m.group(1)] = m.group(3)
    assert tag.get("错题重做", 0) == s_wrong, (tag, summary)
    assert tag.get("到期复习", 0) == s_due, (tag, summary)
    # 汇总为 0 的那一侧，标签里就不该出现同名项（条件追加语义）
    assert ("错题重做" in tag) == (s_wrong > 0), (tag, summary)
    assert ("到期复习" in tag) == (s_due > 0), (tag, summary)
    # l924-08：下限标记只准挂在到期侧。错题侧 list_mistakes() 无 LIMIT 是全量真数，
    # 它若也带上「· 至多」就是说谎文案；到期侧一旦建标签就必须带 —— 双向都钉。
    assert mark.get("到期复习") == (" · 至多" if s_due > 0 else None), (mark, summary)
    assert mark.get("错题重做") is None, (mark, summary)
    assert labels[-1] == "弱项专练", f"弱项专练须恒在且收尾：{labels}"
    assert labels.count("弱项专练") == 1, labels
    assert not [c for c in fake.calls if c[0] == "success"], "非双零场景不应出整页空态"


# --- 下限语义已声明（l922-123 的现状桩按预告改写）------------------------------------------------

def test_下限语义已标出_到期侧仍是页内条数而错题侧是全量真数(monkeypatch):
    """l922-123 的现状桩（原名 `test_现状桩_到期复习是页内条数而错题是全量条数`）翻转版。

    该例当时钉的是"文案把下限读起来像真值"这条**在册缺陷**，并预告
    「改成 COUNT 口径时会主动红」。l923-20 走的是 l922-123 给的**第二条出口**
    （文案标下限语义），所以：
      · **不对称本身没变**：`dao.get_due_reviews(limit=50)` → `core/progress.py:397-406`
        的 SQL 带 `LIMIT ?` ⇒ 真数在库侧丢掉；`list_mistakes()`（:201-215）不带 LIMIT ⇒ 全量真数。
        到期真数 >50 时汇总行的到期侧仍是**下限**，这一点本例继续钉住；
      · **变的是字面**：汇总行到期侧从「到期复习 N 道」改成「最近 50 条内到期复习 N 道」，
        把"这是被 50 截断的读数"写进用户看得见的文案里，不再需要点进去才发现。
    因此本例从「登记缺陷」转成钉两条正面事实：① 文案已标下限；② 查询参数一字未动
    （`limit=50` 原样 ⇒ COUNT 伴生查询那条出口没被顺手实装，仍待人工裁决）。
    将来若实装 COUNT 真数口径，本例会红——那是预期的第二次翻转。

    l924-09 注记（**第二次翻转没有发生，是设计而非漏改**）：伴生查询确已实装，但它落在
    汇总行**下方的另一行** `st.caption` 上，汇总行到期侧与 `limit=50` 都没换成真数口径
    ⇒ 本例的三条断言原样成立。真数那一行由下面的新增例钉，不并入本例（保持本例的
    期望值集合与 l924-08 交付时逐字相同）。本桩里 `due_total` 缺省==页内条数 ⇒ 打满也不出提示行。
    """
    fake, summary, labels = _body(monkeypatch, _mk(60, "wrong"), _mk(50, "due"))
    assert summary == "**错题 60 道 · 最近 50 条内到期复习 50 道**", summary
    assert "最近 50 条" in summary, "下限语义标记被摘掉了：50 会被读成到期总量"
    assert "错题 60 道" in summary, "错题侧是真值，不该带上下限字样"
    # 标签侧（:93-98）自 l924-08 起也带下限标记：到期侧「· 至多」、错题侧无。
    # （l923-20 把这一处留给文案裁量，本单采纳"标"那条出口；page_cap==50 跨源断言未动。）
    assert labels == ["到期复习 (50 · 至多)", "错题重做 (60)", "弱项专练"], labels
    dao = fake.dao
    assert dao.get_due_reviews.call_args.kwargs == {"limit": 50}, dao.get_due_reviews.call_args
    assert dao.list_mistakes.call_args.kwargs == {}, dao.list_mistakes.call_args


# --- COUNT(*) 伴生查询（l924-09 新增，全部为净增量例，未回改上方任何既有例）-----------------------

def test_打满且真数更大_汇总行下方补一行真数提示(monkeypatch):
    """真数 >50 ⇒ 汇总行下方多一行「实际到期共 N 道」，且**不顶替**任何既有读数。"""
    fake, summary, labels = _body(monkeypatch, _mk(3, "wrong"), _mk(50, "due"), due_total=137)
    hints = _due_total_hints(fake)
    assert len(hints) == 1, f"真数提示应恰好一行，实为 {hints}"
    assert hints[0] == "实际到期共 137 道 · 上面只列出最先到期的 50 道", hints[0]
    # 同屏三个数各司其职：汇总行仍是页内条数，标签仍是带上限标记的页内条数，只有新行是真数。
    assert summary == "**错题 3 道 · 最近 50 条内到期复习 50 道**", summary
    assert labels == ["到期复习 (50 · 至多)", "错题重做 (3)", "弱项专练"], labels


def test_未打满_不查真数也不出提示行(monkeypatch):
    """未打满 ⇒ 真数恒等于页内条数，多问一次 COUNT 纯属浪费，多写一行纯属重复。"""
    fake, _, _ = _body(monkeypatch, _mk(3, "wrong"), _mk(5, "due"), due_total=999)
    dao = fake.dao
    assert dao.get_due_reviews_total.called is False, "未打满时不该发伴生查询"
    assert _due_total_hints(fake) == [], "未打满时不该出现真数提示行（999 是故意给的诱饵值）"


def test_打满但真数恰等页内条数_查了而不提示(monkeypatch):
    """页打满而真数==50：伴生查询要发（否则测不出"提示"与"查询"两道闸），但不许出行。"""
    fake, _, _ = _body(monkeypatch, [], _mk(50, "due"), due_total=50)
    dao = fake.dao
    assert dao.get_due_reviews_total.call_count == 1, dao.get_due_reviews_total.call_args_list
    assert _due_total_hints(fake) == [], "真数没超过页内条数却说「实际到期共 50 道」是重复信息"


# --- 伴生查询的 SQL 侧（真库沙盒，钉"谓词与页查询同源"）--------------------------------------------

def _mk_dao(tmp_path, due, future):
    """往 tmp_path 沙盒库里写 due 条已到期 + future 条未到期复习，返回 DAO。

    用真库而不是桩：本段要钉的是 **SQL 谓词**，桩件里 COUNT 永远等于我喂进去的长度、
    测不出漏写 WHERE 这类错。到期日含**恰等于今天**这一条（`<=` 的闭区间边界）。
    """
    from datetime import date, timedelta
    from core.progress import ProgressDAO
    dao = ProgressDAO(str(tmp_path / "due_total.db"))
    today = date.today()
    with dao.conn:
        for i in range(due):
            days = 0 if i == 0 else (i % 30) + 1  # i==0 ⇒ 恰等于今天（边界）
            due_date = (today - timedelta(days=days)).isoformat()
            dao.conn.execute(
                "INSERT INTO review_state (lang, problem_id, interval_days, ease, review_streak, "
                "next_due_date, last_result) VALUES (?,?,?,?,?,?,?)",
                ("python", f"due_{i}", 3, 2.0, 1, due_date, "pass"),
            )
        for i in range(future):
            due_date = (today + timedelta(days=i + 1)).isoformat()
            dao.conn.execute(
                "INSERT INTO review_state (lang, problem_id, interval_days, ease, review_streak, "
                "next_due_date, last_result) VALUES (?,?,?,?,?,?,?)",
                ("python", f"future_{i}", 3, 2.0, 1, due_date, "pass"),
            )
    return dao


def test_dao_伴生查询与页查询同谓词_只去掉LIMIT(tmp_path):
    """60 条已到期 + 20 条未到期 ⇒ 真数 60、页内 50，两者谓词同源。"""
    dao = _mk_dao(tmp_path, due=60, future=20)
    try:
        assert dao.get_due_reviews_total() == 60
        assert len(dao.get_due_reviews(limit=50)) == 50, "页侧仍被 LIMIT 截断（本单没动它）"
        # 同源判据：把 limit 抬到真数之上，两侧必须落在同一个数上
        assert len(dao.get_due_reviews(limit=1000)) == dao.get_due_reviews_total() == 60
    finally:
        dao.close()


def test_dao_无到期时真数为零(tmp_path):
    """空库/全未到期 ⇒ COUNT 返回 0（整数而非 None，页面侧要拿它做 > 比较）。"""
    dao = _mk_dao(tmp_path, due=0, future=5)
    try:
        total = dao.get_due_reviews_total()
        assert total == 0, total
        assert isinstance(total, int) and total is not None
    finally:
        dao.close()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
