# 表连接（JOIN）

## 为什么需要 JOIN

实际数据库不会把所有信息塞进一张大表——会分成几张相关联的小表（这叫**规范化**）。比如：

- `students(id, name, dept_id, score)`：学生表
- `departments(id, name)`：部门表

学生表里只有 `dept_id`，要显示**部门名字**就得"连接"两张表。这就是 JOIN。

## INNER JOIN：两边都有才显示

```sql
SELECT s.name, d.name AS dept_name
FROM students s
INNER JOIN departments d ON s.dept_id = d.id;
```

逐字解读：

- `students s` 给表起个**别名** s（写起来短）
- `INNER JOIN departments d ON 条件`：把 students 和 departments 连接起来，连接条件是 `s.dept_id = d.id`
- 结果：每个学生一行，**带上对应部门名字**

`INNER`（内）的意思：只保留**两边都匹配上**的行。如果某个学生的 `dept_id` 在 departments 里找不到，那一行不会出现。

## LEFT JOIN：左边全保留，右边没匹配填 NULL

```sql
SELECT s.name, d.name
FROM students s
LEFT JOIN departments d ON s.dept_id = d.id;
```

`LEFT JOIN` 和 `INNER JOIN` 的区别：左边表（students）的**所有行都保留**——即使右边 departments 没匹配，对应列填 `NULL`。

业务场景：
- "所有学生 + 他们的部门（没部门也要列出来）" → LEFT JOIN
- "所有有部门的学生" → INNER JOIN

## 三种 JOIN 速查

| 类型 | 含义 |
|---|---|
| `INNER JOIN` | 两边都有才显示（最常用，**默认**就是 INNER） |
| `LEFT JOIN` | 左表全保留，右表没匹配填 NULL |
| `RIGHT JOIN` | 反过来；不常用，可以用 LEFT JOIN 调换两表代替 |

## ON 条件是什么

```sql
... ON s.dept_id = d.id
```

ON 后面是**连接条件**——告诉数据库"这两张表怎么对上"。最常见就是 "外键 = 主键"。

## 表别名（alias）

```sql
SELECT s.name FROM students AS s ...
```

`AS s` 给表起个短别名，后面用 `s.列名` 引用。`AS` 可省略：`students s`。

⚠️ **多表查询里强烈建议用别名**——同名列时区分清楚（`s.name` vs `d.name`）。

## 多表 JOIN

```sql
SELECT s.name, d.name AS dept, c.name AS course
FROM students s
INNER JOIN departments d ON s.dept_id = d.id
INNER JOIN courses c ON s.course_id = c.id;
```

逐次 JOIN 即可——每个 JOIN 配一个 ON 条件。

## 常见错误

1. **没用别名导致歧义**：两表都有 `name` 列，`SELECT name` 报"列不明确"
2. **ON 写成 WHERE 风格**：`ON s.dept_id = 1` 这种把过滤条件写进 ON——能跑但语义乱；过滤用 WHERE
3. **忘了 INNER 和 LEFT 的区别**：用 INNER 时，**左表 dept_id 为 NULL 的学生会被丢掉**
4. **逗号连接（旧 SQL）**：`FROM students, departments WHERE ...`——能跑但容易写错；**永远用显式 JOIN 关键字**

## 现在做练习

5 道题：INNER JOIN 取部门名、LEFT JOIN 找无部门学生、JOIN+WHERE 综合、3 表 JOIN、JOIN+GROUP BY。
