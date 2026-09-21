# -*- coding: utf-8 -*-
"""topic 双号现状桩（l922-05：只读定性之后的加固，不改任何目录名）。

实测现状（2026-09-21）——
  · **排序通道**：`core/loader.py:139` 对 `content/<lang>/*/` 做 **字典序** `sorted()`；
    `ui/pages/language.py:370` 显示的「第 N / M 个知识点」取的是这个列表的**位置**。
    全仓**没有任何代码解析号数**（`split('_')` 取号 / `int(slug...)` / `lstrip('0')` 三处在
    core/ ui/ scripts/ 里零命中）⇒ 号数只是「用来定字典序的字符串」，从不参与数值比较。
  · **双号 6 组 12 目录**：python 20/21/22、r 14、agent_dev 07/08。
    （任务书写「5 处」，磁盘实为 6 组——它把 agent_dev 的 07、08 两组合并计成了 1 处。）
    另 r 的 `02b_dataframe` 与 `02_logic_and_summary` 是**字母后缀消歧**，号数不重复，不算双号。
  · **是否影响展示顺序：不影响相对次序，但影响号数语义。** 号段全部 2 位零填充且 ≤24，
    故字典序与数值序当前**完全等价、零倒置**；双号组内由 slug 字母序决胜（`20_hr_pandas` 先于
    `20_numpy_basics`，`08_read_code` 先于 `08_review_pr`），次序稳定可复现。
  · **真实代价是「号数 vs 位置」错位**：`位置+1 != 号数` 的条数 python 7、r 16、agent_dev 8、
    sql 0、cpp 0，最大漂移 +3（python 第 25 位是 22 号专题）。用户看到的是「第 25 个知识点」，
    文档/口头说「22 号那课」则有两解。

本例钉三条，任何一条变了都必须显式改这里（改号数＝重编号，属日间决策，见
`docs/insights/learn-topic-dualnum-20260921.md` 的方案稿）：
  ① 六组双号的**存在与组内次序**（新增双号、消解双号、或改名换了字母序 → 红）；
  ② **字典序 == 数值序**（将来出现单位数前缀 `9_x` 或进位到三位数会当场倒置 → 红）；
  ③ 双号目录在列表里**必须相邻**（若往两兄弟之间插第三个专题 → 红）。
只读 `load_language`，零写盘零源码改动。
"""
import re
from collections import Counter

from core.loader import load_language

LANGS = ("python", "sql", "cpp", "r", "agent_dev")

# 现状清单：键为 (语言, 号数)，值为 loader 实际给出的顺序（即字典序下的展示序）
DUAL_GROUPS = {
    ("python", "20"): ["20_hr_pandas", "20_numpy_basics"],
    ("python", "21"): ["21_datetime_ts", "21_hr_viz"],
    ("python", "22"): ["22_hr_model", "22_statsmodels"],
    ("r", "14"): ["14_real_world_data", "14_sem_basics"],
    ("agent_dev", "07"): ["07_data_security", "07_write_spec"],
    ("agent_dev", "08"): ["08_read_code", "08_review_pr"],
}


def _prefix(slug):
    """号数前缀拆成（数字段, 字母段）：'20_hr_pandas' → ('20','')，'02b_dataframe' → ('02','b')。

    字母后缀是**消歧**写法（r 的 02 与 02b 号数不重复），故按 (数字段, 字母段) 组合判重，
    不把 02b 记成 02 的双号。
    """
    m = re.match(r"^(\d+)([a-z]*)", slug)
    return (m.group(1), m.group(2)) if m else ("", "")


def test_双号六组现状_且字典序与数值序零倒置():
    slugs = {}
    for lang in LANGS:
        topics = load_language(lang)
        assert topics, f"{lang} 一个专题都没加载到——空列表会让本例假绿"
        slugs[lang] = [t.slug for t in topics]

    # ① 双号清单逐组核对（键集合与组内顺序都要对）
    found = {}
    for lang, lst in slugs.items():
        cnt = Counter(_prefix(s) for s in lst if _prefix(s)[0])
        for num, c in cnt.items():
            if c > 1:
                found[(lang, num[0])] = [s for s in lst if _prefix(s) == num]
    assert found == DUAL_GROUPS, (
        f"双号清单漂移（重编号/改名/新增双号都要显式改这里）：\n 实测 {found}\n 钉桩 {DUAL_GROUPS}")

    # ② 字典序 == 数值序：按 (号数, 字母后缀, slug) 排出来的顺序必须与 loader 的字典序完全一致
    for lang, lst in slugs.items():
        assert lst == sorted(lst), f"{lang} 展示序不是字典序——loader 的 sorted() 被换了"
        assert lst == sorted(lst, key=lambda s: (int(_prefix(s)[0] or -1), _prefix(s)[1], s)), (
            f"{lang} 字典序与数值序已倒置（号数位数或零填充变了，展示顺序会变）：{lst}")
        widths = {len(_prefix(s)[0]) for s in lst if _prefix(s)[0]}
        assert widths == {2}, f"{lang} 号数位数不齐：{widths}（单位数或三位数会让 ② 失去保护）"

    # ③ 双号兄弟必须相邻
    for (lang, num), names in DUAL_GROUPS.items():
        idx = [slugs[lang].index(n) for n in names]
        assert idx == list(range(idx[0], idx[0] + len(idx))), (
            f"{lang} 的 {num} 号两兄弟被拆开了（位置 {idx}）——中间插了专题")
