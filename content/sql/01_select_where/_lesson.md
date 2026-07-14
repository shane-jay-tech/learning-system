# SELECT 与 WHERE

## SQL 是什么

SQL（读作"S-Q-L"或"sequel"）是 **结构化查询语言**，专门用来跟数据库打交道。你可以把数据库想象成一个"超级 Excel"——里面有很多张表，每张表都有列名（字段）和很多行（记录）。SQL 就是你跟这个超级 Excel 说话的语言：你说"把成绩 90 分以上的人列出来"，它就吐给你一张筛好的表。

学 SQL 的实际用处特别大：分析订单数据、查用户行为、做财务报表、看运营指标——只要数据躺在数据库里，SQL 就是你拿到它的钥匙。

## 我们的练习表

本节练习里我们准备了一张 `students`（学生）表，每次提交时它会自动建好：

| id | name  | score |
|----|-------|-------|
| 1  | Alice | 92    |
| 2  | Bob   | 87    |
| 3  | Cathy | 75    |
| 4  | David | 60    |
| 5  | Eve   | 95    |

三个列：`id`（学号）、`name`（姓名）、`score`（成绩）。

## SELECT：查哪些列

`SELECT` 是"选择"的意思，用来指定**你想看哪些列**。

```sql
SELECT * FROM students;
```

- `*`（星号）= 全部列
- `FROM students` 告诉数据库"从 students 这张表里查"
- 末尾的分号 `;` 是 SQL 一句话的结尾

如果你只想看姓名一列：

```sql
SELECT name FROM students;
```

想看姓名和成绩两列，用逗号隔开：

```sql
SELECT name, score FROM students;
```

## WHERE：筛掉不要的行

`SELECT` 决定列，`WHERE` 决定行。它后面跟一个条件，**只留下满足条件的行**。

```sql
SELECT name FROM students WHERE score >= 80;
```

这句话翻译成中文：从 `students` 表里，找出 `score` 大于等于 80 的人，只显示 `name` 列。

WHERE 里能用的比较运算符：

| 符号  | 含义       |
|-----|----------|
| `=`   | 等于（不是 ==）|
| `<>` 或 `!=` | 不等于  |
| `>`   | 大于       |
| `<`   | 小于       |
| `>=`  | 大于等于    |
| `<=`  | 小于等于    |

**字符串比较** 要用单引号包起来：

```sql
SELECT * FROM students WHERE name = 'Alice';
```

## 几个新手要知道的细节

1. **关键字大小写不敏感**：`SELECT` 和 `select` 一样能跑。但**约定**关键字大写，让查询更易读
2. **表名/列名建议精确大小写**：虽然 SQLite 比较宽松，到了正经数据库（PostgreSQL）就严格了
3. **分号** `;` 在我们这里可加可不加；多句 SQL 之间必须加分号
4. **字符串只用单引号** `'Alice'`，不用双引号

## 常见错误

- `WHERE score = '80'` —— 把数字当字符串比较，可能出意外结果。数字就用数字
- `SELECT name, FROM students` —— 多了一个逗号，表头前不要加逗号
- `SELECT * WHERE score > 80` —— 漏了 `FROM students`

## 开始练习

下面两道题：先把全表查出来，再用 WHERE 筛出 80 分以上的同学姓名。做完之后你就掌握了 SQL 最常用的 80% 操作。
