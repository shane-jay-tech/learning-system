# SQL 字符串函数

## 这一节学什么

PA 报表里 80% 的字段是字符串——姓名、部门、学历、岗位。SQL 提供一套**字符串处理函数**：截取、拼接、替换、模式匹配。

## 长度与截取

```sql
LENGTH(name)              -- 字符长度
SUBSTR(name, 1, 3)         -- 从第 1 位取 3 个（SQLite 1-based）
SUBSTR(name, 2)            -- 从第 2 位到结尾
```

⚠️ SQLite / PostgreSQL 的 SUBSTR 下标从 1 开始；MySQL 也是。

## 拼接

```sql
'Hello, ' || name           -- SQLite/PG: 用 ||
CONCAT('Hello, ', name)     -- MySQL: 用 CONCAT
```

SQLite 用 `||`（双竖线），不是 `+`。

## 大小写

```sql
UPPER(name)
LOWER(name)
```

## 替换

```sql
REPLACE(name, 'Mr.', 'Mr')   -- 替换所有 'Mr.' 为 'Mr'
TRIM(name)                    -- 去首尾空白
LTRIM(name) / RTRIM(name)     -- 去左/右
```

## 模糊匹配：LIKE

```sql
WHERE name LIKE 'A%'          -- 以 A 开头
WHERE name LIKE '%son'         -- 以 son 结尾
WHERE name LIKE '%la%'         -- 包含 la
WHERE name LIKE '_lice'        -- _ 匹配 1 个字符
```

| 通配符 | 含义 |
|---|---|
| `%` | 任意 0+ 字符 |
| `_` | **恰好** 1 个字符 |

要精确匹配 `%` 或 `_` 字面值用 `ESCAPE`：`LIKE '50\%' ESCAPE '\'`。

## 大小写不敏感的 LIKE

```sql
WHERE LOWER(name) LIKE 'a%'    -- 通用做法
WHERE name ILIKE 'a%'           -- PG 专属
```

## 找子串位置

```sql
INSTR(name, 'ce')             -- 'ce' 在 name 中第几位（1-based，0 表示没找到）
```

## 实战：把姓名拆 first/last

```sql
SELECT
  SUBSTR(name, 1, INSTR(name, ' ') - 1) AS first,
  SUBSTR(name, INSTR(name, ' ') + 1) AS last
FROM users;
```

## 数字 ↔ 字符串

```sql
CAST(123 AS TEXT)              -- '123'
CAST('123' AS INTEGER)         -- 123
```

## 常见错误

1. **|| 当算术加号**：`'a' + 1` 在 SQLite 不会报错但行为意外（数字相加，字符串变 0）
2. **LIKE 用错通配符**：忘了 `%` 写 `name LIKE 'A'` 只匹配单字 'A'
3. **LIKE 大小写敏感**：`'A%'` 和 `'a%'` 在严格数据库里不一样
4. **SUBSTR 从 0 还是 1**：跨数据库时易混；SQLite/PG/MySQL 都是 1-based

## 现在做练习

5 道题：LENGTH、SUBSTR 取首字、LIKE 模糊、REPLACE、UPPER 排序。
