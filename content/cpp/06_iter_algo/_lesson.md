# 迭代器与 algorithm 库

## 迭代器是什么

迭代器（iterator）就是 **"指向容器中某元素的指针"**。所有 STL 容器都支持迭代器接口：

```cpp
vector<int> v = {3, 1, 4, 1, 5};
auto it = v.begin();    // 指向第一个
*it;                    // 取值（解引用）
++it;                   // 走到下一个
it == v.end();          // 是否走到了"末尾之后"
```

`v.begin()` 指向第一个元素；`v.end()` 指向**末尾的下一位**（不要解引用！）。

为什么有迭代器？让 algorithm 库可以**对所有容器统一工作**——无论是 vector、map、set，sort 都用 `(begin, end)` 调用：

```cpp
sort(v.begin(), v.end());            // vector
// set 自带排序，不能 sort
// map 用 begin/end 遍历但不能 sort
```

## algorithm 库：常用函数

```cpp
#include <algorithm>
```

### 排序

```cpp
sort(v.begin(), v.end());                    // 升序
sort(v.begin(), v.end(), greater<int>());    // 降序
sort(v.begin(), v.end(), [](int a, int b){    // 自定义
    return a > b;
});
```

`[](...){...}` 是 **lambda 表达式**——匿名函数，在需要小函数时方便。

### 查找 / 极值

```cpp
find(v.begin(), v.end(), 5);     // 返回迭代器；找不到 == end()
*max_element(v.begin(), v.end());  // 最大值
*min_element(v.begin(), v.end());  // 最小值
count(v.begin(), v.end(), 1);    // 等于 1 的个数
```

### 二分查找（前提：已排序）

```cpp
sort(v.begin(), v.end());
binary_search(v.begin(), v.end(), 5);    // bool：是否存在
```

### 反转 / 求和

```cpp
reverse(v.begin(), v.end());              // 原地反转
accumulate(v.begin(), v.end(), 0);        // 求和（要 <numeric>）
```

### 去重（前提：已排序）

```cpp
sort(v.begin(), v.end());
v.erase(unique(v.begin(), v.end()), v.end());
```

`unique` 把重复元素挪到末尾，返回新末尾迭代器；`erase` 从那截掉。固定套路。

## lambda 表达式（C++11+）

```cpp
auto add = [](int a, int b) { return a + b; };
add(3, 5);    // 8

// 在 sort 里
sort(v.begin(), v.end(), [](int a, int b){ return a > b; });
```

`[]` 是**捕获列表**（这里空，不捕获外部变量）；后跟参数列表 + 函数体。

## 容器算法搭配

```cpp
vector<int> v = {3, 1, 4, 1, 5, 9, 2, 6};

// 删除小于 3 的元素（erase-remove 套路）
v.erase(remove_if(v.begin(), v.end(),
                  [](int x){ return x < 3; }),
        v.end());

// 把每个元素 +1
for_each(v.begin(), v.end(), [](int& x){ x += 1; });
```

## 常见错误

1. **end() 解引用**：`*v.end()` 是未定义行为
2. **修改容器后旧迭代器失效**：`it = v.begin(); v.push_back(...); *it`——某些情况下 it 失效
3. **未排序就 binary_search**：必须先 sort
4. **lambda 捕获引用过期**：`[&]` 捕获的局部变量销毁后用 lambda 会出问题

## 现在做练习

5 道题：sort 降序、find 是否存在、count、reverse、lambda 自定义比较。
