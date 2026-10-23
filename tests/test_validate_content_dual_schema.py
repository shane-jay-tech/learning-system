# -*- coding: utf-8 -*-
"""l1023-012 双 schema 校验测试：paths yaml（路径定义 schema）vs exercise yaml（练习 schema）。

主判四例（任务书口径：两类 yaml 各验 1 例，合法过／非法拦）＋1 例现仓守卫
（content/paths/ 6 件现值在双 schema 下零 ERROR 零 WARN，防 schema 过严回归）。
scan(content_dir=...) 指向 tmp 目录，零触真库。
"""
from scripts import validate_content
from scripts.validate_content import scan

PATHS_LEGAL = """title: 测试路径
subtitle: 双 schema 测试
icon: "T"
estimated_hours: 3
milestones:
  - id: m1
    title: 里程碑一
    description: 里程碑描述
    topics:
      - "python/01_basics"
"""

PATHS_ILLEGAL = """title: 坏路径
milestones:
  - id: m1
    title: 里程碑一
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

EXERCISE_ILLEGAL = """title: 缺字段的题
topic: "python/01_basics"
"""


def _write(tmp_path, relpath, text):
    p = tmp_path / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def test_paths_schema_legal_passes(tmp_path):
    _write(tmp_path, "content/paths/legal.yaml", PATHS_LEGAL)
    files, parse_errors, field_issues, path_issues, _ = scan(
        content_dir=str(tmp_path / "content")
    )
    assert parse_errors == []
    assert [f["domain"] for f in files] == ["paths"]
    assert field_issues == []  # 练习 schema 不越权套在 paths/ 上
    assert path_issues == []  # 合法路径定义零告警


def test_paths_schema_illegal_blocked(tmp_path):
    _write(tmp_path, "content/paths/bad.yaml", PATHS_ILLEGAL)
    _, _, _, path_issues, _ = scan(content_dir=str(tmp_path / "content"))
    errors = [i for i in path_issues if i["severity"] == "error"]
    assert errors, "milestone 缺 topics/description 必须被 ERROR 拦下"
    joined = "；".join(i["message"] for i in errors)
    assert "milestone#1" in joined
    assert "topics" in joined and "description" in joined


def test_exercise_schema_legal_passes(tmp_path):
    _write(tmp_path, "content/python/01_basics/legal.yaml", EXERCISE_LEGAL)
    _, parse_errors, field_issues, path_issues, _ = scan(
        content_dir=str(tmp_path / "content")
    )
    assert parse_errors == []
    assert field_issues == []  # 合法练习零告警
    assert path_issues == []  # 练习文件不进路径 schema 分支


def test_exercise_schema_illegal_blocked(tmp_path):
    _write(tmp_path, "content/python/01_basics/bad.yaml", EXERCISE_ILLEGAL)
    _, _, field_issues, _, _ = scan(content_dir=str(tmp_path / "content"))
    errors = [i for i in field_issues if i["severity"] == "error"]
    assert errors, "练习缺 statement/difficulty 必须被 ERROR 拦下"
    assert set(errors[0]["missing"]) == {"statement", "difficulty"}
    assert errors[0]["no_answer"] and errors[0]["no_hints"]


def test_real_repo_paths_clean_under_dual_schema():
    """现仓守卫：content/paths/ 6 件在路径定义 schema 下零 ERROR 零 WARN。"""
    files, parse_errors, _, path_issues, _ = scan(domain_filter={"paths"})
    assert len(files) == 6
    assert parse_errors == []
    assert [i for i in path_issues if i["severity"] == "error"] == []
    assert [i for i in path_issues if i["severity"] == "warn"] == []
    assert validate_content.PATHS_DIRNAME == "paths"  # 双 schema 按目录判的锚
