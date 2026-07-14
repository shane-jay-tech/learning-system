# 模块化与配置

## 为什么"全堆一个文件"会崩

刚开始你的工具就一个 `main.py`，100 行没问题。
等 agent 加了几次新功能后，main.py 涨到 1500 行——**改一处会牵动其他几处**，改完跑通了别处又坏。

这时候就该**拆模块**了。

## 三层标准结构

任何工具都能套这个模板：

```
my_tool/
├── ui/             ← 界面层（Streamlit / CLI / Flask）
├── core/           ← 业务层（算法、数据处理）
└── data/           ← 数据层（数据库、文件 IO）
```

**核心原则**：UI 不直接操作数据库，业务层不知道用什么 UI。这样：
- 改 UI 不影响业务
- 业务可以重用（写 CLI 也行写 Web 也行）
- 数据层换（SQLite → PostgreSQL）业务不变

## 抽配置出来：.env

❌ 写死在代码里：
```python
API_KEY = "sk-abc123..."
DATABASE_URL = "postgres://..."
DEBUG = True
```

✅ 放 `.env.local`：
```
API_KEY=sk-abc123...
DATABASE_URL=postgres://...
DEBUG=true
```

代码里读：
```python
import os
from dotenv import load_dotenv

load_dotenv(".env.local")
api_key = os.environ["API_KEY"]
debug = os.environ.get("DEBUG", "false").lower() == "true"
```

`.env.local` **加进 .gitignore**——绝不 commit 密钥。

## 抽魔法数字：常量

```python
# ❌ 魔法数字
if user_count > 1000:
    use_cache()

# ✅ 命名常量
CACHE_THRESHOLD = 1000
if user_count > CACHE_THRESHOLD:
    use_cache()
```

读代码的人（包括 3 个月后的你）知道 1000 啥意思了。

## 依赖注入：让代码可测

```python
# ❌ 硬编码依赖
def calc_total(user_id):
    db = sqlite3.connect("prod.db")    # 写死了 prod 数据库
    ...

# ✅ 依赖注入
def calc_total(user_id, db):
    ...

# 测试时
test_db = sqlite3.connect(":memory:")
calc_total(123, test_db)
```

第二种**测试时能用假 db**——这就是好代码的标志。

## 函数职责单一

```python
# ❌ 一个函数干 5 件事
def process(user):
    data = fetch_from_db(user)
    cleaned = clean(data)
    result = analyze(cleaned)
    save_to_db(result)
    send_email(result)
```

5 件事打包一起 → 单元测试不可能。

```python
# ✅ 拆开
def fetch_user_data(user_id, db): ...
def clean_data(data): ...
def analyze(data): ...
def save_result(result, db): ...
def notify(result, mailer): ...
```

每个 50 行以内，每个能单独测。

## requirements.txt：锁定依赖

```
streamlit>=1.32
pandas>=2.0,<3.0
pyyaml>=6.0
scipy>=1.10
```

新人 clone 你的项目跑：
```bash
pip install -r requirements.txt
```

不写这个文件 → 别人跑你的代码十之八九装不全包。

## __init__.py：模块入口

```
my_tool/
├── core/
│   ├── __init__.py        ← 让 core 是可导入的包
│   ├── analyzer.py
│   └── cleaner.py
```

`__init__.py` 可以为空，但得有——告诉 Python "这个目录是个包"。

## 让 Agent 帮你重构

```
"这个 main.py 1200 行了，我看着头大。请：
1. 按业务功能拆成 3-5 个文件
2. 每个文件都加单元测试
3. 把所有硬编码的路径/key 抽到 config.py
4. 给我看一下新的目录结构"
```

Agent 重构能力很强，但**你要明确说明拆成几层、抽什么**。

## 常见错误

1. **import 循环**：a 引 b、b 引 a → 拆模块时常见。把共用部分抽到第三个文件
2. **超大 __init__.py**：里面塞业务逻辑——`__init__` 应该只做"暴露 API"
3. **配置散落多处**：一会儿环境变量、一会儿 yaml、一会儿硬编码——选一个
4. **测试 import 不到**：项目根没在 sys.path——加 `conftest.py` 或 `pyproject.toml`

## 现在做练习

5 道题：抽配置到 env、命名常量代替魔法数字、拆函数、依赖注入改造、判断模块结构对错。
