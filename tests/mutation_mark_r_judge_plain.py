# -*- coding: utf-8 -*-
"""mark_r_judge_plain.py 的变异检验（mutation check）。

为什么要有这个文件：**绿色的测试只能证明「跑过了」，证明不了「拦得住」**。这里把
mark_r_judge_plain.py 的每一处关键防护逐个破坏掉，再跑同一套测试——测试必须**转红**，
否则那处防护就是没人守的（说明测试是假的、或根本没覆盖到）。

第四轮 GPT 独立评审的 P1-4 指出：口头声称「10 项变异全红」无法复核。本文件把它变成
可执行的证据。

用法（在 learning-system 仓库根目录）：
    python tests/mutation_mark_r_judge_plain.py

输出每一处变异的红/漏标记，最后打印「N/N 被测试拦住」；有漏即退出码 1。
本文件刻意不叫 test_*.py —— pytest 不会收集它（它是工具，不是用例）。
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TXN_TESTS = "tests/test_mark_r_judge_txn.py"
PLAIN_TESTS = "tests/test_mark_r_judge_plain.py"

TARGETS = [
    TXN_TESTS,
    PLAIN_TESTS + "::test_空输入_check不再vacuous_pass_allow_empty才放行",
    PLAIN_TESTS + "::test_临时文件_提交前被换成链接_拒绝并回滚且外部文件零改动",
    PLAIN_TESTS + "::test_第二个文件写盘失败_第一个文件回滚成原字节",
]

# (编号+说明, 被替换的原文, 替换成什么)
MUTATIONS = [
    ("M01 去掉 replace 前的 applying 记录（结果不确定就失账）",
     '            _journal_append(self.journal, {"t": "entry", "rel": rel, "state": "applying"})\n',
     ""),
    ("M02 去掉 committing 状态记录（崩溃后分不清是否半写）",
     '        _journal_append(self.journal, {"t": "state", "state": "committing"})\n',
     ""),
    ("M03 去掉 committed 状态记录（成功提交被误判成半写而回滚）",
     '        _journal_append(self.journal, {"t": "state", "state": "committed"})\n',
     ""),
    ("M04 不写旧内容备份（回滚没有材料）",
     '            _write_exclusive(bdir / name, p["old"])\n            self.backups[p["rel"]] = name',
     '            self.backups[p["rel"]] = name'),
    ("M05 回滚时无条件覆盖（不看 sha，覆盖并发修改）",
     '        if cur_sha != e.get("new_sha"):',
     '        if False:'),
    ("M06 遇到第三种内容直接放弃恢复（不留副本、不恢复）",
     '            if e.get("state") == "applied":',
     '            if False:'),
    ("M07 清理失败静默吞掉",
     '    except OSError as e:\n        return "%s（%s）" % (path, e)\n    return None',
     '    except OSError:\n        return None\n    return None'),
    ("M08 去掉未记账暂存文件的兜底扫描",
     '            residue = _cleanup_recorded_temps(tmps) + _sweep_staged_temps(entries)',
     '            residue = _cleanup_recorded_temps(tmps)'),
    ("M09 去掉 --fixture 守卫（--allow-empty 单独放行）",
     '        if not getattr(args, "fixture", False):',
     '        if False:'),
    ("M10 回滚计数把「未改动」也算成已回滚",
     '                   % (len(tx.restored), need, e))',
     '                   % (len(tx.restored) + len(tx.untouched), need, e))'),
    ("M11 committed 不做完整性校验（半写批次被当成成功清掉）",
     '        if state == "committed":\n            bad = _validate_committed(entries, records)',
     '        if False:\n            bad = _validate_committed(entries, records)'),
    ("M12 不校验日志条目路径（损坏日志可让恢复越界）",
     '        bad = _validate_entries(entries, root, d)',
     '        bad = None'),
    ("M13 不校验 begin 唯一性",
     '        if len(begins) != 1:',
     '        if False:'),
    ("M14 残留扫描失败被当成没有残留",
     '        return [], "残留扫描失败（%s）：%s" % (base, e)',
     '        return [], None'),
    ("M15 事务目录放回题库目录内（会被题库工具误收）",
     '    return Path(root).resolve() / TXN_DIRNAME',
     '    return r_dir(root) / TXN_DIRNAME'),
    ("M17 不校验 rel 与 path 的绑定（恢复可把 A 的旧内容写回 B）",
     '    if expected.resolve() != p.resolve():',
     '    if False:'),
    ("M18 事务目录扫描失败被当成「没有未完成事务」",
     '        _fail("扫描事务目录失败（%s）：%s——按 fail-closed 处理，不把「扫不动」当成"\n              "「没有未完成事务」" % (d, e))',
     '        return []'),
    ("M16 _make_temp 异常清理回到静默吞掉",
     '        why = _unlink_report(tmp) if tmp is not None else None',
     '        why = None'),
]


def _run(node_ids, cwd, timeout=900):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header",
                           "-p", "no:cacheprovider", *node_ids],
                          capture_output=True, text=True, encoding="utf-8",
                          env=env, cwd=str(cwd), timeout=timeout)


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="mrj-mutation-"))
    try:
        for sub in ("scripts", "tests"):
            (work / sub).mkdir(parents=True, exist_ok=True)
        for rel in ("scripts/mark_r_judge_plain.py", "scripts/__init__.py",
                    "tests/__init__.py", TXN_TESTS, PLAIN_TESTS, "pytest.ini"):
            src = REPO / rel
            if src.exists():
                shutil.copy2(src, work / rel)
        target = work / "scripts" / "mark_r_judge_plain.py"
        pristine = target.read_text(encoding="utf-8")

        base = _run(TARGETS, work)
        print("基线（未变异）：", base.stdout.strip().splitlines()[-1] if base.stdout.strip() else "?")
        if base.returncode != 0:
            print("基线不绿，变异检验没有意义。以下是基线输出：")
            print(base.stdout[-3000:])
            return 2

        missed = []
        for name, old, new in MUTATIONS:
            if old not in pristine:
                print("[锚点缺失] %s —— 源码已变，请更新本文件的变异锚点" % name)
                missed.append(name)
                continue
            target.write_text(pristine.replace(old, new, 1), encoding="utf-8")
            try:
                r = _run(TARGETS, work)
            finally:
                target.write_text(pristine, encoding="utf-8")
            last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "(无输出)"
            caught = r.returncode != 0
            if not caught:
                missed.append(name)
            print("%s %s  %s" % ("[红]" if caught else "[漏]", name, last))

        print(chr(10) + "变异检验结果：%d/%d 被测试拦住"
              % (len(MUTATIONS) - len(missed), len(MUTATIONS)))
        for name in missed:
            print("  未被拦住：%s" % name)
        return 0 if not missed else 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
