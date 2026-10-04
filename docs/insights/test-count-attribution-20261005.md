# 测试用例数权威口径归因报告（l1002-80，只读零改码）

- 时点：2026-10-05（exec-shift-20261003-manual）；全部 pytest 读数带 **PYTHONUTF8=1**（矿内明令）
- 矿源：l924-28 遗留（865 vs 947 差 82 未归因）＋l923-25 双口径（762/802）并入对照

## 一、四口径现值（完成标准①）

| 口径 | 命令 | 现值 |
|---|---|---|
| 正则·report 默认 | `generate_system_report.py count_tests()`（`^\s*def test_` × `tests/test_*.py` glob） | **1136** |
| 正则·rg 全 tests/ | `rg -c "^\s*def test_" tests/`（含非 test_ 前缀件） | 1136 行（`-o` 唯一名 1125——同名函数 11 处跨/内文件） |
| **pytest 收集（--strict）** | `PYTHONUTF8=1 python -m pytest tests/ --collect-only -q` | **1265 collected**（1.17s） |
| 历史 | l923-25（9/23）762/802；l924-28（9/24）865/947 | 已涨 +374/+318（后续批次加例） |

## 二、差额分解（1265 − 1136 = 129，完成标准②）

| 构成 | 量级 | 证据 |
|---|---|---|
| **parametrize 展开** | 主项（带 `[` 的收集条目 **177** 条，来自 22 文件/48 装饰器） | 展开大头：test_每个定义id都出现在解锁面源码里 ×22、test_branch_matches_condition ×10、test_module_syntax_variants ×8、连续天数重置 ×7… |
| 类内方法与同名函数 | 正则行 1136 vs 唯一名 1125（差 11＝跨文件同名） | rg -o 去重口径 |
| 非 `test_*.py` glob 文件 | rg 全 tests/ 与 report glob 差 ≈2 行 | conftest/helper 形态件 |
| 条件 skip | 收集期**不剔除**（skip 只影响运行态） | 0 贡献 |

**构成百分比**：正则可数 1136（89.8%）＋ 参数化/结构展开净增 129（10.2%）。历史 82 差额（865→947）与此同构（当时 parametrize 面更小），现值差额放大到 129 是后续批（l1002-11/16/19 等）大量使用 parametrize 所致。

## 三、「权威口径=pytest 收集」落地方案（完成标准③，零改码）

1. `generate_system_report.py:99 count_tests()`：默认路径改 `strict=True`（实现已在，仅翻转默认）——代价：报告生成从瞬时变 **+1.17s**。
2. `check_report`（:167）与 `--check` 链自动跟随（同一 count_tests 出口）。
3. 快照断言影响面：`docs/system-report-v0.6.5.md:25`（「802 个」行）与 `tests/` 内所有 `== 数字` 用例数断言须同批刷成 1265 系——**逐件 rg "802\|865\|947\|1136" docs/ tests/**（改造时一次性）。
4. 漂移敏感度警示：pytest 收集数随「加例/parametrize 展开」漂，权威口径上收后**每次加例都会动 report 数字**——check_report 对该字段的容差（±N 或只增不减）建议同批裁决。

## 四、零改码声明

`generate_system_report.py`、tests/、docs 快照零触碰；两模式实跑为只读。
