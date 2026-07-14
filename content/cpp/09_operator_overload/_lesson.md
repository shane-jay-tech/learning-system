# 运算符重载

## 让自定义类型支持 + - * /

C++ 允许你**给自己定义的类**重载运算符——让 `Money(100) + Money(50)` 像普通加法一样用。

```cpp
class Money {
public:
    int amount;
    Money(int a) : amount(a) {}

    Money operator+(const Money& other) const {
        return Money(amount + other.amount);
    }
};

Money a(100), b(50);
Money c = a + b;   // 实际调 a.operator+(b)
cout << c.amount;  // 150
```

## 二元运算符（最常用）

```cpp
class Vec {
    int x, y;
public:
    Vec(int x, int y) : x(x), y(y) {}

    Vec operator+(const Vec& o) const { return Vec(x + o.x, y + o.y); }
    Vec operator-(const Vec& o) const { return Vec(x - o.x, y - o.y); }
    bool operator==(const Vec& o) const { return x == o.x && y == o.y; }
    bool operator<(const Vec& o) const { return x < o.x || (x == o.x && y < o.y); }
};
```

注意几个习惯：
- 参数 `const T&`：避免拷贝
- 函数本身 `const`（在末尾）：表示不改自身
- 返回新对象（`+ - *`）；`==` 返回 bool

## 流插入运算符 <<

```cpp
class Money {
public:
    int amount;
    Money(int a) : amount(a) {}
};

ostream& operator<<(ostream& os, const Money& m) {
    return os << "$" << m.amount;
}

cout << Money(100);   // $100
```

`<<` 第一个参数是 `ostream&`——所以 **必须** 写在类外（不能成为成员函数）。

## 复合赋值 += 等

```cpp
class Counter {
    int n = 0;
public:
    Counter& operator+=(int x) {     // 注意返回引用
        n += x;
        return *this;
    }
};

Counter c;
c += 5;
c += 3;
```

返回 `*this` 让链式调用 `c += 5 += 3` 也能工作。

## 一元运算符

```cpp
Vec operator-() const { return Vec(-x, -y); }   // 负号
Vec& operator++() {                                // 前缀 ++
    x++; y++;
    return *this;
}
Vec operator++(int) {                              // 后缀 ++（哑参数 int）
    Vec tmp = *this;
    ++(*this);
    return tmp;
}
```

## 下标运算符 []

```cpp
class Array {
    int data[10];
public:
    int& operator[](int i) { return data[i]; }
    const int& operator[](int i) const { return data[i]; }
};

Array a;
a[0] = 100;     // 调用 operator[]
```

## 函数调用运算符 ()

```cpp
class Adder {
    int base;
public:
    Adder(int b) : base(b) {}
    int operator()(int x) const { return base + x; }
};

Adder add5(5);
cout << add5(3);   // 8 —— 像函数一样调用
```

这样的对象叫 **函数对象（functor）**——比 lambda 历史更早，但功能类似。

## 不能重载的

`?:`（三元）、`::`（作用域）、`.`（成员）、`sizeof`、`typeid` —— 这些 C++ 不让你改。

## 常见错误

1. **`+=` 不返回引用**：写成 `Counter operator+=(int)` 链式调用就坏掉
2. **流插入函数没用 `&`**：`ostream operator<<(ostream os, ...)` 错——按值传 ostream 会复制（不允许）
3. **`==` 没加 const**：临时对象 / const 对象比较时编译报错
4. **重载到处都是**：能用普通方法就别重载——让代码更易读

## 现在做练习

5 道题：Money + 重载、Vec ==、operator<<、operator[]、operator()。
