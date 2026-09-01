import logging
from dataclasses import dataclass
from typing import Any, Optional

from core.ai_review import review, grade_open_answer
from core.progress import ProgressDAO
from core.runners.cpp_runner import CppRunner
from core.runners.python_runner import PythonRunner
from core.runners.r_runner import RRunner
from core.runners.sql_runner import SQLRunner

logger = logging.getLogger(__name__)


_RUNNERS = {
    "python": PythonRunner(),
    "sql": SQLRunner(),
    "cpp": CppRunner(),
    "r": RRunner(),
    "agent_dev": PythonRunner(),
}


@dataclass
class JudgeResult:
    passed: bool
    run_result: Any
    ai_feedback: str
    expected_display: str
    actual_display: str
    diff_hint: str = ""


def _to_problem_dict(problem) -> dict:
    if isinstance(problem, dict):
        return problem
    if hasattr(problem, "to_dict"):
        return problem.to_dict()
    return {
        k: getattr(problem, k, None)
        for k in (
            "id", "title", "statement", "expected_output",
            "expected_rows", "setup_sql", "tests", "starter_code",
            "difficulty", "topic", "hints",
            "judge_mode", "rubric", "reference_answer",
        )
    }


def _format_rows(rows) -> str:
    if not rows:
        return "(空)"
    return "\n".join(" | ".join(str(c) for c in row) for row in rows)


def _normalize(s: str, lang: str = "") -> str:
    if s is None:
        return ""
    s = s.replace("\r\n", "\n").rstrip("\n")
    # R 的 print() 会产生 [1] 前缀与列对齐空格，归一化以兼容 cat() 和 print()
    if lang == "r":
        import re
        lines = []
        for line in s.split("\n"):
            line = re.sub(r"^\s*\[\d+\]\s*", "", line)
            line = re.sub(r"\s+", " ", line).strip()
            lines.append(line)
        return "\n".join(lines).rstrip("\n")
    return s


def _cell_eq(a, b) -> bool:
    """宽松单元格比较：数值 1 与 1.0 视为相等；None 只与 None 相等；其余按字符串。"""
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    if a is None or b is None:
        return a is None and b is None
    return str(a) == str(b)


def _rows_equal(actual_rows, expected_rows) -> bool:
    if len(actual_rows) != len(expected_rows):
        return False
    return all(len(a) == len(e) and all(_cell_eq(x, y) for x, y in zip(a, e))
               for a, e in zip(actual_rows, expected_rows))


def _first_diff_cell(actual_rows, expected_rows):
    """返回 (行号, 列号, 实际值, 期望值)——行数/列数不同时用 None 表示缺失。"""
    for i in range(max(len(actual_rows), len(expected_rows))):
        a = actual_rows[i] if i < len(actual_rows) else None
        e = expected_rows[i] if i < len(expected_rows) else None
        width = max(len(a) if a is not None else 0, len(e) if e is not None else 0)
        for j in range(width):
            av = a[j] if a is not None and j < len(a) else None
            ev = e[j] if e is not None and j < len(e) else None
            if not _cell_eq(av, ev):
                return i + 1, j + 1, av, ev
    return None


def _error_summary(stderr: str) -> str:
    """从 stderr 提取最有信息量的一行作为 diff 提示。

    Python 的 traceback 第一行恒为 "Traceback (most recent call last):"，
    真正错误在最后一行；g++ 的编译错误含 "error:" 关键字。逐个过滤。
    """
    if not stderr:
        return "运行失败"
    lines = [l.strip() for l in stderr.splitlines() if l.strip()]
    if not lines:
        return "运行失败"
    for l in lines:
        if "error:" in l.lower() and not l.lower().startswith("traceback"):
            return l[:120]
    meaningful = [l for l in lines
                  if not (l.startswith("Traceback") or l.startswith(("File ", "  File ", "    ")))]
    if meaningful:
        return meaningful[-1][:120]
    return lines[-1][:120]


def _check_recommendation_completed(d: ProgressDAO, lang: str, pid: str) -> None:
    """If this problem was previously recommended, emit recommendation_completed with full attribution."""
    try:
        row = d.conn.execute(
            "SELECT payload_json FROM learning_events "
            "WHERE event_type='recommendation_shown' AND lang=? AND problem_id=? "
            "ORDER BY rowid DESC LIMIT 1",
            (lang, pid)
        ).fetchone()
        if row:
            import json
            payload = json.loads(row[0]) if row[0] else {}
            d.emit_event("recommendation_completed", lang=lang, problem_id=pid,
                         payload={
                             "recommendation_id": payload.get("recommendation_id", ""),
                             "reason_code": payload.get("reason_code", ""),
                             "surface": payload.get("surface", ""),
                             "rank": payload.get("rank", 0),
                         })
    except Exception:
        pass


def _record_attempt(lang: str, pid: str, code: str, passed: bool,
                    feedback: str, dao: Optional[ProgressDAO],
                    difficulty: int = 3) -> None:
    """统一的作答持久化：run 题和开放题共用，避免两处逻辑漂移。"""
    if not pid:
        return
    if pid.startswith("AI_VARIANT::"):
        # AI 变式题不落库：伪 ID 写进 attempts/problems_status 会污染
        # 错题本、进度统计、间隔复习与成就（幽灵条目 + 死按钮）
        return
    own_dao = dao is None
    d = dao or ProgressDAO()
    try:
        d.record_attempt_and_status(lang, pid, code, passed, feedback)
        d.update_review_state(lang, pid, passed, difficulty)
        d.emit_event("attempt_submitted", lang=lang, problem_id=pid,
                     payload={"passed": passed})
        event_type = "problem_passed" if passed else "problem_failed"
        d.emit_event(event_type, lang=lang, problem_id=pid)
        if passed:
            _check_recommendation_completed(d, lang, pid)
    except Exception as e:
        logger.warning("record_attempt_and_status failed: %s", e)
    finally:
        if own_dao:
            d.close()


def _run_test_cases(runner, lang: str, code: str, pdict: dict) -> tuple:
    """执行所有 test cases，返回 (passed, last_run_result, diff_hint)。"""
    expected = {}
    if pdict.get("setup_sql"):
        expected["setup_sql"] = pdict["setup_sql"]
    if pdict.get("expected_rows") is not None:
        expected["expected_rows"] = pdict["expected_rows"]

    test_cases = pdict.get("tests") or [{}]
    passed = True
    last_run_result = None
    diff_hint = ""

    for ti, tc in enumerate(test_cases):
        tc = tc or {}
        stdin = str(tc.get("stdin", "") or "")
        case_expected = expected.copy()
        case_run = runner.run(code, stdin=stdin, expected=case_expected)
        last_run_result = case_run

        if pdict.get("expected_rows") is not None:
            if case_run.rows is not None:
                actual_rows = [list(r) for r in case_run.rows]
                expected_rows = [list(r) for r in pdict["expected_rows"]]
                if not _rows_equal(actual_rows, expected_rows):
                    passed = False
                    if len(actual_rows) != len(expected_rows):
                        diff_hint = f"行数：实际 {len(actual_rows)} / 期望 {len(expected_rows)}"
                    else:
                        r_i, c_i, av, ev = _first_diff_cell(actual_rows, expected_rows)
                        diff_hint = (f"第 {r_i} 行第 {c_i} 列不一致：实际 {av} / 期望 {ev}。"
                                     f"请检查 SELECT 字段顺序与 ORDER BY。")
                    break
            else:
                passed = False
                diff_hint = "SQL 执行失败：" + _error_summary(case_run.stderr)
                break
        else:
            # 期望输出可能合法为空串：必须用 is not None，不能 or（空串会误回退到题目级期望）
            case_expected_out = tc["expected_output"] if tc.get("expected_output") is not None \
                else pdict.get("expected_output") or ""
            expected_out = _normalize(str(case_expected_out), lang)
            actual_out = _normalize(case_run.stdout, lang)
            case_passed = case_run.ok and (expected_out == actual_out)
            if not case_passed:
                passed = False
                if case_run.ok:
                    diff_hint = "输出与期望不一致，注意空格、大小写、标点和换行。"
                else:
                    diff_hint = f"运行错误：{_error_summary(case_run.stderr)}"
                if len(test_cases) > 1:
                    diff_hint = f"第 {ti+1} 组测试未通过——" + diff_hint
                break

    return passed, last_run_result, diff_hint


def _build_display(lang: str, pdict: dict, run_result) -> tuple:
    """构造 expected_display 和 actual_display。"""
    if pdict.get("expected_rows") is not None:
        expected_display = _format_rows(pdict["expected_rows"])
        actual_display = (
            _format_rows(run_result.rows) if run_result and run_result.rows is not None
            else ((run_result.stdout or "") if run_result else "(空)")
        ) or "(空)"
    else:
        expected_display = _normalize(pdict.get("expected_output") or "", lang) or "(空)"
        actual_display = _normalize(run_result.stdout if run_result else "", lang) or "(空)"
    return expected_display, actual_display


def judge(lang: str, problem, code: str, dao: Optional[ProgressDAO] = None) -> JudgeResult:
    pdict = _to_problem_dict(problem)

    if not (code or "").strip():
        # 空代码：直接友好拒绝，四语言行为统一（此前 Python/R 空代码会"通过"）
        expected_display, _ = _build_display(lang, pdict, None)
        return JudgeResult(
            passed=False, run_result=None,
            ai_feedback="代码为空：请在编辑器中写下你的解答，再点「提交」。",
            expected_display=expected_display, actual_display="(空)",
            diff_hint="代码为空",
        )

    if pdict.get("judge_mode") == "ai_open":
        return _judge_open(lang, pdict, answer=code, dao=dao)

    if lang not in _RUNNERS:
        return JudgeResult(
            passed=False, run_result=None,
            ai_feedback=f"暂不支持的语言：{lang}",
            expected_display="", actual_display="",
            diff_hint=f"支持：{', '.join(_RUNNERS.keys())}",
        )

    runner = _RUNNERS[lang]
    passed, run_result, diff_hint = _run_test_cases(runner, lang, code, pdict)
    expected_display, actual_display = _build_display(lang, pdict, run_result)
    feedback = review(lang, pdict, code, run_result, passed)
    difficulty = int(pdict.get("difficulty") or 3)
    _record_attempt(lang, pdict.get("id") or "", code, passed, feedback, dao, difficulty)

    return JudgeResult(
        passed=passed,
        run_result=run_result,
        ai_feedback=feedback,
        expected_display=expected_display,
        actual_display=actual_display,
        diff_hint=diff_hint,
    )


def _judge_open(lang: str, pdict: dict, answer: str, dao: Optional[ProgressDAO] = None) -> JudgeResult:
    """开放题：交 LLM 按 rubric 评分。LLM 不可用时不记录 attempt（不把基础设施故障算成用户失败）。"""
    res = grade_open_answer(lang, pdict, answer)
    result = JudgeResult(
        passed=res["passed"],
        run_result=None,
        ai_feedback=res["feedback"],
        expected_display=pdict.get("reference_answer") or "（开放题，无标准答案）",
        actual_display=answer or "(空)",
        diff_hint="",
    )
    if res.get("llm_ok") and not str(pdict.get("id") or "").startswith("AI_VARIANT::"):
        pid = pdict.get("id") or ""
        own_dao = dao is None
        d = dao or ProgressDAO()
        try:
            attempt_id = d.record_attempt_and_status(lang, pid, answer, res["passed"], res["feedback"])
            d.update_review_state(lang, pid, res["passed"])
            dimensions = res.get("dimensions") or []
            if dimensions and attempt_id:
                d.record_rubric_scores(lang, pid, attempt_id, dimensions,
                                       prompt_version=res.get("prompt_version"),
                                       model=res.get("model"))
            d.emit_event("ai_open_scored", lang=lang, problem_id=pid,
                         payload={"score": res.get("score"), "passed": res["passed"]})
        except Exception as e:
            logger.warning("_judge_open record failed: %s", e)
        finally:
            if own_dao:
                d.close()
    return result
