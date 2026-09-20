# -*- coding: utf-8 -*-
"""core/report._build_goals 分支钉桩（l920-06）。

纯函数直测：不建库、不碰 progress.db、零生产码改动。
锚点 l920-06：src/core/report.py:69 def _build_goals(report) —— tests/test_report.py 6 例未覆盖本符号。

分支覆盖（现测值，照现状翻桩）：
  ① grand_wrong>0        → 「清理 N 道错题……」
  ② weak_topics 非空     → 「重点攻克 **X** 知识点（做 3-5 道相关题）」
  ③ streak==0            → 「恢复每日打卡……」
  ③' 0<streak<7          → 「保持打卡到 7 天连续（当前 N 天）」
  ③'' streak>=7          → 「保持优秀节奏，当前连续 N 天」
  ④ due_reviews>0        → 「完成 N 道到期复习题」
  末尾 goals[:3] 硬截断；④ 在满配时恒被丢弃。
"""
from core.report import _build_goals


def _report(**kw):
    """最小报告骨架：只放 _build_goals 真正读的键。"""
    base = {"grand_wrong": 0, "weak_topics": [], "streak": 0, "due_reviews": 0}
    base.update(kw)
    return base


def test_空报告_只出打卡恢复一条():
    goals = _build_goals(_report())
    assert goals == ["恢复每日打卡——哪怕只做 1 道题也比断连好"], f"空报告目标漂移：{goals}"


def test_满报告_五候选取前三():
    report = _report(grand_wrong=12, weak_topics=[("python/19_regex", 3.75)],
                     streak=21, due_reviews=8)
    goals = _build_goals(report)
    assert len(goals) == 3, f"满报告应被截断成 3 条，实得 {len(goals)}：{goals}"
    assert goals[0] == "清理 12 道错题——错题是最高效的学习材料"
    assert goals[1] == "重点攻克 **python/19_regex** 知识点（做 3-5 道相关题）"
    assert goals[2] == "保持优秀节奏，当前连续 21 天"
    # ④ due_reviews 在满配下被 [:3] 丢弃——显式钉住这个「静默丢目标」行为
    assert not any("到期复习" in g for g in goals),         f"截断契约破裂：到期复习目标不该挤进前 3：{goals}"


def test_到期复习_在空槽位时可见():
    """①②③ 都不产出时，④ 才排得进前 3。"""
    goals = _build_goals(_report(streak=7, due_reviews=5))
    assert goals == ["保持优秀节奏，当前连续 7 天", "完成 5 道到期复习题"], f"目标漂移：{goals}"
    # 注：③ 恒产出一条（三个分支互斥且穷尽），故 ④ 最多只能到第 2 位
    assert len(goals) <= 3


def test_streak边界_0_6_7三档():
    assert _build_goals(_report(streak=0))[0] == "恢复每日打卡——哪怕只做 1 道题也比断连好"
    assert _build_goals(_report(streak=6))[0] == "保持打卡到 7 天连续（当前 6 天）"
    assert _build_goals(_report(streak=7))[0] == "保持优秀节奏，当前连续 7 天"
    # streak==6 与 ==7 是分界（<7 而非 <=7）
    assert "保持打卡到 7 天连续" in _build_goals(_report(streak=6))[0]
    assert "保持优秀节奏" in _build_goals(_report(streak=7))[0]


def test_弱项只取第一名_且缺due_reviews键不炸():
    report = _report(weak_topics=[("a/1", 9.0), ("b/2", 8.0), ("c/3", 7.0)])
    goals = _build_goals(report)
    assert goals[0] == "重点攻克 **a/1** 知识点（做 3-5 道相关题）", f"弱项取首名口径漂移：{goals}"
    assert "b/2" not in "".join(goals) and "c/3" not in "".join(goals), "弱项只应取 top1"
    # due_reviews 用 .get 兜底：缺键 → 不抛 KeyError（与 grand_wrong 等硬下标不同）
    del report["due_reviews"]
    assert _build_goals(report) == goals, "缺 due_reviews 键应等价于 0"
