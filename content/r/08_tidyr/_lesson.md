# tidyr：数据整形（pivot_longer / pivot_wider）

## 整形是什么

数据有两种"形状"：

**宽表（wide）**：每个观测一行，每个变量一列
```
name    math  english  history
Alice   85    78       90
Bob     72    88       85
```

**长表（long）**：每个观测的每个变量是一行
```
name    subject  score
Alice   math     85
Alice   english  78
Alice   history  90
Bob     math     72
...
```

很多分析（特别是画图、混合效应模型）需要**长表**。`tidyr` 提供两个函数互相转换。

## pivot_longer：宽变长

```r
library(tidyr)

df_wide <- data.frame(
  name = c("Alice", "Bob"),
  math = c(85, 72),
  english = c(78, 88),
  history = c(90, 85)
)

df_long <- df_wide %>%
  pivot_longer(
    cols = c(math, english, history),     # 要"摞起来"的列
    names_to = "subject",                  # 列名变成这个变量
    values_to = "score"                    # 值变成这个变量
  )
```

`cols` 指定哪些列要变长；`names_to` 是新的"列名变量"；`values_to` 是新的"值变量"。

## pivot_wider：长变宽

```r
df_wide_back <- df_long %>%
  pivot_wider(
    names_from = subject,    # 从哪列取新列名
    values_from = score       # 从哪列取值
  )
```

## 常见参数

```r
df %>% pivot_longer(
  cols = -name,                    # "除了 name 之外的列"
  names_to = "subject",
  values_to = "score",
  values_drop_na = TRUE             # 丢掉 NA 行
)

df %>% pivot_longer(
  cols = starts_with("score_"),     # 列名匹配
  names_to = "subject",
  names_prefix = "score_",          # 去前缀
  values_to = "value"
)
```

## ggplot 配合长表

```r
library(ggplot2)

df_long %>%
  ggplot(aes(x = subject, y = score, fill = name)) +
  geom_col(position = "dodge")
```

ggplot 的 aesthetic 映射要求**每个数据点对应一行**——长表天生适合。

## tidyr 常用辅助：separate / unite

```r
# 把 "Alice/HR" 拆成两列
df %>% separate(name_dept, into = c("name", "dept"), sep = "/")

# 反过来，合并两列
df %>% unite(combined, name, dept, sep = "/")
```

## drop_na 与 fill

```r
df %>% drop_na()                # 删除含 NA 的行
df %>% drop_na(score)            # 只看 score 列
df %>% fill(score, .direction = "down")    # NA 用上面非 NA 填
```

## 常见错误

1. **pivot_longer 里 cols 写错**：用反引号引列名 `` `name` ``，避免和函数冲突
2. **pivot_wider 后多行重复**：因为 names_from + 其他维度组合不唯一——需要先 group_by 聚合
3. **`tidyselect` 表达式**：cols 支持 `where(is.numeric)`、`-name`、`starts_with("a")` 等高级语法
4. **改完没赋回**：`df %>% pivot_longer(...)` 不存就丢了

## 现在做练习

5 道题：宽变长基本、变回宽、separate 拆分、长表配 group_by 求和、starts_with 选列。
