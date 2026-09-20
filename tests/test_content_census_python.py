# -*- coding: utf-8 -*-
"""python 题库纵向普查钉桩（l920-01）。

口径：core.loader.load_language("python")，只读题库文件，零写库零源码改动。
锚点 l920-01：content/python 实测 121 题 / 27 lesson。编号与总数全部精确钉桩，
任何增删题/改难度/丢 hints 都会让本文件变红，强制内容变更知悉。

实测基线（2026-09-19，D:\\code\\learning-system）：
  题数 121 / topic 27；difficulty 直方图 {1:27, 2:56, 3:31, 4:7}（5 档 0 题）
  答案字段：expected_output 113、tests 46、rubric 8、reference_answer 8（总和 121）
  judge_mode：run 113 / ai_open 8；hints 缺失 0 题
"""
import collections

from core.loader import load_language

LANG = "python"
EXPECTED_TOPICS = 27
EXPECTED_PROBLEMS = 121
EXPECTED_DIFF = {1: 27, 2: 56, 3: 31, 4: 7}
EXPECTED_SLUGS = (
    "01_hello_and_vars", "02_conditionals", "03_loops", "04_functions", "05_lists",
    "06_strings", "07_dicts_sets", "08_files_exceptions", "09_pandas_basics",
    "10_pandas_filter_group", "11_matplotlib", "12_io_excel", "13_scipy_stats",
    "14_sklearn_intro", "15_ab_text", "16_classes_oop", "17_decorators_props",
    "18_generators_iter", "19_regex", "20_hr_pandas", "20_numpy_basics",
    "21_datetime_ts", "21_hr_viz", "22_hr_model", "22_statsmodels",
    "23_sklearn_advanced", "24_real_world_data",
)


def _topics():
    return load_language(LANG)


def _problems():
    return [p for t in _topics() for p in t.problems]


def test_题数121_且topic27():
    topics = _topics()
    problems = [p for t in topics for p in t.problems]
    assert len(topics) == EXPECTED_TOPICS, f"python topic 数漂移：{len(topics)} != {EXPECTED_TOPICS}"
    assert len(problems) == EXPECTED_PROBLEMS, f"python 题数漂移：{len(problems)} != {EXPECTED_PROBLEMS}"


def test_topic_slug集合精确():
    slugs = tuple(t.slug for t in _topics())
    assert slugs == EXPECTED_SLUGS, (
        f"python topic slug 集合漂移：\n新增={sorted(set(slugs) - set(EXPECTED_SLUGS))}\n"
        f"缺失={sorted(set(EXPECTED_SLUGS) - set(slugs))}"
    )


def test_difficulty直方图精确():
    got = dict(sorted(collections.Counter(p.difficulty for p in _problems()).items()))
    assert got == EXPECTED_DIFF, f"python difficulty 分布漂移：{got} != {EXPECTED_DIFF}"
    assert set(got) <= {1, 2, 3, 4, 5}, f"difficulty 出现越界档位：{sorted(got)}"
    # python 题库无 5 档题——保留为显式事实，避免「以为有 5 档」的误读
    assert got.get(5, 0) == 0, "python 题库出现 difficulty=5（基线为 0，须有意变更）"


def test_答案字段完备计数精确():
    problems = _problems()
    fields = collections.Counter()
    for p in problems:
        for key in ("expected_output", "expected_rows", "tests", "rubric", "reference_answer"):
            if getattr(p, key, None):
                fields[key] += 1
    assert dict(fields) == {
        "expected_output": 113, "tests": 46, "rubric": 8, "reference_answer": 8,
    }, f"python 答案字段计数漂移：{dict(fields)}"
    # python 题库不产出 expected_rows（那是 sql 的字段）
    assert "expected_rows" not in fields, "python 题库意外出现 expected_rows"


def test_judge_mode与hints完备():
    problems = _problems()
    judge = dict(collections.Counter(p.judge_mode for p in problems))
    assert judge == {"run": 113, "ai_open": 8}, f"python judge_mode 分布漂移：{judge}"
    missing = [p.id for p in problems if not p.hints]
    assert missing == [], f"python 缺 hints 名单漂移：{sorted(missing)}"
    # judge_mode=run 必须带可机判答案字段（expected_output 或 tests）
    bad = [p.id for p in problems if p.judge_mode == "run"
           and not (p.expected_output or p.tests)]
    assert bad == [], f"run 模式却无可机判字段：{bad}"
