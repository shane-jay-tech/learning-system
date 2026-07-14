# 生成器与迭代器（yield）

## 生成器是什么

生成器是 **"懒计算"** 的容器——你不一次造完整个序列，而是"用一个给一个"。处理大数据/无穷序列时省内存。

```python
def count_up_to(n):
    i = 1
    while i <= n:
        yield i
        i += 1

for x in count_up_to(5):
    print(x)
# 输出 1 2 3 4 5
```

`yield` 像 `return`，但**函数不结束**——下次调用从这里继续。

## 函数 vs 生成器

```python
def make_list(n):       # 普通函数：一次造好整个列表
    return [i * i for i in range(n)]

def gen_squares(n):     # 生成器：一个一个出
    for i in range(n):
        yield i * i

# n=10000000 时
make_list(10**7)      # 内存占用：~400 MB
sum(gen_squares(10**7))  # 内存占用：极小
```

**有 yield 的函数**自动变成生成器——返回一个生成器对象，不是列表。

## 生成器表达式

```python
squares = (x * x for x in range(5))    # 注意是圆括号不是方括号
sum(squares)    # 30
```

`(...)` 生成器表达式 vs `[...]` 列表推导式——前者懒、后者一次出。

## 用 next 手动取

```python
gen = count_up_to(3)
print(next(gen))    # 1
print(next(gen))    # 2
print(next(gen))    # 3
print(next(gen))    # StopIteration（异常）
```

`for x in gen` 在底层就是循环 `next(gen)` 直到 StopIteration。

## yield from：生成器组合

```python
def chain(*iterables):
    for it in iterables:
        yield from it

list(chain([1,2], [3,4], [5]))   # [1, 2, 3, 4, 5]
```

`yield from xxx` 把另一个可迭代对象的所有值"转交"给当前生成器。

## itertools 库（生成器的瑞士军刀）

```python
import itertools

itertools.count(1)         # 1, 2, 3, ... 无穷
itertools.cycle("AB")      # A, B, A, B, ...
itertools.repeat(0, 5)     # 0, 0, 0, 0, 0
itertools.chain([1,2], [3,4])
itertools.islice(gen, 10)  # 取前 10 个

# 组合数学
list(itertools.combinations([1,2,3], 2))   # [(1,2), (1,3), (2,3)]
list(itertools.permutations([1,2,3], 2))   # [(1,2),(1,3),(2,1),(2,3),(3,1),(3,2)]
```

## 自定义迭代器（class）

```python
class Countdown:
    def __init__(self, n):
        self.n = n

    def __iter__(self):
        return self

    def __next__(self):
        if self.n <= 0:
            raise StopIteration
        v = self.n
        self.n -= 1
        return v

list(Countdown(3))   # [3, 2, 1]
```

但 99% 情况用 `yield` 写生成器函数更短。

## 常见错误

1. **生成器只能消费一次**：`gen = gen_squares(5); list(gen); list(gen)` 第二次得空——生成器走到末尾就废了
2. **混淆 `yield` 和 `return`**：return 在生成器里表示结束（不是返回值）
3. **生成器表达式用方括号**：`[x*x for x in range(5)]` 是列表（占内存），`(x*x for x in range(5))` 才是生成器
4. **next 不接 try 漏 StopIteration**：手动 next 时要捕获

## 现在做练习

5 道题：写斐波那契生成器、生成器表达式求平方和、yield from 合并、itertools.combinations 组合数、自己写迭代器类。
