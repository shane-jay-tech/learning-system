# -*- coding: utf-8 -*-
"""content yaml schema 边界 fuzz 钉桩（2026-09-05 夜 1023）。

两类断言：
- 优雅路径：畸形输入被跳过/降级/校验器报 error（不 crash、不静默污染）；
- 洞钉桩：当前会 crash 的输入用 pytest.raises 钉住现状并标「发现的洞」——
  修复生产代码时应有意地翻转这些用例（改为优雅断言）。

样本全部内联字符串，经 tmp_path 临时 content 目录注入，不碰真实题库。
"""
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import loader


LANG = "python"


def _write(tmp_path, rel, text, binary=False):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        p.write_bytes(text)
    else:
        p.write_text(text, encoding="utf-8")
    return p


def _load(tmp_path, lang=LANG):
    loader.invalidate_cache()
    return loader.load_language(lang, content_dir=str(tmp_path / "content"))


GOOD = """\
title: "正常题"
topic: "01_demo"
difficulty: 2
tags: ["demo"]
statement: "题目陈述"
starter_code: "# code"
hints: ["h1"]
"""


class TestLoaderGraceful:
    """加载器优雅路径钉桩：跳过或降级，不 crash。"""

    def _topic(self, tmp_path, body, name="01_demo", fname="01_ok.yaml"):
        _write(tmp_path, f"content/{LANG}/{name}/{fname}", body)
        return tmp_path

    def test_yaml_syntax_error_skipped(self, tmp_path):
        """语法错误（未闭合引号）：整文件跳过，专题仍加载。"""
        self._topic(tmp_path, 'title: "unclosed\nstatement: x')
        topics = _load(tmp_path)
        assert len(topics) == 1 and topics[0].problems == []

    def test_empty_file_loads_with_defaults(self, tmp_path):
        """空 yaml → {}：以全默认值静默装载（现行契约，非洞）。"""
        self._topic(tmp_path, "")
        topics = _load(tmp_path)
        p = topics[0].problems[0]
        assert p.title == "01_ok" and p.statement == "" and p.difficulty == 1

    def test_difficulty_numeric_string_coerced(self, tmp_path):
        self._topic(tmp_path, GOOD.replace("difficulty: 2", 'difficulty: "3"'))
        p = _load(tmp_path)[0].problems[0]
        assert p.difficulty == 3

    def test_tags_string_not_iterated(self, tmp_path):
        self._topic(tmp_path, GOOD.replace('tags: ["demo"]', "tags: single_tag"))
        p = _load(tmp_path)[0].problems[0]
        assert p.tags == ["single_tag"]  # 不拆字符

    def test_hints_string_coerced(self, tmp_path):
        self._topic(tmp_path, GOOD.replace('hints: ["h1"]', "hints: 只有一条提示"))
        p = _load(tmp_path)[0].problems[0]
        assert p.hints == ["只有一条提示"]

    def test_rubric_list_joined_to_bullets(self, tmp_path):
        self._topic(tmp_path, GOOD + "rubric:\n  - 甲\n  - 乙\n")
        p = _load(tmp_path)[0].problems[0]
        assert p.rubric == "- 甲\n- 乙"

    def test_title_missing_falls_back_to_filename(self, tmp_path):
        self._topic(tmp_path, GOOD.replace('title: "正常题"\n', ""))
        p = _load(tmp_path)[0].problems[0]
        assert p.title == "01_ok"

    def test_statement_null_becomes_empty(self, tmp_path):
        self._topic(tmp_path, GOOD.replace('statement: "题目陈述"', "statement: ~"))
        p = _load(tmp_path)[0].problems[0]
        assert p.statement == ""

    def test_deep_nesting_no_crash(self, tmp_path):
        """合法但深嵌套的杂项字段：加载不递归爆炸。"""
        deep = "[" * 200 + "]" * 200
        self._topic(tmp_path, GOOD + f"extra_field: {deep}\n")
        topics = _load(tmp_path)
        assert len(topics[0].problems) == 1

    def test_bad_indent_skipped(self, tmp_path):
        self._topic(tmp_path, "title: x\n  bad: indent\n")
        topics = _load(tmp_path)
        assert topics[0].problems == []


class TestLoaderHoles:
    """原「发现的洞」四用例：2026-09-06 loader 隔离修复后已翻转为新行为断言——
    坏文件进诊断记录（loader.get_load_diagnostics），专题框照常加载，不 crash。"""

    def test_hole1_yaml_root_is_list_isolated(self, tmp_path):
        # 原洞 #1：yaml 根为 list 时 data.get → AttributeError；现在整文件隔离。
        _write(tmp_path, f"content/{LANG}/01_demo/01_root.yaml", "- a\n- b\n")
        topics = _load(tmp_path)
        assert len(topics) == 1 and topics[0].problems == []
        diags = loader.get_load_diagnostics()
        assert len(diags) == 1
        assert diags[0].path.endswith("01_root.yaml")
        assert diags[0].error_type == "TypeError"  # root 非 mapping

    def test_hole2_yaml_root_is_scalar_isolated(self, tmp_path):
        # 原洞 #1 同源：根为标量 → 同样隔离为 TypeError。
        _write(tmp_path, f"content/{LANG}/01_demo/01_root.yaml", "just_a_string\n")
        topics = _load(tmp_path)
        assert len(topics) == 1 and topics[0].problems == []
        diags = loader.get_load_diagnostics()
        assert len(diags) == 1
        assert diags[0].path.endswith("01_root.yaml")
        assert diags[0].error_type == "TypeError"

    def test_hole3_difficulty_non_numeric_isolated(self, tmp_path):
        # 原洞 #2：difficulty: "hard" → int() ValueError；现在该文件进诊断，不炸整批。
        _write(tmp_path, f"content/{LANG}/01_demo/01_diff.yaml",
               GOOD.replace("difficulty: 2", 'difficulty: "hard"'))
        topics = _load(tmp_path)
        assert len(topics) == 1 and topics[0].problems == []
        diags = loader.get_load_diagnostics()
        assert len(diags) == 1
        assert diags[0].path.endswith("01_diff.yaml")
        assert diags[0].error_type == "ValueError"

    def test_hole4_non_utf8_file_isolated(self, tmp_path):
        # 原洞 #3：非 UTF-8 字节 → UnicodeDecodeError；现在进诊断记录。
        _write(tmp_path, f"content/{LANG}/01_demo/01_bin.yaml",
               b"\xff\xfe\x00bad\x00", binary=True)
        topics = _load(tmp_path)
        assert len(topics) == 1 and topics[0].problems == []
        diags = loader.get_load_diagnostics()
        assert len(diags) == 1
        assert diags[0].path.endswith("01_bin.yaml")
        assert diags[0].error_type == "UnicodeDecodeError"


class TestDeepAuditErrors:
    """校验器钉桩：畸形结构报 error 而非 crash/漏报（monkeypatch ROOT 指向 tmp）。"""

    @pytest.fixture()
    def audit(self, monkeypatch, tmp_path):
        import scripts.audit_content_deep as acd
        monkeypatch.setattr(acd, "ROOT", tmp_path)
        (tmp_path / "content").mkdir(parents=True, exist_ok=True)
        return acd.deep_audit

    def test_topic_field_mismatch_is_error(self, audit, tmp_path):
        _write(tmp_path, f"content/{LANG}/01_demo/01_a.yaml",
               GOOD.replace('topic: "01_demo"', 'topic: "99_other"'))
        errors, _ = audit()
        assert any("topic=" in e and "不一致" in e for e in errors)

    def test_duplicate_title_in_topic_is_error(self, audit, tmp_path):
        _write(tmp_path, f"content/{LANG}/01_demo/01_a.yaml", GOOD)
        _write(tmp_path, f"content/{LANG}/01_demo/02_b.yaml", GOOD)  # 同题名
        errors, _ = audit()
        assert any("同专题标题重复" in e for e in errors)

    def test_expected_rows_not_list_is_error(self, audit, tmp_path):
        _write(tmp_path, f"content/{LANG}/01_demo/01_a.yaml",
               GOOD.replace('topic: "01_demo"', 'topic: "01_demo"\nexpected_rows: "not-a-list"'))
        errors, _ = audit()
        assert any("expected_rows 必须是列表" in e for e in errors)

    def test_expected_rows_row_not_list_is_error(self, audit, tmp_path):
        _write(tmp_path, f"content/{LANG}/01_demo/01_a.yaml",
               GOOD.replace('topic: "01_demo"', 'topic: "01_demo"\nexpected_rows:\n  - "scalar-row"'))
        errors, _ = audit()
        assert any("行不是列表" in e for e in errors)

    def test_expected_rows_composite_cell_is_error(self, audit, tmp_path):
        _write(tmp_path, f"content/{LANG}/01_demo/01_a.yaml",
               GOOD.replace('topic: "01_demo"', 'topic: "01_demo"\nexpected_rows:\n  - [1, {a: 2}]'))
        errors, _ = audit()
        assert any("复合类型" in e for e in errors)

    def test_tests_not_list_is_error(self, audit, tmp_path):
        _write(tmp_path, f"content/{LANG}/01_demo/01_a.yaml",
               GOOD.replace('topic: "01_demo"', 'topic: "01_demo"\ntests: "oops"'))
        errors, _ = audit()
        assert any("tests 必须是列表" in e for e in errors)

    def test_tests_item_not_dict_is_error(self, audit, tmp_path):
        _write(tmp_path, f"content/{LANG}/01_demo/01_a.yaml",
               GOOD.replace('topic: "01_demo"', 'topic: "01_demo"\ntests:\n  - "plain-string"'))
        errors, _ = audit()
        assert any("必须是字典" in e for e in errors)

    def test_clean_file_zero_errors(self, audit, tmp_path):
        _write(tmp_path, f"content/{LANG}/01_demo/01_a.yaml", GOOD)
        errors, _ = audit()
        assert errors == []
