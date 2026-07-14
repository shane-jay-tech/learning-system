# 装饰器与 property

## 装饰器：给函数"加层皮"

装饰器是 Python 的"代码增强器"——**在不改原函数的情况下，给它加额外行为**。

```python
def log_call(func):
    def wrapper(*args, **kwargs):
        print(f"调用 {func.__name__}")
        result = func(*args, **kwargs)
        print(f"返回 {result}")
        return result
    return wrapper

@log_call
def add(a, b):
    return a + b

add(3, 5)
# 调用 add
# 返回 8
```

`@log_call` 等价于 `add = log_call(add)`——把 add 替换成 wrapper。

## *args, **kwargs：接收任意参数

装饰器要兼容**任何参数列表**的函数，所以用 `*args, **kwargs`：
- `*args` 接收任意位置参数（变成元组）
- `**kwargs` 接收任意关键字参数（变成字典）

```python
def f(*args, **kwargs):
    print(args, kwargs)

f(1, 2, x=10)
# (1, 2) {'x': 10}
```

## 常用内置装饰器

```python
@staticmethod        # 类的静态方法（不需要 self/cls）
@classmethod         # 类方法（第一个参数 cls）
@property             # 把方法变成属性（不带括号调用）
@functools.lru_cache  # 自动缓存函数结果
```

## @property：方法当属性用

```python
class Circle:
    def __init__(self, radius):
        self.radius = radius

    @property
    def area(self):
        return 3.14159 * self.radius ** 2

c = Circle(5)
print(c.area)        # 78.53975 —— 注意没有括号
```

为什么要这样？让 `c.area` 看起来像普通属性，但底层是计算（不存值）。半径变了 area 自动变。

加 setter 还能控制赋值：

```python
class Temperature:
    def __init__(self):
        self._c = 0

    @property
    def celsius(self):
        return self._c

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("too cold")
        self._c = value

t = Temperature()
t.celsius = 25     # 走 setter
print(t.celsius)   # 25
```

## 写带参数的装饰器（高级）

```python
def repeat(n):
    def deco(func):
        def wrapper(*args, **kwargs):
            for _ in range(n):
                func(*args, **kwargs)
        return wrapper
    return deco

@repeat(3)
def hello():
    print("hi")

hello()   # 打印 3 次 hi
```

三层嵌套：`repeat(3)` 返回 `deco`，`deco(hello)` 返回 `wrapper`。

## functools.wraps：保留原函数信息

```python
import functools

def my_decorator(func):
    @functools.wraps(func)        # 关键
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

不加 `@functools.wraps`，被装饰的函数的 `__name__` / `__doc__` 会变成 wrapper 的——调试时混乱。

## 常见错误

1. **wrapper 忘了 return**：被装饰函数有返回值时，wrapper 不 return 就丢了
2. **`@xxx()` vs `@xxx`**：带参数装饰器用 `@xxx(args)`；普通的用 `@xxx`
3. **property 改值不生效**：`c.area = 100` 报错——没写 setter
4. **lru_cache 用在有副作用的函数上**：缓存了第一次结果，后续调用不再跑——副作用消失

## 现在做练习

5 道题：写计时装饰器、用 functools.wraps、@property、@property + setter、带参数装饰器。
