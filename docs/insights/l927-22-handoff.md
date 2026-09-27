---
id: l927-22
title: K-2 动态实测移交清单（两枚运行时读数的取证步骤）＋ 未登录面静态证据汇编
task: l927-22（zcode-bridge 波次 24，工作类型 docs，风险档 B）
shift: qoder-executor-20260927-1850-learn48
written: 2026-09-27T19:0x
head_at_write: 4d11b51（开工 porcelain 0 行）
mode: 🔴 **零起服务、零监听端口、零配置改动**——本班只读码＋读盘＋`netstat` 现点观察；两枚运行时读数的取证步骤写成"日间人工窗照做即可"的清单
status: 移交清单——判据①②③全中；两读数各给"方法／命令／判据／安全注意／收尾"五段，未执行任何一步
supersedes_or_extends: extends `zcode-bridge/done/20260925-154247-4d88.result.md`（遗留①②＝本档的两枚读数）、`docs/insights/learn-smokeboot-port-design-20260924.md`（§五-3 已登记"smoke_boot 不传 --server.address"，本档**不重复其端口三案**）、`docs/insights/learn-readme-commands-audit-20260922.md:25`（smoke_boot 判"禁夜跑"的在册依据）
---

# K-2 两枚运行时读数：取证清单 ＋ 静态面汇编

> 卷宗完成标准：①两读数取证步骤齐 ②静态路径复核 ③零起服务。
> 两枚读数原文（154247 遗留①）：**(A)** 谁都能连上 `127.0.0.1:8501` 的 WebSocket 并读写该库——本仓无鉴权，答案静态已知，但"回环外是否可达"需实测；**(B)** 撞口时 `smoke_boot.py` 不传 `--server.address` 的**实际绑定**。

## 〇、一句话结论

1. 🔴 **读数 A 的"可达性"这一维，应用层给不出答案，只有网络层能给**：静态复核显示 streamlit 1.59.1 的 WebSocket 握手**没有无条件身份闸**——`starlette_websocket.py:408-449` 里 XSRF 校验的形态是 `if origin_header and validate_xsrf_token(...)`（`:413`），只用来**决定是否解析 auth cookie**；不带 `Origin` 头的非浏览器客户端会走空 `user_info`，然后 `:449 runtime.connect_session(...)` **照常建会话**。⇒ 结论：**只要 TCP 连得上，就是一个合法会话**；XSRF/CORS 是浏览器同源防线，对 curl/自建 WS 客户端无国界。所以 A 的全部悬念只剩"绑在哪个地址＋防火墙放不放行"——这正是必须实测的部分。
2. 🔴 **读数 B 的静态答案已可判半**：`--server.port` 由 CLI 显式给（`scripts/smoke_boot.py:12` 硬编码 8599）⇒ 撞口时 streamlit **不换端口**，直接 `_LOGGER.error("Port %s is not available"); sys.exit(1)`（`.venv/.../starlette_server.py:380-381`；换端口分支只在"端口未手工设定"时走 `continue`，最多 100 次 `MAX_PORT_SEARCH_RETRIES`，`starlette_server_config.py:57`）。⇒ **"漂到别的端口还绑了全网"这一支被静态排除**；剩下的悬念是"端口空着时它到底绑哪"。
3. 🔴 **绑址的决定链（本班新核，两档都未写全）**：`server.address` 的包内默认是 **None**（`config.py:916-926`），fallback 常量 **`DEFAULT_SERVER_ADDRESS = "0.0.0.0"`**（`starlette_server_config.py:60`），且当"取值为默认且 `not config.is_manually_set('server.address')` 且有 IPv6"时**升格绑 `"::"`（IPv6 双栈通配＝回环外可达）**（`starlette_server.py:84-98`）。⇒ **本仓 smoke_boot 的回环性，全押在 `.streamlit/config.toml` 那一行 `address = "127.0.0.1"`**（该件确在版本库内：`git ls-files .streamlit/` 命中；`config.py:2847-2848` 口径下 per-project 覆盖 global，不会被家目录配置悄悄改回去）。
4. ⚠ **smoke_boot 自己看不见这个风险**：它的健康轮询只打 `http://127.0.0.1:8599/_stcore/health`（`:24`）⇒ 绑 `::`（全网）时回环一样通、脚本一样报 `health ready: True`。**"绿"与"没暴露"在本仓是两个互不蕴含的命题**（属"绿但零覆盖"家族在册形态）。
5. 🔴 **本清单第 0 步不是可选项**：任何一次起服务都必须先把 `LS_PROGRESS_DB` 指到临时库——`core/progress.py:13-34` 的 A5① 默认库护栏**只在 `PYTEST_CURRENT_TEST` 存在时生效**（`:26-27`），`streamlit run` 不受保护；而 6 个页面在渲染时都无条件 `ProgressDAO()`（`ui/pages/home.py:24`、`dashboard.py:105`、`diagnostic.py:60`、`language.py:198`、`mistakes.py:62`、`path.py:27`），`ProgressDAO.__init__` 会 `os.makedirs`＋`sqlite3.connect`＋`PRAGMA journal_mode=WAL`＋`executescript CREATE TABLE IF NOT EXISTS`×7（`core/progress.py:54-116`）⇒ **"只是起个服务看一眼"本身就是对生产库 `data/progress.db` 的一次写型操作**（WAL 建侧车、可能 checkpoint）。

---

## 一、② 静态路径复核：四个入口的 `--server.address` 缺省值代码路径

现点复算（本班实跑，只读）：`grep -rn "server.address\|server.port\|streamlit run" start.bat launcher.pyw scripts/smoke_boot.py scripts/find_port.py`

| 入口 | 端口来源 | `--server.address` | 绑址实际决定者 | 起服务用的解释器 |
|---|---|---|---|---|
| `start.bat:26-27` | `scripts/find_port.py`（探 **8511-8530**，`bind("127.0.0.1",p)` 后**立即 close** ⇒ bind→close 竞态在册 `learn-smokeboot-port-design-20260924.md:146/187`） | **显式 `127.0.0.1`** ✔ | CLI | `.venv\Scripts\python.exe`（`start.bat:19`） |
| `launcher.pyw:277`＋`:111-115` | `find_free_port(preferred=8511, max_tries=20)`（同样 `bind(("127.0.0.1",p))`，`:81-89`） | **显式 `127.0.0.1`** ✔（`:112`） | CLI | `.venv`（launcher 自身） |
| `scripts/smoke_boot.py:11-13` | 硬编码 **8599** | 🔴 **未传** | **`.streamlit/config.toml`**（依赖 `cwd`：脚本 `:14` 传 `cwd=str(ROOT)` ⇒ 项目配置会被发现；家目录配置在 streamlit 顺序里被项目配置覆盖） | `sys.executable`＝**谁调用它**（这是版本分裂点，见 §三·前置 2） |
| 裸 `streamlit run app.py`（开发模式，`launcher.pyw:14` 注释点名） | 包默认 **8501**（`config.py:931-936` `default_val=8501`） | 未传 | 同上 | 调用者 |

🔴 **对锚点措辞的收窄**：154247 写"谁都能连上 `127.0.0.1:8501`"，但本仓**三个正式入口没有一个落在 8501**（start.bat/launcher 从 **8511** 起找、smoke_boot 用 **8599**）⇒ 8501 只有"有人手跑裸 `streamlit run app.py`"时才出现。移交清单因此**必须先定入口再定端口**，否则会去测一个本仓根本不用的端口。
另复核在册档 `learn-readme-commands-audit-20260922.md:25` 那句"起 streamlit 子进程＋**绑 127.0.0.1:8599**"：端口对、**绑址是推断而非实测**（实际由 config.toml 决定，见本表第 3 行）——该档"禁夜跑（起进程）"的定性**与绑址无关，仍然成立**。

包侧生效值的零服务取法（**这一步不需要起服务**，可在任何窗跑）：
```
cd D:\code\learning-system && .venv\Scripts\python.exe -c "from streamlit import config; config.get_config_options(); print(config.get_option('server.address'), config.is_manually_set('server.address'), config.get_option('server.port'))"
# 期望：127.0.0.1 True 8501（cwd 必须是仓库根，否则项目 config.toml 不会被读到 ⇒ 会打印 None False 8501）
```

---

## 二、① 读数 A：回环外可达性取证步骤（日间人工窗，15–20 分钟）

**要坐实什么**：本机之外的人（同 LAN、或本机上非回环地址）能不能连到 app 端口并建立会话；Windows 防火墙是否已经在替本仓兜这层。

- **前置 0（硬）**：`set LS_PROGRESS_DB=%TEMP%\l92722-sandbox.db`（或 PowerShell `$env:LS_PROGRESS_DB="$env:TEMP\l92722-sandbox.db"`）；跑完复点生产库 `certutil -hashfile data/progress.db SHA256` 前 8 位应仍为开工基线值。
- **前置 1**：先跑 §一 末的零服务取法，确认 `server.address` 生效值；再 `netstat -ano | findstr :<PORT>` 确认该端口当前**无监听**（本班 18:5x 现点：8501／8511／8512／8599 **四条都无 LISTENING**，机器另有 50 个监听套接字，与端口无冲突）。
- **前置 2**：钉死解释器＝`.venv\Scripts\python.exe`（本机实装 streamlit **1.59.1** 在 `.venv`、**1.58.0** 在全局 `D:\Program\Lib\site-packages`；两版绑定实现同族但默认值可能不同 ⇒ **不钉解释器＝测的是另一个包**）。
- **步骤（起一次服务，测三腿，随后立刻关）**：
  1. 腿 1（回环，正对照）：`curl -sS -o - -w "\n%{http_code}\n" http://127.0.0.1:<PORT>/_stcore/health` ⇒ 期望 `ok`／200。
  2. 腿 2（**本机非回环地址**，主判据）：先 `ipconfig | findstr IPv4` 取本机 LAN IP（记为 `<LAN_IP>`，**不要把 IP 写进报告**，只记"192.168/10.x 网段"级别），再 `curl http://<LAN_IP>:<PORT>/_stcore/health`。
     - 绑 `127.0.0.1` ⇒ `Could not connect` / `Connection refused` ⇒ **A 判"回环内"**；
     - 返回 200 ⇒ **A 判"回环外可达（同机侧证）"** ⇒ 立刻进第 4 步（防火墙放行同机自连不构成 LAN 证据，但说明监听在 `0.0.0.0`）。
  3. 腿 3（**LAN 另一台机器／手机热点同网段**，坐实判据）：在对端执行同一条 `curl http://<LAN_IP>:<PORT>/_stcore/health`。三态记录：`refused` / `timeout`（＝防火墙挡） / `200`（＝真暴露）。🔴 三态必须分开记，"timeout"与"refused"结论不同：前者是防火墙在挡（应用侧仍绑了全网，属"靠 OS 兜"），后者才是绑址本身挡的。
  4. 会话腿（证明"连得上＝有会话"，不需要真操作数据）：`curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: <base64>" http://<LAN_IP>:<PORT>/_stcore/stream` ⇒ 记 **101 还是 403/400**。配合 §一-1 的代码路径，**若腿 3 通且这里 101，则"未登录可读写"成立**；若 101 只在腿 1 出现，则暴露面止于回环（＝现状设计意图）。
  5. 只读观察防火墙口径（**不改任何规则**）：`netsh advfirewall show allprofiles state`（记 Profile 与 DefaultInboundAction）＋（PowerShell）`Get-NetFirewallProfile | Select Name,DefaultInboundAction`。
- **判据落表**：`(腿2, 腿3, 会话腿)` 三元组 → `回环内 / 绑全网但被防火墙挡 / 全网可会话` 三档，逐档写实际值。
- **安全注意**：① 全程 `LS_PROGRESS_DB` 指向临时库；② **不要**把 `attempts`/`learning_events` 的真实内容暴露给任何 HTTP 响应或报告（本仓 `data/progress.db` 有 15 行历史作答）；③ 测完立刻 `terminate`（launcher 的 `terminate_backend` 语义可照用：terminate → 4s → kill），并 `netstat` 复点端口已释放；④ 禁夜跑档在册（`learn-readme-commands-audit-20260922.md:25/32`）⇒ **只排日间窗**；⑤ 并发窗内不要跑（同仓可能有人在做性能基线，起服务会让读数不可归因）。
- **收尾**：删临时库；把端口/PID/三态/会话码/防火墙四档读数写进 result；`certutil` 复点主库 size＋sha8。

## 三、① 读数 B：`smoke_boot.py` 撞口时的实际绑定取证步骤（日间窗，10 分钟）

**要坐实什么**：8599 被占时，`smoke_boot`（不传 `--server.address`）到底是"退出"还是"漂到别的端口"，漂/不漂时**内核实际绑在哪个地址**。

- **方法 1（零服务，先做）**：`python -c` 打印生效 `server.address` 与 `is_manually_set`（见 §一 末）——若这一步就打出 `127.0.0.1 / True`，则 B 的"绑址"半部已被静态闭合，方法 2 只剩复核"内核真绑"。
- **方法 2（真起服务＋造撞口）**：
  1. `set LS_PROGRESS_DB=...`（同前置 0）。
  2. 造占位（**用回环占 8599**，与真实场景同形）：`powershell -c "$l=[System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse('127.0.0.1'),8599); $l.Start(); Start-Sleep 300; $l.Stop()"`（后台开一个 5 分钟占位窗口）。
  3. `.venv\Scripts\python.exe scripts\smoke_boot.py`（`sys.executable` 必须是 `.venv`，否则测的是 1.58.0）。
  4. **同时**取三类读数：
     - smoke_boot 自己的 stdout（期望：`streamlit exited early rc=1` ＋ `health ready: False`）；
     - streamlit 日志（`smoke_boot` 把子进程 `stdout/stderr` 指向 `subprocess.DEVNULL/STDOUT`，**看不到 `Port 8599 is not available` 这行**——它进的是 streamlit 自己的 logger 输出，被 DEVNULL 吞了）⇒ 因此**必须**补第三条腿：`netstat -ano | findstr :8599` ＋ `Get-NetTCPConnection -LocalPort 8599 -State Listen | Select LocalAddress,LocalPort,OwningProcess`，取 **LocalAddress 与 PID**（PID 应等于占位进程，不等于 streamlit）；
     - 换占位地址再测一次（把占位改成 `0.0.0.0:8599`：`[System.Net.IPAddress]::Any`）⇒ 若 smoke_boot 仍 rc=1，则"CLI 显式端口不漂"这一支在两种占位形态下都闭合。
  5. **不漂端口的情形下**，再测"端口空着时绑哪"：清掉占位 → 起 smoke_boot → 立刻 `Get-NetTCPConnection -LocalPort 8599 -State Listen | Select LocalAddress`。🔴 判读表：`127.0.0.1`＝config.toml 兜住（现状符合设计）；`::` 或 `0.0.0.0`＝**回环绑定已失效**（此时 §二 腿 2/3 必须补测，且属可静默回归——`rg "config.toml" tests/` 在册零断言，见 §四-3）。
- **安全注意**：① 步骤 2/4 的占位脚本只在**回环/本机通配**上监听一个**不接受请求**的 socket，不提供任何服务、不读任何数据，测完 `Stop`／超时自释；② 严禁把 smoke_boot 的 8599 与真实使用中的 launcher 端口（8511+）混测；③ 起服务前复点主库 sha8，结束后再点一次并写进 result（**不得"跑完改回去"**，`data/` 无 git 还原点）。
- **收尾**：`taskkill` 只在确认 PID 归属后使用；`netstat` 复点 8599/8511 均已无监听。

---

## 四、未登录面静态证据汇编（本班独立复点，逐条带出处）

1. **无身份层（实体否证）**：本仓产品码无鉴权概念，`data/progress.db` 8 张表**身份类列名命中 0**——两条读数由 154247 一手实测（`rg -c` 11 个关键词全 0；`identity_like_columns = []`）。本班未重复扫（同域无漂移：`git log` 该域无新码改动），只**复点其结论仍与盘上一致**：`grep -rn "login\|Bearer\|permission" core ui app.py` → 0 命中（本单一枚 `ui/pages/home.py` 的 `security_notice_seen` 提示是**告知**不是闸）。
2. **在世对应物＝部署模式闸**（"非本机部署一律拒执行"）：`core/config.py:10-17`（`RUNNER_SECURITY_MODE`／`PUBLIC_DEPLOY` → `is_public_deploy()`）＋四 runner `run()` 入口的 `check_security()`；🔴 注意语义差：它拒绝的是**执行学生代码**，**不是拒绝网络连接**——公开模式起来的服务照样收 WS 会话，只是每次提交返回拒绝文案。⇒ **它不构成 §二 的替代答案**。
3. **回环绑定无测试钉（复点，仍成立）**：`rg -n "config.toml" tests/` → 零断言；`rg -n "127\.0\.0\.1" tests/` 命中项全是 `test_launcher`／`test_find_port` 自己的 bind 夹具，不是配置断言 ⇒ **删掉 `.streamlit/config.toml` 里那行不会被任何测试拦下**，按 §一-3 的链即变成 `"::"`。属裁决面（是否加一条"配置断言"），本班未加。
4. **包侧会话层无身份闸**（本班新核，见 §〇-1 的行号链）＋ 存在 `/_stcore/auth/login|logout|callback` 路由（`.venv/.../starlette_auth_routes.py:628-646`）——那是 streamlit 云/OAuth 的形状，本仓未配置任何 auth 提供者 ⇒ 不构成本机的登录面。
5. **默认库护栏不覆盖服务态**：`core/progress.py:13-34`（A5① 2026-09-27 用户授权，由来正是 `learn36` 那次 `dao=None` 写出 14 行合成数据）＋ `:26-27` 的 `PYTEST_CURRENT_TEST` 条件 ⇒ 服务态一律走 `_DEFAULT_DB`；配套在册前科：`core/judge.py:199`、`:342`、`core/recommend.py:73`、`:232`、`core/report.py:22` 全是 `dao or ProgressDAO()`。⇒ **§二/§三 的前置 0 是强制项**，也是本班自己"零写库"的做法依据（本班从未建立 sqlite 连接）。
6. **凭据面（只报存在性与形状，零值）**：`_call` 子进程 env 继承父进程（`core/ai_review.py:519-536`），key 由 `D:/code/scripts/llm_call.py` 自行解析——**该路径在 cwd 外＋凭据域双红线，本班未读**；154247 遗留② 已把"是否经日志外泄"交人工，本档**不重复登记**。本班进程内唯一凭据形态项是 harness 注入的路径名（值未读取）。
7. **现点盘态**：`data/progress.db` **122,880 B／sha8 `cd2dbce4`**（与在册基线同值）；`ls -la data/` 只有 `.gitkeep / backups/ / progress.db(+ -shm 32,768 / -wal 0)` ⇒ **`data/streamlit.log` 与 `data/launcher.log` 都不存在**（前者由 `launcher.pyw:121` 起后端时以 `"ab"` 创建、后者由 `_setup_logging()` 按 `launcher.pyw:39` 的 `LOG_FILE` 创建，均未见＝本机近期没经由 launcher 起过服务；`start.bat` 那条路径压根不落日志文件）。⇒ 154247 遗留②"中枢报错回显会进 `data/streamlit.log`"这一假设的**文件前提在当前盘态下不成立**，交接时需重述为"起过一次服务之后，这两个文件里是否出现含 key 的行"（本班**未读任何日志内容**，属凭据/隐私域）。

---

## 五、③ 零起服务自证 ＋ 复算入口

- **零起服务主证**：本班**未执行** `smoke_boot.py`／`streamlit run`／`start.bat`／`launcher.pyw` 任一入口；未 bind 过任何 socket（唯一涉及端口的动作是 `netstat -ano | grep -E ":(8501|8511|8512|8599)"` 的**读表**，输出零行＝当前无监听）；未改 `.streamlit/config.toml`、未改防火墙规则、未设 `RUNNER_SECURITY_MODE`／`LS_PROGRESS_DB`（只在清单里写给执行人）。
- **零写库**：未建立任何 sqlite 连接（本班不需要库读数，两枚读数都是"交给人取"的）；`data/progress.db` 开工 **122,880 B／`cd2dbce4`** → 收工同值（`certutil -hashfile … SHA256` 前 8 位）。侧车 `-shm` mtime 变化系在册的**只读探针回写 shm 头**机理（大小 32,768 B 不变），本班连库都未开，与之无关，未去"清"。
- **只读边界**：为复核绑定决策链 import/读取了 **`.venv` 内**的 streamlit 源码（`web/server/starlette/*.py`、`config.py`，路径均在 cwd 内）；未读 `D:/code/scripts/llm_call.py`（凭据域＋cwd 外，本班只 `ls` 过它存在，未读内容）；未读任何日志内容、未取任何学生作答文本。
- **git 面**：`git status --porcelain`＝本班三件 `?? docs/insights/l927-2{0,1,2}-*.md`，生产码/配置/题面零 diff；未 add/commit/checkout/restore/stash/clean。
- **未跑 pytest**：并发窗禁跑全量（同刻 `colony41`／`quant49`／`psy77`／`kaoyan78` 在别仓）、本单零码改动；§四-3 的"测试零断言"是 `rg` 读数不是运行读数。
- 复算入口：`D:\code\tmp\qoder-executor-20260927-1850-learn48\`（本班为 l927-22 **未新增脚本**，全部取证靠上列单行命令，可整段重跑）；探针 `probe_similar.py`／`probe_face.py`／`probe_face2.py`／`probe_samples.py` 属 l927-20/21，**有意保留**作那两档的复算入口。

---

## 六、交人工的三条裁决（本班一律不动手）

| # | 待拍 | 本班已量到的后果 |
|---|---|---|
| Q1 | 要不要给"回环绑定"加测试钉（`tests/` 断言 `.streamlit/config.toml` 的 `server.address == "127.0.0.1"`）？ | 不加＝删那行会静默变 `"::"`（全网可达）且 smoke_boot 仍报绿；加＝一条只读断言，零运行时成本 |
| Q2 | 要不要让 `smoke_boot.py` 也显式传 `--server.address 127.0.0.1`（与 start.bat/launcher 对齐）？ | 传＝不依赖 config 发现与 `cwd`，成本 1 行；不传＝保持"最小暴露面靠一份配置"的现口径（`learn-smokeboot-port-design-20260924.md:188` 已按"只登记不动"处置过同一处） |
| Q3 | 读数 A 若实测为"绑全网但被防火墙挡"，本仓口径算合格吗？ | 属**产品/部署口径裁决**：现在应用侧只有一行配置在挡，OS 挡的是第二层；本班不判合格性，只保证取证步骤可照做 |

⚠ 另登记一条**执行侧风险**：本清单第 0 步（`LS_PROGRESS_DB`）一旦被执行人漏掉，一次"只为看绑定"的起服务就会对生产库做 WAL＋建表 DDL——**这正是本档把它写成硬前置的原因**（154247 的"最小方案"里这句写在括号里）。
