# 移动语义（move / 右值引用）

## 问题：拷贝太贵

```cpp
vector<int> make_big() {
    vector<int> v(1000000);
    return v;     // 返回时拷贝整个 vector？
}

vector<int> w = make_big();
```

历史上 C++ 这种返回大对象的代码会**深拷贝**百万元素——超慢。**移动语义**（C++11+）让我们说"v 反正快没了，把它的内部指针**搬**给 w 就行"。

## 左值与右值

- **左值**：有名字的对象（`int x = 5`，x 是左值）
- **右值**：临时的、马上要消失的（`5`、`x + 1`、`make_big()` 的返回值）

```cpp
int a = 5;       // a 是左值，5 是右值
int b = a;       // 拷贝 a
int c = a + 1;   // a + 1 是右值
```

## 右值引用 T&&

```cpp
void take(int& x);     // 接左值
void take(int&& x);    // 接右值

take(5);               // 5 是右值 → 调右值版
int a = 10;
take(a);               // a 是左值 → 调左值版
```

`T&&` 是右值引用——**只接右值**。

## 移动构造 / 移动赋值

```cpp
class Buffer {
    int* data;
    size_t size;
public:
    // 拷贝构造（深拷贝）
    Buffer(const Buffer& o) {
        size = o.size;
        data = new int[size];
        for (size_t i = 0; i < size; i++) data[i] = o.data[i];
    }

    // 移动构造（偷指针）
    Buffer(Buffer&& o) noexcept {
        data = o.data;
        size = o.size;
        o.data = nullptr;       // o 不再拥有
        o.size = 0;
    }

    ~Buffer() { delete[] data; }
};
```

移动构造的关键：
1. **接管**对方的资源（拿指针）
2. **置 nullptr**对方的资源（避免双重 delete）
3. **noexcept**：标准库容器只在移动构造 noexcept 时才用移动而非拷贝

## std::move：把左值"变"右值

```cpp
vector<int> a = {1,2,3};
vector<int> b = a;             // 拷贝（a 还在）
vector<int> c = std::move(a);  // 移动（a 被掏空）
// a 现在是空 vector（用 a 不会崩，但内容是不确定的）
```

`std::move(x)` **不真的移动**——它只是把 x 强转为右值引用，让"移动构造"被选中。

## 编译器自动用移动的场景

```cpp
vector<int> v = make_big();   // 返回值优化（NRVO/RVO）+ 移动构造
v.push_back(42);              // 临时 int → 走 push_back(T&&) 移动版
```

通常**不需要手写 move**——返回值、push_back 临时对象、emplace_back 都自动用移动。

## 何时显式用 std::move

```cpp
class Wrapper {
    string name;
public:
    Wrapper(string n) : name(std::move(n)) {}   // 接收值参数后 move 给成员
};
```

**接受**值参数 + **存到**成员时——`std::move` 把值参数搬进去而非拷贝。

## 移动后对象状态

```cpp
string s = "hello";
string t = std::move(s);
// 对 s 还能用，但内容不确定（可能是空，也可能是 "hello"）
// 标准只保证 s 处于"有效但未指定"状态
```

**移动后的对象，唯一安全做的是赋新值或析构**。

## 常见错误

1. **移动后还用原对象**：`auto v = std::move(w); cout << w[0];`——w 内容未定义
2. **const T&& 没意义**：const 让你不能改 → 也就不能移动；用 const T& 即可
3. **手写移动构造没 nullptr**：导致原对象析构时 delete 同一指针 → double-free
4. **移动构造没 noexcept**：vector 等容器扩容时会退回拷贝，移动语义白做了

## 现在做练习

5 道题：std::move 把字符串搬给 vector、识别左值右值、移动 vs 拷贝计数、移动后对象、emplace_back vs push_back。
