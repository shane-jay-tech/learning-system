# learning 仓 unittest 发现计数基线（n915-77，只读）

- 任务：n915-77-learn-tests-discovery（created 2026-09-15T23:39:01，软预算 ≤20 分钟）
- 执行：sweep-20260915-2300（GLM-5.3-Flash），2026-09-16 03:1x

## 一、实跑（先命令后数字）

```
python -m unittest discover -s tests -p "test_*.py"
→ Ran 0 tests in 0.000s / NO TESTS RAN
```

原因：本仓测试为 **pytest 风格函数用例**（无 unittest.TestCase），unittest discover 口径天然为 0——非缺陷；基线口径应使用 `python -m pytest tests -q`。

## 二、基线表（来源 / passed / skipped / 日期）

| 来源 | passed | skipped | 日期 |
|---|---:|---:|---|
| d914-67 result（learn-portability-test） | 364 | 7 | 2026-09-14 |
| d914-68 result（learn-achievements-test） | 368 | 7 | 2026-09-14 |
| 本班 n915-66 实跑（pytest tests -q） | **368** | **7** | 2026-09-16 |

（3 行 ≥3 ✓；全量口径 pytest 稳定在 368+7。）

## 三、声明

未改测试文件；不 push。

## 遗留问题

无（unittest 口径 0 为形态差异，建议例行基线统一用 pytest 口径）。
