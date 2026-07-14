# Statsmodels 统计建模

Statsmodels 是 Python 的统计建模库，擅长做**传统统计推断**：回归分析、假设检验、置信区间。和 scikit-learn 的区别是：sklearn 侧重预测，statsmodels 侧重解释。

## 线性回归示例

```python
import statsmodels.api as sm
import numpy as np

# 自变量（加常数项）
X = sm.add_constant([1, 2, 3, 4, 5])
# 因变量
y = [2.1, 4.0, 5.8, 8.1, 9.9]

# 拟合 OLS 回归
model = sm.OLS(y, X).fit()

# 查看结果
print(model.params)      # 截距和斜率
print(model.rsquared)    # R²
print(model.summary())   # 完整报告
```

## 关键输出解读

| 指标 | 含义 | 好的标准 |
|------|------|---------|
| R² | 模型解释了多少变异 | 越接近 1 越好 |
| coef | 回归系数 | 每增加 1 单位 X，Y 变多少 |
| P>|t| | p 值 | <0.05 表示显著 |
| [0.025, 0.975] | 95% 置信区间 | 不含 0 则显著 |

## 何时用 Statsmodels？

- 需要 p 值、置信区间、系数显著性检验
- 论文/报告要求统计推断
- 想了解变量之间的因果关系方向
