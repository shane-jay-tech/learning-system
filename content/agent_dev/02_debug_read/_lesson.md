# 调试与读代码

## 报错信息要怎么看

Agent 改完跑一下报错——**stack trace** 看起来像天书但其实有规律。从下往上读，最后一行是错误**类型**，倒数第二行是**触发的位置**。

```
Traceback (most recent call last):
  File "main.py", line 5, in <module>
    result = divide(10, 0)
  File "main.py", line 2, in divide
    return a / b
ZeroDivisionError: division by zero
```

读法：
1. **最后一行 `ZeroDivisionError`**：错误**类型**——除零
2. **倒数第二行 `return a / b`**：实际**出错的代码行**
3. **倒数第三行 `File "main.py", line 2, in divide`**：在 main.py 第 2 行的 divide 函数里
4. 上面的层是**调用链**：main.py:5 调用了 divide，divide 里第 2 行出错

## 你给 Agent 的报告应该是这样的

❌ "它不工作"
❌ "代码崩了"

✅ "main.py 第 2 行 `return a / b`，b=0 时抛 ZeroDivisionError，调用栈是 main.py:5 → divide()"

**报错信息 + 行号 + 函数名 + 触发条件**——agent 拿着这个能秒修。

## 5 个最常见的 Python 错误

| 错误 | 说明 | 怎么修 |
|---|---|---|
| `NameError` | 变量没定义 | 检查拼写、检查是否在作用域内 |
| `IndentationError` | 缩进不对 | 检查空格 vs Tab、对齐 |
| `IndexError` | 列表越界 | 检查 `len()` 和下标 |
| `KeyError` | 字典 key 不存在 | 用 `dict.get(k, default)` |
| `TypeError` | 类型不对（如 `"a" + 1`）| 看清两边类型 |

## print 调试：穷人的 debugger

```python
def calc(items):
    print(f"DEBUG items = {items}")     # 看输入
    total = 0
    for i, x in enumerate(items):
        print(f"  i={i}, x={x}")          # 看每次循环
        total += x
    print(f"DEBUG total = {total}")     # 看输出
    return total
```

**80% 的 bug 用 print 就能定位**。等 print 还不够再用真 debugger。

## 用 IDE 的 debugger（VS Code）

1. 在某行左边点一下打**断点**（红圈）
2. F5 启动调试
3. 程序跑到断点处停下
4. 你能看**所有变量**当前值
5. F10 单步走、F11 进入函数

学一次，省你余生 100 个 print。

## 二分定位：bug 在哪一段

代码 100 行不知道哪坏了？

1. 在中间加 `print("=== mid ===")`
2. 跑一下：
   - 看到 `=== mid ===` → bug 在后半段
   - 没看到 → bug 在前半段
3. 在那一半的中间再加 print，重复

**5-7 次缩进定位**到具体行——比从头读 100 行高效多了。

## Agent 改完后的"自检清单"

让 agent 改完代码，跑前 5 个动作：

1. `git diff` — 看 agent 实际改了啥
2. 跑 happy path 一次（看正常情况能跑吗）
3. 跑 1 个边界情况（输入空、输入很大）
4. 看终端**有没有 warning**（agent 经常忽略 warning）
5. 看输出**和预期一致吗**（不只是没崩就行）

## 常见错误

1. **看到 traceback 就慌**：从下往上读，找到第一个**你自己代码**的位置
2. **agent 说"修好了"就信**：自己跑一次再说
3. **改一处看一处**：每改一处都跑一下，别堆 5 个改动一起测
4. **吞掉 exception**：`try: ... except: pass` —— 让 bug 隐藏，比报错更糟

## 现在做练习

5 道题：找出错的行号、读 stack trace、改 NameError、改 IndexError、找 print 调试位置。
