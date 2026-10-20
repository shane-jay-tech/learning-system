# -*- coding: utf-8 -*-
"""l1007-19：_lesson.md 读取失败处理现状钉桩（1030 遗留 2）。

现值（core/loader.py:151-157）：_lesson.md 存在但读取 OSError ⇒ logger.warning
单通道，lesson_md 回退空串，**不进** _record_load_error 诊断记录（与 yaml 面
_record_load_error 三态通道不同轨）＝1030 原判「仍走原 logger.warning 路径」现状维持。
本件钉三态（不存在=静默空串弧／权限错=warning 弧／IO 错=warning 弧）不影响主流程。
"""
from __future__ import annotations

import logging
import os

import pytest

from core import loader


def _mk_topic(base, lang, slug, files=None):
    d = base / lang / slug
    d.mkdir(parents=True)
    for name, content in (files or {}).items():
        (d / name).write_text(content, encoding="utf-8")
    return d


def test_missing_lesson_silent_empty(tmp_path, monkeypatch, caplog):
    """不存在态：无 _lesson.md ⇒ 静默走空串弧（无 warning——exists 守卫前置）。"""
    _mk_topic(tmp_path, "python", "t1", {"q.yaml": "question: q\nanswer: a\n"})
    with caplog.at_level(logging.WARNING):
        topics = loader.load_language("python", content_dir=str(tmp_path))
    assert len(topics) == 1 and topics[0].lesson_md == ""
    assert "Read lesson failed" not in caplog.text


def test_unreadable_lesson_warns_and_mainflow_continues(tmp_path, monkeypatch, caplog):
    """读取失败态（目录冒充文件→IsADirectoryError/OSError）：warning 单通道＋主流程照常。"""
    d = _mk_topic(tmp_path, "python", "t2", {"q.yaml": "question: q\nanswer: a\n"})
    (d / "_lesson.md").mkdir()  # 目录冒充文件 ⇒ open 必 OSError
    with caplog.at_level(logging.WARNING):
        topics = loader.load_language("python", content_dir=str(tmp_path))
    assert len(topics) == 1, "主流程不受影响（topic 照常产出）"
    assert topics[0].lesson_md == ""
    assert "Read lesson failed" in caplog.text, "warning 单通道现状"
    assert any(r.levelno == logging.WARNING for r in caplog.records)
