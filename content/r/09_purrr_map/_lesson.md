# purrr：函数式编程（map 系列）

## 为什么用 purrr

R 经常需要"对一组东西每个都做同样的事"：
- 对每个班分别拟合一个模型
- 对每列做相同的清洗
- 读 10 个 csv 文件批量合并

历史上你用 `for` 或 `apply`。`purrr`（tidyverse 的一部分）提供更**类型安全**的 `map` 系列。

```r
library(purrr)
```

## map：对每个元素应用函数

```r
v <- c(1, 4, 9, 16, 25)
sqrts <- map(v, sqrt)              # 返回 list
sqrts <- map_dbl(v, sqrt)          # 返回 double 向量
```

| 函数 | 返回 |
|---|---|
| `map(x, f)` | list（最通用） |
| `map_dbl(x, f)` | double 向量 |
| `map_int(x, f)` | int 向量 |
| `map_chr(x, f)` | character 向量 |
| `map_lgl(x, f)` | logical 向量 |

`map_xxx` 强制返回类型——**类型不匹配立即报错**，比 sapply 更安全。

## 匿名函数：~ 和 .x

```r
v <- 1:5
map_dbl(v, ~ .x * .x)        # 等价 map_dbl(v, function(x) x*x)
```

`~` 开头是 lambda，`.x` 是参数。

## map 多个输入

```r
a <- c(1, 2, 3)
b <- c(10, 20, 30)
map2_dbl(a, b, ~ .x + .y)        # c(11, 22, 33)
```

`map2` 接两个输入，`.x` 和 `.y` 分别引用。

## walk：副作用版本

```r
walk(1:3, ~ cat("Hello", .x, "\n"))   # 仅打印，不返回
```

`walk` 像 `map` 但返回 invisible 原输入——专门用于"做事不取结果"。

## 配合数据框：map 一列

```r
library(dplyr)

df <- data.frame(x = c(1, 4, 9, 16))
df %>% mutate(sqrt_x = map_dbl(x, sqrt))
```

## 嵌套数据框：先 split 再 map

```r
# 对每个班分别建模
models <- df %>%
  split(.$class) %>%               # 按 class 拆成多个数据框
  map(~ lm(score ~ years, data = .x))

# 取每个模型的 R²
map_dbl(models, ~ summary(.x)$r.squared)
```

这是 **"分组建模"** 的标准 tidyverse 写法。

## reduce：累加

```r
reduce(1:5, `+`)             # 1+2+3+4+5 = 15
reduce(1:5, `+`, .init = 100) # 从 100 开始累加 → 115

# 累加版（保留每步）
accumulate(1:5, `+`)         # c(1, 3, 6, 10, 15)
```

## keep / discard：过滤

```r
keep(1:10, ~ .x %% 2 == 0)        # 保留偶数
discard(1:10, ~ .x %% 2 == 0)      # 丢掉偶数
```

## 常见错误

1. **map_dbl 类型不匹配**：函数返回非 double → 立即报错；用 map() 退一步
2. **`~` lambda 参数没写 `.x`**：`map(v, ~ x*x)` 错；要 `~ .x*.x`
3. **for 循环 vs map**：循环写副作用 OK；返回值场景 map 更短更对
4. **嵌套深时可读性差**：能 1-2 行解决就用 map；超过 3 层考虑拆函数

## 现在做练习

5 道题：map_dbl 求平方根、map2 加和、reduce 求和、keep 过滤、按 class 分组建模。
