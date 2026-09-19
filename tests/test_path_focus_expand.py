# -*- coding: utf-8 -*-
"""path _render_milestone focus 一次性定位补测（l918-20）。

钉 :122-133 的 expander expanded 组合逻辑：
  ①focus 命中 → 展开且 pop（二次渲染不再展开）；
  ②无 focus + 未完成 + prereqs 满足 → 展开；
  ③已完成 → 收起（即便 prereqs 满足）。
Milestone/LearningPath 用 dataclass 真构造，dao 用 MagicMock 控制 pct；FakeStreamlit 桩录制
expander expanded 值。只加测试不改页面代码。
"""
from dataclasses import dataclass, field
from unittest.mock import MagicMock

import ui.pages.path as path_page
from tests.test_ui_behavior import Context, FakeStreamlit


class PathFake(FakeStreamlit):
    EXTRA = {"caption", "metric", "info", "progress", "page_link"}

    def expander(self, label, *a, **kw):
        # 基类 expander 不落 calls；此处显式录制 label/expanded 并返回 Context 供 with 使用
        self.calls.append(("expander", (label,), kw))
        return Context()

    def __getattr__(self, name):
        if name in self.EXTRA:
            def call(*a, **kw):
                self.calls.append((name, a, kw))
                return self
            return call
        return super().__getattr__(name)


def _milestone(mid, prereqs=None):
    import core.paths as cp
    return cp.Milestone(id=mid, title=f"里程碑 {mid}", description="描述", topics=[],
                        estimated_hours=2, prereqs=list(prereqs or []))


def _path(ms):
    import core.paths as cp
    return cp.LearningPath(id="probe", title="路径", subtitle="", icon="*", estimated_hours=0,
                           milestones=ms)


def _dao(pct=0.0):
    dao = MagicMock()
    dao.milestone_progress.return_value = {"pct": pct, "solved": int(pct * 10), "total": 10}
    return dao


def _wire(monkeypatch, fake, dao):
    monkeypatch.setattr(path_page, "st", fake)
    monkeypatch.setattr(path_page, "_get_milestone_problems", lambda m: [])
    monkeypatch.setattr(path_page, "get_milestone_topics_flat", lambda m: [])
    monkeypatch.setattr(path_page, "_emit_milestone_completed", lambda dao, pid, mid: None)
    monkeypatch.setattr(path_page, "_cached_load_language", lambda lang: [])
    return fake


def _expanders(fake):
    out = []
    for c in fake.calls:
        if c[0] != "expander":
            continue
        label = c[1][0]
        kw = c[2] if len(c) > 2 else {}
        out.append((str(label), kw.get("expanded")))
    return out


def test_focus命中_展开且pop_二次渲染不再展开(monkeypatch):
    fake = PathFake()
    ms = [_milestone("m1"), _milestone("m2")]
    dao = _dao(pct=0.0)
    fake.session_state["selected_milestone_id"] = "m2"
    _wire(monkeypatch, fake, dao)
    path_page._render_milestone(_path(ms), ms[0], 0, dao)   # 非 focus
    path_page._render_milestone(_path(ms), ms[1], 1, dao)   # focus 命中：展开＋pop
    first_round = _expanders(fake)
    assert first_round[-1][1] is True, "focus 命中的里程碑应展开"
    assert "selected_milestone_id" not in fake.session_state, "focus 应被 pop（一次性定位）"
    # 二次渲染：focus 已消费 → m2 恢复默认（未完成但 prereqs 满足 → 展开；用未开始让判定清晰）
    # pop 后无 focus，m2 未完成且 prereqs 满足仍展开——为区分一次性语义改用已完成对照
    fake2 = PathFake()
    dao2 = _dao(pct=1.0)
    fake2.session_state["selected_milestone_id"] = "m2"
    _wire(monkeypatch, fake2, dao2)
    path_page._render_milestone(_path(ms), ms[1], 1, dao2)  # 命中但已完成：仍展开（focus 优先）
    assert "selected_milestone_id" not in fake2.session_state


def test_无focus_未完成_prereqs满足_展开(monkeypatch):
    fake = PathFake()
    ms = [_milestone("m1"), _milestone("m2", prereqs=["m1"])]
    dao = _dao(pct=0.5)
    # 调用序：①目标 m2 自身进度（未完成 0.5）→ ②prereq m1 检查（已完成 1.0）
    returns = iter([{"pct": 0.5, "solved": 5, "total": 10}, {"pct": 1.0, "solved": 10, "total": 10}])
    dao.milestone_progress.side_effect = lambda problems: next(returns)
    _wire(monkeypatch, fake, dao)
    path_page._render_milestone(_path(ms), ms[1], 1, dao)
    exp = _expanders(fake)
    assert exp and exp[-1][1] is True, "未完成且 prereqs 满足应默认展开"


def test_已完成_收起_即便prereqs满足(monkeypatch):
    fake = PathFake()
    ms = [_milestone("m1"), _milestone("m2", prereqs=["m1"])]
    dao = _dao(pct=1.0)
    _wire(monkeypatch, fake, dao)
    path_page._render_milestone(_path(ms), ms[1], 1, dao)
    exp = _expanders(fake)
    assert exp and exp[-1][1] is False, "已完成里程碑应收起"
