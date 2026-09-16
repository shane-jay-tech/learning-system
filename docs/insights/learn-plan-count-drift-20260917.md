# learning plan.md 验收数字订正（916p-a3-011，2026-09-17）

## 实测（命令与数字同段）

```
$ python -m pytest tests -q
376 passed, 7 skipped in 32.29s
（SKIPPED[1] test_r_runner.py:25 Rscript not available）
```

## 数字链（3 行）

| 数字 | 来源 | 说明 |
|---|---|---|
| 304 passed | plan.md:33（旧值） | 侧栏改造验收时点（d913c-12 前后） |
| 368 passed / 7 skipped | docs/insights/learn-sidebar-218-20260915.md:11/21；learn-skipped-audit-20260916.md:10 | 9/15 侧栏 218px 修复后基线 |
| 376 passed / 7 skipped | docs/insights/learn-judge-edges-20260916.md:25＋本次实测 | l916-02 judge-extend 后现值 |

## 订正

plan.md:33「304 passed，7 skipped」→「376 passed，7 skipped」＋补实测命令与口径说明（pytest 非 unittest discover；2026-09-17 复核）。rg -n "304 passed" plan.md → 输出为空 ✓。

## 提交

git log -1 --stat：仅 plan.md 一文件。不 push。
