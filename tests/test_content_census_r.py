# -*- coding: utf-8 -*-
"""r 题库纵向普查钉桩（l920-02；2026-09-20 复核修复）。

口径同 l920-01（core.loader.load_language），只读题库文件，零写库零源码改动。

2026-09-20 复核修复（GPT 干净版复核项 6 / F-10）——本文件现在明确分两层，
不再把「内容盘点快照」当永久可用性契约：
  · 【内容盘点快照 census】题数 / topic 数 / 难度直方图 / slug 精确顺序 /
    各答案字段计数：内容发布基线的快照，题库扩容时**有意翻桩**；
  · 【可用性契约 contract】每道题必须显式 judge_mode、取值合法、与答案字段匹配：
    永久成立的可执行规则，不随题目数量变化；
  · 【机判字段 schema 版本开关】R_SCHEMA_VERSION 版本 1 = 现状（r 题库不使用
    expected_rows / tests 机判字段）；将来要建多 DataFrame 机判题，把它改成 2
    并满足语义规则即可放宽。旧版「任何 R 题出现 expected_rows|tests 即失败」的
    反向断言会永久禁止能力建设，已删除。

实测基线（2026-09-19）：
  题数 84 / topic 18；difficulty 直方图 {1:15, 2:37, 3:31, 4:1}
  expected_output 70、rubric 14、reference_answer 14；judge_mode run 70 / ai_open 14
  expected_rows / tests 两字段 84 题全 None；hints 缺失 0 题
2026-09-20 D6：给原本依赖 loader 隐式默认的 70 题补显式 judge_mode: run
（题干与答案字段零改动；等价性证明见 tests/test_judge_mode_equivalence.py）。
"""
import collections
import glob
import os

import pytest
import yaml

from core.loader import load_language

LANG = "r"

# ---- 内容盘点快照基线（census）：内容扩容时有意翻桩 ----
EXPECTED_TOPICS = 18
EXPECTED_PROBLEMS = 84
EXPECTED_DIFF = {1: 15, 2: 37, 3: 31, 4: 1}
EXPECTED_SLUGS = (
    "01_vectors_and_basics", "02_logic_and_summary", "02b_dataframe", "03_dplyr",
    "04_ggplot", "05_lm_anova", "06_mixed_apa", "07_glm", "08_tidyr", "09_purrr_map",
    "10_stringr_lubridate", "11_survival", "12_clustering", "13_rmarkdown",
    "14_real_world_data", "14_sem_basics", "15_cfa", "16_mediation",
)

# ---- 机判字段 schema 版本：1 = 不引入 expected_rows/tests；2 = 允许（语义规则仍在）----
R_SCHEMA_VERSION = 1
VALID_JUDGE_MODES = {"run", "ai_open"}
SOURCE_ANSWER_FIELDS = ("expected_output", "tests", "expected_rows", "rubric", "reference_answer")


def _topics():
    return load_language(LANG)


def _problems():
    return [p for t in _topics() for p in t.problems]


def _r_yaml_files():
    return sorted(glob.glob("content/r/*/*.yaml"))


def _source_data():
    return [(f, yaml.safe_load(open(f, encoding="utf-8")) or {}) for f in _r_yaml_files()]


# ================================================================== 内容盘点快照（census）

def test_census_题数84_且topic18():
    topics = _topics()
    problems = [p for t in topics for p in t.problems]
    assert len(topics) == EXPECTED_TOPICS, f"r topic 数漂移：{len(topics)} != {EXPECTED_TOPICS}"
    assert len(problems) == EXPECTED_PROBLEMS, f"r 题数漂移：{len(problems)} != {EXPECTED_PROBLEMS}"


def test_census_topic_slug集合精确():
    slugs = tuple(t.slug for t in _topics())
    assert slugs == EXPECTED_SLUGS, (
        f"r topic slug 集合漂移：新增={sorted(set(slugs) - set(EXPECTED_SLUGS))} "
        f"缺失={sorted(set(EXPECTED_SLUGS) - set(slugs))}"
    )


def test_census_difficulty直方图精确():
    got = dict(sorted(collections.Counter(p.difficulty for p in _problems()).items()))
    assert got == EXPECTED_DIFF, f"r difficulty 分布漂移：{got} != {EXPECTED_DIFF}"


def test_census_答案面字段与判定模式分布():
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
    assert [p.id for p in problems if not p.hints] == [], "r 缺 hints 名单漂移"


# ================================================================== 可用性契约（永久）

def test_契约_每道题显式judge_mode():
    """源文件级：r 题库 84/84 必须显式写 judge_mode——新题依赖 loader 隐式默认即红。"""
    files = _r_yaml_files()
    assert len(files) == EXPECTED_PROBLEMS, (
        f"r 题目源文件数漂移：{len(files)} != {EXPECTED_PROBLEMS}")
    missing = [os.path.basename(f) for f, d in _source_data() if "judge_mode" not in d]
    assert missing == [], f"缺显式 judge_mode 的 r 题目：{sorted(missing)}"


def test_契约_judge_mode取值合法():
    bad = [(f, d.get("judge_mode")) for f, d in _source_data()
           if d.get("judge_mode") not in VALID_JUDGE_MODES]
    assert bad == [], f"r 题目 judge_mode 取值非法（合法值 {sorted(VALID_JUDGE_MODES)}）：{bad}"
    bad_loaded = [p.id for p in _problems() if p.judge_mode not in VALID_JUDGE_MODES]
    assert bad_loaded == [], f"loader 归一化后出现非法 judge_mode：{bad_loaded}"


def test_契约_判定模式与答案字段匹配():
    """run ↔ 有可机判答案面；ai_open ↔ 有 rubric。与题数无关，永久成立。"""
    problems = _problems()
    run_without_answer = [p.id for p in problems
                          if p.judge_mode == "run" and not (p.expected_output or p.tests)]
    ai_without_rubric = [p.id for p in problems
                         if p.judge_mode == "ai_open" and not p.rubric]
    ai_with_stdout = [p.id for p in problems
                      if p.judge_mode == "ai_open" and p.expected_output]
    assert run_without_answer == [], f"run 题缺可机判答案面：{run_without_answer}"
    assert ai_without_rubric == [], f"ai_open 题缺 rubric：{ai_without_rubric}"
    assert ai_with_stdout == [], f"ai_open 题不该同时声明 expected_output：{ai_with_stdout}"


# ================================================================== 机判字段：语义规则 + 版本开关

def test_机判字段_业务语义规则():
    """永久规则：一旦某题声明 expected_rows / tests，必须成对满足业务约束。

    这是「有业务语义的规则」——不禁止能力建设，只禁止半成品形态。
    """
    bad = []
    for f, d in _source_data():
        has_rows, has_tests = "expected_rows" in d, "tests" in d
        if not (has_rows or has_tests):
            continue
        rel = os.path.relpath(f).replace("\\", "/")
        if d.get("judge_mode") != "run":
            bad.append((rel, "声明机判字段就必须 judge_mode: run"))
        if has_rows and not str(d.get("setup_sql") or "").strip():
            bad.append((rel, "expected_rows 必须配 setup_sql（否则无表可查）"))
        if has_tests and not isinstance(d.get("tests"), list):
            bad.append((rel, "tests 必须是 list"))
        if d.get("expected_output"):
            bad.append((rel, "机判题不该同时声明 expected_output（判定面必须唯一）"))
    assert bad == [], f"r 机判字段语义违规：{bad}"


def test_机判字段_版本1快照_出现即提示升级而非永久封杀():
    """版本 1 的内容快照：r 题库当前不使用 expected_rows / tests。

    真出现机判字段时本用例会红，但**红的是提示**：内容形态已进入 schema 版本 2，
    请把 R_SCHEMA_VERSION 改成 2（并确认新题满足上面的业务语义规则），
    而不是在版本 1 下静默改口径。
    """
    if R_SCHEMA_VERSION != 1:
        pytest.skip("R_SCHEMA_VERSION=%d 允许机判题，版本 1 快照桩自动放宽" % R_SCHEMA_VERSION)
    src_used = [os.path.relpath(f).replace("\\", "/") for f, d in _source_data()
                if "expected_rows" in d or "tests" in d]
    assert src_used == [], (
        f"r 源文件出现机判字段 {src_used}：题库形态已进入 schema 版本 2——"
        "请把本文件的 R_SCHEMA_VERSION 改成 2，并确认新题满足 run 模式 + setup_sql + 唯一判定面")
    problems = _problems()
    used = [p.id for p in problems if p.expected_rows is not None or p.tests is not None]
    assert used == [], f"loader 侧出现机判字段：{used}"
