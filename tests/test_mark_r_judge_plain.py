# -*- coding: utf-8 -*-
"""scripts/mark_r_judge_plain.py 的加固验证（D6 复核修复，2026-09-20）。

复核意见（GPT 干净版）：迁移脚本的防护用了 assert，而 python -O 会把 assert 整个
剥离；缺「重复执行 / 异常输入 / 只允许插入一行」的字节级证明。要求：
  · 去掉对 assert 的安全依赖 → 显式校验 + 非零退出；
  · dry-run / apply / 重复 apply / check 的端到端测试；
  · 字节级差分测试（新文件 == 原文 + 恰一行）。

本文件的验证分三层：
  ① 端到端（真子进程，--root 指临时基线）：dry-run 零写盘、apply 恰插一行、
     重复 apply 零改动、check 未完成 exit 1 / 完成后 exit 0、分布门禁；
  ② fail-closed：无 tags / 空输出 / 坏 yaml / 非法模式值 / 空 judge_mode 行
     等异常输入一律非零退出且**一个字节都不写**（连同一批的合法文件也不写）；
  ③ 字节级差分：真题库 84 行逐行「删掉再插回」，必须与原字节完全相等，
     且长度差 == 该行字节数 + 一个换行——即「新文件 == 原文 + 恰一行」。
     另用 -O 跑一遍异常输入，证明 assert 剥离后防护仍在；
  ④ 批量原子性 / 临时文件安全 / 空输入（第二轮复核 SCRIPT-001..004）：
     · 第二个文件写盘失败（真机只读属性 → os.replace WinError 5）时**第一个文件
       必须回滚成原字节**，不留半写状态、不留临时文件残留；
     · 第二个文件被并发篡改 → 整批终止、零提交；
     · 写盘后回读不达标 → 整批回滚；staging 阶段失败 → 原文件分毫未动；
     · 固定名临时文件抢占攻击（旧实现 <file>.tmp<PID>）已失效；
       mkstemp 返回后被换成符号链接/硬链接（TOCTOU）→ 拒绝且外部文件零改动；
     · scan 里的 OSError（*.yaml 是目录）与顶层 IO 异常 → 统一 FAIL 非零、零写盘；
     · content/r 为空 → 不再 vacuous pass，默认 FAIL，--allow-empty 才放行。
"""
import hashlib
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

from scripts import mark_r_judge_plain as mrj

SCRIPT = str(Path("scripts") / "mark_r_judge_plain.py")
MARK_LINE = "judge_mode: run"

RUN_MISSING = (
    'title: "缺 judge_mode 的普通题"\n'
    'topic: "t1"\n'
    'difficulty: 2\n'
    'tags: ["io", "starter"]\n'
    'statement: |\n'
    '  请输出 Hello\n'
    'starter_code: |\n'
    '  # 写代码\n'
    'expected_output: |\n'
    '  Hello\n'
    'hints:\n'
    '  - "用 cat"\n'
)
RUN_EXPLICIT = RUN_MISSING.replace('tags: ["io", "starter"]\n',
                                   'tags: ["io", "starter"]\n' + MARK_LINE + '\n')
RUN_MISSING_CRLF = RUN_MISSING.replace("\n", "\r\n")
AI_OPEN = (
    'title: "开放题"\n'
    'topic: "t1"\n'
    'difficulty: 3\n'
    'tags: ["open"]\n'
    'judge_mode: ai_open\n'
    'statement: |\n'
    '  解释一下\n'
    'starter_code: |\n'
    '  # 写回答\n'
    'rubric:\n'
    '  - "要点一"\n'
)
BLOCK_TAGS = (
    'title: "块状 tags"\n'
    'topic: "t1"\n'
    'difficulty: 1\n'
    'tags:\n'
    '  - "a"\n'
    '  - "b"\n'
    'statement: |\n'
    '  x\n'
    'starter_code: |\n'
    '  y\n'
    'expected_output: |\n'
    '  1\n'
)
BAD_NO_TAGS = (
    'title: "没有 tags 行"\n'
    'topic: "t1"\n'
    'difficulty: 1\n'
    'statement: |\n  x\n'
    'expected_output: |\n  1\n'
)
BAD_EMPTY_OUTPUT = (
    'title: "空期望输出"\n'
    'topic: "t1"\n'
    'difficulty: 1\n'
    'tags: ["t"]\n'
    'statement: |\n  x\n'
    'expected_output: ""\n'
)
BAD_YAML = 'title: "坏 yaml"\ntags: [未闭合\n'
BAD_MODE = (
    'title: "非法模式值"\n'
    'topic: "t1"\n'
    'difficulty: 1\n'
    'tags: ["t"]\n'
    'judge_mode: manual\n'
    'statement: |\n  x\n'
    'expected_output: |\n  1\n'
)
BAD_INDENT_AFTER_TAGS = (
    'title: "tags 之后是缩进续行"\n'
    'topic: "t1"\n'
    'difficulty: 1\n'
    'tags:\n'
    '  - "a"\n'
    'statement: |\n'
    '  x\n'
    'expected_output: |\n'
    '  1\n'
).replace('  - "a"\n', '  - "a"\n   不缩进的续行\n')


# ------------------------------------------------------------------ 工具

def _write(path: Path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8")) if isinstance(text, str) else path.write_bytes(text)


def _corpus(root, files):
    base = Path(root) / "content" / "r"
    for rel, text in files.items():
        _write(base / rel, text)
    return base


def _snapshot(base: Path):
    return {str(p.relative_to(base)).replace("\\", "/"): p.read_bytes()
            for p in sorted(base.rglob("*")) if p.is_file()}


def _cli(root, *args, py_flags=()):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, *py_flags, SCRIPT, "--root", str(root), *args],
        capture_output=True, text=True, encoding="utf-8", env=env,
        cwd=str(Path.cwd()))


def _expected_after_insert(raw: bytes, line: str = MARK_LINE) -> bytes:
    """独立实现（不调被测函数）：在顶层 tags 行后插入一行。"""
    text = raw.decode("utf-8")
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    idx = next(i for i, l in enumerate(lines) if l.startswith("tags:"))
    return ("".join(lines[:idx + 1]) + line + eol + "".join(lines[idx + 1:])).encode("utf-8")


GOOD_CORPUS = {
    "t1/01_missing.yaml": RUN_MISSING,
    "t1/02_explicit.yaml": RUN_EXPLICIT,
    "t1/03_open.yaml": AI_OPEN,
    "t1/04_crlf.yaml": RUN_MISSING_CRLF,
}


def _good_corpus(tmp_path):
    base = _corpus(tmp_path, GOOD_CORPUS)
    return base, _snapshot(base)


# ------------------------------------------------------------------ ① 端到端

def test_端到端_dry_run_零写盘(tmp_path):
    base, before = _good_corpus(tmp_path)
    r = _cli(tmp_path)
    assert r.returncode == 0, r.stderr
    assert "dry-run" in r.stdout and "将补" in r.stdout
    assert _snapshot(base) == before, "dry-run 竟然改动了文件"
    assert "待补 judge_mode = 2" in r.stdout


def test_端到端_apply_字节级恰插一行_且零意外改动(tmp_path):
    base, before = _good_corpus(tmp_path)
    r = _cli(tmp_path, "--apply", "--expect-distribution", "run=3,ai_open=1")
    assert r.returncode == 0, r.stderr + r.stdout
    assert "已写盘 = 2" in r.stdout and "PASS" in r.stdout
    after = _snapshot(base)
    assert set(after) == set(before), "文件集合被改动"

    changed = [k for k in before if after[k] != before[k]]
    assert changed == ["t1/01_missing.yaml", "t1/04_crlf.yaml"], changed
    for rel in changed:
        old, new = before[rel], after[rel]
        assert new == _expected_after_insert(old), "%s 的插入结果与独立实现不一致" % rel
        eol = b"\r\n" if b"\r\n" in old else b"\n"
        assert len(new) - len(old) == len(MARK_LINE.encode("utf-8")) + len(eol), (
            "%s 不是「原文 + 恰一行」" % rel)
        assert new.count(eol) == old.count(eol) + 1
        # 题干/答案字段零改动（yaml 解析层再证一次）
        d_old, d_new = yaml.safe_load(old), yaml.safe_load(new)
        assert d_new.pop("judge_mode") == "run"
        assert d_new == d_old
    # CRLF 文件的换行风格必须原样保留
    assert b"\r\n" in after["t1/04_crlf.yaml"]
    # 已显式 / ai_open 的两个文件一个字节都不许动
    for rel in ("t1/02_explicit.yaml", "t1/03_open.yaml"):
        assert after[rel] == before[rel], "%s 被误改" % rel


def test_端到端_重复apply零改动(tmp_path):
    base, _ = _good_corpus(tmp_path)
    first = _cli(tmp_path, "--apply")
    assert first.returncode == 0, first.stderr
    mid = _snapshot(base)
    second = _cli(tmp_path, "--apply")
    assert second.returncode == 0, second.stderr
    assert "已写盘 = 0" in second.stdout
    assert _snapshot(base) == mid, "重复 apply 不是零改动（幂等被破坏）"
    third = _cli(tmp_path, "--apply", "--expect-distribution", "run=3,ai_open=1")
    assert third.returncode == 0 and _snapshot(base) == mid


def test_端到端_check_未完成exit1_完成后exit0(tmp_path):
    base, before = _good_corpus(tmp_path)
    r1 = _cli(tmp_path, "--check")
    assert r1.returncode == 1
    assert "FAIL" in r1.stdout and "[缺]" in r1.stdout
    assert _snapshot(base) == before, "--check 不该写盘"
    assert _cli(tmp_path, "--apply").returncode == 0
    r2 = _cli(tmp_path, "--check")
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "PASS：4/4 判定模式全部显式" in r2.stdout


def test_端到端_check_分布门禁不符即exit1(tmp_path):
    _good_corpus(tmp_path)
    assert _cli(tmp_path, "--apply").returncode == 0
    ok = _cli(tmp_path, "--check", "--expect-distribution", "run=3,ai_open=1")
    assert ok.returncode == 0, ok.stdout
    bad = _cli(tmp_path, "--check", "--expect-distribution", "run=4,ai_open=0")
    assert bad.returncode == 1
    assert "分布" in bad.stdout
    bad_spec = _cli(tmp_path, "--check", "--expect-distribution", "run=x")
    assert bad_spec.returncode == 1 and "计数不是整数" in bad_spec.stderr


# ------------------------------------------------------------------ ② fail-closed

@pytest.mark.parametrize("bad_name,bad_text", [
    ("bad_no_tags.yaml", BAD_NO_TAGS),
    ("bad_empty_output.yaml", BAD_EMPTY_OUTPUT),
    ("bad_yaml.yaml", BAD_YAML),
    ("bad_mode.yaml", BAD_MODE),
    ("bad_indent.yaml", BAD_INDENT_AFTER_TAGS),
])
def test_异常输入_整批fail_closed_非零且零写盘(tmp_path, bad_name, bad_text):
    files = dict(GOOD_CORPUS)
    files["t1/" + bad_name] = bad_text
    base = _corpus(tmp_path, files)
    before = _snapshot(base)
    r = _cli(tmp_path, "--apply")
    assert r.returncode == 1, "异常输入应显式退出 1（得到 %s）：%s" % (r.returncode, r.stdout)
    assert "FAIL：" in (r.stdout + r.stderr), "应打印显式 FAIL 诊断，而不是崩栈：%r" % (r.stdout + r.stderr)
    assert "Traceback" not in (r.stdout + r.stderr), "不该以未捕获异常收场：%r" % r.stderr
    assert _snapshot(base) == before, "异常输入下仍有文件被写（未 fail-closed）"
    # dry-run / check 同样非零
    assert _cli(tmp_path).returncode == 1
    assert _cli(tmp_path, "--check").returncode == 1


def test_O模式_assert被剥离也拦得住异常输入(tmp_path):
    """-O 下 assert 全部失效——防护必须仍然有效（这是修复前的致命点）。"""
    files = dict(GOOD_CORPUS)
    files["t1/bad_no_tags.yaml"] = BAD_NO_TAGS
    base = _corpus(tmp_path, files)
    before = _snapshot(base)
    r = _cli(tmp_path, "--apply", py_flags=("-O",))
    assert r.returncode == 1, "python -O 下异常输入应显式退出 1（得到 %s）：%s" % (r.returncode, r.stdout)
    assert "FAIL：" in (r.stdout + r.stderr) and "Traceback" not in (r.stdout + r.stderr), (
        "python -O 下应走显式校验（而非崩栈）：%r" % (r.stdout + r.stderr))
    assert _snapshot(base) == before, "python -O 下有文件被写"


def test_O模式_正常输入仍可正确插入(tmp_path):
    base, before = _good_corpus(tmp_path)
    r = _cli(tmp_path, "--apply", py_flags=("-O",))
    assert r.returncode == 0, r.stderr + r.stdout
    after = _snapshot(base)
    assert after["t1/01_missing.yaml"] == _expected_after_insert(before["t1/01_missing.yaml"])
    assert _cli(tmp_path, "--check", py_flags=("-O",)).returncode == 0


def test_路径边界_拒绝对content_r之外写盘(tmp_path):
    base, before = _good_corpus(tmp_path)
    outside = Path(tmp_path) / "content" / "python" / "t" / "01_x.yaml"
    _write(outside, RUN_MISSING)
    with pytest.raises(mrj.HardeningError) as e:
        mrj.apply_one(tmp_path, outside)
    assert "content/r 之外" in str(e.value)
    assert outside.read_bytes() == RUN_MISSING.encode("utf-8")
    assert _snapshot(base) == before


def test_单行差分校验_两行插入被拒(tmp_path):
    base, before = _good_corpus(tmp_path)
    old = before["t1/01_missing.yaml"]
    two = _expected_after_insert(_expected_after_insert(old))
    with pytest.raises(mrj.HardeningError):
        mrj._assert_single_line_insert(old, two, (MARK_LINE + "\n").encode("utf-8"),
                                       "t1/01_missing.yaml")
    with pytest.raises(mrj.HardeningError):
        mrj._assert_single_line_insert(old, old, (MARK_LINE + "\n").encode("utf-8"), "x")


def test_插入函数_块状tags插到块尾(tmp_path):
    base = _corpus(tmp_path, {"t1/block.yaml": BLOCK_TAGS})
    assert _cli(tmp_path, "--apply").returncode == 0
    text = (base / "t1/block.yaml").read_text(encoding="utf-8")
    assert "  - \"b\"\njudge_mode: run\nstatement: |" in text
    assert yaml.safe_load(text)["judge_mode"] == "run"


# ------------------------------------------------- ④ 批量原子性 / 临时文件安全 / 空输入

def _prepare(root):
    """走公开接口拿「已全量生成并验证通过」的计划（模拟 _run 的提交前状态）。"""
    s = mrj.scan(root)
    assert not s["anomalies"], s["anomalies"]
    return mrj.prepare_all(root, s["todo"]), s


def test_空输入_check不再vacuous_pass_allow_empty才放行(tmp_path):
    """SCRIPT-004：content/r 空目录时旧输出是「PASS：0/0 判定模式全部显式」——什么也没证明。"""
    base = Path(tmp_path) / "content" / "r"
    base.mkdir(parents=True, exist_ok=True)
    r = _cli(tmp_path, "--check")
    assert r.returncode == 1, "空目录 --check 必须 FAIL（得到 %s）" % r.returncode
    assert "0 个 yaml" in (r.stdout + r.stderr)
    assert "PASS" not in r.stdout, "空输入不该出现 vacuous pass：%r" % r.stdout
    assert _snapshot(base) == {}
    # dry-run / apply 同样不放过空输入
    assert _cli(tmp_path).returncode == 1
    assert _cli(tmp_path, "--apply").returncode == 1
    # 第三轮 SCRIPT-004：单给 --allow-empty 一律拒绝——生产门禁不得靠一个参数空跑成功
    lone = _cli(tmp_path, "--check", "--allow-empty")
    assert lone.returncode == 1, "单给 --allow-empty 必须被拒：%s" % (lone.stdout + lone.stderr)
    assert "--fixture" in (lone.stdout + lone.stderr), lone.stdout + lone.stderr
    # --allow-empty + --fixture 才放行（测试专用出口）
    ok = _cli(tmp_path, "--check", "--allow-empty", "--fixture")
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert "PASS：0/0 判定模式全部显式（--allow-empty --fixture：空目录）" in ok.stdout


def test_第二个文件写盘失败_第一个文件回滚成原字节(tmp_path):
    """SCRIPT-001 真机复现：第 2 个目标不可替换（Windows 只读属性 → os.replace WinError 5）。

    要求：第一个文件已经 os.replace 成功，也必须回滚成原字节——不许留部分写盘。
    """
    base, before = _good_corpus(tmp_path)
    victim = base / "t1" / "04_crlf.yaml"        # 排序在 01 之后 → 会先写 01
    os.chmod(victim, stat.S_IREAD)
    try:
        r = _cli(tmp_path, "--apply")
    finally:
        os.chmod(victim, stat.S_IWRITE)
    out = r.stdout + r.stderr
    assert r.returncode == 1, "部分写盘失败必须非零退出：%s" % out
    assert "FAIL" in out and "Traceback" not in out, out
    assert "已回滚 1/1" in out, "应点名回滚了 1 个已替换文件：%s" % out
    assert _snapshot(base) == before, "第一个文件没有被恢复成原字节（部分写盘未回滚）"
    # 回滚后仍是「未显式」状态：check 依然 FAIL
    assert _cli(tmp_path, "--check").returncode == 1


def test_第二个文件被并发篡改_整批终止且零提交(tmp_path):
    """SCRIPT-001/003：准备阶段之后目标被改动 → 终止且一个字节都不提交。"""
    base, before = _good_corpus(tmp_path)
    plans, s = _prepare(tmp_path)
    assert len(plans) == 2
    victim = base / "t1" / "04_crlf.yaml"
    victim.write_bytes(victim.read_bytes() + "# 并发篡改\n".encode("utf-8"))
    tampered = _snapshot(base)
    with pytest.raises(mrj.HardeningError) as e:
        mrj.commit_all(tmp_path, plans, expect=s["snapshot"])
    assert "并发修改" in str(e.value) and "04_crlf.yaml" in str(e.value), str(e.value)
    after = _snapshot(base)
    assert after["t1/01_missing.yaml"] == before["t1/01_missing.yaml"], "第一个文件被写了一半"
    assert after == tampered, "除篡改本身外不该有任何字节变化"


def test_写盘后回读不达标_整批回滚(tmp_path, monkeypatch):
    """SCRIPT-001：提交阶段成功但最终回读不达标（第 2 次 scan 报异常）→ 整批回滚原字节。"""
    base, before = _good_corpus(tmp_path)
    real_scan = mrj.scan
    calls = {"n": 0}

    def flaky_scan(root):
        calls["n"] += 1
        s = real_scan(root)
        if calls["n"] >= 2:
            s["anomalies"] = [("t1/01_missing.yaml", "模拟：写盘后回读形态异常")]
        return s

    monkeypatch.setattr(mrj, "scan", flaky_scan)
    rc = mrj.main(["--root", str(tmp_path), "--apply"])
    assert rc == 1, "写盘后回读不达标应非零退出"
    assert calls["n"] >= 2
    assert _snapshot(base) == before, "回读不达标时必须把已写文件回滚成原字节"


def test_staging阶段失败_原文件分毫未动(tmp_path, monkeypatch):
    """SCRIPT-001：临时文件阶段就失败（磁盘满/目录不可写）→ 原文件一个字节都不动。"""
    base, before = _good_corpus(tmp_path)
    plans, s = _prepare(tmp_path)

    def boom(*a, **kw):
        raise OSError("模拟：临时文件创建失败（磁盘满/目录不可写）")

    monkeypatch.setattr(mrj.tempfile, "mkstemp", boom)
    with pytest.raises(mrj.HardeningError) as e:
        mrj.commit_all(tmp_path, plans, expect=s["snapshot"])
    assert "创建临时文件失败" in str(e.value), str(e.value)
    assert _snapshot(base) == before


def test_临时文件_固定名抢占攻击已失效(tmp_path):
    """SCRIPT-002：旧实现用固定名 <file>.tmp<PID> 且 open(tmp,"wb")（跟随符号链接）。

    这里把旧名全部预先占住并写入哨兵字节（真机无建符号链接权限，故用普通文件占位：
    旧实现会直接 truncate 掉它们，新实现必须一个新字节都不写到这些名字上）。
    """
    base, before = _good_corpus(tmp_path)
    sentinel = b"SENTINEL-DO-NOT-TOUCH"
    decoys = [base / "t1" / ("01_missing.yaml.tmp%d" % os.getpid()),
              base / "t1" / ("04_crlf.yaml.tmp%d" % os.getpid())]
    for d in decoys:
        d.write_bytes(sentinel)
    plans, s = _prepare(tmp_path)
    mrj.commit_all(tmp_path, plans, expect=s["snapshot"])     # 同进程 → PID 与旧实现一致
    for d in decoys:
        assert d.read_bytes() == sentinel, "抢占名 %s 被写入了（固定名临时文件回来了）" % d.name
    for rel in ("t1/01_missing.yaml", "t1/04_crlf.yaml"):
        assert (base / rel).read_bytes() == _expected_after_insert(before[rel]), rel
    assert _cli(tmp_path, "--check").returncode == 0


def _swap_with_link(tmp_name, outside):
    """把 tmp_name 换成指向 outside 的链接；无建符号链接权限时退化为硬链接。"""
    os.unlink(tmp_name)
    try:
        os.symlink(str(outside), tmp_name)
        return "symlink"
    except OSError:
        os.link(str(outside), tmp_name)
        return "hardlink"


def test_临时文件_提交前被换成链接_拒绝并回滚且外部文件零改动(tmp_path, monkeypatch):
    """SCRIPT-002 TOCTOU 攻击：在我们的临时文件就位后、os.replace 之前，攻击者把临时名
    换成指向外部文件的链接（符号链接；本机无 SeCreateSymbolicLinkPrivilege 时退化为硬链接，
    两者都命中同一条防线：写后回读不达标 → 拒绝 → 回滚）。

    断言三件事：脚本 fail-closed 非零；外部文件一个字节没被写穿；content/r 全部恢复原字节。
    """
    base, before = _good_corpus(tmp_path)
    outside = Path(tmp_path) / "outside.txt"
    outside.write_bytes(b"OUTSIDE-ORIGINAL")
    real_replace = os.replace
    kind = {"v": None, "n": 0}

    def hostile_replace(src, dst):
        kind["n"] += 1
        if kind["n"] == 1:                     # 只在第一次提交时动手，不影响回滚
            kind["v"] = _swap_with_link(str(src), outside)
        return real_replace(src, dst)

    monkeypatch.setattr(mrj.os, "replace", hostile_replace)
    plans, s = _prepare(tmp_path)
    with pytest.raises(mrj.HardeningError) as e:
        mrj.commit_all(tmp_path, plans, expect=s["snapshot"])
    print("本次攻击变体 =", kind["v"])
    assert kind["v"] in ("symlink", "hardlink")
    assert "已回滚 1/1" in str(e.value), str(e.value)
    assert outside.read_bytes() == b"OUTSIDE-ORIGINAL", "外部文件被写穿"
    # 断言范围写精确：比对全部题目 yaml（.judge_plain_txn/ 是事务记账，不是题目）。
    # 回滚证据不得被这件事掩盖——下面单独钉住「冲突副本必须留下」。
    after = _snapshot(base)
    corpus = {k: v for k, v in after.items() if not k.startswith(mrj.TXN_DIRNAME + "/")}
    assert corpus == before, "content/r 题目未恢复成原字节 / 有链接残留"
    assert kind["n"] >= 2, "回滚自身也应走 os.replace（攻击只在第一次动手）"
    # 被掉包后写进目标的那份「既非旧也非新」的字节必须留痕，而不是被悄悄丢掉
    conflicts = [k for k in after if k.startswith(mrj.TXN_DIRNAME + "/" + mrj.CONFLICT_DIRNAME + "/")]
    assert len(conflicts) == 1, "冲突副本未保存：%s" % sorted(after)
    assert after[conflicts[0]] == b"OUTSIDE-ORIGINAL", "冲突副本内容不对"


def test_临时文件身份校验_非普通文件或换过inode即拒(tmp_path):
    """SCRIPT-002 防线契约单测。

    「持有 fd 时被 unlink 后换名」在 POSIX 上可发生（Windows 会直接拒绝 unlink 打开中的
    临时文件，WinError 32），故这里按契约单测校验函数本身：正常放行、换 inode 拒绝、
    不是普通文件拒绝。
    """
    base = _corpus(tmp_path, {"t1/01_missing.yaml": RUN_MISSING})
    fd, name = tempfile.mkstemp(dir=str(base / "t1"), prefix="01_missing.yaml.", suffix=".tmp")
    other = Path(tmp_path) / "other.tmp"
    other.write_bytes(b"not-the-temp-file")
    try:
        st_fd = os.fstat(fd)
        mrj._assert_temp_identity(Path(name), st_fd, "单测")          # 正常：放行，不抛
        with pytest.raises(mrj.HardeningError) as e1:
            mrj._assert_temp_identity(other, st_fd, "单测")            # 换成了别的 inode
        assert "inode" in str(e1.value), str(e1.value)
        with pytest.raises(mrj.HardeningError) as e2:
            mrj._assert_temp_identity(base / "t1", st_fd, "单测")      # 不是普通文件
        assert "普通文件" in str(e2.value), str(e2.value)
    finally:
        os.close(fd)
        mrj._unlink(name)
        other.unlink()
    # 清理干净：只该剩那个原始 yaml，临时文件与 other 都不许落在 content/r 里
    assert _snapshot(base) == {"t1/01_missing.yaml": RUN_MISSING.encode("utf-8")}


def test_scan遇到OSError_统一FAIL零写盘(tmp_path):
    """SCRIPT-003 真机复现：content/r/t1/05_dir.yaml 是目录 → read_bytes() 抛 OSError。"""
    base = _corpus(tmp_path, dict(GOOD_CORPUS))
    (base / "t1" / "05_dir.yaml").mkdir()
    before = _snapshot(base)
    r = _cli(tmp_path, "--apply")
    out = r.stdout + r.stderr
    assert r.returncode == 1, "目录型 *.yaml 应走 fail-closed：%s" % out
    assert "FAIL" in out and "Traceback" not in out, out
    assert "05_dir.yaml" in out and "读取/解析异常" in out, out
    assert _snapshot(base) == before, "异常输入下仍有文件被写"
    assert _cli(tmp_path, "--check").returncode == 1


def test_顶层IO异常_统一转FAIL非零(tmp_path, monkeypatch):
    """SCRIPT-003：连扫描都抛 OSError（目录不可访问）也必须统一 FAIL，而不是崩栈。"""
    base, before = _good_corpus(tmp_path)

    def boom(root):
        raise OSError("模拟：content/r 不可访问")

    monkeypatch.setattr(mrj, "r_files", boom)
    assert mrj.main(["--root", str(tmp_path), "--check"]) == 1
    assert mrj.main(["--root", str(tmp_path), "--apply"]) == 1
    assert _snapshot(base) == before


# ------------------------------------------------------------------ ③ 字节级差分（真题库）

def _real_r_files():
    import glob
    return sorted(Path(p) for p in glob.glob("content/r/*/*.yaml"))


def test_真题库_每行删掉再插回_字节完全相等():
    """84 行逐行证明：原文 + 恰一行 == 现状字节（含 16 个 CRLF 文件与带引号的 ai_open）。"""
    files = _real_r_files()
    assert len(files) == 84
    checked = {"run": 0, "ai_open": 0}
    for f in files:
        raw = f.read_bytes()
        text = raw.decode("utf-8")
        eol = "\r\n" if "\r\n" in text else "\n"
        lines = text.splitlines(keepends=True)
        jm = [i for i, l in enumerate(lines) if l.startswith("judge_mode:")]
        assert len(jm) == 1, "%s 的 judge_mode 行数 = %d" % (f, len(jm))
        line_text = lines[jm[0]].rstrip("\r\n")
        stripped = "".join(l for i, l in enumerate(lines) if i != jm[0])
        rebuilt = mrj._insert_line_after_tags(stripped, line_text, eol, f)
        assert rebuilt.encode("utf-8") == raw, "%s 删掉再插回后字节不一致" % f
        assert len(raw) - len(stripped.encode("utf-8")) == len(line_text.encode("utf-8")) + len(eol)
        mode = yaml.safe_load(text)["judge_mode"]
        checked[mode] += 1
        assert mrj._assert_single_line_insert is not None
    assert checked == {"run": 70, "ai_open": 14}, checked


def test_真题库_run题现状字节_等于原文加恰一行judge_mode_run():
    """70 道 run 题的现状字节 == 备份的改动前字节 + 恰一行（对照 data/backups 的 pre-D6 基线）。"""
    backup = Path("data/backups/content-20260920-133722/content/r")
    if not backup.is_dir():
        pytest.skip("pre-D6 备份不在盘上（%s），跳过字节基线对照" % backup)
    manifest = {}
    for line in (Path("data/backups/content-20260920-133722") / "manifest-before.txt") \
            .read_text(encoding="utf-8").splitlines():
        h, p = line.split(None, 1)
        manifest[p.replace("\\", "/")] = h
    changed = 0
    for f in _real_r_files():
        rel = str(f).replace("\\", "/")
        old_path = backup / f.parent.name / f.name
        if not old_path.exists():
            continue
        old = old_path.read_bytes()
        # 备份自身完整性：manifest 的 sha256 必须对得上（证据链）
        assert hashlib.sha256(old).hexdigest() == manifest[rel], "备份文件被改动：%s" % rel
        new = f.read_bytes()
        if yaml.safe_load(new.decode("utf-8"))["judge_mode"] == "run":
            assert new == _expected_after_insert(old, MARK_LINE), \
                "%s 不等于「改动前原文 + 恰一行」" % rel
            changed += 1
        else:
            assert new == old, "%s（ai_open）不该被动过" % rel
    assert changed == 70, "run 题数量漂移：%d" % changed


def test_真题库_check通过_70_14分布门禁():
    """真仓库端到端只读门禁：--check + 精确分布，零写盘。"""
    root = Path.cwd()
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in _real_r_files()}
    r = _cli(root, "--check", "--expect-distribution", "run=70,ai_open=14")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PASS：84/84 判定模式全部显式" in r.stdout
    after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in _real_r_files()}
    assert after == before, "--check 不该写盘"
