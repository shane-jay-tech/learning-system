# -*- coding: utf-8 -*-
"""content/ 题库 yaml 校验器（l1023-013 落盘；验证逻辑原型见 l1011-24）。

三功能（对齐 l1011-24 原型口径）：
  1. YAML 解析检查——content/ 下全部 *.yaml 逐件 yaml.safe_load，报解析错误；
  2. 必填字段检查·双 schema（l1023-012 接入）——按一级域区分：
     - 练习 schema（python/cpp/r/sql/agent_dev 等题库域）：statement / topic / difficulty
       缺一计 ERROR（判退出码）；答案四键（expected_output|expected_rows|tests|rubric）
       全空、hints 缺失计 WARN（对齐 test_content_census.py 答案/hints 全量非空契约，
       仅提示不判退出码）；
     - 路径定义 schema（paths/ 域，按目录判）：顶层 title / milestones 缺失或 milestones
       空、milestone 缺 id/title/topics/description 计 ERROR；顶层 subtitle/icon/
       estimated_hours 缺失计 WARN（l1023-012 实测 6 件现值全数满足，零新增告警）。
  3. basename 唯一性——跨目录同名文件名计数（同名不同 topic 目录＝by design，仅提示不判错）。

用法：
  python scripts/validate_content.py                  # 全量扫描 content/（443 件口径）
  python scripts/validate_content.py --domain cpp,sql # 按域过滤（逗号分隔，含 paths）

只读：零写库、零写盘（仅 stdout 打印）。退出码：0＝无解析错误且两类 schema 均无 ERROR 级字段缺失；1＝有（WARN 不影响退出码）。
"""
from __future__ import annotations

import argparse
import collections
import glob
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT, "content")
PATHS_DIRNAME = "paths"  # 路径定义域（按目录判双 schema，l1023-012）
ANSWER_KEYS = ("expected_output", "expected_rows", "tests", "rubric")
REQUIRED_KEYS = ("statement", "topic", "difficulty")
PATHS_REQUIRED = ("title", "milestones")
PATHS_WARN_KEYS = ("subtitle", "icon", "estimated_hours")
MILESTONE_REQUIRED = ("id", "title", "topics", "description")


def _check_paths_data(data):
    """路径定义 schema 校验（l1023-012）：返回 [(severity, message), ...]。

    ERROR：顶层缺 title/milestones、milestones 空或非列表、milestone 缺
    id/title/topics/description（topics 需非空列表）；
    WARN：顶层缺 subtitle/icon/estimated_hours。
    """
    issues = []
    if not isinstance(data, dict):
        return [("error", "路径定义 yaml 顶层非映射")]
    missing_top = [k for k in PATHS_REQUIRED if not data.get(k)]
    if missing_top:
        issues.append(("error", f"缺 {','.join(missing_top)}"))
    warn_top = [k for k in PATHS_WARN_KEYS if not data.get(k)]
    if warn_top:
        issues.append(("warn", f"缺 {','.join(warn_top)}"))
    milestones = data.get("milestones")
    if isinstance(milestones, list) and milestones:
        for idx, ms in enumerate(milestones, 1):
            if not isinstance(ms, dict):
                issues.append(("error", f"milestone#{idx} 非映射"))
                continue
            missing_ms = [k for k in MILESTONE_REQUIRED if not ms.get(k)]
            if missing_ms:
                issues.append(("error", f"milestone#{idx} 缺 {','.join(missing_ms)}"))
    return issues


def scan(domain_filter=None, content_dir=None):
    """扫描 content/ 全部 yaml，返回 (files, parse_errors, field_issues, path_issues, dup_basenames)。

    files: [{rel, domain}]; parse_errors: [(rel, errmsg)];
    field_issues: [{rel, severity, missing, no_answer, no_hints}]（练习 schema 域）;
    path_issues: [{rel, severity, message}]（paths/ 路径定义 schema，l1023-012）;
    dup_basenames: {basename: [rel, ...]}（出现 >1 次的同名件）。
    """
    content_root = content_dir or CONTENT_DIR
    rel_base = os.path.dirname(content_root)
    yaml_paths = sorted(
        p for p in glob.glob(os.path.join(content_root, "**", "*.yaml"), recursive=True)
        if os.path.isfile(p)
    )
    files, parse_errors, field_issues, path_issues = [], [], [], []
    basename_map = collections.defaultdict(list)

    for path in yaml_paths:
        rel = os.path.relpath(path, rel_base).replace("\\", "/")
        domain = os.path.relpath(path, content_root).split(os.sep)[0]
        if domain_filter and domain not in domain_filter:
            continue
        files.append({"rel": rel, "domain": domain})
        basename_map[os.path.basename(path)].append(rel)

        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            parse_errors.append((rel, str(exc).splitlines()[0]))
            continue

        if domain == PATHS_DIRNAME:
            # l1023-012 双 schema：paths/ 按路径定义 schema 校验（不再跳过）
            for severity, message in _check_paths_data(data):
                path_issues.append({"rel": rel, "severity": severity, "message": message})
            continue

        if not isinstance(data, dict):
            field_issues.append({"rel": rel, "severity": "error", "missing": list(REQUIRED_KEYS),
                                 "no_answer": True, "no_hints": True})
            continue
        missing = [k for k in REQUIRED_KEYS if not str(data.get(k, "")).strip()
                   and not (k == "difficulty" and data.get("difficulty") == 0)]
        no_answer = not any(data.get(k) for k in ANSWER_KEYS)
        no_hints = not data.get("hints")
        if missing or no_answer or no_hints:
            field_issues.append({"rel": rel, "severity": "error" if missing else "warn",
                                 "missing": missing,
                                 "no_answer": no_answer, "no_hints": no_hints})

    dup_basenames = {b: rels for b, rels in basename_map.items() if len(rels) > 1}
    return files, parse_errors, field_issues, path_issues, dup_basenames


def main(argv=None):
    parser = argparse.ArgumentParser(description="content/ 题库 yaml 校验器（只读）")
    parser.add_argument("--domain", default="",
                        help="按一级域过滤（逗号分隔，如 python,cpp）；缺省=全量")
    args = parser.parse_args(argv)
    domain_filter = {d.strip() for d in args.domain.split(",") if d.strip()} or None

    files, parse_errors, field_issues, path_issues, dup_basenames = scan(domain_filter)

    by_domain = collections.Counter(f["domain"] for f in files)
    print("== content/ yaml 校验（l1023-013 落盘，口径 l1011-24；双 schema l1023-012）==")
    print(f"扫描文件数：{len(files)}  按域：{dict(sorted(by_domain.items()))}")
    if domain_filter:
        print(f"域过滤：{','.join(sorted(domain_filter))}")

    print(f"\n[1] YAML 解析：错误 {len(parse_errors)} 件")
    for rel, msg in parse_errors:
        print(f"  PARSE-ERR {rel}: {msg}")

    exercise_errors = [i for i in field_issues if i["severity"] == "error"]
    exercise_warns = [i for i in field_issues if i["severity"] == "warn"]
    print(f"[2] 练习 schema 字段：ERROR {len(exercise_errors)} 件／WARN {len(exercise_warns)} 件")
    for i in field_issues:
        bits = []
        if i["missing"]:
            bits.append(f"缺 {','.join(i['missing'])}")
        if i["no_answer"]:
            bits.append("答案四键全空")
        if i["no_hints"]:
            bits.append("缺 hints")
        print(f"  {i['severity'].upper()} {i['rel']}: {'；'.join(bits)}")

    path_errors = [i for i in path_issues if i["severity"] == "error"]
    path_warns = [i for i in path_issues if i["severity"] == "warn"]
    print(f"[3] 路径定义 schema 字段（paths/，l1023-012）：ERROR {len(path_errors)} 件／WARN {len(path_warns)} 件")
    for i in path_issues:
        print(f"  {i['severity'].upper()} {i['rel']}: {i['message']}")

    print(f"[4] basename 跨目录同名：{len(dup_basenames)} 组（同名不同 topic 目录＝by design，仅提示）")
    for base, rels in sorted(dup_basenames.items()):
        print(f"  DUP {base} ×{len(rels)}: {'; '.join(rels)}")

    ok = not parse_errors and not exercise_errors and not path_errors
    print(f"\n结论：{'PASS' if ok else 'FAIL'}｜文件 {len(files)}／解析错误 {len(parse_errors)}"
          f"／字段 ERROR {len(exercise_errors)}／字段 WARN {len(exercise_warns)}"
          f"／路径 ERROR {len(path_errors)}／路径 WARN {len(path_warns)}／同名组 {len(dup_basenames)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
