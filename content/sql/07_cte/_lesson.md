# CTE：WITH 公共表表达式

## CTE 解决什么问题

子查询写多了你会发现一个问题——**嵌套太深，根本读不懂**：

```sql
SELECT name FROM students
WHERE dept_id IN (
  SELECT id FROM departments
  WHERE budget > (
    SELECT AVG(budget) FROM departments
  )
);
```

CTE（Common Table Expression）让你**先命名一个临时结果，再用它**：

```sql
WITH big_depts AS (
  SELECT id FROM departments
  WHERE budget > (SELECT AVG(budget) FROM departments)
)
SELECT name FROM students
WHERE dept_id IN (SELECT id FROM big_depts);
```

读起来像"先做这一步，再做那一步"——业务分析师的最爱。

## 基本语法

```sql
WITH 别名 AS (
  SELECT ...
)
SELECT ... FROM 别名;
```

`WITH` 开头，`别名` 起名（像建了张临时视图），`AS (...)` 里写定义，**主查询接在后面**。

## 多个 CTE 串起来

```sql
WITH
  pass_students AS (
    SELECT * FROM students WHERE score >= 60
  ),
  pass_count_by_class AS (
    SELECT class, COUNT(*) AS n FROM pass_students GROUP BY class
  )
SELECT class, n FROM pass_count_by_class WHERE n >= 2;
```

逗号分隔多个 CTE。**后面的能引用前面的**。

## CTE vs 子查询

| 场景 | CTE 优势 |
|---|---|
| 同一个查询用 2-3 次 | 写一次，复用多次 |
| 复杂多层逻辑 | 拆成多步，每步一行思路 |
| 团队协作 | 别人能读懂你的 SQL |

什么时候不用 CTE：**只用一次的简单子查询**——直接子查询更短。

## 递归 CTE（处理树形/层级数据）

```sql
WITH RECURSIVE org_tree AS (
  -- 起点：CEO 没上级
  SELECT id, name, manager_id, 1 AS depth
  FROM employees
  WHERE manager_id IS NULL

  UNION ALL

  -- 递归：每个员工 + 他下属
  SELECT e.id, e.name, e.manager_id, t.depth + 1
  FROM employees e
  JOIN org_tree t ON e.manager_id = t.id
)
SELECT * FROM org_tree ORDER BY depth, id;
```

`WITH RECURSIVE` 关键字开头；`UNION ALL` 把递归基础和递归步连起来。这是 PA "组织架构层级展开"的标准写法。

## CTE 在窗口函数后做过滤

之前我们说"WHERE 不能过滤窗口函数结果"——CTE 解决：

```sql
WITH ranked AS (
  SELECT class, name, score,
         ROW_NUMBER() OVER (PARTITION BY class ORDER BY score DESC) AS rn
  FROM students
)
SELECT class, name, score FROM ranked WHERE rn <= 2;
```

比之前的"派生表"语法可读性更好。

## 常见错误

1. **CTE 别名冲突**：CTE 别名和现有表重名 → 优先用 CTE，可能误伤
2. **WITH 后忘加 AS**：`WITH cte (SELECT ...)` 错；要 `WITH cte AS (SELECT ...)`
3. **递归 CTE 漏 UNION ALL**：递归基础和递归步必须用 UNION ALL 连
4. **递归无终止**：递归 CTE 没"出口"会无穷循环——SQLite 默认有递归深度限制

## 现在做练习

5 道题：单 CTE、多 CTE 串联、CTE 配窗口函数、递归 CTE 算序列、CTE 重命名列。
