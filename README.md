# 编程 + Agent 开发学习平台 v0.6.5

面向中文零基础用户的 **Python · SQL · C++ · R · Agent 开发** 交互式学习系统。

- **桌面 app**（PyWebView 套壳）+ 网页（Streamlit）双模式
- 5 种语言并行学，进度独立，400 题、85 知识点、3 条学习路径
- 每题：讲解 + 编辑器 + 沙箱运行 + AI 老师点评（难度分层）+ 多轮追问 + 错题本
- AI 出变式题、自适应间隔复习、学习面板、报告导出、AI 进展自查
- **成就系统**：22 枚徽章，涵盖打卡/语言/路径/特殊成就
- **学习热力图**：90 天活动日历可视化
- **开放题维度评分**：AI 按 rubric 逐维度打分并追踪历史
- **多路径交叉推荐**：完成一条路径的里程碑后，自动推荐其他路径的互补内容

## 启动方式

### 方式 A — 桌面 app（**推荐日常使用**）

```bash
pip install -r requirements.txt
python scripts/health_check.py     # 首次检查环境
```

然后**双击桌面快捷方式**「编程学习平台」即可——独立窗口、自定义图标、紫色启动画面、关窗口干净退出。如果桌面没有，跑一次：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/create_shortcut.ps1
```

### 方式 B — 开发模式（改代码热重载）

```bash
streamlit run app.py
```

浏览器自动打开 http://localhost:8511（与心理系统 8501 错开）。**改代码后页面自动刷新**——开发用这个。

## 环境要求

| 必装                 | 用于         | 不装的后果                    |
|--------------------|------------|---------------------------|
| Python ≥ 3.10      | 整个平台       | 跑不起来                      |
| pip 装的依赖（见上）       | UI / YAML  | 跑不起来                      |
| AI 点评依赖 D:/code/scripts/llm_call.py 与 .env.local | AI 老师反馈 | 点评显示"暂时不可用"，不影响判题 |
| g++（MinGW）         | C++ 题目     | 提交 C++ 题会提示"未检测到 g++"   |
| Rscript（R 安装包）     | R 题目       | 提交 R 题会提示"未检测到 Rscript" |

> Windows 安装 MinGW：https://www.mingw-w64.org/  
> Windows 安装 R：https://cran.r-project.org/bin/windows/base/

## 目录结构

```
learning-system/
├── app.py                    # Streamlit 入口
├── core/
│   ├── runners/              # 4 种语言的沙箱执行器
│   ├── judge.py              # 判题协调（运行 + AI 点评 + 写库）
│   ├── ai_review.py          # 调 llm_call.py
│   ├── progress.py           # SQLite 进度库
│   └── loader.py             # 题库加载（YAML + Markdown）
├── content/                  # 题库（按语言分目录）
│   ├── python/01_hello_and_vars/{_lesson.md, *.yaml}
│   ├── sql/01_select_where/...
│   ├── cpp/01_io_and_vars/...
│   └── r/01_vectors_and_basics/...
├── ui/
│   ├── styles.py             # 全局 CSS
│   ├── components.py         # 复用组件
│   └── pages/{home,language,mistakes}.py
├── tests/                    # pytest
├── scripts/health_check.py
└── data/progress.db          # 自动生成
```

## 添加一道题

1. 找到对应语言的 topic 目录（例如 `content/python/01_hello_and_vars/`）
2. 新建一个 yaml 文件，文件名前两位是序号（决定显示顺序），如 `03_my_problem.yaml`
3. 字段（必填星号）：

```yaml
title: "题目名"            # *
topic: "01_hello_and_vars" # *
difficulty: 1              # 1-5
tags: ["io"]
statement: |               # * Markdown 题目描述
  请用 print 输出 ...
starter_code: |            # * 起手代码模板
  # 在这里写代码

expected_output: |         # *（普通题）期望 stdout
  Hello

# 或者（SQL 题）：
# setup_sql: |
#   CREATE TABLE ...; INSERT ...;
# expected_rows:
#   - [1, "Alice", 92]

# 可选：测试用例的 stdin
# tests:
#   - stdin: "3 5\n"
#     expected_output: "8\n"

hints:
  - "提示一"
  - "提示二"
```

4. 保存后刷新浏览器（题库有 mtime 缓存，无需重启）。

## 添加一个新知识点（topic）

1. 在 `content/<lang>/` 下新建 `02_xxx/` 目录
2. 写 `_lesson.md` 作为讲解，再放若干题目 yaml
3. 在 `core/loader.py` 的 `_TOPIC_TITLES` 字典里加上中文标题（可选；不加会用 slug 替代）

## 运行测试

```bash
pytest
pytest --cov=. --cov-branch --cov-config=.coveragerc --cov-report=term-missing
```

C++ 和 R 的 runner 测试在工具不在 PATH 时会自动 skip，不会失败。

## 自检命令

改完代码后跑这几个确认没坏：

```bash
python scripts/health_check.py            # 环境和依赖
python scripts/audit_content.py --strict   # 内容质量
python scripts/audit_content_deep.py       # 内容深度校验（SQL setup 试跑/语法/id）
python -m pytest tests -q                  # 全量测试
python scripts/perf_baseline.py            # 性能
python scripts/generate_system_report.py   # 系统指标
```

## 已知限制与安全边界

> **⚠️ 重要安全声明：本系统当前运行器不是安全沙箱，不要部署到公网、校园网共享服务器或多人共用环境。**
>
> 支持场景：**本机、单人、可信代码练习**。运行器使用 subprocess + tempdir + 超时做基本隔离，学生代码可执行宿主机命令——这在本机自用时等同于"你自己在终端跑代码"，可以接受；但联网多人场景下这是严重安全漏洞。
>
> 如需安全模式：设置环境变量 `RUNNER_SECURITY_MODE=public` 或 `PUBLIC_DEPLOY=1`，此时所有 runner 将拒绝执行学生代码并返回明确错误。

- **不是真正的安全沙箱**：用 `subprocess + tempdir + 超时` 做隔离，本机单人使用足够
- **AI 点评依赖外网**：调 D:/code/scripts/llm_call.py，断网或 key 失效时点评会降级为静态文案，但判题不受影响
- **没有用户系统**：单本地数据库，多人共用会串数据
- **无单步调试**：只能整段提交运行（AI 点评会提供变量追踪提示辅助定位问题）
- **C++ 题目编译选项固定**为 `-std=c++17 -O0 -Wall`；要改编译选项需要修改 `core/runners/cpp_runner.py`

## 后续路线

- v0.1 ✅ 骨架：每语言 1 topic + 2 题
- v0.2 ✅ 扩展：每语言 5+ topic + 30 题
- v0.3 ✅ 间隔复习 + AI 出题 + 学习路径 + 82 topics + 359 题
- v0.3.1 ✅ 安全守卫 + AI 分层 + 首屏优化 + 路径桥接 + 回归测试
- v0.3.2 ✅ 推荐接入 review_state + 诊断 UI + 双栏布局 + 内容补全
- v0.3.3 ✅ 选题状态统一 + 4 空 topic 补齐 + 内容审计清零 + 性能索引
- v0.3.4 ✅ 性能多次采样 + 导航 helper 全覆盖 + README 检查扩展
- v0.3.5 ✅ 口径闭合 + 性能余量 3× + 一键发布验证
- v0.3.6 ✅ 报告校验闭环 + 路径里程碑验证 + 发布语义精确
- v0.3.7 ✅ 校验语义化 + 行级路径校验 + pytest skip 白名单 + 性能表自动生成
- v0.4.0 ✅ Agent 真实任务包（8 道实战题）+ 多路径交叉推荐引擎
- v0.5.0 ✅ 成就系统 + 学习热力图 + 开放题维度评分 + Spec 迭代/多轮迭代内容
- v0.5.1 ✅ 优化指南执行：验收测试+三态成就+6级推荐+事件表+安全增强
- v0.5.2 ✅ 推荐结构化+AI Schema校验+迁移管理+审计增强
- v0.5.3 ✅ 内容质量治理+事件扩展+golden set+迁移测试+400题
- v0.5.4 ✅ 质量治理闭环：waiver白名单+事件注册表+推荐完成追踪+漂移检测
- v0.6.0 ✅ 错题本专项练习+推荐效果面板+复习健康度+维度趋势+Dashboard增强
- v0.6.1 ✅ cross_recommend修复+路径事件+推荐漏斗v2+事件surface标注
- v0.6.2 ✅ 漏斗SQL修复+DAO聚合方法+recommendation_id+漏斗测试
- v0.6.3 ✅ 推荐归因全链路+复习健康度v2+逾期分桶+高风险题识别
- v0.6.4 ✅ 性能大修（签名memo，页面重跑提速50-100×）+启动优化（惰性ACE、WebView持久缓存）+4个bug修复（诊断导航/弱项导航/R版本排序/重置失效）+时间本地化+AI等待预算
- v0.6.5 ✅ 四路深度审计修复：判题正确性（SQL列序/递归CTE/注释/空代码/进程树/结果集上限）+数据层（streak截断bug/窗口函数/时间索引/查询memo/AI反馈缓存）+启动器脚本（僵尸进程/健康检查/快捷方式/回填时区）+交互体验（变式题不落库/切语言状态/诊断重测）
- v0.7 📋 PDF报告导出、AI变式题增强、数据导入导出
