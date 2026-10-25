# -*- coding: utf-8 -*-
"""l1025-005 validator 语义检测档测试：占位 expected_output 逃检堵口。

两主判例（任务书口径：占位件被拦 1 例＋正常件过 1 例）＋2 边界例
（tests 内用例占位／顶层与 tests 期望不一致抽检）。scan(content_dir=...)
指向 tmp 目录，零触真库。
"""
from scripts.validate_content import scan, _is_placeholder

EXERCISE_PLACEHOLDER = """title: 占位题
topic: "python/01_basics"
difficulty: 1
statement: |
  计算两数之和。
starter_code: |
  print(1 + 1)
expected_output: |
  TODO 待补
hints:
  - "想一想加法"
"""

EXERCISE_LEGAL = """title: 两数之和
topic: "python/01_basics"
difficulty: 1
statement: |
  计算 1+1 并输出结果。
starter_code: |
  print(1 + 1)
expected_output: |
  2
hints:
  - "想一想加法"
"""

EXERCISE_TESTS_PLACEHOLDER = """title: 用例占位题
topic: "python/01_basics"
difficulty: 1
statement: |
  读入并输出。
starter_code: |
  print(input())
tests:
  - stdin: "5\\n"
    expected_output: "占位文本\\n"
hints:
  - "直接输出"
"""

EXERCISE_STALE_TOP = """title: 顶层陈旧题
topic: "python/01_basics"
difficulty: 1
statement: |
  读入并输出两倍。
starter_code: |
  print(int(input()) * 2)
expected_output: |
  4
tests:
  - stdin: "3\\n"
    expected_output: "6\\n"
  - stdin: "5\\n"
    expected_output: "10\\n"
hints:
  - "乘二"
"""


def _write(tmp_path, relpath, text):
    p = tmp_path / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _scan_one(tmp_path, name, text):
    _write(tmp_path, f"content/python/01_basics/{name}", text)
    _, parse_errors, field_issues, _, _ = scan(
        content_dir=str(tmp_path / "content"), domain_filter={"python"}
    )
    assert parse_errors == []
    return field_issues


def test_占位expected_output被拦(tmp_path):
    issues = _scan_one(tmp_path, "04_placeholder.yaml", EXERCISE_PLACEHOLDER)
    assert len(issues) == 1 and issues[0]["severity"] == "warn"
    assert any("占位文本" in m for m in issues[0]["semantic"])


def test_正常件过语义档(tmp_path):
    issues = _scan_one(tmp_path, "02_legal.yaml", EXERCISE_LEGAL)
    # 既有字段维度零告警，语义维度零告警
    assert issues == []


def test_tests内用例占位被点名列(tmp_path):
    issues = _scan_one(tmp_path, "06_tests_placeholder.yaml", EXERCISE_TESTS_PLACEHOLDER)
    assert len(issues) == 1
    assert any("tests#1" in m and "占位文本" in m for m in issues[0]["semantic"])


def test_顶层与tests期望不一致抽检(tmp_path):
    issues = _scan_one(tmp_path, "08_stale_top.yaml", EXERCISE_STALE_TOP)
    assert len(issues) == 1
    assert any("不一致" in m for m in issues[0]["semantic"])


def test_占位判别_短示例拦长文本放():
    assert _is_placeholder("示例")
    assert _is_placeholder("输出示例")
    assert not _is_placeholder("参照下面的示例格式逐行输出三人姓名与部门")  # 长合法文本
    assert _is_placeholder("TODO")
    assert _is_placeholder("placeholder")
    assert not _is_placeholder("42")
