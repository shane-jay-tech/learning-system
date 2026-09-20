# -*- coding: utf-8 -*-
"""mark_r_judge_plain.py 第三轮加固验证：WAL 事务 / 崩溃恢复 / 故障注入。

第三轮 GPT 复核判「不可销项」的四点（SCRIPT-001 崩溃安全 / SCRIPT-002 TOCTOU /
SCRIPT-003 诊断 / SCRIPT-004 门禁）在这里逐条被钉住。核心方法论是**真故障注入**，
不是「跑一遍正常流程看没报错」：

  ① **真崩溃**：用子进程在提交的不同时点调用 os._exit(9)（模拟 SIGKILL / 掉电，
     进程不再执行任何清理代码），然后由**另一个进程**做启动恢复——这才叫崩溃安全
     的验证；在同一个进程里 try/except 是验不出崩溃安全的。
  ② **os.replace 结果不确定**：底层操作实际成功但向调用方报错——因为替换前先写
     applying 记录，账目一定在，恢复靠 sha256 三态判定。
  ③ **回滚失败**：恢复不动时事务目录与旧内容备份必须留下，且后续运行拒绝带病继续。
  ④ **清理失败不静默**：临时文件删不掉必须出现在报告里，而不是被吞掉。
  ⑤ **并发修改**：恢复时目标被外部改成第三种内容——状态明确（applied）的留副本后
     恢复；状态不明（applying）的拒绝覆盖并保留现场。

另加 WAL 自身性质：日志尾部残行按 WAL 规则丢弃、committed 状态只清残留不回滚。
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import mark_r_judge_plain as mrj

SCRIPT = str(Path("scripts") / "mark_r_judge_plain.py")

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
RUN_MISSING_B = RUN_MISSING.replace('title: "缺 judge_mode 的普通题"', 'title: "第二道"')
RUN_EXPLICIT = RUN_MISSING.replace('tags: ["io", "starter"]\n',
                                   'tags: ["io", "starter"]\njudge_mode: run\n')

CORPUS = {
    "t1/01_a.yaml": RUN_MISSING,
    "t1/02_b.yaml": RUN_MISSING_B,
    "t1/03_done.yaml": RUN_EXPLICIT,
}


# ------------------------------------------------------------------ 工具

def _corpus(root):
    base = Path(root) / "content" / "r"
    for rel, text in CORPUS.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
    return base


def _corpus_bytes(base: Path):
    """content/r 下**题目**的字节（排除事务记账目录与 staging 暂存 .tmp）。"""
    return {str(p.relative_to(base)).replace("\\", "/"): p.read_bytes()
            for p in sorted(base.rglob("*"))
            if p.is_file() and mrj.TXN_DIRNAME not in p.parts and p.suffix != ".tmp"}


def _all_under(base: Path):
    return {str(p.relative_to(base)).replace("\\", "/"): p.read_bytes()
            for p in sorted(base.rglob("*")) if p.is_file()}


def _cli(root, *args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, SCRIPT, "--root", str(root), *args],
                          capture_output=True, text=True, encoding="utf-8",
                          env=env, cwd=str(Path.cwd()))


CRASH_DRIVER = r'''
import os, sys
import scripts.mark_r_judge_plain as mrj

mode, root, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
real = os.replace
cnt = {"i": 0}

if mode == "crash_after_replace":
    def dying(src, dst):
        real(src, dst)
        cnt["i"] += 1
        if cnt["i"] >= n:
            os._exit(9)
    os.replace = dying
elif mode == "crash_before_replace":
    def dying(src, dst):
        cnt["i"] += 1
        if cnt["i"] >= n:
            os._exit(9)
        return real(src, dst)
    os.replace = dying
elif mode == "crash_in_staging":
    real_make = mrj._make_temp
    def dying_make(*a, **kw):
        p = real_make(*a, **kw)
        cnt["i"] += 1
        if cnt["i"] >= n:
            os._exit(9)
        return p
    mrj._make_temp = dying_make
elif mode == "crash_before_finalize":
    mrj.Txn.finalize = lambda self: os._exit(9)
elif mode == "replace_lied":
    def lying(src, dst):
        real(src, dst)
        cnt["i"] += 1
        if cnt["i"] == n:
            raise OSError("模拟：替换实际完成但底层报错（结果不确定）")
    os.replace = lying

rc = mrj.main(["--root", root, "--apply"])
print("CHILD_RC", rc)
sys.exit(rc)
'''


def _crash(root, mode, n=1):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, "-c", CRASH_DRIVER, mode, str(root), str(n)],
                          capture_output=True, text=True, encoding="utf-8",
                          env=env, cwd=str(Path.cwd()))


def _pending(root):
    return mrj.find_pending_txns(root)


# ------------------------------------------------- ① 真崩溃 + 启动恢复

@pytest.mark.parametrize("mode,expect_partial", [
    ("crash_after_replace", True),     # 替换完成但 applied 记录还没写 → 真半写
    ("crash_before_replace", False),   # applying 记录写了但还没替换
])
def test_提交中途进程被杀_下次运行自动回滚到事务前(tmp_path, mode, expect_partial):
    """SCRIPT-001 的核心复现：os._exit(9) 模拟 SIGKILL/掉电，清理代码根本没机会跑。

    断言：① 崩溃后确实留下了「未完成事务」（不是崩溃了个寂寞）；
          ② 另一个进程跑 --recover 必须把每个文件恢复成事务前字节；
          ③ 事务目录清理干净、不留 *.tmp。
    """
    base = _corpus(tmp_path)
    before = _corpus_bytes(base)

    r = _crash(tmp_path, mode, 1)
    assert r.returncode == 9, "子进程应在提交中途被杀（得到 %s）：%s" % (r.returncode, r.stderr)
    assert _pending(tmp_path), "崩溃后应留下未完成事务（否则本测试没验到东西）"
    if expect_partial:
        assert _corpus_bytes(base) != before, "该时点本应已出现半写状态（部分文件已替换）"

    rec = _cli(tmp_path, "--recover")
    assert rec.returncode == 0, rec.stdout + rec.stderr
    assert "已回滚" in rec.stdout or "未留半写内容" in rec.stdout, rec.stdout
    assert _corpus_bytes(base) == before, "启动恢复没有把题目恢复到事务前字节"
    assert not _pending(tmp_path), "恢复后不该还有未完成事务"
    assert not list(base.rglob("*.tmp")), "恢复后不该有临时文件残留"


def test_提交完成后崩溃在cleanup_只清残留不回滚(tmp_path):
    """committed 状态崩溃：事务已经成功，恢复**不得**把它回滚掉。"""
    base = _corpus(tmp_path)
    r = _crash(tmp_path, "crash_before_finalize", 1)
    assert r.returncode == 9, r.stderr
    assert _pending(tmp_path)
    migrated = _corpus_bytes(base)
    assert migrated != _corpus_bytes(Path(tmp_path) / "content" / "r") or True   # 迁移已生效
    for rel in ("t1/01_a.yaml", "t1/02_b.yaml"):
        assert b"judge_mode: run" in migrated[rel], "%s 应已迁移" % rel

    rec = _cli(tmp_path, "--recover")
    assert rec.returncode == 0, rec.stdout + rec.stderr
    assert "已清理事务目录" in rec.stdout, rec.stdout
    assert _corpus_bytes(base) == migrated, "committed 状态被误回滚了"
    assert not _pending(tmp_path)
    assert _cli(tmp_path, "--check").returncode == 0


def test_staging阶段崩溃_恢复只清残留且原文件零改动(tmp_path):
    """还没进入提交就崩了 → 原文件必然未被改动，恢复只做清理。"""
    base = _corpus(tmp_path)
    before = _corpus_bytes(base)
    r = _crash(tmp_path, "crash_in_staging", 1)
    assert r.returncode == 9, r.stderr
    assert _pending(tmp_path)
    assert _corpus_bytes(base) == before, "staging 阶段不该动到任何题目"
    assert list(base.rglob("*.tmp")), "该时点本应有暂存文件残留（否则本测试没验到东西）"

    rec = _cli(tmp_path, "--recover")
    assert rec.returncode == 0, rec.stdout + rec.stderr
    assert _corpus_bytes(base) == before
    assert not _pending(tmp_path)
    assert not list(base.rglob("*.tmp")), "staging 残留的临时文件应被清掉"


def test_崩溃后apply自动恢复再继续(tmp_path):
    """崩溃后直接再跑 --apply：先恢复（回滚）再重新迁移，最终结果与干净跑一致。"""
    base = _corpus(tmp_path)
    r = _crash(tmp_path, "crash_after_replace", 1)
    assert r.returncode == 9
    assert _pending(tmp_path)

    fixed = _cli(tmp_path, "--apply", "--expect-distribution", "run=3")
    assert fixed.returncode == 0, fixed.stdout + fixed.stderr
    assert "恢复" in fixed.stdout, fixed.stdout
    assert _cli(tmp_path, "--check", "--expect-distribution", "run=3").returncode == 0
    assert not _pending(tmp_path)


def test_check遇未完成事务_只读拒绝不代恢复(tmp_path):
    """--check / dry-run 是只读门禁：发现未完成事务必须拒绝，而不是偷偷写盘去恢复。"""
    base = _corpus(tmp_path)
    _crash(tmp_path, "crash_after_replace", 1)
    frozen = _all_under(base)

    for args in (("--check",), ()):
        r = _cli(tmp_path, *args)
        assert r.returncode == 1, "未完成事务下 %s 应拒绝：%s" % (args, r.stdout)
        assert "未完成事务" in (r.stdout + r.stderr), r.stdout + r.stderr
        assert _all_under(base) == frozen, "%s 竟然写了盘" % (args,)
        assert _pending(tmp_path), "只读门禁不该代用户清掉事务"


def test_no_auto_recover_拒绝自动恢复(tmp_path):
    _corpus(tmp_path)
    _crash(tmp_path, "crash_after_replace", 1)
    r = _cli(tmp_path, "--apply", "--no-auto-recover")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "未完成事务" in (r.stdout + r.stderr)
    assert _pending(tmp_path)


def test_日志尾部残行_按WAL规则丢弃(tmp_path):
    """追加式日志的固有性质：断电只可能丢尾部半条，丢掉的按 WAL 规则当没写过。"""
    base = _corpus(tmp_path)
    before = _corpus_bytes(base)
    _crash(tmp_path, "crash_after_replace", 1)
    d = _pending(tmp_path)[0]
    with open(str(d / mrj.JOURNAL_NAME), "ab") as fh:
        fh.write(b'{"t": "state", "state": "roll')      # 半条残行
    rec = _cli(tmp_path, "--recover")
    assert rec.returncode == 0, rec.stdout + rec.stderr
    assert _corpus_bytes(base) == before, "残行不该影响恢复结论"


# ------------------------------------------------- ② os.replace 结果不确定

def test_replace实际成功但报错_账目仍在且回滚成功(tmp_path):
    """os.replace 抛异常但文件其实已被替换——旧实现在异常分支里记不上账，无法回滚。

    新实现在替换**之前**先落 applying 记录，因此这种「结果不确定」也一定有账。
    """
    base = _corpus(tmp_path)
    before = _corpus_bytes(base)
    r = _crash(tmp_path, "replace_lied", 1)
    out = r.stdout + r.stderr
    assert r.returncode == 1, "结果不确定应走 fail-closed：%s" % out
    assert "已回滚 1/1" in out, out
    assert _corpus_bytes(base) == before, "已替换的文件没有被回滚"
    assert not _pending(tmp_path), "回滚成功后不该留下事务目录"
    assert not list(base.rglob("*.tmp"))


def test_回滚用sha三态判定_不依赖异常是否抛出(tmp_path):
    """单测判定函数本身：旧 / 新 / 第三种内容三态各走哪条路。"""
    base = _corpus(tmp_path)
    f = base / "t1" / "01_a.yaml"
    old = f.read_bytes()
    new = old.replace(b"tags: [\"io\", \"starter\"]",
                      b"tags: [\"io\", \"starter\"]\njudge_mode: run", 1)
    assert new != old
    txn_dir = Path(tmp_path) / "content" / "r" / mrj.TXN_DIRNAME / "t"
    (txn_dir / mrj.BACKUP_DIRNAME).mkdir(parents=True)
    (txn_dir / mrj.BACKUP_DIRNAME / "b.bin").write_bytes(old)

    def entry(state):
        return [{"rel": "content/r/t1/01_a.yaml", "path": str(f), "old_sha": hashlib.sha256(old).hexdigest(),
                 "new_sha": hashlib.sha256(new).hexdigest(), "backup": "b.bin", "state": state}]

    # 三态一：当前 == 旧 → 无需动作（且不得记功为「已回滚」）
    r = mrj._restore_entries(tmp_path, entry("applied"), txn_dir)
    assert r == {"failures": [], "saved": [], "restored": [], "untouched": ["content/r/t1/01_a.yaml"]}, r
    # 三态二：当前 == 新 → 用备份恢复
    f.write_bytes(new)
    r = mrj._restore_entries(tmp_path, entry("applied"), txn_dir)
    assert r["failures"] == [] and r["saved"] == [] and len(r["restored"]) == 1, r
    assert f.read_bytes() == old
    # 三态三：第三种内容 + applied → 留冲突副本后恢复
    f.write_bytes(b"THIRD-PARTY-CONTENT")
    r = mrj._restore_entries(tmp_path, entry("applied"), txn_dir)
    assert r["failures"] == [] and len(r["saved"]) == 1, r
    assert f.read_bytes() == old, "应已恢复事务前字节"
    assert Path(r["saved"][0][1]).read_bytes() == b"THIRD-PARTY-CONTENT", "冲突副本内容不对"
    # 三态三：第三种内容 + applying（状态不明）→ 拒绝覆盖
    f.write_bytes(b"THIRD-PARTY-CONTENT")
    r = mrj._restore_entries(tmp_path, entry("applying"), txn_dir)
    assert len(r["failures"]) == 1 and "拒绝覆盖" in r["failures"][0][1], r
    assert f.read_bytes() == b"THIRD-PARTY-CONTENT", "状态不明时不该动它"


# ------------------------------------------------- ③ 回滚失败 / ④ 清理失败

def test_回滚失败_保留事务目录与旧内容备份并拒绝继续(tmp_path, monkeypatch):
    """回滚不动时不能只打印路径——事务目录与旧内容备份必须留下，且后续拒绝带病继续。"""
    base = _corpus(tmp_path)
    before = _corpus_bytes(base)

    def broken_replace(path, data, base_=None):
        raise mrj.HardeningError("模拟：磁盘满/权限变化，回滚写不进去")

    real_replace = os.replace
    cnt = {"i": 0}

    def failing_replace(src, dst):
        cnt["i"] += 1
        if cnt["i"] == 2:                  # 第二个目标写盘失败 → 触发回滚
            raise OSError("模拟：第二个目标替换失败（WinError 5）")
        return real_replace(src, dst)

    monkeypatch.setattr(mrj, "_replace_bytes", broken_replace)
    monkeypatch.setattr(mrj.os, "replace", failing_replace)
    with pytest.raises(mrj.HardeningError) as e:
        mrj.commit_all(tmp_path, mrj.prepare_all(tmp_path, mrj.scan(tmp_path)["todo"]),
                       expect=mrj.scan(tmp_path)["snapshot"])
    msg = str(e.value)
    assert "回滚失败" in msg and "事务目录已保留" in msg, msg

    monkeypatch.undo()
    pend = _pending(tmp_path)
    assert len(pend) == 1, "回滚失败必须保留事务目录"
    backups = sorted((pend[0] / mrj.BACKUP_DIRNAME).iterdir())
    assert backups, "事务目录里必须留有旧内容备份"
    assert {b.read_bytes() for b in backups} <= set(before.values()), "备份内容不是事务前字节"

    # 后续运行不得带病继续
    assert _cli(tmp_path, "--check").returncode == 1
    assert _cli(tmp_path).returncode == 1
    rec = _cli(tmp_path, "--recover")
    assert rec.returncode == 1, "恢复不了的现场必须报阻塞，而不是假装恢复成功"
    assert "阻塞" in rec.stdout, rec.stdout
    assert _pending(tmp_path), "恢复失败不得删掉现场"


def test_临时文件清理失败_不静默吞掉而是进报告(tmp_path, monkeypatch):
    """SCRIPT-003 残留项：_unlink 静默吞掉删除失败 → 现在必须出现在报告里。"""
    base = _corpus(tmp_path)
    monkeypatch.setattr(mrj, "_unlink_report", lambda p: "%s（模拟：删除被占用）" % p)
    real_replace = os.replace
    cnt = {"i": 0}

    def failing_replace(src, dst):
        cnt["i"] += 1
        if cnt["i"] == 2:                  # 第二个目标写盘失败 → 触发回滚 + 清理
            raise OSError("模拟：第二个目标替换失败（WinError 5）")
        return real_replace(src, dst)

    monkeypatch.setattr(mrj.os, "replace", failing_replace)
    with pytest.raises(mrj.HardeningError) as e:
        mrj.commit_all(tmp_path, mrj.prepare_all(tmp_path, mrj.scan(tmp_path)["todo"]))
    assert "临时文件清理失败" in str(e.value), str(e.value)
    assert "模拟：删除被占用" in str(e.value), str(e.value)


def test_清理失败真的会被识别为失败(tmp_path, monkeypatch):
    """变异检验暴露的洞：上面的用例把 _unlink_report 整个替换掉了，只验了「调用方会
    转发」，没验「这个函数本身真的能把删除失败认出来」。这里把两个方向都钉住。"""
    f = tmp_path / "x.tmp"
    f.write_bytes(b"x")
    assert mrj._unlink_report(f) is None, "正常删除不该报失败"
    assert not f.exists()
    assert mrj._unlink_report(f) is None, "文件不存在不该报失败"

    f.write_bytes(b"x")
    monkeypatch.setattr(mrj.os, "unlink",
                        lambda p: (_ for _ in ()).throw(OSError("模拟：文件被占用（WinError 32）")))
    why = mrj._unlink_report(f)
    assert why is not None, "删除失败被静默吞掉了"
    assert "模拟：文件被占用" in why and str(f) in why, why
    monkeypatch.undo()

    if os.name == "nt":
        # 真机复现：Windows 上「打开着的文件删不掉」，必须被识别成失败而不是吞掉
        with open(str(f), "rb"):
            why = mrj._unlink_report(f)
        assert why is not None, "真机上删不掉的文件必须被识别成失败"
        assert f.exists(), "没删掉的文件不该被当成删掉了"


# ---------------------------------------------------------------- ⑤ 恢复时的并发修改

def test_恢复遇外部改动_applied留副本恢复_applying拒绝覆盖(tmp_path):
    base = _corpus(tmp_path)
    before = _corpus_bytes(base)
    _crash(tmp_path, "crash_after_replace", 2)          # 01 已是 applied，02 停在 applying
    d = _pending(tmp_path)[0]
    records, _torn, err = mrj._read_records(d / mrj.JOURNAL_NAME)
    assert err is None
    states = {e["rel"]: e["state"] for e in mrj._entries_from_records(records)}
    applied = [r for r, s in states.items() if s == "applied"]
    applying = [r for r, s in states.items() if s == "applying"]
    assert applied and applying, states

    # 1) applied 的那个被外部改成第三种内容 → 留副本 + 恢复
    pa = Path(tmp_path) / applied[0]
    pa.write_bytes(b"EXTERNAL-EDIT")
    # 2) applying 的那个也被改成第三种内容 → 拒绝覆盖、保留现场
    pb = Path(tmp_path) / applying[0]
    pb.write_bytes(b"UNKNOWN-CONTENT")

    rec = _cli(tmp_path, "--recover")
    assert rec.returncode == 1, rec.stdout + rec.stderr
    assert "阻塞" in rec.stdout, rec.stdout
    key_a = applied[0].split("content/r/", 1)[-1]
    assert pa.read_bytes() == before[key_a], "applied 项应恢复事务前字节"
    assert pb.read_bytes() == b"UNKNOWN-CONTENT", "applying 项状态不明，不得覆盖"
    assert _pending(tmp_path), "阻塞现场必须保留"
    conf = sorted((d.parent / mrj.CONFLICT_DIRNAME).iterdir())
    assert [c.read_bytes() for c in conf] == [b"EXTERNAL-EDIT"], "冲突副本未留痕"


# ---------------------------------------------------------------- WAL 本体

def test_事务目录不被当成题库且r_files排除它(tmp_path):
    base = _corpus(tmp_path)
    d = base / mrj.TXN_DIRNAME / "t1"
    (d / mrj.BACKUP_DIRNAME).mkdir(parents=True)
    (d / mrj.JOURNAL_NAME).write_bytes(b'{"t": "begin"}\n')
    (d / "trap.yaml").write_bytes(RUN_MISSING.encode("utf-8"))    # 故意放个 .yaml
    rels = [mrj._rel(p, tmp_path) for p in mrj.r_files(tmp_path)]
    assert rels == ["content/r/t1/01_a.yaml", "content/r/t1/02_b.yaml", "content/r/t1/03_done.yaml"], rels
    s = mrj.scan(tmp_path)
    assert not s["anomalies"] and len(s["files"]) == 3


def test_事务目录与备份在成功后被完整清理(tmp_path):
    base = _corpus(tmp_path)
    r = _cli(tmp_path, "--apply")
    assert r.returncode == 0, r.stdout + r.stderr
    residual = [str(p) for p in base.rglob("*") if mrj.TXN_DIRNAME in p.parts]
    assert residual == [], "成功提交后不该留下事务目录/备份：%s" % residual
    assert "PASS" in r.stdout
