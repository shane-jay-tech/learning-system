# 正则表达式（re）

## 正则是什么

正则表达式是 **匹配文本模式** 的小语言。比如：
- 找出所有像邮箱的字符串：`r"[\w.+-]+@[\w.-]+\.\w+"`
- 验证手机号是不是 11 位纯数字：`r"^\d{11}$"`
- 把所有"日期"变成 ISO 格式：用 `re.sub`

```python
import re
```

## 4 个核心函数

```python
re.search(pattern, text)      # 找第一个匹配；返回 Match 对象或 None
re.findall(pattern, text)     # 找所有匹配；返回列表
re.match(pattern, text)       # 从开头匹配（很少用）
re.sub(pattern, repl, text)   # 替换
```

## 常用元字符

| 字符 | 含义 |
|---|---|
| `.` | 任意一个字符（除换行）|
| `\d` | 数字（[0-9]）|
| `\w` | 字母数字下划线 |
| `\s` | 空白（空格/tab/换行）|
| `^` `$` | 开头 / 结尾 |
| `*` `+` `?` | 0+ / 1+ / 0-1 次 |
| `{3}` | 恰好 3 次；`{3,5}` 3-5 次 |
| `[abc]` | a 或 b 或 c |
| `[^abc]` | 不是 a/b/c |
| `\b` | 单词边界 |
| `()` | 分组 |
| `\|` | 或 |

## raw string：永远用 r"..."

```python
re.search(r"\d+", "abc 123")         # 推荐
re.search("\\d+", "abc 123")          # 等价但容易写错
```

正则里的 `\` 太多——用 raw string `r"..."` 让 `\` 不被 Python 转义，直接传给正则引擎。

## 实战：邮箱匹配

```python
text = "Contact: alice@x.com or bob@y.org for info."
emails = re.findall(r"[\w.+-]+@[\w.-]+\.\w+", text)
# ['alice@x.com', 'bob@y.org']
```

## 分组与捕获

```python
text = "Date: 2026-05-29"
m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
m.group(0)   # '2026-05-29'  整体
m.group(1)   # '2026'        第 1 组
m.group(2)   # '05'
```

`(...)` 捕获组——可以分别取出来。

## re.sub 替换

```python
text = "Phone: 138-1234-5678"
new = re.sub(r"\d", "*", text)
# 'Phone: ***-****-****'

# 用分组
text = "2026-05-29"
new = re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\3/\2/\1", text)
# '29/05/2026'
```

`r"\1"` 引用第 1 组捕获。

## 贪婪 vs 非贪婪

```python
text = "<b>bold</b> and <i>italic</i>"
re.findall(r"<.+>", text)      # ['<b>bold</b> and <i>italic</i>'] 贪婪
re.findall(r"<.+?>", text)     # ['<b>', '</b>', '<i>', '</i>'] 非贪婪
```

`+?` 在 + 后加 ? 表示**最少匹配**。处理 HTML/JSON 时常用。

## 编译加速（重复使用时）

```python
pattern = re.compile(r"\d+")
for line in lines:
    pattern.findall(line)    # 比每次 re.findall 快
```

## 常见错误

1. **`. * +` 默认贪婪**：经常匹配过多——加 ? 转非贪婪
2. **不用 raw string**：`"\d"` 在 Python 里是 `\d`（OK），但 `"\b"` 是退格符（错）！
3. **`re.match` 只从开头匹配**：要全局搜用 `re.search`
4. **替换字符串里的反斜杠**：`re.sub(r"...", r"\\1", ...)` 想引用组 1 写 `r"\1"` 即可

## 现在做练习

5 道题：找邮箱、统计数字、提取日期、re.sub 屏蔽手机号、findall 加分组。
