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

2026-09-20 第二轮复核加固（GPT 复审 4 条未消解意见 → SCRIPT-001..004）：
  · **SCRIPT-001 批量原子性**：--apply 不再逐文件「生成+写盘」，改为两阶段——
    ① prepare_all 把全部目标生成为 (old, new) 并**全部验证通过**（本阶段零写盘），
    ② commit_all 先进 staging（全部新内容落成同目录排他临时文件），再逐个
    os.replace，任一失败即把**已替换的文件回滚成原字节**；提交后回读不达标
    （含最终 scan 异常/分布不符）同样整批回滚。要么全写、要么全不写。
  · **SCRIPT-002 临时文件安全**：废弃固定名 <file>.tmp<PID>（可被预置符号链接抢占），
    改用 tempfile.mkstemp(dir=path.parent, prefix=..., suffix=...) 的 O_EXCL 独占 fd
    写入，并显式校验「临时名是普通文件且 inode/st_dev == fd 的 inode/st_dev」，
    拦住创建后被替换（TOCTOU）的情况；目标本身是符号链接一律拒绝。
  · **SCRIPT-003 异常处理完整性**：scan/apply/commit 全程把 OSError、UnicodeError
    与 yaml 解析异常统一转成 HardeningError（统一 FAIL + 非零退出）；提交前用
    「文件集合 + 逐文件 sha256 快照」复核，发现增删或内容被并发改动即终止且不提交。
  · **SCRIPT-004 空输入边界**：content/r 下 0 个 yaml 不再 vacuous pass
    （旧输出「PASS：0/0 判定模式全部显式」什么也没证明），默认判 FAIL；
    仅小型 fixture 场景可显式加 --allow-empty。

纪律：
  · 默认 dry-run，只打印计划；写盘必须显式 --apply；
  · 幂等：已有 judge_mode 的文件一律跳过，重复 --apply 零改动；
  · 逐文件回读断言：写盘前后 yaml 解析结果除 judge_mode 外必须完全相等，
    且行尾风格（LF/CRLF）保持原样；
  · 只读/只写 content/r/*/*.yaml，零网络、零依赖、不碰其他语言。

用法：
  python scripts/mark_r_judge_plain.py                     # dry-run：列出待改文件
  python scripts/mark_r_judge_plain.py --apply             # 写盘（幂等、批量原子）
  python scripts/mark_r_judge_plain.py --check             # 校验是否已全部显式（不满足则 exit 1）
  python scripts/mark_r_judge_plain.py --check --expect-distribution run=70,ai_open=14
  python scripts/mark_r_judge_plain.py --root <dir> --apply   # 对临时基线跑（测试用）
  python scripts/mark_r_judge_plain.py --root <dir> --check --allow-empty  # 空 fixture 显式放行
"""
import argparse
import collections
import glob
import hashlib
import os
import stat
import sys
import tempfile
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


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _unlink(path) -> None:
    """尽力删除（含符号链接本身；不存在也不算错）。绝不吞掉别的动作。"""
    try:
        os.unlink(str(path))
    except OSError:
        pass


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


# ---------------------------------------------------------------- 扫描

def scan(root) -> dict:
    """返回 {files, todo, explicit, anomalies, snapshot}。

    异常输入只记录、不上抛；读盘/权限/文件消失（OSError）等一律转成 anomaly，
    由 _run 统一 fail-closed（一个字节都不写）。snapshot 是「相对路径 → sha256」的
    文件集合快照，供提交前复核「文件没被增删、内容没被并发改动」。
    """
    todo, explicit, anomalies, snapshot = [], {}, [], {}
    try:
        files = r_files(root)
    except OSError as e:
        _fail("扫描 content/r 失败：%s" % e)
    except UnicodeError as e:
        _fail("扫描 content/r 时编码异常：%s" % e)
    for f in files:
        rel = _rel(f, root)
        try:
            raw = f.read_bytes()
            snapshot[rel] = _sha(raw)
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
        except (OSError, UnicodeError, yaml.YAMLError) as e:
            # 权限/文件消失/是目录/编码或解析异常：一律转成统一 FAIL，不崩栈
            anomalies.append((rel, "读取/解析异常（%s）：%s" % (type(e).__name__, e)))
    return {"files": files, "todo": todo, "explicit": explicit,
            "anomalies": anomalies, "snapshot": snapshot}


# ---------------------------------------------------------------- 生成计划（零写盘）

def prepare_one(root, path) -> dict:
    """只读 + 全量校验，产出一个提交计划；**本函数绝不写盘**。

    计划 = {path, rel, old, new, old_sha, new_sha}；任何校验不通过即抛
    HardeningError，调用方整批终止（这就是「先全部生成并验证，再进入提交」的前提）。
    """
    path = Path(path)
    _assert_inside(path, r_dir(root))
    rel = _rel(path, root)
    if os.path.islink(str(path)):
        _fail("%s 是符号链接，拒绝写入（路径边界可能被绕过）" % rel)
    try:
        old = path.read_bytes()
    except OSError as e:
        _fail("%s 读取失败：%s" % (rel, e))
    except UnicodeError as e:
        _fail("%s 读取时编码异常：%s" % (rel, e))
    text, eol = _decode(old, path)
    data = _parse(text, path)
    if "judge_mode" in data:
        _fail("%s 已有 judge_mode，拒绝重复插入（幂等保护）" % rel)
    if _judge_mode_lines(text):
        _fail("%s 文本层已存在 judge_mode 行，拒绝插入第二行" % rel)
    new_text = _insert_line_after_tags(text, MARK, eol, path)
    new_data = _parse(new_text, path)
    if new_data.get("judge_mode") != MARK_MODE:
        _fail("%s 插入后回读 judge_mode 未生效" % rel)
    expect = dict(data)
    expect["judge_mode"] = MARK_MODE
    if new_data != expect:
        _fail("%s 除 judge_mode 外还有字段被改动，拒绝写盘" % rel)
    for key in ANSWER_KEYS:
        if key in data and data[key] != new_data.get(key):
            _fail("%s 字段 %s 发生变化，拒绝写盘" % (rel, key))
    new = new_text.encode("utf-8")
    _assert_single_line_insert(old, new, (MARK + eol).encode("utf-8"), rel)
    return {"path": path, "rel": rel, "old": old, "new": new,
            "old_sha": _sha(old), "new_sha": _sha(new)}


def prepare_all(root, paths) -> list:
    """把**全部**目标文件生成为 (old, new) 并逐条验证通过；任一失败即上抛、零写盘。"""
    return [prepare_one(root, p) for p in paths]


# ---------------------------------------------------------------- 临时文件（安全）

def _assert_temp_identity(tmp: Path, st_fd, when: str) -> None:
    """临时名必须仍是「我们独占创建的那个普通文件」——否则拒绝（防 TOCTOU 换名）。"""
    st_name = os.lstat(str(tmp))
    if not stat.S_ISREG(st_name.st_mode):
        _fail("临时文件 %s 不是普通文件（疑似符号链接/被替换，%s），拒绝写入" % (tmp, when))
    if (st_name.st_dev, st_name.st_ino) != (st_fd.st_dev, st_fd.st_ino):
        _fail("临时文件 %s 与独占 fd 不是同一个 inode（创建后被替换，%s），拒绝写入" % (tmp, when))


def _make_temp(path: Path, data: bytes, base=None) -> Path:
    """在目标同目录排他创建临时文件并写入 data，返回临时路径。

    安全要点（SCRIPT-002）：
      · tempfile.mkstemp 用 O_CREAT|O_EXCL 拿独占 fd，**绝不复用已存在的名字**——
        预先摆好的 <name>.tmp<PID> 符号链接因此无从命中（旧实现的固定名就栽在这）；
      · 写入走已持有的 fd，名字事后被换掉也改不了写入目标；
      · 再显式校验「临时名是普通文件，且 st_dev/st_ino == fd 的 st_dev/st_ino」，
        把「创建后被换成符号链接/硬链接」（TOCTOU）也拦下来。
    """
    fd = None
    tmp = None
    try:
        try:
            fd, name = tempfile.mkstemp(dir=str(path.parent),
                                        prefix=path.name + ".", suffix=".tmp")
        except OSError as e:
            _fail("创建临时文件失败（%s）：%s" % (path.parent, e))
        tmp = Path(name)
        if base is not None:
            _assert_inside(tmp, base)
        st_fd = os.fstat(fd)
        _assert_temp_identity(tmp, st_fd, "写入前")
        with os.fdopen(fd, "wb") as fh:
            fd = None                     # 所有权交给文件对象
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        # 写入后再验一次：把窗口压到「本次校验 → os.replace」之间，越短越安全
        _assert_temp_identity(tmp, st_fd, "写入后提交前")
        return tmp
    except BaseException:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if tmp is not None:
            _unlink(tmp)
        raise


def _replace_bytes(path: Path, data: bytes, base=None) -> None:
    """排他临时文件 + os.replace 写单个文件的字节（提交与回滚共用），写后即回读比对。"""
    tmp = _make_temp(path, data, base)
    try:
        os.replace(str(tmp), str(path))
    except OSError as e:
        _unlink(tmp)
        _fail("写入 %s 失败：%s" % (path, e))
    if os.path.islink(str(path)):
        _fail("%s 写入后变成符号链接，拒绝接受" % path)
    try:
        back = path.read_bytes()
    except OSError as e:
        _fail("%s 写入后回读失败：%s" % (path, e))
    if back != data:
        _fail("%s 写入后回读字节不一致（原子写失败？）" % path)


# ---------------------------------------------------------------- 提交（批量原子 + 回滚）

def _verify_unchanged(root, plans, expect) -> None:
    """提交前复核：文件集合无增删、目标字节 == 准备时、其他文件内容未被改动。

    任何一项不符即 HardeningError → 整批终止、**一个字节都不写**。
    """
    try:
        now = r_files(root)
    except OSError as e:
        _fail("提交前重新扫描 content/r 失败：%s" % e)
    now_map = {_rel(f, root): f for f in now}
    if expect is not None:
        added = sorted(set(now_map) - set(expect))
        removed = sorted(set(expect) - set(now_map))
        if added or removed:
            _fail("扫描后 content/r 文件集合发生变化（新增 %s / 删除 %s），终止且不提交"
                  % (added[:5], removed[:5]))
    plans_by_rel = {p["rel"]: p for p in plans}
    for rel, old_sha in (expect or {}).items():
        f = now_map.get(rel)
        if f is None:
            _fail("%s 在准备后消失，终止且不提交" % rel)
        try:
            raw = f.read_bytes()
        except OSError as e:
            _fail("%s 复核读取失败：%s" % (rel, e))
        plan = plans_by_rel.get(rel)
        if plan is not None:
            if raw != plan["old"]:
                _fail("%s 在准备阶段后被改动（并发修改），终止且不提交" % rel)
        elif _sha(raw) != old_sha:
            _fail("%s 在扫描后被改动（并发修改），终止且不提交" % rel)


def _rollback(applied, base=None) -> list:
    """把已替换的文件恢复原字节；返回回滚失败的 [(rel, why)]（空列表 = 全部成功）。"""
    failures = []
    for p in reversed(list(applied)):
        try:
            _replace_bytes(p["path"], p["old"], base)
            if p["path"].read_bytes() != p["old"]:
                failures.append((p["rel"], "回滚后字节仍不等于原字节"))
        except (HardeningError, OSError) as e:
            failures.append((p["rel"], str(e)))
    return failures


def commit_all(root, plans, expect=None) -> list:
    """批量提交（all-or-nothing）；返回已提交的 plans。

    阶段：
      ① 快照复核（文件集合无增删、内容未被并发改动）——不符即终止，零写盘；
      ② staging：全部新内容先写成同目录排他临时文件（原文件此阶段分毫未动），
         任一失败即清理全部临时文件并终止；
      ③ 提交：逐个 os.replace + 立刻回读校验，任一失败即把**已替换的文件回滚成
         原字节**（回滚失败的会点名列出，供人工恢复）。
    """
    if not plans:
        return []
    _verify_unchanged(root, plans, expect)
    base = r_dir(root)
    staged = []
    try:
        for p in plans:
            staged.append((p, _make_temp(p["path"], p["new"], base)))
    except BaseException:
        for _, tmp in staged:
            _unlink(tmp)
        raise
    applied = []
    try:
        for p, tmp in staged:
            try:
                os.replace(str(tmp), str(p["path"]))
            except OSError as e:
                _fail("提交 %s 失败：%s" % (p["rel"], e))
            applied.append(p)                      # 先记账，任何后续失败都要回滚它
            if os.path.islink(str(p["path"])):
                _fail("%s 写入后变成符号链接，拒绝接受" % p["rel"])
            try:
                back = p["path"].read_bytes()
            except OSError as e:
                _fail("%s 写盘后回读失败：%s" % (p["rel"], e))
            if back != p["new"]:
                _fail("%s 写盘回读字节不一致（原子写失败？）" % p["rel"])
    except Exception as e:
        failed = _rollback(applied, base)
        msg = ("提交阶段失败（已回滚 %d/%d 个已替换文件）：%s"
               % (len(applied) - len(failed), len(applied), e))
        if failed:
            msg += "；以下文件回滚失败，需人工恢复：" + "；".join(
                "%s（%s）" % (rel, why) for rel, why in failed)
        else:
            msg += "；全部目标已恢复原字节，未留半写状态"
        raise HardeningError(msg) from e
    finally:
        for _, tmp in staged:
            _unlink(tmp)
    return applied


def apply_all(root, plans, expect=None) -> list:
    """apply 的批量入口（供 _run 与测试直接调用）。"""
    return commit_all(root, plans, expect=expect)


def apply_one(root, path) -> bytes:
    """单文件写盘（兼容入口），返回新字节；任何校验失败即抛 HardeningError（写盘前）。"""
    plan = prepare_one(root, path)
    commit_all(root, [plan])
    return plan["new"]


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
    if not s["files"]:
        if not getattr(args, "allow_empty", False):
            print("FAIL：%s 下 0 个 yaml——空输入一律判失败（否则是 vacuous pass："
                  "「0/0 判定模式全部显式」什么也没证明）；确为小型 fixture 场景"
                  "请显式加 --allow-empty" % r_dir(root))
            return EXIT_FAIL
        print("注意：--allow-empty 已启用，%s 是空目录，本次判定不覆盖任何题目" % r_dir(root))
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
        print("PASS：%d/%d 判定模式全部显式%s"
              % (len(s["explicit"]), len(s["files"]),
                 "（--allow-empty：空目录）" if not s["files"] else ""))
        return EXIT_OK

    if not args.apply:
        for f in s["todo"]:
            print("  [dry-run] 将补 %s → %s" % (MARK, _rel(f, root)))
        print("dry-run 结束（未写盘；加 --apply 落盘）")
        return EXIT_OK

    # ① 先全量生成 + 全部验证通过（本阶段零写盘；任一文件异常即整批终止）
    plans = prepare_all(root, s["todo"])
    # ② 再进入提交阶段：快照复核 → staging → 批量 os.replace → 回读；失败即回滚
    commit_all(root, plans, expect=s["snapshot"])
    written = len(plans)
    rest = scan(root)
    dist_after = collections.Counter(rest["explicit"].values())
    print("已写盘 = %d" % written)
    print("回读：已显式 = %d；仍待补 = %d" % (len(rest["explicit"]), len(rest["todo"])))
    problems = []
    for rel, why in rest["anomalies"]:
        problems.append("写盘后形态异常 %s：%s" % (rel, why))
    for f in rest["todo"]:
        problems.append("写盘后仍待补：%s" % _rel(f, root))
    if expected is not None and dict(dist_after) != expected:
        problems.append("写盘后 judge_mode 分布 %s != 期望 %s" % (dict(dist_after), expected))
    if problems:
        for why in problems:
            print("  [回读失败] %s" % why)
        failed = _rollback(plans, r_dir(root))
        print("FAIL：写盘后回读不达标，已回滚 %d/%d 个文件%s"
              % (len(plans) - len(failed), len(plans),
                 "；以下文件回滚失败，需人工恢复：" + "；".join(
                     "%s（%s）" % (rel, why) for rel, why in failed) if failed else ""))
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
    ap.add_argument("--allow-empty", action="store_true", dest="allow_empty",
                    help="允许 content/r 下 0 个 yaml（仅小型 fixture 场景；默认空输入判失败）")
    args = ap.parse_args(argv)
    try:
        return _run(args)
    except HardeningError as e:
        print("FAIL：%s" % e, file=sys.stderr)
        return EXIT_FAIL
    except (OSError, UnicodeError, yaml.YAMLError) as e:
        # 兜底：任何未被就地转成 HardeningError 的 IO/编码/解析异常也统一 FAIL + 非零退出
        print("FAIL：未预期的 IO/编码/解析异常（已按 fail-closed 处理）：%s" % e, file=sys.stderr)
        return EXIT_FAIL


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    sys.exit(main())
