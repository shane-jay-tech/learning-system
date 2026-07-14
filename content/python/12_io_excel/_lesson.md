# 文件 IO：CSV 与 Excel

## 数据进出 pandas 的两条主路

真实数据通常存在文件里——HRBP 的"员工花名册"、问卷调查的"原始打分表"基本都是 csv 或 xlsx。pandas 提供了**一整套** read_xxx / to_xxx 函数。

## CSV：read_csv / to_csv

```python
import pandas as pd

# 读
df = pd.read_csv("students.csv")
df = pd.read_csv("data.csv", encoding="utf-8")    # 中文文件强制 utf-8

# 写
df.to_csv("out.csv", index=False, encoding="utf-8")
```

`index=False` **几乎总是要写**——不写的话 pandas 会多写一列行号。

## Excel：read_excel / to_excel

```python
df = pd.read_excel("scores.xlsx", sheet_name="Sheet1")
df.to_excel("out.xlsx", sheet_name="结果", index=False)
```

需要装 `openpyxl`：`pip install openpyxl`。本平台已装。

## 常用读 csv 参数

| 参数 | 作用 |
|---|---|
| `encoding="utf-8"` | 中文 csv 必备 |
| `sep=","` 或 `sep="\t"` | 自定义分隔符（默认逗号；TSV 用 `\t`）|
| `header=0` 或 `header=None` | 是否第一行是表头 |
| `names=["a","b"]` | 自定义列名（搭配 header=None）|
| `usecols=["a","b"]` | 只读指定列 |
| `nrows=100` | 只读前 100 行 |
| `parse_dates=["date"]` | 把列解析成日期 |

## 写多个 sheet 到一个 xlsx

```python
with pd.ExcelWriter("out.xlsx") as w:
    df1.to_excel(w, sheet_name="A 班", index=False)
    df2.to_excel(w, sheet_name="B 班", index=False)
```

## 大文件分块读

```python
chunks = pd.read_csv("huge.csv", chunksize=10000)
for chunk in chunks:
    process(chunk)
```

`chunksize` 让你按块迭代，不必一次把整个文件塞进内存。

## DataFrame ↔ JSON

```python
df.to_json("data.json", orient="records", force_ascii=False)
df = pd.read_json("data.json")
```

`orient="records"` 是最常用的——每行变一个 JSON 对象。

## 常见错误

1. **写 csv 没加 index=False**：多一列 0,1,2,...
2. **中文乱码**：Windows 写 csv 默认 cp1252 / GBK，**显式 `encoding="utf-8"` 或 `utf-8-sig`**（后者带 BOM，Excel 打开能直接显示中文）
3. **Excel 时间列被当字符串**：用 `parse_dates=["列名"]`
4. **`read_excel` 报"openpyxl not found"**：`pip install openpyxl`

## 现在做练习

5 道题：写后读 csv、读 csv 求和、按 utf-8 写中文 csv、写 Excel、读 csv 筛选。
