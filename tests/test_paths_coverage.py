# -*- coding: utf-8 -*-
"""paths ↔ content 双向覆盖钉桩（D5 补学习路径，2026-09-20；同日复核修复）。

上游：l920-08 只读对账量出「磁盘 85 个 topic 只有 43 个被任何 path 引用（50.6%），
cpp 13/13 零引用（0.0%）」；用户 2026-09-20 拍板 D5「补学习路径」——
内容已在库，补路径比砍内容便宜。

本单落点（详见 docs/insights/learn-path-coverage-fill-20260920.md）：
  新增 3 条主线 content/paths/{cpp_foundation,python_advanced,r_advanced}.yaml
  ＋既有 2 条各加 1 个里程碑（people_analytics m6b、agent_mastery a10）
  ⇒ 未被引用 topic 42 → 0（覆盖 43/85 → 85/85），悬空引用仍为 0。

2026-09-20 复核修复（GPT 干净版 F-08 / TEST-003）：
  · 口径改成**集合语义**——set(磁盘 topic) == set(path 引用)，不再用「审计脚本内部
    字典的长度」间接推断覆盖率（工具内部结构一变测试就红而业务语义没变）；
  · 删掉 85 / 13 这类精确数字当系统不变量，改为性质断言：每一条磁盘 topic 至少被一条
    path 引用、path 引用必须存在、prereq 必须存在且无环。精确内容盘点归 census 桩。
"""
import glob
import os

import yaml

from core.paths import load_all_paths
from scripts.audit_paths_prereq import audit

NEW_PATH_IDS = {"cpp_foundation", "python_advanced", "r_advanced"}


def _path_files():
    return sorted(glob.glob("content/paths/*.yaml"))


def _path_updates():
    """yield (key, milestones)；供集合口径与 prereq 判环共用。"""
    for f in _path_files():
        key = os.path.basename(f)[:-5]
        d = yaml.safe_load(open(f, encoding="utf-8")) or {}
        yield key, (d.get("milestones") or [])


def _disk_topics():
    """磁盘上真实存在的 topic 集合（lang/slug）。

    纯结构扫描：content/<lang>/<slug>/ 里只要有 yaml 或 _lesson.md 就算一个 topic
    （content/paths 与 content/datasets 没有 topic 子目录，自然不参与）。
    """
    out = set()
    for lang_dir in sorted(glob.glob("content/*/")):
        lang = os.path.basename(os.path.normpath(lang_dir))
        for topic_dir in sorted(glob.glob(lang_dir + "*/")):
            slug = os.path.basename(os.path.normpath(topic_dir))
            if glob.glob(topic_dir + "*.yaml") or glob.glob(topic_dir + "_lesson.md"):
                out.add(lang + "/" + slug)
    return out


def _referenced():
    refs = set()
    for _key, ms in _path_updates():
        for m in ms:
            refs.update(m.get("topics") or [])
    return refs


def test_每一条磁盘topic至少被一条path引用():
    disk, refs = _disk_topics(), _referenced()
    assert disk, "磁盘上一个 topic 都没扫到——扫描口径坏了"
    assert _path_files(), "content/paths 下一个主线文件都没有"
    missing = sorted(disk - refs)
    assert missing == [], f"有 topic 未被任何 path 引用：{missing}"


def test_path引用的topic必须真的存在():
    disk, refs = _disk_topics(), _referenced()
    dangling = sorted(refs - disk)
    assert dangling == [], f"path 引用了磁盘上不存在的 topic：{dangling}"


def test_cpp语言所有topic都被引用_D5前为0之13():
    disk = {t for t in _disk_topics() if t.startswith("cpp/")}
    refs = _referenced()
    assert disk, "cpp 下没扫到任何 topic"
    assert disk <= refs, f"cpp 未被任何 path 引用的 topic：{sorted(disk - refs)}"


def test_prereq必须存在且无环():
    for key, ms in _path_updates():
        ids = {m["id"] for m in ms}
        deps = {m["id"]: set(m.get("prereqs") or []) for m in ms}
        for mid, prs in deps.items():
            dangling = sorted(p for p in prs if p not in ids)
            assert dangling == [], f"{key}: {mid} 引用不存在的 prereq {dangling}"
        # Kahn 拓扑排序（本文件独立实现，不吃审计脚本的实现细节）
        order = []
        ready = [i for i in ids if not deps[i]]
        while ready:
            node = ready.pop()
            order.append(node)
            for mid in ids:
                if node in deps[mid]:
                    deps[mid].discard(node)
                    if not deps[mid] and mid not in order and mid not in ready:
                        ready.append(mid)
        assert len(order) == len(ids), f"{key}: prereq 图存在环（拓扑序 {order}）"


def test_审计脚本口径与独立计算一致():
    """交叉校验：审计脚本的结构 == 本文件独立扫描结果（口径漂移时暴露，而不是靠长度推断）。"""
    a = audit()
    disk = _disk_topics()
    refs = _referenced()
    assert {l + "/" + s for l, slugs in a["disk"].items() for s in slugs} == disk
    assert set(a["topic_refs"]) == refs
    assert {l: v for l, v in a["unreferenced"].items() if v} == {}


def test_三条新主线在盘且可被加载():
    ids = {p.id for p in load_all_paths()}
    assert NEW_PATH_IDS <= ids, (
        f"新主线缺失：{sorted(NEW_PATH_IDS - ids)}（现有 {sorted(ids)}）")
