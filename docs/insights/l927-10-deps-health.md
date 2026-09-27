# l927-10 learning 依赖与运行环境健康检查（requirements／node 双面，只读零安装）

> 班次：`qoder-executor-20260927-1520-learn46`（波次 21 只读采集子班）｜时戳 `2026-09-27T17:3x+08:00`（`date` 现取）
> 仓现值：HEAD `8ef64c6`、`git status --porcelain` 开单前 **0 行**
> **零安装、零联网、零写库**：全程只读 `pip freeze`／AST／grep。未跑 `pip install`／`pip check`／`pip list --outdated`（后者会联网，卷宗禁）。
> 🔴 本档**否证掉一条在册结论**（W4：`learn-deps-suspects-20260918.md` 对 pywebview 的「偏删」建议），见第四节。

---

## 一、依赖面清单（先命令后数字）

### 1.1 声明层（磁盘现点）

| 文件 | 存在？ | 规模 | 复跑命令 |
|---|---|---|---|
| `requirements.txt` | ✅ | **11** 条顶层声明（8 运行＋2 dev＋1 空注释行剔除后） | `grep -cE '^[A-Za-z]' requirements.txt` → **11** |
| `requirements-freeze.txt` | ✅ | **195** 行，全部 `name==version`（非 `==` 形态行 **0**，含 editable／`-e`／`file:` 的行 **0**） | `wc -l < requirements-freeze.txt` → 195；`grep -vE "^[A-Za-z0-9._-]+==" requirements-freeze.txt` → 空 |
| `pyproject.toml` / `setup.py` / `setup.cfg` / `Pipfile` / `poetry.lock` | ❌ 全不存在 | — | `ls pyproject.toml setup.py Pipfile* poetry.lock` → No such file |
| `package.json` / `package-lock.json` | ❌ 不存在 | — | 见 1.3 node 面 |

### 1.2 实装层：**这台机上有两套解释器在跑本仓**（关键结构事实）

| 环境 | 谁用它 | 包数 | 复跑 |
|---|---|---|---|
| **`.venv\Scripts\python.exe`（＝运行面）** | `start.bat:19/27`（`PYTHON=.venv\Scripts\python.exe`）；`create_shortcut.ps1:7/16`→`launcher.pyw`→`launcher.pyw:110 sys.executable` 起 streamlit→`python_runner.py:119 [sys.executable,"-I",src]` 跑学生代码 | **62** | `.venv/Scripts/python.exe -m pip freeze \| wc -l` |
| **`D:\Program\python.exe`（＝测试面）** | `plan.md:33` 与 `docs/insights/l927-03-baseline.md` 记的全量口径是裸 `python -m pytest tests -q` ⇒ 落系统 python（1162 passed／0 failed／7 skipped @ HEAD `2665f0a`） | **205** | `python -m pip freeze \| wc -l` |

`pyvenv.cfg`：`include-system-site-packages = false` ⇒ **两环境完全隔离**，`.venv` 看不见系统里装好的 pywebview。

### 1.3 node 面：**如实零发现**

| 判据 | 结果 |
|---|---|
| `git ls-files \| grep -icE "\.(js\|ts\|tsx\|jsx)$"` | **0** |
| `package.json` / `package-lock.json` / 任何 npm workspace | **不存在** |
| 前端资产来源 | 随 wheel 分发：`streamlit/static/`（`.venv`＝1.59.1、系统＝1.58.0）、`streamlit_ace/frontend/build/*.js`（本地资产，`grep -rn "cdn\|jsdelivr\|unpkg" .venv/Lib/site-packages/streamlit_ace/*.py` → **0 命中**） |
⇒ 本仓**没有 node/npm 构建面**，"node 双面"在本域等价于「无」。离线可用（前端资产不走 CDN）这条**是好消息，如实记**。

---

## 二、钉死度评估

### 2.1 声明层（`requirements.txt`）

| 项 | 数字 | 复跑 |
|---|---|---|
| 有**上下界**（`>=x,<y`）的条数 | **9 / 11** | `grep -cE "^[A-Za-z].*,<" requirements.txt` → 9 |
| **只给下界、无上界** | **2 条**：`requirements.txt:12 pytest>=8.0`、`:13 pytest-cov>=5.0` | `grep -nE "^[A-Za-z].*>=[^,]*$" requirements.txt` |
| hash 锁定（`--require-hashes`／`sha256=`） | **0** | `grep -cE -- "--hash\|sha256=" requirements.txt requirements-freeze.txt` → 0/0 |
| 独立 dev 清单 | **无**（`requirements-dev.txt` 不存在，dev 两条混在生产声明里，靠一行 `# dev only` 注释区分） | `ls requirements*` |

**判定**：运行依赖钉得**及格**（区间约束＋两环境实测 11/11 都在区间内、零越界，见 2.2）；**测试依赖钉不住**（`pytest>=8.0` 无上界，环境实装 **9.1.1**；`pytest-cov>=5.0` 实装 **7.1.0**）——按这个声明，将来 pytest 10.x 发布后会被直接吃进回归基线，而基线（1162 passed）是逐测试语义钉的。

### 2.2 逐条 × 三面（复跑＝本档点名探针；`缺`＝该层查无此包）

| 包 | 声明区间 | freeze | `.venv`（运行面） | 系统（测试面） | 判定 |
|---|---|---|---|---|---|
| streamlit | `>=1.32,<2` | 1.58.0 | **1.59.1** | 1.58.0 | 区间都满足，但 freeze↔venv **漂移** |
| streamlit-ace | `>=0.1.1,<1` | **缺** | 0.1.1 | **缺** | 🔴 freeze 缺行＋测试面未装（→ W2） |
| pywebview | `>=4.4,<7` | 6.2.1 | **缺** | 6.2.1 | 🔴 运行面未装（→ W1） |
| pyyaml | `>=6.0,<7` | 6.0.2 | 6.0.3 | 6.0.2 | 满足，venv 漂移 |
| pandas | `>=2.0,<4` | 3.0.3 | 3.0.3 | 3.0.3 | ✅ 三面一致 |
| numpy | `>=1.24,<3` | 2.3.5 | **2.5.1** | 2.3.5 | 满足，运行面↔freeze↔测试面三方不一（→ W3） |
| scipy | `>=1.10,<2` | 1.18.0 | 1.18.0 | 1.18.0 | ✅ |
| scikit-learn | `>=1.3,<2` | 1.9.1 | **1.9.0** | 1.9.1 | 满足，运行面↔测试面差一版（→ W3） |
| matplotlib | `>=3.7,<4` | 3.11.0 | 3.11.0 | 3.11.0 | ✅ |
| pytest | `>=8.0`（无上界） | 9.1.1 | 9.1.1 | 9.1.1 | 满足，但无护栏 |
| pytest-cov | `>=5.0`（无上界） | 7.1.0 | 7.1.0 | 7.1.0 | 满足，但无护栏 |

**越界命中：0 条**（11/11 在两环境都落在声明区间内）——所以「声明↔实装」没有硬冲突，问题全在**冻结层与运行面对不上**。

### 2.3 🔴 `requirements-freeze.txt` 钉的**不是本仓运行面**（本档最重要的结构结论）

```
freeze ∩ 系统 python 版本全等 : 195 / 195  = 100%
freeze ∩ .venv     版本全等   :  50 / 195  =  26%
.venv 有而 freeze 无          : ['streamlit-ace']
```
⇒ freeze 是**共享全局 python 的快照**（含 `paddleocr`／`playwright`／`aistudio-sdk`／`opencv`／`modelscope`／`tiktoken`／`pingouin`／`librosa` 等 134 个别的项目的包，它们不在 `.venv` 里），
`python_runner.py:119` 与 `start.bat` 走的 `.venv` 才是本仓运行面。
⇒ **两个后果**：① 拿 freeze 复原＝装进 134 个与本仓无关的重型包，且**复原不出 `streamlit-ace`**（编辑器组件反而不在 freeze 里）；
② 9/17 那份核验（`learn-requirements-reconcile-20260917.md`）说的「freeze 非本机现况快照，需刷新」——**方向对、结论需收窄**：现在 freeze 对系统 python 是**逐版本 100% 全等**的，它不是"过期快照"，而是**钉错了对象**。刷新它（`pip freeze > requirements-freeze.txt`）若仍在系统 python 里跑，等于把邻居仓的包继续钉进本仓基线；**必须先在 `.venv` 里跑**才修得对。⚠ 重钉基线＝人工闸，本单只给方向不给动作。

---

## 三、预警清单（按爆炸半径排）

### W1 🔴 运行面 `.venv` 缺 `pywebview` ⇒ README 推荐的桌面入口在这台机上起不来
- 链条：`create_shortcut.ps1:1` 注释写「优先用项目自带的 `.venv`（**依赖都在里面**）」→ `:16` 选 `.venv\Scripts\pythonw.exe` → `launcher.pyw:31 import webview` **失败** → `:33 webview = None` → `:261-265` 弹「缺少依赖／未安装 pywebview，桌面模式无法启动」。
- 否证对象：上面那句 ps1 注释的前提，与 `pyvenv.cfg: include-system-site-packages=false` 一起构成死路（系统里 6.2.1 装了也看不见）。
- 非致命旁证为何没救它：`scripts/health_check.py:81` 把 pywebview 判成非致命（`"desktop mode only; web mode unaffected"`）——web 模式确实不受影响，但 README:33 把**方式 A 桌面 app 标成「推荐日常使用」**，所以这条恰恰打在推荐路径上。
- 形状：`pip install pywebview` 在 `.venv` 里跑一次即可闭合（一行命令，属安装动作 ⇒ **人工闸**，本班未执行）。

### W2 🔴 测试面系统 python 缺 `streamlit-ace` ⇒ 编辑器静默降级，且 1162 绿覆盖不到它
- `ui/components.py:11-22 _ensure_ace()`：`try: from streamlit_ace import st_ace` / **`except Exception:` 全吞** → `_HAS_ACE=False` → `:123` 回落 `st.text_area(...)`。
- 降级丢的是**这个产品对写代码的人的核心 affordance**：语法高亮、行号 gutter、vscode 键位、`font_size=15`、`tab_size=4`（`:108-122`），且**没有任何用户可见提示**说"你现在用的是降级编辑器"。
- 覆盖取证：`grep -rn "st_ace\|streamlit_ace" tests --include=*.py` → 唯一命中 `tests/test_ui_behavior.py:121-124`，而它是 `monkeypatch.setattr(components, "st_ace", lambda **kw: ...)` **直接桩掉** ⇒ 真 import 路径在两环境任一缺包时都不会被抓红。**属「绿但零覆盖」在册形态。**
- ⚠ 这条与「谁用哪套解释器」绑定：`start.bat`／桌面快捷方式走 `.venv`（有 ace，正常）；而**开发口径 `python -m pytest`／`streamlit run app.py`（README:45 方式 B）走系统 python（无 ace）** ⇒ 方式 B 下开发者看到的编辑器和学生看到的不是同一个。

### W3 🟡 两环境 11 项版本漂移 ＋ 学生代码跟随启动解释器 ⇒ 同一题可能两种结果
```
两环境共同包数 61 ／ 版本漂移 11：
  numpy 2.5.1(venv) ↔ 2.3.5(sys)     scikit-learn 1.9.0 ↔ 1.9.1
  streamlit 1.59.1 ↔ 1.58.0          pyyaml 6.0.3 ↔ 6.0.2     pillow / pyarrow / charset-normalizer / …
```
- 传导路径：`core/runners/python_runner.py:119` `[sys.executable, "-I", src]`，`:56` 还把 `os.path.dirname(sys.executable)` 塞进 `PATH` ⇒ **学生代码的解释器与工具链查找路径由"谁启动了 app"决定**，不由依赖清单决定。
- 受影响题面（`grep -rl "import numpy|from numpy" content` 等）：numpy **17** 个 yaml、pandas **32**、sklearn **13**、matplotlib **10**、scipy **7**。其中 `content/python/20_numpy_basics/01_create_array.yaml:16 expected_output: "  30.0"` 这类**逐字钉死输出**的题，跨 numpy 小版本／跨平台 BLAS 有排版与末位差异的空间。
- ⚠ **本单不实算数值差异**（属统计／结论域，且要跑学生代码＝执行面）；只把"漂移在世＋传导路径在世"登记为预警，量级判断交主班或另单。

### W4 🟡 `numpy`／`scipy`／`scikit-learn`／`matplotlib` 在应用代码里**零 import**，但绝不能按"未用依赖"删
- 取证：AST 扫 `app.py`／`launcher.pyw`／`core/**`／`ui/**`／`scripts/*.py`／`tests/*.py` 的 import 面 ⇒ 非 stdlib 非本仓的第三方模块只有 4 个真消费者：`streamlit`(15 文件)、`yaml`(17)、`pytest`(76)、`webview`(2)、`streamlit_ace`(1)、`pandas`(1)；**`import numpy`/`scipy`/`sklearn`/`matplotlib` 命中 0**（`grep -rln "numpy" …` 的 4 个命中全是 `20_numpy_basics` 这类**目录名字符串**，不是 import）。
- 但它们被**学生题面**真用（W3 的 17/7/13/10 个 yaml）⇒ 声明合理、**可发现性为零**。任何"grep import 找未用依赖"的清理都会误删这 4 条 ⇒ 建议在本仓 README 的依赖小节补一句"科学计算栈是给学生题面用的，应用代码不 import 它"（属文档位一行改动，留人工）。

### W5 🟡 依赖面**零守卫**：没有任何测试核对它
```
$ grep -rln "requirements" tests --include=*.py
（空，0 命中）
```
⇒ 声明↔freeze↔实装三者的对账、launcher 解释器↔venv 依赖齐全性，全靠人肉。W1／W2 这类"环境缺一个包"的缺陷在本仓**没有任何自动化能发现**，而全量测试照样 1162 绿。

### W6 🟢 README 安装口径会把包装到运行面之外
`README.md:22-27`：`pip install -r requirements.txt` **未提先建／激活 `.venv`**；而 `README.md:40` 的桌面链与 `start.bat` 都读 `.venv` ⇒ 照 README 装的人（尤其"Python 3.10+ 装好就能跑"的零基础用户，正是本仓的目标人群）会把 11 个包装进系统 python，桌面入口仍因 `.venv` 缺 pywebview 起不来。`start.bat` 会建 venv 但**不装依赖**（`:7-18` 只有 `python -m venv .venv`，全文件 `grep -n "pip" start.bat` → **0 命中**）⇒ **两条入口都不保证 `.venv` 依赖齐全**，这就是 W1 的成因。

### W7 🟢 在册建议的**复核结论**（pywebview 相关，详见第四节）
`learn-deps-suspects-20260918.md` 给的「streamlit-ace：留」✅ 复算成立（真消费＋freeze 有锁，只是那份 freeze 是系统快照）；
给的「pywebview：偏删」❌ **被否证**，见下。

---

## 四、否证掉的在册锚点（⚠ 本档最重要的一条订正）

**被否证件**：`docs/insights/learn-deps-suspects-20260918.md`（任务 l918-08，2026-09-19 晨间执行班）第一节：
> 「全仓 grep `webview.create_window`/`webview.start` **零命中**——不存在真正用 pywebview 开窗的 launcher」／「**零业务消费**」／「**建议：偏删待拍板**」

**磁盘实况**（HEAD `8ef64c6`）：
```
launcher.pyw:31   import webview
launcher.pyw:295  window = webview.create_window(
launcher.pyw:307      storage_path=str(HERE / "data" / "webview_profile"),
launcher.pyw:382  webview.start(
launcher.pyw:387  logger.exception("webview.start failed")
```
⇒ **pywebview 是桌面模式的硬依赖，有真实开窗调用，不能删。**

**误判成因（可复算的口径缺陷，不是手抖）**：那份档的证据命令是
`grep -rn "webview" --include="*.py" --include="*.toml" --include="*.bat" .`
——`--include=*.py` **匹配不到扩展名为 `.pyw` 的 `launcher.pyw`**（该文件首次入库 `b14a136` 2026-07-14，最后修改 `57dfb21` 2026-09-04，都早于那份档的 9-19 ⇒ 不是"后来才加的"）。
复跑对照：
```
不含 pyw：grep -rn "webview" --include=*.py --include=*.toml --include=*.bat --include=*.ps1 . | 排除 .venv/docs/__pycache__ → 6 命中
含   pyw：同命令加 --include=*.pyw                                                  → 20 命中
```
⇒ 建议处置：把 `learn-deps-suspects-20260918.md` 的「偏删」结论标为**已否证**（改档属文档位，留人工／主班）；`requirements.txt:3` 的 `pywebview>=4.4,<7` **保留**。

**顺带一条同源提醒**：`README.md:40` 早已写明「`launcher.pyw` 自己 spawn `streamlit run app.py` 并开 **PyWebView** 窗口」——那份 9-19 档与 README 直接矛盾，当时没人发现。**根因是"按扩展名筛文件的 grep"被当成了"全仓"。**

---

## 五、判据对照（卷宗四条）

| 判据 | 判定 | 落点 |
|---|---|---|
| ①依赖面清单 | ✅ | 第一节：声明层 4 行表＋实装层两环境（62／205）＋node 面零发现 |
| ②钉死度评估 | ✅ | 第二节：9/11 有上界、2 条 dev 无上界、hash 0、**越界 0 条**、freeze↔venv 全等仅 50/195（freeze 钉错对象） |
| ③预警清单 | ✅ | 第三节 **W1–W7**（🔴2／🟡3／🟢2），环境类漂移预警在 W3 |
| ④零安装 | ✅ | 未 `pip install`／未建 venv／未联网／未跑 `pip --outdated`；只读 `pip freeze`×2＋AST＋grep。工作树除本档外 0 变化 |
| 附加：`data/progress.db` 未被写 | ✅ | 开工／收工 sha8 均 `cd2dbce4`（122,880 B），与在册基线前缀一致 |

## 六、给主班的「可直接批的形状」（都不自动执行）

| 编号 | 动作 | 最小改动面 | 回滚成本 | 复算读数 |
|---|---|---|---|---|
| A | **`.venv` 补装 pywebview**（闭 W1） | **零文件改动**，1 条命令：`.venv\Scripts\python.exe -m pip install "pywebview>=4.4,<7"` | 低（`pip uninstall`，`.venv` 不在 git 里） | 装后 `.venv/Scripts/python.exe -c "import importlib.metadata as m;print(m.version('pywebview'))"` |
| B | **系统 python 补装 streamlit-ace**（闭 W2 的开发面） | 零文件改动，1 条命令 | 低 | `python -c "import streamlit_ace"` rc=0 |
| C | **freeze 重钉到 `.venv`**（闭 2.3） | `requirements-freeze.txt` 1 个文件整体重写（195 → 约 62 行） | 中（旧件留档即可回滚） | 重钉前后备 `wc -l`＋`freeze∩venv 全等 62/62` |
| D | **`start.bat` 建 venv 后补装依赖**（闭 W6 根因） | 在 `start.bat:18`（venv 建好）与 `:19`（`set PYTHON=`）之间插 1 行 `"%PYTHON%" -m pip install -r requirements.txt` | 低（1 行） | 删 `.venv` 后跑 `start.bat`，再跑 `.venv/.../python.exe -m pip freeze \| wc -l`（期望 ≥73＝62＋pywebview 族） |
| E | **依赖面加守卫测试**（闭 W5） | 新增 1 个测试文件（核对声明 11 条在两环境均可 import＋freeze 覆盖运行面） | 低（新文件） | 新测试件 passed 计数＋故意卸一个包看它是否变红 |
| F | **`_ensure_ace` 降级要出声**（闭 W2 的静默面） | `ui/components.py:123` 前加一条 `render_notice`／`st.caption` | 低，但**改的是用户可见文案＋生产码** ⇒ 双人工闸（与本波 l927-09 的文案面口径一致） | 降级路径出现可见提示；`tests/test_ui_behavior.py` 需同步接线 |

⚠ A–F 全部**未执行**：A／B 是安装动作、C 是重钉基线、D／E／F 改生产码或测试位 ⇒ 均按 brief §4 停人工闸后，本单只出材料。

## 七、遗留

1. **W3 的数值差异未实算**（要跑学生代码＝执行面，且属跨版本结论）：`numpy 2.3.5↔2.5.1`、`scikit-learn 1.9.0↔1.9.1` 对 `20_numpy_basics`／`23_sklearn_advanced` 共 8 个题面的 `expected_output` 是否逐字一致，需另开一单（可双解释器对照跑，不写库）。
2. **未跑任何测试**（并发窗禁跑全量；本单判据也不需要）。W2 的"绿覆盖不到"结论来自**读码＋桩点定位**，非跑红复现。
3. `.venv` 62 包里有 `coverage`／`f2py`／`fonttools`／`git`／`pytest` 等，**未逐个追要性**（谁是传递依赖 vs 直接选择），只做了顶层 11 条的三面核对；若要出"最小可运行依赖集"需另单。
4. 本档**未代登 insights 索引**（本仓有真闭合哨兵 `tests/test_insights_index_closure.py`，现 92/92）⇒ 与 l927-09／l927-11 一并**待主班代登**。
