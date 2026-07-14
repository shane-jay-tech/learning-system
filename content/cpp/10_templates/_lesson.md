# 模板（template）

## 模板解决什么

写完 `int max(int a, int b)` 后，你还要写 `double max(double a, double b)`、`string max(string, string)`...这就是 C++ 没模板时的窘境。

模板让你**写一次代码，编译期生成多个版本**：

```cpp
template <typename T>
T max(T a, T b) {
    return a > b ? a : b;
}

max(3, 5);          // T = int
max(3.14, 2.71);    // T = double
max(string("a"), string("b"));   // T = string
```

`template <typename T>` 声明 T 是类型参数；调用时编译器**根据参数类型推导 T**。

## 类模板

```cpp
template <typename T>
class Box {
    T value;
public:
    Box(T v) : value(v) {}
    T get() const { return value; }
};

Box<int> bi(42);
Box<string> bs("hello");
```

类模板**实例化时**必须显式给类型：`Box<int>` 不是 `Box`。

## 多个类型参数

```cpp
template <typename K, typename V>
class Pair {
    K key;
    V val;
public:
    Pair(K k, V v) : key(k), val(v) {}
    K first() const { return key; }
    V second() const { return val; }
};

Pair<string, int> p("Alice", 25);
```

## STL 全靠模板

```cpp
vector<int> v;          // vector 是模板，T = int
map<string, int> m;     // map 是模板 <K, V>
unique_ptr<MyClass> p;
```

你之前用过的 STL 容器**全是模板**。所以 `vector<int>` 和 `vector<string>` 是**两个不同类型**，但代码完全一致。

## 函数模板的非类型参数

```cpp
template <typename T, int N>
class FixedArray {
    T data[N];
public:
    int size() const { return N; }
};

FixedArray<int, 10> arr;     // 编译期 N=10
```

`int N` 是**编译期常量**——不是类型，是值。

## 编译期检查

模板代码只有**用到时**才生成：

```cpp
template <typename T>
T max(T a, T b) {
    return a > b ? a : b;
}

struct Foo {};       // Foo 没定义 >
max(Foo{}, Foo{});   // 编译错误：no operator > for Foo
```

错误信息一长串——是模板的常见痛点。

## constexpr 函数（顺带）

```cpp
constexpr int square(int x) {
    return x * x;
}

constexpr int N = square(5);    // 25，编译期算
int arr[square(3)];              // arr[9]，编译期常量
```

`constexpr` 函数能在编译期算——和模板配合做"零成本抽象"。

## 常见错误

1. **类模板用 ≠ 函数模板**：`Box(42)` 错（C++17 前），要 `Box<int>(42)`；C++17 起 CTAD 能推导
2. **模板写在 cpp 里**：模板**必须写在头文件**——否则其他文件编译时找不到生成的代码
3. **错误信息海量**：耐心看第一行错误，往往是 "no matching function" 之类
4. **特化和重载混淆**：模板特化（`template<> ...`）和函数重载是不同概念

## 现在做练习

5 道题：函数模板 max、类模板 Box、Pair 多参数、求和模板、模板特化（高级）。
