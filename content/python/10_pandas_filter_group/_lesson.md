# pandas 筛选与分组

## 这一节学什么

People Analytics / HRBP 80% 的工作就是 **"筛选 + 分组聚合"**：
- 算"每个部门的平均工资"
- "工龄 5 年以上员工的离职率"
- "各学历人数 + 各学历的平均绩效分"

pandas 的 `boolean indexing` + `groupby` 把这些合在两三行代码里。

## 布尔筛选（boolean indexing）

```python
df[df["score"] >= 80]                      # 分数≥80 的所有行
df[(df["score"] >= 80) & (df["class"] == "A")]   # 与
df[(df["class"] == "A") | (df["class"] == "B")]  # 或
df[df["name"].isin(["Alice", "Bob"])]      # 在列表里
df[~df["name"].isin(["Alice"])]             # 非（取反）
```

⚠️ 与/或/非 用 `& | ~`，**不是 `and or not`**，且必须每个条件用括号包好。

## groupby：分组聚合

```python
df.groupby("class")["score"].mean()
# class
# A    87.5
# B    80.0
```

- 用 `groupby("列")` 分组（列里相同值的归一组）
- 然后选要聚合的列 `["score"]`
- 调用聚合函数 `.mean()`

## 多个聚合

```python
df.groupby("class")["score"].agg(["mean", "max", "count"])
#        mean  max  count
# class
# A      87.5   92      2
# B      80.0   80      1
```

`.agg([...])` 一次给出多个统计量。

## 分组多列

```python
df.groupby(["dept", "level"])["salary"].mean()
```

`groupby` 接列表 → 多层分组。

## 重置索引

groupby 后第一列变成索引（不再是普通列）。如果要变回普通列：

```python
result = df.groupby("class")["score"].mean().reset_index()
```

## apply：每个分组应用自定义函数

```python
def top_score(g):
    return g.nlargest(2, "score")

df.groupby("class").apply(top_score)
```

每个 `g` 是该分组的子 DataFrame。

## 常用聚合速查

| 函数 | 含义 |
|---|---|
| `mean()` | 平均 |
| `sum()` | 求和 |
| `count()` | 非空个数 |
| `size()` | 行数（含空） |
| `min()` / `max()` | 极值 |
| `std()` / `var()` | 标准差 / 方差 |
| `nunique()` | 不同值个数 |
| `agg([...])` | 一次多个 |

## 常见错误

1. **&/| 不加括号**：`df[a > 1 & b < 2]` 出错；要 `df[(a > 1) & (b < 2)]`
2. **groupby 后忘选列**：`df.groupby("c").mean()` 会对所有数值列求均值（可能不是你想要的）
3. **结果索引迷失**：sort 后下标乱，`reset_index(drop=True)` 重排
4. **过滤后修改原表**：`subset = df[...]; subset["x"] = 1` 可能触发 SettingWithCopyWarning；用 `df.loc[条件, "x"] = 1` 直接改

## 现在做练习

5 道题：筛选高分、按部门均值、按部门人数、多条件过滤、agg 多统计。
