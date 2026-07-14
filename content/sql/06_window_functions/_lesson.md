# 窗口函数（OVER / PARTITION BY）

## 窗口函数解决什么问题

到这里你会的 GROUP BY 是把多行**压缩成一行**：5 个学生分组成 2 班，每班一行平均分。

但有些问题需要 **每行都保留 + 同时算个跨行的值**：
- 给每个学生标"在他班里排第几名"——每个学生一行**+** 班内排名
- 给每行加一列"该班的平均分"，方便对比"高于/低于本班均值多少"
- 计算"环比/同比"：今天的销量 vs 昨天的

GROUP BY 解决不了这些（它把行压缩了）。**窗口函数**专门解决——每行都在，同时给一个"窗口范围内"的统计。

## 基本语法

```sql
SELECT
  name, class, score,
  AVG(score) OVER (PARTITION BY class) AS class_avg
FROM students;
```

逐字读：
- `AVG(score) OVER (...)` —— 窗口聚合
- `PARTITION BY class` —— **按班级分窗**：每个班是一个独立的"窗口"
- `class_avg` —— 这一列的别名

结果：每个学生行都保留，多了一列"我们班的平均分"。

## 排名函数：ROW_NUMBER / RANK / DENSE_RANK

```sql
SELECT name, class, score,
  ROW_NUMBER() OVER (PARTITION BY class ORDER BY score DESC) AS rn
FROM students;
```

每行加一个"班内按分数降序的名次"。

三个排名函数差异（分数 92 92 87 75 时）：

| 函数 | 序号 |
|---|---|
| `ROW_NUMBER` | 1, 2, 3, 4（**永远连续**，并列也算两个） |
| `RANK` | 1, 1, 3, 4（并列共享 + 后面跳号） |
| `DENSE_RANK` | 1, 1, 2, 3（并列共享 + **不跳号**） |

要"取每班前 N 名"——用 ROW_NUMBER（保证连续）+ 外层 WHERE 过滤。

## LAG / LEAD：取前一行 / 后一行

```sql
SELECT date, sales,
  LAG(sales)  OVER (ORDER BY date) AS yesterday,
  LEAD(sales) OVER (ORDER BY date) AS tomorrow
FROM daily;
```

- `LAG(列, n=1)`：往**前** n 行的值
- `LEAD(列, n=1)`：往**后** n 行的值

环比就是 `(sales - LAG(sales)) / LAG(sales)`。

## 窗口聚合 vs GROUP BY

| 场景 | 用什么 |
|---|---|
| "每班平均分（结果 2 行）" | GROUP BY |
| "每个学生 + 他班的平均分（结果 N 行）" | 窗口函数 |

记忆口诀：**要不要保留每一行？要 → 窗口；不要 → GROUP BY**。

## OVER 里的部分都可省

```sql
AVG(score) OVER ()                          -- 整个表的平均
AVG(score) OVER (PARTITION BY class)         -- 按班分组
AVG(score) OVER (PARTITION BY class ORDER BY id)  -- 累计平均
```

`OVER ()` 空括号 = 全表为一个窗口。

## 常见错误

1. **窗口函数和 GROUP BY 混用**：可以但语义复杂；先想清楚要不要压缩行
2. **`PARTITION BY` 写成 `PARTITION`**：少了 BY
3. **OVER 后面没括号**：`AVG(score) OVER` 错；`OVER ()` 才对
4. **以为可以 WHERE 过滤窗口结果**：WHERE 在窗口函数**之前**执行；要过滤窗口结果用子查询包一层

## 现在做练习

5 道题：班内排名、班平均、累计求和、LAG 环比、TOP 2 子查询。
