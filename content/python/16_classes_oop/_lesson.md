# 类与面向对象（class / 继承）

## 类是什么

到目前你只用过 Python **内置**的类型：int、str、list、dict。**class** 让你**定义自己的类型**——把"数据 + 操作数据的方法"打包成一个东西。

```python
class Student:
    def __init__(self, name, score):    # 构造函数
        self.name = name
        self.score = score

    def passed(self):
        return self.score >= 60

s = Student("Alice", 85)
print(s.name)         # Alice
print(s.passed())     # True
```

`__init__` 是**构造函数**——`Student("Alice", 85)` 调用时自动跑。`self` 指"当前这个对象"——所有实例方法的第一个参数都是它。

## 实例属性 vs 类属性

```python
class Student:
    school = "ABC University"      # 类属性（所有实例共享）

    def __init__(self, name):
        self.name = name           # 实例属性（每个实例自己的）

a = Student("Alice")
b = Student("Bob")
print(a.school, b.school)   # 都是 "ABC University"
print(a.name, b.name)       # Alice, Bob
```

## 方法的三种调用形式

```python
class Counter:
    count = 0

    def __init__(self):
        Counter.count += 1
        self.id = Counter.count

    def show(self):                  # 实例方法（最常见）
        print(f"id={self.id}")

    @classmethod
    def total(cls):                  # 类方法
        return cls.count

    @staticmethod
    def helper(x):                   # 静态方法（不依赖 self/cls）
        return x * 2

c1 = Counter(); c2 = Counter()
c1.show()              # id=1
print(Counter.total()) # 2
print(Counter.helper(5))  # 10
```

## 继承：复用别人的类

```python
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        print(f"{self.name} makes a sound")

class Dog(Animal):                   # 继承 Animal
    def speak(self):                  # 重写父类方法
        print(f"{self.name} says: Woof!")

d = Dog("Rex")
d.speak()    # Rex says: Woof!
```

`Dog(Animal)` 的括号里写父类。子类自动获得父类的所有属性和方法。

## super：调用父类方法

```python
class Manager(Employee):
    def __init__(self, name, salary, team):
        super().__init__(name, salary)   # 先初始化父类的部分
        self.team = team
```

`super()` 是"父类的代理"——在子类构造函数里调 `super().__init__(...)` 是几乎必做的。

## 特殊方法（魔法方法）

```python
class Money:
    def __init__(self, amount):
        self.amount = amount

    def __repr__(self):              # print 时怎么显示
        return f"Money({self.amount})"

    def __add__(self, other):         # +
        return Money(self.amount + other.amount)

    def __eq__(self, other):          # ==
        return self.amount == other.amount

m1 = Money(100); m2 = Money(50)
print(m1 + m2)      # Money(150)
print(m1 == Money(100))   # True
```

`__xxx__` 是 Python 的"特殊方法"——让你的类**像内置类型一样自然使用**。

## 常见错误

1. **忘了 self**：方法第一个参数必须是 self；不写就成了类方法
2. **直接调用方法名**：`Student.passed()` 缺 self 报错；应 `s.passed()` 或 `Student.passed(s)`
3. **__init__ 里不写 self.xxx 赋值**：实例没有这些属性，调用时 AttributeError
4. **多重继承钻石问题**：避免复杂多继承，用 super() 配合 MRO 解决

## 现在做练习

5 道题：定义 Student 类、加方法、继承、super、运算符重载。
