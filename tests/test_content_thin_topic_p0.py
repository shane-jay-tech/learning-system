# -*- coding: utf-8 -*-
"""薄 topic 结构哨兵：P0 四目录现状 + topic 级题量下限（l922-128，2026-09-22）。

上游：`docs/insights/learn-thin-thick-topics-20260921.md` §四 P0 两行给出四个落点目录
（`cpp/01_io_and_vars` 2→5、`cpp/02_branch_loop` 3→5、`python/20_numpy_basics` 3→5、
`python/21_datetime_ts` 3→5；净增 9 题，399→408）。

**本单没有补题**：题面与 `expected_output` 属新增教学内容，执行班没有权威素材来源时不得代造
（内容正确性红线；缺什么素材、三处口径联动清单见 `zcode-bridge/outbox/l922-128-thin-topics-fill.result.md`）。
本文件补的是 l922-07 遗留 2 点名的结构缺口——「现 `tests/test_content_census.py` 只在**题**级断言，
无 topic 级」，把「补题这件事发生时哪些口径必须同步」变成可 diff 的红。

判据风格沿用 `tests/test_paths_reconcile.py`（l922-125）与 `tests/test_paths_coverage.py`：
绑磁盘实取、比例式、不锁会随内容自然增长的条目魔数；三个阈值常量的现值与取数命令逐条写在就近注释里。

取数口径（全部经 `core.loader` / `core.paths` 从磁盘实算，不引文档数字）：
    PYTHONIOENCODING=utf-8 python -c "from core.loader import load_language; \
    import collections; c={f'{lg}/{t.slug}': len(t.problems) \
    for lg in ('python','sql','cpp','r','agent_dev') for t in load_language(lg)}; \
    print(len(c), sum(c.values()), dict(sorted(collections.Counter(c.values()).items())))"
2026-09-22 @ HEAD 157d201 实算：85 topic / 399 题，题数直方 {2:4, 3:8, 4:10, 5:55, 6:6, 8:2}，众数 5。

复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_content_thin_topic_p0.py -q
只读题库（零写库、零 yaml 改动、零网络、零 session_state）。
"""
import collections

from core.loader import load_language
from core.paths import load_all_paths

LANGS = ("python", "sql", "cpp", "r", "agent_dev")

# l922-07 §四 P0 两行的四个落点（key = "lang/slug"，磁盘实取）
P0_DIRS = (
    "cpp/01_io_and_vars",
    "cpp/02_branch_loop",
    "python/20_numpy_basics",
    "python/21_datetime_ts",
)

# 2026-09-22 现状快照：目录 -> 该目录各题 difficulty（升序）。
# 补题即红**是设计意图**（与 tests/test_content_difficulty_pins.py 的 PINNED_HIST 同构），
# 目的是逼改动者在同一提交里同步下列口径（2026-09-22 全仓 grep「399」实取，共 3 处等值 + 1 处直方）：
#   1) tests/test_content_difficulty_pins.py 的 PINNED_HIST（逐语言 1-5 档题数直方）
#   2) 同文件 :80 `assert sum(per_lang.values()) == 399`
#   3) tests/test_content_census.py:27 `assert total == 399`
#   4) README.md:52 对外口径「399 题、85 知识点、6 条学习路径」
# 另 tests/test_scripts.py:310 是 `total_problems >= 399` 下界护栏，补题无需改它。
# 若新题难度全 <=3，则 PINNED_TOP_TIER 不动（见 test_content_difficulty_pins.py 的 >=4 名单桩）。
P0_SNAPSHOT = {
    "cpp/01_io_and_vars": [1, 2],
    "cpp/02_branch_loop": [1, 2, 2],
    "python/20_numpy_basics": [2, 3, 4],
    "python/21_datetime_ts": [2, 3, 4],
}

# 结构下限：现值全仓 topic 题数最小 2（直方 2 档有 4 个目录），掉到 1 说明新建目录只放了题占位
MIN_QUESTIONS_PER_TOPIC = 2

# 非薄（题数 >= 全仓众数）占比下界：现值 63/85 = 74.1%（众数 5，薄 22 个）。
# 0.72 留 1 个目录的余量：全仓再多出 2 个薄目录即红，补题让它变厚只会更宽松。
NON_THIN_RATIO_FLOOR = 0.72

# 里程碑层面「题/标称小时」下界：现值最稀 = 1.667（cpp_foundation:c1 5题/3h 与
# people_analytics:m4 5题/3h **并列最稀**——l922-07 §四称 c1「全仓最稀」，实测是并列，此处按实况登记）。
# 补题后此值只会上升（c1 补满 → 3.33），1.6 这道下限不会挡路；它挡的是「里程碑变得更稀」。
MILESTONE_Q_PER_HOUR_FLOOR = 1.6


def _difficulty_by_topic():
    """{lang/slug: [difficulty 升序]}，全部从 core.loader 实取。"""
    return {
        f"{lang}/{topic.slug}": sorted(p.difficulty for p in topic.problems)
        for lang in LANGS
        for topic in load_language(lang)
    }


def _modal_count(sizes):
    """题数众数；并列时取**较小**者（薄集合随之变小，判据偏保守不误伤）。"""
    hist = collections.Counter(sizes)
    top = max(hist.values())
    return min(size for size, n in hist.items() if n == top)


def _below_floor(counts, floor=MIN_QUESTIONS_PER_TOPIC):
    """返回题数低于 floor 的目录名（纯函数，供合成自检复用）。"""
    return sorted(name for name, qs in counts.items() if len(qs) < floor)


def _non_thin_ratio_ok(counts, floor=NON_THIN_RATIO_FLOOR):
    """(是否达标, 非薄数, 总数, 众数)；薄 = 题数 < 全仓众数。"""
    if not counts:
        return True, 0, 0, 0
    sizes = [len(qs) for qs in counts.values()]
    mode = _modal_count(sizes)
    non_thin = sum(1 for n in sizes if n >= mode)
    return non_thin >= floor * len(sizes), non_thin, len(sizes), mode


def _milestone_densities(counts):
    """[(题/小时, 'path:milestone')]，分子取磁盘题数、分母取 paths yaml 的 estimated_hours。"""
    sizes = {name: len(qs) for name, qs in counts.items()}
    out = []
    for path in load_all_paths():
        for ms in path.milestones:
            if not ms.estimated_hours:
                continue
            questions = sum(sizes.get(t, 0) for t in ms.topics)
            out.append((questions / ms.estimated_hours, f"{path.id}:{ms.id}"))
    return out


def test_P0四目录现状_钉死难度多重集():
    """现状快照：四个 P0 目录的题数与难度多重集逐一对账（磁盘实算见模块 docstring）。

    变红的唯一正确响应是「补题的那位把三处口径一起改了」（见 P0_SNAPSHOT 注释），
    而不是把本断言放宽。cpp 侧尤其注意 tests/test_content_difficulty_pins.py::
    test_cpp_无4到5档_是现状而非用例失效 仍钉着 cpp 末档=3，补的 cpp 题难度须 <=3。
    """
    live = _difficulty_by_topic()
    assert {k: live.get(k) for k in P0_DIRS} == P0_SNAPSHOT, (
        "P0 薄目录题量/难度已变动：请同批改 PINNED_HIST ＋ 两处 `== 399` 等值断言 ＋ README:52"
        "（完整同步清单见本文件 P0_SNAPSHOT 注释），"
        "并把本快照与 docs/insights/learn-thin-thick-topics-20260921.md 的落点表一起刷新"
    )


def test_topic级题量下限_全仓无单题目录():
    """topic 级下限桩（l922-07 遗留 2 点名的缺口）：任何目录至少 2 题。"""
    offenders = _below_floor(_difficulty_by_topic())
    assert offenders == [], f"以下 topic 题数低于 {MIN_QUESTIONS_PER_TOPIC}：{offenders}"


def test_非薄topic占比_比例式下界():
    """失衡不得恶化：非薄（题数 >= 众数）目录占比 >= NON_THIN_RATIO_FLOOR。

    分子分母都绑磁盘实取，众数本身也算出来——补题只会更宽松，新造薄目录才会红。
    """
    live = _difficulty_by_topic()
    ok, non_thin, total, mode = _non_thin_ratio_ok(live)
    assert ok, (
        f"薄 topic 失衡恶化：非薄 {non_thin}/{total} = {non_thin / total:.1%} "
        f"低于下界 {NON_THIN_RATIO_FLOOR:.0%}（全仓题数众数 {mode}）"
    )


def test_里程碑题时密度_下限绑磁盘():
    """里程碑层面「题/标称小时」>= MILESTONE_Q_PER_HOUR_FLOOR（现值最稀 1.667）。"""
    densities = _milestone_densities(_difficulty_by_topic())
    assert densities, "paths 未取到任何里程碑（口径失效，非真绿）"
    worst = min(densities)
    assert worst[0] >= MILESTONE_Q_PER_HOUR_FLOOR, (
        f"里程碑 {worst[1]} 题时密度降到 {worst[0]:.2f}，低于下限 "
        f"{MILESTONE_Q_PER_HOUR_FLOOR}（2026-09-22 现值最稀 1.667 @ cpp_foundation:c1 / people_analytics:m4）"
    )


def test_哨兵有牙_合成劣化必红而补齐不红():
    """自证三条下限不是永绿：喂合成 counts，劣化必须被拒、补齐必须放过。"""
    base = _difficulty_by_topic()
    mode = _modal_count([len(qs) for qs in base.values()])

    # ① 新增一个单题目录 → 下限桩必须抓到
    one = dict(base, **{"cpp/99_synthetic_single": [1]})
    assert _below_floor(one) == ["cpp/99_synthetic_single"]
    assert _below_floor(base) == []

    # ② 把 3 个原本非薄的目录削成 2 题 → 比例桩必须红（劣化方向）
    worsened = dict(base)
    for i, (name, qs) in enumerate(sorted(base.items())):
        if len(qs) >= mode and i < 3:
            worsened[name] = [2, 2]
    assert _non_thin_ratio_ok(base)[0] is True
    assert _non_thin_ratio_ok(worsened)[0] is False, "比例下界无牙：削薄三个目录仍判绿"

    # ③ 四个 P0 目录补齐到众数 → 两条判据都必须放过（好改动不该红）
    filled = dict(base)
    for name in P0_DIRS:
        filled[name] = [2, 2, 3, 3, mode] if len(base[name]) < mode else base[name]
    assert _below_floor(filled) == []
    assert _non_thin_ratio_ok(filled)[0] is True
    assert min(_milestone_densities(filled))[0] > MILESTONE_Q_PER_HOUR_FLOOR, (
        "补齐后 cpp_foundation:c1 密度应明显抬过下限，否则本桩对补题无感知"
    )
