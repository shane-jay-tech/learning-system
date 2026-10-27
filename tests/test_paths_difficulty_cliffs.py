"""难度断崖/平台阈值分布下限桩（l1002-83，l922-11 遗留契约化）。

**口径声明（断言注释即契约）**：
- 曲线纵轴 = 里程碑 topics 下全部题目 difficulty 的 **mean**（非 max——换 max 口径时
  quick_stats 的平台期会消失、agent_mastery 的 a7 会读成孤峰，矿源 l922-11 明令写死）。
- 断崖 = 相邻里程碑 mean 差 >= 0.6；平台 = 相邻 mean 差 < 0.25。两阈值是 l922-11
  为「可读」自定的显示口径（非仓内既有契约），本桩把「现值分布」钉成下限——
  改阈值须先改本文件并复算，不得静默换口径。

桩的形态：钉**全路径分布的计数区间**（分子分母绑磁盘实取，同 test_content_difficulty_pins 风格），
不锁具体题目、不判难度数值该多少（内容域红线）。
"""
import glob
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CLIFF = 0.6    # 断崖阈值（mean 差 >= 0.6）
PLATEAU = 0.25  # 平台阈值（mean 差 < 0.25）
PATHS_DIR = ROOT / "content" / "paths"


def milestone_means(pid: str, content_root: Path = None) -> list:
    """里程碑 difficulty mean 序列（磁盘实取，None 表示空专题）。"""
    root = content_root or (ROOT / "content")
    yaml_path = (PATHS_DIR / f"{pid}.yaml") if content_root is None else (content_root / "paths" / f"{pid}.yaml")
    d = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    means = []
    for m in d["milestones"]:
        vals = []
        for t in m["topics"]:
            lang, _, slug = t.partition("/")
            for f in glob.glob(str(root / lang / slug / "*.yaml")):
                q = yaml.safe_load(Path(f).read_text(encoding="utf-8"))
                vals.append(int(q.get("difficulty", 1)))
        means.append(sum(vals) / len(vals) if vals else None)
    return means


def cliff_plateau_counts(means: list) -> tuple:
    """返回 (断崖计数, 平台计数)——mean 口径。"""
    cliffs = plateaus = 0
    pairs = [(a, b) for a, b in zip(means, means[1:]) if a is not None and b is not None]
    for a, b in pairs:
        if a - b >= CLIFF:
            cliffs += 1
        if abs(a - b) < PLATEAU:
            plateaus += 1
    return cliffs, plateaus


def test_断崖平台计数在现值分布区间内():
    """分布下限桩：六路径的断崖/平台计数钉在现值区间（l922-11 实测形状）。"""
    # l922-11 实测形状（mean 口径）：quick_stats 无断崖双平台；agent_mastery 两断崖三平台。
    qs = milestone_means("quick_stats")
    qc, qp = cliff_plateau_counts(qs)
    assert (qc, qp) == (0, 3), f"quick_stats 断崖/平台 = {(qc, qp)}，契约形状 (0, 3)（l1028-05 翻钉：14_sem/15_cfa 4 档题抬升里程碑 mean，平台 2→3）"

    am = milestone_means("agent_mastery")
    ac, ap = cliff_plateau_counts(am)
    assert (ac, ap) == (1, 3), f"agent_mastery 断崖/平台 = {(ac, ap)}，契约形状 (1, 3)（l1028-05 翻钉：07/08/10 三题升 4 档抹平一段断崖，2→1）"

    # 全六路径总量的下限（不设上限——内容建设可新增断崖/平台，破坏既有形状才是红）
    total_cliffs = total_plateaus = 0
    paths = 0
    for yml in sorted(glob.glob(str(PATHS_DIR / "*.yaml"))):
        pid = Path(yml).stem
        paths += 1
        c, p = cliff_plateau_counts(milestone_means(pid))
        total_cliffs += c
        total_plateaus += p
    assert paths == 6, f"path 数应为 6，实得 {paths}"
    assert total_cliffs >= 1, f"全路径断崖计数 {total_cliffs} 低于现值下限 1（l1028-05：quick_stats 0 + agent_mastery 1）"
    assert total_plateaus >= 3, f"全路径平台计数 {total_plateaus} 低于现值下限 3（agent_mastery 段）"
