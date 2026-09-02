# 编程 + Agent 开发学习平台

面向中文零基础用户的 **Python · SQL · C++ · R · Agent 开发** 交互式学习系统，当前版本 v0.6.5。提供桌面 app 与网页双模式，覆盖讲解、练习、AI 点评、错题本、成就、热力图和学习报告。

## 技术架构

- Python + Streamlit 网页界面
- PyWebView 桌面套壳（`launcher.pyw`）
- 本地文件存储学习进度、错题、事件与数据导出
- 沙箱运行器执行 Python / SQL / C++ / R 练习
- DeepSeek 兼容的 OpenAI API 用于 AI 讲解、点评与开放题评分
- `scripts/` 提供健康检查、备份、审计、性能基线与冒烟测试工具

学习数据默认保存在本机数据目录；数据库、环境文件、日志和虚拟环境均被 Git 忽略，不会上传到 GitHub。

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

### 方式 A — 桌面 app（推荐日常使用）

```powershell
python scripts/health_check.py                 # 首次检查环境
powershell -ExecutionPolicy Bypass -File scripts/create_shortcut.ps1
```

然后双击桌面「编程学习平台」快捷方式即可；独立窗口、自定义图标、紫色启动画面、关窗口干净退出。

### 方式 B — 开发模式（改代码热重载）

```powershell
streamlit run app.py
```

浏览器自动打开 http://localhost:8511（与心理系统 8501 错开）。

## 学习闭环

- 5 种语言并行学，进度独立；400 题、85 知识点、3 条学习路径。
- 每题：讲解 + 编辑器 + 沙箱运行 + AI 老师点评（难度分层）+ 多轮追问 + 错题本。
- AI 出变式题、自适应间隔复习、学习面板、报告导出、AI 进展自查。
- 开放题按 rubric 逐维度评分并追踪历史。
- 多路径交叉推荐：完成一条路径里程碑后，自动推荐其他路径的互补内容。
- 学习数据可导出、可迁移、可备份；关键行为写入学习事件账本。

## 当前能力亮点（v0.6.5）

- **成就系统**：22 枚徽章，涵盖打卡、语言、路径与特殊成就。
- **学习热力图**：90 天活动日历可视化。
- **双模式**：桌面 app 与 Streamlit 网页共用同一套核心与数据。
- **沙箱执行**：本地运行用户代码，支持多种语言并带安全与超时边界。
- **诊断与报告**：生成系统报告、路径诊断与学习面板视图。

## 验证

```powershell
pytest                           # 单元与回归测试
python scripts/health_check.py   # 环境健康检查
python scripts/smoke_boot.py     # 快速启动冒烟测试
python scripts/perf_baseline.py  # 性能基线
python scripts/audit_content.py  # 题库内容审计
python scripts/backup_data.py    # 学习数据备份
python scripts/prune_old_data.py # 过期数据清理
python scripts/generate_system_report.py # 系统报告
```

## 目录

```text
app.py                Streamlit 入口
core/                 判题、AI、进度、成就、推荐、报告等核心模块
core/runners/         Python / SQL / C++ / R 沙箱运行器
ui/                   Streamlit 页面与组件
content/              python / cpp / r / sql / agent_dev 题库与知识点
scripts/              健康检查、备份、审计、性能与维护脚本
tests/                测试套件
docs/                 系统报告
data/                 本地学习数据（不进入 Git）
```
