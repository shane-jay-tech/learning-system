# 混合效应模型 + APA 报告 + 效应量

## 这一节学什么

People Analytics 论文里你会看到的高级统计：

1. **混合效应模型** `lme4::lmer()` —— 处理嵌套数据（员工 in 部门）
2. **效应量** `effectsize::cohens_d()` —— 不光看 p 值还要看效应大小
3. **APA 格式报告** —— 论文标准化

## 混合效应模型（lme4）

经典场景：你有 100 个员工分布在 10 个部门——员工的绩效**不仅受个人影响，还受部门影响**。普通 lm 假定独立同分布，会高估"显著性"。

```r
library(lme4)

# 固定效应：years 影响绩效
# 随机效应：部门有自己的"基线"
model <- lmer(score ~ years + (1 | dept), data = df)
summary(model)
```

公式 `(1 | dept)` 读作 "每个 dept 自己一个截距（随机变化的基线）"。

## 提关键数字

```r
fixef(model)     # 固定效应系数
ranef(model)     # 随机效应（每个 dept 的偏差）
VarCorr(model)   # 随机效应的方差结构
```

## 效应量：报告时**必给**

p 值告诉你"是否显著"，**效应量**告诉你"差距多大"。

### Cohen's d（两组均值差）

```r
library(effectsize)
cohens_d(score ~ class, data = df_two_groups)
# 经验：|d|≈0.2 小、0.5 中、0.8 大
```

### eta²（ANOVA 的效应量）

```r
library(effectsize)
fit <- aov(score ~ class, data = df)
eta_squared(fit)
# η² < 0.06 小、< 0.14 中、≥ 0.14 大
```

### r²（回归的效应量）

直接 `summary(lm(...))$r.squared` 即可——R² 本身就是效应量。

## broom 包：把模型结果变成 tidy 数据框

```r
library(broom)
fit <- lm(y ~ x, data = df)
tidy(fit)        # 系数表（数据框）
glance(fit)      # 模型水平统计（R² 等）
augment(fit)     # 原数据 + 拟合值 + 残差
```

特别适合配合 dplyr/ggplot2 做"批量建模"。

## APA 格式报告

期刊要求一致。t 检验：

> 培训组（M = 78.5, SD = 6.2）显著高于对照组（M = 65.0, SD = 7.5），t(18) = 4.72, p < .001, d = 1.95。

线性回归：

> 工龄显著正向预测工资，b = 1000.5, SE = 45.2, t(98) = 22.13, p < .001。模型解释了 84.5% 的方差，R² = .845。

ANOVA：

> 三个班分数差异显著，F(2, 12) = 22.4, p < .001, η² = .79。

## 报告时的 4 个数字

无论什么检验，APA 风格至少给 4 个数字：

1. **检验统计量**（t / F / χ² / r）
2. **自由度**（df 或 (df1, df2)）
3. **p 值**
4. **效应量**

少了任何一个，审稿人会让你补。

## 常见错误

1. **混合效应却用 lm**：观测不独立时 p 值被低估，假阳性高
2. **报告只给 p 没给效应量**：审稿人最常 reject 理由之一
3. **lme4 不存在 p 值**：lme4 故意不给 p（理论原因）；要 p 用 `lmerTest` 包
4. **factor 没设参照水平**：哪个类别是基线很重要——影响系数解读

## 现在做练习

5 道题：lmer 固定效应、tidy 提系数、Cohen's d、eta²、APA 风格 t 报告。
