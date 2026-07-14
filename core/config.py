"""共享配置——把多处用的常量集中在这里，方便迁移和测试 monkeypatch。"""
import os


def get_llm_script_path() -> str:
    """取 D:/code/scripts/llm_call.py 路径，可被环境变量 LLM_SCRIPT 覆盖。"""
    return os.environ.get("LLM_SCRIPT", "D:/code/scripts/llm_call.py")


def get_runner_security_mode() -> str:
    """运行器安全模式。local_only=本机单人（默认）；public=公开部署（拒绝执行学生代码）。"""
    return os.environ.get("RUNNER_SECURITY_MODE", "local_only")


def is_public_deploy() -> bool:
    """公开部署模式下返回 True，此时 runner 应拒绝执行学生代码。"""
    return get_runner_security_mode() == "public" or os.environ.get("PUBLIC_DEPLOY") == "1"
