# 日期与时间处理

Python 的 `datetime` 模块让你能解析、计算和格式化日期时间。在 HR 数据分析中，入职日期、工龄、考勤统计都离不开它。

## 核心类

```python
from datetime import date, datetime, timedelta

# 今天的日期
today = date.today()

# 创建特定日期
hire_date = date(2023, 3, 15)

# 日期差
tenure = today - hire_date
print(tenure.days)  # 工龄天数
```

## 字符串 ↔ 日期

```python
# 字符串 → 日期
dt = datetime.strptime("2024-01-15", "%Y-%m-%d")

# 日期 → 字符串
s = dt.strftime("%Y年%m月%d日")  # "2024年01月15日"
```

## 常用格式码

| 码 | 含义 | 示例 |
|----|------|------|
| `%Y` | 四位年 | 2024 |
| `%m` | 两位月 | 03 |
| `%d` | 两位日 | 15 |
| `%H` | 小时(24h) | 14 |
| `%M` | 分钟 | 30 |

## timedelta 做日期运算

```python
from datetime import timedelta

tomorrow = date.today() + timedelta(days=1)
last_week = date.today() - timedelta(weeks=1)
```
