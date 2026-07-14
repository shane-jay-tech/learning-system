# 结构方程模型（SEM）基础

SEM 是心理学研究的核心方法之一，能同时处理测量误差和变量间因果关系。

## 为什么重要

心理学的核心构念（工作满意度、组织承诺、心理资本）无法直接测量，必须通过多个题目间接推断。SEM 把这个过程形式化：测量模型（题目→潜变量）+ 结构模型（潜变量间关系）一步到位。

## 核心概念

- **潜变量**：不可直接测量的构念，用多个可观测指标推断
- **路径分析**：变量间因果/预测关系的数学表达
- **模型拟合指标**：CFI > 0.90、RMSEA < 0.08、SRMR < 0.08
- **lavaan 语法**：`=~` 定义测量、`~` 定义回归、`~~` 定义协方差

## 最小示例

```r
library(lavaan)
model <- '
  satisfaction =~ s1 + s2 + s3
  commitment =~ c1 + c2 + c3
  commitment ~ satisfaction
'
fit <- sem(model, data = mydata)
summary(fit, fit.measures = TRUE, standardized = TRUE)
```

## 建模流程

1. 画理论模型图（哪些变量影响哪些）
2. 翻译成 lavaan 语法
3. 拟合模型 `sem()`
4. 看拟合指标（CFI / TLI / RMSEA / SRMR）
5. 看路径系数和显著性

## 常见错误

- 样本量太小（SEM 通常需要 N > 200）
- 模型不收敛（可能是多重共线性或模型设定错误）
- 只看 p 值不看效应量和拟合指标
