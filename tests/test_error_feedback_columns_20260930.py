# -*- coding: utf-8 -*-
"""caret 列定位（D-12 修法：1247 登记 → l927-02 落地）：Python/R/SQL 三语言 locate_column。

钉三件事：
  ① Python caret 列：几何真值全部来自本机 CPython 3.12.9 实采
     （tmp/l927-02 探针：`print(nope)` caret idx 10 → 列 7；`print(` idx 9 → 列 6；
     函数内 `1/0` `~^~` idx 11 → 列 8）。列号锚定**最后一个 main.py 帧**——
     3.11+ 每帧都带 caret，取"最后一个 caret 块"会指到库帧头上（本件有合成反例钉住）。
  ② R：本机无 Rscript ⇒ 合成钉 R ≥ 4.3 `行:列:` 报文形态（沿 1247 L-9 先例，
     工具链在位窗复测）；含 "Error" 行限定防学生自己打印的时间戳误判。
  ③ SQL：SQLite 报文不带任何位置信息 ⇒ 恒 None——这是**实测契约**（真跑 SQLRunner 验），
     不是缺口；宁缺勿错，绝不瞎报一个列号。
cpp 两形态定位回归不动（tests/test_error_feedback_rows.py::test_cpp_行列定位 继续守）。

复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_error_feedback_columns_20260930.py -q
"""
from types import SimpleNamespace

from core.judge import _row_feedback
from core.runners import error_feedback as ef
from core.runners.python_runner import PythonRunner
from core.runners.sql_runner import SQLRunner

# —— 本机 CPython 3.12.9 实采的 stderr 骨架（路径换成合成路径，几何逐字保留）——
NAMEERROR_312 = (
    "Traceback (most recent call last):\n"
    '  File "C:/tmp/ls_py_x/main.py", line 11, in <module>\n'
    "    print(nope)\n"
    "          ^^^^\n"
    "NameError: name 'nope' is not defined. Did you mean: 'None'?\n"
)
SYNTAX_312 = (
    '  File "C:/tmp/ls_py_x/main.py", line 9\n'
    "    print(\n"
    "         ^\n"
    "SyntaxError: '(' was never closed\n"
)
# 函数内错误：两个帧都带 caret，必须锚到**最后**的 main.py 帧（`1/0` 那帧）
INNER_312 = (
    "Traceback (most recent call last):\n"
    '  File "C:/tmp/ls_py_x/main.py", line 9, in <module>\n'
    "    print(f())\n"
    "          ^^^\n"
    '  File "C:/tmp/ls_py_x/main.py", line 8, in f\n'
    "    return 1/0\n"
    "           ~^~\n"
    "ZeroDivisionError: division by zero\n"
)
# 库帧插队反例：最后一个 caret 块属于库帧，main.py 帧本身没有 caret ⇒ 必须 None
LIB_FRAME_312 = (
    "Traceback (most recent call last):\n"
    '  File "C:/tmp/ls_py_x/main.py", line 9, in <module>\n'
    "    print(numpy.frobnicate(x))\n"
    '  File "C:/py/site-packages/numpy/__init__.py", line 300, in frobnicate\n'
    "    return _core.frobnicate(x)\n"
    "            ^^^^^^^^^^^^^^^^^^^\n"
    "ValueError: bad shape\n"
)


# ---------------------------------------------------------------- ① Python
def test_python_runtime_caret_列_实采几何():
    assert ef.locate_column("python", NAMEERROR_312) == 7   # nope 起点在去缩进行第 7 列
    assert ef.locate_column("agent_dev", NAMEERROR_312) == 7
    assert ef.locate("python", NAMEERROR_312) == 5         # 行折算不受本单影响（11-6）
    assert ef.where_phrase("python", NAMEERROR_312) == "第 5 行第 7 列："


def test_python_syntax_caret_列_实采几何():
    assert ef.locate_column("python", SYNTAX_312) == 6     # `(` 未闭合，caret 在第 6 列


def test_python_函数内错误_锚定最后一个main帧而非最后一个caret块():
    # `~^~` 形态：~ 画在 1 上，^ 指向 / ——取 ^ 的位置
    assert ef.locate("python", INNER_312) == 2             # 8-6=2，学生第 2 行
    assert ef.locate_column("python", INNER_312) == 8      # `/` 在去缩进行 `return 1/0` 第 8 列


def test_python_库帧插队_宁缺勿错返回None():
    assert ef.locate_column("python", LIB_FRAME_312) is None


def test_python_无caret_仍返回None_行反馈形态不变():
    # 既有 RAW_NAMEERROR 骨架（无 caret 行）：列继续缺省，"第 N 行："话术逐字不变
    no_caret = ('Traceback (most recent call last):\n'
                '  File "C:/tmp/ls_py_x/main.py", line 11, in <module>\n'
                '    print(nope)\n'
                "NameError: name 'nope' is not defined\n")
    assert ef.locate_column("python", no_caret) is None
    assert ef.where_phrase("python", no_caret) == "第 5 行："


def test_python_真runner端到端_行号列号一起进反馈():
    r = PythonRunner().run("a = 1\nb = 2\nc = a + b\nprint('ok')\nprint(nope)\n")
    assert ef.locate("python", r.stderr) == 5
    assert ef.locate_column("python", r.stderr) == 7
    hint = _row_feedback("python", r)
    assert hint.startswith("第 5 行第 7 列："), hint
    r2 = PythonRunner().run("def f():\n    return 1/0\nprint(f())\n")
    assert ef.locate("python", r2.stderr) == 2 and ef.locate_column("python", r2.stderr) == 8


# ---------------------------------------------------------------- ② R（合成钉）
def test_r_解析错_行列表_合成钉():
    assert ef.locate_column("r", 'Error: main.R:2:7: unexpected symbol\n1: x <- 1\n2: y y\n') == 7
    assert ef.locate_column("r", 'Error: <text>:3:5: unexpected symbol\n') == 5


def test_r_运行期错误不带位置_返回None():
    assert ef.locate_column("r", "Error in print(x) : object 'x' not found\nExecution halted\n") is None


def test_r_时间戳不误判_限定Error行():
    # 学生自己 print 的时间戳形如 12:30: … 不在 Error 行上 ⇒ 不许当坐标
    assert ef.locate_column("r", 'print("12:30: ok")\nExecution halted\n') is None


# ---------------------------------------------------------------- ③ SQL（None 契约）
def test_sql_真runner语法错_报文无位置_恒None():
    r = SQLRunner().run("SELECT nam FROMm missing_table_x")  # 合法 SELECT 带坏表名→真到 SQLite 解析层
    assert r.ok is False and "near" in r.stderr.lower()
    assert ef.locate_column("sql", r.stderr) is None       # 实测契约：SQLite 报文不带位置
    assert ef.locate("sql", r.stderr) is None              # 行定位既有口径一并钉住


def test_sql_合成near报文_恒None():
    assert ef.locate_column("sql", 'near "SELEC": syntax error') is None


# ---------------------------------------------------------------- cpp 对照回归
def test_cpp_两形态列定位_行为不回归():
    a = "main.cpp:12:5: error: expected ';' before '}' token\n"
    b = "main.cpp(12:5): error: expected ';' before '}' token\n"
    assert ef.locate_column("cpp", a) == 5 and ef.locate_column("cpp", b) == 5
    assert ef.where_phrase("cpp", a) == "第 12 行第 5 列："


def test_cpp_无列形态_返回None():
    assert ef.locate_column("cpp", "main.cpp:12: error: expected ';'\n") is None


# ---------------------------------------------------------------- 判分零改动自证
def test_列定位纯函数_不吃ok_不改分类():
    for ok in (True, False):
        rr = SimpleNamespace(stderr=NAMEERROR_312, ok=ok, timed_out=False,
                             exit_code=1, error_kind="runtime")
        assert ef.classify("python", rr.stderr) == "undefined_name"
        assert _row_feedback("python", rr) == _row_feedback(
            "python", SimpleNamespace(stderr=NAMEERROR_312))
