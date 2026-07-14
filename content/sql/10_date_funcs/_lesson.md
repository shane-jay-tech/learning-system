# SQL 日期函数

## 日期在数据库里

PA 分析里几乎每张表都有日期列——入职日期、离职日期、问卷答题日期、报销日期。**日期函数**让你算"工龄""留存天数""按月/季度统计"。

SQLite 的日期通常存为 **TEXT 字符串**（ISO 格式 'YYYY-MM-DD'）或 Unix 时间戳。

## 当前时间

```sql
SELECT DATE('now');           -- 今日：'2026-05-29'
SELECT TIME('now');           -- 当前时分秒
SELECT DATETIME('now');       -- '2026-05-29 12:34:56'
SELECT DATE('now', '-7 days');  -- 7 天前
```

## STRFTIME：格式化与提取

```sql
STRFTIME('%Y', date)       -- 年（'2026'）
STRFTIME('%m', date)       -- 月（'05'）
STRFTIME('%d', date)       -- 日（'29'）
STRFTIME('%Y-%m', date)    -- 年-月（'2026-05'）适合按月分组
STRFTIME('%w', date)       -- 周几（0=周日, 1-6=周一到周六）
```

## 日期算术

```sql
-- 计算两个日期相差天数
SELECT JULIANDAY('2026-05-29') - JULIANDAY('2026-01-01');   -- 148

-- 加减时间
DATE(hire_date, '+30 days')
DATE(hire_date, '+1 year')
DATE(hire_date, '-3 months')
DATE(hire_date, 'start of month')   -- 当月 1 号
```

`JULIANDAY` 把日期转成"儒略日"（一个浮点数），相减得天数差。

## 工龄计算

```sql
SELECT name,
  CAST((JULIANDAY('now') - JULIANDAY(hire_date)) / 365.25 AS INTEGER) AS years
FROM employees;
```

`CAST(... AS INTEGER)` 把浮点向下取整。

## 按月统计（Cohort）

```sql
SELECT STRFTIME('%Y-%m', hire_date) AS month,
       COUNT(*) AS hires
FROM employees
GROUP BY month
ORDER BY month;
```

输出每月新员工数——HR 月度报表的标准写法。

## 留存分析

```sql
-- 入职 90 天后还在职
SELECT COUNT(*) FROM employees
WHERE leave_date IS NULL
   OR JULIANDAY(leave_date) - JULIANDAY(hire_date) >= 90;
```

## 常见错误

1. **日期当字符串比较**：`hire_date >= '2026-01-01'` 在 ISO 格式下能工作（按字典序刚好对齐时间），但其他格式不一定
2. **STRFTIME 占位符大小写**：`%y` 是 2 位年（'26'），`%Y` 是 4 位年（'2026'）
3. **'now' 是 UTC**：SQLite 默认 UTC；要本地时间用 `'now', 'localtime'`
4. **JULIANDAY 跨标准时间转换**：DST 切换会出现非整数天差

## 现在做练习

5 道题：DATE('now')、STRFTIME 提取月、JULIANDAY 算工龄、按月分组、最近 30 天。
