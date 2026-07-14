# scipy.stats：假设检验

## 这一节学什么

People Analytics 经常要回答这种问题：
- 这两组员工的绩效**真的有差异**吗？还是只是抽样波动？
- A/B 测试里转化率从 5% 涨到 6%，**显著吗**？
- 学历和绩效**有相关性**吗？

回答这些靠 **假设检验**。`scipy.stats` 是 Python 做检验的标准工具。

```python
from scipy import stats
```

## p 值是什么

每次假设检验给一个数字 **p 值**：
- p < 0.05：通常认为"差异显著"（拒绝原假设——**有差异**）
- p ≥ 0.05：差异不显著（无法拒绝原假设——**没法证明有差异**）

⚠️ **p < 0.05 不等于"100% 有差异"**——只是说"如果原假设是真的，得到这个结果的概率小于 5%"。

## t 检验：比较两组均值

最常用的检验之一：两组数据的均值是否显著不同？

```python
group_a = [85, 92, 78, 88, 95]
group_b = [72, 68, 75, 82, 70]
t_stat, p_value = stats.ttest_ind(group_a, group_b)

print(f"t={t_stat:.3f}, p={p_value:.4f}")
# t=4.218, p=0.0030 → p<0.05 显著差异
```

`ttest_ind`：独立样本 t 检验（两组独立的数据）；
`ttest_rel`：配对样本（同一批人前后测）。

## 卡方检验：分类变量

"性别和是否离职有关吗"——两个分类变量的关联：

```python
import numpy as np
# 列联表：男离职/不离职、女离职/不离职
table = np.array([[30, 70], [40, 60]])
chi2, p, dof, expected = stats.chi2_contingency(table)
print(f"卡方={chi2:.3f}, p={p:.4f}")
```

## 相关系数

"工资和绩效相关性多强"：

```python
salary = [5000, 8000, 6500, 12000, 9000]
perf = [70, 88, 75, 95, 82]
r, p = stats.pearsonr(salary, perf)
# r 接近 1：强正相关；接近 -1：强负相关；接近 0：无关
```

`pearsonr` 是皮尔逊相关；`spearmanr` 是 Spearman 秩相关（不要求线性）。

## 描述统计

```python
data = [85, 92, 78, 88, 95, 72, 68]
stats.describe(data)
# DescribeResult(nobs=7, minmax=(68, 95), mean=82.57, variance=...)
```

## 单样本检验

"这班学生平均分是否显著高于 80"：

```python
scores = [85, 92, 78, 88, 95]
t, p = stats.ttest_1samp(scores, 80)
```

## 常见错误

1. **混淆 t-test 类型**：独立用 ind，配对用 rel——选错结论可能反过来
2. **数据不正态就用 t 检验**：小样本 + 严重偏态时改用 Mann-Whitney U（`stats.mannwhitneyu`）
3. **多重比较**：5 组两两比一次（10 次 t 检验），出现 p<0.05 的概率被放大；要用 ANOVA + 事后检验
4. **p 值越小越好的迷思**：p 衡量的是"假设关系下数据有多反常"，**不是**效应大小；要看"多显著 vs 多大"两件事

## 现在做练习

5 道题：单样本 t、独立样本 t、配对 t、卡方、相关系数。
