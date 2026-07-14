# 异常处理（try / catch / throw）

## 异常是什么

C++ 异常处理思路和 Python 一样：**try 块里出错就抛异常，被 catch 接住**。

```cpp
#include <stdexcept>

try {
    if (x == 0) {
        throw runtime_error("can't divide by zero");
    }
    int y = 100 / x;
} catch (const runtime_error& e) {
    cout << "Error: " << e.what() << endl;
}
```

`throw 对象` 抛出异常；`catch (const T&)` 按类型捕获；`e.what()` 拿错误消息。

## 常用标准异常

```cpp
#include <stdexcept>

throw invalid_argument("bad arg");      // 参数无效
throw out_of_range("index too big");     // 越界
throw runtime_error("something wrong");   // 运行时错误
throw logic_error("design flaw");          // 逻辑错误
throw bad_alloc();                          // 内存分配失败（new 失败）
```

都继承自 `std::exception`，都有 `what()` 方法。

## 多个 catch

```cpp
try {
    risky();
} catch (const out_of_range& e) {
    cout << "out: " << e.what() << endl;
} catch (const runtime_error& e) {
    cout << "runtime: " << e.what() << endl;
} catch (const exception& e) {       // 兜底
    cout << "other: " << e.what() << endl;
}
```

C++ 按**最先匹配**的 catch 执行——所以**派生类要写在基类之前**，否则永远走不到。

## catch (...) 万能兜底

```cpp
try { ... }
catch (...) {
    cout << "unknown error" << endl;
}
```

`catch (...)` 接住任何类型——但**拿不到错误信息**。一般只在最外层用。

## 自定义异常类

```cpp
class MyException : public std::runtime_error {
public:
    MyException(const string& msg) : runtime_error(msg) {}
};

throw MyException("custom error");
```

继承 `std::exception` 或它的子类——这样 catch (const std::exception&) 也能接住。

## RAII：异常安全的资源管理

C++ 没 try/finally，**资源管理靠 RAII**：

```cpp
{
    ifstream file("data.txt");        // 构造时打开
    // ... 这里抛异常也没关系
}                                     // 离开作用域时 file 自动关
```

`ifstream` 析构函数自动关文件——**即使抛异常**也会执行。所以 C++ 用 RAII（unique_ptr、ifstream、lock_guard 这些）做"自动清理"。

## 不要在析构函数里抛异常

```cpp
~Foo() {
    throw runtime_error("oops");   // 极度危险
}
```

如果析构期间正在处理另一个异常，再抛会 `std::terminate` 直接杀死程序。

## noexcept 关键字

```cpp
int safe_func() noexcept {        // 保证不抛
    return 42;
}
```

`noexcept` 标注让编译器优化、提示用户"这个不会出错"。但**违反承诺**会立即 terminate。

## 常见错误

1. **catch 顺序错**：基类在前 → 派生类的 catch 走不到
2. **按值 catch**：`catch (exception e)` 会切片（slicing）；要 `catch (const exception&)`
3. **抛裸指针**：`throw new int(5)` 谁负责 delete？永远抛对象，不抛指针
4. **滥用异常做控制流**：异常是"意外"——用作正常流程会让代码混乱

## 现在做练习

5 道题：基础 try/catch、throw runtime_error、自定义异常、out_of_range 越界、多 catch。
