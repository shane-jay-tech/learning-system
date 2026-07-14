# 字符串（str）

## 字符串就是文字

```python
s = "Hello, World!"
t = '小明'
multi = """这是
跨行的字符串"""
```

单引号、双引号都行；三引号 `"""..."""` 可以跨行。Python 字符串 **不可变**——一旦创建就不能改某一位（要"改"只能造新字符串）。

## 索引和切片（和列表一样）

```python
s = "hello"
s[0]        # 'h'
s[-1]       # 'o'
s[1:4]      # 'ell'
s[::-1]     # 'olleh' —— 反转
len(s)      # 5
```

## 拼接：+ 和 join

```python
"Hello" + ", " + "World"   # 'Hello, World'
"Ha" * 3                    # 'HaHaHa'
" ".join(["a", "b", "c"])  # 'a b c'
```

`join` 是把列表里的字符串用某个分隔符串起来——**单字符串拼接列表元素首选**。

## f-string：格式化输出（最重要）

```python
name = "小明"
age = 18
print(f"{name} is {age} years old")
# 输出：小明 is 18 years old
```

`f"..."` 里 `{ }` 内可以放变量或表达式。常用格式：

```python
pi = 3.14159
f"{pi:.2f}"      # '3.14' —— 保留 2 位小数
f"{42:5d}"        # '   42' —— 占 5 格右对齐
f"{0.95:.1%}"     # '95.0%' —— 百分比
```

## 常用方法

| 方法 | 干啥 |
|---|---|
| `s.upper()` / `s.lower()` | 全大写 / 全小写 |
| `s.strip()` | 去掉首尾空白 |
| `s.split(sep)` | 按 sep 切成列表，省略 sep 默认按空白切 |
| `s.replace(a, b)` | 把 a 全替换成 b |
| `s.startswith(p)` / `s.endswith(p)` | 是否以 p 开头/结尾 |
| `s.count(p)` | p 在 s 里出现几次 |
| `s.find(p)` | p 第一次出现的下标，找不到返 -1 |
| `s.isdigit()` / `s.isalpha()` | 是否全是数字/字母 |

```python
"  Hello, World  ".strip()         # 'Hello, World'
"a,b,c,d".split(",")               # ['a', 'b', 'c', 'd']
"Mississippi".count("s")           # 4
"hello".replace("l", "L")          # 'heLLo'
```

## 遍历字符

```python
for c in "Python":
    print(c, end=" ")
# 输出：P y t h o n
```

字符串可以像列表一样遍历，每次拿一个字符。

## 数字 ↔ 字符串

```python
str(42)       # '42'
str(3.14)     # '3.14'
int("42")     # 42
float("3.14") # 3.14
int("hello")  # ❌ ValueError
```

⚠️ `int("3.5")` 也会报错——只能转**纯整数字符串**；要先 `float` 再 `int`。

## in 子串判断

```python
"ell" in "hello"     # True
"xyz" in "hello"     # False
```

## 常见错误

1. **字符串不可变**：`s[0] = "X"` 报错；要改用切片造新串：`s = "X" + s[1:]`
2. **`split` 默认分隔符**：`"a  b".split()`（无参）会忽略多余空白，得 `['a', 'b']`；`split(" ")` 会保留：`['a', '', 'b']`
3. **大小写敏感**：`"Hello" == "hello"` 是 `False`；要忽略大小写比 `s1.lower() == s2.lower()`
4. **`+` 号拼字符串和数字会出错**：`"年龄" + 18` 报错；要先 `str(18)` 或用 f-string

## 现在做练习

5 道题：大小写转换、数元音、字符串反转、单词替换、词数统计。
