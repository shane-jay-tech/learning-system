# 字典与集合（dict / set）

## 字典：用"名字"取值

列表用下标（位置）取值，字典用 **键**（key）取值。当你需要"用名字找东西"时，字典是首选。

```python
ages = {"Alice": 25, "Bob": 30, "Cathy": 22}
ages["Alice"]    # 25
ages["Bob"]      # 30
```

形式：`{键: 值, 键: 值, ...}`，每对用冒号 `:`，对之间用逗号。

## 增删改查

```python
ages["David"] = 28        # 新增
ages["Alice"] = 26        # 修改（key 已存在就覆盖）
del ages["Bob"]           # 删除
"Cathy" in ages           # True
ages.get("Eve", 0)        # 0（key 不存在时给默认值，不会报错）
```

⚠️ 直接 `ages["不存在的"]` 会抛 `KeyError`；用 `get(key, default)` 更安全。

## 遍历字典

```python
for name in ages:
    print(name, ages[name])

# 更常用：同时拿 key 和 value
for name, age in ages.items():
    print(name, age)

ages.keys()      # dict_keys(['Alice', 'Bob', ...])
ages.values()    # dict_values([25, 30, ...])
ages.items()     # dict_items([('Alice', 25), ...])
```

## 字典推导式

```python
squares = {x: x*x for x in range(1, 6)}
# {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}

names = ["Alice", "Bob"]
ages = [25, 30]
d = {n: a for n, a in zip(names, ages)}
# {'Alice': 25, 'Bob': 30}
```

## 词频统计：字典最经典用法

```python
text = "apple banana apple cherry banana apple"
counts = {}
for word in text.split():
    counts[word] = counts.get(word, 0) + 1
# {'apple': 3, 'banana': 2, 'cherry': 1}
```

更优雅的方法是用标准库 `collections.Counter`，后续学到。

## 集合：去重 + 数学集合运算

集合 `set` 是 **无序、不重复** 的容器，专门用来：

- **去重**：`set([1,2,2,3])` → `{1, 2, 3}`
- **判断成员**：`x in s` 比列表的 `in` 快得多（百万级数据时差异巨大）
- **集合运算**：交并差

```python
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}
a | b    # 并集 {1,2,3,4,5,6}
a & b    # 交集 {3, 4}
a - b    # 差集 {1, 2}
a ^ b    # 对称差 {1,2,5,6}（在任一不在两者）
```

注意：**空集合不能写 `{}`**（那是空字典），要写 `set()`。

## 字典 vs 集合 vs 列表 怎么选

| 你想做的 | 选 |
|---|---|
| "我有一组按顺序的东西，要按位置取" | 列表 |
| "我有一堆名字到值的映射" | 字典 |
| "我只关心有没有，不关心顺序也不要重复" | 集合 |
| "去重一个列表" | `list(set(原列表))` |

## 常见错误

1. **空集合写错**：`s = {}` 是空字典；`s = set()` 才是空集合
2. **字典 key 必须可哈希**：列表不能当 key（因为列表可变）；字符串、数字、元组可以
3. **dict 取不存在的 key 报错**：用 `d.get(key, default)` 防御
4. **集合无序**：`for x in {1,2,3}` 的顺序不保证；要顺序就用列表
5. **dict 在 Python 3.7+ 保留插入顺序**——但**不要依赖**（依赖了将来移植麻烦）

## 现在做练习

5 道题：词频、查值（用 get）、求两组数据的交集、字典翻转、字符直方图。
