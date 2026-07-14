# NULL 处理

## NULL 是什么

`NULL` 不是 0、不是空字符串，而是 **"不知道 / 未填写"**。比如员工的 `leave_date` 列：
- NULL = 还在职，没离开
- 具体日期 = 已离职

NULL 在 SQL 里有**特殊行为**——很多新手栽在这上面。

## NULL 比较的陷阱

```sql
SELECT NULL = NULL;       -- 不是 TRUE，是 NULL（未知）
SELECT NULL = 1;           -- NULL，不是 FALSE
SELECT NULL <> 1;          -- NULL，不是 TRUE
```

WHERE 子句把 NULL 当 false，所以：

```sql
WHERE col = NULL          -- 永远不匹配（即使 col 真的是 NULL）！
WHERE col IS NULL         -- 这才对！
WHERE col IS NOT NULL
```

## 算术里的 NULL

```sql
SELECT NULL + 1;       -- NULL（任何运算包含 NULL 结果是 NULL）
SELECT 1 + 1;           -- 2
```

聚合函数**自动忽略 NULL**：

```sql
SELECT AVG(score) FROM students;
-- 如果 score 列有 NULL，AVG 用 (非 NULL 的总和) / (非 NULL 的个数) 算
SELECT COUNT(*) FROM students;       -- 数所有行
SELECT COUNT(score) FROM students;   -- 只数 score 非 NULL 的行
```

`COUNT(*)` vs `COUNT(列名)` 是新手常误解的——前者数行，后者数非空。

## COALESCE：第一个非 NULL 值

```sql
SELECT COALESCE(nickname, name, 'Anonymous')
FROM users;
```

读："看 nickname，是 NULL 就看 name；name 也 NULL 就用 'Anonymous'。"

经典用法：**给 NULL 一个默认显示值**：

```sql
SELECT name, COALESCE(salary, 0) FROM employees;
```

## IFNULL（SQLite/MySQL）

```sql
IFNULL(col, default)     -- 等价 COALESCE(col, default)
```

`IFNULL` 只接 2 参数；`COALESCE` 接任意个，更通用。

## NULLIF：满足条件时变 NULL

```sql
NULLIF(score, 0)    -- score=0 时返回 NULL，否则返回 score
```

防除零的常用招：

```sql
SELECT total / NULLIF(count, 0) FROM stats;  -- count=0 时结果是 NULL（避免除零错）
```

## NOT IN 和 NULL 灾难

之前的 `08_exists` 章节已经讲过：

```sql
WHERE id NOT IN (SELECT dept_id FROM students)
-- 只要 dept_id 列有 NULL，整个表达式失效，返回空集
```

**结论**：处理"不在"逻辑用 `NOT EXISTS` 或显式 `IS NOT NULL` 加保护。

## 排序时 NULL 的位置

```sql
SELECT name, score FROM students ORDER BY score;
-- 默认 NULL 排在最前（升序）或最后（降序），取决于数据库

-- 显式控制（SQLite 3.30+ 支持）
SELECT name FROM students ORDER BY score NULLS LAST;
```

## 常见错误

1. **WHERE col = NULL**：永远不匹配。用 IS NULL
2. **`COUNT(*)` 和 `COUNT(col)`** 混用，结果不一致而困惑
3. **NULL + 0**：你以为是 0，实际是 NULL。用 COALESCE 包一下
4. **拼字符串遇 NULL**：`'Hello, ' || NULL` 在 SQLite 中等于 NULL，整个字符串变 NULL

## 现在做练习

5 道题：IS NULL 找未离职、COALESCE 默认值、NULLIF 防除零、COUNT(*)vs COUNT(col)、ORDER BY NULL 处理。
