# 生存分析（survival）

## 生存分析在 PA 里的用法

PA 里 **"留任时间"** 是核心问题——员工平均待多久？什么因素让人离职更快？

普通 `lm` 处理不好这种问题，因为：
- 数据有 **审查（censoring）**：分析时还在职的人"还没观察完"
- 输出的不是"是否离职"，是"多久离职"

**生存分析** 专门处理这种数据。R 用 `survival` 包。

```r
library(survival)
```

## Surv() 对象：生存数据的格式

```r
df <- data.frame(
  time = c(12, 24, 8, 36, 5, 18),       # 留任月数
  event = c(1, 0, 1, 0, 1, 1)            # 1=离职, 0=审查（还在职）
)

s <- Surv(df$time, df$event)
print(s)
# 12   24+   8  36+   5  18
# +号表示审查（数据没结束）
```

## Kaplan-Meier 曲线

最经典的生存分析输出——画"在某时点还有多少人留着"：

```r
fit <- survfit(Surv(time, event) ~ 1, data = df)
summary(fit)
plot(fit)
```

`~ 1` 表示不分组（整体）。要分组比较：

```r
fit <- survfit(Surv(time, event) ~ dept, data = df)
plot(fit, col = c("red","blue"))
```

## Log-rank 检验：两组生存曲线是否不同

```r
test <- survdiff(Surv(time, event) ~ dept, data = df)
# 输出 chi-square 和 p
```

## Cox 比例风险模型（最常用）

```r
fit <- coxph(Surv(time, event) ~ years + age + dept, data = df)
summary(fit)
```

输出 **HR（hazard ratio）**：HR=1.5 表示该变量每增加 1 单位，离职**风险**增加 50%。

```r
exp(coef(fit))     # HR
confint(fit)        # 系数置信区间（log HR）
```

## 中位生存时间

```r
fit <- survfit(Surv(time, event) ~ 1, data = df)
summary(fit)$table     # 包含 median 等
```

## 实战：HR 解读

| HR | 意义 |
|---|---|
| HR > 1 | 风险增加（更易离职） |
| HR = 1 | 无影响 |
| HR < 1 | 风险降低（保护因子） |

## 常见错误

1. **event 写反**：1 通常是事件发生（离职），0 是审查；写反结果完全相反
2. **time 含 0 或负数**：survival 不接受
3. **Cox 假设违反**：比例风险假设要求 HR 不随时间变（用 `cox.zph` 检查）
4. **多变量共线性**：变量互相高相关时 HR 估计不稳

## 现在做练习

5 道题：构造 Surv 对象、survfit 中位数、log-rank 检验 p 值、Cox 模型 HR、Cox 多变量。
