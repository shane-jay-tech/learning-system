"""path 文案守卫桩第一批（l1002-78，l924-19 遗留案乙：P4/P5 钉桩＋P2 在册指认）。

分工留痕（l1002-78 首版曾含 P2，发现 l930-11 tests/test_paths_no_gap_claim.py 已以
**命题级无条件形态**（连 GAP×题数条件都不带）在册且更强 ⇒ 撤本件 P2 避免双桩双维护，
P2 统一以该件为准；本件保留 P4/P5（在册无桩）与 tmp 副本变异框架。

命题与产出档 docs/insights/learn-path-claim-audit-20260924.md §四逐字对应：
- P2 空缺承诺：description/graduation_project 不得在「里程碑实有题数 > 0」时写
  「还没有/暂无/待解锁/待补充/待题目/尚未」（GAP 式）。
- P4 工时自洽：path 顶层 estimated_hours == 各里程碑 estimated_hours 之和。
- P5 被引专题非空：被引用的每个专题在磁盘与 loader 双轨都有题（双轨不等即红）。

P1（数字=磁盘量）/P3（Milestone 序数跨引）**刻意不钉**——A-1/A-2/A-3 人工裁决在册
（档 §三），未清账前钉了当场红（档 §四案甲反向顺序警示）；位置留占位注释。

红线遵守：零 yaml/文案改动；变异自证用 tmp 副本内容根，不动真 content/paths/。
"""
import glob
import os
import shutil
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys_paths = str(ROOT)
if sys_paths not in __import__("sys").path:
    __import__("sys").path.insert(0, sys_paths)

from core.loader import load_language  # noqa: E402

PATHS_DIR = ROOT / "content" / "paths"
GAP = __import__("re").compile(r"还没有|暂无|待解锁|待补充|待题目|尚未")  # P2 空缺承诺

_fields_cache: dict = {}


def per_topic_disk(lang_slug: str, content_root: Path = None) -> int:
    """轨 1 磁盘：content/<lang>/<slug>/*.yaml 计数。"""
    root = content_root or (ROOT / "content")
    return len(glob.glob(str(root / lang_slug / slug_glob(lang_slug) / "*.yaml")))


def slug_glob(slug: str) -> str:
    return slug


def _split(slug: str) -> tuple:
    lang, _, topic = slug.partition("/")
    return lang, topic


def per_topic(slug: str, content_root: Path = None) -> int:
    """双轨：磁盘计数 == loader 运行时计数，缺一轨即红（档 §四 per_topic 原型）。"""
    lang, topic = _split(slug)
    root = content_root or (ROOT / "content")
    disk = len(glob.glob(str(root / lang / topic / "*.yaml")))
    runtime = len(next(t for t in load_language(lang) if t.slug == topic).problems)
    assert disk == runtime, (slug, disk, runtime)
    return disk


def _milestone_fields(ms: dict):
    """P2 的扫描面：description 与 graduation_project 两个自由文本字段。"""
    for fld in ("description", "graduation_project"):
        val = ms.get(fld)
        if isinstance(val, str):
            yield fld, val


def _claims_on(root: Path):
    """对指定内容根跑 P2/P4/P5 三命题；返回 (violations, checked_paths)。
    抽成带 root 参数的纯形态是为了变异自证能用 tmp 副本（不动真 content/paths/）。"""
    violations = []
    checked = []
    for yml in sorted(glob.glob(str(root / "paths" / "*.yaml"))):
        d = yaml.safe_load(Path(yml).read_text(encoding="utf-8"))
        ms = d["milestones"]
        checked.append(Path(yml).name)
        for i, m in enumerate(ms, 1):
            n = sum(per_topic(t, root) for t in m["topics"])
            for fld, val in _milestone_fields(m):
                # P2 空缺承诺
                if GAP.search(val) and n > 0:
                    violations.append(f"P2 {Path(yml).name} m{i} {fld}: 空缺承诺 vs 实有 {n} 题")
                # P1a（占位——A-1/A-2 清账前不钉，见文件头）
                # P3（占位——同上）
        # P4 工时自洽
        total = d.get("estimated_hours")
        ms_sum = sum(m.get("estimated_hours", 0) for m in ms)
        if total is not None and total != ms_sum:
            violations.append(f"P4 {Path(yml).name}: 顶层工时 {total} != 里程碑合计 {ms_sum}")
        # P5 被引专题非空
        for m in ms:
            for t in m["topics"]:
                if per_topic(t, root) <= 0:
                    violations.append(f"P5 {Path(yml).name}: 被引专题无题 {t}")
    return violations, checked


def test_P4_工时自洽_且_P5_被引专题非空():
    """两桩主例（档 §四案乙）：现值全绿、永不自愈、永不改文案。
    P2（GAP 空缺承诺）由 tests/test_paths_no_gap_claim.py 在册守护（l930-11，命题级更强）。
    """
    violations, checked = _claims_on(ROOT / "content")
    assert checked == sorted(p.name for p in PATHS_DIR.glob("*.yaml")), "扫描面须覆盖全部 path yaml"
    p4 = [v for v in violations if v.startswith("P4")]
    p5 = [v for v in violations if v.startswith("P5")]
    assert p4 == [], f"工时不自洽：{p4}"
    assert p5 == [], f"被引专题无题：{p5}"


def test_P1_P3_占位_等A类清账():
    """占位哨兵：P1（数字=磁盘量）/P3（Milestone 序数跨引）在 A-1/A-2/A-3 人工裁决
    （档 §三）清账前**不得钉**——直接钉会让全量当场 1 红（档 §四案甲反向顺序警示）。
    本例钉的是「占位仍在」这一流程事实。"""
    src = Path(__file__).read_text(encoding="utf-8")
    assert "A-1/A-2/A-3 人工裁决在册" in src or "等A类清账" in Path(__file__).name or "等A类清账" in src
    # 哨兵字面量拆写，防「断言字符串自匹配」的自指假红：
    num_probe = "NUM " + "= re.compile" if False else "NUM" + "= re.compile"
    msref_probe = "MS" + "REF"
    assert num_probe not in src, "P1 判据不得提前进场（A 类未清账）"
    assert msref_probe not in src, "P3 判据不得提前进场（A 类未清账）"


def test_变异自证_tmp副本_GAP承诺改出后_P2_转红(tmp_path):
    """变异自证（tmp 副本法，不动真 content/paths/）：把某里程碑 description 改出
    「尚未提供题目」式 GAP 承诺（该里程碑实有题 > 0）⇒ P2 必红。"""
    src_root = tmp_path / "content"
    src_root.mkdir()
    shutil.copytree(ROOT / "content" / "paths", src_root / "paths")
    # 被引专题的磁盘题也要在 tmp 根下（per_topic 双轨要读）——软链不便（win），整树拷最小族：
    for yml in glob.glob(str(PATHS_DIR / "*.yaml")):
        d = yaml.safe_load(Path(yml).read_text(encoding="utf-8"))
        for m in d["milestones"]:
            for t in m["topics"]:
                lang, topic = _split(t)
                dst = src_root / lang / topic
                if not dst.exists():
                    shutil.copytree(ROOT / "content" / lang / topic, dst,
                                    ignore=shutil.ignore_patterns("__pycache__"))

    target = src_root / "paths" / "quick_stats.yaml"
    d = yaml.safe_load(target.read_text(encoding="utf-8"))
    d["milestones"][0]["description"] = "入门专题，尚未提供题目，敬请期待。"  # GAP 命中且该里程碑实有题 > 0
    target.write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")

    violations, _ = _claims_on(src_root)
    assert any(v.startswith("P2") and "quick_stats" in v for v in violations), violations
