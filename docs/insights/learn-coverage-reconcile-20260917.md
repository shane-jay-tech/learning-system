# learning 覆盖率三口径对账（916p-a3-014，2026-09-17，只读）

## 三口径表（3 行，含 mtime）

| 来源 | mtime | percent | num_statements |
|---|---|---|---|
| .coverage-baseline.json（7/14 基线） | 2026-07-14 12:37 | **37%** | 3169 |
| .coverage-after.json（7/14 改造后） | 2026-07-14 12:56 | **70%** | 3387 |
| .coverage（当前实测，2026-09-16 20:51） | 2026-09-16 20:51 | **77%** | 4327 |

当前口径实测命令与数字同段：

```
$ python -m pytest tests -q --cov --cov-report=term 2>&1 | grep -E '^TOTAL|passed'
TOTAL                                4327    934   1552    175    77%
376 passed, 7 skipped in 35.24s
```

两 json 逐份（命令与数字同段）：

```
$ python -c "…percent_covered_display / num_statements…"
.coverage-baseline.json 37 3169
.coverage-after.json 70 3387
```

## 语句基数差异解释（3169→3387→4327）

- 3169→3387（+218）：7/14 当天基线→改造后，源码增长（新功能模块）；
- 3387→4327（+940）：7/14 之后近两个月的批次开发（侧栏 218px、判分边界、judge-extend 等多批新增模块与页面），源码自然增长为主——统计口径三份一致（.coveragerc source=. / branch / omit 未变，:7/14 与当前共 3 份文件均受同一 .coveragerc 约束），故差异主要不是口径而是代码量。

## 结论

- **基线文件应刷新**：37% 基线绑定的 3169 语句基数已严重过时（现 4327），「较基线提升」类比较已失真；
- **以当前实测为准**：77%（4327 语句 / 934 未覆盖 / 1552 分支部分覆盖），它反映 2026-09-16 的真实代码面；
- 刷新命令（只给不执行）：`python -m coverage json -o .coverage-baseline.json`（在当前 --cov 运行产物上导出，或重跑 `python -m pytest tests -q --cov --cov-report=json:.coverage-baseline.json`），建议同时在 PLAN/README 标注新基线日期。

## 验收对照

- ✅ 当前口径命令与 TOTAL 行数字同段（4327/77%）。
- ✅ 两 json percent 与 num_statements 逐份贴出（37/3169、70/3387）。
- ✅ 三口径表 3 行含 mtime。
- ✅ 结论句明确（应刷新＋以当前实测为准＋刷新命令一行）。
