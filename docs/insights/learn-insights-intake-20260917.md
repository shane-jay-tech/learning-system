# learning docs/insights 未入库报告收口（916p-a3-017，2026-09-17）

## 数字（命令与输出同段）

```
$ ls docs/insights/*.md | wc -l → 27 份（任务书快照 21；差异=本夜新增 6 份）
$ git status --porcelain docs/insights（提交前）→ 20 行 ??（任务书 17 为撰写时点；+3=本夜 a3-014/015/016 报告）
```

## 归属表（20 份；mtime 实测，均 ≤9/16 无在写风险）

| 批次 | 份数 | 文件 |
|---|---|---|
| 9/13 工效/视觉批 | 12 | learning-breakpoint-constant / dashboard-density / empty-caption-tokens / empty-state / ergo-diag-path-1366 / error-feedback / focus-visible / line-length / narrow-sidebar / nav-current-item（各 20260913）＋ silent-except-batch2 / weekly-card-note |
| 9/14-15 基线批 | 3 | learning-empty-caption-tokens-20260914、learn-bank-cadence-20260915、learn-sidebar-218-20260915、learn-tests-baseline-20260915（n915-77） |
| 9/16-17 判分/对账批 | 5 | learn-judge-edges-20260916、learn-skipped-audit-20260916、learn-coverage-reconcile-20260917、learn-dashboard-coverage-20260917、learn-verify-commands-audit-20260917 |

## 提交与复验

```
$ git commit → 20 files changed, 638 insertions(+)
$ git status --porcelain docs/insights → 空 ✓
$ python -m pytest tests -q → 384 passed, 7 skipped（与提交前一致）
```

## 验收对照

- ✅ 两数字同段（27 份总量／20 行未跟踪）。
- ✅ 归属表 20 行=未跟踪行数，含 mtime 判定（无晚于本单开始时间的份）。
- ✅ git log -1 --stat＝20 份入库。
- ✅ 提交后 docs/insights 干净；逐份列路径 add，无 -A/-u/.；不 push。
