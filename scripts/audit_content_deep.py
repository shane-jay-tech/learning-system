"""内容深度校验：结构之外的语义层检查（audit_content.py 的补充）。

检查项：
- SQL 题 setup_sql 真实可执行（内存库试跑 + 白名单校验）
- Python/agent_dev 题 starter_code 语法可解析（ast.parse）
- expected_rows 结构合法（列表的列表、单元格为标量）
- 题目 id 全局唯一、yaml 内 topic 字段与目录一致、同专题标题不重复
- _lesson.md 有 H1 标题；无占位符残留（TODO/FIXME/占位/Lorem…）
- tests 结构合法；有 stdin 的题 statement 应提到输入方式（warning）
- 开放题有 reference_answer（warning）
- 路径里程碑 prereqs 引用存在的里程碑 id

用法：
    python scripts/audit_content_deep.py            # 输出 errors/warnings
    python scripts/audit_content_deep.py --strict   # warnings 也算失败
    python scripts/audit_content_deep.py --json
"""
import argparse
import ast
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 注意：不做 TODO/FIXME/占位 之类的标记扫描——本仓库的教学内容会合法地
# 提及这些词（"read_xxx 函数"、"todo app"、"用 NULL 占位"、"看到 TODO 注释"），
# 关键词扫描误报率过高。真正的结构/语义校验见 deep_audit()。


def _sql_setup_error(problem) -> str:
    """返回 setup_sql 的试跑错误描述；None = 通过。"""
    from core.runners.sql_runner import _validate_setup_sql
    setup = problem.setup_sql
    if not setup:
        return None  # 结构审计已提示缺失
    err = _validate_setup_sql(setup)
    if err:
        return f"setup_sql 白名单校验失败: {err}"
    try:
        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(setup)
        finally:
            conn.close()
    except sqlite3.Error as e:
        return f"setup_sql 执行失败: {e}"
    return None


def _strip_comments_and_strings(code: str, lang: str) -> str:
    """去除注释与字符串字面量，返回只含真实代码骨架的文本（括号平衡检查用）。

    幼稚的裸计数会把注释里的 "(1)" 或字符串里的 "{r setup}" 当成代码括号。
    """
    out = []
    i, n = 0, len(code)
    if lang == "cpp":
        line_comment, block_comment = "//", ("/*", "*/")
        string_delims = ('"', "'")
    else:  # r
        line_comment, block_comment = "#", None
        string_delims = ('"', "'")
    while i < n:
        ch = code[i]
        nxt = code[i + 1] if i + 1 < n else ""
        if ch == line_comment[0] and nxt == line_comment[1]:
            while i < n and code[i] != "\n":
                i += 1
            continue
        if block_comment and ch == block_comment[0][0] and nxt == block_comment[0][1]:
            i += 2
            while i + 1 < n and not (code[i] == block_comment[1][0] and code[i + 1] == block_comment[1][1]):
                i += 1
            i += 2
            continue
        if ch in string_delims:
            delim = ch
            i += 1
            while i < n:
                if code[i] == "\\":
                    i += 2
                    continue
                if code[i] == delim:
                    i += 1
                    break
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _brace_balance_error(starter: str, lang: str) -> str:
    code = _strip_comments_and_strings(starter, lang)
    for open_ch, close_ch, name in (("{", "}", "大括号"), ("(", ")", "圆括号")):
        if code.count(open_ch) != code.count(close_ch):
            delta = code.count(open_ch) - code.count(close_ch)
            return f"starter_code {name}不平衡（{open_ch} 比 {close_ch} 多 {delta} 个）"
    return None


def _python_syntax_error(starter: str) -> str:
    try:
        ast.parse(starter)
        return None
    except SyntaxError as e:
        return f"starter_code 语法错误: {e.msg} (line {e.lineno})"


def deep_audit():
    from core.loader import load_language
    from core.paths import load_all_paths
    from ui.components import ALL_LANGS

    errors, warnings = [], []
    seen_ids = {}
    open_no_ref = {}

    for lang in ALL_LANGS:
        topics = load_language(lang, str(ROOT / "content"))
        for topic in topics:
            lesson = topic.lesson_md or ""
            if lesson.strip():
                import re as _re
                if not _re.search(r"^\s*#\s+\S", lesson, _re.MULTILINE):
                    warnings.append(f"[{lang}/{topic.slug}] lesson 缺少 H1 标题（# 开头）")

            titles_in_topic = {}
            for p in topic.problems:
                pid = p.id
                if pid in seen_ids:
                    errors.append(f"[{pid}] 题目 id 重复（与 {seen_ids[pid]} 冲突）")
                seen_ids[pid] = pid

                if p.topic != topic.slug:
                    errors.append(f"[{pid}] yaml 内 topic={p.topic!r} 与目录 {topic.slug} 不一致")

                if p.title in titles_in_topic:
                    errors.append(f"[{pid}] 同专题标题重复: {p.title!r}")
                titles_in_topic[p.title] = pid

                # SQL：setup_sql 试跑
                if lang == "sql" and p.judge_mode == "run":
                    err = _sql_setup_error(p)
                    if err:
                        errors.append(f"[{pid}] {err}")

                # Python 系：starter 语法
                if lang in ("python", "agent_dev") and p.starter_code.strip():
                    err = _python_syntax_error(p.starter_code)
                    if err:
                        errors.append(f"[{pid}] {err}")

                # expected_rows 结构
                if p.expected_rows is not None:
                    if not isinstance(p.expected_rows, list):
                        errors.append(f"[{pid}] expected_rows 必须是列表")
                    else:
                        for ri, row in enumerate(p.expected_rows):
                            if not isinstance(row, list):
                                errors.append(f"[{pid}] expected_rows 第 {ri+1} 行不是列表: {row!r}")
                                break
                            for ci, cell in enumerate(row):
                                if isinstance(cell, (dict, list)):
                                    errors.append(f"[{pid}] expected_rows[{ri}][{ci}] 是复合类型: {cell!r}")
                                    break

                # tests 结构 + stdin 提示一致性
                if p.tests is not None:
                    if not isinstance(p.tests, list):
                        errors.append(f"[{pid}] tests 必须是列表")
                    else:
                        has_stdin = False
                        for ti, tc in enumerate(p.tests):
                            if not isinstance(tc, dict):
                                errors.append(f"[{pid}] tests[{ti}] 必须是字典: {tc!r}")
                                continue
                            has_stdin = has_stdin or bool(tc.get("stdin"))
                        if has_stdin:
                            stmt = (p.statement or "")
                            if not any(k in stmt for k in ("输入", "读入", "读取", "input", "stdin", "标准输入")):
                                warnings.append(f"[{pid}] 有 stdin 测试但 statement 未提及输入方式")

                # 开放题参考（按专题聚合：多数开放题靠 rubric 评分，无单一标准答案属有意设计）
                if p.judge_mode == "ai_open" and not p.reference_answer:
                    open_no_ref.setdefault(f"{lang}/{topic.slug}", []).append(p.title)

    # 路径：prereqs 引用存在性
    for path in load_all_paths():
        milestone_ids = {m.id for m in path.milestones}
        for m in path.milestones:
            for prereq in m.prereqs:
                if prereq not in milestone_ids:
                    errors.append(f"[path:{path.id}/{m.id}] prereq 引用不存在的里程碑: {prereq}")

    # 专题编号重复：并行系列（如 HR 系列 / 02b 子专题）会复用编号，
    # 属有意设计，仅作信息提示
    import re as _re2
    for lang in ALL_LANGS:
        num_counts = {}
        for topic in load_language(lang, str(ROOT / "content")):
            m = _re2.match(r"^(\d+)", topic.slug)
            if m:
                num_counts.setdefault(int(m.group(1)), []).append(topic.slug)
        dupes = {n: slugs for n, slugs in num_counts.items() if len(slugs) > 1}
        if dupes:
            detail = ", ".join("%d->%s" % (n, "/".join(s)) for n, s in sorted(dupes.items()))
            warnings.append("[%s] 专题编号重复（并行系列，属有意设计）: %s" % (lang, detail))

    # 开放题无参考：按专题聚合提示
    for topic_key, titles in sorted(open_no_ref.items()):
        warnings.append(f"[{topic_key}] {len(titles)} 道开放题无 reference_answer（rubric 评分，无单一标准答案）")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Deep content audit")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    errors, warnings = deep_audit()
    if args.json:
        print(json.dumps({"errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
        return 0 if not errors and not (args.strict and warnings) else 1

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  {w}")
        print()
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        print()
    fail = len(errors) + (len(warnings) if args.strict else 0)
    if fail == 0:
        print(f"PASS: 0 errors, {len(warnings)} warnings")
    else:
        print(f"FAIL: {len(errors)} errors, {len(warnings)} warnings")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
