# 判题沙箱资源限额三缺设计材料：CPU／内存／进程数（l1004-01，16e3 D-2/D-3/D-4）

> 产线：执行班 l1004-01（2026-10-06）。**材料型，零生产码改动**；Job Object 落码属执行器行为变更，另派（任务书禁止事项明言）。
> 矿源：`zcode-bridge/done/20260925-120548-16e3.result.md` 遗留节（D-2/D-3/D-4 逐字见 §一）。
> 与 l927-11（F-1 文件系统零约束裁决）、l927-05（判题安全边界巡检 G 系）的差异：彼两单管**文件系统与安全边界**，本单专做**资源维度**（CPU 时间／内存／进程数）方案。

## §〇 限额单源钉子现值（TestCapsSingleSource 复核 ✓）

- 钉子：`tests/test_sandbox_limit_boundaries_20260925.py:357-373`——既有资源限额**只有一处定义**：`core/runners/python_runner.py` 的 `MAX_STDOUT_BYTES = 1_000_000`／`MAX_STDERR_BYTES = 100_000`／`_MAX_STDIN_BYTES = 1_000_000`，`r_runner`/`cpp_runner` 以 `from ...python_runner import MAX_STDOUT_BYTES, MAX_STDERR_BYTES` 复用；钉子同时钉值（`(1_000_000, 100_000, 1_000_000)`）。`sql_runner` 为进程内执行（无子进程），不在此钉面。
- 本单设计沿用该纪律：**三限额的常量若落地，单源落 `python_runner.py`（或上收 `core/runners/base.py`）＋TestCapsSingleSource 扩一条**，防四语言漂移。

## §一 三缺现值（16e3 行为实测逐字＋代码锚）

| 缺 | 16e3 实测 | 代码锚（本班复核） |
|---|---|---|
| **D-2 无 CPU 时间限额** | `wall 5.80 timed_out True exit None kind timeout elapsed_ms 5794` ⇒ 只有墙钟 5 秒（`PythonRunner.timeout_sec = 5`），单核满载 5 秒×并发数是真实成本上界 | `python_runner.py:106`（timeout_sec=5）；`cpp_runner.py:24-25`（总 10/编译 7）；POSIX 侧可 `RLIMIT_CPU`，本机 `nt` 无 `resource` 模块 ⇒ 需 Job Object |
| **D-3 无内存限额** | `rc 1 ... MemoryError`（隔离在子进程内）⇒ 失控分配靠 OS 兜底；多路并发时可能系统级提交失败 | `python_runner.py:144-159` Popen 无任何内存参数；byte caps 只限**管道回读**，不限进程堆 |
| **D-4 无进程数限额** | 派生 5 子进程全部成功；只有事后 `_kill_tree` 兜底；`taskkill` 失败时 `finally` 退化 `proc.kill()` ⇒ 可能残留孤儿（16e3 变异 m3 形态） | `python_runner.py:160-166`（Popen）＋ `_kill_tree`；进程数创建时不受阻 |

## §二 Windows Job Object 接入设计

### 2.1 API 形状（零新依赖，ctypes 直调 kernel32；不引 pywin32）

```
hJob = CreateJobObjectW(None, "ls_judge_<pid>")
# ① 内存（D-3）：SetInformationJobObject(hJob, JobObjectExtendedLimitInformation=9, &extLimit, sizeof)
#    JOBOBJECT_EXTENDED_LIMIT_PARAMETERS：
#      ProcessMemoryLimit = JOB_MEMORY_LIMIT（建议 512 MB 起，按语言 rollout 实测校准）
#      LimitFlags = JOB_OBJECT_LIMIT_PROCESS_MEMORY
# ② CPU 时间（D-2）：SetInformationJobObject(hJob, JobObjectExtendedLimitInformation=9, …)
#      LimitFlags |= JOB_OBJECT_LIMIT_JOB_TIME，JobTime = (LONGLONG)cpu_seconds * 10_000_000（100ns 单位）
#      或只读 accounting：QueryInformationJobObject(JobObjectBasicAccountingInformation=8) 轮询 TotalUserTime
# ③ 进程数（D-4）：LimitFlags |= JOB_OBJECT_LIMIT_ACTIVE_PROCESS，ActiveProcessLimit = 8（建议值）
# ④ 收尾：LimitFlags |= JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE（CloseHandle 即整树杀，替代/兜底 _kill_tree）
AssignProcessToJobObject(hJob, OpenProcess(PROCESS_SET_QUOTA|PROCESS_TERMINATE, FALSE, proc.pid))
```

- **挂点**：各 runner `subprocess.Popen(...)` 返回后、`communicate` 前一行（`python_runner.py:160` 与 `cpp_runner.py` 编译/运行两个 Popen 后）；Windows 上 `proc._handle` 可直接作 hProcess 免 OpenProcess。Job 由子进程**继承**，学生代码再派孙进程同在限额内（D-4 的正解）。POSIX 侧对称形状＝`resource.setrlimit(RLIMIT_CPU/RLIMIT_AS)`＋`preexec_fn`（本机不生效，留接口注释即可）。
- **轮询点**：现有 `communicate(timeout=墙钟)` 结构不动；Job 限额超限时进程被系统终止、`communicate` 提前返回，语义自然收敛进既有 try/except 骨架。

### 2.2 失败语义（三限额统一表）

| 失败 | 表现 | 映射（建议） |
|---|---|---|
| 内存超限（D-3） | 进程被 Job 终止，`proc.returncode` 非 0（Windows 无信号语义） | 新 `error_kind="memory_terminated"`（沿用 `error_feedback.classify` 词表单源纪律，加一档）；stderr 提示「超出内存限额」 |
| CPU 时间超限（D-2） | Job 终止，同上；与墙钟超时区分靠 `QueryInformationJobObject` accounting 读数 | `error_kind="cpu_time_terminated"`；墙钟 `timeout` 档保持不变（两档并存：墙钟先到＝老形态，CPU 先到＝新形态） |
| 进程数超限（D-4） | 学生代码内 `fork/spawn` 直接失败（子进程创建被拒） | 学生侧看到 `OSError/PermissionError`——**无需新错误档**，属正常业务失败 |
| Assign/CreateJob 失败 | API 返回 FALSE（如权限/句柄问题） | **fail-open 降级**：记 warning，回落现状（墙钟＋`_kill_tree`）；不因限额设施故障拒绝判题 |

### 2.3 按语言 rollout

| runner | rollout 档 | 说明 |
|---|---|---|
| `python_runner` | 第一批 | 本机主力语言；`-I` 隔离模式，Job 继承链干净 |
| `cpp_runner` | 第二批 | 编译（g++）与运行两个 Popen 各自 Assign 或同一 Job（建议同一 Job，编译 CPU 也受限） |
| `r_runner` | 第二批 | Rscript 同形；注意 16e3 前 r_runner 曾有 returncode≠0 的 R	setdll 噪声（python_runner.py:37 注释），rollout 时回归该场景 |
| `sql_runner` | **不适用** | 进程内 `executescript`，无子进程可 Assign；内存维度已有 authorizer 白名单函数面（`sql_runner.py:187/:189`），资源限额若需只能 Python 侧另设——本单明示**出圈** |

### 2.4 单人桌面 vs 公开部署两档风险定级

- **信任模型原文（README 无「安全边界」专节——l927-05 G4 在案；现状散落两处，逐字引用）**：
  - `README.md:64`：「**沙箱执行**：本地运行用户代码，支持多种语言并带安全与超时边界。」
  - `ui/pages/home.py:55-57`：「本系统的代码执行器使用 subprocess 隔离，适合本机单人学习。／- 不要暴露到公网或校园网共享服务器／- 不要在多人共用环境运行」
- **单人桌面（`RUNNER_SECURITY_MODE=local_only`，默认）＝低风险**：D-2/D-3/D-4 均可容忍——墙钟 5 秒＋树杀＋OS（MemoryError 隔离在子进程）已覆盖本机单人场景的最坏面；Job Object 是**增强项非必需项**。16e3 原文「风险等级请主班按"本机单人"口径定」⇒ 本材料建议定级：**低（增强项）**。
- **公开部署（`RUNNER_SECURITY_MODE=public`）＝设计上拒绝执行**：`core/runners/base.py:29-35 check_security()` 直接返回 `sandbox` 错误不跑学生代码——Job Object 在现设计下**无用武之地**；但若未来 public 模式放开受控执行，D-2/D-3/D-4 三缺从「容忍」升「必需」，Job Object 即第二道防线。建议：落地时把三限额做成**与安全模式无关的常开护栏**（local_only 也受益：防学生代码意外拖机）。
- **定级总表**：单人桌面＝低风险/增强项；公开部署＋拒绝执行（现值）＝不适用；公开部署＋放开执行（未来）＝高风险/必需项。

## §三 落地边界（材料型声明）

- 本单零生产码：Job Object 落码＝执行器行为变更，按任务书禁止事项**另派**；落地时须同步 ①TestCapsSingleSource 扩钉（限额常量单源）②`error_feedback.classify` 词表加档 ③行为级测试（Windows 本机可真跑，无需 skip 形态）。
- 建议首批参数（待实测校准）：内存 512 MB／CPU 时间 5 秒（与墙钟同值，取先到）／活动进程数 8。
