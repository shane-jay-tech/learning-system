# -*- coding: utf-8 -*-
"""l1007-02：stderr/message 头尾保留行为钉（案2 落地批 judge 侧回归＋loader 同族）。

三面：
① _truncate（python_runner）头 60%/尾 40%：长输入两端都保留＋省略标记；短输入原样。
② LoadDiag message 头尾保留（loader）：>200 字符异常 → 头140＋中段省略标记＋尾60；
   ≤200 原样（含 error_type 稳面回归）。
③ 护栏：省略标记计入额度（l1004-02 公共护栏：提示行计 byte 限额 ≤120B——标记约 60-80B 在额度内）。
"""
from __future__ import annotations

from core.runners.python_runner import _truncate
from core import loader


def test_truncate_keeps_head_and_tail():
    data = b"HEAD-MARKER" + b"x" * 10_000 + b"TAIL-MARKER"
    out = _truncate(data, 2_000)
    assert out.startswith(b"HEAD-MARKER"), "头部应保留（异常类型行通常在此）"
    assert out.endswith(b"TAIL-MARKER"), "尾部应保留（traceback 出错位置在此）"
    assert len(out) <= 2_000, "总额度不超限（标记计额度内）"
    assert "中段省略".encode() in out, "省略标记可见"


def test_truncate_short_input_untouched():
    assert _truncate(b"short", 2_000) == b"short"


def test_loaddiag_message_head_tail_preserved(caplog):
    """>200 字符异常：message = 头140＋省略标记＋尾60（头尾都可见）。"""
    long_msg = "A" * 150 + "MIDDLE" + "Z" * 150
    loader._record_load_error("fake/path.yaml", ValueError(long_msg))
    diag = loader.get_load_diagnostics()[-1]
    m = diag.message
    assert len(m) <= 200, "总量不超 200"
    assert m.startswith("A" * 10), "头部保留（异常类型/上下文）"
    assert m.endswith("Z" * 10), "尾部保留（出错位置）"
    assert "中段省略" in m


def test_loaddiag_short_message_untouched():
    loader._record_load_error("fake/short.yaml", ValueError("short msg"))
    diag = loader.get_load_diagnostics()[-1]
    assert diag.message == "short msg"
    assert diag.error_type == "ValueError"


def test_lesson_read_error_enters_diagnostics(tmp_path, monkeypatch):
    """l1007-36（l1007-19 遗留·通道统一批第一件）：lesson 面 OSError 接诊断通道——
    _lesson.md 读取失败不再只 logger.warning，LoadDiag(error_type=OSError) 入 _last_load_errors。"""
    import os
    lang_dir = tmp_path / "python"
    lang_dir.mkdir()
    topic = lang_dir / "demo"
    topic.mkdir()
    (topic / "_lesson.md").mkdir()   # l1007-36：建成目录 ⇒ open 抛 PermissionError（Windows）/IsADirectoryError（POSIX）
    (topic / "01_basic.yaml").write_text("id: basic\ntitle: t", encoding="utf-8")

    loader._last_load_errors.clear()   # load_language 开头也会 clear——先清再取本次全量
    loader.load_language('python', content_dir=str(tmp_path))
    diags = loader._last_load_errors
    # Windows 上 open(目录) 抛 PermissionError（POSIX 为 IsADirectoryError）——两者均 ∈ OSError 内容错组
    assert any(
        d.error_type in ("IsADirectoryError", "PermissionError") and "_lesson.md" in d.path
        for d in diags), (
        f"lesson 读取失败应入诊断通道：{[ (d.error_type, d.path) for d in diags ]}")
