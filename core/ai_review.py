import json
import logging
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional

from core.config import get_llm_script_path

# Offline error guidance via the shared hub (best-effort). When the LLM is down,
# we still translate the student's runtime error into plain language instead of
# only saying "AI unavailable". Source: psy-analysis friendly_errors.
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # D:\code
    from scripts.common import friendly_errors as _fe  # type: ignore
except Exception:  # pragma: no cover
    _fe = None

TIMEOUT_SEC = 60
_MAX_FIELD = 4000  # 单字段最多 4000 字符，避免 Windows cmdline 32KB 限制

PROMPT_VERSIONS = {
    "code_review_strict": "v2.0",
    "code_review_beginner_pass": "v2.0",
    "code_review_beginner_fail": "v2.0",
    "open_scoring": "v2.1",
    "follow_up": "v1.0",
    "lesson_qa": "v1.0",
}

# 模型分档（用户哲学：简单/交互的活让 flash 干，质量关键时才上高性能模型）。
# model_id 通过 env 覆盖 {ROLE}_MODEL 只作用于本次调用，不改 .env.local，
# 多模型协作的 deepseek-v4-pro 评审不受影响。
_FLASH_MODEL = "deepseek-v4-flash"
# 快档（代码点评 / 追问 / 知识点问答等交互）：flash 优先，失败退 kimi / gpt
_FAST_CHAIN = (("deepseek", _FLASH_MODEL), ("kimi", None), ("gpt", None))
# 质量档（开放题评分等"判定"类，需保证质量）：deepseek-v4-pro 优先，再 gpt / kimi
_QUALITY_CHAIN = (("deepseek", None), ("gpt", None), ("kimi", None))

logger = logging.getLogger(__name__)

from core.utils import trim_text as _trim_impl


def _trim(s: str, n: int = _MAX_FIELD) -> str:
    return _trim_impl(s, n)


FOLLOW_UP_SYSTEM = (
    "你是上一题的同一位资深中文编程老师，学生对你刚给的代码点评有不懂的地方，"
    "想继续追问。请耐心、具体地回答——结合学生的题目、代码、运行结果说，"
    "**不要泛泛而谈**。\n\n"
    "回答要求：\n"
    "- 全程中文，控制在 200-250 字\n"
    "- 直接答问题，不要先说「好的」「这是个好问题」之类的废话\n"
    "- 必要时给 1-2 行代码示例（不超过 3 行）\n"
    "- 如果学生问的概念你前面提过，可以引用「我刚才说到的 X」\n"
    "- 学生提的若是误解，要直接指出但不挖苦"
)

_SYSTEM_PROMPT_STRICT = (
    "你是一位有 10+ 年经验的资深中文编程老师，"
    "**像资深程序员评审同事代码**那样既鼓励又专业地批改学生的代码。\n\n"
    "回复必须包含下面 4 段，全程中文，总长不超过 300 字：\n\n"
    "【思路】一句话评判：通过/未通过的原因，思路是否合理。\n\n"
    "【代码品质】**必给**——从以下维度挑 2-3 条具体点评（不要全说，挑最值得说的）：\n"
    "- 命名：变量/函数名是否表达意图（i/j/x 多了就批；好名字就夸）\n"
    "- 简洁/Pythonic：能不能用 list comprehension、内置函数、unpacking 等更地道写法\n"
    "- 边界：是否处理空输入/0/负数/越界等特殊情况\n"
    "- 风格习惯：Python 用 enumerate/with/f-string；C++ 用 range-for / const T& / RAII；"
    "SQL 用显式 JOIN 不用逗号 + WHERE；R 用向量化代替 for；\n"
    "- 复杂度：算法是否过于低效（n² 能否变 n、有无重复计算）\n"
    "- DRY：是否有重复代码可抽函数；有无魔法数字\n\n"
    "【改进建议】1-2 条**具体可行**的优化（指明「哪一行改成什么」，不贴超过 3 行代码）。\n\n"
    "【进阶提示】一个延伸知识点（语言生态里相关的高级特性、最佳实践、常见陷阱）。\n\n"
    "硬性要求：\n"
    "- 不说「还不错」「挺好的」「加油」等空话——必须**具体到位置和理由**\n"
    "- 即使代码完全正确，也要给至少 1 条可改进点（资深程序员总能挑出东西）\n"
    "- 不贴超过 3 行的代码示例\n"
    "- 不用英文术语缩写（如要用，附中文解释）\n"
    "- 总长 200-300 字之间"
)

_SYSTEM_PROMPT_BEGINNER_PASS = (
    "你是一位耐心的中文编程老师，学生刚完成一道入门练习题并**通过了**。\n\n"
    "你的首要任务是**建立学生的自信心**——让他们觉得'我能学会编程'。\n\n"
    "回复必须包含下面 3 段，全程中文，总长 150-250 字：\n\n"
    "【做对了什么】具体指出学生代码里做得好的 1-2 个点（用了什么语法/逻辑、思路清晰的地方）。\n\n"
    "【为什么对】用大白话解释为什么这样写是正确的——帮助学生建立因果关系理解。\n\n"
    "【下一步】一个小小的延伸提示——'下一题会用到 X，留意一下'或'试试把这个思路用在 Y 场景'。\n\n"
    "硬性要求：\n"
    "- 以肯定、鼓励为主——不要在入门通过题里挑刺或指出'可改进点'\n"
    "- 不贴超过 2 行的代码示例\n"
    "- 不用专业术语缩写（如要用，附中文解释）\n"
    "- 语气亲切但不空洞——'做对了'后面必须跟具体原因"
)

_SYSTEM_PROMPT_BEGINNER_FAIL = (
    "你是一位耐心的中文编程老师，学生刚提交了一道入门练习题但**没通过**。\n\n"
    "你的任务是帮学生找到**一个最关键的问题**，不要同时指出太多错误。\n\n"
    "回复必须包含下面 4 段，全程中文，总长 200-300 字：\n\n"
    "【哪里出了问题】指出最关键的一个错误——具体到哪一行/哪个概念用错了。\n\n"
    "【为什么错】用大白话解释这个错误的原因，最好举一个生活类比。\n\n"
    "【变量追踪】选一个代表性输入，列出 3-5 步关键变量的变化过程，帮助学生看到"
    "程序实际在做什么（格式：第1步 x=... → 第2步 y=... → ...）。\n\n"
    "【怎么改】给一个明确的修改方向（不直接给完整答案），让学生自己动手修。\n\n"
    "硬性要求：\n"
    "- 只聚焦一个最关键错误，不要列一堆问题让学生更焦虑\n"
    "- 语气鼓励：'这个错误很常见，改一下就好'\n"
    "- 不贴超过 2 行的代码示例\n"
    "- 不用专业术语缩写（如要用，附中文解释）"
)


def _build_review_system_prompt(difficulty: int, passed: bool, lang: str) -> str:
    """根据题目难度和是否通过，选择合适的 AI 点评策略。"""
    if difficulty <= 2 and passed:
        return _SYSTEM_PROMPT_BEGINNER_PASS
    if difficulty <= 2 and not passed:
        return _SYSTEM_PROMPT_BEGINNER_FAIL
    return _SYSTEM_PROMPT_STRICT


# 兼容旧引用
SYSTEM_PROMPT = _SYSTEM_PROMPT_STRICT

AI_OPEN_SYSTEM = (
    "你是一位评分严格但鼓励学生的中文编程老师。请根据题目的评分标准（rubric）"
    "对学生的开放式回答进行评判。\n\n"
    "只输出一个 JSON 对象，不要输出 JSON 以外的任何内容（不要加代码围栏、不要解释）：\n"
    '{"passed": true 或 false, "score": 0到100的整数, '
    '"dimensions": [{"name": "维度名", "score": 0到100, "comment": "一句话点评"}], '
    '"feedback": "中文总评，200-300字，具体指出做得好和欠缺的地方，语气鼓励"}\n\n'
    "passed=true 表示学生达到了 rubric 的主要要点；passed=false 表示未达到。\n"
    "dimensions 数组：把 rubric 里的每个评分要点拆成一个维度，分别打分和点评。\n"
    "feedback 要具体——指出回答里命中/遗漏了 rubric 的哪些要点，而不是泛泛而谈。"
)

LESSON_QA_SYSTEM = (
    "你是一位耐心的中文编程老师。学生正在阅读一节知识点讲解，对其中某处有疑问，向你提问。"
    "请**紧扣这节讲解的内容**，用大白话讲清楚——必要时举一个小例子。\n\n"
    "回答要求：\n"
    "- 全程中文，控制在 200-300 字\n"
    "- 紧扣本节主题，别跑题到无关的高级内容\n"
    "- 直接答，不要「好的」「这是个好问题」之类的开场白\n"
    "- 需要时给 1-2 行代码示例（不超过 3 行）\n"
    "- 如果学生的疑问超出本节范围，简短点到为止，并说明这属于后面的内容"
)


def _call_chain(prompt: str, system: str, chain) -> str:
    """按 chain（(role, model_id) 元组序列）依次尝试，返回第一个非空结果；全失败返回空串。"""
    for model, model_id in chain:
        text = _call(model, prompt, system=system, model_id=model_id)
        if text:
            return text
    return ""


def review(lang: str, problem: dict, code: str, run_result: Any, passed: bool) -> str:
    title = problem.get("title", "")
    statement = problem.get("statement", "")
    expected = problem.get("expected_output") or problem.get("expected_rows") or ""
    stdout = (getattr(run_result, "stdout", "") or "").strip()
    stderr = (getattr(run_result, "stderr", "") or "").strip()
    verdict = "已通过" if passed else "未通过"
    difficulty = int(problem.get("difficulty") or 1)

    prompt = (
        f"语言：{lang}\n"
        f"题目：{_trim(title, 200)}\n"
        f"题目要求：{_trim(statement, 1500)}\n"
        f"期望输出：{_trim(str(expected), 800)}\n"
        f"学生代码：\n```\n{_trim(code)}\n```\n"
        f"运行输出：\n{_trim(stdout, 800) or '(空)'}\n"
        f"错误信息：\n{_trim(stderr, 800) or '(无)'}\n"
        f"判题结果：{verdict}\n\n"
        "请按系统提示给出反馈。"
    )

    system = _build_review_system_prompt(difficulty, passed, lang)
    text = _call_chain(prompt, system, _FAST_CHAIN)
    if text:
        return _post_check(text, difficulty, passed)
    return _offline_fallback(passed, stderr)


def _post_check(text: str, difficulty: int, passed: bool) -> str:
    """轻量后处理：检查 AI 输出是否违反分层策略。"""
    if difficulty <= 2 and passed:
        _HARSH_MARKERS = ["不足", "缺点", "问题是", "错误在于", "应该改为"]
        harsh_count = sum(1 for m in _HARSH_MARKERS if m in text)
        if harsh_count >= 2:
            text += "\n\n（提示：你做对了！上面的建议仅供参考，核心思路是正确的。）"
    return text


def _offline_fallback(passed: bool, stderr: str) -> str:
    """LLM 不可用时的兜底点评：命中具体错误模式就给离线指引。"""
    msg = "AI 点评暂时不可用（网络或服务异常），请稍后再试。判题本身不受影响。"
    if not passed and stderr and _fe is not None:
        try:
            fr = _fe.friendly_explain(stderr)
            if fr.title != "出了点问题":  # 仅在命中具体模式时补充，避免废话
                msg += (f"\n\n先给你一个离线提示——**{fr.title}**：{fr.explanation} "
                        f"👉 {fr.suggested_action}")
        except Exception:
            pass
    return msg


def follow_up(
    lang: str,
    problem: dict,
    code: str,
    run_result: Any,
    passed: bool,
    initial_review: str,
    history: List[Dict[str, str]],
    user_question: str,
) -> str:
    """学生针对原 review 继续追问。history 是 [{'role': 'user'/'ai', 'text': ...}, ...]"""
    title = problem.get("title", "")
    statement = problem.get("statement", "")
    stdout = (getattr(run_result, "stdout", "") or "").strip()
    stderr = (getattr(run_result, "stderr", "") or "").strip()
    verdict = "已通过" if passed else "未通过"

    # 优先保留：当前代码+错误信息完整，历史对话按轮次保留最近5轮
    recent_history = history[-10:]  # 最近5轮（每轮2条）
    chat_log_lines = []
    for msg in recent_history:
        role = "学生" if msg["role"] == "user" else "老师"
        # 最近3轮完整保留，更早的压缩
        if msg in history[-6:]:
            chat_log_lines.append(f"{role}：{_trim(msg['text'], 800)}")
        else:
            chat_log_lines.append(f"{role}：{_trim(msg['text'], 200)}")
    chat_log = "\n".join(chat_log_lines) if chat_log_lines else "(无前序对话)"

    prompt = (
        f"语言：{lang}\n"
        f"题目：{_trim(title, 200)}\n"
        f"题面：{_trim(statement, 1000)}\n"
        f"学生代码：\n```\n{_trim(code, 3000)}\n```\n"
        f"运行输出：{_trim(stdout, 800) or '(空)'}\n"
        f"错误信息：{_trim(stderr, 800) or '(无)'}\n"
        f"是否通过：{verdict}\n\n"
        f"你之前给的点评：\n{_trim(initial_review, 1200)}\n\n"
        f"对话历史：\n{chat_log}\n\n"
        f"学生现在追问：{_trim(user_question, 500)}\n\n"
        "请基于以上上下文回答（200-250 字，中文）。"
    )

    return _call_chain(prompt, FOLLOW_UP_SYSTEM, _FAST_CHAIN) or "AI 暂时连不上，请稍后再问。"


def ask_lesson(lang: str, topic_title: str, lesson_md: str,
               history: List[Dict[str, str]], user_question: str) -> str:
    """学生阅读知识点讲解时随时提问。history 是 [{'role':'user'/'ai','text':...}, ...]。"""
    chat_log_lines = []
    for msg in history[-10:]:  # 最近 10 条，避免 prompt 过长
        role = "学生" if msg["role"] == "user" else "老师"
        chat_log_lines.append(f"{role}：{_trim(msg['text'], 400)}")
    chat_log = "\n".join(chat_log_lines) if chat_log_lines else "(无前序对话)"

    prompt = (
        f"语言：{lang}\n"
        f"知识点主题：{_trim(topic_title, 200)}\n"
        f"这节讲解的内容：\n{_trim(lesson_md, 2500)}\n\n"
        f"对话历史：\n{chat_log}\n\n"
        f"学生的疑问：{_trim(user_question, 500)}\n\n"
        "请基于这节讲解的内容回答（中文，200-300 字）。"
    )

    # 知识点问答 = 快档（flash 优先）
    return _call_chain(prompt, LESSON_QA_SYSTEM, _FAST_CHAIN) or "AI 老师暂时连不上，请稍后再问。"


_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _extract_json(text: str) -> Optional[dict]:
    """从 LLM 输出里稳健地抽 JSON 对象。容忍 ```json 围栏 / 前后废话。失败返回 None。"""
    raw = text.strip()
    # 先剥 markdown 代码围栏
    raw = _FENCE_RE.sub("", raw).strip()
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group())
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def grade_open_answer(lang: str, problem: dict, answer: str) -> dict:
    """开放题 AI 评分。返回 {passed, score, feedback, llm_ok}。绝不抛异常。"""
    try:
        parts = []
        stmt = problem.get("statement")
        if stmt:
            parts.append(f"题目：{_trim(str(stmt), 1500)}")
        rubric = problem.get("rubric")
        if rubric:
            parts.append(f"评分标准（rubric）：\n{_trim(str(rubric), 1500)}")
        ref = problem.get("reference_answer")
        if ref:
            parts.append(f"参考答案：\n{_trim(str(ref), 1500)}")
        parts.append(f"学生回答：\n{_trim(str(answer))}")
        prompt = "\n\n".join(parts)

        # 开放题评分 = 质量档（deepseek-v4-pro 优先，保证判定质量）
        text = None
        responding_model = None
        for model, model_id in _QUALITY_CHAIN:
            text = _call(model, prompt, system=AI_OPEN_SYSTEM, model_id=model_id)
            if text:
                responding_model = model_id or model
                break
        if not text:
            return {
                "passed": False, "score": None,
                "feedback": "AI 评判暂时不可用（网络或服务异常），请稍后再试。",
                "llm_ok": False,
            }

        parsed = _extract_json(text)
        if parsed is not None:
            raw_passed = parsed.get("passed")
            if isinstance(raw_passed, str):
                passed = raw_passed.strip().lower() == "true"
            else:
                passed = bool(raw_passed)
            score = parsed.get("score")
            if score is not None:
                try:
                    score = int(float(score))
                    score = max(0, min(100, score))
                except (TypeError, ValueError):
                    score = None
            feedback = str(parsed.get("feedback", "")).strip() or "（AI 未给出点评文本）"
            dimensions = parsed.get("dimensions") or []
            if isinstance(dimensions, list):
                dimensions = [
                    {"name": str(d.get("name", "")),
                     "score": max(0, min(100, int(float(d.get("score", 0))))),
                     "comment": str(d.get("comment", ""))}
                    for d in dimensions if isinstance(d, dict) and d.get("name")
                ]
            else:
                dimensions = []
            if score is not None and passed and score < 40:
                passed = False
            if score is not None and not passed and score >= 80:
                passed = True
            return {"passed": passed, "score": score, "feedback": feedback,
                    "dimensions": dimensions, "llm_ok": True,
                    "prompt_version": PROMPT_VERSIONS.get("open_scoring"),
                    "model": responding_model}

        # 解析失败兜底：把整段当 feedback，passed 用保守启发式
        # （含「通过」但同时含任一否定词时判失败——如「没有通过测试」「不合格」）
        raw = text.strip()
        _NEG = ("未通过", "不通过", "没通过", "没有通过", "不合格", "未达标", "未达到", "不予通过")
        passed = ("通过" in raw) and not any(neg in raw for neg in _NEG)
        return {"passed": passed, "score": None, "feedback": raw, "llm_ok": True}
    except Exception as e:
        logger.error("grade_open_answer error: %s", e)
        return {
            "passed": False, "score": None,
            "feedback": "AI 评判暂时不可用（网络或服务异常），请稍后再试。",
            "llm_ok": False,
        }


def _call(model: str, prompt: str, system: str = SYSTEM_PROMPT,
          model_id: Optional[str] = None) -> str:
    # model_id：单次调用覆盖该 relay 的模型 id（通过 {ROLE}_MODEL 环境变量）。
    # llm_call.py 用 setdefault 读 .env.local，所以这里传的会胜出，且只作用于本次子进程。
    call_env = None
    if model_id:
        call_env = {**os.environ, f"{model.upper()}_MODEL": model_id}
    try:
        proc = subprocess.run(
            [sys.executable, get_llm_script_path(), "--model", model,
             "--system", system, "--prompt", prompt],
            capture_output=True,
            timeout=TIMEOUT_SEC,
            env=call_env,
        )
    except subprocess.TimeoutExpired:
        logger.warning("AI call timeout: model=%s", model)
        return ""
    except Exception as e:
        logger.warning("AI call failed: model=%s err=%s", model, e)
        return ""
    if proc.returncode != 0:
        err_bytes = getattr(proc, "stderr", b"") or b""
        logger.warning("AI call non-zero: model=%s rc=%s err=%s",
                       model, proc.returncode,
                       err_bytes.decode("utf-8", errors="replace")[:200])
        return ""
    return proc.stdout.decode("utf-8", errors="replace").strip()
