# -*- coding: utf-8 -*-
"""paths 元数据对账钉桩（l918-16；2026-09-20 复核修复）。

钉三条：
  ① header estimated_hours == sum(里程碑 estimated_hours)——**全路径强制，不留白名单例外**。
     2026-09-20 D5 追加 a10 后 agent_mastery 合计 26 → 29，而 header 仍写 22：
     用户按 header 读总时长＝少报 7 小时（约 24%）。GPT 独立复核判 CRITICAL——
     「新增里程碑后继续维持不一致＝把遗留错误固化成新基线」。已把 header 修为 29
     并**删除旧白名单 KNOWN_HOURS_MISMATCH**：任何 path 失配即红。
  ② 同 path 专题重复引用——quick_stats 的 r/05_lm_anova、r/06_mixed_apa 各被两个里程碑
     引用（_path_overall_progress 会重复计数致进度虚高），按已知清单钉桩；
  ③ prereqs 完整性——所有 prereq 引用存在且无环（现状干净，必须保持为空）。
"""
import glob

import yaml

PATHS = sorted(glob.glob("content/paths/*.yaml"))
KNOWN_DUP_TOPICS = {
    "quick_stats": {"r/05_lm_anova": 2, "r/06_mixed_apa": 2},
}


def _load():
    for f in PATHS:
        key = f.replace("\\", "/").rsplit("/", 1)[-1].split(".")[0]
        yield key, yaml.safe_load(open(f, encoding="utf-8"))


def test_全路径_header时数等于里程碑合计_无白名单例外():
    """所有 content/paths/*.yaml 一律 header == 合计（2026-09-20 复核修复）。

    旧版用 KNOWN_HOURS_MISMATCH 白名单把 agent_mastery 的 22 vs 29 当「已知遗留」放行；
    白名单已删——时长失配不再是可接受状态，任何 path 不符即红。
    """
    checked = [key for key, _ in _load()]
    for key, d in _load():
        ms = d.get("milestones") or []
        assert ms, f"{key} 没有里程碑，无法核算时长"
        per = [(m.get("id"), m.get("estimated_hours")) for m in ms]
        total = sum(h for _, h in per)
        header = d.get("estimated_hours")
        assert header == total, (
            f"{key} header 时数与里程碑合计不符：header={header} 合计={total}；逐个={per}")
    # 覆盖性：每一个 path 文件都被检查过（防「循环空了所以全绿」）
    expected = [f.replace("\\", "/").rsplit("/", 1)[-1].split(".")[0] for f in PATHS]
    assert checked == expected and expected, f"未覆盖全部 path：{checked} != {expected}"


def test_全路径_里程碑时数为正数():
    """时数必须是正实数（允许 0.5 步长的半小时间隔）：零/负数/字符串会让合计断言假绿。"""
    def _num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)

    for key, d in _load():
        header = d.get("estimated_hours")
        assert _num(header), f"{key} header estimated_hours 不是数字：{header!r}"
        assert header > 0, f"{key} header estimated_hours 非正：{header!r}"
        for m in d.get("milestones") or []:
            h = m.get("estimated_hours")
            assert _num(h), f"{key}/{m.get('id')} estimated_hours 不是数字：{h!r}"
            assert h > 0, f"{key}/{m.get('id')} estimated_hours 非正：{h!r}"


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
