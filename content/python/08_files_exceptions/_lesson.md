# 文件读写与异常

## 异常处理：try / except

到现在你写的代码"出错就崩"。但真实场景里你不希望一个小错误把整个程序终止——比如用户输入了奇怪的东西，应该提示"请重新输入"，而不是程序整个挂掉。

```python
try:
    n = int(input("数字："))
    print(100 / n)
except ValueError:
    print("输入的不是数字！")
except ZeroDivisionError:
    print("不能除以 0！")
```

机制：

1. `try:` 块里放"可能出错"的代码
2. `except <异常类型>:` 捕获指定异常，给出处理
3. 没出错就跳过 except；出错且匹配上某个 except 就跑那段

## 常见异常类型

| 异常 | 什么时候发生 |
|---|---|
| `ValueError` | 类型对，但值不行——`int("abc")` |
| `TypeError` | 类型不对——`"abc" + 5` |
| `ZeroDivisionError` | 除以 0 |
| `KeyError` | dict 取不存在的 key |
| `IndexError` | 列表下标越界 |
| `FileNotFoundError` | 打开不存在的文件 |
| `Exception` | 万能兜底（**不推荐随便用**——会盖住真错误） |

## 多个 except + finally

```python
try:
    risky()
except ValueError:
    print("值错了")
except (TypeError, KeyError):     # 一次捕多种
    print("类型或 key 错")
except Exception as e:             # 兜底；e 是异常对象
    print(f"未预料的错: {e}")
finally:
    print("无论如何都跑")            # 收尾用，比如关文件
```

## 文件读写：with open

```python
# 写入
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("Hello\n")
    f.write("World\n")

# 读取（一次读全部）
with open("notes.txt", "r", encoding="utf-8") as f:
    content = f.read()

# 读取（按行）
with open("notes.txt", "r", encoding="utf-8") as f:
    for line in f:
        print(line.rstrip())   # 去掉行尾换行
```

模式（mode）：

| 模式 | 含义 |
|---|---|
| `"r"` | 读（默认）；文件不存在抛 FileNotFoundError |
| `"w"` | 写；**会清空原内容** |
| `"a"` | 追加；不清空，往末尾加 |
| `"r+"` / `"w+"` | 读写 |

`encoding="utf-8"` 在 Windows 上**强烈建议显式写**——不写默认 GBK，遇到中文会乱码。

## 为什么用 with

```python
# 不推荐：忘 close 会"占着"文件句柄
f = open("a.txt")
data = f.read()
f.close()

# 推荐：with 自动关
with open("a.txt") as f:
    data = f.read()
```

`with` 块结束时自动关文件，即使中途抛异常也保证关。

## 主动抛异常：raise

```python
def set_age(age):
    if age < 0:
        raise ValueError(f"年龄不能为负数，收到 {age}")
    ...
```

`raise` 在自己的代码里主动抛——告诉调用方"输入不合理"。比悄悄返回 `None` 安全多了。

## 常见错误

1. **except Exception 包太宽**：会把所有错都吞掉，包括你的代码 bug；**优先精确捕获**
2. **没写 encoding**：Windows 中文文件 100% 乱码
3. **忘了 with 自动关**：自己 open 又忘 close → 文件句柄泄露
4. **用 r 模式写 / 用 w 模式读**：模式选错——w 会清空原文件，慎重
5. **try 里包太多**：try 块越大，越难定位错误。只把会出错的那一行包进去

## 现在做练习

5 道题：捕获 ValueError、捕获 ZeroDivisionError、写后读文件、行数统计、文件求和。
