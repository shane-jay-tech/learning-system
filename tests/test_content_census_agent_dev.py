# -*- coding: utf-8 -*-
"""agent_dev 题库纵向普查钉桩（l920-05）。

口径同 l920-01，只读题库文件，零写库零源码改动。
agent_dev 专属：rubric 键集形态——多数题为「多评分点」题（judge_mode=ai_open），
loader 把 yaml 的 rubric list 渲染成「- 要点」行文本；本文件钉 rubric 行数分布与行前缀契约。

实测基线（2026-09-19）：
  题数 78 / topic 15；difficulty 直方图 {1:11, 2:32, 3:27, 4:7, 5:1}
  rubric：48 题有（行数 3:5, 4:21, 5:10, 6:9, 7:3），30 题无
  答案面：expected_output 30、tests 1、reference_answer 38；judge_mode run 30 / ai_open 48
  hints 缺失 0 题
"""
import collections

from core.loader import load_language

LANG = "agent_dev"
EXPECTED_TOPICS = 15
EXPECTED_PROBLEMS = 78
EXPECTED_DIFF = {1: 11, 2: 32, 3: 27, 4: 7, 5: 1}
EXPECTED_RUBRIC_LINES = {3: 5, 4: 21, 5: 10, 6: 9, 7: 3}
EXPECTED_SLUGS = (
    "01_git_basics", "02_debug_read", "03_spec_writing", "04_review_agent",
    "05_modular_config", "06_frontier", "07_data_security", "07_write_spec",
    "08_read_code", "08_review_pr", "09_decompose", "10_debug_logs",
    "11_real_tasks", "12_spec_iteration", "13_multi_round",
)


def _topics():
    return load_language(LANG)


def _problems():
    return [p for t in _topics() for p in t.problems]


def test_题数78_且topic15():
    topics = _topics()
    problems = [p for t in topics for p in t.problems]
    assert len(topics) == EXPECTED_TOPICS, f"agent_dev topic 数漂移：{len(topics)} != {EXPECTED_TOPICS}"
    assert len(problems) == EXPECTED_PROBLEMS, f"agent_dev 题数漂移：{len(problems)} != {EXPECTED_PROBLEMS}"


def test_topic_slug集合精确():
    slugs = tuple(t.slug for t in _topics())
    assert slugs == EXPECTED_SLUGS, (
        f"agent_dev topic slug 集合漂移：新增={sorted(set(slugs) - set(EXPECTED_SLUGS))} "
        f"缺失={sorted(set(EXPECTED_SLUGS) - set(slugs))}"
    )


def test_difficulty直方图精确():
    got = dict(sorted(collections.Counter(p.difficulty for p in _problems()).items()))
    assert got == EXPECTED_DIFF, f"agent_dev difficulty 分布漂移：{got} != {EXPECTED_DIFF}"
    # agent_dev 是五语言里唯一覆盖满 1-5 档的题库
    assert set(got) == {1, 2, 3, 4, 5}, f"agent_dev 应覆盖 1-5 全档：{sorted(got)}"


def test_rubric行数直方图与行前缀契约():
    problems = _problems()
    lines_dist = collections.Counter()
    no_rubric = 0
    list_style = 0   # yaml rubric 为 list → loader 渲染成「- 要点」行
    str_style = 0    # yaml rubric 为字符串 → loader 原样透传（含「评分维度：」「1. …」等混合前缀）
    for p in problems:
        if not p.rubric:
            no_rubric += 1
            continue
        lines = [l for l in p.rubric.split("\n") if l.strip()]
        lines_dist[len(lines)] += 1
        if all(l.startswith("- ") for l in lines):
            list_style += 1
        else:
            str_style += 1
    assert no_rubric == 30, f"agent_dev 无 rubric 题数漂移：{no_rubric} != 30"
    assert dict(sorted(lines_dist.items())) == EXPECTED_RUBRIC_LINES, (
        f"agent_dev rubric 行数分布漂移：{dict(sorted(lines_dist.items()))} != {EXPECTED_RUBRIC_LINES}")
    # 双形态分布（照现状翻桩；yaml 侧实测 list 36 / str 12）
    assert (list_style, str_style) == (36, 12), (
        f"agent_dev rubric 形态漂移：list式={list_style} str式={str_style}（基线 36/12）")


def test_judge_mode与答案面配对():
    problems = _problems()
    fields = collections.Counter()
    for p in problems:
        for key in ("expected_output", "tests", "rubric", "reference_answer"):
            if getattr(p, key, None):
                fields[key] += 1
    assert dict(fields) == {
        "expected_output": 30, "tests": 1, "rubric": 48, "reference_answer": 38,
    }, f"agent_dev 答案字段计数漂移：{dict(fields)}"
    judge = dict(collections.Counter(p.judge_mode for p in problems))
    assert judge == {"run": 30, "ai_open": 48}, f"agent_dev judge_mode 分布漂移：{judge}"
    # ai_open 必须带 rubric（否则无评分点可依）
    bad = [p.id for p in problems if p.judge_mode == "ai_open" and not p.rubric]
    assert bad == [], f"ai_open 却无 rubric：{bad}"
    missing = [p.id for p in problems if not p.hints]
    assert missing == [], f"agent_dev 缺 hints 名单漂移：{sorted(missing)}"
