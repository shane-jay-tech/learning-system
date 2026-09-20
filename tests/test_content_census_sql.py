# -*- coding: utf-8 -*-
"""sql 题库纵向普查钉桩（l920-04）。

口径同 l920-01，只读题库文件，零写库零源码改动。
sql 专属：expected_rows 形态（每题为行列表，行数＝该题结果集行数）＋建表语句 setup_sql 存在性。

实测基线（2026-09-19）：
  题数 54 / topic 12；difficulty 直方图 {1:12, 2:22, 3:19, 4:1}
  setup_sql 54/54 存在；expected_rows 54/54 且恒为 list，行数直方图 {1:12,2:10,3:14,4:7,5:9,6:1,7:1}
  judge_mode 全 run；hints 缺失 0 题
"""
import collections

from core.loader import load_language

LANG = "sql"
EXPECTED_TOPICS = 12
EXPECTED_PROBLEMS = 54
EXPECTED_DIFF = {1: 12, 2: 22, 3: 19, 4: 1}
EXPECTED_ROWS_LEN = {1: 12, 2: 10, 3: 14, 4: 7, 5: 9, 6: 1, 7: 1}
EXPECTED_SLUGS = (
    "01_select_where", "02_aggregate", "03_orderby_having", "04_joins",
    "05_subqueries_case", "06_window_functions", "07_cte", "08_exists",
    "09_string_funcs", "10_date_funcs", "11_null_handling", "12_people_analytics",
)


def _topics():
    return load_language(LANG)


def _problems():
    return [p for t in _topics() for p in t.problems]


def test_题数54_且topic12():
    topics = _topics()
    problems = [p for t in topics for p in t.problems]
    assert len(topics) == EXPECTED_TOPICS, f"sql topic 数漂移：{len(topics)} != {EXPECTED_TOPICS}"
    assert len(problems) == EXPECTED_PROBLEMS, f"sql 题数漂移：{len(problems)} != {EXPECTED_PROBLEMS}"


def test_topic_slug集合精确():
    slugs = tuple(t.slug for t in _topics())
    assert slugs == EXPECTED_SLUGS, (
        f"sql topic slug 集合漂移：新增={sorted(set(slugs) - set(EXPECTED_SLUGS))} "
        f"缺失={sorted(set(EXPECTED_SLUGS) - set(slugs))}"
    )


def test_difficulty直方图精确():
    got = dict(sorted(collections.Counter(p.difficulty for p in _problems()).items()))
    assert got == EXPECTED_DIFF, f"sql difficulty 分布漂移：{got} != {EXPECTED_DIFF}"


def test_setup_sql全覆盖():
    """sql 题的判分依赖建表/样例数据；缺 setup_sql 等于该题跑不起来。"""
    problems = _problems()
    missing = [p.id for p in problems if not (p.setup_sql and p.setup_sql.strip())]
    assert missing == [], f"sql 缺 setup_sql：{missing}"
    assert len(problems) == 54, "前置：sql 题数须为 54 才谈得上全覆盖"


def test_expected_rows形态与行数直方图精确():
    problems = _problems()
    shape = collections.Counter()
    lens = collections.Counter()
    for p in problems:
        if isinstance(p.expected_rows, list):
            shape["list"] += 1
            lens[len(p.expected_rows)] += 1
        else:
            shape[type(p.expected_rows).__name__] += 1
    assert dict(shape) == {"list": 54}, f"sql expected_rows 外层形态漂移：{dict(shape)}"
    assert dict(sorted(lens.items())) == EXPECTED_ROWS_LEN, (
        f"sql expected_rows 行数直方图漂移：{dict(sorted(lens.items()))} != {EXPECTED_ROWS_LEN}")
    # 行实测为「值列表」（无列名），且非空——照现状翻桩
    bad = [p.id for p in problems
           if not all(isinstance(row, list) and row for row in p.expected_rows)]
    assert bad == [], f"sql expected_rows 含非 list/空行：{bad}"
    total_rows = sum(len(p.expected_rows) for p in problems)
    assert total_rows == 160, f"sql expected_rows 总行数漂移：{total_rows} != 160"
    # 值列表首行样例（01_select_all：id,name,score 三列）——防列数/口径静默变化
    first = next(p for p in problems if p.id == "sql/01_select_where/01_select_all")
    assert first.expected_rows[0] == [1, "Alice", 92], (
        f"sql 首题 expected_rows 值漂移：{first.expected_rows[0]!r}")


def test_judge与hints完备():
    problems = _problems()
    judge = dict(collections.Counter(p.judge_mode for p in problems))
    assert judge == {"run": 54}, f"sql judge_mode 分布漂移：{judge}"
    missing = [p.id for p in problems if not p.hints]
    assert missing == [], f"sql 缺 hints 名单漂移：{sorted(missing)}"
