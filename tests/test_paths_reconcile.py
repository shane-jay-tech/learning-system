# -*- coding: utf-8 -*-
"""paths 元数据对账钉桩（l918-16；2026-09-20 复核修复；2026-09-21 l922-02 头注订正）。

钉五条（本文件实有 6 个 test_ 用例：①-⑤ 各一，另 1 例是 ⑤ 下限的缩半有牙自检；
头注计数与用例数须一致——l921-02 点名的滞后）：
  ① header estimated_hours == sum(里程碑 estimated_hours)——**全路径强制，不留白名单例外**。
     2026-09-20 D5 追加 a10 后 agent_mastery 合计 26 → 29，而 header 仍写 22：
     用户按 header 读总时长＝少报 7 小时（约 24%）。GPT 独立复核判 CRITICAL——
     「新增里程碑后继续维持不一致＝把遗留错误固化成新基线」。已把 header 修为 29
     并**删除旧白名单 KNOWN_HOURS_MISMATCH**：任何 path 失配即红。
  ② 同 path 专题重复引用——quick_stats 的 r/05_lm_anova、r/06_mixed_apa 各被两个里程碑
     引用（_path_overall_progress 会重复计数致进度虚高），按已知清单钉桩；
  ③ prereqs 完整性——所有 prereq 引用存在且无环（现状干净，必须保持为空）。
  ④ 里程碑时数为正数——header 与每个 milestone 的 estimated_hours 必须是正实数
     （允许 0.5 步长），否则零/负数/字符串会让 ① 的合计断言假绿。
  ⑤ topic 引用无悬空——path → content 方向每个 "lang/slug" 引用都落到 content/<lang>/<slug>/
     实目录（l921-02 接 l920-08 建议 #3 补的零风险翻桩）。覆盖面兜底下限自 l922-125 起改为
     与磁盘 topic 目录数联动的动态口径（_REF_COVERAGE_FLOOR × 目录数，见下方 _disk_topic_dir_count
     的取数命令），替代 l920-08 的字面量 43——只防整体删空、不锁上限，专题扩充时下限随目录数上移。
     2026-09-21 实测：去重被引用 85 / 磁盘 85 / 悬空 0 / 未被引用 0（2026-09-22 复核同值）。
"""
import glob
import os

import yaml

PATHS = sorted(glob.glob("content/paths/*.yaml"))
KNOWN_DUP_TOPICS = {
    "quick_stats": {"r/05_lm_anova": 2, "r/06_mixed_apa": 2},
}


def _load():
    for f in PATHS:
        key = f.replace("\\", "/").rsplit("/", 1)[-1].split(".")[0]
        yield key, yaml.safe_load(open(f, encoding="utf-8"))


# 覆盖面兜底下限（l922-125 动态化）：去重 topic 引用数 >= _REF_COVERAGE_FLOOR × 磁盘 topic 目录数。
# 保留 l920-08「防里程碑删空」语义——里程碑被整段删掉时引用数会远低于磁盘专题目录数即红；
# 不锁上限（正常新增专题时磁盘目录与引用同步增长，比例不降），也去掉了写死 43 离真值差 42 的钝感。
# 0.9 留 10% 余量，容许少量「建了目录但暂未挂进任何路径」的专题（当前实测未被引用 0）。
_REF_COVERAGE_FLOOR = 0.9


def _disk_topic_dir_count() -> int:
    """磁盘上的 topic 目录数（动态分母）。

    取数命令（口径 = content/<lang>/<slug>/ 里带 _lesson.md 的目录，与 load_language 认专题一致）：
        python -c "import glob; print(len({p.rsplit('/_lesson.md',1)[0] for p in glob.glob('content/*/*/_lesson.md')}))"
    2026-09-22 实测 = 85。paths/ 与 datasets/ 下无 *_lesson.md，天然不计入，无需再排除。
    """
    return len({p.replace("\\", "/").rsplit("/_lesson.md", 1)[0]
                for p in glob.glob("content/*/*/_lesson.md")})


def _assert_ref_floor(dedup_ref_count: int, topic_dir_count: int) -> None:
    """覆盖面断言（抽出来供缩半夹具做有牙自检，见 test_覆盖面下限夹具_缩半引用即红）。"""
    floor = _REF_COVERAGE_FLOOR * topic_dir_count
    assert dedup_ref_count >= floor, (
        f"去重 topic 引用数 {dedup_ref_count} 低于磁盘 topic 目录数 {topic_dir_count} 的 "
        f"{_REF_COVERAGE_FLOOR:.0%} 下限（{floor:.1f}），疑有里程碑被删空")


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


def test_topic_引用无悬空_每个引用都落到实目录():
    """l921-02（接 l920-08 建议）：path → content 方向钉桩，悬空 topic 引用数必须为 0。

    口径与 scripts/audit_paths_prereq.py 一致：topic 引用形如 "lang/slug"，
    存在性以 content/<lang>/<slug>/ 目录为准。l920-08 当时是 43 个去重引用，
    2026-09-21 复跑为 85 个（专题扩充，锚点数字已漂移，悬空仍为 0），
    所以这是零风险翻桩；一旦里程碑写错 slug、或删掉专题目录而路径没同步，本例即红。
    """
    refs = []
    for key, d in _load():
        for m in d.get("milestones") or []:
            for t in m.get("topics") or []:
                refs.append((key, m.get("id"), t))
    assert refs, "一条 topic 引用都没读到——空循环会让本例假绿"

    root = os.path.normpath("content")
    dangling = []
    for key, mid, ref in sorted(set(refs)):
        parts = str(ref).split("/")
        # 空段（"r/"、"/r"）与越界段（"../x"）都算悬空：目录存在性不足以挡住它们。
        target = os.path.normpath(os.path.join(root, *parts)) if len(parts) == 2 else ""
        ok = len(parts) == 2 and all(parts) and target.startswith(root + os.sep) and os.path.isdir(target)
        if not ok:
            dangling.append("%s/%s: %r" % (key, mid, ref))
    assert not dangling, "悬空 topic 引用（应为 0）：%s" % "; ".join(dangling)

    # 覆盖面兜底：只防「引用被整体删空」，不锁上限（正常新增专题不该变红）。
    # l922-125：下限由字面量 43 改为与磁盘 topic 目录数联动的动态口径（取数命令见
    # _disk_topic_dir_count 的 docstring）；缩半有牙自检见 test_覆盖面下限夹具_缩半引用即红。
    _assert_ref_floor(len(set(r for _, _, r in refs)), _disk_topic_dir_count())


def test_覆盖面下限夹具_缩半引用即红():
    """l922-125 有牙自检：把去重引用数砍半，动态下限断言必须红（内存夹具，零写盘）。

    取磁盘真实目录数 N（当前 85）：满覆盖 N/N 通过；缩到 N//2（模拟里程碑被删空一半）
    必须让 _assert_ref_floor 抛 AssertionError。这条防的是「把断言又写回恒真的绝对值」——
    旧口径 43 离真值 85 差 42，删掉近半里程碑仍绿，正是本单要修的钝感。
    """
    n = _disk_topic_dir_count()
    assert n >= 3, f"磁盘 topic 目录数异常偏低（{n}），夹具前提失效"
    _assert_ref_floor(n, n)  # 满覆盖：不红
    raised = False
    try:
        _assert_ref_floor(n // 2, n)  # 缩半：必红（n//2 < 0.9×n 对一切 n>=3 成立）
    except AssertionError:
        raised = True
    assert raised, (
        f"缩半夹具（{n // 2}/{n}）未触发下限断言——断言退化成恒真，失去防删空能力")
