# 数组与字符串

## C++ 怎么装一组数据

C++ 装一组数据有两种主流写法：

1. **C 风格数组** `int a[10]`——固定大小、贴近底层
2. **`std::vector<int>`**——动态大小、像 Python 列表

入门阶段我们先用 vector，省心又安全。

## std::vector：动态数组

```cpp
#include <vector>
using namespace std;

vector<int> v = {3, 5, 7};   // 初始化
vector<int> w(5, 0);         // 5 个 0：[0,0,0,0,0]
v.push_back(9);               // 加到末尾：[3,5,7,9]
v.size();                     // 4
v[2];                         // 7（下标从 0 起）
```

vector 比 C 数组好用得多——能动态扩、知道自己多长、调用方法（push_back / pop_back / clear）。

## for 遍历 vector

```cpp
vector<int> v = {3, 5, 7, 11, 14};

// 经典：用下标
for (int i = 0; i < v.size(); i++) {
    cout << v[i] << " ";
}

// 现代：range-for（C++11+）
for (int x : v) {
    cout << x << " ";
}
```

range-for 简洁很多，**没必要拿下标时优先用**。

## std::string：字符串

```cpp
#include <string>
using namespace std;

string s = "Hello";
string t;
cin >> t;             // 读一个不带空格的词
getline(cin, t);      // 读一整行（含空格）

s.size();             // 5
s[0];                 // 'H'
s + " World";         // 拼接：'Hello World'
s += "!";             // 自身追加
```

## 常用字符串方法

```cpp
s.empty();              // 是否空
s.find("ll");           // 子串首次位置；找不到返回 string::npos
s.substr(1, 3);         // 从下标 1 取 3 个字符："ell"
s.length();             // 同 size()
```

## 数组求和的标准写法

```cpp
vector<int> v = {3, 5, 7, 11, 14};
int total = 0;
for (int x : v) total += x;
cout << total;     // 40
```

或者用 STL 的 accumulate：

```cpp
#include <numeric>
int total = accumulate(v.begin(), v.end(), 0);
```

## getline 的坑

读一行字符串时如果之前用了 `cin >> n`，要先 `cin.ignore()` 把残留的换行吃掉：

```cpp
int n;
cin >> n;
cin.ignore();           // 关键！吃掉 n 后的回车
string line;
getline(cin, line);
```

否则 `getline` 会读到一个空行。

## 常见错误

1. **vector 越界访问**：`v[10]` 而 v 长度只有 5——是 **未定义行为**（不会报错但会乱跑）；用 `v.at(10)` 会抛异常
2. **`size()` 是无符号整数**：`for (int i = 0; i < v.size() - 1; ...)` 当 v 为空时 `0 - 1` 溢出成超大数，循环不停。**显式转换为 int 或用 ssize**
3. **`string` 和 char* 混用**：用 string 就用 string，少混
4. **getline 前忘 ignore**：见上

## 现在做练习

5 道题：vector 求和、找最大值、字符串反转、单词数、数字符出现次数。
