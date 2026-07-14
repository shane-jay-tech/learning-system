# 函数（def / return）

## 函数解决的是什么问题

到现在你写的代码都是"一次性脚本"——一行一行执行。可如果你需要**多次做同一件事**呢？

- 算 5 个圆的面积——重复 5 次同样的公式
- 在多个地方判断"是不是闰年"——同样的逻辑写好几遍
- 不同情况下都要把"摄氏度转华氏度"

复制粘贴看似快，但只要逻辑一改，你就要找出所有副本一个个改。**函数** 就是把"做一件事的方法"打包，给它起个名字，以后想做就直接喊名字。

## 第一个函数

```python
def add(a, b):
    return a + b

print(add(3, 5))    # 输出 8
print(add(10, 20))  # 输出 30
```

逐字解读：

- `def` 是 "**def**ine"（定义）的意思
- `add` 是函数名（自己起，规则同变量名）
- 括号里的 `a, b` 是 **参数**（这次调用要传给我什么）
- 冒号 `:` 不能少
- 函数体要 **缩进**（4 个空格）
- `return` 把结果"送出去"
- `add(3, 5)` 是 **调用** 函数

## return：把结果送出去

```python
def square(x):
    return x * x

result = square(7)      # result 现在是 49
print(square(7) + 1)    # 输出 50
```

`return` 后面跟着的值就是这次调用的"产出"。一旦执行 `return`，函数立即结束（后面的代码不会跑）。

如果函数没写 `return`，Python 默认返回 `None`：

```python
def greet(name):
    print(f"Hello, {name}!")
    # 没有 return

x = greet("Alice")    # 屏幕打印：Hello, Alice!
print(x)              # 输出：None
```

## 默认参数值

参数可以预设默认值，调用时不传就用默认：

```python
def power(base, exp=2):
    return base ** exp

print(power(5))       # 不传 exp → 默认是 2 → 5² = 25
print(power(5, 3))    # 显式传 → 5³ = 125
```

## 函数能让条件判断更整洁

回想 `02_conditionals` 里你写的奇偶判断：

```python
n = 7
if n % 2 == 0:
    print("even")
else:
    print("odd")
```

包成函数后：

```python
def parity(n):
    if n % 2 == 0:
        return "even"
    else:
        return "odd"

print(parity(7))    # odd
print(parity(8))    # even
```

好处：要判 5 个数的奇偶，不用复制 5 遍 if-else，写 5 行 `parity(...)` 就行。

## 多个 return：早退

函数可以有多个 `return`——哪个先执行就用哪个，**之后的代码不再执行**：

```python
def is_positive(n):
    if n > 0:
        return True
    return False

print(is_positive(5))    # True
print(is_positive(-3))   # False
```

这种"提前退出"在判断类函数里特别常用，可读性比写一个长 if-else 强。

## 局部变量 vs 全局变量

函数里定义的变量**只在函数内有效**：

```python
def calc():
    x = 10        # 局部变量，只在 calc 里能用
    return x * 2

print(calc())     # 20
print(x)          # NameError: x 在外面看不见
```

这是好事——不同函数互不干扰，互不污染。

## 函数命名建议

- **小写 + 下划线**：`is_prime`、`calc_total`、`format_name`
- **动词开头**（动作）：`get_user`、`compute_avg`、`print_table`
- **bool 返回的常用 `is_` / `has_`**：`is_empty`、`has_permission`

## 常见错误

1. **忘了 `return`**：函数算出结果但没 return，调用方拿到 `None`
2. **return 后面还有代码**：return 已经退出了，那些代码永远不会跑
3. **直接用 print 而不 return**：print 只是显示，return 才能"被外面拿来用"。要让函数能参与计算，**用 return**
4. **参数顺序乱**：调用 `add(3, 5)` 时，3 给 a，5 给 b。位置不要弄反

## 现在做练习

5 道题：写 5 个函数，从最简单的两数相加开始，到判断质数、求平均。
