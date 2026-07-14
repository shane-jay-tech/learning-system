# stringr + lubridate：字符串与日期

## stringr：一致的字符串接口

R 自带的字符串函数（`grep`、`gsub`、`substr`）参数顺序乱七八糟。`stringr` 提供统一的 `str_*` 系列：

```r
library(stringr)

str_length("hello")              # 5
str_to_upper("hello")             # "HELLO"
str_to_lower("HELLO")             # "hello"
str_sub("hello", 1, 3)            # "hel"
str_replace("a-b-c", "-", "/")     # "a/b-c"（第一个）
str_replace_all("a-b-c", "-", "/") # "a/b/c"
str_split("a,b,c", ",")            # list("a","b","c")
str_trim("  hello  ")              # "hello"
str_pad("5", 3, pad="0")           # "005"
```

记忆：**所有 stringr 函数都以 `str_` 开头，第一个参数永远是字符串向量**。

## str_detect / str_subset

```r
v <- c("apple", "banana", "cherry")
str_detect(v, "an")          # c(FALSE, TRUE, FALSE)
str_subset(v, "an")           # c("banana")
```

## 正则替换

```r
str_replace_all("phone 13812345678", "\\d", "*")
# "phone ***********"
```

stringr 用 ICU 正则——和 `re` 类似但更现代。

## lubridate：日期处理

R 自带的 `as.Date` 慢且不友好。`lubridate` 让日期解析、加减、提取都更直观：

```r
library(lubridate)

d <- ymd("2026-05-29")        # 解析年-月-日
d <- mdy("05/29/2026")         # 月/日/年
d <- dmy("29-05-2026")         # 日-月-年
d <- ymd_hms("2026-05-29 14:30:00")  # 含时分秒
```

## 提取日期分量

```r
year(d)        # 2026
month(d)       # 5
day(d)         # 29
wday(d)        # 周几（默认 1=周日, 7=周六）
wday(d, label = TRUE)   # 直接给"Sun"/"Mon"
```

## 日期算术

```r
d + days(7)            # 7 天后
d + months(2)          # 2 个月后
d - years(1)           # 1 年前
interval(d1, d2)        # 区间
as.numeric(d2 - d1, units = "days")  # 天数差
```

## 时长 vs 期间

```r
duration(7, "days")    # 物理时间（精确秒数）
period(7, "days")      # 日历时间（处理夏令时等）
```

99% 用 `period`（更符合直觉）。

## 当前时间

```r
now()                  # 当前时刻
today()                # 今天日期
```

## 实战：算工龄

```r
employees <- data.frame(
  name = c("Alice", "Bob"),
  hire_date = c("2024-01-15", "2024-06-20")
)
employees$years <- as.numeric(today() - ymd(employees$hire_date), units = "days") / 365.25
```

## 常见错误

1. **`as.Date()` vs `ymd()`**：as.Date 慢且要指定 format；优先用 lubridate
2. **stringr 函数和 base R 同名**：`library(stringr)` 后 `str_replace` 是 stringr 的；用 :: 防冲突
3. **wday 周首日因区域不同**：默认 1=周日（美式）；中国习惯 1=周一，加 `week_start = 1`
4. **时区陷阱**：`ymd_hms` 默认 UTC；本地化用 `tz = "Asia/Shanghai"`

## 现在做练习

5 道题：str_to_upper、str_replace_all、ymd 解析 + 提取月、日期相差天数、str_detect 过滤。
