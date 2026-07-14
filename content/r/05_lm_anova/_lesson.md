# R 线性模型与方差分析

## 这一节学什么

R 在统计建模上**比 Python 更强**——它从一开始就为做研究设计。本节讲两件 People Analytics 必备工具：

1. **lm()**：线性回归——预测 + 解释
2. **aov() / anova()**：方差分析（ANOVA）——比较多组均值

## 第一个回归：lm()

```r
df <- data.frame(
  x = c(1, 2, 3, 4, 5),
  y = c(2, 4, 5, 4, 6)
)
model <- lm(y ~ x, data = df)
summary(model)
```

`y ~ x` 读作 "y 由 x 解释"，是 R 的 **公式语法**。

`summary(model)` 输出一张完整报告：每个系数、p 值、R²、F 检验……论文级。

## 取出关键结果

```r
coef(model)            # 系数（截距 + 斜率）
confint(model)         # 95% 置信区间
predict(model, new)    # 预测
fitted(model)          # 训练集拟合值
resid(model)           # 残差
```

## 多元回归：多个自变量

```r
model <- lm(salary ~ years + age + gender, data = hr_df)
summary(model)
```

公式中用 `+` 加多个变量；`*` 表示交互项；`-1` 表示去掉截距。

## ANOVA（方差分析）

"3 个班的成绩有显著差异吗？"——用 ANOVA：

```r
df <- data.frame(
  score = c(85, 92, 78, 88, 95, 70, 72, 65, 60, 55, 80, 82, 78, 85, 90),
  class = factor(rep(c("A", "B", "C"), each = 5))
)
aov_res <- aov(score ~ class, data = df)
summary(aov_res)
```

输出会给你 **F 值** 和 **p 值**——p<0.05 表示**至少有两个班存在差异**（具体哪两个要再做事后检验）。

## 事后检验（post-hoc）

ANOVA 显著后想知道**到底是哪两组不一样**：

```r
TukeyHSD(aov_res)
```

Tukey 给所有两两比较的差异和 p 值。

## factor 是关键

R 会自动把字符列当作 character，但建模时要变 **factor**——告诉 R "这是分类变量，不是连续值"。

```r
df$class <- factor(df$class)         # 把 class 转成因子
df$class <- factor(df$class,
                   levels = c("C", "A", "B"))   # 设定参照水平和顺序
```

参照水平就是回归中的"基线"（其它水平和它比较）。

## 解读 lm 输出

```
Call:
lm(formula = y ~ x, data = df)

Coefficients:
            Estimate Std. Error t value Pr(>|t|)
(Intercept)   1.5     0.6        2.5     0.04 *
x             1.2     0.2        6.0     0.005 **

R-squared: 0.85, F-statistic p-value: 0.005
```

读法：
- `Estimate`：系数（x 每加 1，y 平均加 1.2）
- `Pr(>|t|)`：每个系数的 p 值
- `R-squared`：模型解释了 85% 的 y 方差
- `F-statistic p-value`：整个模型显著吗

## 常见错误

1. **分类变量没转 factor**：R 把它当连续数值，建模错误
2. **`~` 和 `=` 混淆**：公式用 `~` 不用 `=`
3. **缺失值处理**：含 NA 时 lm 默认丢行；要 `na.action = na.omit`
4. **多重共线性**：自变量互相高相关时系数会乱跳；先 `cor()` 检查相关矩阵

## 现在做练习

5 道题：lm 系数、R²、ANOVA p 值、TukeyHSD、多元回归。
