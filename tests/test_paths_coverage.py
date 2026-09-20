# -*- coding: utf-8 -*-
"""paths ↔ content 双向覆盖钉桩（D5 补学习路径，2026-09-20）。

上游：l920-08 只读对账量出「磁盘 85 个 topic 只有 43 个被任何 path 引用（50.6%），
cpp 13/13 零引用（0.0%）」；用户 2026-09-20 拍板 D5「补学习路径」——
内容已在库，补路径比砍内容便宜。

本单落点（详见 docs/insights/learn-path-coverage-fill-20260920.md）：
  新增 3 条主线 content/paths/{cpp_foundation,python_advanced,r_advanced}.yaml
  ＋既有 2 条各加 1 个里程碑（people_analytics m6b、agent_mastery a10）
  ⇒ 未被引用 topic 42 → 0（覆盖 43/85 → 85/85），悬空引用仍为 0。

本用例把这个结果钉死：新增 topic 却没进任何 path、或路径里写错 slug 时立即红，
逼显式决策。与 tests/test_paths_reconcile.py 分工——那条管「path 内部元数据自洽」
（header 时数／同 path 重复／prereq 环），本条管「content ↔ path 双向覆盖」。
口径不另立：直接复用 l920-08 的只读对账脚本 scripts/audit_paths_prereq.py。
只读题库与 paths，零写库零源码改动。
"""
from core.paths import load_all_paths
from scripts.audit_paths_prereq import audit

EXPECTED_DISK_TOPICS = 85
EXPECTED_CPP_TOPICS = 13
NEW_PATH_IDS = {"cpp_foundation", "python_advanced", "r_advanced"}


def test_未被引用topic_归零():
    a = audit()
    unreferenced = {k: v for k, v in a["unreferenced"].items() if v}
    assert unreferenced == {}, f"有 topic 未被任何 path 引用：{unreferenced}"


def test_悬空topic引用与悬空prereq_归零():
    a = audit()
    assert a["dangling"] == {}, f"悬空 topic 引用：{a['dangling']}"
    assert a["dangling_prereq"] == {}, f"悬空 prereq：{a['dangling_prereq']}"


def test_cpp覆盖率_13之13_原为零引用孤儿语言():
    a = audit()
    disk = a["disk"]["cpp"]
    covered = [s for s in disk if ("cpp/" + s) in a["topic_refs"]]
    assert len(disk) == EXPECTED_CPP_TOPICS, f"cpp topic 数漂移：{len(disk)}"
    assert len(covered) == EXPECTED_CPP_TOPICS, (
        f"cpp 覆盖率不足：{len(covered)}/{len(disk)}；未覆盖={sorted(set(disk) - set(covered))}"
    )


def test_三条新主线在盘且可被加载():
    ids = {p.id for p in load_all_paths()}
    assert NEW_PATH_IDS <= ids, f"新主线缺失：{sorted(NEW_PATH_IDS - ids)}（现有 {sorted(ids)}）"


def test_全库覆盖率_85之85():
    a = audit()
    total = sum(len(v) for v in a["disk"].values())
    assert total == EXPECTED_DISK_TOPICS, (
        f"磁盘 topic 总数漂移：{total} != {EXPECTED_DISK_TOPICS}"
        "（新增 topic 必须同时进某条 path，或有意翻本桩）"
    )
    assert len(a["topic_refs"]) == total, (
        f"去重被引用数漂移：{len(a['topic_refs'])} != {total}"
    )
