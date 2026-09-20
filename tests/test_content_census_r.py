# -*- coding: utf-8 -*-
"""r 题库纵向普查钉桩（l920-02）。

口径同 l920-01（core.loader.load_language），只读题库文件，零写库零源码改动。
任务锚点预期含「r 专属 expected_rows/tests 字段形态（多 DataFrame 题）」——
**实测落空并如实钉桩**：content/r 下 84 个 yaml 无一含 expected_rows / tests 键
（grep '^expected_rows:|^tests:' content/r → 0 命中），loader 侧恒为 None。
r 的答案面走 expected_output(70) + rubric(14) + judge_mode=ai_open(14)，见下逐例断言。

实测基线（2026-09-19）：
  题数 84 / topic 18；difficulty 直方图 {1:15, 2:37, 3:31, 4:1}
  expected_output 70、rubric 14、reference_answer 14；judge_mode run 70 / ai_open 14
  expected_rows / tests 两字段 84 题全 None；hints 缺失 0 题

2026-09-20 追加（D6 落地，见 scripts/mark_r_judge_plain.py 与
docs/insights/learn-r-plain-downgrade-20260920.md）：用户拍板「r 84 题缺
expected_rows/tests → 降级为普通题（不硬补测试用例）」，故只给原本依赖 loader
隐式默认的 70 题补了显式 `judge_mode: run`；题干与答案字段零改动。
本文件末尾新增用例把「84/84 判定模式必须显式 / 源文件不得出现 expected_rows|tests」
钉死——这两条正是 D6 的处置口径。
"""
import collections

from core.loader import load_language

LANG = "r"
EXPECTED_TOPICS = 18
EXPECTED_PROBLEMS = 84
EXPECTED_DIFF = {1: 15, 2: 37, 3: 31, 4: 1}
EXPECTED_SLUGS = (
    "01_vectors_and_basics", "02_logic_and_summary", "02b_dataframe", "03_dplyr",
    "04_ggplot", "05_lm_anova", "06_mixed_apa", "07_glm", "08_tidyr", "09_purrr_map",
    "10_stringr_lubridate", "11_survival", "12_clustering", "13_rmarkdown",
    "14_real_world_data", "14_sem_basics", "15_cfa", "16_mediation",
)


def _topics():
    return load_language(LANG)


def _problems():
    return [p for t in _topics() for p in t.problems]


def test_题数84_且topic18():
    topics = _topics()
    problems = [p for t in topics for p in t.problems]
    assert len(topics) == EXPECTED_TOPICS, f"r topic 数漂移：{len(topics)} != {EXPECTED_TOPICS}"
    assert len(problems) == EXPECTED_PROBLEMS, f"r 题数漂移：{len(problems)} != {EXPECTED_PROBLEMS}"


def test_topic_slug集合精确():
    slugs = tuple(t.slug for t in _topics())
    assert slugs == EXPECTED_SLUGS, (
        f"r topic slug 集合漂移：新增={sorted(set(slugs) - set(EXPECTED_SLUGS))} "
        f"缺失={sorted(set(EXPECTED_SLUGS) - set(slugs))}"
    )


def test_difficulty直方图精确():
    got = dict(sorted(collections.Counter(p.difficulty for p in _problems()).items()))
    assert got == EXPECTED_DIFF, f"r difficulty 分布漂移：{got} != {EXPECTED_DIFF}"


def test_expected_rows与tests形态_全None翻桩():
    """任务预期「r 有多 DataFrame 题 → 看 expected_rows/tests 形态」；实测为 0。
    本用例把这个「不存在」钉死：任何一题出现该字段即红，逼内容作者显式决策。"""
    problems = _problems()
    rows_shape = collections.Counter(
        "list(%d)" % len(p.expected_rows) if isinstance(p.expected_rows, list)
        else type(p.expected_rows).__name__ for p in problems)
    tests_shape = collections.Counter(
        "list(%d)" % len(p.tests) if isinstance(p.tests, list)
        else type(p.tests).__name__ for p in problems)
    assert dict(rows_shape) == {"NoneType": 84}, f"r expected_rows 形态漂移：{dict(rows_shape)}"
    assert dict(tests_shape) == {"NoneType": 84}, f"r tests 形态漂移：{dict(tests_shape)}"


def test_答案面走expected_output与rubric():
    problems = _problems()
    fields = collections.Counter()
    for p in problems:
        for key in ("expected_output", "tests", "rubric", "reference_answer"):
            if getattr(p, key, None):
                fields[key] += 1
    assert dict(fields) == {
        "expected_output": 70, "rubric": 14, "reference_answer": 14,
    }, f"r 答案字段计数漂移：{dict(fields)}"
    judge = dict(collections.Counter(p.judge_mode for p in problems))
    assert judge == {"run": 70, "ai_open": 14}, f"r judge_mode 分布漂移：{judge}"
    # judge_mode 与答案面必须一一对应：run↔expected_output，ai_open↔rubric
    mismatch = [p.id for p in problems
                if (p.judge_mode == "run") != bool(p.expected_output)]
    assert mismatch == [], f"r judge_mode 与 expected_output 不匹配：{mismatch}"
    missing = [p.id for p in problems if not p.hints]
    assert missing == [], f"r 缺 hints 名单漂移：{sorted(missing)}"


# ===== 2026-09-20 D6：判定模式显式化（源文件级钉桩） =====

def _r_yaml_files():
    import glob
    return sorted(glob.glob("content/r/*/*.yaml"))


def test_judge_mode源文件级显式_84之84():
    """D6：r 题库不存在「多 DataFrame 机判题」形态 → 降级为普通题，只补标记字段。

    源文件级（不经 loader）断言两件事：
      ① 84 个 yaml **每个都显式写了 judge_mode**（当前 run 70 / ai_open 14）——
         新题若依赖 loader 的隐式默认（run）即红，逼作者显式声明判定模式；
      ② 源文件里**不得出现 expected_rows / tests 键**——D6 已拍板不硬补机判用例，
         将来谁要加，必须先翻本桩（显式决策），不能悄悄改口径。
    """
    import os

    import yaml

    files = _r_yaml_files()
    assert len(files) == EXPECTED_PROBLEMS, (
        f"r 题目源文件数漂移：{len(files)} != {EXPECTED_PROBLEMS}")
    no_judge_mode, judge_counts, has_rows_or_tests = [], collections.Counter(), []
    for f in files:
        data = yaml.safe_load(open(f, encoding="utf-8")) or {}
        if "judge_mode" not in data:
            no_judge_mode.append(os.path.basename(f))
        judge_counts[data.get("judge_mode")] += 1
        if "expected_rows" in data or "tests" in data:
            has_rows_or_tests.append(os.path.relpath(f).replace("\\", "/"))
    assert no_judge_mode == [], f"缺显式 judge_mode 的 r 题目：{sorted(no_judge_mode)}"
    assert dict(judge_counts) == {"run": 70, "ai_open": 14}, (
        f"r 源文件 judge_mode 分布漂移：{dict(judge_counts)}")
    assert has_rows_or_tests == [], (
        f"r 源文件出现 expected_rows/tests（D6 已拍板降级为普通题，需显式翻桩）：{has_rows_or_tests}")
