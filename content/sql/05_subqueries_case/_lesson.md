# 子查询 + CASE WHEN

## 子查询：查询里嵌查询

子查询就是**把一个 SELECT 包在另一个 SELECT 里面**当条件用。

### WHERE 里的子查询

"找出比平均分高的学生"——你需要先算平均分（一个数），再用它过滤：

```sql
SELECT name, score FROM students
WHERE score > (SELECT AVG(score) FROM students);
```

括号里的 `SELECT AVG(score) FROM students` 先跑一次出一个数（比如 81.8），然后外层把它当常量比较。

### IN 里的子查询

"找出 HR 部门或 Eng 部门的学生"：

```sql
SELECT name FROM students
WHERE dept_id IN (SELECT id FROM departments WHERE name IN ('HR', 'Eng'));
```

子查询返回**一列多行**，外层用 IN 判断。

### FROM 里的子查询（派生表）

```sql
SELECT MAX(avg_score)
FROM (SELECT class, AVG(score) AS avg_score FROM students GROUP BY class) t;
```

子查询的结果可以当一张**临时表** `t` 来用。

## CASE WHEN：行级条件表达式

`CASE WHEN` 是 SQL 的"if-else"，在 SELECT 里给行打上分类标签：

```sql
SELECT name, score,
  CASE
    WHEN score >= 90 THEN 'A'
    WHEN score >= 80 THEN 'B'
    WHEN score >= 60 THEN 'C'
    ELSE 'F'
  END AS grade
FROM students;
```

逐子句：
- `CASE` 开始
- 多个 `WHEN 条件 THEN 值`
- 可选 `ELSE 默认值`
- `END` 结束（必须）
- `AS grade` 起别名

## CASE 在聚合里的妙用

"统计及格人数 vs 不及格人数"：

```sql
SELECT
  SUM(CASE WHEN score >= 60 THEN 1 ELSE 0 END) AS pass_n,
  SUM(CASE WHEN score < 60  THEN 1 ELSE 0 END) AS fail_n
FROM students;
```

把 `CASE` 包在 `SUM` 里 — 满足条件计 1 否则 0，加起来就是计数。这是分析常用招式。

## 简短 CASE（switch 风格）

```sql
SELECT name,
  CASE dept_id
    WHEN 1 THEN 'HR'
    WHEN 2 THEN 'Eng'
    ELSE 'Other'
  END AS dept
FROM students;
```

适合"对一列等值匹配"的场景。

## 常见错误

1. **CASE 没 END**：编译器报"语法错误 near ..."
2. **WHERE 子查询返回多行用 ='**：`WHERE x = (SELECT ...)` 子查询返回多行就报错；用 IN
3. **FROM 子查询没起别名**：`FROM (SELECT ...)` 必须 `FROM (SELECT ...) t`
4. **子查询每行都跑一次**：相关子查询性能差，能改 JOIN 就改 JOIN

## 现在做练习

5 道题：高于平均、IN 子查询、FROM 派生表、CASE 等级、CASE 计数。
