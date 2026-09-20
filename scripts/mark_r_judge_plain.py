# -*- coding: utf-8 -*-
"""r 题库判定模式显式化（D6 降级为普通题，2026-09-20）。

背景（l920-02 普查结论 + 用户 2026-09-20 拍板）：
  content/r 下 84 个题目的 yaml 无一含 expected_rows / tests 键（grep 0 命中），
  即 r 题库根本没有「多 DataFrame 机判题」这种形态；r 实际判定面是
  expected_output 70（stdout 比对＝普通题）＋ rubric/journal 14（judge_mode: ai_open）。
  用户拍板 D6：**降级为普通题，不硬补测试用例**。

本脚本做什么：
  给 70 个「有 expected_output、未写 judge_mode」的 r 题目补一行显式
  `judge_mode: run`（与既有的 14 个 `judge_mode: ai_open` 对齐）——
  **只加标记字段，题干与答案字段一律不动**（脚本内建有回读断言）。
  加完 r 题库 84/84 判定模式全部显式，不再依赖 loader 的隐式默认值，
  「r 是普通题（stdout 比对）」这个决定因此可被 grep/测试钉住。

纪律：
  · 默认 dry-run，只打印计划；写盘必须显式 --apply；
  · 幂等：已有 judge_mode 的文件一律跳过，重复 --apply 零改动；
  · 逐文件回读断言：写盘前后 yaml 解析结果除 judge_mode 外必须完全相等，
    且行尾风格（LF/CRLF）保持原样；
  · 只读/只写 content/r/*/*.yaml，零网络、零依赖、不碰其他语言。

用法：
  python scripts/mark_r_judge_plain.py            # dry-run：列出待改文件
  python scripts/mark_r_judge_plain.py --apply    # 写盘（幂等）
  python scripts/mark_r_judge_plain.py --check    # 校验：84/84 是否已全部显式（不满足则 exit 1）
"""
import argparse
import glob
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
R_GLOB = str(ROOT / "content" / "r" / "*" / "*.yaml")
MARK = "judge_mode: run"


def _insert_after_tags(text: str, eol: str) -> str:
    """在顶层 tags 块之后插入标记行；tags 为块状列表时插到块尾。"""
    lines = text.splitlines(keepends=True)
    idx = None
    for i, line in enumerate(lines):
        if line.startswith("tags:"):
            idx = i
            break
    if idx is None:
        raise ValueError("找不到顶层 tags: 行，拒绝猜测插入位置")
    # tags 为块状列表（值在后续缩进行）时，插到块尾
    j = idx
    if lines[idx].rstrip("\r\n").strip() == "tags:":
        k = idx + 1
        while k < len(lines) and lines[k].strip().startswith("- "):
            j = k
            k += 1
    return "".join(lines[:j + 1]) + MARK + eol + "".join(lines[j + 1:])


def _plan():
    """返回 [(path, before_dict)]，只含有 expected_output 且未写 judge_mode 的文件。"""
    todo, already = [], []
    for f in sorted(glob.glob(R_GLOB)):
        data = yaml.safe_load(open(f, encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError(f"{f} 解析结果不是 mapping")
        if "judge_mode" in data:
            already.append((f, data.get("judge_mode")))
            continue
        if not data.get("expected_output"):
            raise ValueError(f"{f} 既无 judge_mode 又无 expected_output——形态异常，人工处理")
        todo.append(f)
    return todo, already


def _apply(f: str) -> None:
    raw = open(f, "rb").read()
    text = raw.decode("utf-8")
    before = yaml.safe_load(text)
    eol = "\r\n" if "\r\n" in text else "\n"
    new_text = _insert_after_tags(text, eol)
    after = yaml.safe_load(new_text)
    # 回读断言①：只多了 judge_mode，其他键值逐字相等（题干/答案字段未动）
    assert after.get("judge_mode") == "run", f"{f} judge_mode 未生效"
    expect = dict(before)
    expect["judge_mode"] = "run"
    assert after == expect, f"{f} 除 judge_mode 外还有字段被改动，拒绝写盘"
    # 回读断言②：答案面与题干字节级不变（再证一次，防止 yaml round-trip 假相等）
    for key in ("statement", "expected_output", "rubric", "reference_answer",
                "hints", "starter_code", "title", "topic", "difficulty", "tags"):
        if key in before:
            assert before[key] == after[key], f"{f} 字段 {key} 发生变化"
    open(f, "wb").write(new_text.encode("utf-8"))


def main():
    ap = argparse.ArgumentParser(description="r 题库判定模式显式化（D6）")
    ap.add_argument("--apply", action="store_true", help="写盘（默认只 dry-run）")
    ap.add_argument("--check", action="store_true", help="只校验显式化是否完成，未完成 exit 1")
    args = ap.parse_args()

    todo, already = _plan()
    total = len(todo) + len(already)
    if args.check:
        print(f"r 题目 yaml 总数 = {total}")
        print(f"已显式 judge_mode = {len(already)}（ai_open {sum(1 for _, v in already if v == 'ai_open')}"
              f" / run {sum(1 for _, v in already if v == 'run')}）")
        print(f"待补 judge_mode = {len(todo)}")
        if todo:
            for f in todo:
                print("  [缺]", os.path.relpath(f, ROOT))
            print("FAIL：仍有题目依赖隐式默认判定模式")
            return 1
        print("PASS：84/84 判定模式全部显式")
        return 0

    print(f"r 题目 yaml 总数 = {total}；已显式 = {len(already)}；待补 = {len(todo)}")
    if not args.apply:
        for f in todo:
            print("  [dry-run] 将补 judge_mode: run →", os.path.relpath(f, ROOT))
        print("dry-run 结束（未写盘；加 --apply 落盘）")
        return 0

    written = 0
    for f in todo:
        _apply(f)
        written += 1
    # 写盘后立刻回读：再计划一次必须为空（幂等自证）
    rest, after_already = _plan()
    print(f"已写盘 = {written}")
    print(f"回读：已显式 = {len(after_already)}；仍待补 = {len(rest)}")
    if rest:
        for f in rest:
            print("  [残留]", os.path.relpath(f, ROOT))
        return 1
    print("PASS：写盘完成且回读一致（幂等：再跑 --apply 将零改动）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
