# 编程 + Agent 开发学习平台（0.6.5）

面向中文零基础用户的 **Python · SQL · C++ · R · Agent 开发** 交互式学习系统，当前版本 v0.6.5。提供桌面 app 与网页双模式，覆盖讲解、练习、AI 点评、错题本、成就、热力图和学习报告。

## 技术架构

- Python + Streamlit 网页界面
- PyWebView 桌面套壳（`launcher.pyw`）
- 本地文件存储学习进度、错题、事件与数据导出
- 沙箱运行器执行 Python / SQL / C++ / R 练习
- DeepSeek 兼容的 OpenAI API 用于 AI 讲解、点评与开放题评分
- `scripts/` 提供健康检查、备份、审计、性能基线与冒烟测试工具

学习数据默认保存在本机数据目录；数据库、环境文件、日志和虚拟环境均被 Git 忽略，不会上传到 GitHub。日志靠 `.gitignore` 的 `*.log` 规则兜住，实际写在 `data/`（`launcher.log` 与 `streamlit.log`，跑过桌面入口后才有）；仓库根的 `logs/` 是**无写入方的空目录**，`.gitignore` 里并没有 `logs/` 这条规则。

## 环境要求

- Python 3.10+
- pip
- 可选：PyWebView 桌面运行所需的 WebView2（Windows 10/11 自带）

安装依赖：

```powershell
pip install -r requirements.txt
python scripts/health_check.py
```

## 启动

> 安全说明：服务默认仅监听 127.0.0.1（回环），不暴露局域网。

### 方式 A — 桌面 app（推荐日常使用）

```powershell
python scripts/health_check.py                 # 首次检查环境
powershell -ExecutionPolicy Bypass -File scripts/create_shortcut.ps1
```

然后双击桌面「编程学习平台」快捷方式即可；独立窗口、自定义图标、紫色启动画面、关窗口干净退出。入口链（l923-22 按磁盘实况补登，与 `scripts/create_shortcut.ps1:5/:7`、`launcher.pyw:108-122`、`start.bat:19-27` 逐字相符）：`scripts/create_shortcut.ps1` → 生成的快捷方式指向仓库根 `launcher.pyw`（解释器优先 `.venv\Scripts\pythonw.exe`，图标 `assets\app.ico`）→ `launcher.pyw` 自己 spawn `streamlit run app.py` 并开 PyWebView 窗口。`start.bat` 是**另一条独立入口**（建 venv → `scripts/find_port.py` 探空闲端口 → 直接起 streamlit），不被 `launcher.pyw` 调用，只在缺 pywebview 的报错提示里被点名（`launcher.pyw:265`）。

### 方式 B — 开发模式（改代码热重载）

```powershell
streamlit run app.py
```

浏览器自动打开 http://localhost:8511（与心理系统 8501 错开）。

> **AI 判题链路前提（l1007-14）**：AI 点评依赖 `openai` 包。`.venv` 默认未装（`python -c "import openai"` 报 ModuleNotFoundError）；需 AI 判题时用**根解释器**起服务（根 Python 已装 openai），或经主班批准后向 `.venv` 补装。自检：`python -c "import openai"`。

## 学习闭环

- 5 种语言并行学，进度独立；408 题、85 知识点、6 条学习路径（三项计数会随题库与 `content/paths/` 扩充变动，逐数字的复跑命令与对账见 `docs/insights/learn-readme-numbers-20260922.md`；补题需同批同步的等值点清单见 `plan.md`「题库内容规范」）。
- 每题：讲解 + 编辑器 + 沙箱运行 + AI 老师点评（难度分层）+ 多轮追问 + 错题本。
- AI 出变式题、自适应间隔复习、学习面板、报告导出、AI 进展自查。
- 开放题按 rubric 逐维度评分并追踪历史。
- 多路径交叉推荐：完成一条路径里程碑后，自动推荐其他路径的互补内容。
- 学习数据可导出、可迁移、可备份；关键行为写入学习事件账本。

## 信任模型（沙箱边界）

（本节即首页提示所称的「安全边界」章节。）

代码执行器（`core/runners/`）是**护栏而非安全边界**。按部署形态分两档：

- **本机单人（默认，`RUNNER_SECURITY_MODE` 未设或 `local_only`，见 `core/config.py`）**：执行器假设操作者＝机器所有者，隔离目标是「防学生代码的意外事故」（死循环拖机、超大输出、误写文件），不是防恶意用户。现有护栏：子进程隔离＋墙钟超时＋输出/输入字节上限＋工作目录临时化＋env 白名单与 PATH 收窄（见 `core/runners/python_runner.py` 的 `_ENV_ALLOWLIST` 与 `_safe_env`）。已知未管控面：网络出站、文件系统写位（护栏外）、解释器目录内的旁路可执行文件——单人场景按可接受风险对待，材料见 `docs/insights/sandbox-network-identity-path-material-20261006.md`（F-2/F-5/F-6）与 `docs/insights/l927-11-fs-constraint-adjudication.md`（F-1 文件系统）。
- **公开部署（`RUNNER_SECURITY_MODE=public` 或 `PUBLIC_DEPLOY=1`）**：执行器**直接拒绝运行学生代码**（`core/runners/base.py` 的 `check_security`），只保留浏览与讲解。这是当前唯一支持的公开姿态；「公开环境受控执行」所需的资源限额（`docs/insights/sandbox-resource-limits-design-20261006.md`）、出站管控与身份隔离均属未落地的安全面清单，放开前必须逐项补齐。

不要把本系统暴露到公网或多人共用环境后依赖沙箱护栏充当安全边界——那是它明确不提供的保证。

## 当前能力亮点（v0.6.5）

- **成就系统**：22 枚徽章，涵盖打卡、语言、路径与特殊成就。
- **学习热力图**：13 周（91 日格）活动日历可视化。
- **双模式**：桌面 app 与 Streamlit 网页共用同一套核心与数据。
- **沙箱执行**：本地运行用户代码，支持多种语言并带安全与超时边界。
- **诊断与报告**：生成系统报告、路径诊断与学习面板视图。

## 验证

```powershell
# 属性标注（l927-32，2026-09-28 逐条实测副作用后追加；口径见 docs/insights/l927-32-note.md）：
#   只读＝零写盘可夜跑 ／ 写盘＝会落盘 ／ 需日间＝连生产库或起进程，夜桥禁照块跑
pytest                           # 单元与回归测试 —— 只读（实测仅写 .pytest_cache/ 与 __pycache__）｜全量约 400s，可夜跑
python scripts/health_check.py   # 环境健康检查 —— 只读（实测仓内零文件变化、生产库 sha 不变）｜可夜跑
python scripts/smoke_boot.py     # 快速启动冒烟测试 —— 起进程（绑 127.0.0.1:8599，脚本自带 terminate）｜需日间，夜桥禁跑
python scripts/perf_baseline.py  # 性能基线 —— 连生产库（无参 ProgressDAO()，默认库 data/progress.db；连接期生成临时 -wal/-shm 侧车）｜需日间
python scripts/audit_content.py  # 题库内容审计 —— 只读（实测 rc=0 零写盘）｜可夜跑
python scripts/backup_data.py    # 学习数据备份 —— 写盘＋删档（写新 zip、默认 --keep 5 轮换删最旧备份，并对生产库做 WAL checkpoint）｜需日间，夜桥禁跑
python scripts/prune_old_data.py # 过期数据清理 —— 连生产库；默认干跑不删行，加 --apply 即 DELETE＋VACUUM 删数据行｜需日间，夜桥禁跑
python scripts/generate_system_report.py # 系统报告 —— 只读（实测零写盘，只打印指标；--strict 会走 pytest 收集，慢）｜可夜跑
python scripts/validate_content.py # 内容校验器 —— 只读（content/ 全量 yaml：解析＋练习 schema 必填字段＋basename 同名三面计数；--domain 过滤域）｜可夜跑
```

## 目录

```text
app.py                     Streamlit 入口
launcher.pyw               桌面 app 启动器（PyWebView 套壳，被桌面快捷方式调用）
start.bat                  浏览器模式启动脚本（建 venv → 探端口 → streamlit，独立于 launcher）
requirements.txt           运行依赖清单
requirements-freeze.txt    实测锁定版本快照
pytest.ini                 pytest 配置（testpaths / python_files / -ra）
.coveragerc                覆盖率统计口径（branch=True，omit .venv/tests/datasets）
.gitignore                 忽略规则（进度库、*.log、.venv 等；**没有** logs/ 这条）
plan.md                    前端人体工学改造计划（固化目标与内容口径的在册依据）
README.md                  本文件
.streamlit/                Streamlit 运行时配置（config.toml：回环绑定、极简工具栏）
assets/                    图标与启动画面（app.ico / app.png）
core/                      判题、AI、进度、成就、推荐、报告等核心模块
core/runners/              Python / SQL / C++ / R 沙箱运行器
ui/                        Streamlit 页面与组件
content/                   python / cpp / r / sql / agent_dev 题库与知识点
content/paths/             学习路径定义（YAML，与 README「学习闭环」的路径数同源）
content/datasets/          Python 练习用的示例数据（CSV ＋ 生成脚本；PythonRunner 判题时整树只读挂载，
                           l1023-019 档核正：唯一消费方＝python 题面，SQL/R/C++ runner 零引用）
                           hr_recruitment/hr_survey 两件＝确定性测试夹具资产（l1006-05 案B转正登记：
                           tests/test_hr_dataset_determinism.py md5 硬钉，题面暂未消费，hr 族扩题可直接引用）
                           l1025-001..003 扩容：research_data/survey_data/ml_dataset/sales_data 四件
                           ＝statsmodels/sklearn_advanced/real_world 补题批2 数据基座（确定性 seed=42）
scripts/                   健康检查、备份、审计、性能与维护脚本（含 1 个 PowerShell 件）
tests/                     测试套件
docs/                      系统报告与巡检留痕 insights/
data/                      本地学习数据（不进入 Git，`.gitkeep` 占位除外；日志也落这里）
logs/                      空目录，全仓零写方（来历未考；日志实际写在 data/*.log）
```
