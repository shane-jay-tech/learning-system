# -*- coding: utf-8 -*-
"""content/ 题库 yaml 校验器（l1023-013 落盘；验证逻辑原型见 l1011-24）。

三功能（对齐 l1011-24 原型口径）：
  1. YAML 解析检查——content/ 下全部 *.yaml 逐件 yaml.safe_load，报解析错误；
  2. 必填字段检查（练习 schema）：statement / topic / difficulty 缺一计 ERROR（判退出码）；
     答案四键（expected_output|expected_rows|tests|rubric）全空、hints 缺失计 WARN
     （对齐 test_content_census.py 答案/hints 全量非空契约，仅提示不判退出码）；
  3. basename 唯一性——跨目录同名文件名计数（同名不同 topic 目录＝by design，仅提示不判错）。

TODO(l1023-012): content/paths/ 为学习路径定义 yaml（title/milestones schema，非练习 yaml），
  双 schema 判分支待姊妹单 l1023-012 闭合后接入；当前单 schema 口径下 paths/ 文件
  只做解析＋basename 两面，练习字段检查跳过（skipped 计数单列，不误报——l1011-24 实测
  paths/ 18 处字段缺失均属路径定义 schema 不同，非缺陷）。

用法：
  python scripts/validate_content.py                  # 全量扫描 content/（443 件口径）
  python scripts/validate_content.py --domain cpp,sql # 按域过滤（逗号分隔，含 paths）

只读：零写库、零写盘（仅 stdout 打印）。退出码：0＝无解析错误且练习域无 ERROR 级字段缺失；1＝有（WARN 不影响退出码）。
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
PATHS_DIRNAME = "paths"  # 路径定义域（练习字段检查跳过，见文件头 TODO）
ANSWER_KEYS = ("expected_output", "expected_rows", "tests", "rubric")
REQUIRED_KEYS = ("statement", "topic", "difficulty")


def scan(domain_filter=None):
    """扫描 content/ 全部 yaml，返回 (files, parse_errors, field_issues, skipped_paths, dup_basenames)。

    files: [{rel, domain}]; parse_errors: [(rel, errmsg)];
    field_issues: [{rel, missing, no_answer, no_hints}]（仅练习域）;
    skipped_paths: [rel]（paths/ 域跳过字段检查的文件）;
    dup_basenames: {basename: [rel, ...]}（出现 >1 次的同名件）。
    """
    yaml_paths = sorted(
        p for p in glob.glob(os.path.join(CONTENT_DIR, "**", "*.yaml"), recursive=True)
        if os.path.isfile(p)
    )
    files, parse_errors, field_issues, skipped_paths = [], [], [], []
    basename_map = collections.defaultdict(list)

    for path in yaml_paths:
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        domain = os.path.relpath(path, CONTENT_DIR).split(os.sep)[0]
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
            skipped_paths.append(rel)  # TODO(l1023-012)：双 schema 分支接入后按路径定义 schema 校验
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
    return files, parse_errors, field_issues, skipped_paths, dup_basenames


def main(argv=None):
    parser = argparse.ArgumentParser(description="content/ 题库 yaml 校验器（只读）")
    parser.add_argument("--domain", default="",
                        help="按一级域过滤（逗号分隔，如 python,cpp）；缺省=全量")
    args = parser.parse_args(argv)
    domain_filter = {d.strip() for d in args.domain.split(",") if d.strip()} or None

    files, parse_errors, field_issues, skipped_paths, dup_basenames = scan(domain_filter)

    by_domain = collections.Counter(f["domain"] for f in files)
    print("== content/ yaml 校验（l1023-013 落盘，口径 l1011-24）==")
    print(f"扫描文件数：{len(files)}  按域：{dict(sorted(by_domain.items()))}")
    if domain_filter:
        print(f"域过滤：{','.join(sorted(domain_filter))}")

    print(f"\n[1] YAML 解析：错误 {len(parse_errors)} 件")
    for rel, msg in parse_errors:
        print(f"  PARSE-ERR {rel}: {msg}")

    exercise_errors = [i for i in field_issues if i["severity"] == "error"]
    exercise_warns = [i for i in field_issues if i["severity"] == "warn"]
    print(f"[2] 练习 schema 字段：ERROR {len(exercise_errors)} 件／WARN {len(exercise_warns)} 件"
          f"（paths/ 跳过 {len(skipped_paths)} 件，待 l1023-012 双 schema）")
    for i in field_issues:
        bits = []
        if i["missing"]:
            bits.append(f"缺 {','.join(i['missing'])}")
        if i["no_answer"]:
            bits.append("答案四键全空")
        if i["no_hints"]:
            bits.append("缺 hints")
        print(f"  {i['severity'].upper()} {i['rel']}: {'；'.join(bits)}")

    print(f"[3] basename 跨目录同名：{len(dup_basenames)} 组（同名不同 topic 目录＝by design，仅提示）")
    for base, rels in sorted(dup_basenames.items()):
        print(f"  DUP {base} ×{len(rels)}: {'; '.join(rels)}")

    ok = not parse_errors and not exercise_errors
    print(f"\n结论：{'PASS' if ok else 'FAIL'}｜文件 {len(files)}／解析错误 {len(parse_errors)}"
          f"／字段 ERROR {len(exercise_errors)}／字段 WARN {len(exercise_warns)}"
          f"／paths 跳过 {len(skipped_paths)}／同名组 {len(dup_basenames)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
