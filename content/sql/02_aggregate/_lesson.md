# 聚合函数与分组（COUNT / AVG / GROUP BY）

## 为什么需要聚合

之前我们查的都是"原始的行"——表里有什么就查出什么。但真实问题往往是 **统计性的**：

- 这次考试**平均**分多少？
- **多少**人及格？
- **每个班级**的最高分是多少？

回答这些问题，需要对一批行做"汇总"——这就是 **聚合函数**。

## 五个常用聚合函数

| 函数 | 干啥 |
|---|---|
| `COUNT(*)` | 数行数（含空值） |
| `COUNT(列)` | 数该列非空的行数 |
| `SUM(列)` | 求和（仅数值列） |
| `AVG(列)` | 平均值（仅数值列） |
| `MAX(列)` / `MIN(列)` | 最大值 / 最小值 |

例子：

```sql
SELECT COUNT(*) FROM students;          -- 总人数
SELECT AVG(score) FROM students;        -- 平均分
SELECT MAX(score), MIN(score) FROM students;  -- 最高最低
```

## WHERE 配合聚合：先过滤再统计

```sql
SELECT COUNT(*) FROM students WHERE score >= 60;
```

这是"先把不及格的人过滤掉，再数有多少人及格"。

## GROUP BY：按某列分组分别聚合

`GROUP BY` 让聚合**对每个分组独立计算**。比如表里如果还有 `class` 列，想看每个班的平均分：

```sql
SELECT class, AVG(score) FROM students GROUP BY class;
```

输出会是：

```
class | AVG(score)
A     | 85.5
B     | 78.0
```

**口诀**：SELECT 里出现的非聚合列，必须出现在 GROUP BY 里。否则数据库会报错（或者给一个未定义的结果）。

## CASE WHEN：条件计数

想统计"60 分以下有几个人，60 分以上有几个人"，用 `CASE WHEN`：

```sql
SELECT
  SUM(CASE WHEN score >= 60 THEN 1 ELSE 0 END) AS pass_count,
  SUM(CASE WHEN score < 60  THEN 1 ELSE 0 END) AS fail_count
FROM students;
```

`CASE WHEN ... THEN ... ELSE ... END` 是 SQL 的"条件表达式"，相当于 Python 的 if-else。

## 给结果列起别名：AS

聚合函数自带的列名（`AVG(score)`）不好读。用 `AS` 重命名：

```sql
SELECT AVG(score) AS avg_score FROM students;
```

输出列名就是 `avg_score`。

## 常见错误

1. **GROUP BY 里漏列**：`SELECT class, name, AVG(score) FROM students GROUP BY class` —— `name` 既不是聚合也不在 GROUP BY 里，报错或返回不可控值
2. **WHERE 里写聚合**：`WHERE AVG(score) > 80` —— WHERE 在聚合**之前**执行，应该用 `HAVING AVG(score) > 80`
3. **AVG 忘了类型**：`AVG('92')`——把分数当字符串了，结果会乱

## 现在做练习

下面 3 道题：求平均分、找最高分、按等级分组计数。把 AVG / MAX / GROUP BY 各练一遍。
