# dplyr：现代 R 数据处理

## 为什么学 dplyr

R 自带的数据处理够用但语法老派。`dplyr`（tidyverse 的核心包）让数据处理写起来**像在描述步骤**：

> 拿这张表 → 筛选成绩 ≥ 80 的 → 按班级分组 → 算每班均值

直接对应代码：

```r
library(dplyr)

df %>%
  filter(score >= 80) %>%
  group_by(class) %>%
  summarize(avg = mean(score))
```

`%>%` 叫 **管道符**，把左边的结果传给右边——就像 shell 里的 `|`。

## 五个核心动词

| 动词 | 干啥 |
|---|---|
| `filter()` | 筛行（按条件） |
| `select()` | 选列 |
| `mutate()` | 加 / 改列 |
| `arrange()` | 排序 |
| `summarize()` | 聚合（配合 group_by 用） |

加上 `group_by()` 一共 6 件套，**90% 的数据清洗活都用得上**。

## 一个一个用

```r
df %>% filter(score >= 80, class == "A")    # 多条件用逗号（=AND）
df %>% select(name, score)                  # 只留两列
df %>% select(-id)                          # 去掉 id 列
df %>% mutate(passed = score >= 60)         # 加新列
df %>% mutate(score = score + 5)            # 改原列
df %>% arrange(score)                       # 升序
df %>% arrange(desc(score))                 # 降序
df %>% arrange(class, desc(score))          # 多列
```

## group_by + summarize：分组聚合

```r
df %>%
  group_by(class) %>%
  summarize(
    n = n(),                # 行数
    avg = mean(score),
    max_s = max(score)
  )
```

`n()` 是 dplyr 提供的"当前组行数"。

## 链式写法的好处

不用 dplyr 时 R 写聚合逻辑像剥洋葱：

```r
summarize(group_by(filter(df, score>=80), class), avg=mean(score))
```

用 dplyr 后从左到右读得通：

```r
df %>% filter(score>=80) %>% group_by(class) %>% summarize(avg=mean(score))
```

## %>% 在 R 4.1+ 也能用 |>

```r
df |> filter(score >= 80)   # |> 是 R 自带的管道符（无需 dplyr）
```

效果几乎一样，但 `%>%` 还是更通用（因为 dplyr 老代码都是它）。

## 常见错误

1. **没 `library(dplyr)`**：报"找不到 filter"
2. **`filter` 用 `=` 而非 `==`**：`filter(score = 80)` 错；要 `filter(score == 80)`
3. **`summarize` 后还能用 mutate**：summarize 已经压缩成一行/组，但仍是数据框可继续 mutate
4. **管道断了**：`df %>% filter(...) %>%` 后面没东西就报错；保证每个 %>% 后面都有动词

## 现在做练习

5 道题：filter、select、mutate、arrange、group_by + summarize。
