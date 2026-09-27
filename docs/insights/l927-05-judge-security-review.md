# learning 判题安全边界复核（执行安全域年度巡检）——l927-05，2026-09-27

> 执行：波次 19 只读采集子班 `qoder-executor-20260927-1400-learn44`，cwd `D:\code\learning-system`。
> 时戳 `2026-09-27T14:00+08:00`。盘态：HEAD `2665f0a`、`git status --porcelain` **0 行**（本班自取，不信 brief 转述）。
> 性质：**只出现状与缺口清单**。资源限制／超时／沙箱参数**一律未改**，判分逻辑**一律未动**，配置**一律未写**。
> 卷宗口径：CLAUDE.md 路由表把「判题逻辑、执行安全边界」列为升级硬触发域 ⇒ 本档是**给升级档评审用的材料**，不是修法。

---

## 一、边界参数表（现值 ＋ 配置来源，逐位盘上复点）

### 1.1 执行侧（`core/runners/`，四语言）

| 参数 | **现值** | 落点（file:line） | 配置来源 | 覆盖面／备注 |
|---|---|---|---|---|
| Python 运行超时 | **5 s**（墙钟） | `python_runner.py:104 timeout_sec = 5` | 类属性硬编码 | `agent_dev` 复用同一实例（`judge.py:16-22 _RUNNERS`）⇒ 两门共享 |
| SQL 执行超时 | **2 s** | `sql_runner.py:116 timeout_sec = 2` | 同上 | 实现是 `threading.Timer(2, conn.interrupt)`（`:181`），非杀进程——只打断 SQLite VM |
| SQL 结果行上限 | **10,000 行** | `sql_runner.py:117 _MAX_ROWS` | 同上 | 超限截断并附「结果集过大」提示（`:200-204`） |
| C++ 总超时 | **10 s** | `cpp_runner.py:24 total_timeout_sec = 10` | 同上 | 编译＋运行**共享**这 10 s |
| C++ 编译超时 | **7 s** | `cpp_runner.py:25 compile_timeout_sec = 7` | 同上 | 超时返回 `error_kind="timeout"`（`:119-124`） |
| C++ 运行超时（余量） | **`max(1, 10 − 已用)` s** | `cpp_runner.py:139` | 同上 | 🔴 下限 floor 1 s ⇒ 见 §三 G6 |
| R 运行超时 | **5 s** | `r_runner.py:15 timeout_sec = 5` | 同上 | |
| 超时后二次回收等待 | **2 s**，再超时则 `out/err = b"", b""` | `python_runner.py:134-136`／`cpp_runner.py:118,153` | 硬编码 | 🔴 输出证据静默丢失 ⇒ G7 |
| `taskkill` 自身超时 | **10 s** | `python_runner.py:80-82` | 硬编码 | 整棵进程树回收（`/F /T`）；非 Windows 退化为 `proc.kill()` |
| stdout 上限 | **1 MB**（`1_000_000`） | `python_runner.py:30 MAX_STDOUT_BYTES` | 模块常量 | cpp／r **import 复用同一常量**（`cpp_runner.py:11`、`r_runner.py:10`）⇒ 四语言同源单点 |
| stderr 上限 | **100 KB** | `python_runner.py:31 MAX_STDERR_BYTES` | 同上 | 截断带「输出过长，已截断（>N 字节）」用户可读提示 |
| stdin 上限 | **1 MB** | `python_runner.py:92 _MAX_STDIN_BYTES` | 同上 | 🔴 **静默截断、零提示**（在册缺陷 D-1，见 G2） |
| 环境变量白名单 | **9 键**：`SYSTEMROOT/PATH/TEMP/TMP/USERPROFILE/APPDATA/LOCALAPPDATA/PYTHONIOENCODING/PROCESSOR_ARCHITECTURE` | `python_runner.py:36-41 _ENV_ALLOWLIST`＋`:49 _safe_env` | 同上 | 三外部 runner 共用；`PROCESSOR_ARCHITECTURE` 是为 R 退出清理不崩而放行（`:33-37` 注释，2026-05-30 二分定位） |
| PATH 收窄 | 解释器目录 ＋ `System32` ＋ `%SYSTEMROOT%` | `python_runner.py:44-47,52-57`；cpp 另置 `g++ 目录＋系统目录`（`cpp_runner.py:95-97`） | 同上 | 取代早期「完整继承父 PATH」，学生代码不能经 PATH 调任意程序 |
| Python 解释器隔离 | **`-I`** | `python_runner.py:118-119 [sys.executable, "-I", src]` | 同上 | 忽略用户 site-packages 与 `PYTHON*` 环境变量 |
| 执行工作目录 | `tempfile.TemporaryDirectory(prefix="ls_py_/ls_cpp_…")`，`ignore_cleanup_errors=True` | `python_runner.py:110`／`cpp_runner.py:87` | 同上 | 源码写进临时目录再跑；**cwd 不是围栏**（绝对路径不受 cwd 约束）⇒ G3 |
| SQL 语句闸 | SQLite **authorizer**：只放 `SQLITE_SELECT/READ/FUNCTION/RECURSIVE`，其余 `SQLITE_DENY` | `sql_runner.py:161-172`，`:189 conn.set_authorizer(...)` | 代码内 | 多语句另由 `cur.execute()` 单语句限制挡（`_split_sql_statements:17` 只用于题面切分） |
| setup_sql 权限 | **不受 authorizer 约束**（authorizer 在 setup 之后才装） | `sql_runner.py:187`（executescript）→ `:189`（装 authorizer） | 题库 yaml | 信任「题面＝可信源」⇒ G8 |
| 公开部署总闸 | `RUNNER_SECURITY_MODE=public` **或** `PUBLIC_DEPLOY=1` ⇒ **拒绝执行学生代码** | `base.py:29-36 check_security()`＋`config.py:10-17` | **仅环境变量**，默认 `local_only` | 四 runner `run()` 首行都调它 ⇒ 真总闸；错误形状 `error_kind="sandbox"` |

### 1.2 判题侧（`core/judge.py` 本体）

- `_RUNNERS` 字典硬编码 5 键映射（`:16-22`），`agent_dev → PythonRunner`；**judge 自身不含任何超时／资源参数**，全部下沉到 runner。
- 本班**未动**判分口径：`ok`／`exit_code`／通过-失败判定逐字未碰（HEAD 那笔 `2665f0a` 只改 `error_kind` 列的取值，commit 自述「判题结论一字不改」）。

### 1.3 AI 点评侧（`core/ai_review.py`，判题链的出网分支）

| 参数 | 现值 | 落点 | 来源 |
|---|---|---|---|
| 单模型调用超时 | **30 s** | `:22 TIMEOUT_SEC` | 硬编码 |
| 级联链总预算 | **45 s**（deadline 单调钟切块） | `:23 _CHAIN_BUDGET_SEC`；`:231-237` | 硬编码 |
| 单字段截断 | **4,000 字符** | `:24 _MAX_FIELD`（注释注明为绕 Windows 32 KB cmdline 限） | 硬编码 |
| 反馈缓存条数上限 | **64** | `:56 _FEEDBACK_CACHE_MAX`，`:64/:100` while 裁剪 | 硬编码 |
| LLM 可执行脚本路径 | `D:/code/scripts/llm_call.py`，**`LLM_SCRIPT` 环境变量可覆盖** | `config.py:5-7`；调用点 `ai_review.py:527-533` | 环境变量 |
| 该子进程的 env | **`{**os.environ, ROLE_MODEL}`＝父进程全量环境**（非白名单） | `ai_review.py:524-526` | 代码 |

### 1.4 服务暴露面（判题入口的边界）

| 参数 | 现值 | 落点 |
|---|---|---|
| HTTP 绑定地址 | **`127.0.0.1`** | `.streamlit/config.toml` `[server] address`——**全站唯一单源** |
| 显式传参 | `start.bat:27`、`launcher.pyw:112` 传 `--server.address 127.0.0.1`；`scripts/smoke_boot.py:10-15` **不传**（靠 toml 兜） | 在册（l924-27 C4） |
| 鉴权层 | 无（Streamlit 原生无登录面） | 相邻红线域 ⇒ 本班**只登记不裁决**，见 G9 |
| 错误细节外泄 | `showErrorDetails = false`（config.toml `[client]`）；`toolbarMode = "minimal"`；`gatherUsageStats = false` | 现值在世 |

---

## 二、近期变更清单（`git log` 实测）

| commit | 日期 | 动了边界的哪一块 | 性质 |
|---|---|---|---|
| `2665f0a`（**HEAD**） | 2026-09-27 | `python_runner.py` ＋20/−4：新增 `_error_kind_for()`，把编译期错误从「一律 runtime」分出 `syntax` | 边界**读数**变化，非边界**值**变化；判题结论自述不改 |
| `3dcdcbc` | 2026-09-25 | 四语言共用 `error_feedback` 一张表（judge／4 runner／sql 全触） | 超时话术单一来源化（`timeout_message`）；`error_feedback.py:12` 自述此前「同一个 timeout 在四处分别写作…」 |
| `cbda0c4` | 2026-09-25 | 新增 `tests/test_sandbox_limit_boundaries_20260925.py`（373 行） | **把「实际边界」钉成可复算断言**，并登记 D-1…D-4 三类缺席限额；**未改任何实现** |
| `ee40bd7` | 2026-09-23 | `CppRunner` 补通配兜底，多版本 MinGW 目录可发现 | 🔴 **放宽了发现面**（PATH/g++ 定位），属边界变更而非纯修 bug |
| `4a16ac9`／`39ef90e` | 2026-09-16 | judge 三函数反例边界补测／docstring 契约化 | 零行为改动 |
| `57dfb21` | 2026-09-04 | **「bind server to loopback」**＝`127.0.0.1` 回环约束的引入笔（同笔锁依赖＋自动备份） | 暴露面收窄，本域唯一一次结构性收紧 |
| `b14a136` | 2026-07-14 | 建立本地基线 | ⚠️ `git log -S"_ENV_ALLOWLIST" -- core/runners/` 与 `-S"timeout_sec"` 各只命中 **2 笔**（baseline ＋ 3dcdcbc）⇒ **白名单自 07-14 未变过**；5 个 timeout 数值同样 0 变更 |

**小结**：近 30 天这条域的热度全在「**话术与读数**」（error_kind／行级反馈／超时文案统一），
**边界数值零次调整**，**暴露面只收紧过一次**（09-04 回环），**放宽过一次**（09-23 cpp 通配兜底）。

---

## 三、边界缺口清单（只列不改；供升级档评审）

| # | 缺口 | 现证 | 严重度 | 在册状态 |
|---|---|---|---|---|
| **G1** | **CPU 时间／内存／进程数三类限额全无实现**，只有墙钟＋事后 `taskkill` 回收 | `test_sandbox_limit_boundaries_20260925.py::TestMissingCapsLedgerPin`（缺席钉子：真接了 rlimit/Job Object 它会转红）；`bytearray(10**12)` 兜底只剩 OS `MemoryError` | 中 | **已在册**（D-2/D-3/D-4），本班复点仍在 |
| **G2** | stdin 超 1 MB **静默截断**，stdout/stderr 一字不提 | 同件 `:161` 登记 D-1；`python_runner.py:95-100 _safe_stdin` 无提示 | 中 | 已在册 |
| **G3** | 🔴 **没有 OS 级沙箱**：白名单＋PATH 收窄＋临时 cwd 都**不限制**学生代码用**绝对路径**读写文件、起 socket 出网。`import os; os.remove(...)`／`urllib.request.urlopen(...)` 在 `local_only` 下畅通无阻 | 全仓 `core/runners/` 内 `rlimit`/`setrlimit`/Job Object/`CREATE_RESTRICTED_TOKEN` **零命中**；`README.md:64` 却写「本地运行用户代码……带**安全**与超时边界」 | **高（口径与实现不符）** | **未见在册**——`learn-judge-edges`／`learn-judge-mode-census` 都在讲判分边界，不在讲 OS 边界 |
| **G4** | `python_runner.py:54` 注释「本机单人边界仍以 **README 的信任模型**为准」——该信任模型在 README **不存在**：全仓 `grep -rn "信任模型"` 唯一命中就是这条注释自身 | 实测两行 grep | 中 | **新登记（本班）** |
| **G5** | 边界参数**零运维旋钮**：5 个 timeout／3 个字节上限／白名单全部硬编码在模块里；本仓**没有** `data/system_config.json`，`core/config.py` 只有 2 个 env getter（`RUNNER_SECURITY_MODE`／`LLM_SCRIPT`）⇒ 调 1 个数字＝改生产码＝触升级硬触发域 | `ls data/*.json` 空；`config.py` 全文 17 行 | 低-中（工程性） | **新登记（本班）** |
| **G6** | cpp 10 s 总预算里编译占 7 s ⇒ 慢编译把学生程序挤到 floor `max(1, …)`；**同一份代码在不同机器（编译耗时不同）可得到不同判定** ⇒ 稳定性缺口，非安全缺口 | `cpp_runner.py:139` | 中 | **新登记（本班）**；本机无 g++ ⇒ 该链恒 skip，**现网测不到**（见 §五） |
| **G7** | 超时 kill 后再 `communicate(timeout=2)`，仍超时则 `out_b, err_b = b"", b""`：死循环题的**部分输出证据被丢弃**（`timed_out` 判定本身仍正确） | `python_runner.py:134-136` | 低 | **新登记（本班）** |
| **G8** | SQL authorizer 在 `setup_sql` **之后**才装 ⇒ 题库 setup 全权；「题面 yaml 可信」是**未写进文档的信任前提**（与 G4 同根） | `sql_runner.py:187/:189` | 低-中 | **新登记（本班）** |
| **G9** | `LLM_SCRIPT` 环境变量可把**要执行的脚本路径**换成任意值，且调用点传 `{**os.environ}`（父进程全量环境，含凭据）给该子进程 ⇒ 能改应用环境者即可以用户身份执行任意脚本。相邻**凭据／鉴权红线** ⇒ **本班不判严重度、不提修法**，只登记事实 | `config.py:5-7`＋`ai_review.py:524-533` | **交人工** | 命中 brief §4 红线域 |
| **G10** | `smoke_boot.py` 不显式传 `--server.address`，靠 `config.toml` 兜回环；toml 那行被删则冒烟实例绑 LAN | `.streamlit/config.toml`＋`scripts/smoke_boot.py:10-15` | 低 | **已在册**（l924-27 C4／遗留 3），本班复点仍在 |
| **G11** | **与 `75fb` 死循环发现的交叉**：同一风险类、两个实现，**边界不对称**——主仓有墙钟闸（5 s → `_kill_tree` → `timed_out`＋`error_kind="timeout"`＋话术「可能存在死循环」）；demo 侧（`learning-system-demo/assets/runners.js`，Pyodide WASM 主线程同步）**零超时闸，死循环直接挂起页面**（`grep -nE "timeout|interrupt" runners.js` → 0 命中，见 75fb 结果件证据节）。demo 侧输出爆炸反而有双截断（harness 200,000 字符＋显示层 8,000） | `done/20260925-120537-75fb.result.md` 执行摘要④／遗留 1 | 中（跨仓） | 修法（Pyodide `setInterruptBuffer` 或迁 Web Worker）由 75fb 交回主班，**未立单** |

> ⚠️ G11 的证据边界：`learning-system-demo` 在**本班 cwd 之外**，按卷宗禁止事项「触碰 cwd 之外的路径」**本班未开其盘上件**，
> 交叉结论全部取自 `done/20260925-120537-75fb.result.md`（09-26 03:35 落）**属二手引用未复点**。主班要钉这条须另派 demo 域的单。

---

## 四、巡检卫生项（顺带核到，不属判题域，只登记）

- **`learning-system/tmp/` 大量残留**：顶层 **84** 条目、递归 **387** 文件、**4,999,100 B**，含 2 份**生产码备份**
  （`tmp/l923-33-path.py.bak`、`tmp/l923_07_dashboard_mine.py.bak`）与多份 `*-mutate.py`／`*-patch.py`。
  `.gitignore:19 /tmp/` 把它整棵遮住 ⇒ `git status --porcelain` 恒 0 行、**看板看不见**。
  与波次 19 共通指示 §6「临时件落 `D:\code\tmp\<班名>`，用完自己清；别在仓根留任何临时件」相悖——
  历班把快照写在**仓内 tmp/** 而非工作区 tmp/。本班**未删任何人的在途件**（§5 现场毁灭红线），只报数。

---

## 五、本机覆盖缺口对本档结论的限制（自证边界）

- 本机 `which g++` = **NO_GPP**、无 R 安装 ⇒ `test_cpp_runner.py`（4 条）＋`test_r_runner.py`（3 条）**整件 skip**
  （复点：`9 passed, 7 skipped in 0.09s`，与 `l927-03-baseline.md` §一逐位相符）。
  ⇒ **G6/G7 的 cpp 侧、R 侧的 env `extra` 分支（`r_runner.py:69-93`）在本档全部是读码结论，非执行结论。**
- 本档未起服务、未发任何学生代码到网络、未调 LLM（零成本零出网）、未读 `data/progress.db` 内容。
- 判分逻辑／资源限制／超时／沙箱参数**零改动**（完成标准④）；产物只有本档。
- 产物**不代登 insights 索引**（本仓真闭合哨兵 `tests/test_insights_index_closure.py`，索引由主班收班单点写）。
