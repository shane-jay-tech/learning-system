# learning insights 索引与未引用清单核对（r917-20，p917-20 重投）

- 生成时间：2026-09-20T12:46:06+08:00
- **20 这个数已复跑并订正**：当刻实测 **43**。

## 一、当刻份数与前缀分布（命令与数字同段）

命令：
```
Get-ChildItem 'docs\insights' -Filter '*.md' | Measure-Object | Select-Object -ExpandProperty Count
```
输出：
```
43
```
命令：
```
(Get-ChildItem 'docs\insights' -Filter 'learn-*.md' | Measure-Object).Count     → 24
(Get-ChildItem 'docs\insights' -Filter 'learning-*.md' | Measure-Object).Count  → 14
```
**两套前缀纳入口径 = 都纳入**：24 + 14 = 38；另 5 份为无前缀/其它前缀（`agent-dev-rubric-review-20260905.md»、`content-id-conflict-04-functions-20260919.md»、`content-quality-sample-20260905.md»、`silent-except-batch2-20260913.md»、`weekly-card-note-20260913.md»）。
**38 + 5 = 43 ✅ == 总份数。**
mtime 分布：早期批次 9/05–9/16，密集批 9/17–9/19（对应 `7088f7b» 的 "20 份成批入库" 与后续夜班产出）。

## 二、索引表

命令（只读扫描）：
```
python zcode-bridge/tmp/r917-verify/refscan.py learning-system
```
输出（头部）：
```
repo= learning-system
total= 43
cited= 2
uncited= 41
sum_check= 43
```

| 项 | 值 |
|---|---|
| 总份数 | **43** |
| 被引用 | **2** |
| 未引用 | **41** |
| 相加校验 | **2 + 41 = 43 == 43 ✅** |
| mtime 区间 | 2026-09-05 ~ 2026-09-19 |

## 三、与 `7088f7b»（20 份）的对照

| 项 | 7088f7b | 当刻 | 归因 |
|---|---|---|---|
| 份数 | 20 | **43** | 9/18–9/19 又落 23 份（`learn-*.md» 批量） |
| 前缀 | 未区分 | `learn-*»=24 / `learning-*»=14 / 其它=5 | 两套命名并存 |

## 四、未引用项判定（41 份）

- **挂接候选（0 份）**：41 份的名称均**未**出现在仓内任何非 insights 文件中；且均为夜班一次性「扫描/清点/对账」型产出（如 `learn-uncommitted-inventory-20260917.md»、`learning-metrics-recheck-20260917.md»），消费方是当夜规划文档。
- **独立存档（41 份）**：理由统一——**内容为时点快照**（清点/对账/覆盖率实测），不具长期常驻文档价值；`plan.md» 只登记计划项，强挂会让它臃肿。**逐份列表**由 §二 命令的 `U» 行完整输出（41 行）。

**两数相加 = 2 + 41 = 43 == 总份数 ✅**

## 五、未修改 plan.md / README.md 的证明

本单全程只读，**未对 `plan.md» / `README.md» 发起任何写调用**；唯一写入为新增本报告文件。

## 六、遗留

1. 41 份未引用属设计结果（时点快照型），若产品期望提高挂接率需另定口径。
2. 两套前缀（`learn-*»/`learning-*»）并存已如实统计，**未做统一改名**（改名会破坏既有引用）。
