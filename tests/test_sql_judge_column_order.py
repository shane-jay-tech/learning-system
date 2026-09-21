"""l921-03：SQL 判分比对口径钉桩 ＋ setup_sql 方言可执行普查。

钉的是 l920-04 留的未查项「判分只能按列序比对——列顺序变了而值相同时判分器行为
取决于实现（本单未查判分侧比对逻辑）」。现行为由 `_rows_equal` / `_cell_eq` 的实现决定，
本文件把它变成断言：**改判分口径必须显式改这里，不允许悄悄发生**。
本单零改判分逻辑（红线：判分属正确性核心，只钉不改）。
可复跑：python -m pytest tests/test_sql_judge_column_order.py -q（或 -k sql）
"""
import glob
import sqlite3

import yaml
from pathlib import Path

from core.judge import _cell_eq, _rows_equal
from core.loader import load_language
from core.runners.sql_runner import SQLRunner

SQL_DIR = Path(__file__).resolve().parent.parent / "content" / "sql"


# ---------- ① 位置敏感（列序 / 行序） ----------

def test_sql_judge_is_column_order_sensitive():
    """同值换列序 ⇒ 判不等。这是现行为，不是 bug 断言：expected_rows 按位置对齐。"""
    assert _rows_equal([[1, "A"], [2, "B"]], [[1, "A"], [2, "B"]]) is True
    assert _rows_equal([[1, "A"], [2, "B"]], [["A", 1], ["B", 2]]) is False


def test_sql_judge_is_row_order_sensitive_and_needs_order_by():
    """行序同样敏感：没有 ORDER BY 时同一查询两次返回不同行序即可判错（题目侧必须自己定序）。"""
    assert _rows_equal([[1], [2]], [[2], [1]]) is False
    assert _rows_equal([[1], [2], [3]], [[1], [2]]) is False, "行数不等必须先短路"


# ---------- ② 单元格宽松面（别被"严格相等"误伤） ----------

def test_sql_judge_cell_equality_caliber():
    assert _cell_eq(1, 1.0) is True, "数值 1 与 1.0 同值"
    assert _cell_eq(True, 1) is True, "bool 分支按真值比较（实测口径，反直觉但已锁）"
    assert _cell_eq("1 ", "1") is False, "字符串严格相等，不做空白剥离"
    assert _cell_eq(None, None) is True and _cell_eq(None, 0) is False


# ---------- ③ 端到端：真跑 SQL 再走同一比较器 ----------

def test_sql_judge_end_to_end_positional_reject_and_accept():
    runner = SQLRunner()
    setup = "CREATE TABLE t (id INTEGER, name TEXT); INSERT INTO t VALUES (1,'A'),(2,'B');"
    res = runner.run("SELECT id, name FROM t ORDER BY id;", expected={"setup_sql": setup})
    assert res.ok and res.rows is not None, res.stderr
    rows = [list(r) for r in res.rows]
    assert _rows_equal(rows, [[1, "A"], [2, "B"]]) is True, "按题目列序应通过"
    assert _rows_equal(rows, [["A", 1], ["B", 2]]) is False, "列序颠倒必须判不过"


# ---------- ④ setup_sql 方言可执行普查（本机 sqlite3） ----------

def test_sql_setup_statements_all_execute_locally():
    """每道题的 setup_sql 必须能在本机 sqlite3 跑通——列方言（如 MySQL 反引号、窗口函数版本）
    一旦混进题面，这里就是第一道网。不可执行的题 id 会直接出现在断言消息里。"""
    targets = []
    for topic in load_language("sql"):
        for problem in (getattr(topic, "problems", None) or []):
            if getattr(problem, "setup_sql", None):
                targets.append((str(problem.id), problem.setup_sql))
    broken = []
    for pid, sql in targets:
        con = sqlite3.connect(":memory:")
        try:
            con.executescript(sql)
            con.commit()
        except Exception as exc:  # noqa: BLE001 - 普查要把任何方言不兼容都收上来
            broken.append(f"{pid}: {exc}")
        finally:
            con.close()
    assert targets, "loader 未取到任何 setup_sql，普查口径可能已失效（content/sql 结构变了？）"
    assert not broken, "以下题目的 setup_sql 在本机 sqlite3 不可执行：" + " | ".join(broken)


def test_sql_setup_census_two_independent_calibers_agree():
    """loader 口径 vs 直接 glob yaml 口径必须同数——两个口径不一致说明有题没被 loader 收到。"""
    via_loader = sum(
        1 for topic in load_language("sql") for p in (getattr(topic, "problems", None) or [])
        if getattr(p, "setup_sql", None)
    )
    files = sorted(glob.glob(str(SQL_DIR / "*" / "*.yaml")))
    via_yaml = 0
    for f in files:
        data = yaml.safe_load(Path(f).read_text(encoding="utf-8")) or {}
        if data.get("setup_sql"):
            via_yaml += 1
    assert via_loader == via_yaml > 0, f"loader={via_loader} yaml={via_yaml} 两口径不一致"
