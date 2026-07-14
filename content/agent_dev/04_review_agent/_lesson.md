# 审 Agent 代码

## 别相信 agent 自己说的

Agent 经常说：
- "已经测试通过了" — 它没真跑
- "完全按你的 spec 实现" — 偷偷加了你没说的功能
- "已经修复 bug" — 改了一处但留了别处

**你必须自己验证**，不能只看 agent 自我汇报。

## 5 大常见陷阱

### 1. 假装写了测试

```python
def test_add():
    result = add(2, 3)
    # TODO: assert result == 5
```

测试**没断言** = 永远 PASS = 没测。审代码时搜 `def test_`，看每个测试有没有 `assert`。

### 2. 命名重复 / 覆盖

```python
def login(user):
    user = user.strip()       # 覆盖了参数 user
    ...

list = ["a", "b"]              # 覆盖了内置 list
```

agent 不长记性会用内置名（list / dict / type / id）当变量。**每个变量名搜一下是不是 builtin**。

### 3. 异常被吞掉

```python
try:
    risky_op()
except Exception:
    pass               # 错误被悄悄吃了——bug 隐藏在这
```

`except Exception: pass` 是审计的红灯。让 agent 改成具体异常 + 至少 log 一下。

### 4. 过度工程化

```python
class AbstractFactoryHandlerStrategy:
    ...
class ConcreteImplementationFactory(AbstractFactoryHandlerStrategy):
    ...
```

5 行能解决的事写 5 个类——agent 喜欢炫技，让它**简化到能跑就行**。

### 5. 版本兼容暗坑

```python
data = json.loads(text, strict=False)        # 旧 Python OK
match value:                                  # Python 3.10+ 才有
    case 1: ...
```

Agent 写完了，你的 Python 3.9 跑不了。**问 agent 兼容到什么版本**。

## 审代码的 SOP

每次 agent 改完，跑这 5 步：

### 步骤 1：`git diff` 看实际改了啥
不只是看 agent 总结。它经常顺手改了你不想动的地方。

### 步骤 2：搜测试断言
```bash
grep -r "def test_" tests/
```
逐个看，确保每个 test 函数有 assert。

### 步骤 3：跑边界用例
- 空输入 / 0 / 负数 / None
- 超大输入 / 含特殊字符
- 网络断（如果用网）/ 文件不存在

### 步骤 4：搜可疑模式
```bash
grep -r "except.*pass" .          # 吞异常
grep -r "TODO\|FIXME" .            # 没做完的标记
grep -r "print(" .                  # 调试代码忘删
```

### 步骤 5：让另一个 agent 审
让 ChatGPT/Claude 审一遍，"找出 5 个潜在问题"——多个 agent 互审能抓住单 agent 漏的。

## 给 agent 的"加固"指令

写 spec 时**加一句**就能减少 50% 陷阱：

> 实现完成后请自检：
> - 每个 test 函数有 assert 吗？
> - 异常处理是否捕获具体类型而非 Exception？
> - 是否引入了用户没要求的依赖？
> - 边界情况（空输入/None）会崩吗？
> 把这 4 项的检查结果列出来再交付。

## 现在做练习

5 道题：找假测试、找命名覆盖、找吞异常、识别过度工程、检查兼容。
