# learning smoke_boot 硬编码 8599 与 find_port 端口族统一：撞口复现＋两案对照＋推荐案验收口径（l924-27，只出稿 · 零生产码改动）

> **卷宗**：`zcode-bridge/inbox/l924-27.task.md`（现址 `zcode-bridge/done/`）。产出面＝本档一份；`scripts/` 零 diff（自证见 §四）。
> 🔴 **本档是两案裁决材料，一律"建议稿、未选案"**：A/B/B′ 三案与"是否顺带修健康判据＋退出码"全部交人工，执行手不代拍板。
> 三枚探针在 gitignore 的 `tmp/l924-27/`（`git check-ignore -v` → `.gitignore:19:/tmp/`）：`probe_port.py`（纯表达式级，零 streamlit）、`probe_collide.py`/`probe_collide2.py`（**一次性子进程＋45 s 超时**）、`probe_health.py`（无撞口基线）。
> ⚠ **全程未起 `app.py`**（波次纪律：冒烟启动类判据只做复现推演＋可复算命令）；被测服务是 3 行 `tmp/l924-27/tiny_app.py`，不碰 `data/`、不连库、不发 LLM 请求；两轮实验结束均复验 8599/8733 回到空闲。

## 〇、锚点与前提复核（卷宗每条前提都实测）

| 卷宗前提 | 实测 | 命令 | 判定 |
|---|---|---|---|
| `scripts/smoke_boot.py:12` 为 `"--server.port", "8599", "--server.headless", "true",` | 逐字一致 | `sed -n '10,15p' scripts/smoke_boot.py` | ✅ 零漂移 |
| `scripts/find_port.py:6` 为 `def find_port(start: int = 8511, end: int = 8530) -> int:` | 逐字一致；且该文件**只有 20 行**、`:16` 为 `sys.exit(f"no free port in {start}-{end}")`（`test_find_port.py:143` 用 0 基 `lines[15]` 钉同一行，两处不矛盾） | `sed -n '1,20p' scripts/find_port.py` | ✅ 零漂移 |
| 🔴 「`:10-14` Popen 直起」 | Popen 调用实跨 **`:10-15`**（闭合括号与 `cwd=` 在 :15）；"直起、无占用检测"成立 | `Read` 全文件 | ⚠ 行号小漂，按磁盘实况修正 |
| 🔴 **否证（本单最重要）**：「撞口时 health 轮询 150 次超时误报『启动失败』」 | **三处不成立**：① `smoke_boot.py` 全文**不含**"启动失败"字样（`rg -n "启动失败" scripts/smoke_boot.py` 空），该措辞属 `launcher.pyw:280/:287/:333/:388`；② 撞口时**根本轮不到 150 次**——Windows 下 streamlit 子进程照样起成功（探针 2 实测），health 首轮即 200；③ 后果不是"误报失败"而是**假绿成功**（探针 2 读到外来服务的 200，子进程一行都没服务过） | 见 §二 | ❌ 因果与症状都错 ⇒ 按实况改写复现结论，不判 failed |
| 🔴 否证：「start.bat 用 find_port 取口启动主服务后，smoke_boot 再起 8599 ⇒ 撞口」 | 两条入口的端口域**与 8599 不相交**：`find_port` 默认段 8511-8530、`launcher.pyw:277` 是 `find_free_port(preferred=8511, max_tries=20)` ⇒ 上界 8530。⇒ 主服务与冒烟**天然不撞**；真撞口对象只有"别的东西占了 8599"（并发冒烟班、手工 `--server.port 8599`、任意本机服务） | `rg -n "85(11\|30\|99)" --glob '!docs/**' .` | ❌ 前提的因果链不成立，但"8599 游离于端口族之外＋无占用检测"这两条**成立** |
| 「三方调用关系（smoke_boot/find_port/start.bat）」 | 实为**四方、两条独立入口链**：`launcher.pyw` 自带第二套端口探测（`:81 find_free_port`）与第二套健康判据（`:134 is_health_ready`），**不 import** `scripts/find_port.py` | `rg -n "find_free_port\|is_health_ready\|find_port" --glob '!docs/**' .` | ⚠ 面比卷宗宽，见 §一 |
| smoke_boot 的调用方 | 仅 `README.md:72`（`python scripts/smoke_boot.py`，验证命令块第 3 条）；`tests/` **零引用**、无 `.github/`、`plan.md` 无引用 | `rg -n "smoke_boot" --glob '!docs/**' .` | ✅ 影响面极小（⇒ 修复成本低，但也**没有任何桩在钉它**） |
| 🔴 新发现（卷宗未提）：失败信号本身不可编程消费 | `rg -n "sys.exit\|raise\|exit\(" scripts/smoke_boot.py` → **空输出** ⇒ 无论 ready 真假，脚本**退出码恒 0**；`ready` 只活在 stdout 文本里。而 `:14` 又把子进程 `stdout=DEVNULL, stderr=STDOUT` ⇒ 真出事时唯一诊断（streamlit 自己打的 error）被丢掉 | 见左 | 三缺陷而非两缺陷，见 §三-3 |
| ⚠ 顺带核到（不属本单，只登记） | `.streamlit/config.toml` 的 `[server] address = "127.0.0.1"` 是**唯一**把服务钉在回环上的地方；`start.bat:27` 与 `launcher.pyw:112` 都另传 `--server.address 127.0.0.1`，**只有 smoke_boot 不传** ⇒ 它靠 config.toml 兜。该行一旦被删，冒烟起的实例会绑到 LAN（真服务仍是回环） | `python -c "print(open('.streamlit/config.toml',encoding='utf-8').read())"`（`rg` 默认跳点目录，不可用） | 进 §五 遗留 3 |

## 一、调用关系图（完成标准①，rg 证据）

```
                 ┌──────────────── 入口 1：桌面 app ────────────────┐
 桌面快捷方式 ──▶ launcher.pyw ─┬─ :81  find_free_port(preferred=8501, max_tries=20)  ← 自带端口探测（不 import scripts/find_port）
 （create_shortcut.ps1）        │                                :277 实际传 preferred=8511 ⇒ 8511..8530
                               ├─ :108 start_streamlit_backend(port) ── streamlit run app.py --server.port <port> --server.address 127.0.0.1
                               └─ :134 is_health_ready(port)  ⇒ 判据 r.status == 200   ← 注释：此前 <500 会把 404 当成功
  失败路径：:276-281（端口）/:283-290（起服务）try/except ⇒ show_error_box("启动失败") ＋ return 1   （退出码可控）

                 ┌──────────────── 入口 2：命令行/开发 ─────────────┐
 start.bat ──────┬─ :26  for /f %%p in ('python scripts\find_port.py') do set "PORT=%%p"
                 │        └─ scripts/find_port.py :6 find_port(8511, 8530)（bind 试口，:16 全占则 sys.exit）
                 └─ :27  streamlit run app.py --server.port %PORT% --server.address 127.0.0.1 --server.headless false
                    （**无健康检查、无退出码**：streamlit 阻塞到关窗口，Ctrl+C 即结束）

                 ┌──────────── 入口 3：冒烟（README.md:72，人读输出）┐
 smoke_boot.py ──┬─ :10-15 Popen(streamlit run app.py --server.port "8599" --server.headless true ...)   ← 硬编码、无占用检测
                 ├─ :14 stdout=DEVNULL, stderr=STDOUT                  ← 子进程诊断被丢
                 ├─ :19-30 150 × 0.2 s 轮 http://127.0.0.1:8599/_stcore/health ⇒ 判据 r.status < 500
                 └─ 结尾无 sys.exit ⇒ **rc 恒 0**
   与入口 1/2 的端口域交集：∅（8599 ∉ 8511-8530）⇒ 今天不撞主服务，只撞"别的东西"
```

| 通道 | 端口来源 | 占用检测 | 健康判据 | 子进程日志 | 失败退出码 |
|---|---|---|---|---|---|
| `launcher.pyw`（桌面） | `find_free_port` 自带，preferred 8511 | ✅ bind | `status == 200`（**已收严**） | 写 `logs/streamlit.log` | ✅ `return 1` |
| `start.bat`（开发） | `scripts/find_port.py` | ✅ bind | ❌ 无（不起轮询） | 直接进控制台 | ❌ 无（`pause` 吞掉） |
| `scripts/smoke_boot.py`（冒烟） | **字面量 8599 ×2 处** | ❌ **无** | `status < 500`（**旧口径**） | `DEVNULL` | ❌ **恒 0** |

⇒ **"统一"的真对象不是两个文件，是三套端口探测＋两套健康判据**；卷宗的两案都只动第 3 行那一格。

```
$ rg -n "find_port|find_free_port|is_health_ready|smoke_boot|8599" --glob '!docs/**' .   （择要，全量见本档命令）
README.md:72:python scripts/smoke_boot.py            ← smoke_boot 唯一调用方
start.bat:26:for /f %%p in ('"%PYTHON%" scripts\find_port.py') do set "PORT=%%p"
scripts/find_port.py:6 / :20                          ← 定义与 __main__ 出口
launcher.pyw:81 / :134 / :277                         ← 第二套探测＋第二套判据（自带，未复用）
scripts/smoke_boot.py:12 / :24                        ← 8599 两处字面量
tests/test_find_port.py:26 / :133-151                 ← 钉 find_port 签名(:6)、出口(:16)、start.bat 接线(:26)
tests/test_launcher.py:74-82 / :126-130               ← 钉 is_health_ready 与 start_streamlit_backend(port)
```

## 二、撞口复现（完成标准②的"复现推演"，三探针实跑支撑）

### 1. 静态链（先给"应当发生什么"）

CLI 显式传 `--server.port` ⇒ `config.parse_config_options` 走 `config.py:2811-2812 _set_option(opt_name, opt_val, _DEFINED_BY_FLAG)` ⇒
`starlette_server.py:87-89 _is_port_manually_set()` 为 True ⇒ 撞口时 **`starlette_server.py:310-312`（及同步路径 `:504-506`）**：`_LOGGER.error("Port %s is not available"); sys.exit(1)`
⇒ **不换口、子进程自杀**（`MAX_PORT_SEARCH_RETRIES=100` 的扫段逻辑在"手工给口"时被短路）。Linux 形态下这就是全部故事。

### 2. 🔴 Windows 实测把上面那条推翻了：子进程**不会**自杀，它"起成功"了

```
$ PYTHONIOENCODING=utf-8 timeout 180 python tmp/l924-27/probe_collide2.py     （一次性子进程，占用者 20 s TTL，退出前复验端口释放）
[0] 外来假服务占住 8599；探针前是否空闲＝False（False 即占用生效）
[1] 子进程状态：仍在运行（等待 2.5s）
    child.log 关键行： ['2026-09-25 03:55:41.508 Uvicorn server started on 127.0.0.1:8599', 'URL: http://127.0.0.1:8599']
    [2] 双监听期间: status=200 body='FOREIGN-HOLDER' ⇒ smoke_boot 会判 ready=True ／ 实际应答者＝外来假服务
[3] 子进程已终止 rc=1
[4] 子进程退出后: status=200 body='FOREIGN-HOLDER' ⇒ smoke_boot 会判 ready=True ／ 实际应答者＝外来假服务
[6] 探针结束 8599 空闲：True
```
根因（源码级）：`uvicorn/config.py:582-585` 在 bind 前 `sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)`；Windows 语义下 `SO_REUSEADDR` **允许绑到已被占用的口**（正为防这个才有 `SO_EXCLUSIVEADDRUSE`），于是 `:586-588` 的 `except OSError → sys.exit(STARTUP_FAILURE)` 分支**不触发**，streamlit 的 `_is_port_manually_set → sys.exit(1)` 也就永远走不到。
⇒ 本机（Windows 11 / streamlit 1.58.0 / uvicorn 0.50.0 / Python 3.12.9 / `errno.EADDRINUSE=10048`）实测形态＝**两个监听者同口共存，先 bind 者继续收连接**。
对照：普通 `socket.bind`（不带 REUSEADDR）在占用时确实失败——`[0]` 行 `free(8599)==False` 就是这条的读数，也正是 `find_port` 赖以工作的性质。

### 3. 三探针分工与读数（逐条可复算）

| 探针 | 证明什么 | 关键读数 |
|---|---|---|
| `tmp/l924-27/probe_port.py`（**零 streamlit**，纯表达式） | smoke_boot 的判定式对"外来服务"也给绿；find_port 的跳过/退出语义 | `[P1] ready=True (status=200) ⇒ 假绿成立`；`[P2a] find_port(8599,8599) → SystemExit('no free port in 8599-8599')`；`[P2b] find_port(8599,8603) → 8600`；rc=0 |
| `tmp/l924-27/probe_collide.py`（真 streamlit＋占位，45 s 超时） | 撞口时子进程**不死**（推翻 §二-1 的静态预期） | `[2] 子进程退出码 = TIMEOUT>45s，terminate 后 returncode=1`（＝它一直活着）；`[3] Uvicorn server started on 127.0.0.1:8599`；rc=0 |
| `tmp/l924-27/probe_collide2.py`（同上＋分辨应答者） | 撞口时**谁在应答**＝假绿的确证 | 见 §二-2 全文 |
| `tmp/l924-27/probe_health.py`（无撞口基线） | 判据收紧后仍可验收；给 ready 时延基线 | `[A] (200, 'ok', 2) 首帧 ready 用时 1.9s`（第 2 轮 ×0.2 s 即中）；`[D] 探针结束 8733 空闲：True`；rc=0 |

### 4. 撞口后果矩阵（现实现 vs 修好之后）

| 形态 | 现实现读数 | 后果 | 被哪一处修掉 |
|---|---|---|---|
| 8599 空闲（常态） | `health ready: True (~2-3 s)`，rc=0 | 正确 | — |
| 8599 被**非 HTTP** 程序占（数据库/游戏） | bind 被 uvicorn 的 REUSEADDR 绕过 ⇒ 子进程活着；urlopen 连到对方，多半连接被拒/异常 ⇒ 轮询满 150 次 ⇒ `health ready: False (30.xs)`，**rc 仍 0** | 误报红＋自动化假绿，30 s 白等，诊断被 DEVNULL 吞 | 占用检测（A/B 案）＋退出码（§三-3） |
| 8599 被**另一路 smoke_boot**占（并发执行班，**本波 8 路同跑时最可能**） | 先起者应答 200 `ok` ⇒ 后起者 `health ready: True` | 🔴 **纯假绿**：后起者那次冒烟根本没验自己的 app.py | 占用检测 ＋ 应答身份校验（body=='ok' 只挡"非 streamlit"，挡不了"别人的 streamlit"⇒ 必须靠端口不共用） |
| 8599 被**任意会应答 200 的服务**占 | 探针 2 实读 `status=200 body='FOREIGN-HOLDER'` ⇒ `ready=True` | 🔴 纯假绿 | body 身份校验 ＋ 占用检测 |
| 真 app.py 起不来（导入炸） | `proc.poll()` 非 None ⇒ 打 `streamlit exited early rc=1`，ready=False，**rc 仍 0** | 人看得见、机器看不见 | 退出码 |

## 三、两案对照（完成标准②：各案"改哪个文件几行"）

### 1. A 案 —— smoke_boot 改调 `find_port` 取空闲口（健康 URL 同步参数化）

| 面 | 内容 |
|---|---|
| 改动 | `scripts/smoke_boot.py` **1 个文件，约 +6/−3 行**：`:8` 后加 2 行 import＋1 行 `port = find_port()`；`:12` `"8599"` → `str(port)`；`:24` URL 改 f-string。`find_port.py`／`start.bat` **零改动** |
| import 形态（已实测可用，两种都行） | `from find_port import find_port`（同目录，`python scripts/smoke_boot.py` 时 `sys.path[0]=scripts/`）与 `from scripts.find_port import find_port`（PEP 420 命名空间包，`tests/test_find_port.py:26` 用的是后者形态）—— 两条本机均返回端口成功 |
| 连带语义 | 8511-8530 全占时 `find_port` 走 `sys.exit("no free port in 8511-8530")` ⇒ smoke_boot 输出里**不再出现 `health ready:` 行**、rc=1。这是"改文案前先改契约"，需在验收口径里同步 |
| 🔴 真风险（**卷宗未列**） | 沿用默认段 ⇒ 冒烟与**主服务共用 8511-8530 池**：① 冒烟会稳定抢走 8511（未起主服务时），与桌面/开发入口抢池；② `find_port` 是 bind→**close**→返回（`tests/test_find_port.py:80-92` 专门钉这条语义），存在"取口—真 bind"之间的竞态窗口，两路并发可同时取到同口 —— Windows 上后果不是报错而是 §二-2 的**双监听假绿**。并发执行班下这条被 A 案从理论变现实 |
| 回归门禁 | `tests/test_find_port.py`（现值 **8 passed**）钉的是 `find_port.py:6/:16` 与 `start.bat:26`，A 案不碰 ⇒ 不红；`tests/test_scripts.py`（现值 **22 passed**）不引用 smoke_boot ⇒ 不红。**A 案零测试churn**，代价是零测试覆盖也依旧（该文件今天无人钉） |

### 2. B 案 —— 保持 8599，前置 socket 占用探测，占用即换

| 面 | 内容 |
|---|---|
| 改动 | `scripts/smoke_boot.py` **1 个文件，约 +10/−2 行**：新增 8 行探测（`for p in range(8599, 8609): bind 成功即用`，或 `from launcher` 复用——⚠ `launcher.pyw` 是 `.pyw`，import 需 `importlib` 特殊处理，实际会写成自带的小函数）＋ `:12`/`:24` 两处参数化 |
| 保住的好性质 | 冒烟口与主服务 8511-8530 **继续不相交**（§二 实测这是既有的**优点**，不是缺陷） |
| 代价 | 端口探测逻辑**第三次复制**（`find_port.py:6-16`、`launcher.pyw:81-90`、新代码）⇒ 与 A 案的"统一"目标相反；且自带探测同样有 bind→close 竞态窗口 |
| 回归门禁 | 同 A 案：零测试 churn、零测试覆盖 |

### 3. 🔴 两案都不解决的第 3、4 处缺陷（必须单列，否则修完仍会假绿）

| # | 缺陷 | 修法（各 ≈1-3 行，全在 `smoke_boot.py`） | 依据 |
|---|---|---|---|
| C1 | 判据 `r.status < 500` ⇒ 404/200 外来应答都算 ready | 收紧为 `r.status == 200 and body.strip() == "ok"` | `launcher.pyw:139` 已单独修过同款（注释点名"<500 会把 404 当成功"）；streamlit 侧 `runtime.py:567-575` 就绪定值 `("ok")`、未就绪 503/`unavailable`（探针 3 实读 `(200,'ok')`） |
| C2 | 失败无退出码（rc 恒 0） | 结尾 `sys.exit(0 if ready else 1)` | `rg "sys.exit\|raise\|exit\(" scripts/smoke_boot.py` 空 ⇒ 现无出口；README 的验证块是顺序人读，rc 一旦有意义才谈得上接 CI |
| C3 | 子进程诊断被 `DEVNULL` 吞 | `stdout=open(ROOT/"logs"/"smoke_boot.log","ab")`（照 `launcher.pyw:121-129` 的现成写法） | 探针 2 的 `[1] child.log 关键行` 能读出 `Uvicorn server started on ...:8599` —— 有日志才可归因 |
| C4 | 不传 `--server.address 127.0.0.1`，靠 `.streamlit/config.toml` 兜回环 | 显式加该参数（另 1 行） | 另两条入口都显式传（`start.bat:27`、`launcher.pyw:112`）；属最小暴露面口径，不碰鉴权/隐私数值 |

### 4. 推荐案（B′＝两案合流；🔴 建议稿，未选案）

> 取向：**取 A 案的"复用同一实现"＋ B 案的"独立端口段"**，再把 C1-C4 一并收掉。全部改动在 `scripts/smoke_boot.py` 一个文件，估 **约 +16/−6 行**（38 行 → 约 48 行）。

1. 冒烟**独占端口段** `8599-8613`，用 `find_port(8599, 8613)` 取口（复用实现 ⇒ 不再第三套；独立段 ⇒ 不抢主服务池、消掉 A 案真风险①）；全段占用则打印 `health ready: False (no free port in 8599-8613)` 后 `sys.exit(1)`（统一输出契约，消 A 案文案漂移）。
2. 健康 URL 与命令行端口**同一个 `port` 变量**（两处 8599 字面量归一，`rg -c 8599 scripts/smoke_boot.py` 应读 0 或 1 —— 若做判据，注意"注释里也别留该字面串"这条同族坑）。
3. C1 判据收紧：`status == 200 and body == "ok"`。
4. C2 退出码 ＋ C3 子进程日志 ＋ C4 显式 `--server.address 127.0.0.1`。
5. 残留（明说不粉饰）：bind→close→真 bind 的**竞态窗口不消失**（A/B/B′ 都有）。窗口内两路同时取到同口，Windows 下仍是双监听共存；唯一彻底解法是**持有 socket 直到子进程起来**（＝改 `find_port` 语义，会撞 `tests/test_find_port.py:80-92` 那条专门钉"函数不能把口泄漏出去"的断言 ⇒ 属判据冲突，须人工裁决）。B′ 用独立段把碰撞概率从"与主服务同池"降到"两路冒烟同时开跑"，不声称消除。
6. 配套建议（另单）：新增 `tests/test_smoke_boot.py`（今天该文件 **tests 零引用**），钉：端口单源、`no free port` 时 rc!=0、外来 200 非 `ok` body 不判 ready。B′ 若不配桩，仍是"文本契约"。

## 四、推荐案验收口径（完成标准③）＋ 零改动自证（完成标准④）

### 1. 正向：真跑一次（**本单未执行**，交人工/落码班）

```powershell
# 仓库根 D:\code\learning-system；会真的起 app.py（约数秒至数十秒），故本只读单不跑
$env:PYTHONIOENCODING="utf-8"
python scripts/smoke_boot.py        ; echo "exit=$LASTEXITCODE"     # 期望：health ready: True (<N>s)  且 exit=0
```
- 期望输出字面：修复后仍为 `health ready: True (%.1fs)`（现文案；卷宗写的"输出 ready: True"少一个 `health ` 前缀，按磁盘字面为准）。
- 时延基线：探针 3 用 3 行 tiny_app 实测首帧 ready **1.9 s**（第 2 轮 ×0.2 s）；`app.py` 全量导入必然更慢 ⇒ 建议阈值 **45 s** 内 `True`，但**阈值须由落码班用真 app.py 跑一次定**（本单无权跑）。
- 轮询预算：`:19` 的 `150 × 0.2 s ≈ 30 s` 上限**小于**建议阈值 ⇒ 判据落地时要一并说明"轮询预算是否够 app.py"，否则会出现"其实再等 3 秒就好"的新假红。这条也只有真跑一次才定得了。

### 2. 反向：撞口路径（一次性、可复算、**不起 app.py**）

```bash
cd /d/code/learning-system && PYTHONIOENCODING=utf-8 timeout 180 python tmp/l924-27/probe_collide2.py ; echo "rc=$?"
```
- 修复前实读（本档 §二-2）：双监听、`status=200 body='FOREIGN-HOLDER'`、按现判据 ready=True。
- 修复后（B′）期望：子进程换到 8600、外来 200 被 body 校验拒判、`health ready: True` 由**自己的**实例给出，或探测失败时 rc=1 且 `logs/smoke_boot.log` 有可归因日志。

### 3. 门禁面（落码后逐字跑）

```bash
cd /d/code/learning-system && PYTHONIOENCODING=utf-8 python -m pytest tests/test_find_port.py tests/test_scripts.py -q
```
本单（零改动）现值：**8 passed / 22 passed，rc=0**。另建议加跑 `tests/test_launcher.py`（钉 `is_health_ready`/`start_streamlit_backend`，B′ 若顺手抽公共判据就会碰到它）。本单未跑全量套件（并行默认约束，卷宗无点名）。

### 4. 零改动自证

```bash
cd /d/code/learning-system && git diff --stat -- scripts/ ; git status --porcelain -- scripts/ launcher.pyw start.bat
```
实测**均空输出**（`scripts/`、`launcher.pyw`、`start.bat` 零 diff）；在盘产物只有本档＋索引件 2 行＋gitignore 的 `tmp/l924-27/` 四枚探针与两枚 child 日志。

## 五、遗留问题（交主班／人工）

1. **三案未选**（A 复用默认段 / B 自带探测 / B′ 复用实现＋独立段）＋ **C1-C4 是否随单收**（拆开则至少 C1、C2 与端口案同批，否则修完仍可假绿）。
2. **bind→close 竞态是否接受**：彻底解法与 `tests/test_find_port.py:80-92` 的既有断言直接冲突 ⇒ 判据冲突类，必须人工裁决，不属执行手授权。
3. **`smoke_boot.py` 不传 `--server.address`**（靠 `.streamlit/config.toml` 的 `address="127.0.0.1"` 兜）：属最小暴露面口径，相邻"凭据/隐私"红线域 ⇒ 只登记，不动。
4. **真 app.py 的正向验收未跑**（波次纪律禁本类只读单起服务）：`<N>s` 阈值与"150×0.2 s 轮询预算够不够 app.py"两个数都**空缺**，须落码班实跑一次补。
5. **smoke_boot 在 tests/ 零引用、无 CI**（无 `.github/`）⇒ 本档所有"rc/退出码"结论都还是**静态＋探针推演**，没有现网自动化消费它；§三-4 第 6 条的桩建议是否立项，交主班排单。
6. 卷宗产出面与本单实际：卷宗写"含 scripts/ 下 smoke_boot/find_port/start.bat 三方"，`start.bat` 实在**仓库根**不在 `scripts/` 下；且真面是四方两入口（§一）——按磁盘实况交付，未据此判 failed。
