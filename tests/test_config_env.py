# -*- coding: utf-8 -*-
"""core/config 环境组合钉桩（l918-25）。

config 三函数此前在测试里只被 monkeypatch 替身，真实实现零断言。本文件用
monkeypatch.setenv/delenv 钉 4 组合：默认 local_only／RUNNER_SECURITY_MODE=public／
PUBLIC_DEPLOY=1 旁路／LLM_SCRIPT 覆盖。
"""
import os

import core.config as config
from core.config import get_llm_script_path, get_runner_security_mode, is_public_deploy


def test_默认环境_local_only(monkeypatch):
    monkeypatch.delenv("RUNNER_SECURITY_MODE", raising=False)
    monkeypatch.delenv("PUBLIC_DEPLOY", raising=False)
    assert get_runner_security_mode() == "local_only"
    assert is_public_deploy() is False


def test_runner_security_mode_public_生效(monkeypatch):
    monkeypatch.setenv("RUNNER_SECURITY_MODE", "public")
    monkeypatch.delenv("PUBLIC_DEPLOY", raising=False)
    assert get_runner_security_mode() == "public"
    assert is_public_deploy() is True


def test_public_deploy_1_旁路生效(monkeypatch):
    """旁路语义：RUNNER_SECURITY_MODE 仍是 local_only，仅 PUBLIC_DEPLOY=1 也判公开部署。"""
    monkeypatch.setenv("RUNNER_SECURITY_MODE", "local_only")
    monkeypatch.setenv("PUBLIC_DEPLOY", "1")
    assert get_runner_security_mode() == "local_only"
    assert is_public_deploy() is True


def test_public_deploy_非1值_不旁路(monkeypatch):
    monkeypatch.delenv("RUNNER_SECURITY_MODE", raising=False)
    monkeypatch.setenv("PUBLIC_DEPLOY", "true")
    assert is_public_deploy() is False, "仅 '1' 字面量生效，其他值不旁路"


def test_llm_script_默认与覆盖(monkeypatch):
    monkeypatch.delenv("LLM_SCRIPT", raising=False)
    assert get_llm_script_path() == "D:/code/scripts/llm_call.py"
    monkeypatch.setenv("LLM_SCRIPT", "D:/custom/llm.py")
    assert get_llm_script_path() == "D:/custom/llm.py"
