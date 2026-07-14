# ggplot2：发表级数据可视化

## 为什么 ggplot2 很重要

R 在数据可视化领域的"杀手锏"是 `ggplot2`。它**几乎是所有顶级期刊论文图表**的来源。
和 matplotlib 不同，ggplot2 用一种叫 **图形语法（Grammar of Graphics）** 的写法——你**先描述要把什么映射到什么**，剩下的它自动算。

## 一个图的最简骨架

```r
library(ggplot2)

ggplot(data = df, aes(x = score, y = age)) +
  geom_point()
```

三件事：
1. `ggplot(数据, 映射)`：声明哪个表，哪些列对应 x/y
2. `aes(...)`：**映射关系**——哪列对应坐标轴/颜色/形状
3. `geom_xxx()`：用什么形状画（点/线/柱/箱）

ggplot2 用 `+` 把图层叠起来。

## 五个常用 geom

| geom | 图类型 |
|---|---|
| `geom_point()` | 散点图 |
| `geom_line()` | 折线图 |
| `geom_bar(stat="identity")` 或 `geom_col()` | 柱状图 |
| `geom_histogram()` | 直方图 |
| `geom_boxplot()` | 箱线图 |

## 加颜色映射

```r
ggplot(df, aes(x = score, y = age, color = class)) +
  geom_point()
```

`color = class` 让点按 class 自动着色（A 班一种色 B 班另一种）。这是 ggplot2 最核心的**美学映射**。

## 标题和坐标轴

```r
ggplot(df, aes(x = class, y = score)) +
  geom_boxplot() +
  labs(title = "各班成绩分布",
       x = "班级",
       y = "分数")
```

`labs()` 一次设标题、x 轴、y 轴。

## 主题（theme）

```r
ggplot(...) + theme_minimal()    # 干净留白
ggplot(...) + theme_bw()         # 黑白学术风
```

主题影响整体视觉。`theme_minimal()` 和 `theme_bw()` 是论文常用的两个。

## 保存到文件

```r
p <- ggplot(...)  # 把图存到变量
ggsave("plot.png", p, width = 6, height = 4, dpi = 300)
```

`ggsave` 是 ggplot2 自带的保存函数；`width/height` 是英寸；`dpi` 控制分辨率。

## 在练习平台中怎么"判图"

判图困难——**题目让你画完后再 cat 出某个统计量**，平台对比 stdout。

## 常见错误

1. **没 library(ggplot2)**：报"找不到 ggplot"
2. **把变量当字符串**：`aes(x = "score")` 错（这是字面字符串）；应 `aes(x = score)`
3. **+ 写成 %>%**：管道符是给数据用的；图层叠用 `+`
4. **`geom_bar` 默认按计数**：要按值画必须 `geom_bar(stat="identity")` 或用 `geom_col()`

## 现在做练习

5 道题：散点图 + 输出 max、柱状图 + 输出 sum、按 class 着色、箱线图 + 输出 IQR、保存 ggsave。
