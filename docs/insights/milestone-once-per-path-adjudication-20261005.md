# milestone 事件 once-per-path 语义裁决材料（l1002-39，只读零改码）

- 时点：2026-10-05（exec-shift-20261003-manual）

## 一、现值（完成标准①，复现 SQL/脚本内联）

`ui/pages/path.py:219-225 _emit_milestone_completed`：幂等键 `milestone_done:{path_id}:{milestone_id}`（**含 path_id**）⇒ 同一 milestone 在不同 path 下**各发一次** `path_milestone_completed`；docstring（:207 `_emit_path_started` 同区）写 "once per path" 与该键形态自洽，但矿源点名的语义歧义在「跨路径共享 milestone 是否应只发一次」。

**共享专题现值**（l922-07 复用 10 个复现成立）：
- 被引用专题 85 个，其中 **10 个被 ≥2 条路径共享**（python 基础 5 个被 agent_mastery/people_analytics 双引；r 族 5 个被 people_analytics/quick_stats 双引或三引，r/05_lm_anova、r/06_mixed_apa 达 3 条路径）。
- **跨路径双发候选 = 10 个共享专题**所属的 milestone 事件（用户走任一路径完成该里程碑即各发一次）。

## 二、两案对照（完成标准②）

| 案 | 键形态 | 事件库影响 |
|---|---|---|
| **A：跨路径唯一**（键去 milestone_id：`milestone_done:{milestone_id}`） | 全局首达即发 | 事件库少收「同 milestone 跨路径」的重复完成事件（现值最多 10 个专题、约涉及 5-6 个 milestone 对）；副作用：**path 维度完成率统计失真**（走 B 路径再遇已发过的 milestone 不再记事件，path 自己的「里程碑完成」账缺行）；meta 表键少 path 维度后**不可区分哪条路径先完成** |
| **B：维持现状**（键含 path_id，once per **(path, milestone)**） | 每路径独立记账 | 事件库按路径独立完整（path 维度统计自洽）；共享专题用户走两条线会各见一次「milestone 完成」——产品视角是「两条线各自毕业」还是「重复庆祝」，属产品语义裁决 |

**docstring 措辞修正建议**（不改码时的最小动作）：`_emit_milestone_completed` docstring 补一句「once per (path, milestone)——跨路径共享 milestone 会各发一次（l1002-39 裁决材料在案），非 docstring 泛指的 once per path」。`_emit_path_started` 的 "once per path" 本身准确（键确实只有 path_id），无需动。

## 三、零改码声明

全程只读（yaml/yml 加载、path.py 摘录）；路径结构零改动。
