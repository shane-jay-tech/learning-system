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

2026-09-20 复核加固（GPT 独立复核判「暂不建议销项」后按意见修复）：
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

2026-09-20 第二轮复核加固（GPT 复审 SCRIPT-001..004）：
  · 批量原子性：--apply 不再逐文件「生成+写盘」，改为两阶段——prepare_all 全量
    生成并验证（零写盘）→ commit 阶段先 staging 再逐个替换，任一失败即回滚；
  · 临时文件安全：tempfile.mkstemp(dir=path.parent) 的 O_EXCL 独占 fd + 写入前后
    校验 st_dev/st_ino 身份 + 拒绝符号链接目标；
  · 异常处理：scan/apply/commit 全程把 OSError/UnicodeError/yaml 异常统一转成
    HardeningError；提交前用「文件集合 + 逐文件 sha256 快照」复核并发改动；
  · 空输入：content/r 下 0 个 yaml 不再 vacuous pass，默认 FAIL。

2026-09-20 第三轮复核加固（GPT 复审判「不可销项」，用户拍板走「事务日志+启动恢复」
而非降级承诺；原意见 SCRIPT-001 崩溃安全 / SCRIPT-002 TOCTOU / 003 诊断 / 004 门禁）：
  · **WAL 事务日志**：每次 --apply 在 <root>/content/r/.judge_plain_txn/<txn>/ 下
    建事务，逐条**追加**写 journal.wal（每条写完即 fsync，不依赖 rename，无撕裂
    风险），记录 begin / temp / state(committing) / entry(applying|applied) /
    state(committed|rolled_back|rollback_failed)；
  · **旧内容备份**：提交前把每个目标的**事务前原始字节**写入 backups/（O_EXCL 独占
    创建 + fsync），begin 记录即隐含有可恢复的旧内容；
  · **启动恢复**：任何一次运行先扫描未完成事务——prepared（尚未替换）直接清理；
    committing（提交中被杀/掉电）**自动回滚到事务前字节**再继续；committed 只清
    残留；rollback_failed 保留事务目录并拒绝继续（--check/dry-run 一律只读不代恢复，
    必须显式 --recover）；
  · **os.replace 结果不确定**：在 replace **之前**先落 applying 记录（fsync 后才
    动手），因此「已完成但抛异常」的文件一定有账；恢复/回滚靠 sha256 三态判定
    （== 新内容 → 恢复；== 旧内容 → 无需动作；两者都不是 → 冲突，**拒绝覆盖**）；
  · **回滚不覆盖并发修改**：只回写「当前字节 == 本次新内容」的文件；备份先验
    sha256，损坏备份拒绝使用；回滚失败保留备份与事务目录供人工恢复（不再是只打印路径）；
  · **诊断**：临时文件清理失败不再静默吞掉，一律进入错误报告（含残留文件名清单）；
  · **门禁**：--allow-empty 必须同时给 --fixture（测试专用出口），单给一律拒绝；
  · **异常统一**：staging/备份/journal/回读各边界一律转 HardeningError，非 CLI 路径
    调用内部接口也拿不到裸 OSError。

承诺边界（第三轮 P0-1 + 第四轮 P0-3/P2-1 校准后的版本，逐条可被代码与测试核对）：
  ✅ 在「WAL、备份、目标文件都可读，且没有检测到无法判定的外部修改」的前提下，下一次
     运行（或显式 --recover）会把事务收敛成「全做完」或「全没做」；
  ✅ 提交中途被杀（进程终止 / 容器被 kill / 解释器崩溃）留下的半写状态回滚到事务前字节；
  ✅ os.replace「实际成功却向调用方报错」也有账可查（替换前先落 applying 记录）；
  ✅ 回滚不覆盖并发修改；既非旧也非新的字节先存副本再恢复（状态明确时）或拒绝覆盖
     （崩溃后状态不明时）；回滚失败保留事务目录与旧内容备份供人工恢复；
  ✅ 清理失败（临时文件、事务目录、残留扫描）一律进入报告，不静默吞掉；
  ✅ 恢复阶段对日志做完整性与边界校验：begin 唯一、条目字段齐全、rel 不重复、目标路径
     必须落在 content/r 内、备份名不得含路径分隔符或 ..、committed 必须每个条目都有
     applied 且目标字节确实是本事务写入的新内容；任一项不通过即**保留事务目录并阻塞**。
  ⚠️ **不是无条件收敛**：日志损坏、备份缺失或校验和不符、条目状态不明且内容无法判定、
     上次回滚失败等情况下，脚本会**阻塞并保留现场**（连同恢复材料）等人工处理，
     不会自作主张继续或清理。
  ⚠️ **默认自动回滚的语义**：--apply 发现未完成事务时默认先回滚再继续；崩溃后若有人
     手工改过目标文件，改动内容既非旧也非新时会先存进冲突副本；若改动后恰好等于本事务
     要写入的新内容，则无法与事务自身的写入区分，会被一并回滚。--check 与 dry-run 是
     只读门禁，发现未完成事务一律拒绝并提示 --recover，不代用户恢复。
  ❌ **不承诺掉电下的「目录项持久化」**：文件内容在替换前已 fsync；POSIX 上会尽力对目录
     做 fsync（失败仅 best effort、不报错），**Windows 上不做等价的目录项 flush**——
     因此不保证 os.replace 之后目录项在掉电场景下的持久性。掉电后某次替换若未生效，
     恢复会把它当成未完成事务回滚，不会留下半写题目。
  ❌ **不承诺抵御恶意并发攻击者**：目录若可被不可信用户写入，「临时文件身份校验 →
     os.replace」之间理论上仍有 TOCTOU 窗口（Windows 无 renameat2 / 目录 fd 等价接口）。
     本脚本的安全模型是**可信目录所有者**，不是防恶意并发。
  ❌ 不承诺崩溃时正在写的那个临时文件一定被删掉：有「按内容 sha 匹配」的兜底扫描，
     扫不掉的一律在报告里点名，不做静默处理。

纪律：
  · 默认 dry-run，只打印计划；写盘必须显式 --apply；
  · 幂等：已有 judge_mode 的文件一律跳过，重复 --apply 零改动；
  · 逐文件回读断言：写盘前后 yaml 解析结果除 judge_mode 外必须完全相等，
    且行尾风格（LF/CRLF）保持原样；
  · 只读/只写 content/r/*/*.yaml 与 content/r/.judge_plain_txn/，零网络、零依赖。

用法：
  python scripts/mark_r_judge_plain.py                     # dry-run：列出待改文件
  python scripts/mark_r_judge_plain.py --apply             # 写盘（幂等、事务化、崩溃可恢复）
  python scripts/mark_r_judge_plain.py --check             # 校验是否已全部显式（不满足则 exit 1）
  python scripts/mark_r_judge_plain.py --recover           # 只做启动恢复（回滚未完成事务）后退出
  python scripts/mark_r_judge_plain.py --check --expect-distribution run=70,ai_open=14
  python scripts/mark_r_judge_plain.py --root <dir> --apply   # 对临时基线跑（测试用）
  python scripts/mark_r_judge_plain.py --root <dir> --check --allow-empty --fixture
"""
import argparse
import collections
import glob
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
import time
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

# 事务（WAL）相关常量
TXN_DIRNAME = ".judge_plain_txn"
JOURNAL_NAME = "journal.wal"
BACKUP_DIRNAME = "backups"
CONFLICT_DIRNAME = "conflict"      # 回滚时发现的「既非旧也非新」字节副本（绝不自动删）
RESERVED_TXN_NAMES = (BACKUP_DIRNAME, CONFLICT_DIRNAME)
TXN_VERSION = 1

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


def _unlink_report(path) -> "str | None":
    """删除失败时**返回**诊断（而不是静默吞掉），供调用方汇总进错误报告。"""
    try:
        os.unlink(str(path))
    except FileNotFoundError:
        return None
    except OSError as e:
        return "%s（%s）" % (path, e)
    return None


def _is_within(path, base) -> bool:
    try:
        Path(path).resolve().relative_to(Path(base).resolve())
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------- 路径与读取

def content_root(root) -> Path:
    return Path(root).resolve() / "content"


def r_dir(root) -> Path:
    return content_root(root) / "r"


def txn_root(root) -> Path:
    """事务目录：<root>/.judge_plain_txn/ ——**放在 content/r 之外**。

    第四轮 SCRIPT-010：放在题库目录里会被题库备份/打包/扫描工具当成内容资产
    （崩溃那一刻里面还带着**完整旧内容备份**），风险高于收益。放到仓库根目录的隐藏
    目录，与 content/ 彻底隔离；仓库里同时用 .gitignore 忽略它。
    r_files() 仍保留排除逻辑（对老路径遗留的事务目录也一并挡掉）。
    """
    return Path(root).resolve() / TXN_DIRNAME


def r_files(root):
    """<root>/content/r/*/*.yaml（排序保证可复现）；**排除事务目录**。"""
    base = txn_root(root)
    out = []
    for p in glob.glob(str(r_dir(root) / "*" / "*.yaml")):
        pp = Path(p)
        if (pp.parent == base) or _is_within(pp, base):
            continue          # 事务目录里的东西（备份/日志）绝不是题目
        out.append(pp)
    return sorted(out)


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
    HardeningError（第三轮 SCRIPT-003：内部接口也拿不到裸 OSError/解析异常），
    调用方整批终止（这就是「先全部生成并验证，再进入提交」的前提）。
    """
    path = Path(path)
    _assert_inside(path, r_dir(root))
    rel = _rel(path, root)
    try:
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
    except HardeningError:
        raise
    except (OSError, UnicodeError, yaml.YAMLError) as e:
        # 统一异常类型：非 CLI 调用内部接口时也不会漏出裸异常
        _fail("%s 生成提交计划时异常（%s）：%s" % (rel, type(e).__name__, e))
    return {"path": path, "rel": rel, "old": old, "new": new,
            "old_sha": _sha(old), "new_sha": _sha(new)}


def prepare_all(root, paths) -> list:
    """把**全部**目标文件生成为 (old, new) 并逐条验证通过；任一失败即上抛、零写盘。"""
    return [prepare_one(root, p) for p in paths]


# ---------------------------------------------------------------- 临时文件（安全）

def _assert_temp_identity(tmp: Path, st_fd, when: str) -> None:
    """临时名必须仍是「我们独占创建的那个普通文件」——否则拒绝（防 TOCTOU 换名）。"""
    try:
        st_name = os.lstat(str(tmp))
    except OSError as e:
        _fail("临时文件 %s 状态读取失败（%s）：%s" % (tmp, when, e))
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
    except BaseException as e:
        # 第四轮 SCRIPT-008：异常清理路径过去用 _unlink()（静默吞），临时文件删不掉时
        # 报告里只看到最初的写入错误，看不见"还留了个临时文件"——这里改成可报告。
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        why = _unlink_report(tmp) if tmp is not None else None
        if isinstance(e, HardeningError):
            if why:
                raise HardeningError("%s；另外临时文件清理失败，需人工删除：%s" % (e, why)) from e
            raise
        if isinstance(e, (OSError, UnicodeError, ValueError)):
            msg = "写临时文件失败（%s）：%s" % (path, e)
            if why:
                msg += "；另外临时文件清理失败，需人工删除：%s" % why
            _fail(msg)
        raise          # KeyboardInterrupt / SystemExit 等原样上抛，不包装


def _replace_bytes(path: Path, data: bytes, base=None) -> None:
    """排他临时文件 + os.replace 写单个文件的字节（回滚用），写后即回读比对。"""
    tmp = _make_temp(path, data, base)
    try:
        try:
            os.replace(str(tmp), str(path))
        except OSError as e:
            _unlink(tmp)
            _fail("写入 %s 失败：%s" % (path, e))
    except BaseException:
        _unlink(tmp)
        raise
    if os.path.islink(str(path)):
        _fail("%s 写入后变成符号链接，拒绝接受" % path)
    try:
        back = path.read_bytes()
    except OSError as e:
        _fail("%s 写入后回读失败：%s" % (path, e))
    if back != data:
        _fail("%s 写入后回读字节不一致（原子写失败？）" % path)


# ================================================================ 事务层（WAL）
# 设计要点（第三轮 GPT 复核 SCRIPT-001 的正面回应）：
#   1) 日志是**追加式**的（open "ab" + 每条 fsync），不做 rename —— 没有「日志本身
#      被撕裂」的问题；只可能丢一条尾部残行，而残行按 WAL 规则直接丢弃。
#      （也因此不占用 os.replace 这条通道，提交阶段用到的 os.replace 仍只有目标文件。）
#   2) 备份先落盘并 fsync，之后才写 begin 记录 —— 「存在 begin 记录」即蕴含
#      「旧内容已可恢复」。
#   3) 替换**之前**先写 entry(applying) 并 fsync；所以「os.replace 实际成功但向
#      调用方报错」这种结果不确定的情形一定留有账目，恢复时按 sha256 三态判定。
#   4) 回滚只覆盖「当前字节 == 本次写入的新内容」的文件；既非旧也非新 → 判为并发
#      修改，拒绝覆盖并点名。备份使用前先验 sha256。
#   5) 崩溃后第一次运行会先做启动恢复：prepared → 清理；committing → 回滚到事务前
#      字节；committed → 仅清残留。--check / dry-run 是只读门禁，不代用户恢复。

def _fsync_dir(path: Path) -> bool:
    """尽力 fsync 目录项。返回值只作记录，调用方不把它当失败。

    POSIX：打开目录 fd 后 fsync；失败仅 best effort（返回 False，不报错）。
    Windows：**不做等价的目录项 flush**（Python 路径下没有可移植且可靠的目录句柄方案），
    直接返回 False——因此本脚本不保证 os.replace 之后目录项的掉电持久性；文件内容本身
    仍在替换前已 fsync。（第四轮 P2-1：原措辞「Windows 不支持目录 fsync」过于绝对。）"""
    if os.name == "nt":
        return False
    try:
        fd = os.open(str(path), os.O_RDONLY)
    except OSError:
        return False
    try:
        os.fsync(fd)
        return True
    except OSError:
        return False
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


def _write_exclusive(path: Path, data: bytes) -> None:
    """O_EXCL 独占创建 + 写入 + fsync（备份文件用）。失败一律 HardeningError。"""
    fd = None
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0),
                     0o600)
        with os.fdopen(fd, "wb") as fh:
            fd = None
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
    except OSError as e:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        _fail("写事务备份失败（%s）：%s" % (path, e))


def _journal_append(journal: Path, record: dict) -> None:
    """追加一条日志并 fsync。追加式：不做 rename，就没有「日志被撕裂」的窗口。"""
    line = (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    try:
        with open(str(journal), "ab") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())
    except OSError as e:
        _fail("写事务日志失败（%s）：%s" % (journal, e))


def _read_records(journal: Path):
    """读 WAL；返回 (records, torn_tail, error)。尾部残行按 WAL 规则丢弃。"""
    try:
        raw = journal.read_bytes()
    except OSError as e:
        return None, False, "读取事务日志失败：%s" % e
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return None, False, "事务日志不是合法 UTF-8：%s" % e
    parts = text.split("\n")
    tail = parts.pop()                 # 最后一个片段：非空即为未写完的残行
    records = []
    for ln in parts:
        if not ln.strip():
            continue
        try:
            rec = json.loads(ln)
        except ValueError:
            return None, False, "事务日志中间存在非法记录（疑似损坏）：%r" % ln[:120]
        if not isinstance(rec, dict):
            return None, False, "事务日志记录不是对象：%r" % ln[:120]
        records.append(rec)
    return records, bool(tail.strip()), None


def _txn_state(records) -> str:
    """由记录推导事务状态：prepared / committing / committed / rolled_back / rollback_failed。"""
    state = "prepared"
    for rec in records:
        if rec.get("t") == "state":
            s = rec.get("state")
            if s in ("committing", "committed", "rolled_back", "rollback_failed"):
                state = s
    return state


def _validate_entry(e, root, txn_dir) -> "str | None":
    """校验单条 WAL 条目，返回问题描述或 None。

    第四轮 SCRIPT-006：恢复阶段过去直接信任日志里的 path/backup，日志一旦被截断、
    损坏或人工改过，恢复就可能读写 content/r 之外的路径。恢复材料本身是脚本信任
    边界的一部分——「防恶意攻击者」不在承诺内，但「损坏日志不得导致恢复越界」必须在。
    """
    rel, path, backup = e.get("rel"), e.get("path"), e.get("backup")
    if not rel or not path or not backup or not e.get("old_sha") or not e.get("new_sha"):
        return "条目字段缺失（rel/path/backup/old_sha/new_sha 必须齐全）：%r" % (rel or path)
    p = Path(str(path))
    if not p.is_absolute():
        return "目标路径不是绝对路径：%r" % path
    try:
        p.resolve().relative_to(r_dir(root).resolve())
    except ValueError:
        return "目标路径越界（不在 content/r 内）：%s" % path
    name = str(backup)
    if name != Path(name).name or "/" in name or "\\" in name or ".." in name:
        return "备份文件名不合法（不得含路径分隔符或 ..）：%r" % backup
    bdir = (txn_dir / BACKUP_DIRNAME).resolve()
    try:
        (bdir / name).resolve().relative_to(bdir)
    except ValueError:
        return "备份路径越界：%r" % backup
    return None


def _validate_committed(entries, records) -> "str | None":
    """校验「日志自称 committed」是否真的成立；返回问题描述或 None。

    第四轮 SCRIPT-005：恢复分支过去只看最后一条 state 记录就认 committed 并**直接删掉
    事务目录**（连同恢复材料）。日志被截断 / 选择性损坏 / 人工改过时，这一手会把
    「日志说已提交、实际只写了一半」的事务当成成功，既漏了迁移又丢了备份。
    判据：最后一条状态必须是 committed；每个 begin 条目都必须有配对的 applied；
    不得出现 begin 之外的 entry；目标文件当前字节必须确实是本事务写入的新内容。
    """
    states = [r.get("state") for r in records if r.get("t") == "state"]
    if not states or states[-1] != "committed":
        return "最后一条状态记录不是 committed（%r）" % (states[-1:] or None)
    got = {}
    for r in records:
        if r.get("t") == "entry":
            got[r.get("rel")] = r.get("state")
    known = {e.get("rel") for e in entries}
    missing = [e.get("rel") for e in entries if got.get(e.get("rel")) != "applied"]
    if missing:
        return "以下条目没有 applied 记录：%s" % missing[:5]
    unknown = [rel for rel in got if rel not in known]
    if unknown:
        return "存在不属于本事务的 entry 记录：%s" % sorted(unknown)[:5]
    for e in entries:
        try:
            raw = Path(e["path"]).read_bytes()
        except OSError as err:
            return "复核 %s 失败：%s" % (e.get("rel"), err)
        if _sha(raw) != e.get("new_sha"):
            return "%s 的当前字节并非本事务写入的新内容" % e.get("rel")
    return None


def _validate_entries(entries, root, txn_dir) -> "str | None":
    """整批条目校验：字段完整、路径不越界、rel 不重复。返回第一个问题或 None。"""
    seen = set()
    for e in entries:
        why = _validate_entry(e, root, txn_dir)
        if why:
            return why
        rel = e.get("rel")
        if rel in seen:
            return "同一条目 rel 重复出现：%r" % rel
        seen.add(rel)
    return None


def _entries_from_records(records) -> list:
    """从 begin 记录取条目定义，再用 entry 记录补状态（applying/applied）。"""
    begin = None
    for rec in records:
        if rec.get("t") == "begin":
            begin = rec
    if begin is None:
        return []
    out = []
    for e in begin.get("entries") or []:
        out.append({"rel": e.get("rel"), "path": e.get("path"),
                    "old_sha": e.get("old_sha"), "new_sha": e.get("new_sha"),
                    "backup": e.get("backup"), "state": None})
    by_rel = {e["rel"]: e for e in out}
    for rec in records:
        if rec.get("t") == "entry":
            e = by_rel.get(rec.get("rel"))
            if e is not None:
                e["state"] = rec.get("state")
    return out


def _tmps_from_records(records) -> list:
    """staging 临时文件的**完整路径**清单（恢复时据它清理残留）。

    只记名字是不够的：临时文件在目标同目录，不在事务目录里——曾经用 d.parent/name
    去删，结果回滚成功了却留下一堆 .tmp 残骸（有测试钉住）。
    """
    out = []
    for rec in records:
        if rec.get("t") != "temp":
            continue
        if rec.get("path"):
            out.append(rec["path"])
        elif rec.get("name"):
            out.append(rec["name"])
    return out


def _cleanup_recorded_temps(tmps) -> list:
    """按日志记录清理 staging 残留；返回删除失败的诊断（绝不静默吞）。"""
    out = []
    for tp in tmps:
        why = _unlink_report(tp)
        if why:
            out.append(why)
    return out


def _restore_entries(root, entries, txn_dir) -> dict:
    """把条目恢复成事务前字节。

    返回 {"failures": [(rel, why)], "saved": [(rel, 副本路径)],
          "restored": [rel], "untouched": [rel]}——分成「真的写回去了」与
    「进了替换但字节本来就没变」两类，报告里的分子分母据此计算，不再虚报。

    安全规则（第三轮 SCRIPT-001 第 3/4/5 条）：
      · 当前 sha == 旧 sha → 已经是原字节，跳过；
      · 当前 sha == 新 sha → 用备份恢复（备份先验 sha256，损坏即拒绝）；
      · 既非旧也非新 → 分两种情况区别对待（这是「不盲目覆盖」与「不留半写」的折中）：
          - 条目状态 applied（本事务确实写过这个文件）→ **先把这份字节存成冲突副本**，
            再按备份恢复——批量语义优先，但证据一定留痕，人工可复查；
          - 条目状态 applying（崩溃后状态不明，无法断定是不是本事务写的）→
            **拒绝覆盖**，保留事务目录等人工判断；
      · 回滚自身失败 → 保留事务目录（内含备份）供人工恢复，不再只是打印路径。
    """
    base = r_dir(root)
    failures, saved, restored, untouched = [], [], [], []
    for e in reversed(list(entries)):
        rel = e.get("rel")
        if not e.get("state"):            # 从未进入 applying → 从未被替换
            continue
        path = Path(e["path"]) if e.get("path") else None
        if path is None:
            failures.append((rel, "事务日志缺少目标路径"))
            continue
        try:
            cur = path.read_bytes()
        except OSError as err:
            failures.append((rel, "回滚前读取失败：%s" % err))
            continue
        cur_sha = _sha(cur)
        if cur_sha == e.get("old_sha"):
            untouched.append(rel)          # 已是事务前字节：本次并未真正改动它
            continue
        if cur_sha != e.get("new_sha"):
            if e.get("state") == "applied":
                copy = _save_conflict(root, rel, cur)
                if copy is None:
                    failures.append((rel, "内容既非事务前也非事务后，且冲突副本保存失败，拒绝覆盖"))
                    continue
                saved.append((rel, copy))
            else:
                failures.append((rel, "状态不明（applying）且内容既非事务前也非事务后，"
                                      "无法判断是否为本事务所写，拒绝覆盖"))
                continue
        backup = txn_dir / BACKUP_DIRNAME / str(e.get("backup") or "")
        try:
            old = backup.read_bytes()
        except OSError as err:
            failures.append((rel, "旧内容备份读取失败（%s）：%s" % (backup, err)))
            continue
        if _sha(old) != e.get("old_sha"):
            failures.append((rel, "旧内容备份校验和不符，拒绝用损坏备份恢复"))
            continue
        try:
            _replace_bytes(path, old, base)
        except (HardeningError, OSError) as err:
            failures.append((rel, str(err)))
            continue
        try:
            if path.read_bytes() != old:
                failures.append((rel, "回滚后字节仍不等于原字节"))
                continue
        except OSError as err:
            failures.append((rel, "回滚后回读失败：%s" % err))
            continue
        restored.append(rel)
    return {"failures": failures, "saved": saved,
            "restored": restored, "untouched": untouched}


class Txn(object):
    """一次批量提交的事务句柄。"""

    def __init__(self, root, txn_id, plans, base):
        self.root = Path(root)
        self.base = Path(base)
        self.txn_id = txn_id
        self.dir = txn_root(root) / txn_id
        self.journal = self.dir / JOURNAL_NAME
        self.plans = list(plans)
        self.backups = {}          # rel -> 备份文件名
        self.temps = {}            # rel -> 临时文件路径
        self.states = {}           # rel -> applying | applied
        self.written = []          # 确认已替换的 plan（= 旧实现的 applied）
        self.touched = []          # 已进入 applying 的 plan（含 os.replace 结果不确定的）
        self.residue = []          # 清理失败留下的残留（诊断用，绝不静默吞）
        self.conflict_saved = []   # 回滚时保存的冲突副本 [(rel, 路径)]
        self.restored = []         # 回滚时真正写回旧字节的文件
        self.untouched = []        # 进入过替换但字节始终未变的文件

    # ---------------------------------------------------------- 建立
    @classmethod
    def create(cls, root, plans):
        txn_id = "%s-%d" % (time.strftime("%Y%m%dT%H%M%S", time.localtime()), os.getpid())
        d = txn_root(root) / txn_id
        try:
            (d / BACKUP_DIRNAME).mkdir(parents=True, exist_ok=False)
        except OSError as e:
            _fail("创建事务目录失败（%s）：%s" % (d, e))
        tx = cls(root, txn_id, plans, r_dir(root))
        try:
            tx._write_backups()
            _journal_append(tx.journal, {
                "t": "begin", "v": TXN_VERSION, "txn": txn_id,
                "root": str(Path(root).resolve()),
                "created": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
                "pid": os.getpid(),
                "entries": [{"rel": p["rel"], "path": str(p["path"]),
                             "old_sha": p["old_sha"], "new_sha": p["new_sha"],
                             "backup": tx.backups[p["rel"]]} for p in plans],
            })
            _fsync_dir(tx.dir)
            _fsync_dir(txn_root(root))
        except BaseException:
            tx._drop_dir()
            raise
        return tx

    def _write_backups(self):
        bdir = self.dir / BACKUP_DIRNAME
        for i, p in enumerate(self.plans):
            name = "%04d-%s.bin" % (i, p["old_sha"][:16])
            _write_exclusive(bdir / name, p["old"])
            self.backups[p["rel"]] = name

    # ---------------------------------------------------------- staging
    def stage(self):
        """把全部新内容写成目标同目录的排他临时文件（原文件此阶段分毫未动）。"""
        try:
            for p in self.plans:
                tmp = _make_temp(p["path"], p["new"], self.base)
                self.temps[p["rel"]] = tmp
                _journal_append(self.journal,
                                {"t": "temp", "rel": p["rel"], "name": tmp.name,
                                 "path": str(tmp)})
        except BaseException:
            self.abort_prepared()
            raise

    def abort_prepared(self):
        """staging 阶段失败：清临时文件 + 清事务目录（state 仍是 prepared，零改动）。"""
        self.residue.extend(self._cleanup_temps())
        self._drop_dir()

    # ---------------------------------------------------------- 提交
    def commit(self):
        _journal_append(self.journal, {"t": "state", "state": "committing"})
        _fsync_dir(self.dir)
        for p in self.plans:
            rel = p["rel"]
            # 先记账（fsync）再动手：os.replace 结果不确定时也一定有账
            _journal_append(self.journal, {"t": "entry", "rel": rel, "state": "applying"})
            self.states[rel] = "applying"
            self.touched.append(p)
            tmp = self.temps[rel]
            try:
                os.replace(str(tmp), str(p["path"]))
            except OSError as e:
                _fail("提交 %s 失败：%s" % (rel, e))
            self.temps.pop(rel, None)
            self.written.append(p)
            _fsync_dir(p["path"].parent)
            _journal_append(self.journal, {"t": "entry", "rel": rel, "state": "applied"})
            self.states[rel] = "applied"
            if os.path.islink(str(p["path"])):
                _fail("%s 写入后变成符号链接，拒绝接受" % rel)
            try:
                back = p["path"].read_bytes()
            except OSError as e:
                _fail("%s 写盘后回读失败：%s" % (rel, e))
            if back != p["new"]:
                _fail("%s 写盘回读字节不一致（原子写失败？）" % rel)
        _journal_append(self.journal, {"t": "state", "state": "committed"})
        _fsync_dir(self.dir)

    # ---------------------------------------------------------- 终结
    def entry_views(self) -> list:
        return [{"rel": p["rel"], "path": str(p["path"]), "old_sha": p["old_sha"],
                 "new_sha": p["new_sha"], "backup": self.backups.get(p["rel"]),
                 "state": self.states.get(p["rel"])} for p in self.plans]

    def rollback(self) -> list:
        """回滚到事务前字节；返回失败清单。全部成功即连同事务目录一起清理。"""
        res = _restore_entries(self.root, self.entry_views(), self.dir)
        failures, saved = res["failures"], res["saved"]
        self.conflict_saved, self.restored, self.untouched = saved, res["restored"], res["untouched"]
        if failures:
            _journal_append(self.journal, {
                "t": "state", "state": "rollback_failed",
                "failures": [{"rel": r, "why": w} for r, w in failures]})
            _fsync_dir(self.dir)
            # 保留事务目录：里面有旧内容备份，是人工恢复的材料
        else:
            _journal_append(self.journal, {"t": "state", "state": "rolled_back"})
            self.residue.extend(self._cleanup_temps())
            self._drop_dir()
        return failures

    def finalize(self) -> list:
        """提交成功：清理临时文件与事务目录，返回已替换的 plans。"""
        self.residue.extend(self._cleanup_temps())
        self._drop_dir()
        return self.written

    # ---------------------------------------------------------- 内部
    def _cleanup_temps(self) -> list:
        """删掉还没被 os.replace 消费的临时文件；失败**返回**诊断而不是吞掉。"""
        out = []
        for rel, tmp in list(self.temps.items()):
            why = _unlink_report(tmp)
            if why:
                out.append(why)
            self.temps.pop(rel, None)
        return out

    def _drop_dir(self):
        """删除事务目录（含备份与日志）；失败把残留记进 self.residue。"""
        why = _rmtree_report(self.dir)
        if why:
            self.residue.append(why)
        troot = txn_root(self.root)
        try:
            if troot.is_dir() and not any(troot.iterdir()):
                os.rmdir(str(troot))
        except OSError as e:
            self.residue.append("事务根目录清理失败（%s）：%s" % (troot, e))


class _EmptyTxn(object):
    """零计划的空事务（幂等重复 apply 走的路径）。"""

    dir = None
    written = []
    touched = []
    residue = []

    def finalize(self):
        return []

    def rollback(self):
        return []


def _rmtree_report(path) -> "str | None":
    if path is None:
        return None
    try:
        shutil.rmtree(str(path))
    except FileNotFoundError:
        return None
    except OSError as e:
        return "事务目录清理失败（%s）：%s" % (path, e)
    return None


def _save_conflict(root, rel: str, data: bytes) -> "str | None":
    """把「既非事务前也非事务后」的字节存一份副本（人工恢复材料）。

    这是第三轮 SCRIPT-001 第 5 条的落点：回滚时若发现目标内容与预期都不符，
    既不盲目覆盖、也不直接丢弃——先留证据，再恢复。副本放在
    <root>/content/r/.judge_plain_txn/conflict/ 下，**不会被自动清理**。
    """
    d = txn_root(root) / CONFLICT_DIRNAME
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    name = "%s-%s.bin" % (rel.replace("/", "_").replace("\\", "_"), _sha(data)[:12])
    p = d / name
    try:
        if not p.exists():
            _write_exclusive(p, data)
    except HardeningError:
        return None
    return str(p)


def _sweep_staged_temps(entries) -> list:
    """扫出「已创建但 temp 记录还没写就崩了」的暂存文件并删除。

    判据必须硬：候选文件形如 <目标名>.*.tmp，且**内容 sha256 == 该条目的新内容**
    ——满足这两条才可能只是我们的 staging 产物，绝不误删别人的文件。
    """
    out = []
    for e in entries:
        tgt = Path(e["path"]) if e.get("path") else None
        new_sha = e.get("new_sha")
        if tgt is None or not new_sha:
            continue
        try:
            cands = sorted(tgt.parent.glob(tgt.name + ".*.tmp"))
        except OSError:
            continue
        for c in cands:
            try:
                if c.is_file() and _sha(c.read_bytes()) == new_sha:
                    why = _unlink_report(c)
                    if why:
                        out.append(why)
            except OSError:
                continue
    return out


def find_pending_txns(root) -> list:
    """未完成事务（有日志的事务目录）。"""
    d = txn_root(root)
    if not d.is_dir():
        return []
    try:
        return sorted(p for p in d.iterdir()
                      if p.is_dir() and p.name not in RESERVED_TXN_NAMES
                      and (p / JOURNAL_NAME).is_file())
    except OSError:
        return []


def find_debris(root) -> list:
    """没有日志的事务目录残留（create 中途失败留下），原文件必然未被改动。"""
    d = txn_root(root)
    if not d.is_dir():
        return []
    try:
        return sorted(p for p in d.iterdir()
                      if p.is_dir() and p.name not in RESERVED_TXN_NAMES
                      and not (p / JOURNAL_NAME).is_file())
    except OSError:
        return []


def _scan_residue(root) -> tuple:
    """content/r 下遗留的 *.tmp（staging 残留）清单——诊断用。

    返回 (残留清单, 扫描错误或 None)。第四轮 SCRIPT-003：过去扫描失败被静默吞掉，
    调用方无法区分「没有残留」与「根本扫不动」——这正是诊断能力的关键差别。
    """
    out, err, base = [], None, r_dir(root)
    try:
        first = list(os.scandir(str(base)))
    except OSError as e:
        return [], "残留扫描失败（%s）：%s" % (base, e)
    tbase = txn_root(root)

    def walk(d, entries):
        nonlocal err
        for entry in entries:
            try:
                if entry.is_dir(follow_symlinks=False):
                    try:
                        walk(Path(entry.path), list(os.scandir(entry.path)))
                    except OSError as e:
                        err = "残留扫描中途失败（%s）：%s" % (entry.path, e)
                elif entry.name.endswith(".tmp") and not _is_within(entry.path, tbase):
                    out.append(entry.path)
            except OSError as e:
                err = "残留扫描中途失败（%s）：%s" % (entry.path, e)

    # 注意：这里刻意自己走目录而不用 Path.rglob —— pathlib 的 glob 会**静默吞掉**
    # OSError（读不了的目录直接跳过），于是「扫不动」和「没有残留」分不出来，
    # 正是第四轮 SCRIPT-003 指出的诊断缺陷。自己走才能把失败如实报出来。
    walk(base, first)
    return sorted(out), err


def recover_pending(root) -> dict:
    """启动恢复：把未完成事务收敛到确定状态。

    返回 {"recovered": [(txn, 做了什么)], "blocked": [(txn, 为什么)], "debris": [...]}。
    """
    recovered, blocked, debris = [], [], []
    for d in find_debris(root):
        why = _rmtree_report(d)
        if why:
            blocked.append((d.name, why))
        else:
            debris.append(d.name)
    for d in find_pending_txns(root):
        records, torn, err = _read_records(d / JOURNAL_NAME)
        if err:
            blocked.append((d.name, "%s（事务目录已保留，请人工核对）" % err))
            continue
        begins = [r for r in records if r.get("t") == "begin"]
        if len(begins) != 1:
            blocked.append((d.name, "begin 记录数 = %d（应恰 1 条），日志不可信；"
                            "事务目录已保留在 %s" % (len(begins), d)))
            continue
        state = _txn_state(records)
        entries = _entries_from_records(records)
        tmps = _tmps_from_records(records)
        bad = _validate_entries(entries, root, d)
        if bad:
            blocked.append((d.name, "日志条目校验不通过（%s）；事务目录已保留在 %s" % (bad, d)))
            continue
        if state == "rollback_failed":
            blocked.append((d.name, "上次回滚失败，事务目录保留在 %s（内含旧内容备份）" % d))
            continue
        if state == "committing" and not entries:
            blocked.append((d.name, "日志缺少 begin 条目定义，无法自动恢复"))
            continue
        if state == "committed":
            bad = _validate_committed(entries, records)
            if bad:
                blocked.append((d.name, "日志自称已提交但完整性校验不通过（%s）；"
                                "事务目录已保留在 %s，未按成功处理" % (bad, d)))
                continue
        if state in ("prepared", "committed", "rolled_back"):
            residue = _cleanup_recorded_temps(tmps) + _sweep_staged_temps(entries)
            why = _rmtree_report(d)
            if why:
                blocked.append((d.name, why))
            else:
                note = ("状态 %s：未留半写内容，已清理事务目录%s"
                        % (state, "（尾行残记录已按 WAL 规则丢弃）" if torn else ""))
                if residue:
                    note += "；但有临时文件删不掉，需人工删除：%s" % "；".join(residue)
                recovered.append((d.name, note))
            continue
        # committing：真正需要回滚的半写状态
        res = _restore_entries(root, entries, d)
        failures, saved = res["failures"], res["saved"]
        if failures:
            _journal_append(d / JOURNAL_NAME, {
                "t": "state", "state": "rollback_failed",
                "failures": [{"rel": r, "why": w} for r, w in failures]})
            blocked.append((d.name, "回滚失败，事务目录保留在 %s（内含旧内容备份）：%s"
                            % (d, "；".join("%s（%s）" % (r, w) for r, w in failures))))
            continue
        residue = _cleanup_recorded_temps(tmps) + _sweep_staged_temps(entries)
        _journal_append(d / JOURNAL_NAME, {"t": "state", "state": "rolled_back"})
        why = _rmtree_report(d)
        if why:
            blocked.append((d.name, why))
        else:
            note = "提交中途终止 → 已回滚 %d 个文件到事务前字节" % len(res["restored"])
            if residue:
                note += "；有临时文件删不掉，需人工删除：%s" % "；".join(residue)
            if saved:
                note += "；%d 个文件回滚前内容与预期都不符，副本已存 %s" % (
                    len(saved), txn_root(root) / CONFLICT_DIRNAME)
            recovered.append((d.name, note))
    # 收尾：事务根目录空了就一并删掉（conflict/ 里还有副本时会保留，不会被误删）
    troot = txn_root(root)
    try:
        if troot.is_dir() and not any(troot.iterdir()):
            os.rmdir(str(troot))
    except OSError as e:
        blocked.append((troot.name, "事务根目录清理失败（%s）：%s" % (troot, e)))
    return {"recovered": recovered, "blocked": blocked, "debris": debris}


def _print_recovery(rec) -> None:
    for tid, what in rec["recovered"]:
        print("  [恢复] %s：%s" % (tid, what))
    for tid in rec["debris"]:
        print("  [清理] %s：无日志残留（原文件未被改动）" % tid)
    for tid, why in rec["blocked"]:
        print("  [阻塞] %s：%s" % (tid, why))


# ---------------------------------------------------------------- 提交（事务化）

def _verify_unchanged(root, plans, expect) -> None:
    """提交前复核：文件集合无增删、目标字节 == 准备时、其他文件内容未被改动。

    任何一项不符即 HardeningError → 整批终止、**一个字节都不写**（此检查在建立
    事务之前，因此不会留下事务目录）。
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


def begin_commit(root, plans, expect=None):
    """建立事务 + staging + 提交（失败即回滚）；成功返回仍**未 finalize** 的 Txn。

    调用方拿到 Txn 后应做写盘后回读校验：不达标 → tx.rollback()；达标 → tx.finalize()。
    """
    if not plans:
        return _EmptyTxn()
    _verify_unchanged(root, plans, expect)
    tx = Txn.create(root, plans)
    try:
        tx.stage()
    except BaseException as e:
        if tx.residue:
            _fail("%s；另外临时文件清理失败，需人工删除：%s" % (e, "；".join(tx.residue)))
        raise
    try:
        tx.commit()
    except BaseException as e:
        failed = tx.rollback()
        # 分子分母都按「真的需要还原的文件」算：os.replace「实际成功但抛异常」时
        # written 还没记上（用它会算出「已回滚 -1/0」）；而只是进了 applying 却没被
        # 改动的文件也不该记功（用 touched 会把没动的文件也算成回滚成功）。
        need = len(tx.restored) + len(failed)
        if need:
            msg = ("提交阶段失败（已回滚 %d/%d 个需还原的文件）：%s"
                   % (len(tx.restored), need, e))
        else:
            msg = "提交阶段失败（没有任何文件实际被改动）：%s" % e
        if tx.untouched:
            msg += "；另有 %d 个曾进入替换但字节未变" % len(tx.untouched)
        if failed:
            msg += "；以下文件回滚失败，需人工恢复：" + "；".join(
                "%s（%s）" % (rel, why) for rel, why in failed)
            msg += "；事务目录已保留（%s），内含事务前原始字节备份" % tx.dir
        else:
            msg += "；全部目标已恢复原字节，未留半写状态"
        if tx.conflict_saved:
            msg += "；%d 个目标回滚前的内容既非旧也非新，已存副本供复查：%s" % (
                len(tx.conflict_saved), "；".join(p for _, p in tx.conflict_saved))
        if tx.residue:
            msg += "；临时文件清理失败，需人工删除：%s" % "；".join(tx.residue)
        raise HardeningError(msg) from e
    return tx


def commit_all(root, plans, expect=None) -> list:
    """兼容入口：提交并在成功时立即终结事务；返回已替换的 plans。"""
    tx = begin_commit(root, plans, expect=expect)
    return tx.finalize()


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

    # ---- 启动恢复（第三轮 SCRIPT-001：崩溃后不留不确定状态）
    pending = find_pending_txns(root)
    if pending and not args.recover:
        if (not args.apply) or args.no_auto_recover:
            print("检测到 %d 个未完成事务（上次运行中途终止）：" % len(pending))
            for d in pending:
                print("  [未完成] %s" % d.name)
            print("FAIL：本仓库处于未完成事务状态，先跑 --recover 恢复（回滚到事务前字节）再继续；"
                  "--check / dry-run 是只读门禁，不代你恢复。")
            return EXIT_FAIL
    if pending and (args.recover or args.apply):
        rec = recover_pending(root)
        _print_recovery(rec)
        if rec["blocked"]:
            print("FAIL：存在无法自动恢复的事务，需人工处理（上面已点名，备份保留在事务目录内）")
            return EXIT_FAIL
        if args.recover:
            return EXIT_OK
    elif args.recover:
        debris = find_debris(root)
        if debris:
            rec = recover_pending(root)
            _print_recovery(rec)
        print("没有未完成事务，无需恢复。")
        return EXIT_OK

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
                  "请同时加 --allow-empty --fixture" % r_dir(root))
            return EXIT_FAIL
        if not getattr(args, "fixture", False):
            print("FAIL：--allow-empty 必须与 --fixture 同时给出（第三轮 SCRIPT-004："
                  "单给 --allow-empty 等于给生产门禁留了一个空跑成功的逃生门）")
            return EXIT_FAIL
        print("注意：--allow-empty --fixture 已启用（测试专用出口），%s 是空目录，"
              "本次判定不覆盖任何题目" % r_dir(root))
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
                 "（--allow-empty --fixture：空目录）" if not s["files"] else ""))
        return EXIT_OK

    if not args.apply:
        for f in s["todo"]:
            print("  [dry-run] 将补 %s → %s" % (MARK, _rel(f, root)))
        print("dry-run 结束（未写盘；加 --apply 落盘）")
        return EXIT_OK

    # ① 先全量生成 + 全部验证通过（本阶段零写盘；任一文件异常即整批终止）
    plans = prepare_all(root, s["todo"])
    # ② 建事务（备份 + WAL）→ staging → 提交；崩溃可恢复，失败即回滚
    tx = begin_commit(root, plans, expect=s["snapshot"])
    if tx.dir is not None:
        print("事务 = %s（日志 %s）" % (tx.txn_id, tx.dir))
    written = len(tx.written)
    # ③ 写盘后回读校验：不达标 → 回滚；达标 → 终结并清理事务目录
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
        failed = tx.rollback()
        need = len(tx.restored) + len(failed)
        msg = ("FAIL：写盘后回读不达标，已回滚 %d/%d 个需还原的文件"
               % (len(tx.restored), need))
        if failed:
            msg += "；以下文件回滚失败，需人工恢复：" + "；".join(
                "%s（%s）" % (rel, why) for rel, why in failed)
            msg += "；事务目录已保留（%s），内含事务前原始字节备份" % tx.dir
        if tx.conflict_saved:
            msg += "；%d 个目标回滚前的内容既非旧也非新，已存副本供复查：%s" % (
                len(tx.conflict_saved), "；".join(p for _, p in tx.conflict_saved))
        if tx.residue:
            msg += "；临时文件清理失败，需人工删除：%s" % "；".join(tx.residue)
        print(msg)
        return EXIT_FAIL
    tx.finalize()
    if tx.residue:
        print("  [残留] 临时文件清理失败，需人工删除：%s" % "；".join(tx.residue))
    leftover, scan_err = _scan_residue(root)
    if scan_err:
        print("  [残留] %s" % scan_err)
    if leftover:
        print("  [残留] content/r 下仍有 %d 个 *.tmp：%s" % (len(leftover), "；".join(leftover[:5])))
    print("PASS：写盘完成且回读一致（事务已提交并清理；幂等：再跑 --apply 将零改动）")
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
                    help="允许 content/r 下 0 个 yaml（**必须同时给 --fixture**，测试专用）")
    ap.add_argument("--fixture", action="store_true",
                    help="声明本次对合成测试基线运行；--allow-empty 的强制同伴（生产门禁不得使用）")
    ap.add_argument("--recover", action="store_true",
                    help="只做启动恢复（回滚未完成事务）后退出")
    ap.add_argument("--no-auto-recover", action="store_true", dest="no_auto_recover",
                    help="--apply 时若发现未完成事务则拒绝继续（默认自动回滚后继续）")
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
