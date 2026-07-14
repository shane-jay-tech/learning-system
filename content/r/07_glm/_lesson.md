# GLM：广义线性模型

## 这一节学什么

`lm()` 处理的是**连续的数值因变量**——比如预测工资。但很多实际问题的因变量是**类别**：
- 员工**会不会**离职（0/1）—— 二分类
- 员工**得几次**警告（0, 1, 2, 3...）—— 计数

这种情况要用 **GLM（广义线性模型）**：

```r
fit <- glm(y ~ x, data = df, family = binomial)   # 逻辑回归
fit <- glm(y ~ x, data = df, family = poisson)     # 泊松回归
```

`family` 决定 GLM 的"类型"。

## 逻辑回归（最常用）

预测员工是否离职：

```r
df <- data.frame(
  leave = c(0, 1, 0, 1, 0, 1, 0, 1),    # 是否离职（0/1）
  years = c(10, 1, 8, 2, 7, 1, 9, 2)     # 工龄
)
fit <- glm(leave ~ years, data = df, family = binomial)
summary(fit)
```

输出系数（log odds）：负系数表示 years 越长越不离职。

## 提取关键数字

```r
coef(fit)                # 系数（log odds 尺度）
exp(coef(fit))            # 转 odds ratio（OR）—— 业务可读
confint(fit)              # 置信区间
predict(fit, type = "response")   # 预测概率（0-1）
```

`exp(coef)` 给出 **OR**——比如 OR = 0.5 表示"x 每增加 1，离职几率变成原来的一半"。这是论文标准报告。

## family 速查

| 因变量 | family | 用途 |
|---|---|---|
| 0/1 二分类 | `binomial` | 离职/通过/购买 |
| 计数（≥0 整数） | `poisson` | 缺勤次数、警告次数 |
| 连续（正太） | `gaussian`（=lm） | 等价于 lm |
| 比例（0-1 连续） | `quasibinomial` | 满意度评分 |

## 模型评估：AIC 与 deviance

```r
AIC(fit)               # 越小越好（信息准则）
fit$deviance           # 残差偏差（越小越好）
fit$null.deviance       # 空模型偏差
```

R² 在 GLM 不如 lm 直接——用 **McFadden's pseudo-R²**：

```r
1 - fit$deviance / fit$null.deviance   # 0-1，越高越好
```

## 多变量 + 类别预测变量

```r
fit <- glm(leave ~ years + age + gender + dept, data = df, family = binomial)
```

R 自动把 factor 列编成虚拟变量。

## 预测新数据

```r
new_df <- data.frame(years = c(3, 8))
predict(fit, new_df, type = "response")   # 概率
predict(fit, new_df, type = "link")       # log odds（默认）
```

`type = "response"` 给概率（0-1），`type = "link"` 给 logit。

## 常见错误

1. **忘 family**：`glm(y ~ x)` 默认 `gaussian`（等于 lm），二分类会出大错
2. **二分类 y 不是 0/1 或 factor**：必须是 0/1 或者 2 个水平的 factor
3. **OR 没 exp**：报告时给 `coef` 而非 `exp(coef)` —— 业务读不懂
4. **小样本下 GLM 收敛失败**：完美分离时模型给警告——加正则化或简化模型

## 现在做练习

5 道题：逻辑回归系数、OR、AIC、预测概率、McFadden's R²。
