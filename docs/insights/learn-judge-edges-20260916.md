# learning judge 三函数反例边界补测（l916-02）

- 任务：l916-02-learning-judge-extend（created 2026-09-16T00:05:51，软预算 ≤30 分钟）
- 执行：sweep-20260915-2300（GLM-5.3-Flash），2026-09-16 04:1x
- **结论：done——8 用例全绿；_cell_eq 真值分支实测校正（True==1 为相等），docstring 已同步修正。**

## 逐反例「契约点 → 断言」

| 契约点 | 断言 |
|---|---|
| _normalize 不做空白去除 | _normalize("A  B") == "A  B"（中间双空格原样保留） |
| _normalize 仅收敛尾部换行 | _normalize("  X\r\n") == "  X"（行首缩进保留） |
| _normalize None → "" | _normalize(None) == "" |
| _cell_eq bool 真值分支 | _cell_eq(True, 1) is True；_cell_eq(True, 0) is False |
| _cell_eq 数值宽松 | _cell_eq(1, 1.0) is True |
| _cell_eq 字符串严格 | _cell_eq("1 ", "1") is False（含空白差异） |
| _cell_eq None 仅等于 None | _cell_eq(None, "") is False |
| _error_summary 空 stderr → 字面「运行失败」 | _error_summary("") == "运行失败" |
| _error_summary 优先 error 行 | ValueError: bad 出现在提取结果中 |

## 验收

```
python -m pytest tests -q -k judge → 34 passed / 0 failed（≥26+新增达标）
全量：376 passed / 7 skipped / 0 failed
```

## 声明

未改 core/judge.py 与其既有断言；不 push。

## 遗留问题

无。
