# -*- coding: utf-8 -*-
"""错题本页 tab 计数标签与空态文案的契约桩（l922-123）。

钉 ui/pages/mistakes.py 的 `_render_mistakes_body`（磁盘实况 :30-63，
任务书锚点 :36/:47 **未漂移**，逐字命中）。这套「计数 → 汇总行 → tab 标签」联动此前无 UI 桩
（`tests/test_mistakes_edges.py` 只测 `_render_due_reviews` 的行内细节）：

- :36 `st.markdown(f"**错题 {wrong_count} 道 · 到期复习 {overdue_count} 道**")` —— 汇总行无条件先出
- :38-40 双零 ⇒ 整页 `st.success` 空态并 **return**（一个 tab 都不建）
- :42-47 标签按 `if overdue_count:` / `if wrong_count:` 条件追加，`"弱项专练"` 恒在且排最后
- :49 `st.tabs(tab_labels)` 的返回下标靠 :52-63 的 `tab_idx` 手动对齐 —— 标签与索引是**两处独立推导**，
  任一侧改条件而另一侧没跟上就会串 tab（本桩用「标签序列 == 期望序列」整序断言把它锁住）

DAO 与 `_lookup_problem` 全部打桩，**不触真实题库**（`_problem_lookup_cache` 的失效通道属
l922-119 待裁决项，本单不依赖也不实装）。只加测试，不改页面代码。
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import app  # noqa: F401  # 与 test_ui_behavior 同桩模式：app 侧 import 预绑定 st
import ui.components as components
import ui.pages.mistakes as mistakes_page
from tests.test_ui_behavior import Context, FakeStreamlit

SUMMARY_PREFIX = "**错题 "


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
    """造 n 条假记录；字段覆盖 :69-91（due）与 :96-117（mistake）实际读到的键。"""
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


def _body(monkeypatch, mistakes, reviews):
    """渲染 `_render_mistakes_body`，返回 (fake, 汇总行文本, tab 标签序列或 None)。"""
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
    dao.close.return_value = None
    fake.dao = dao  # 供「取数口径」类断言回看调用实参
    mistakes_page._render_mistakes_body(dao)
    summary = [str(a[0]) for name, a, _ in fake.calls if name == "markdown"
               and str(a[0]).startswith(SUMMARY_PREFIX)]
    assert len(summary) == 1, f"汇总行应恰好一条，实为 {summary}"
    labels = [c[1][0] for c in fake.calls if c[0] == "tabs"]
    assert len(labels) <= 1, f"tabs 至多调一次，实为 {len(labels)}"
    return fake, summary[0], (labels[0] if labels else None)


# --- 三场景（任务书点名）+ 第四场景（只有到期）------------------------------------------------

def test_双零_整页走success空态且不建任何tab(monkeypatch):
    fake, summary, labels = _body(monkeypatch, [], [])
    assert summary == "**错题 0 道 · 到期复习 0 道**", summary
    assert labels is None, ":38-40 双零分支必须 return，不能走到 st.tabs"
    succ = [str(a[0]) for name, a, _ in fake.calls if name == "success"]
    assert succ == ["没有错题也没有到期复习，做得不错！"], succ
    assert not [c for c in fake.calls if c[0] == "markdown"
                and "弱项专练" in str(c[1][0])], "空态下不该渲染任何分区"


def test_只有错题_标签两级且无到期复习项(monkeypatch):
    _, summary, labels = _body(monkeypatch, _mk(2, "wrong"), [])
    assert labels == ["错题重做 (2)", "弱项专练"], labels
    assert summary == "**错题 2 道 · 到期复习 0 道**", summary


def test_双有_到期复习在前错题在后弱项收尾(monkeypatch):
    _, summary, labels = _body(monkeypatch, _mk(3, "wrong"), _mk(5, "due"))
    assert labels == ["到期复习 (5)", "错题重做 (3)", "弱项专练"], labels
    assert summary == "**错题 3 道 · 到期复习 5 道**", summary


def test_只有到期_标签两级且无错题项(monkeypatch):
    _, summary, labels = _body(monkeypatch, [], _mk(4, "due"))
    assert labels == ["到期复习 (4)", "弱项专练"], labels
    assert summary == "**错题 0 道 · 到期复习 4 道**", summary


# --- 计数-标签联动契约（跨场景泛化）--------------------------------------------------------------

@pytest.mark.parametrize("n_wrong,n_due", [(0, 1), (1, 0), (1, 1), (7, 13), (0, 50), (1, 2)])
def test_汇总行数字与tab标签数字逐值相等(monkeypatch, n_wrong, n_due):
    """:36 汇总行与 :44/:46 标签里的数字必须同源 —— 两处各写一遍，是最容易漂的一对。"""
    import re
    fake, summary, labels = _body(monkeypatch, _mk(n_wrong, "wrong"), _mk(n_due, "due"))
    s_wrong, s_due = (int(x) for x in re.findall(r"\d+", summary))
    assert (s_wrong, s_due) == (n_wrong, n_due), summary
    tag = {}
    for lb in labels:
        m = re.match(r"(.+) \((\d+)\)$", lb)
        if m is None:
            assert lb == "弱项专练", f"唯一不带计数的标签应是弱项专练，实为 {lb}"
            continue
        tag[m.group(1)] = int(m.group(2))
    assert tag.get("错题重做", 0) == s_wrong, (tag, summary)
    assert tag.get("到期复习", 0) == s_due, (tag, summary)
    # 汇总为 0 的那一侧，标签里就不该出现同名项（条件追加语义）
    assert ("错题重做" in tag) == (s_wrong > 0), (tag, summary)
    assert ("到期复习" in tag) == (s_due > 0), (tag, summary)
    assert labels[-1] == "弱项专练", f"弱项专练须恒在且收尾：{labels}"
    assert labels.count("弱项专练") == 1, labels
    assert not [c for c in fake.calls if c[0] == "success"], "非双零场景不应出整页空态"


# --- 现状桩（登记缺陷，不改码）--------------------------------------------------------------------

def test_现状桩_到期复习是页内条数而错题是全量条数(monkeypatch):
    """:31-34 两侧计数口径**不同源**：到期侧被页面写死的 `limit=50` 截断，错题侧无 LIMIT。

    - `dao.get_due_reviews(limit=50)` → `core/progress.py:397-406` 的 SQL 带 `LIMIT ?`，
      真数在库侧就被丢掉，页面只能拿页内条数当计数；
    - `dao.list_mistakes()` → `core/progress.py:201-215` 的 SQL **不带 LIMIT** ⇒ 全量真数。

    ⇒ 到期真数 >50 时，汇总行与标签里的「到期复习 N 道」是**下限**不是真值，
    而同一行的「错题 M 道」是真值。本例钉住这个不对称（改成 COUNT 口径时会主动红）。
    """
    fake, summary, labels = _body(monkeypatch, _mk(60, "wrong"), _mk(50, "due"))
    assert summary == "**错题 60 道 · 到期复习 50 道**", summary
    assert labels == ["到期复习 (50)", "错题重做 (60)", "弱项专练"], labels
    dao = fake.dao
    assert dao.get_due_reviews.call_args.kwargs == {"limit": 50}, dao.get_due_reviews.call_args
    assert dao.list_mistakes.call_args.kwargs == {}, dao.list_mistakes.call_args


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
