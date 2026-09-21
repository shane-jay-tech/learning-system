# README 目录树 vs 磁盘清单核对（l922-131，2026-09-22）

- 任务：`l922-131-readme-tree-check`（cwd `D:/code/learning-system`，执行班 `qoder-executor-20260922-0000-learn11`，软预算 ≤15 分钟）
- 基线：HEAD `1831cc7`；取数时刻 2026-09-22T04:50+08:00；核对时工作树含同班上一单 `l922-130` 的 4 项在途件（与本单目标无交集）。
- 性质：**对账登记为主**。全仓 README 树段 9 条逐条给三态；订正建议按「本单已改 ≤1 行」与「超一行只登记」分档。
- **所有数字绑 commit，不绑日期**；引本档读数请先在 `1831cc7` 的树段上复跑 §四 的命令。
- 不重复立案：README 的**数字口径**（399/85/6/22）由 `learn-readme-numbers-20260922.md`（l922-108）管，**验证块 8 条命令**由 `learn-readme-commands-audit-20260922.md`（l922-109）管；本单只管 **`## 目录` 代码块的条目 ↔ 磁盘清单**。

## 一、锚点复核

| 任务书锚点 | 磁盘实况 | 判定 |
|---|---|---|
| `README.md:82-92`「目录树段」 | :82 开栏 ```text、:83-91 共 **9** 条目、:92 闭栏 ``` | 行段未漂移；但条目数是 9（锚点未给数，按实取） |
| `scripts/`「实测 17 个 .py（`ls scripts/*.py \| wc -l`）」 | 该命令实测 **16**；17 是 `find scripts -maxdepth 1 -type f` 的**全部文件数**（16 个 .py ＋ `create_shortcut.ps1`） | **锚点预期数过期**（把两个口径混了）；同一偏差已由 l922-109 档 §一 登记，本单复算一致 ⇒ 只引不另立 |

## 二、逐条三态（树 → 盘）

三态定义：**在盘**＝树中条目在仓库根存在；**缺盘**＝树中写了但盘上没有（幽灵条目）；**盘有树无**＝顶层磁盘条目未被树收录。

| # | 树条目（README:83-91） | 三态 | 盘上实况 |
|---:|---|---|---|
| 1 | `app.py` | 在盘 | file，tracked，「Streamlit 入口」相符 |
| 2 | `core/` | 在盘 | dir，tracked（22 个文件） |
| 3 | `core/runners/` | 在盘 | `__init__.py` + `base.py` + `python_runner.py`/`sql_runner.py`/`cpp_runner.py`/`r_runner.py` ⇒ 描述「Python / SQL / C++ / R」相符（另有 base/__init__ 属实现件，不算缺漏） |
| 4 | `ui/` | 在盘 | `pages/`、`components.py`、`styles.py` ⇒ 「页面与组件」相符 |
| 5 | `content/` | 在盘 | **行内枚举不全**：树只写 `python / cpp / r / sql / agent_dev`，盘上另有 `paths/`（6 个 yaml，:52 正文提过）与 `datasets/`（`generate_hr_data.py` ＋ 2 csv，**全文零提及**） |
| 6 | `scripts/` | 在盘 | 16 个 .py ＋ 1 个 `create_shortcut.ps1`（:37 用到）；树行只描述 Python 侧用途 |
| 7 | `tests/` | 在盘 | 86 个 .py，「测试套件」相符 |
| 8 | `docs/` | 在盘 | **描述失真**：树写「系统报告」，盘上 `docs/*.md` 仅 3 份（system-report v0.6.3/.4/.5），而 `docs/insights/` 有 **61 份**（本档落盘后 62）⇒ 主成分未反映 |
| 9 | `data/` | 在盘 | `.gitkeep`（tracked）＋ `progress.db`、`backups/`（被 `.gitignore` 覆盖）⇒「本地学习数据（不进入 Git）」**成立**，仅占位 `.gitkeep` 例外 |

**缺盘＝0**：树里没有对不上盘的条目。问题全部集中在「盘有树无」与「行内描述」两侧。

## 三、盘有树无（顶层 19 条，排除 `.git`）

| 类别 | 条目 | 数量 |
|---|---|---:|
| 已 tracked、树未列 | `.coveragerc` `.gitignore` `.streamlit/`（`config.toml`）`README.md` `assets/`（`app.ico`/`app.png`）`launcher.pyw` `plan.md` `pytest.ini` `requirements-freeze.txt` `requirements.txt` `start.bat` | 11 |
| 被 `.gitignore` 覆盖 | `.coverage` `.coverage-after.json` `.coverage-baseline.json` `.pytest_cache/` `.venv/` `__pycache__/` `tmp/` | 7 |
| 未跟踪 | `logs/` | 1 |

`logs/` 单独点名（原判读经复核**收窄**，按磁盘实况改写）：该目录**存在且为空**（`len(list(Path('logs').iterdir())) == 0`），
且全仓（排除 `.venv`/`__pycache__`/`.git`）**没有任何文件引用顶层 `logs/`**——
`grep -rn "logs" --include=*.py --include=*.md --include=*.bat --include=*.ps1 --include=*.ini --include=*.toml .`
命中的只有 `agent_dev/10_debug_logs`（题库目录名）与两处测试函数名，**无一处是路径写方**；
真正的日志写在 `launcher.pyw:39 LOG_FILE = HERE / "data" / "launcher.log"` 与 `:121` 的 `data/streamlit.log`（`data/` 被忽略）。
⇒ 顶层 `logs/` 是**无主空目录**：git 看不见它（空目录不入库），`.gitignore` 也只有 `*.log`、**没有 `logs/` 规则**。
README:14「日志…被 Git 忽略」这句因此**名实两不沾**——它说的其实是 `data/` 下的 `.log` 与任意位置的 `*.log` 后缀，
与树里没登记、盘上却是空的 `logs/` 无关。属**文档与规则双缺口 ＋ 一个来历不明的空目录**，非本单范围，建议单列。

## 四、计数自洽（先命令，后读数）

取数脚本（仓库根执行；口径＝从 `## 目录` 小节起找第一对围栏，围栏内每行首 token 即条目）：

```python
import subprocess
from pathlib import Path
raw = Path("README.md").read_text(encoding="utf-8").splitlines()
start = next(i for i, l in enumerate(raw) if l.startswith("## 目录"))
fo = next(i for i in range(start, len(raw)) if raw[i].startswith("```"))
fc = next(i for i in range(fo + 1, len(raw)) if raw[i].startswith("```"))
entries = [l.split()[0] for l in raw[fo + 1:fc]]                 # 树条目
disk = {p.name for p in Path(".").iterdir() if p.name != ".git"}  # 顶层盘条目
print(len(entries), sum(p.exists() for p in map(Path, entries)))
print(len({n for n in disk if n not in {Path(e).name for e in entries}}))
```

读数（`1831cc7`）：

```
树条目 = 9        在盘 = 9        缺盘 = 0        盘有树无 = 19        顶层盘条目（排除 .git）= 27
```

自洽等式三条（**不锁魔数，任一侧变动就应重新复算**）：

- `在盘 + 缺盘 == 树条目数` ⇒ 9 ＋ 0 == 9 ✓
- `盘有树无 == 顶层盘条目 − 树中顶层名数` ⇒ 27 − 8 == 19 ✓（`core/runners/` 是嵌套条目，不计入顶层名集）
- `树条目 == 顶层条目 + 嵌套条目` ⇒ 8 ＋ 1（`core/runners/`）== 9 ✓

顺带用「带语言前缀的键」独立复算 `:52` 的 85 知识点，并示范一个**必须避开的坑**：

```
主题目录按 f"{lang}/{slug}" 建键 = 85 ；按裸 slug 去重 = 84（cpp/01 与 python/01 撞名）
⇒ 任何按 slug 单键对账的主题统计会静默少 1，README:52 的 85 只能由前缀式键复现
```

## 五、订正建议清单

**A. 本单已改（≤1 行，原地替换不改行数）**

- `README.md:90`：`docs/                 系统报告` → `docs/                 系统报告与巡检留痕 insights/`。
  理由：insights 已是 docs/ 的绝对主成分（61 vs 3），原描述会让新人找不到 `docs/insights/` 这条在册留痕链。
  边界：只动这一行，**不增删行** ⇒ `test_version_consistency`（钉版本串在 README:3/:59）与 `test_heatmap_window`（钉 :62 的「13 周」句）行号不受影响；改后跑该两族＋全量复核。

**B. 只登记、不实施（超过「一行内的明显错」，属文档改版需人工定口径）**

1. 树补 tracked 顶层件 11 项（§三 第一行），至少含 `launcher.pyw`／`start.bat`／`assets/`／`.streamlit/`／`requirements.txt`／`pytest.ini`——
   **方式 A（桌面 app，README:33-40 用整段篇幅讲它）的整条入口链在树里零落点**：
   `scripts/create_shortcut.ps1`（:5 取 `launcher.pyw`、:7 取 `.venv\Scripts\pythonw.exe`）生成桌面快捷方式 →
   `launcher.pyw` 自己 spawn `streamlit run app.py`（:108-122）并开 webview 窗口。
   另注：`start.bat` 是**另一条独立入口**（建 venv → `scripts/find_port.py` 找空端口 → streamlit），
   **不被 `launcher.pyw` 引用**（grep 无命中）——README 方式 A 那段只写了 `health_check.py` ＋ `create_shortcut.ps1` 两条命令，
   既没提 `start.bat` 也没提 `find_port.py`，属同一处「入口链未登记」。
2. 树补 `content/` 行的 `paths/`、`datasets/`（`datasets/` 全文零提及）。
3. `scripts/` 行补一句「含 1 个 PowerShell 脚本」，或在 :12 的技术架构行里说明；顺带把「scripts 数量」这类会变动的数字**只留在 insights、不写进 README**（l922-108/l922-109 两单已因此各踩一次过期预期数）。
4. `logs/` 的三缺口（§三 末段：无主空目录／`.gitignore` 无 `logs/` 规则／README:14 措辞名实不副）一并处置——
   出口要么删目录并改 README:14，要么给 `logs/` 补规则与登记；删件需人工批准，本单未动。
5. `data/` 行的「不进入 Git」可加半句「（`.gitkeep` 除外）」，属可选润色。
