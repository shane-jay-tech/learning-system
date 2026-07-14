# 数据框（data.frame） + apply 系列

## R 真正的"主战场"

之前你练的向量是 R 的**单列数据**。但真实数据通常是**多列表格**——比如学生表有 id、name、score、class 多列。R 用 **data.frame**（数据框）来装这种数据，**它就是 R 版的 Excel 表**。

```r
df <- data.frame(
  name = c("Alice", "Bob", "Cathy"),
  score = c(92, 78, 85),
  class = c("A", "B", "A")
)
print(df)
#    name score class
# 1 Alice    92     A
# 2   Bob    78     B
# 3 Cathy    85     A
```

每列必须长度相同；同一列类型一致（这一点 R 比 Python 严，类似数据库表）。

## 取值的几种方式

```r
df$name        # 取整列（向量）
df[, "name"]   # 同上
df[1, ]        # 取第 1 行（仍是 data.frame）
df[1, 2]       # 第 1 行第 2 列
df[df$score >= 80, ]   # 筛选行（按条件）
```

R 的 `[行, 列]` 语法：方括号里两个位置，**逗号前是行、逗号后是列**。空着就是"全选"。

## 列的添加 / 修改

```r
df$grade <- ifelse(df$score >= 80, "Pass", "Fail")
df$score_x2 <- df$score * 2
```

赋值给 `df$新列名` 就是新增；已有列名就是覆盖。

## 内置函数：列汇总

```r
mean(df$score)      # 平均分
sum(df$score)       # 总分
max(df$score)       # 最高分
nrow(df)            # 行数
ncol(df)            # 列数
summary(df)         # 全列描述统计
```

## apply 系列：批量套用函数

R 编程一大特色：尽量**避免写 for 循环**，用 apply 系列替代。

```r
m <- matrix(1:12, nrow = 3)         # 3×4 矩阵
apply(m, 1, sum)   # 对每一行求和（margin=1 表示行）
apply(m, 2, mean)  # 对每一列求均值（margin=2 表示列）
```

`apply(数据, 维度, 函数)`：
- 维度 1 = 沿行
- 维度 2 = 沿列

针对**列表**用 `sapply`：

```r
sapply(c("Alice", "Bob", "Cathy"), nchar)
# Alice   Bob Cathy
#     5     3     5
```

`sapply` 对每个元素应用函数，返回一个向量。

## 读 csv 文件

```r
df <- read.csv("students.csv")           # 读 csv
df <- read.csv("data.csv", encoding = "UTF-8")  # 中文文件加这个
write.csv(df, "out.csv", row.names = FALSE)     # 写 csv
```

`row.names = FALSE` 是常用——不写的话 R 会多写一列行号。

## 常见错误

1. **混淆 `df$name` 和 `df[, "name"]`**：第一种返回向量，第二种**默认**也返回向量；但 `df[, "name", drop = FALSE]` 返回 data.frame
2. **行筛选忘了逗号**：`df[df$score >= 80]` 是错的；要 `df[df$score >= 80, ]`（逗号后留空表示所有列）
3. **用 for 循环代替 apply**：能跑但慢且啰嗦；R 文化是用向量化或 apply
4. **read.csv 中文乱码**：Windows 下读 UTF-8 csv 必须显式 `encoding = "UTF-8"`

## 现在做练习

5 道题：建数据框、按条件筛选、求列均值、apply 求行和、添加新列。
