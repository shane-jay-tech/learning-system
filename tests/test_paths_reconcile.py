# -*- coding: utf-8 -*-
"""paths 元数据对账钉桩（l918-16）。

钉三条现状（2026-09-19 预扫）：
  ① header estimated_hours == sum(milestone hours)——agent_mastery 现状失配
    （2026-09-20 D5 补路径后为 22 vs 29；原 22 vs 26）
    按已知清单钉桩：修复 yaml 或有意翻桩时更新；
  ② 同 path 专题重复引用——quick_stats 的 r/05_lm_anova、r/06_mixed_apa 各被两个里程碑
    引用（_path_overall_progress 会重复计数致进度虚高），按已知清单钉桩；
  ③ prereqs 完整性——所有 prereq 引用存在且无环（现状干净，必须保持为空）。
"""
import glob

import yaml

PATHS = sorted(glob.glob("content/paths/*.yaml"))
# 2026-09-20 有意翻桩（D5 补学习路径，见 zcode-bridge/outbox/l920-09-*.result.md）：
# agent_mastery 追加 a10「Agent 前沿与数据安全」+3h，里程碑合计 26 → 29；
# **header 22 不动**——「header 与合计失配」这条既有遗留（22 vs 26）仍待单独拍板修复，
# 本单只补路径、不夹带修 header，故只把合计值钉到新真值。
KNOWN_HOURS_MISMATCH = {"agent_mastery": (22, 29)}
KNOWN_DUP_TOPICS = {
    "quick_stats": {"r/05_lm_anova": 2, "r/06_mixed_apa": 2},
}


def _load():
    for f in PATHS:
        key = f.replace("\\", "/").rsplit("/", 1)[-1].split(".")[0]
        yield key, yaml.safe_load(open(f, encoding="utf-8"))


def test_hours_header与里程碑合计_失配仅已知agent_mastery():
    for key, d in _load():
        total = sum(m.get("estimated_hours", 0) for m in d.get("milestones", []))
        header = d.get("estimated_hours")
        if key in KNOWN_HOURS_MISMATCH:
            assert (header, total) == KNOWN_HOURS_MISMATCH[key], f"{key} 时数失配值漂移：{header} vs {total}"
        else:
            assert header == total, f"{key} 出现新的 header/合计失配：{header} vs {total}"


def test_专题重复引用_仅quick_stats两条已知():
    for key, d in _load():
        topics = [t for m in d.get("milestones", []) for t in m.get("topics", [])]
        dup = {t: c for t, c in __import__("collections").Counter(topics).items() if c > 1}
        assert dup == KNOWN_DUP_TOPICS.get(key, {}), f"{key} 重复引用漂移：{dup}"


def test_prereqs_引用完整且无环():
    for key, d in _load():
        ms = d.get("milestones", [])
        ids = {m["id"] for m in ms}
        prereq_of = {m["id"]: list(m.get("prereqs", [])) for m in ms}
        for mid, prereqs in prereq_of.items():
            for pr in prereqs:
                assert pr in ids, f"{key}: {mid} 引用不存在的 prereq {pr}"
        # 拓扑排序判环：Kahn
        indeg = {i: 0 for i in ids}
        for mid, prereqs in prereq_of.items():
            for pr in prereqs:
                indeg[mid] += 1
        queue = [i for i, deg in indeg.items() if deg == 0]
        seen = 0
        while queue:
            node = queue.pop()
            seen += 1
            for mid, prereqs in prereq_of.items():
                if node in prereqs:
                    indeg[mid] -= 1
                    if indeg[mid] == 0:
                        queue.append(mid)
        assert seen == len(ids), f"{key}: prereq 图存在环"
