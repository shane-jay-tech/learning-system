# ORDER BY / DISTINCT / LIMIT / UNION

## 这一节学什么

到现在你会 `SELECT 列 FROM 表 WHERE 条件 GROUP BY 列`，已经能做大部分基础查询。但还差几个常用的"修饰词"：让结果**有序**、**去重**、**只取前 N 行**、**和另一张表合并**。这些是日常分析里**几乎每条 SQL 都会用到**的。

## ORDER BY：让结果按某列排序

```sql
SELECT name, score FROM students ORDER BY score DESC;
```

- `ASC`（升序，默认；可以省）
- `DESC`（降序）

多列排序（先按第一列，相同时再按第二列）：

```sql
SELECT * FROM students
ORDER BY score DESC, id ASC;
```

⚠️ **没有 ORDER BY，结果顺序不保证**——即使数据库这次给你排好了，下次可能就乱。要确定顺序就显式写 ORDER BY。

## LIMIT：只要前 N 行

```sql
SELECT * FROM students ORDER BY score DESC LIMIT 3;   -- 前 3 名
```

`LIMIT N` 几乎总是和 `ORDER BY` 一起用——光 LIMIT 没排序拿到的"前 N 个"是随机的。

进阶：`LIMIT 10 OFFSET 20` 是分页（跳过 20 行后取 10 行）。

## DISTINCT：去重

```sql
SELECT DISTINCT score FROM students;       -- 所有不同的分数
SELECT DISTINCT class, grade FROM students;  -- (class, grade) 不同的组合
```

`DISTINCT` 紧跟在 `SELECT` 后面，对**整行**去重——多列时是组合去重。

## UNION：合并两个查询结果

```sql
SELECT name FROM students
UNION
SELECT name FROM alumni;
```

把两个查询的结果**纵向拼起来**，自动去重。要保留重复用 `UNION ALL`（更快，但有重复）。

⚠️ 两边的列数和类型必须一致。`SELECT id, name FROM ...` UNION `SELECT name FROM ...` 会报错。

## HAVING：聚合后再过滤

```sql
SELECT class, AVG(score) FROM students
GROUP BY class
HAVING AVG(score) >= 80;
```

`HAVING` 和 `WHERE` 长得像，但**时机不同**：
- `WHERE` 在分组**之前**过滤行
- `HAVING` 在分组聚合**之后**过滤组

口诀：**WHERE 过滤行，HAVING 过滤组**。

## 完整 SQL 子句顺序

```sql
SELECT 列
FROM 表
WHERE 行过滤
GROUP BY 分组列
HAVING 组过滤
ORDER BY 排序列
LIMIT 行数;
```

记不住时按"S-F-W-G-H-O-L"念两遍就熟了。

## 常见错误

1. **ORDER BY 写在 WHERE 之前**：SQL 语法顺序固定，必须 ORDER BY 在最后
2. **LIMIT 不带 ORDER BY**：得到的"前 N 个"不可控
3. **UNION 两边列数不一致**：报错；要么调整列，要么用 NULL 占位
4. **WHERE 里写聚合函数**：`WHERE AVG(score)>80` 错；要用 HAVING

## 现在做练习

5 道题：降序排列、最低分前 2、去重、UNION 合并、多列排序。
