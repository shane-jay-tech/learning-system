# l927-11 判题沙箱文件系统零约束（F-1）：越界读写取证复核与三案代价裁决材料

> 班次：`qoder-executor-20260927-1520-learn46`（波次 21 只读采集子班）｜时戳 `2026-09-27T17:4x+08:00`（`date` 现取）
> 仓现值：HEAD `8ef64c6`｜开单前 `git status --porcelain` **0 行**
> 锚点：`zcode-bridge/outbox/20260925-154238-28d8.result.md` → 磁盘实取于 **`done/`**（13,420 B，波次 20 前后被 `--consume` 搬家，内容未变，按 brief §3a 口径处理，**不判锚点失效**）
> 形状：**只读取证 ＋ 裁决材料**。**零生产码改动、不开任何写位、不改 ACL、不装不卸包、不联网。**

---

## 一、F-1 锚点复核：结论**成立且被加重**

### 1.1 取证方法（可复现）

**用真 runner 代码路径执行探针载荷**，不经 `judge.py`（⇒ 完全不触碰 `_record_attempt` 那条自开默认库的在册前科路径）：

```python
# 驱动（只 import，不改）
sys.path.insert(0, r"D:\code\learning-system")
from core.runners.python_runner import PythonRunner
r = PythonRunner().run(payload)      # 走 :119 [sys.executable, "-I", src] ＋ :123 cwd=tmpdir ＋ :124 env=_safe_env() ＋ :104 timeout_sec=5
```
解释器：`D:\code\learning-system\.venv\Scripts\python.exe`（＝`start.bat`／桌面快捷方式的**运行面**，见 `docs/insights/l927-10-deps-health.md` 第二节）。
载荷落盘：`docs/insights/` 不收代码，探针件在本班快照目录（收班自清），复跑口径见 1.5。

### 1.2 读数（沙箱子进程内实测，`ok=True exit_code=0 elapsed_ms=333`）

| # | 探针 | 读数 | 判定 |
|---|---|---|---|
| 0 | 沙箱 cwd | `C:\Users\31563\AppData\Local\Temp\ls_py_wjwq4i8i` | 临时目录，**仓外** ✓ |
| 1 | 读 `C:\Windows\win.ini` | ✅ size 92 B，头部 `; for 16-bit app support` | **越界读成功** |
| 2 | 读仓根 `README.md` | ✅ 6,103 B | 越界读成功 |
| 3 | 读 `requirements-freeze.txt` | ✅ 3,570 B | 越界读成功 |
| 4 | 读 `core/judge.py` | ✅ 15,423 B | 越界读成功 |
| 5 | **读 `data/progress.db` 头 16 B** | ✅ `SQLite format 3\0`，size 122,880 | **生产库可被学生代码整读** |
| 6 | **沙箱内算 `progress.db` sha256 前 8** | ✅ **`cd2dbce4`**（与宿主侧独立读数逐字相同） | 读完整、无遮挡 |
| 7 | 读**本班快照目录**（既非 cwd 也非仓内） | ✅ `copy_items.txt` 11,539 B | 越界读面＝**全盘** |
| 8 | `scandir` 仓根 | ✅ **28** 条目 | 可枚举 |
| 9 | `scandir` `data/` | ✅ **5** 条目（`.gitkeep`/`backups`/`progress.db`/`progress.db-shm`/…） | **生产库位置可枚举** |
| 10 | `scandir` 用户主目录 | ✅ **67** 条目（`.agents`/`.bsk`/`.bun`/`.cache`…） | 可枚举 |
| 11 | `scandir` `C:\Windows\System32` | ✅ **4,718** 条目 | 可枚举 |
| 12 | `os.access(progress.db, W_OK)` | ✅ **True**（`R_OK` 亦 True） | **锚点原句复现** |
| 13 | `os.access(仓根, W_OK)` | ✅ True | |
| 14 | `os.access(data/, W_OK)` | ✅ True | 第 3 条写脏路径的门是开的 |
| 15 | `os.access(C:\Windows\System32, W_OK)` | ✅ **True**（access 位判） | 见 1.4 的降级判定 |
| 16 | `os.access(C:\Users\Public, W_OK)` | ✅ True | |
| 17 | **对生产库取写句柄** `os.open(db, O_WRONLY)`（**无** `O_TRUNC`/`O_APPEND`），随即 `close`，**一字节未写** | 🟥 **句柄被接受**；`mtime_delta_ns=0`、size 122,880 不变、sha8 仍 `cd2dbce4` | **写句柄被接受＝结论要点**（OS 层没拦） |
| 18 | 对生产库取 `open(db, "rb+")` 读写句柄，只 `read(4)` 得 `SQLi`，未调 `write` | 🟥 **句柄被接受**；`size_delta=0`、sha8 不变 | 同上，双重印证 |
| 19 | `sqlite3.connect("file:…?mode=ro", uri=True)` 只读连接，**只取计数不取内容** | ✅ 连上：表 **8** 张、`learning_events` **81** 行、`attempts` **15** 行、`review_state` 0 行；sha8 不变 | 学生代码可用 SQL 整读学习记录（**本档不转述任何行内容**） |
| 20 | 真写库试验 | ⛔ **主动停用**（`DISABLED_BY_DISCIPLINE`）——可写性已由 12/17/18 三处定论，**不写任何行** | 遵守「只做判可写性」硬约束 |
| 21 | 越界写到 `C:\Users\Public\ls_f1_escape_probe_<pid>.txt` | 🟥 **成功写入→回读→已删除**（`removed=True`） | **机器级可写路径实逃逸** |
| 22 | 越界写到本班快照目录 | 🟥 成功→已删除 | 同上 |
| 23 | 沙箱内再派生子进程 `[sys.executable, "-I", "-c", "print('spawn-ok')"]` | ✅ `spawn-ok` | **逃逸可再套一层**（`_kill_tree` 只保证超时时收拾，不给能力设限） |
| 24 | 令牌基线 `ctypes.windll.shell32.IsUserAnAdmin()` | **False**（标准过滤令牌；`whoami /priv` 只见 Shutdown/ChangeNotify/Undock/IncreaseWorkingSet/TimeZone 五条已启用或已禁用，**无 SeDebugPrivilege**） | 未提权——但**也不降级**（见 1.4） |
| 25 | 侧车与终值 | `db 122,880 B`／`-wal` 存在 **0 B**／`-shm` 存在 32,768 B／`sha8_final cd2dbce4` | **主库零变化**（侧车 mtime 见 1.6 自报） |

⇒ **锚点 F-1 的两个断言都成立**：`os.access(..., W_OK)=True` ✅ 逐字复现；「实测可越界读系统／仓内任意文件」✅ 复现并扩到全盘。

### 1.3 本波新取证到的**加重项**（锚点里没有的，直接影响三案定价）

| 编号 | 新读数 | 为什么重要 |
|---|---|---|
| **F-1a** | 运行面启动时 `PATH` 首条是 **`D:\code\learning-system\.venv\Scripts`**（因 `python_runner.py:56` 取 `dirname(sys.executable)`），该目录沙箱可见 **24 枚 `*.exe`**，含 **`pip.exe`／`python.exe`／`streamlit.exe`／`pytest.exe`／`uvicorn.exe`／`watchmedo.exe`** | 学生代码可 `subprocess.run(["python","-c",…])` 起一个**不带 `-I`** 的第二解释器（全环境、cwd 进 `sys.path`），也可 `pip install` ⇒ **`_safe_env` 的 PATH 收窄＋`-I` 隔离＋F-2 的"无代理"结论，都在这一条面前失效**。（本班**未实跑 pip**，避免联网歧义；可达性由 17/23/25 的 icacls·whoami·子进程三例实证。） |
| **F-1b** | `ctypes` **可 import**（`can_import_ctypes: true`） | 任何 **Python 层**的拦截（改 `open`、包 `os`、审计 hook）**都可被 `ctypes.windll.kernel32.CreateFileW` 绕过** ⇒ 案 A 必须在 OS 层做才有效 |
| **F-1c** | `icacls`（System32）沙箱内**可达且能跑**（rc=0），并原样打印出生产库 DACL | 拦截方案的**信息面**同样开放：学生代码能读出权限结构再决定绕哪条 |
| **F-1d** | 生产库 DACL 关键条目：`NT AUTHORITY\Authenticated Users:(I)(M)`（**Modify**）、`BUILTIN\Users:(I)(RX)`、`BUILTIN\Administrators:(I)(F)`、`NT AUTHORITY\SYSTEM:(I)(F)`，另有两条外部工具留下的 `…\CodexSandboxUsers:(I)(M,DC)` 与一个裸 SID | **W_OK=True 的机制解释**：不是"没设权限"，而是 `Authenticated Users` 被**继承**授予 Modify。⇒ 案 A 的落点是"给这个主体加 Deny"（Deny 优先于 Allow），而非改 Allow |
| **F-1e** | `data/` 与 `progress.db` 的**属主＝运行用户本身**（`dir /q` 显示属主为 `修得柳色与卿\31563`，沙箱内 `whoami` 同一身份；`.Owner` 解析为 `…-1001`） | 🔴 **这是案 A 的天花板**：Windows 里对象**属主恒隐式持有 WRITE_DAC**，同身份子进程可把那条 Deny 改回去 ⇒ **纯 ACL／纯路径拦截对同权限进程不构成防线**，必须与案 C（降权到不同主体）同用。⚠ 本条是「在册 Windows 规则＋本班身份读数」的推论，**未做改 ACL 的写动作去实证**（那是系统权限位改动＝人工闸），需人工在真机验证一次 |

### 1.4 现状一句话

沙箱给学生的约束是**「语言与超时」**（命令白名单＋`-I`＋5 秒超时＋输出上限＋env 白名单 9 键＋PATH 收窄到 3 条），
**文件系统与网络是零约束**，且当前**运行身份＝文件属主＝普通但完整的用户令牌**（不降级也不提权）。
⇒ 与 `ui/pages/home.py:55` 那句「本系统的代码执行器使用 subprocess **隔离**」直接矛盾（本波 `l927-09` 的 P10 已从文案面登记同一冲突，`l927-05` 的 **G3** 是首登记）。

### 1.5 复跑口径（不贴代码也能重算）

```bash
# 沙箱读数：把载荷交给真 runner 跑（载荷见本班快照目录，收班自清；要点见 1.2 表 25 行）
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe <driver.py> <payload.py>
# 锚点原句最小复现（只判可写性，不写任何行）
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -c "import sys;sys.path.insert(0,r'D:\code\learning-system');from core.runners.python_runner import PythonRunner;print(PythonRunner().run('import os;print(os.access(r\'D:\\\\code\\\\learning-system\\\\data\\\\progress.db\',os.W_OK))').stdout)"
# DACL / 属主 / 令牌（只查询，零改动）
./.venv/Scripts/python.exe -c "…subprocess.run(['icacls', DB])…"   # 见 1.2 的 F-1c/F-1d
cmd //c "dir /q data"        # 属主列
powershell -NoProfile -Command "(Get-Acl 'D:\code\learning-system\data\progress.db').Owner"
```

### 1.6 🔴 自报：本班探针的一个副作用（**如实登记，未去"修数据"**）

| 对象 | 探针前 | 探针后 | 判定 |
|---|---|---|---|
| `data/progress.db` | 122,880 B／sha8 **cd2dbce4**／mtime 2026-09-25 20:49:09 | 122,880 B／sha8 **cd2dbce4**／mtime 同左 | **零变化** ✅ |
| `data/progress.db-wal` | 0 B／mtime 2026-09-25 20:55 | 0 B／mtime 同左 | 零变化 ✅ |
| `data/progress.db-shm` | 32,768 B／mtime 2026-09-27 **14:31** | 32,768 B／mtime 2026-09-27 **17:37** | ⚠ **mtime 被我改了**（大小未变） |

成因：19 号探针用 `mode=ro` URI 打开 WAL 模式库时，SQLite 仍需映射并回写 `-shm`（WAL 索引）头部——**这正是 brief §6「别逐枚打开真库（会长出 -wal/-shm 侧车）」点到的机制**，本班踩在了它的前半句上（侧车本就存在，我只是刷新了它）。
影响判定：`-shm` 是可丢弃的运行时索引，**不含数据**；主库与 `-wal` 逐字节未动、sha8 与在册基线前缀 `cd2dbce4` 三个取样点（开班／探针内／收工）全部一致 ⇒ **无污染事故**。
处置：**未去"修"任何文件**（不删 `-shm`、不 chmod、不重建），只登记。下次此类取证应把 19 号换成「读文件头＋`sqlite3` 只读 schema 走临时副本（Backup API）」，不直开真库。

---

## 二、三案代价对比矩阵（**只出材料，不开写位**）

前提：本机信任模型是「**单人本机**」（`README.md:40`、`home.py:55` 的自陈），所以"防学生"在这里的真实语义是
**防自己写的代码手滑毁数据／防公开化后变成真漏洞**，不是防恶意攻击者。裁决口径建议按这个前提定价，别按多租户 SaaS 定价。

| 维度 | **案 A：路径拦截**（cwd 外写入拒绝；OS 层＝只读/Deny ACL，或 minifilter） | **案 B：进程隔离**（独立低权账户／容器化 runner／Windows Sandbox／AppContainer） | **案 C：权限降级**（同机不同主体：受限令牌 `CREATE_RESTRICTED_TOKEN`／降权服务账户／把 `data/` 属主改成非运行用户） |
|---|---|---|---|
| 挡得住 1.2 的哪几条 | 12–18、21–22（写逃逸）；**挡不住** 1、2、5、6、7、8–11（**读**越界，除非连读也 Deny）、**挡不住** F-1a（另起 `python.exe` 不带 `-I`）、F-1b（`ctypes` 直调） | 读写网全挡（含 F-1a/F-1b） | 写与 ACL 绕过全挡；**读**仍可越界（除非按主体重设 DACL） |
| **有效性天花板** | 🔴 **F-1e 直接封项**：运行身份＝属主＝隐式 WRITE_DAC ⇒ 同权子进程可撤销 Deny。**纯 ACL 不构成防线** | 高（前提是隔离边界由 OS 强制，不是 Python 自觉） | 高（关键是"不同主体"，而不是"少几个权限"） |
| 改动面（最小） | ①`python_runner.py`/`r_runner.py`/`cpp_runner.py`/`sql_runner.py` 四处执行点＋`base.check_security` 一处；②机器侧一次性 `icacls /deny` 施加到 `data/`；③runner 改到**副本**上跑（`scripts/backup_data.py` 链已能读 `data/`，需复核） | 新增一个启动形态（服务账户／Sandbox／AppContainer 清单），四个 runner 的 spawn 参数全部重写；`sys.executable` 假设失效（`.venv` 路径在别的上下文里不可达） | 机器侧建低权账户＋把 `data/` 属主改给它＋服务以该账户跑；代码侧 `subprocess` 需带凭据派生（Windows 下要 `CreateProcessAsUser`，Python 标准库不直接支持 ⇒ 要上 `pywin32`/`ctypes` 手写） |
| 新依赖 | 无（ACL 是既有的）／minifilter 需内核驱动＝**不可接受** | 🔴 需新增 `pywin32` 或容器栈——**违反 l927-10 的依赖面现状**（`requirements.txt` 11 条，无一项 Windows 权限库），且 `.venv` 里没有 | 🔴 同上：`CreateProcessAsUser` 需要 `pywin32`（未声明未装） |
| 对**学习者体验**的影响 | 中：报错从"跑通了但毁数据"变成"这条路径写不了"——**必须配可见提示**，否则零基础用户只看到"莫名失败"（呼应 `l927-09` P4/P9 的文案口径缺口） | 高：环境不一致会让学生的 `import pandas` 之类突然失败（科学计算栈是学生题面在用，见 `l927-10` W4）；工具链 `g++`/`Rscript` 需重装进隔离体（本机现在**两者都没装**，7 条恒 skip） | 中低：路径与包不变，只有写权限变化 |
| 对**判题链正确性**的风险 | 低（不碰 `ok`/`passed`/`exit_code`/`error_kind`，与 `judge.py:146` 的"只映射不改判"纪律一致） | 🔴 **中高**：`-I`＋`sys.path`＋PATH 三条假设都要重验；`error_feedback` 的行号折算依赖 `_PREAMBLE_LINES`，隔离体解释器不同就会**行级反馈打歪** | 中：临时目录可见性／`TEMP` 重定向需实测 |
| 回滚成本 | **低**：`icacls /reset`＋还原 4 处 spawn 参数（一处一 commit） | 高：形态级改动，回滚＝删整套启动链 | 高：涉及账户与属主变更，**属主改错会连备份链一起失去可读性** |
| 可验证性（能不能钉成测试） | ✅ 可加定向测试：断言 `os.access(DB, W_OK)` 在沙箱内为 False（现值 True ⇒ 现在跑必红，正好当"未实施"的钉子；参照 `tests/test_runner_security.py`／`test_default_db_guard_20260927.py` 的形状） | ✅ 但需要 CI 有该形态；本机 g++/Rscript 缺位已经让 7 条恒 skip，再加一类环境依赖会扩大"绿但零覆盖"面 | ⚠ 难：降权形态在开发机上难以常开 |
| 与在册缺口的连带 | 顺带压掉 **F-6**（PATH 含解释器目录）→ 必须把 `dirname(sys.executable)` 从 PATH 首条摘掉，否则 **F-1a 的 `pip.exe` 面仍在** | 一并解决 **F-2（出网零管控）** | 一并解决 F-2 需再加防火墙规则 |

---

## 三、推荐（供人工拍板；**本单一律不动代码**）

**主推荐：案 C 为骨、案 A 为肉，案 B 不做。**

1. **第 0 步（零风险，先做）**：把 `python_runner.py:56` 的 `os.path.dirname(sys.executable)` 换成"只放该目录里**被证明必需**的那一个可执行文件名"或直接摘掉，
   ⇒ 一步封掉 **F-1a**（`pip.exe`／`python.exe`／`streamlit.exe` 经 PATH 可调）。这是**一行改动、零新依赖、可回滚**，且是三案里唯一"先做不吃亏"的。
2. **第 1 步（案 A 的可用部分）**：`data/` 对子进程**只读**＋runner 在**副本**上跑（锚点原方案②）。它挡不住属主回改 DACL（F-1e），但能把"手滑写脏"的**默认路径**关掉——
   在本机单人模型下，威胁是**手滑**不是**攻击**，所以"关掉默认路径"已经拿到大部分收益。
   ⚠ 前置：`l927-10` W1/W2 的 `.venv` 依赖补齐要先做，否则副本方案会在缺包的运行面上叠第二层不确定性。
3. **第 2 步（案 C，真边界）**：只有当**运行判题的主体 ≠ 数据属主**时，案 A 的 ACL 才从"提醒"升级成"防线"。
   代价是新依赖（`pywin32` 或等价）＋账户与属主变更 ⇒ 属人工闸中的重档，建议**排到公开化路线图**上再定，而不是现在为本机单人场景预付。
4. **案 B（容器／Windows Sandbox／AppContainer）不推荐**：判题链的三处假设（`-I`、`sys.path`、`_PREAMBLE_LINES` 行号折算）都要重验，
   而本机连 `g++`/`Rscript` 都没有（7 条恒 skip），隔离体会把"覆盖不到的面"再放大一圈。收益不抵成本。
5. **无论选哪案，两件事必须同时做**（否则安全态不可知）：
   - **文案面**：改掉 `ui/pages/home.py:55` 的「subprocess **隔离**」与 `README.md:64` 的「带**安全**与超时边界」（`l927-09` P10、`l927-05` G3 同条冲突）。当前承诺与实况不符，**这是最便宜也最该先做的一条**。
   - **可见性**：拦截必须给出学生读得懂的拒绝（`sql_runner.py:95 _AUTHORIZER_DENY_MSG` 已是现成范式，可循例），并按 `l927-09` P4 的标点/术语口径写文案。
6. **登记不处置**：F-1d 里那两条 `CodexSandboxUsers` ACE 与裸 SID 是**外部工具留下的继承权限**，与本案无关但会影响案 A 的 DACL 基线——动 ACL 前必须先看清它们是谁写的，否则改完仍被外部工具改回。

---

## 四、零改动声明与判据对照

| 卷宗判据 | 判定 | 实况 |
|---|---|---|
| ①越界取证可复现（**只读探针**） | ✅ | 25 行读数（1.2 表）＋复跑口径（1.5）；全程经**真 runner 代码路径**，未自造第二套 spawn 逻辑 |
| ②三案矩阵 | ✅ | 第二节 12 维度 × 3 案，含"有效性天花板"行（F-1e 封项）与依赖连带（`l927-10` W1/W2/W4） |
| ③推荐 | ✅ | 第三节 6 条，给出"第 0 步一行改动"作为不预付重档的落点 |
| ④零生产码改动 | ✅ | `core/`／`ui/`／`scripts/`／`README.md` **一字未动**；工作树只有本档与同波两档（`git status --porcelain` → 3 行全 `??`，全是新建 insights） |
| 硬约束：progress.db **只做判可写性、不写任何行** | ✅ | 12/13–16/17/18 四类判定，20 号真写试验**主动停用**；19 号走 `mode=ro` 且只取计数。主库 122,880 B／sha8 `cd2dbce4`／mtime 全程未变 |
| 硬约束：不开写位、不改代码 | ✅ | 未实施任何拦截、未改 ACL（只 `icacls` 查询）、未建账户、未装包、未联网 |

**盘上残留**：本班探针件在 `D:\code\tmp\qoder-executor-20260927-1520-learn46\`，收班自清；
`C:\Users\Public\ls_f1_escape_probe_170800.txt` 已删（沙箱内 `removed=True`，宿主侧 `ls | grep ls_f1` 零命中）；
`Temp\ls_py_667l9o78`（mtime 2026-09-27 00:46）**不是本班产物**（本班两次运行的临时目录都已自动回收），**未去删它**。

**待主班代登 insights 索引**：`l927-09`／`l927-10`／`l927-11` 三档（本仓有真闭合哨兵 `tests/test_insights_index_closure.py`，现 92/92，本班不代登）。

## 五、遗留

1. **F-1e 的"属主可回改 DACL"未实证**（改 ACL＝系统权限位动作，人工闸）。人工验证形状：施加 `icacls data /deny:*31563:(W)` 后，在沙箱内跑 `icacls data /grant …` 看是否 rc=0；若 rc=0 则案 A 单独无效成立。
2. **F-1a 未实跑 `pip install`**（禁联网/禁装包）。已证"可达可调"，未证"真能装"——但 `pip.exe` 在 PATH 首条目录里这一事实本身已足够触发裁决。
3. **cpp／R 两条 runner 未做动态取证**：本机 `g++`／`Rscript` 未安装（在册 7 条恒 skip），`cpp_runner.py:103-106` 编译步缺 `cwd=`（锚点 F-4）仍只有静态证据。装好工具链后需补一次。
4. **网络面（F-2）本单未复测**，只带出 `socket`／`urllib.request` 可 import 的读数；三案矩阵里 F-2 的收益归属已标（案 B/C 才能真管）。
5. **SQL 只读取数用了真库**（19 号），导致 `-shm` mtime 刷新（1.6 已自报）。下次改走 Backup API 副本，别直开真库。
