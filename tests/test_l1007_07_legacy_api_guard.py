# -*- coding: utf-8 -*-
"""l1007-07：错题本收口③守卫告警测试（l1004-10 遗留 1 ③支）。

守卫＝旧双 API（record_attempt/mark_status）调用时 logger.warning 告警（零破坏：
写语义/返回值零变化，仅加观察日志）。触发例：直接调旧 API ⇒ caplog 捕获
[legacy-api-guard]；不触发例：正身 record_attempt_and_status ⇒ 无告警。
"""
from __future__ import annotations

import logging

import pytest

from core.progress import ProgressDAO


@pytest.fixture()
def dao(tmp_path):
    return ProgressDAO(db_path=str(tmp_path / "progress.db"))


def test_legacy_record_attempt_warns(dao, caplog):
    """触发例：record_attempt ⇒ [legacy-api-guard] warning。"""
    with caplog.at_level(logging.WARNING):
        rid = dao.record_attempt("python", "p1", "print(1)", True, "fb")
    assert isinstance(rid, int), "返回值语义零变化（attempt id）"
    assert "[legacy-api-guard] record_attempt" in caplog.text


def test_legacy_mark_status_warns(dao, caplog):
    with caplog.at_level(logging.WARNING):
        dao.mark_status("python", "p1", "solved")
    assert "[legacy-api-guard] mark_status" in caplog.text
    assert dao.get_status("python", "p1") == "solved", "写语义零变化"


def test_canonical_path_no_warning(dao, caplog):
    """不触发例：正身 record_attempt_and_status ⇒ 无 legacy 告警。"""
    with caplog.at_level(logging.WARNING):
        dao.record_attempt_and_status("python", "p2", "print(2)", False, "fb")
    assert "[legacy-api-guard]" not in caplog.text
    assert dao.get_status("python", "p2") == "wrong"
