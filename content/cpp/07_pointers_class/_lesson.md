# 指针、类、智能指针

## 指针：内存的别名

指针存的是 **内存地址**，可以**远距操控**变量：

```cpp
int x = 42;
int* p = &x;        // p 存 x 的地址
cout << *p;         // 42（解引用：取地址里的值）
*p = 100;           // 修改 x：现在 x = 100
```

`&x` 取地址；`*p` 解引用；`int*` 是"指向 int 的指针"类型。

⚠️ **未初始化的指针**指向随机地址 → 解引用是灾难性的未定义行为。

## nullptr：空指针

```cpp
int* p = nullptr;        // 现代 C++ 标准
if (p) ...                // false（nullptr 当 bool 是 false）
```

老代码用 `NULL` 或 `0`，**新代码一律用 nullptr**——更安全（`NULL` 实际上是 `0`，会和整数混淆）。

## new / delete：手动管理堆内存

```cpp
int* p = new int(42);    // 在堆上分配
cout << *p;
delete p;                 // 必须手动释放！

int* arr = new int[10];   // 数组
delete[] arr;              // 数组要 delete[]
```

⚠️ **每个 new 必须配 delete**，否则**内存泄漏**。

更新潮的做法：**不用 new/delete，用智能指针**（见下）。

## 类（class）

```cpp
class Student {
public:
    string name;
    int score;

    Student(string n, int s) {     // 构造函数
        name = n;
        score = s;
    }

    bool passed() const {            // 成员函数；const 表示不改对象
        return score >= 60;
    }
};

Student a("Alice", 85);
cout << a.passed();    // true
```

- `class` 关键字
- `public:` 访问控制：public 可外面访问；private 只内部
- `Student(...)`：**构造函数**——同名函数，没返回类型，初始化对象
- `const`：成员函数加 `const` 表示"不改对象"

## 析构函数

```cpp
class Buffer {
    int* data;
public:
    Buffer(int n) { data = new int[n]; }
    ~Buffer() { delete[] data; }    // 析构：对象销毁时自动调用
};
```

`~ClassName()` 是析构函数。负责清理资源（释放内存、关文件等）。这就是 C++ 著名的 **RAII 模式**——资源获取即初始化，销毁即释放。

## 智能指针：自动 delete

C++11+ 提供智能指针，**自动释放内存**：

```cpp
#include <memory>

unique_ptr<int> p = make_unique<int>(42);
cout << *p;
// 离开作用域时自动 delete

shared_ptr<int> s = make_shared<int>(100);
shared_ptr<int> s2 = s;     // 引用计数 +1
// 最后一个 shared_ptr 离开时才 delete
```

**现代 C++ 几乎不再用 new/delete**——总是用智能指针。

## 引用 vs 指针

| 引用 `int&` | 指针 `int*` |
|---|---|
| 必须初始化 | 可以为 null |
| 不能改变指向（永远绑定一个对象） | 可改指向（指针可重新赋值） |
| 用 `.` 访问 | 用 `->` 访问 |
| 像别名 | 是地址 |

简单原则：**能用引用就别用指针**。

## 常见错误

1. **野指针**：未初始化或已 delete 的指针——解引用崩溃
2. **double delete**：同一指针 delete 两次
3. **数组用 delete 而非 delete[]**：未定义行为；要 `delete[] arr`
4. **类成员忘了初始化**：构造函数里没赋值的成员是垃圾数据
5. **拷贝包含原始指针的类**：浅拷贝两个对象指向同一块内存，析构时崩

## 现在做练习

5 道题：指针交换、动态数组求和、定义类 + 构造函数、unique_ptr、shared_ptr 引用计数。
