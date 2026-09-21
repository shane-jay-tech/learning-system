# -*- coding: utf-8 -*-
"""learning path 双顺序通道一致性跨层钉桩（l922-126）。

两条独立顺序通道（l922-05 遗留 #2 点名、当时判「当前不矛盾」）：
  · 语言页顺序 = core/loader.py:139 `sorted(glob("content/<lang>/*/"))` 的**目录名字典序**；
  · 路径页顺序 = ui/pages/path.py:143 `get_milestone_topics_flat(milestone)` 的 **yaml 列表序**
                 （milestones[].topics 的手写顺序）。
本单从「同一路径内、同一语言的 milestone.topics 相对序应与语言页相对序一致」的严格口径实测：
**当前有 2 处真倒置，均在 python_advanced（p4 / p5）**——清单见
docs/insights/learn-paths-order-consistency-20260922.md。消解它属「重排 yaml 或给专题加显式
order: 字段」的规划决策（会牵动 l922-05 题号语义与 l918-16 / l920 两族锚点），非执行班擅改，
故主断言以 `xfail(strict=True)` 钉住「已知跨层矛盾未消解」：
  · 现状 2 处倒置 → 断言真红，记为 xfailed（不把全量绿基线拉成 failed）；
  · 若规划把顺序改齐 → 断言转绿 → strict xfail 当场报 XPASS＝红，逼着来删这个标记（＝提醒）。
覆盖性由 test_覆盖全部path 独立钉：6 条 path 全部纳入比对，path 集合漂移即红。
零写盘、零生产码改动（只读 load_language / load_all_paths）。
"""
import pytest

from core.loader import load_language
from core.paths import get_milestone_topics_flat, load_all_paths

ALL_PATH_IDS = {
    "agent_mastery", "cpp_foundation", "people_analytics",
    "python_advanced", "quick_stats", "r_advanced",
}


def _loader_slug_order(lang, cache):
    """语言页展示序 = 直接取 core/loader.load_language 的结果。

    刻意不在测试里重跑一遍 sorted(glob)——那会造出与生产通道并存的第二份顺序判据
    （l922-05 取证自纠的同款教训：两套判据会各自漂移）。
    """
    if lang not in cache:
        cache[lang] = [t.slug for t in load_language(lang)]
    return cache[lang]


def _collect_divergences():
    """逐 path → 逐 milestone → 逐语言，比对 yaml 列表序与 loader 字典序的相对次序。

    loader_positions 非单调递增即判为倒置。悬空引用不在本单职责（已由
    tests/test_paths_reconcile.py 钉「0 悬空」），故跳过 loader 里查不到的 slug。
    """
    loader_cache = {}
    divergences = []
    for path in load_all_paths():
        for m in path.milestones:
            by_lang = {}
            for lang, slug in get_milestone_topics_flat(m):  # yaml 列表序
                by_lang.setdefault(lang, []).append(slug)
            for lang, slugs in by_lang.items():
                pos = {s: i for i, s in enumerate(_loader_slug_order(lang, loader_cache))}
                idxs = [pos[s] for s in slugs if s in pos]
                if idxs != sorted(idxs):
                    divergences.append(
                        "%s/%s [%s] yaml=%s loader_pos=%s" % (path.id, m.id, lang, slugs, idxs))
    return divergences


def test_覆盖全部path():
    """覆盖性：6 条 path 全部纳入比对；path 集合漂移（增删/改名）即红。

    取数命令：python -c "from core.paths import load_all_paths; print(len(load_all_paths()))" → 6
    """
    paths = load_all_paths()
    assert len(paths) == 6, f"path 条数漂移（预期 6）：{len(paths)}"
    assert {p.id for p in paths} == ALL_PATH_IDS, "path 集合与本单钉的清单不符"
    # 每条 path 至少有一个 milestone 被真正遍历到（防「空循环所以假绿」）
    seen = {(path.id, m.id) for path in paths for m in path.milestones}
    assert seen, "一个 milestone 都没比对到，本单将假绿"


@pytest.mark.xfail(
    strict=True,
    reason="2 处 yaml 顺序 vs loader 字典序真倒置（python_advanced p4/p5），"
           "属规划域（重排 yaml 或加显式 order: 字段），清单见 "
           "docs/insights/learn-paths-order-consistency-20260922.md",
)
def test_路径内milestone顺序与语言页顺序一致():
    divergences = _collect_divergences()
    assert not divergences, "跨层顺序矛盾清单（%d 处）：%s" % (
        len(divergences), "; ".join(divergences))
