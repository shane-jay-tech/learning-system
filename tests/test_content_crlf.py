# -*- coding: utf-8 -*-
"""content/**/*.yaml 行尾普查钉桩（l922-04）。

钉的是**真会咬人的两种行尾损伤**，逐文件判：
  ① 零「孤立 CR」——出现不跟 LF 的裸 `\\r`（半截转换、`tr -d '\\n'`、跨平台拼接的典型产物）。
     yaml.safe_load 能容忍 CRLF，但按 `split('\\n')` 或按字节读题的工具会把 `\\r` 留在值里
     （`difficulty: 2` 变成 `2\\r`），这类损伤必须当场红。
  ② 文件内行尾自洽——一个文件里不得 LF 与 CRLF 混用（`CRLF 数` 要么 0、要么等于 `LF 数`）。
     防的是「往 CRLF 文件里追加了几行 LF」这种局部改写，比整档统一更隐蔽。

为什么不钉更响的那句「content/**/*.yaml 零 CR 字符」（l922-04 实测后放弃，三条硬证据）：
  1. **转换对版本库是零收益**：本仓 `core.autocrlf=true` 且无 `.gitattributes`，24 个 CRLF 文件的
     HEAD blob 本就是 LF——`git hash-object` 与 `git rev-parse HEAD:<path>` 24/24 相同，`git diff` 零行。
     盘上那 24 个 CRLF 是 git **检出时自己写的**（`git checkout -- <file>` 实测原样退回 CRLF）。
  2. **钉「零 CR」会立刻撞他单锚定的字节证据链**：`tests/test_mark_r_judge_plain.py:589`
     `test_真题库_run题现状字节_等于原文加恰一行judge_mode_run` 把 r/ 现状字节钉成
     「pre-D6 备份字节 + 恰一行」（备份在 `data/backups/content-20260920-133722/`，按 manifest 的 sha256 复核）。
     把 r/ 16 个文件转成 LF 后该例即红（报错 diff：`At index 19 diff: b'\\n' != b'\\r'`），全量从 566 passed 变 1 failed。
     判分内容族的字节基线不属本单权限，故转换已按 sha256 逐文件回滚（24/24 与转换前逐字节一致）。
  3. 真要统一 LF，得先落 `.gitattributes`（`*.yaml text eol=lf` + `git add --renormalize content/`）
     并**同步重建**上面那条备份基线，属仓库级策略 + r-judge 族联动，留日间定夺（见 l922-04 result 遗留 1）。

只读扫描，零写盘零源码零题库改动。
"""
import glob
import os

_CR = b"\r"
_CRLF = b"\r\n"
_LF = b"\n"


def test_content_yaml_无孤立CR且文件内行尾自洽():
    files = [f.replace(os.sep, "/") for f in sorted(glob.glob("content/**/*.yaml", recursive=True))]
    assert files, "一条 yaml 都没扫到——空循环会让本例假绿"

    lone_cr = []   # ① 裸 CR
    mixed = []     # ② 同文件内 LF 与 CRLF 混用
    for p in files:
        raw = open(p, "rb").read()
        cr = raw.count(_CR)
        crlf = raw.count(_CRLF)
        lf = raw.count(_LF)
        if cr != crlf:
            lone_cr.append("%s: 裸CR=%d CRLF=%d" % (p, cr - crlf, crlf))
        if crlf and crlf != lf:
            mixed.append("%s: LF=%d 而 CRLF=%d（同档混用）" % (p, lf, crlf))
    assert not lone_cr, "content/**/*.yaml 出现不跟 LF 的裸 CR（应为 0）：%s" % "; ".join(lone_cr[:8])
    assert not mixed, (
        "content/**/*.yaml 单文件内行尾混用（应整档统一）：%s" % "; ".join(mixed[:8])
    )
