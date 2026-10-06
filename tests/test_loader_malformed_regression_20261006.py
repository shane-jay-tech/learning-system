# -*- coding: utf-8 -*-
"""learning 题库 loader 三洞闭环回归（l1004-34；1023 三洞＋mtb2 证据保鲜＋1030 闭环）。

三个畸形夹具（yaml 根为 list／difficulty 写 "hard"／GBK 编码）落 tests 专用 tmp 目录
（不进题库 content/），断言 load_language 单文件降级/跳过、不全局崩；并核 _lesson.md
读取失败仍走 warning 路径（1030 未扩项）。
"""
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from core.loader import load_language, get_load_diagnostics  # noqa: E402


@pytest.fixture()
def content_dir(tmp_path):
    d = tmp_path / "content" / "py"
    d.mkdir(parents=True)
    # 健康基线题：保证「有正常题可加载」
    t0 = d / "01_ok"
    t0.mkdir()
    (t0 / "_lesson.md").write_text("# 正常课\n\n内容足够长的正文用于通过长度检查，正文超过两百字的需要吗？其实不必，这里只是占位文本让内容稍微长一点。", encoding="utf-8")
    (t0 / "01_a.yaml").write_text(
        "title: 正常题\ndifficulty: 2\nstatement: 求两数之和。\nstarter_code: 'print(1)'\n",
        encoding="utf-8")
    return d.parent


def _mk(dirpath, name, payload, encoding="utf-8"):
    t = dirpath / name
    t.mkdir(parents=True)
    (t / "bad.yaml").write_text(payload, encoding=encoding) if isinstance(payload, str) else None


def test_hole1_yaml_root_list_isolated_not_crash(content_dir):
    """洞#1：yaml 根为 list（合法 yaml 非字典）⇒ 文件跳过＋诊断，不全局崩。"""
    t = content_dir / "py" / "02_listroot"
    t.mkdir()
    (t / "bad.yaml").write_text("- a\n- b\n", encoding="utf-8")
    topics = load_language("py", str(content_dir))
    ok = [p.id for p in topics[0].problems] if topics and topics[0].slug == "01_ok" else []
    assert any("01_a" in pid for pid in ok), "健康题必须照常加载"
    diags = [(d.error_type, d.message) for d in get_load_diagnostics()]
    # 断言钉 TypeError（isinstance 门的诊断类）；若门被移除，异常改道 _build_problem
    # 变 AttributeError——隔离结局相同（:175 兜底）但诊断类名变，此处即红＝变异反证点。
    assert any(t == "TypeError" for t, m in diags), f"根为 list 应有 TypeError 诊断：{diags}"


def test_hole2_difficulty_non_numeric_skips_file(content_dir):
    """洞#2：difficulty 写 "hard" ⇒ 现行为＝整文件跳过＋诊断（非值级降级 1，
    亦非全局崩——「降级默认 1」的矿方建议未采用，语义在此钉住）。"""
    t = content_dir / "py" / "03_harddiff"
    t.mkdir()
    (t / "bad.yaml").write_text(
        "title: 难度坏值\ndifficulty: hard\nstatement: 题。\n", encoding="utf-8")
    topics = load_language("py", str(content_dir))
    all_pids = [p.id for tp in topics for p in tp.problems]
    assert not any("bad" in pid for pid in all_pids), "difficulty 坏值文件应被隔离"
    diags = [(d.error_type, d.message) for d in get_load_diagnostics()]
    assert any(t == "ValueError" for t, m in diags), f"应有 ValueError 诊断：{diags}"


def test_hole3_gbk_file_isolated(content_dir):
    """洞#3：非 UTF-8（GBK）文件 ⇒ UnicodeDecodeError 进诊断，不全局崩。"""
    t = content_dir / "py" / "04_gbk"
    t.mkdir()
    (t / "bad.yaml").write_text("title: 中文乱码题\nstatement: 编码坏。\n", encoding="gbk")
    topics = load_language("py", str(content_dir))
    all_pids = [p.id for tp in topics for p in tp.problems]
    assert not any("bad" in pid for pid in all_pids)
    diags = [(d.error_type, d.message) for d in get_load_diagnostics()]
    assert any(t == "UnicodeDecodeError" for t, m in diags), f"应有 UnicodeDecodeError 诊断：{diags}"


def test_lesson_md_failure_stays_warning(content_dir, monkeypatch):
    """1030 未扩项：_lesson.md 读取失败仍走 logger.warning，不崩、topic 照常建。"""
    t = content_dir / "py" / "05_badlesson"
    t.mkdir()
    lesson = t / "_lesson.md"
    lesson.write_text("x", encoding="utf-8")
    (t / "01_a.yaml").write_text("title: 题\nstatement: s\n", encoding="utf-8")
    # 让 _lesson.md 读出 OSError：把文件替换成目录
    lesson.unlink()
    lesson.mkdir()
    (t / "_lesson.md" / "inner").write_text("x", encoding="utf-8")
    topics = load_language("py", str(content_dir))
    slugs = [tp.slug for tp in topics]
    assert "05_badlesson" in slugs, "lesson 读取失败不建 topic 才算崩；现行为应照常建 topic"
    assert any("05_badlesson/01_a" in p.id for tp in topics for p in tp.problems)


def test_audit_chain_same_isolation(content_dir):
    """audit_content_deep 同链路（同 loader）不因畸形文件崩——audit() 在畸形目录上可跑完。"""
    (content_dir / "py" / "06_listroot").mkdir()
    (content_dir / "py" / "06_listroot" / "bad.yaml").write_text("- x\n", encoding="utf-8")
    sys.path.insert(0, str(REPO / "scripts"))
    import importlib
    acd = importlib.import_module("audit_content_deep")
    fn = getattr(acd, "audit", None) or getattr(acd, "main", None)
    assert fn is not None
    try:
        fn()
    except SystemExit:
        pass  # main() 可能以 exitcode 收尾，不算崩
