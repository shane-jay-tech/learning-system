# 验证性因子分析（CFA）

CFA 检验"问卷的结构是否符合理论预期"，是量表开发和修订的必备工具。

## 为什么重要

你设计了一份量表（比如"工作倦怠问卷"），理论上分 3 个维度：情绪耗竭、去人格化、低成就感。CFA 就是用数据验证这个理论结构是否成立——题目真的归属于你预想的维度吗？

## 核心概念

- **因子载荷**：题目与潜变量的关联强度，一般要求 > 0.4
- **模型语法**：`latent_var =~ item1 + item2 + item3`
- **判断标准**：载荷显著、CFI > 0.90、RMSEA < 0.08
- **与 EFA 的区别**：EFA 是探索性的（"数据里有几个因子？"），CFA 是验证性的（"我假设有 3 个因子，数据支持吗？"）

## 最小示例

```r
library(lavaan)
cfa_model <- '
  exhaustion =~ e1 + e2 + e3 + e4
  deperson   =~ d1 + d2 + d3
  accomplish =~ a1 + a2 + a3 + a4
'
fit <- cfa(cfa_model, data = burnout_data)
summary(fit, fit.measures = TRUE, standardized = TRUE)
```

## 做题前检查

1. 数据是连续变量还是有序分类？（有序用 `ordered = TRUE`）
2. 样本量是否足够（通常 N > 200，每个因子至少 3 个指标）
3. 看标准化载荷（`standardized = TRUE`），不看非标准化的
4. 模型修正指数 `modindices(fit)` 提示哪里可以改善

## 常见错误

- 把 EFA 和 CFA 在同一批数据上做（应该拆半或用新样本）
- 载荷低于 0.4 的题目强行保留
- 过度依赖修正指数调模型（理论先行，不是数据驱动改模型）
