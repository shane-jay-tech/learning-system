# 函数（C++）

## 函数：把一段逻辑打包

```cpp
int add(int a, int b) {
    return a + b;
}

int main() {
    cout << add(3, 5) << endl;   // 8
    return 0;
}
```

C++ 函数比 Python 严格——必须**先声明返回类型、参数类型**。

形式：

```cpp
返回类型 函数名(参数类型 参数1, 参数类型 参数2) {
    // 函数体
    return ...;
}
```

## 返回类型 void：不返回值

如果函数只做事，不返回结果：

```cpp
void greet(string name) {
    cout << "Hello, " << name << endl;
}
```

`void` 表示"无返回值"。这种函数调用时不能用在赋值语句右边。

## 引用参数：让函数能改外面的值

```cpp
void add_one(int& x) {    // 注意 & 符号
    x += 1;
}

int main() {
    int n = 5;
    add_one(n);
    cout << n;    // 6 —— n 被函数改了
}
```

`int& x` 表示"x 是外面那个变量本身的别名"，函数里改 x 等于改外面那个变量。

不带 `&` 是**值传递**——函数收到的是个副本，怎么改都不影响外面：

```cpp
void try_change(int x) { x = 99; }  // 没 &，传副本
int n = 5;
try_change(n);
cout << n;   // 还是 5
```

## const 引用：能读不能改

传大对象（vector/string）时为了**省内存**，用 `const T&`：

```cpp
int sum(const vector<int>& v) {
    int total = 0;
    for (int x : v) total += x;
    return total;
}
```

`const` 保证函数不会改 v；`&` 避免拷贝整个 vector。这是 C++ 传 vector/string 的**标准写法**。

## 函数声明（前向）

如果 main 在前面要先用 add，但 add 定义在后面，需要先**声明**：

```cpp
int add(int, int);    // 函数声明（参数名可省）

int main() {
    cout << add(3, 5);
    return 0;
}

int add(int a, int b) {   // 实现
    return a + b;
}
```

## 默认参数

```cpp
int power(int base, int exp = 2) {
    int result = 1;
    for (int i = 0; i < exp; i++) result *= base;
    return result;
}

power(5);     // 25 —— exp 用默认值 2
power(5, 3);  // 125
```

## 递归

函数调用自己。算阶乘的经典写法：

```cpp
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
```

⚠️ 递归必须有"出口"（base case），否则栈溢出。

## 函数重载（overload）

C++ 允许**同名不同参数列表**的多个函数共存：

```cpp
int max3(int a, int b, int c) { ... }
double max3(double a, double b, double c) { ... }
```

调用时编译器根据实参类型自动选对应版本。

## 常见错误

1. **忘了 return**：非 void 函数没 return → 编译警告 + 运行行为未定义
2. **传 vector 不加 `&`**：每次调用都拷贝整个 vector，性能差
3. **递归无出口**：栈溢出（StackOverflow）
4. **声明和定义参数类型不一致**：链接错误（很难看懂的报错）

## 现在做练习

5 道题：写 add、写 max_of_three、阶乘（递归）、判断质数、用引用交换两数。
