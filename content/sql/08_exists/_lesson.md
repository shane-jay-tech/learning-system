# EXISTS / NOT EXISTS

## EXISTS 在解决什么

`EXISTS` 检查"子查询有没有结果"。和 IN 长得像但更高效：

```sql
-- 找有学生的部门
SELECT name FROM departments d
WHERE EXISTS (
  SELECT 1 FROM students s WHERE s.dept_id = d.id
);
```

读法："对每个 d，看子查询是否返回任何行——返回就保留 d。"

## EXISTS vs IN

```sql
-- IN 写法
SELECT name FROM departments
WHERE id IN (SELECT dept_id FROM students);

-- EXISTS 写法
SELECT name FROM departments d
WHERE EXISTS (
  SELECT 1 FROM students s WHERE s.dept_id = d.id
);
```

| 维度 | IN | EXISTS |
|---|---|---|
| 子查询返回 | 一列值（数据库要装下整列）| 只看有没有（True/False）|
| 数据量大时 | 慢 | 通常更快 |
| 处理 NULL | 需小心 | 自然忽略 |

业务场景里**两者结果一样的话用 EXISTS 更稳**。

## NOT EXISTS：找"没有对应"的

```sql
-- 找没有学生的部门
SELECT name FROM departments d
WHERE NOT EXISTS (
  SELECT 1 FROM students s WHERE s.dept_id = d.id
);
```

这是 PA 常用的"找没招到人的部门"查询。

## NOT IN 的 NULL 陷阱

```sql
SELECT name FROM departments
WHERE id NOT IN (SELECT dept_id FROM students);
```

⚠️ 如果 students 表里 dept_id 列**有 NULL 值**，这条 SQL 会返回**空集**！因为 `id NOT IN (1, 2, NULL)` 计算时 SQL 不知道 `id != NULL`，整个表达式变 unknown。

**结论**：要用 NOT 的逻辑，**优先 NOT EXISTS**。

## 子查询里的 SELECT 1

`SELECT 1 FROM ...` 还是 `SELECT * FROM ...` 在 EXISTS 里**没有区别**——EXISTS 只关心有没有行，不关心列值。`SELECT 1` 是惯例（明示意图）。

## 关联子查询（correlated subquery）

注意 EXISTS 子查询里的 `s.dept_id = d.id` —— **`d.id` 是外层引用**。这种"外层 + 内层互相引用"叫**关联子查询**：

```sql
SELECT d.name FROM departments d
WHERE (
  SELECT COUNT(*) FROM students s
  WHERE s.dept_id = d.id
) >= 3;   -- 找有 3+ 学生的部门
```

子查询每次外层换一行就重新算一次。

## 常见错误

1. **EXISTS 子查询忘了 WHERE 条件**：`SELECT 1 FROM students` 永远有行 → 永远 true，逻辑错
2. **NOT IN + NULL**：永远返回空集——见上
3. **EXISTS 配 SELECT 列**：`SELECT name EXISTS(...)` 错；EXISTS 是 WHERE 里的过滤条件，不是 SELECT 的列
4. **混淆 EXISTS 和 IN**：用 EXISTS 时子查询要"关联"（引用外层），IN 时子查询独立

## 现在做练习

5 道题：EXISTS 找有学生的部门、NOT EXISTS 找没人的部门、关联子查询 + COUNT、EXISTS + AND、NOT EXISTS 实现 EXCEPT。
