# -*- coding: utf-8 -*-
"""r 题库判定模式显式化（D6 降级为普通题，2026-09-20）。

背景（l920-02 普查结论 + 用户 2026-09-20 拍板）：
  content/r 下 84 个题目的 yaml 无一含 expected_rows / tests 键（grep 0 命中），
  即 r 题库根本没有「多 DataFrame 机判题」这种形态；r 实际判定面是
  expected_output 70（stdout 比对＝普通题）＋ rubric/journal 14（judge_mode: ai_open）。
  用户拍板 D6：**降级为普通题，不硬补测试用例**。

本脚本做什么：
  给 70 个「有 expected_output、未写 judge_mode」的 r 题目补一行显式
  judge_mode: run（与既有的 14 个 judge_mode: ai_open 对齐）——
  **只加标记字段，题干与答案字段一律不动**（脚本内建有回读断言）。
  加完 r 题库 84/84 判定模式全部显式，不再依赖 loader 的隐式默认值，
  「r 是普通题（stdout 比对）」这个决定因此可被 grep/测试钉住。

2026-09-20 复核加固（GPT 独立复核判「暂不建议销项」后按意见修复，
详见 docs/insights/learn-d5d6-review-fix-20260920.md）：
  · **不再依赖 assert 做防护**——全部校验改为显式抛 HardeningError 并由 main()
    转成非零退出码，python -O（assert 被剥离）下同样拦得住（有测试钉住）；
  · 插入边界校验：锚点 tags: 必须顶格、插入点之后一行不得是缩进续行，
    插入后 yaml 解析回读必须「只多 judge_mode」；
  · 合法值枚举 run / ai_open——出现第三种取值即异常（不是静默放过）；
  · 异常输入（无 tags / 无 expected_output / 空输出 / 坏 yaml / 模式值非法 /
    空 judge_mode 行 / 重复 judge_mode 行）→ **整批 fail-closed，一个字节都不写**；
  · 字节级单行差分证明：写盘前校验 new == old + 恰一行，写盘后回读比对新字节；
  · 原子写入（临时文件 + os.replace），且目标路径必须落在 <root>/content/r/ 内；
  · --root 可对临时基线跑端到端；--expect-distribution run=70,ai_open=14
    把 70/14 精确分布做成门禁。

纪律：
  · 默认 dry-run，只打印计划；写盘必须显式 --apply；
  · 幂等：已有 judge_mode 的文件一律跳过，重复 --apply 零改动；
  · 逐文件回读断言：写盘前后 yaml 解析结果除 judge_mode 外必须完全相等，
    且行尾风格（LF/CRLF）保持原样；
  · 只读/只写 content/r/*/*.yaml，零网络、零依赖、不碰其他语言。

用法：
  python scripts/mark_r_judge_plain.py                     # dry-run：列出待改文件
  python scripts/mark_r_judge_plain.py --apply             # 写盘（幂等）
  python scripts/mark_r_judge_plain.py --check             # 校验是否已全部显式（不满足则 exit 1）
  python scripts/mark_r_judge_plain.py --check --expect-distribution run=70,ai_open=14
  python scripts/mark_r_judge_plain.py --root <dir> --apply   # 对临时基线跑（测试用）
"""
import argparse
import collections
import glob
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MARK = "judge_mode: run"
MARK_MODE = "run"
VALID_JUDGE_MODES = ("run", "ai_open")
# 只加标记、绝不动的字段（脚本自证「题干与答案字段零改动」）
ANSWER_KEYS = ("title", "topic", "difficulty", "tags", "statement", "starter_code",
               "expected_output", "expected_rows", "setup_sql", "tests", "hints",
               "rubric", "reference_answer")

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2


class HardeningError(RuntimeError):
    """显式校验失败。

    刻意不用 assert：assert 会被 python -O 剥离，安全依赖它会静默失效；
    本异常由 main() 捕获并转成非零退出码。
    """


def _fail(msg: str):
    """永不返回：抛出 HardeningError。"""
    raise HardeningError(msg)


# ---------------------------------------------------------------- 路径与读取

def content_root(root) -> Path:
    return Path(root).resolve() / "content"


def r_dir(root) -> Path:
    return content_root(root) / "r"


def r_files(root):
    """<root>/content/r/*/*.yaml（排序保证可复现）。"""
    return sorted(Path(p) for p in glob.glob(str(r_dir(root) / "*" / "*.yaml")))


def _rel(path: Path, root) -> str:
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def _assert_inside(path: Path, base: Path) -> None:
    """路径边界：只允许写 <root>/content/r/ 之内的文件。"""
    try:
        Path(path).resolve().relative_to(Path(base).resolve())
    except ValueError:
        _fail("拒绝写 content/r 之外的文件：%s" % path)


def _decode(raw: bytes, path) -> tuple:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        _fail("%s 不是合法 UTF-8，拒绝处理：%s" % (path, e))
    if "\r" in text.replace("\r\n", ""):
        _fail("%s 存在孤立 CR（混合行尾），拒绝写入以免改动字节" % path)
    eol = "\r\n" if "\r\n" in text else "\n"
    return text, eol


def _parse(text: str, path):
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        _fail("%s yaml 解析失败：%s" % (path, str(e)[:160]))
    if not isinstance(data, dict):
        _fail("%s yaml 根节点不是 mapping（%s）" % (path, type(data).__name__))
    return data


def _judge_mode_lines(text: str):
    """文本层面（第 0 列）的 judge_mode 行——用于查重复/空值这种解析看不见的坑。"""
    return [l for l in text.splitlines() if l.startswith("judge_mode:")]


# ---------------------------------------------------------------- 插入

def _insert_line_after_tags(text: str, line: str, eol: str, path=None) -> str:
    """在顶层 tags 字段之后、下一个顶层键之前插入一行；位置不确定即拒绝。

    边界规则：
      · 锚点 tags: 必须是第 0 列（块标量内容恒缩进，不会误命中）；
      · tags 为块状列表时插到块尾；
      · 插入点之后若有非空行，必须是顶层键（第 0 列）——缩进续行说明位置不明确。
    """
    if eol in line:
        _fail("待插入行不得自带换行")
    lines = text.splitlines(keepends=True)
    idx = None
    for i, l in enumerate(lines):
        if l.startswith("tags:"):
            idx = i
            break
    if idx is None:
        _fail("%s 找不到顶层 tags: 行，拒绝猜测插入位置" % path)
    j = idx
    if lines[idx].rstrip("\r\n").strip() == "tags:":
        k = idx + 1
        while k < len(lines) and lines[k].strip().startswith("- "):
            j = k
            k += 1
    if j + 1 < len(lines):
        nxt = lines[j + 1].rstrip("\r\n")
        if nxt.strip() and nxt[0] in (" ", "\t"):
            _fail("%s tags 之后是缩进续行（%r），插入位置不明确" % (path, nxt.strip()[:30]))
    return "".join(lines[:j + 1]) + line + eol + "".join(lines[j + 1:])


def _assert_single_line_insert(old: bytes, new: bytes, inserted: bytes, path) -> None:
    """字节级证明：new 相对 old **恰好插入一行** inserted，无其他任何字节变化。"""
    if old == new:
        _fail("%s 写盘前后字节相同（应恰插入一行）" % path)
    i = 0
    while i < min(len(old), len(new)) and old[i] == new[i]:
        i += 1
    j = 0
    while j < min(len(old), len(new)) - i and old[len(old) - 1 - j] == new[len(new) - 1 - j]:
        j += 1
    ins = new[i:len(new) - j]
    dele = old[i:len(old) - j]
    if dele != b"" or ins != inserted:
        _fail("%s 差分不是「恰插入一行」：插入=%r 删除=%r" % (path, ins[:60], dele[:60]))


# ---------------------------------------------------------------- 扫描 / 写盘

def scan(root) -> dict:
    """返回 {files, todo, explicit, anomalies}；异常输入只记录，不写盘不上抛。"""
    files = r_files(root)
    todo, explicit, anomalies = [], {}, []
    for f in files:
        rel = _rel(f, root)
        try:
            raw = f.read_bytes()
            text, eol = _decode(raw, f)
            data = _parse(text, f)
            lines = _judge_mode_lines(text)
            mode = data.get("judge_mode")
            if mode is None and "judge_mode" in data:
                _fail("judge_mode 值为空（yaml 显式 null）——形态异常，人工处理")
            if mode is None and lines:
                _fail("存在 judge_mode 行但解析不到值（空值/重复行）——形态异常，人工处理")
            if mode is not None:
                if mode not in VALID_JUDGE_MODES:
                    _fail("judge_mode 取值非法：%r（合法值 %s）"
                          % (mode, "/".join(VALID_JUDGE_MODES)))
                if len(lines) != 1:
                    _fail("judge_mode 文本行数 = %d（应恰 1 行）" % len(lines))
                explicit[rel] = mode
                continue
            if "expected_output" not in data:
                _fail("既无 judge_mode 又无 expected_output——形态异常，人工处理")
            if not str(data.get("expected_output") or "").strip():
                _fail("expected_output 为空——判定面为空，拒绝补 judge_mode: run")
            _insert_line_after_tags(text, MARK, eol, f)   # 预检插入位置（不写盘）
            todo.append(f)
        except HardeningError as e:
            anomalies.append((rel, str(e)))
    return {"files": files, "todo": todo, "explicit": explicit, "anomalies": anomalies}


def apply_one(root, path) -> bytes:
    """写盘单个文件，返回新字节；任何校验失败即抛 HardeningError（写盘前）。"""
    path = Path(path)
    _assert_inside(path, r_dir(root))
    old = path.read_bytes()
    text, eol = _decode(old, path)
    data = _parse(text, path)
    if "judge_mode" in data:
        _fail("%s 已有 judge_mode，拒绝重复插入（幂等保护）" % _rel(path, root))
    if _judge_mode_lines(text):
        _fail("%s 文本层已存在 judge_mode 行，拒绝插入第二行" % _rel(path, root))
    new_text = _insert_line_after_tags(text, MARK, eol, path)
    new_data = _parse(new_text, path)
    if new_data.get("judge_mode") != MARK_MODE:
        _fail("%s 插入后回读 judge_mode 未生效" % _rel(path, root))
    expect = dict(data)
    expect["judge_mode"] = MARK_MODE
    if new_data != expect:
        _fail("%s 除 judge_mode 外还有字段被改动，拒绝写盘" % _rel(path, root))
    for key in ANSWER_KEYS:
        if key in data and data[key] != new_data.get(key):
            _fail("%s 字段 %s 发生变化，拒绝写盘" % (_rel(path, root), key))
    new = new_text.encode("utf-8")
    _assert_single_line_insert(old, new, (MARK + eol).encode("utf-8"), _rel(path, root))
    # 原子写：临时文件 + os.replace，失败不留半个文件
    tmp = path.with_name(path.name + ".tmp%d" % os.getpid())
    try:
        with open(tmp, "wb") as fh:
            fh.write(new)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(str(tmp), str(path))
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
    if path.read_bytes() != new:
        _fail("%s 写盘回读字节不一致（原子写失败？）" % _rel(path, root))
    return new


# ---------------------------------------------------------------- CLI

def _parse_expected(spec):
    if not spec:
        return None
    out = {}
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise HardeningError("--expect-distribution 片段无法解析：%r（形如 run=70,ai_open=14）" % part)
        k, v = part.split("=", 1)
        k = k.strip()
        if k not in VALID_JUDGE_MODES:
            raise HardeningError("--expect-distribution 出现非法模式名：%r" % k)
        try:
            out[k] = int(v)
        except ValueError:
            raise HardeningError("--expect-distribution 计数不是整数：%r" % part)
    return out


def _describe(s, root, expected):
    dist = collections.Counter(s["explicit"].values())
    print("content/r 题目 yaml 总数 = %d（%s）" % (len(s["files"]), r_dir(root)))
    print("已显式 judge_mode = %d（%s）"
          % (len(s["explicit"]), "、".join("%s %d" % (k, dist.get(k, 0))
                                          for k in VALID_JUDGE_MODES)))
    print("待补 judge_mode = %d" % len(s["todo"]))
    if expected is not None:
        print("期望分布 = %s" % expected)
    return dist


def _run(args) -> int:
    root = Path(args.root).resolve()
    if not r_dir(root).is_dir():
        _fail("目录不存在：%s（--root 指向仓库根，其下应有 content/r/）" % r_dir(root))
    expected = _parse_expected(args.expect_distribution)
    s = scan(root)
    if s["anomalies"]:
        for rel, why in s["anomalies"]:
            print("  [异常] %s：%s" % (rel, why))
        print("FAIL：存在 %d 个形态异常文件，整批不写盘（fail-closed）" % len(s["anomalies"]))
        return EXIT_FAIL
    dist = _describe(s, root, expected)

    if args.check:
        if expected is not None and dict(dist) != expected:
            print("FAIL：judge_mode 分布 %s != 期望 %s" % (dict(dist), expected))
            return EXIT_FAIL
        if s["todo"]:
            for f in s["todo"]:
                print("  [缺]", _rel(f, root))
            print("FAIL：仍有题目依赖隐式默认判定模式")
            return EXIT_FAIL
        print("PASS：%d/%d 判定模式全部显式" % (len(s["explicit"]), len(s["files"])))
        return EXIT_OK

    if not args.apply:
        for f in s["todo"]:
            print("  [dry-run] 将补 %s → %s" % (MARK, _rel(f, root)))
        print("dry-run 结束（未写盘；加 --apply 落盘）")
        return EXIT_OK

    for f in s["todo"]:
        apply_one(root, f)
    written = len(s["todo"])
    rest = scan(root)
    if rest["anomalies"]:
        for rel, why in rest["anomalies"]:
            print("  [写盘后异常] %s：%s" % (rel, why))
        return EXIT_FAIL
    dist_after = collections.Counter(rest["explicit"].values())
    print("已写盘 = %d" % written)
    print("回读：已显式 = %d；仍待补 = %d" % (len(rest["explicit"]), len(rest["todo"])))
    if expected is not None and dict(dist_after) != expected:
        print("FAIL：写盘后 judge_mode 分布 %s != 期望 %s" % (dict(dist_after), expected))
        return EXIT_FAIL
    if rest["todo"]:
        for f in rest["todo"]:
            print("  [残留]", _rel(f, root))
        return EXIT_FAIL
    print("PASS：写盘完成且回读一致（幂等：再跑 --apply 将零改动）")
    return EXIT_OK


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="r 题库判定模式显式化（D6）")
    ap.add_argument("--apply", action="store_true", help="写盘（默认只 dry-run）")
    ap.add_argument("--check", action="store_true", help="只校验显式化是否完成，未完成 exit 1")
    ap.add_argument("--root", default=str(ROOT),
                    help="仓库根（其下需有 content/r/）；默认脚本所在仓库，测试可指临时基线")
    ap.add_argument("--expect-distribution", default=None, metavar="run=70,ai_open=14",
                    help="把判定模式精确分布做成门禁，不符即 exit 1")
    args = ap.parse_args(argv)
    try:
        return _run(args)
    except HardeningError as e:
        print("FAIL：%s" % e, file=sys.stderr)
        return EXIT_FAIL


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    sys.exit(main())
