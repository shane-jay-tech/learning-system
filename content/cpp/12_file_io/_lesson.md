# 文件 IO（fstream）

## fstream 三件套

C++ 文件操作用 `<fstream>`：

| 类 | 用途 |
|---|---|
| `ifstream` | 读文件 |
| `ofstream` | 写文件 |
| `fstream` | 读写都行 |

```cpp
#include <fstream>
```

## 写文件

```cpp
ofstream out("data.txt");
out << "Hello\n";
out << 42 << " " << 3.14 << endl;
out.close();   // 析构会自动关，但显式关也行
```

`ofstream out(path)` 打开文件用于写——**会清空原内容**。要追加用 `ofstream(path, ios::app)`。

## 读文件

```cpp
ifstream in("data.txt");
string line;
while (getline(in, line)) {
    cout << line << endl;
}
```

`getline(in, line)` 读一行（不含换行符）；返回 in 本身，转 bool 判断是否成功。

## 按词读

```cpp
ifstream in("nums.txt");
int x;
while (in >> x) {
    cout << x << " ";
}
```

`>>` 自动跳空白，按词读。

## 整文件读到字符串

```cpp
ifstream in("data.txt");
string content((istreambuf_iterator<char>(in)),
                istreambuf_iterator<char>());
// content 含整个文件内容
```

这是 C++ "读全部" 的标准写法（虽然有点长）。简化：

```cpp
ifstream in("data.txt");
stringstream ss;
ss << in.rdbuf();
string content = ss.str();
```

## 检查文件是否打开

```cpp
ifstream in("missing.txt");
if (!in) {
    cerr << "can't open" << endl;
    return 1;
}
```

`!in` 在文件没打开时为 true；`in.is_open()` 也行。

## 二进制 vs 文本

```cpp
ofstream out("data.bin", ios::binary);
int x = 42;
out.write(reinterpret_cast<const char*>(&x), sizeof(x));
```

二进制读写直接拷贝内存——快，但跨平台/版本要小心字节序和结构对齐。

## 错误状态

```cpp
ifstream in("data.txt");
while (in >> x) {
    // 正常读到 x
}
if (in.eof()) cout << "到文件末尾";
else if (in.fail()) cout << "读取格式错";
else if (in.bad()) cout << "I/O 错误";
```

通常只判 `while (in >> x)` 就够。

## 常见错误

1. **打开失败没检查**：直接读会读到无效数据
2. **`/` 和 `\\` 混用路径**：Windows 用 `\\` 但 `/` 也行；推荐 `/`（跨平台）
3. **没 close 大量文件**：句柄耗尽；用 RAII（fstream 析构自动关）
4. **二进制和文本混用**：写时 `ios::binary` 读时不带，或反过来——内容错乱
5. **getline 后 `>>` 残留换行**：读完一行后再 `>>` 会跳过换行；但顺序反过来要 `cin.ignore()`

## 现在做练习

5 道题：写后读、按行计数、按词求和、判断文件存在、追加模式。
