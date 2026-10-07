import logging
from dataclasses import dataclass
from typing import Any, Optional

from core.ai_review import review, grade_open_answer, is_degraded_feedback
from core.progress import ProgressDAO
from core.runners.cpp_runner import CppRunner
from core.runners import error_feedback
from core.runners.python_runner import PythonRunner
from core.runners.r_runner import RRunner
from core.runners.sql_runner import SQLRunner
import hashlib
import re

# l1006-03/l1004-07②：submission 幂等窗口——同 (lang, pid, code) 在窗口内的重复提交
# 返回首次判定、不重复计分（SRS/结算/事件零推进）。
SUBMISSION_IDEMPOTENCY_WINDOW_MIN = 10



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
    """输出归一化契约（q914-33 同类显式化；现状描述，零行为改动）。

    - 仅做：``\\r\\n → \\n``、去掉尾部换行；None → ``""``；
    - **反直觉点：不做空白去除/折叠**——中间空格、行首缩进原样保留
      （实证见 tests/test_judge_pure.py「_normalize 不做去除」用例）；
    - 仅 ``lang == "r"`` 时额外处理：去除 R ``print()`` 的 ``[1]`` 行前缀、
      行内空白折叠为单空格并去首尾（兼容 ``cat()`` 输出）。
    """
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
    """宽松单元格比较：数值 1 与 1.0 视为相等；None 只与 None 相等；其余按字符串。

    反直觉点（实测校正 916-02）：bool 分支按真值比较——True 与 1 相等
    （bool(1)==bool(True)）；字符串路径**严格相等、含空白差异**——"1 " 与 "1"
    不等，交给上游 _normalize 的责任（而 _normalize 本身不做空白去除）。
    """
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

    反直觉点（q914-33 显式化）：**空 stderr（或全空行）返回字面量「运行失败」**，
    不是空串——进程失败但无 stderr 时 diff 提示仍非空；命中含 "error:" 的行
    优先返回（截 120 字符），否则取过滤 Traceback/File 行后的最后一行（截 120）。
    """
    if not stderr:
        return "运行失败"
    lines = [l.strip() for l in stderr.splitlines() if l.strip()]
    if not lines:
        return "运行失败"
    # l1007-21（l1007-03 遗留 2）：stderr 首行可能是空行后的进度噪声（加载条/版本横幅），
    # 异常类型行（*Error* 形态）才是摘要应取的——优先取首个 *Error* 行，无则回退既有逻辑。
    for l in lines:
        if re.search(r"\b\w+(Error|Exception)\b", l) and not l.startswith("Traceback"):
            return l[:120]
    for l in lines:
        if "error:" in l.lower() and not l.lower().startswith("traceback"):
            return l[:120]
    meaningful = [l for l in lines
                  if not (l.startswith("Traceback") or l.startswith(("File ", "  File ", "    ")))]
    if meaningful:
        return meaningful[-1][:120]
    return lines[-1][:120]


def _row_feedback(lang: str, run_result, detail: Optional[str] = None) -> str:
    """执行器错误 → 学生可读的**行级**反馈：「第 N 行：<要点>——<中文提示>」。

    只做映射，**不改判题**：不读也不写 `ok`/`passed`/`exit_code`/`error_kind`。
    原始诊断仍由 `run_result.stderr` 逐字呈现（UI 的「错误信息」块），这里只补两件事：
      · 行号折算——Python 的 traceback 行号含 runner 注入的引导段，直接报给学生
        会指着编辑器里不存在的行（`core/runners/error_feedback` 统一折算）；
      · 四语言共用一张提示表——同一类错误不再一个有中文兜底、一个只有英文原文。
    提示与要点重复时只留一份（SQL 侧 runner 已把提示写进 stderr）。
    """
    stderr = getattr(run_result, "stderr", "") or ""
    base = detail if detail is not None else _error_summary(stderr)
    where = error_feedback.where_phrase(lang, stderr)
    hint = error_feedback.hint_only(lang, stderr)
    out = f"{where}{base}" if where else base
    if hint and hint not in out:
        out = f"{out}——{hint}"
    return out


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
            # ③（l1006-03/l1004-07 D3 面）：当日同题已有 completed 则跳过——1 shown : 1 completed
            from datetime import date as _date
            already = d.conn.execute(
                "SELECT COUNT(*) FROM learning_events WHERE event_type='recommendation_completed' "
                "AND lang=? AND problem_id=? AND local_date=?",
                (lang, pid, _date.today().isoformat())).fetchone()[0]   # 本地日期＝写侧口径（date('now') 是 UTC，时区坑）
            if already:
                return
            payload = json.loads(row[0]) if row[0] else {}
            d.emit_event("recommendation_completed", lang=lang, problem_id=pid,
                         payload={
                             "recommendation_id": payload.get("recommendation_id", ""),
                             "reason_code": payload.get("reason_code", ""),
                             "surface": payload.get("surface", ""),
                             "rank": payload.get("rank", 0),
                         })
    except Exception:
        # keep the control-flow semantics (best-effort telemetry) but make
        # the failure visible instead of silently swallowing it
        logger.warning("judge telemetry post failed", exc_info=True)


def _record_attempt(lang: str, pid: str, code: str, passed: bool,
                    feedback: str, dao: Optional[ProgressDAO],
                    difficulty: int = 3, llm_degraded: bool = False) -> None:
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
        attempt_id = d.record_attempt_and_status(lang, pid, code, passed, feedback)
        d.update_review_state(lang, pid, passed, difficulty)
        # ④payload 归一（222f#3）：发射点 A 补 attempt_id，与 backfill_events 形态一致；
        # ③事件当日去重（l1004-07）：code_hash 当日同键跳过，报表 1:N→1:1（SRS/attempts 不动）。
        code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()[:16]
        # ①l1006-04/l1004-08 C 案：降级态结构化入事件位（attempts 计数零变化）
        d.emit_event("attempt_submitted", lang=lang, problem_id=pid,
                     payload={"passed": passed, "attempt_id": attempt_id, "code_hash": code_hash,
                              "llm_degraded": llm_degraded},
                     dedup_code_hash=code_hash)
        event_type = "problem_passed" if passed else "problem_failed"
        d.emit_event(event_type, lang=lang, problem_id=pid,
                     payload={"attempt_id": attempt_id, "code_hash": code_hash},
                     dedup_code_hash=code_hash)
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
                        r_i, c_i, _av, ev = _first_diff_cell(actual_rows, expected_rows)
                        # K-3（154241 验收③）：逐格 oracle 不给值，只给坐标与该列类型——
                        # 「实际 Alice / 期望 1」可被反复提交逐格试探重建整个结果集
                        diff_hint = (f"第 {r_i} 行第 {c_i} 列与期望不一致（该列类型＝{_type_cn(ev)}）。"
                                     f"请检查 SELECT 字段顺序与 ORDER BY。")
                    break
            else:
                passed = False
                diff_hint = "SQL 执行失败：" + _row_feedback(lang, case_run)
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
                    diff_hint = f"运行错误：{_row_feedback(lang, case_run)}"
                if len(test_cases) > 1:
                    diff_hint = f"第 {ti+1} 组测试未通过——" + diff_hint
                break

    return passed, last_run_result, diff_hint


def _type_cn(v) -> str:
    """期望单元格值的类型中文名（K-3：定位给类型，不给值）。"""
    if isinstance(v, bool):
        return "布尔"
    if isinstance(v, int):
        return "整数"
    if isinstance(v, float):
        return "小数"
    if v is None:
        return "空值"
    return "文本"


def _build_display(lang: str, pdict: dict, run_result, passed: bool = True) -> tuple:
    """构造 expected_display 和 actual_display。
    K-2（154241 验收③）：未通过只下发规模差异（行数差/行数+字符数），通过后才全量对照
    （earned reveal，与开放题「写完再看」同构）；学生自己的 actual_display 不是泄漏面，原样。"""
    if pdict.get("expected_rows") is not None:
        if passed:
            expected_display = _format_rows(pdict["expected_rows"])
        else:
            expected_display = (f"期望 {len(pdict['expected_rows'])} 行"
                                f"（未通过时只显示行数差异，答对后展示全量对照）")
        actual_display = (
            _format_rows(run_result.rows) if run_result and run_result.rows is not None
            else ((run_result.stdout or "") if run_result else "(空)")
        ) or "(空)"
    else:
        expected_text = _normalize(pdict.get("expected_output") or "", lang) or "(空)"
        if passed:
            expected_display = expected_text
        else:
            n_lines = len(expected_text.splitlines())
            expected_display = (f"期望 {n_lines} 行 / {len(expected_text)} 字符"
                                f"（未通过时只显示规模，答对后展示全量对照）")
        actual_display = _normalize(run_result.stdout if run_result else "", lang) or "(空)"
    return expected_display, actual_display


def judge(lang: str, problem, code: str, dao: Optional[ProgressDAO] = None) -> JudgeResult:
    pdict = _to_problem_dict(problem)

    if not (code or "").strip():
        # 空代码：直接友好拒绝，四语言行为统一（此前 Python/R 空代码会"通过"）。
        # K-1（154241 验收③）：不构造期望显示——零努力提交从「即得答案」变为「只得到拒绝话术」
        return JudgeResult(
            passed=False, run_result=None,
            ai_feedback="代码为空：请在编辑器中写下你的解答，再点「提交」。",
            expected_display="", actual_display="(空)",
            diff_hint="代码为空",
        )

    pid = pdict.get("id") or ""
    if dao is not None and pid and not pid.startswith("AI_VARIANT::"):
        # 幂等查询仅在调用方显式传 dao 时启用（生产 UI 主路传 dao；
        # dao=None 的测试/脚本路径不自开库——A5①闸），
        d0 = dao
        if True:
            recent = d0.conn.execute(
                "SELECT passed, ai_feedback FROM attempts "
                "WHERE lang=? AND problem_id=? AND code=? "
                "AND ts >= datetime('now', ?) ORDER BY id DESC LIMIT 1",
                (lang, pid, code, f"-{SUBMISSION_IDEMPOTENCY_WINDOW_MIN} minutes"),
            ).fetchone()
        if recent is not None:
            # ②重放：窗口内同题同码 ⇒ 沿用首次判定，零重复计分（安全重试语义）
            return JudgeResult(
                passed=bool(recent[0]), run_result=None,
                ai_feedback=recent[1] or "与刚才的提交相同（未重复计分）",
                expected_display="", actual_display="",
                diff_hint=f"重复提交未重复计分（{SUBMISSION_IDEMPOTENCY_WINDOW_MIN} 分钟内相同代码）",
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
    expected_display, actual_display = _build_display(lang, pdict, run_result, passed)
    feedback = review(lang, pdict, code, run_result, passed)
    difficulty = int(pdict.get("difficulty") or 3)
    _record_attempt(lang, pdict.get("id") or "", code, passed, feedback, dao, difficulty,
                    llm_degraded=is_degraded_feedback(feedback))

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
    _pid = str(pdict.get("id") or "")
    if not res.get("llm_ok") and dao is not None and _pid and not _pid.startswith("AI_VARIANT::"):
        # ②l1006-04/l1004-08 C 案：开放题断线发降级事件（不写 attempt——不把基础设施故障
        # 算成用户失败），断线事故在事件层可对账，与 run 臂口径统一为「可见但不混入计分」。
        try:
            dao.emit_event("ai_open_degraded", lang=lang, problem_id=_pid,
                           payload={"reason": "llm_unavailable"})
        except Exception:
            logger.warning("ai_open_degraded emit failed", exc_info=True)
    if res.get("llm_ok") and not _pid.startswith("AI_VARIANT::"):
        pid = _pid
        own_dao = dao is None
        d = dao or ProgressDAO()
        try:
            attempt_id = d.record_attempt_and_status(lang, pid, answer, res["passed"], res["feedback"])
            difficulty = int(pdict.get("difficulty") or 3)
            d.update_review_state(lang, pid, res["passed"], difficulty)
            dimensions = res.get("dimensions") or []
            if dimensions and attempt_id:
                d.record_rubric_scores(lang, pid, attempt_id, dimensions,
                                       prompt_version=res.get("prompt_version"),
                                       model=res.get("model"))
            # ③l1006-04/l1004-08 C 案：脏 JSON（score=None/维度空）显式 degraded 位——
            # 统计面按 payload 键过滤，attempts/rubric_scores 零 schema 改动。
            # l1007-27（l1007-06 遗留 1 C 案落地）：score=None 钳制——payload 不写 score 键
            # （统计面 SUM/AVG 天然忽略缺键，钳 0 会污染均值）；基线 0 起步（k1007-06 普查空集）。
            _score = res.get("score")
            _payload = {"passed": res["passed"],
                        "degraded": _score is None or not dimensions}
            if _score is not None:
                _payload["score"] = _score
            d.emit_event("ai_open_scored", lang=lang, problem_id=pid, payload=_payload)
        except Exception as e:
            logger.warning("_judge_open record failed: %s", e)
        finally:
            if own_dao:
                d.close()
    return result
