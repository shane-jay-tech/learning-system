# -*- coding: utf-8 -*-
"""难度分布下限桩：钉住逐语言直方与末档（difficulty>=4）题名单（l922-06，2026-09-21）。

锚点复核（落笔前磁盘实跑，与任务书「背景与锚点」逐条比对）：
  - agent_dev 1×难度5 —— 成立（`agent_dev/11_real_tasks/08_end_to_end`）；
  - cpp 10/31/21（无 4/5 档）—— 成立，且 cpp 总数 62 与三档之和相等；
  - r 仅 1×难度4 —— 成立；sql 1×难度4 —— 成立；
  - `test_content_census.py:37` 只钉 1-5 越界 —— 成立（该函数仅断言 `1 <= d <= 5`）。
  ⇒ 本单锚点零漂移；任务书未列 python 的 4 档题数（实为 7），本桩一并钉上。

为什么值得钉下限（判定结论详见 docs/insights/learn-difficulty-histogram-20260921.md）：
  难度档在下游只有**一个**行为差异面 —— `core/progress.py` 的 SRS ease 惩罚
  （`if difficulty >= 4: ease = max(1.5, ease - 0.1)`，实测位于 progress.py:378）。
  cpp 末档是 3 ⇒ 该分支对 cpp **永久不可达**；sql / r 各只有 1 题可达。
  也就是说末档一旦被无声清零（或被无声灌水），全套件**没有任何用例会红**。
  原 `test_difficulty_落1到5` 只管越界，不管形状，所以这里补形状桩：
  改分布必须是一次可 diff 的有意行为，不能随内容增删漂过去。

只读题库（`core.loader.load_language`），零写库、零源码改动、零网络。
复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_content_difficulty_pins.py -q
"""
import collections

from core.loader import load_language

LANGS = ("python", "sql", "cpp", "r", "agent_dev")

# 2026-09-21 磁盘实算快照（键 = difficulty 1..5，值 = 题数；括号内为该语言总题数）
PINNED_HIST = {
    "python":    {1: 27, 2: 56, 3: 31, 4: 7, 5: 0},    # 121
    "sql":       {1: 12, 2: 22, 3: 19, 4: 1, 5: 0},    # 54
    "cpp":       {1: 10, 2: 31, 3: 21, 4: 0, 5: 0},    # 62
    "r":         {1: 15, 2: 37, 3: 31, 4: 1, 5: 0},    # 84
    "agent_dev": {1: 11, 2: 32, 3: 27, 4: 7, 5: 1},    # 78
}

# 末档（difficulty >= 4）全量题 id 快照；p.id 自带 "<lang>/<slug>/<prob>" 前缀
PINNED_TOP_TIER = {
    4: {
        "python/20_numpy_basics/03_stats_summary",
        "python/21_datetime_ts/03_group_by_month",
        "python/22_hr_model/03_confusion_matrix",
        "python/22_statsmodels/03_significance",
        "python/23_sklearn_advanced/02_feature_importance",
        "python/23_sklearn_advanced/03_pipeline",
        "python/24_real_world_data/04_dept_avg",
        "sql/12_people_analytics/04_never_submitted",
        "r/14_real_world_data/04_group_avg",
        "agent_dev/05_modular_config/07_coupling",
        "agent_dev/07_data_security/04_minimization_case",
        "agent_dev/08_read_code/02_find_bug_mutable",
        "agent_dev/11_real_tasks/05_decompose_feature",
        "agent_dev/11_real_tasks/06_emergency_rollback",
        "agent_dev/12_spec_iteration/05_iterative_refinement",
        "agent_dev/13_multi_round/05_full_iteration",
    },
    5: {"agent_dev/11_real_tasks/08_end_to_end"},
}


def _hist_by_lang():
    out = {}
    for lang in LANGS:
        c = collections.Counter()
        for topic in load_language(lang):
            for p in topic.problems:
                c[p.difficulty] += 1
        out[lang] = {d: c[d] for d in range(1, 6)}
    return out


def test_逐语言难度直方_钉死():
    """形状桩：五语言 1-5 档题数逐格对账。任一档增删题即红。"""
    assert _hist_by_lang() == PINNED_HIST, "难度直方漂移：与 2026-09-21 快照不符（见 insight 表）"


def test_合计399与直方自洽():
    """直方快照本身必须仍指向 README 官方口径 399，防「只改测试不改快照」的空转绿。"""
    per_lang = {lang: sum(h.values()) for lang, h in PINNED_HIST.items()}
    assert sum(per_lang.values()) == 399, per_lang
    live = {lang: sum(h.values()) for lang, h in _hist_by_lang().items()}
    assert live == per_lang, f"语言级题量漂移：{live} != {per_lang}"


def test_分布下限_每语言覆盖1到3档():
    """下限桩（任务书「钉分布下限桩」的字面落点）：
    1-3 档是五语言共同的地基层，任何一格掉到 0 就说明该语言的难度梯度塌了一截。
    4/5 档不在此断言内 —— 它们正是本单普查出的空洞（见下一条）。"""
    hist = _hist_by_lang()
    hollow = [(lang, d) for lang in LANGS for d in (1, 2, 3) if hist[lang][d] == 0]
    assert hollow == [], f"基层难度档空洞：{hollow}"


def test_末档_ge4_题id名单_钉死():
    """末档空洞的正面桩：全库 difficulty>=4 的题只有 17 道，逐 id 钉住。
    新增难题是好事，但必须显式动这个快照（连带 SRS ease 惩罚的可达面一起扩大）。"""
    live = {4: set(), 5: set()}
    for lang in LANGS:
        for topic in load_language(lang):
            for p in topic.problems:
                if p.difficulty >= 4:
                    live[p.difficulty].add(p.id)
    assert live[4] == PINNED_TOP_TIER[4], (
        f"4 档名单漂移 新增={sorted(live[4] - PINNED_TOP_TIER[4])} "
        f"消失={sorted(PINNED_TOP_TIER[4] - live[4])}"
    )
    assert live[5] == PINNED_TOP_TIER[5], (
        f"5 档名单漂移 新增={sorted(live[5] - PINNED_TOP_TIER[5])} "
        f"消失={sorted(PINNED_TOP_TIER[5] - live[5])}"
    )


def test_cpp_无4到5档_是现状而非用例失效():
    """cpp 末档=3 是本单判定的**内容空洞**（不是设计口径），单独钉一条，
    这样将来补 cpp 难题时这条会红，逼改动者回来改判定档而不是默默留着不一致。"""
    cpp = _hist_by_lang()["cpp"]
    assert max(d for d, n in cpp.items() if n > 0) == 3, cpp
    assert cpp[4] == 0 and cpp[5] == 0, f"cpp 末档已变，须同步改 insight 判定：{cpp}"
