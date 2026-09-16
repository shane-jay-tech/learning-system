# learning 3 个未跟踪测试文件入库收口（916p-a3-016，2026-09-17）

## 提交前（git status --porcelain tests/ 原文）

```
 M tests/test_ergo_h912_13.py          ← 班前既有 M（非本单范围）
 M tests/test_ui_behavior.py           ← 班前既有 M
?? tests/test_achievements_branches.py
?? tests/test_data_portability_guards.py
?? tests/test_judge_pure.py
```

## 提交（bdcf116）

```
$ git add tests/test_achievements_branches.py tests/test_data_portability_guards.py tests/test_judge_pure.py
$ git commit → test: 3 个未跟踪测试文件入库收口（3 文件）
$ git status --porcelain tests/ → 仅剩 2 行班前既有 M（无 ??）✓
```

## 全量前后对比（命令与数字同段）

```
提交前：python -m pytest tests -q → 384 passed, 7 skipped（本班 a3-015 交付后口径）
提交后：python -m pytest tests -q → 384 passed, 7 skipped    （零变化 ✓；任务书 376 为其撰写时点，差异=本夜 a3-015 等 +8）
```

## 验收对照

- ✅ 提交前三行 ??、提交后 tests/ 无 ??（两次输出同段）。
- ✅ 前后 pytest 数字一致（384 passed/7 skipped/0 failed）。
- ✅ git log -1 --stat 列出 3 个文件。
- ✅ 未 add docs/insights 与源码；无 -A/-u/.；不 push。
