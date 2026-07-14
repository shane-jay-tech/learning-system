# C++ STL 基础（vector / map / set / string）

## STL 是什么

**STL（Standard Template Library，标准模板库）** 是 C++ 自带的"瑞士军刀"——提供了 vector、map、set、string、algorithm 这些常用工具。学好 STL 是从"会写 C++ 语法"跨到"能写实用程序"的关键。

## vector 进阶

```cpp
#include <vector>
vector<int> v = {3, 1, 4, 1, 5};

v.size();           // 5
v.empty();          // false
v.front();          // 3（第一个）
v.back();           // 5（最后一个）
v.push_back(9);     // 末尾添加
v.pop_back();       // 删末尾
v.clear();          // 清空
v.resize(10, 0);    // 调整大小到 10，新增的填 0
```

## map：键值对查找

```cpp
#include <map>
map<string, int> ages;
ages["Alice"] = 25;
ages["Bob"] = 30;

ages["Alice"];        // 25
ages.count("Cathy");  // 0（不存在）
ages.size();          // 2
ages.find("Bob");     // 返回迭代器；用 != end() 判断存在

// 遍历
for (const auto& [name, age] : ages) {
    cout << name << " " << age << endl;
}
```

`map` **按 key 自动升序** 排列。要不排序的用 `unordered_map`（哈希表，更快）。

## set：去重 + 自动排序

```cpp
#include <set>
set<int> s = {3, 1, 4, 1, 5};
// s 内部存储是 {1, 3, 4, 5}（去重 + 升序）

s.insert(2);
s.count(3);     // 1
s.size();       // 5
```

`set` 也按值升序；`unordered_set` 不排序。

## string 进阶

```cpp
string s = "Hello World";
s.size();              // 11
s.substr(6, 5);        // "World"（从 6 取 5 个）
s.find("World");       // 6
s.replace(0, 5, "Hi"); // "Hi World"

// 拼接和数字转字符串
string n_str = to_string(42);   // "42"
int n = stoi("100");             // 100
```

## auto 关键字

C++11+ 支持 `auto`：让编译器自动推导类型，省得写 `vector<int>::iterator` 这种长名字：

```cpp
auto it = v.begin();
auto m = ages.find("Bob");
for (auto x : v) cout << x;
```

## 范围 for（range-for）

遍历容器最简洁的方式：

```cpp
vector<int> v = {1, 2, 3};
for (auto x : v) cout << x << " ";       // 复制每个元素
for (auto& x : v) x *= 2;                 // 引用，可以改 v
for (const auto& x : v) cout << x;        // 不改也不复制（最快）
```

`const auto&` 是迭代大对象的标准写法。

## 常见错误

1. **vector 越界**：`v[10]` 当 v 只有 5 个元素 → 未定义行为；用 `v.at(10)` 抛异常
2. **map 用 `[]` 取不存在的 key**：会**自动插入**那个 key（默认值），改变了 map！查询用 `find()` 或 `count()` 更安全
3. **size() 是无符号**：`for (int i = 0; i < v.size() - 1; ...)` 当 v 空时 -1 变成超大数 → 死循环
4. **range-for 不带 `&` 修改不生效**：`for (auto x : v) x = 0;` 改的是副本，原 v 不变；要 `auto& x`

## 现在做练习

5 道题：vector 排序、map 词频、set 去重、string substr、累加 algorithm。
