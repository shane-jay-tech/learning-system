"""共享工具——抽出多处重复使用的轻量函数。"""
from __future__ import annotations


def trim_text(s: str, max_chars: int) -> str:
    """截断字符串到 max_chars，附加截断提示。"""
    if not s:
        return ""
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + f"\n[... 已截断（>{max_chars} 字符）]"
