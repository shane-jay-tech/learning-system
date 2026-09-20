# -*- coding: utf-8 -*-
"""cpp 题库纵向普查钉桩（l920-03）。

口径同 l920-01，只读题库文件，零写库零源码改动。
cpp 专属：编译型题 tests 字段为 list[dict]，dict 键集实测恒为 {expected_output, stdin}——
stdin 喂入 / expected_output 比对的「stdin→stdout 对」结构。

实测基线（2026-09-19）：
  题数 62 / topic 13；difficulty 直方图 {1:10, 2:31, 3:21}
  tests：45 题为 list[dict]，17 题为 None；键集恒 {"expected_output","stdin"}
  expected_output 62/62 全覆盖；judge_mode 全 run；hints 缺失 0 题
"""
import collections

from core.loader import load_language

LANG = "cpp"
EXPECTED_TOPICS = 13
EXPECTED_PROBLEMS = 62
EXPECTED_DIFF = {1: 10, 2: 31, 3: 21}
EXPECTED_SLUGS = (
    "01_io_and_vars", "02_branch_loop", "03_arrays_strings", "04_functions",
    "05_stl_basics", "06_iter_algo", "07_pointers_class", "08_inheritance",
    "09_operator_overload", "10_templates", "11_exceptions", "12_file_io",
    "13_move_semantics",
)


def _topics():
    return load_language(LANG)


def _problems():
    return [p for t in _topics() for p in t.problems]


def test_题数62_且topic13():
    topics = _topics()
    problems = [p for t in topics for p in t.problems]
    assert len(topics) == EXPECTED_TOPICS, f"cpp topic 数漂移：{len(topics)} != {EXPECTED_TOPICS}"
    assert len(problems) == EXPECTED_PROBLEMS, f"cpp 题数漂移：{len(problems)} != {EXPECTED_PROBLEMS}"


def test_topic_slug集合精确():
    slugs = tuple(t.slug for t in _topics())
    assert slugs == EXPECTED_SLUGS, (
        f"cpp topic slug 集合漂移：新增={sorted(set(slugs) - set(EXPECTED_SLUGS))} "
        f"缺失={sorted(set(EXPECTED_SLUGS) - set(slugs))}"
    )


def test_difficulty直方图精确():
    got = dict(sorted(collections.Counter(p.difficulty for p in _problems()).items()))
    assert got == EXPECTED_DIFF, f"cpp difficulty 分布漂移：{got} != {EXPECTED_DIFF}"


def test_tests形态_stdin_stdout对精确():
    """cpp tests 只有两种形态：None（17 题，纯固定输出）或 list[dict]（45 题）。
    dict 键集必须恒为 {expected_output, stdin}——多键/少键即契约破裂。"""
    problems = _problems()
    shape = collections.Counter()
    keysets = collections.Counter()
    for p in problems:
        t = p.tests
        if isinstance(t, list) and t and isinstance(t[0], dict):
            shape["list[dict]"] += 1
            for case in t:
                keysets[",".join(sorted(case.keys()))] += 1
        else:
            shape[type(t).__name__] += 1
    assert dict(shape) == {"list[dict]": 45, "NoneType": 17}, f"cpp tests 外层形态漂移：{dict(shape)}"
    assert dict(keysets) == {"expected_output,stdin": 45}, f"cpp tests 键集漂移：{dict(keysets)}"


def test_expected_output全覆盖_且judge与hints完备():
    problems = _problems()
    miss_out = [p.id for p in problems if not p.expected_output]
    assert miss_out == [], f"cpp 缺 expected_output：{miss_out}"
    judge = dict(collections.Counter(p.judge_mode for p in problems))
    assert judge == {"run": 62}, f"cpp judge_mode 分布漂移：{judge}"
    missing = [p.id for p in problems if not p.hints]
    assert missing == [], f"cpp 缺 hints 名单漂移：{sorted(missing)}"
