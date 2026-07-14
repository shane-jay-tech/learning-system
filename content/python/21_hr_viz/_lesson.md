# HR 数据可视化

用 Matplotlib 把 HR 数据变成直观图表，是向非技术 HR 同事汇报的核心技能。

## 为什么重要

数字表格看不出趋势，一张图胜过一屏数字。面对老板和业务部门，你需要用图表讲故事。

## 核心图表类型

- **柱状图** `plt.bar()`：部门人数对比、招聘完成率
- **箱线图** `plt.boxplot()`：薪资分布、绩效分数离散度
- **折线图** `plt.plot()`：月度离职趋势、季度招聘量变化
- **散点图** `plt.scatter()`：年龄 vs 薪资、工龄 vs 绩效

## 最小示例

```python
import matplotlib.pyplot as plt

departments = ["技术", "市场", "HR", "财务"]
headcount = [120, 45, 15, 20]
plt.bar(departments, headcount)
plt.title("各部门人数")
plt.ylabel("人数")
plt.show()
```

## 常见错误

- 忘记 `plt.show()` 导致看不到图
- 中文乱码：需设置 `plt.rcParams['font.sans-serif'] = ['SimHei']`
- 图表没标题和轴标签，别人看不懂

## 做题前检查

1. 确认数据结构（列表 or DataFrame）
2. 选对图表类型（比较用柱状、趋势用折线、分布用箱线）
3. 加标题和轴标签
