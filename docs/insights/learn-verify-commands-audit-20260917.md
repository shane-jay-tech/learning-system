# learning README「验证」节 8 条命令可用性核验（916p-a3-013，2026-09-17）

## 汇总表（8/8，命令与退出码同段）

| # | 命令 | 退出码 | 关键输出 | 联网/介入 | README 描述准确 |
|---|---|---|---|---|---|
| 1 | pytest | 0 | 376 passed, 7 skipped in 29.44s | 否 | ✓ |
| 2 | python scripts/health_check.py | 0 | learning-system health check… | 否 | ✓ |
| 3 | python scripts/smoke_boot.py | 0 | health ready: True (4.2s) | 否 | ✓ |
| 4 | python scripts/perf_baseline.py | 0 | === Performance Baseline (5x+1 warmup) === | 否 | ✓ |
| 5 | python scripts/audit_content.py | 0 | PASS: 0 errors, 4 accepted, 0 warnings | 否 | ✓ |
| 6 | python scripts/backup_data.py（写入型，仅 --help） | 0 | usage: [--list] [--restore ZIP] [--keep KEEP]；Backup/restore progress.db | 写入型未实跑 | ✓（描述准确） |
| 7 | python scripts/prune_old_data.py（写入型，仅 --help） | 0 | usage: [--days DAYS] [--keep-per-problem] [--apply] [--json] | 写入型未实跑 | ✓ |
| 8 | python scripts/generate_system_report.py | 0 | === 学习平台系统指标 (v0.6.5, 2026-08-15) === | 否 | ✓ |

## 副作用核验

```
$ git status --porcelain data/ → 空（0 行）✓
$ git status --porcelain 全文 → 仅开工前既有的 M 文件（app.py/core/*.py 等 9/13 时代在途改动），无新增
```

## 结论

**README「验证」节无需订正**：8 条命令全部 exit 0、描述与实际行为一致、无联网要求、无人介入项（0 条）；写入型两条（backup/prune）经 --help 确认参数面后未实跑，符合保守口径。本单不改 README。

## 验收对照

- ✅ 汇总表 8 行，命令与退出码同段。
- ✅ data/ 跑后为空同段。
- ✅ 联网/介入判定：0 条（明确写出）。
- ✅ 结论句明确：无需订正＋依据。
