import json
import logging
import re
import subprocess
import sys
from typing import Dict, Optional

from core.config import get_llm_script_path

TIMEOUT_SEC = 45  # 单机单人；删了 deepseek fallback，最坏只等 45s

logger = logging.getLogger(__name__)

from core.utils import trim_text as _trim_impl


def _trim(s: str, n: int = 2000) -> str:
    return _trim_impl(s, n)


_SYSTEM = (
    "你是一位中文编程老师，要根据已有题目出一道**风格相似但内容不同**的变式题。"
    "返回**纯 JSON**，没有任何额外说明文字、代码围栏、Markdown。"
    "JSON 字段必须包括："
    "{title, statement, starter_code, expected_output, hints (3 条以内的列表)}。"
    "其中 statement 是中文 Markdown，长度 50-200 字；"
    "starter_code 是该语言的起手代码模板，**绝对不能包含完整答案**——只能给个空架子；"
    "expected_output 是程序运行后期望输出的字符串（含换行也写进去）；"
    "hints 是 1-3 条中文提示，每条一行短句。"
    "如果原题需要 stdin 输入，给一个 starter_code 中能读取的提示，并保证 expected_output 是基于一个具体输入的结果。"
    "不要超过给定难度。"
)


def _build_user_prompt(lang: str, original: dict) -> str:
    return (
        f"语言：{lang}\n"
        f"原题难度：{original.get('difficulty', 1)}/5\n"
        f"原题标题：{_trim(original.get('title', ''), 200)}\n"
        f"原题描述：\n{_trim(original.get('statement', ''), 1500)}\n"
        f"原题期望输出：{_trim(str(original.get('expected_output', '')), 500)}\n\n"
        "请基于原题主题出一道**新题**（变式），保持难度相近。直接返回 JSON。"
    )


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text


def _parse_json(text: str) -> Optional[Dict]:
    candidates = [text]
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        candidates.append(m.group(0))
    for c in candidates:
        c = _strip_fences(c)
        try:
            data = json.loads(c)
            if isinstance(data, dict) and "title" in data and "expected_output" in data:
                return data
        except Exception:
            continue
    return None


def generate_variant(lang: str, original: dict, model: str = "deepseek") -> Optional[Dict]:
    """出题=质量档：默认 deepseek-v4-pro（要保证生成的题面/expected_output 正确，
    且比 gpt 更稳）。单模型不做 fallback——出题本就较慢，避免最坏叠加超时。"""
    prompt = _build_user_prompt(lang, original)
    try:
        proc = subprocess.run(
            [sys.executable, get_llm_script_path(), "--model", model,
             "--system", _SYSTEM, "--prompt", prompt],
            capture_output=True,
            timeout=TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        logger.warning("AI generate timeout: model=%s", model)
        return None
    except Exception as e:
        logger.warning("AI generate failed: model=%s err=%s", model, e)
        return None
    if proc.returncode != 0:
        err_bytes = getattr(proc, "stderr", b"") or b""
        logger.warning("AI generate non-zero: rc=%s err=%s",
                       proc.returncode,
                       err_bytes.decode("utf-8", errors="replace")[:200])
        return None
    text = proc.stdout.decode("utf-8", errors="replace")
    data = _parse_json(text)
    if not data:
        logger.warning("AI generate parse failed; head=%s", text[:200])
        return None

    data.setdefault("hints", [])
    if isinstance(data["hints"], str):
        data["hints"] = [h.strip() for h in data["hints"].splitlines() if h.strip()]
    data.setdefault("starter_code", original.get("starter_code", ""))
    data.setdefault("difficulty", original.get("difficulty", 1))
    data.setdefault("topic", original.get("topic", ""))
    data["id"] = f"AI_VARIANT::{original.get('id', 'unknown')}"
    return data
