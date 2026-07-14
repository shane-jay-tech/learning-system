from dataclasses import dataclass, field
from typing import Optional, List, Any

from core.config import is_public_deploy


@dataclass
class RunResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    exit_code: Optional[int] = None
    error_kind: Optional[str] = None
    rows: Optional[List[List[Any]]] = None
    elapsed_ms: int = 0


_PUBLIC_DEPLOY_ERROR = (
    "当前为公开部署模式（RUNNER_SECURITY_MODE=public），"
    "出于安全考虑，不允许执行学生代码。请在本机单人模式下使用。"
)


class BaseRunner:
    def run(self, code: str, stdin: str = "", expected: Optional[dict] = None) -> RunResult:
        raise NotImplementedError

    def check_security(self) -> Optional[RunResult]:
        """公开部署模式下拒绝执行，返回错误 RunResult；本机模式返回 None（允许继续）。"""
        if is_public_deploy():
            return RunResult(
                ok=False, stdout="", stderr=_PUBLIC_DEPLOY_ERROR,
                error_kind="sandbox",
            )
        return None
