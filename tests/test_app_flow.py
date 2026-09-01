"""AppTest 端到端回归：真实跑 app.py，验证交互流程（不碰真实 progress.db）。

较慢（每个用例几秒），但能抓住 fake-st 单测抓不到的 widget 状态类 bug：
例如带 key 的编辑器在「重置」后因 widget 状态优先级而被旧值覆盖。
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

pytest.importorskip("streamlit.testing")
from streamlit.testing.v1 import AppTest  # noqa: E402

from core.progress import ProgressDAO  # noqa: E402


def _app(tmp_path, monkeypatch):
    monkeypatch.setenv("LS_PROGRESS_DB", str(tmp_path / "flow.db"))
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)


def _goto_language(at):
    at.session_state["route"] = "language"
    at.session_state["selected_lang"] = "python"
    at.session_state["selected_topic_idx"] = 0
    at.session_state["selected_problem_idx"] = 0
    at.run()
    assert not at.exception


PID = "python/01_hello_and_vars/01_hello_world"
CK = "code::" + PID


def test_reset_button_remounts_editor_and_restores_starter(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch)
    at.run()
    _goto_language(at)
    assert CK in at.session_state

    starter = at.session_state[CK]
    # 模拟用户打字：编辑器 widget 状态（epoch 0）与 code:: 状态都被写
    at.session_state[CK] = "print('user typed this')"
    at.session_state["editor_" + PID + "_0"] = "print('user typed this')"
    at.run()
    assert at.session_state[CK] == "print('user typed this')"

    # 点击重置 → starter 恢复 + epoch 递增（编辑器重建）
    at.button(key="reset_" + PID).click().run()
    assert not at.exception
    assert at.session_state[CK] == starter
    assert at.session_state["editor_epoch::" + PID] == 1


def test_diagnostic_skip_navigates_to_paths(tmp_path, monkeypatch):
    at = _app(tmp_path, monkeypatch)
    at.run()
    at.session_state["route"] = "diagnostic"
    at.run()
    assert not at.exception

    # 点击「跳过诊断」→ 应去 paths（回归：曾写错成 session_state.page）
    skip = [b for b in at.button if b.label == "跳过诊断"]
    assert skip, "跳过诊断按钮应存在"
    skip[0].click().run()
    assert not at.exception
    assert at.session_state["route"] == "paths"


def test_weak_topic_practice_navigates_via_selection(tmp_path, monkeypatch):
    """错题本「弱项专练 → 练习」必须走统一导航（回归：曾写 lang/topic 无效键）。"""
    db = ProgressDAO(str(tmp_path / "flow.db"))
    try:
        db.mark_status("python", PID, "wrong")
    finally:
        db.close()

    at = _app(tmp_path, monkeypatch)
    at.run()
    at.session_state["route"] = "mistakes"
    at.run()
    assert not at.exception

    btn = [b for b in at.button if b.label == "练习 →"]
    assert btn, "弱项专练应有练习按钮"
    btn[0].click().run()
    assert not at.exception
    assert at.session_state["route"] == "language"
    assert at.session_state["selected_lang"] == "python"
    # selection 已被语言页消费（pop），最终落在正确的 topic 索引上
    assert at.session_state["selected_topic_idx"] == 0
    assert "selection" not in dict(at.session_state.filtered_state)
