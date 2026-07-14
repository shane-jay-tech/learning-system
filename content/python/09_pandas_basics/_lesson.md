# pandas 基础

## pandas 是什么

pandas 是 Python **数据分析的核心库**——People Analytics、HRBP 报表、所有"读 Excel 算东西"的场景都靠它。它把数据装在一个叫 **DataFrame** 的二维表里，行是记录、列是字段，**就是 Python 版的 Excel**。

```python
import pandas as pd
```

约定俗成：导入时缩写为 `pd`。

## 创建 DataFrame

```python
import pandas as pd

df = pd.DataFrame({
    "name":  ["Alice", "Bob", "Cathy"],
    "score": [92, 78, 85],
    "class": ["A", "B", "A"],
})
print(df)
#     name  score class
# 0  Alice     92     A
# 1    Bob     78     B
# 2  Cathy     85     A
```

字典传入：键是列名，值是列数据（列表/数组）。

## 取列、取行

```python
df["name"]            # 取一列（Series）
df[["name", "score"]] # 取多列（仍是 DataFrame）
df.iloc[0]            # 第 1 行（按位置）
df.iloc[0:2]          # 前 2 行
df.loc[df["score"] >= 80]   # 按条件筛行
```

## 描述统计

```python
df["score"].mean()       # 平均
df["score"].sum()
df["score"].max()
df["score"].min()
df["score"].count()      # 非空个数
df["score"].std()        # 标准差
df.describe()            # 一次性给出所有数值列的 8 项统计
```

## 增 / 改 / 删列

```python
df["bonus"] = df["score"] * 0.1     # 新加一列
df["score"] = df["score"] + 5       # 整列加 5
df.drop(columns=["bonus"], inplace=True)  # 删列
```

## 排序

```python
df.sort_values("score", ascending=False)         # 按 score 降序
df.sort_values(["class", "score"], ascending=[True, False])  # 多列
```

## 简洁的链式写法

pandas 大量函数返回新 DataFrame，可以**链起来**：

```python
df.sort_values("score", ascending=False).head(3)
```

`.head(N)` 取前 N 行，`.tail(N)` 取后 N 行。

## Series 的 to_list / value_counts

```python
df["class"].tolist()         # ['A', 'B', 'A']
df["class"].value_counts()   # A 2, B 1（每个值出现次数）
df["class"].nunique()        # 2（不同值的个数）
```

## 常见错误

1. **`df["列"]` 不存在**：返回 KeyError；先 `print(df.columns)` 确认列名
2. **修改时用 chained indexing**：`df["a"]["b"] = 1` 可能不生效；用 `df.loc[行, 列] = 值`
3. **inplace=True 谁懂谁用**：默认大多数 pandas 操作返回新 DataFrame，不改原表；要原地改必须 `inplace=True` 或重新赋值
4. **`df["score"]` 是 Series，不是 list**：调 `tolist()` 或 `to_numpy()` 才是普通 Python 列表

## 现在做练习

5 道题：建表算平均、describe、排序+取前几行、新增列、value_counts。
