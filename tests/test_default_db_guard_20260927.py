# -*- coding: utf-8 -*-
"""A5①（2026-09-27 用户授权）：测试态禁开默认生产库——机制化闸的正面/反向用例。

由来：波次 15 `learn36` 首版测试传 `dao=None`，`core/judge.py:_record_attempt` 自开默认路径
＝`data/progress.db`，往生产库写出 14 行合成数据（事后经用户批准定点清除）。此前这条防线
只写在派单横幅与个别测试文件头（人工约定），本件把它钉成机制。

判据三条：① pytest 进程内、无覆盖 ⇒ 拒开且报错文本点名 A5 与默认库路径；
② 显式 db_path／`LS_PROGRESS_DB`／`LS_ALLOW_DEFAULT_DB_IN_TESTS=1` 三条出口都放行；
③ 非 pytest 进程（真 app／脚本）完全不受影响——闸只拦测试态，不改运行期行为。
"""
import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from core.progress import _DEFAULT_DB, ProgressDAO, _guard_default_db_in_tests


def test_default_db_guard_raises_in_pytest(monkeypatch):
    monkeypatch.delenv("LS_PROGRESS_DB", raising=False)
    monkeypatch.delenv("LS_ALLOW_DEFAULT_DB_IN_TESTS", raising=False)
    assert os.environ.get("PYTEST_CURRENT_TEST"), "本用例前提是 PYTEST_CURRENT_TEST 在册"
    with pytest.raises(RuntimeError) as ei:
        ProgressDAO()
    msg = str(ei.value)
    assert "A5" in msg and _DEFAULT_DB in msg, msg
    # 反向对照：闸是"拒开"，不是"静默换库"——默认路径常量一个字不能变
    assert _DEFAULT_DB.endswith(os.path.join("data", "progress.db")), _DEFAULT_DB


def test_guard_allows_explicit_path_env_and_explicit_optin(monkeypatch, tmp_path):
    monkeypatch.delenv("LS_PROGRESS_DB", raising=False)
    monkeypatch.delenv("LS_ALLOW_DEFAULT_DB_IN_TESTS", raising=False)

    explicit = ProgressDAO(str(tmp_path / "explicit.db"))       # ① 显式 db_path
    explicit.close()

    monkeypatch.setenv("LS_PROGRESS_DB", str(tmp_path / "env.db"))   # ② env 覆盖
    by_env = ProgressDAO()
    assert by_env.db_path == str(tmp_path / "env.db")
    by_env.close()

    monkeypatch.delenv("LS_PROGRESS_DB", raising=False)              # ③ 显式例外开关
    monkeypatch.setenv("LS_ALLOW_DEFAULT_DB_IN_TESTS", "1")
    _guard_default_db_in_tests(None, None)   # 不抛即通过（真开生产库不在测试里做）


def test_guard_is_inert_outside_pytest(monkeypatch):
    """非 pytest 进程不受影响：闸只拦测试态。"""
    monkeypatch.delenv("LS_PROGRESS_DB", raising=False)
    monkeypatch.delenv("LS_ALLOW_DEFAULT_DB_IN_TESTS", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    _guard_default_db_in_tests(None, None)   # 不抛即通过
