# NumPy 基础

NumPy 是 Python 做数值计算的核心库。它提供高效的多维数组（`ndarray`）和大量数学函数。

## 为什么用 NumPy？

- **速度快**：底层用 C 写的，比纯 Python 列表快 10-100 倍
- **语法简洁**：一行代码完成整列运算，不需要写循环
- **生态基石**：Pandas、scikit-learn、SciPy 都建立在 NumPy 之上

## 核心概念

```python
import numpy as np

# 创建数组
arr = np.array([1, 2, 3, 4, 5])

# 基本运算（向量化，不需要循环）
arr * 2        # [2, 4, 6, 8, 10]
arr.mean()     # 3.0
arr > 3        # [False, False, False, True, True]

# 布尔索引（筛选）
arr[arr > 3]   # [4, 5]
```

## 常用操作速查

| 操作 | 代码 | 说明 |
|------|------|------|
| 创建数组 | `np.array([1,2,3])` | 从列表转 |
| 全零 | `np.zeros(5)` | 5 个 0 |
| 范围 | `np.arange(0, 10, 2)` | [0,2,4,6,8] |
| 均值 | `arr.mean()` | 平均值 |
| 标准差 | `arr.std()` | 离散程度 |
| 形状 | `arr.shape` | 维度信息 |
| 筛选 | `arr[arr > 0]` | 布尔索引 |
