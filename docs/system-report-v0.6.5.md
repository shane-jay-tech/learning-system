# 编程 + Agent 开发学习平台 — 系统报告 v0.6.5

> 生成日期：2026-08-15 | 版本：0.6.5

---

## 1. 系统概览

面向中文零基础用户的 **Python · SQL · C++ · R · Agent 开发** 交互式学习系统。

| 指标 | 数值 |
|------|------|
| 支持语言 | 5（Python / SQL / C++ / R / Agent Dev） |
| 总题目数 | 400 |
| 知识点主题 | 85 |
| 学习路径 | 3 条 |
| 路径里程碑 | 25 个 |
| 成就徽章 | 22 枚 |
| 代码沙箱 | 4 种 |
| 代码行数 | ~10,900 行 |
| 测试用例 | 311 个（304 passed, 7 skipped, 0 xfail） |
| 数据库表 | 7 张 |

### 学习路径

| 路径 | 里程碑数 | 预估学时 |
|------|----------|----------|
| Agent 指挥主线 | 10 | 22h |
| People Analytics 主线 | 10 | 48h |
| 统计速成线 | 5 | 10h |

### 题目分布

| 语言 | 题目数 | 知识点 |
|------|--------|--------|
| Python | 121 | 27 |
| SQL | 54 | 12 |
| C++ | 62 | 13 |
| R | 85 | 18 |
| Agent Dev | 78 | 15 |

---

## 2. 技术架构

- **前端**：Streamlit（Web）+ PyWebView（桌面 App）
- **后端**：纯 Python 单进程
- **数据库**：SQLite + WAL（时间列索引 + 渲染内查询 memo）
- **AI**：多模型 fallback 链 + 45s 链级总预算 + 反馈 LRU 缓存
- **内容**：YAML 题目 + Markdown 讲解

---

## 3. v0.6.4 变更（性能与体验大修）

### 性能：签名 memo 化（根因修复）

单次 dashboard 渲染曾调用 `_signature()`（os.walk 全库扫描）184 次，占渲染时间 98%。
加 2 秒 TTL 的签名 memo 后：dashboard ~1208ms→**~7ms**、home ~388ms→**~5ms**、
路径列表 ~394ms→**~2ms**；核心操作 recommend 412.8ms→**3.5ms**。

### 启动与加载

- streamlit_ace 惰性加载（首屏省 0.5s）
- WebView 独立持久 profile（跨启动缓存 22MB 前端资源，仍与心理系统隔离）
- start.bat / 开发模式恢复「自动打开浏览器」（此前 config headless=true 吞掉了这个行为）
- start.bat 自动探测空闲端口（8511-8530），端口被占不再直接报错

### 人性化修复

- 「↺ 重置」真正生效（epoch 计数重建编辑器组件）
- AI 等待诚实化（3×60s 最坏 3 分钟 → 链级 45s 预算；spinner 如实标注）
- 提问发送后清空输入框；判定完成 st.toast 即时提示
- 时间本地化（活动/趋势/热力图按本地日期）

### Bug 修复（v0.6.4）

诊断导航 session key、错题本弱项导航、R 版本排序、x2 xfail 清零。

---

## 4. v0.6.5 变更（深度审计修复轮）

四路独立深度审计（UI 体验 / 数据层 / 沙箱判题 / 启动器脚本）+ 逐项修复，**17 项高/中危缺陷清零**：

### 判题正确性（沙箱与判题链）

| 修复 | 说明 |
|------|------|
| SQL expected_rows 数值宽松比较 | 1 与 1.0 视为相等；差异时给出「第 r 行第 c 列：实际/期望」精确提示 + SELECT 字段顺序建议 |
| 错误摘要取真正原因行 | 此前取 stderr 第一行（Python 恒为 "Traceback..."）；现在过滤骨架行取错误本体 |
| SQL 递归 CTE 误拒 | authorizer 放行 SQLITE_RECURSIVE——content 里的 04_recursive_cte 此前会被 "not authorized" 误拒 |
| SQL 注释识别 | -- 与 /* */ 不再被误切为多语句而误拒 |
| 空代码统一拒绝 | 四语言行为一致，给出「代码为空」友好提示，不产生 attempt 记录 |
| 期望空输出 | `expected_output: ""` 不再因 `or` 回退到题目级期望 |
| R 输出归一化补全 | 折叠列对齐空格，`print(c(1,200))` 与 `cat(1,200)` 可比 |
| SQL 失败不再盲盒 | 语法错误/超时把 stderr 写进 diff 提示 |
| 进程树清理 | 超时用 taskkill /T 杀整棵进程树 + TemporaryDirectory 容错清理，孙进程不再卡死判题 |
| SQL 结果集上限 | 10000 行 + stdout 截断，递归 CTE/笛卡尔积不再打爆内存与 UI |
| 其余加固 | stdin 1MB 上限 + 编码容错；多字节字符截断不再出乱码；SQL 超时 Timer 竞态防护 |
| C++ 编译进程树 | 编译改 Popen + communicate：超时整棵树杀（此前 subprocess.run 只杀直接子进程，MinGW 的 cc1plus 孙进程会卡死管道） |
| PATH 收窄统一 | Python/R 的 PATH 收窄为解释器目录 + System32（与 C++ 一致），不再完整继承父进程 PATH |
| SQL/C++ 中文报错 | 常见英文报错（no such table / 漏分号 / 未定义等 12 个模式）附中文提示，LLM 离线也有兜底 |
| 内容层深度校验 | 新增 `audit_content_deep.py`：SQL setup_sql 内存库试跑、Python/agent_dev starter 语法解析、id/标题/目录一致性、expected_rows 结构、tests 结构、stdin 提示一致性、路径 prereq 存在性、C++/R 起手代码括号平衡（注释与字符串感知）、专题编号重复提示——发现并修复 2 处内容缺陷（agent_dev 02_named_constant 起手代码语法错误、cpp 04_substring 题面残留作者思考过程） |

### 数据层

| 修复 | 说明 |
|------|------|
| daily_streak 截断 bug | 此前 LIMIT 500 行会低估高频用户的连续天数（streak_30 永不触发）；改为 400 个去重本地日期 |
| list_mistakes N+1 | 2×N 相关子查询 → 窗口函数一次扫描 |
| milestone_progress N+1 | 支持状态快照 + 渲染内 memo，数十次单行查询 → 1 次 |
| 时间列索引 | attempts(ts) / rubric_scores(ts) / learning_events(created_at) / problems_status(status,last_attempt_ts)，大表下 O(N)→O(窗口) |
| 渲染内查询 memo | daily_streak / summary / list_mistakes / all_status 单渲染只算一次（dashboard 一次渲染曾 3 次算 streak） |
| dashboard 连接复用 | recommend/cross_recommend 共享 DAO，不再重复开连接 |
| 错题本查找缓存 | find_problem O(M×P) → O(M+P) |
| AI 反馈 LRU 缓存 | 同题同代码重复提交不再重复调用 LLM（失败结果不入缓存） |
| 其余 | rubric 批量插入、到期复习轻量 id 查询、复习健康度上限、错题本死按钮禁用+提示 |
| 追问增量上下文 | follow_up/ask_lesson 的代码/题面/讲解全文只在首轮发送，后续轮次复用历史，多轮追问 prompt 体积约减半 |
| AI 调用 JSON 抽取加固 | 括号配对抽取替代贪婪正则，嵌套对象/字符串内花括号/尾随废话不再解析失败 |
| 数据保留策略 | 新增 `scripts/prune_old_data.py`：attempts/learning_events 按时间 + 每题保留最近 N 次清理（窗口函数实现，干跑/apply 双模式），阻断长期线性膨胀 |
| session_state 回收 | 做题页 LRU 只保留最近 30 道题的状态（代码/对话/编辑器），长会话不再无界累积 |
| HTML 打印版报告 | `report_to_html`：自包含 HTML（内联样式 + @media print + 全内容转义），浏览器 Ctrl+P 打印/另存 PDF；面板新增「🖨️ 打印版 (.html)」下载按钮 |
| 数据备份工具 | 新增 `backup_data.py`：checkpoint 后打包 zip；`--list` / `--restore`（恢复前旧库保留 .bak） |
| 能力维度标准化 | 新增 `core/rubric_dims.py`：LLM 自由文本维度名 → 10 个规范维度（关键词映射）；rubric_scores 增 dimension_id 列（自动迁移）；趋势/均分按规范维度跨题聚合，遗留数据 COALESCE 回退；评分 prompt 引导规范维度名 |
| 数据可移植导入导出 | 新增 `core/data_portability.py`：全库 JSON 导出（versioned 格式 + 结构校验）、合并式导入（状态/复习按题覆盖、答题/事件追加、meta 幂等）；面板新增导出下载与导入上传（渲染内缓存避免每帧序列化全库） |
| WAL checkpoint 治理 | `ProgressDAO.checkpoint_wal()` 公开方法；backup/prune 脚本统一调用（TRUNCATE），维护操作前保证完整落盘 |
| launcher 健壮性收尾 | terminate_backend 提取为模块级可测函数；日志 setup 移入 main()（import 无副作用）；start.bat venv 创建失败检测；health_check 复用 core.config 的 LLM 路径；launcher 测试 5→11 个（单例锁/子进程命令/终止三路/MessageBox/DPI 分支全覆盖） |

### 启动器与脚本

| 修复 | 说明 |
|------|------|
| Streamlit 僵尸进程 | atexit 兜底清理 + 日志滚动（3×1MB）+ 子进程日志句柄关闭 |
| 健康检查 4xx 误判 | 只认 200；launcher 单例二次启动给友好弹窗而非静默退出 |
| create_shortcut.ps1 | 优先 .venv pythonw（此前指向裸系统 pythonw，桌面模式缺全部依赖）；路径改 $PSScriptRoot 推导 |
| health_check 门禁 | 核心依赖缺失退出码 1（llm/g++/Rscript 缺失仅警告）；新增 pywebview 探测 |
| backfill 时区 | UTC→本地日期（此前本地凌晨提交永久归到前一天）+ 按 attempt_id 去重（不再丢同题同天多次提交） |
| 系统报告校验 | 数字整词匹配（total=5 不再被 "15" 假 PASS）+ 类内测试计入 |
| audit_content | 死代码路径校验复活：缺语言前缀/未知语言的 topic 引用现在真报错 |

### 交互与体验

| 修复 | 说明 |
|------|------|
| AI 变式题不落库 | 伪 ID 不再污染错题本/进度/成就/复习池 |
| 切语言索引残留 | 侧栏切语言/主页进入统一重置 topic·problem 索引并清 radio 状态，不再跳回旧专题 |
| 诊断重测 | 清空旧答案；默认不预选；未答完提交有提示；跳转定位到推荐里程碑 |
| 做题中问 AI | 输入框移到按钮下方右栏，不再跨栏找输入框 |
| 文案/可读性 | 时长文案统一、语病修正、辅助文字 ≥12px 且加深对比度、隐藏裸 traceback |

---

## 5. 代码执行安全

| 语言 | 机制 | 限制 |
|------|------|------|
| Python | subprocess + 隔离 | 5s timeout, env 清洗, stdin 1MB |
| C++ | g++ 编译运行 | 10s timeout, 受限 PATH |
| R | Rscript | 5s timeout |
| SQL | sqlite3 in-memory + authorizer | 只允许 SELECT/WITH, 结果 ≤1 万行 |

定位：本机单人可信环境，非公网部署（public 模式整体拒绝执行）。

---

## 6. 测试

| 类别 | 数量 |
|------|------|
| 单元 / 集成测试（pytest 收集，含参数化） | 311 |
| 通过 | 304 |
| 跳过（无 g++ / Rscript） | 7 |
| xfail（已知 bug 遗留） | **0** |
| AppTest 端到端流程 | 3 |

---

## 7. 性能

| 操作 | 中位数 | P95 | 目标 |
|------|--------|-----|------|
| 内容加载（冷） | 122ms | 160ms | <800ms |
| 内容加载（缓存） | 0ms | — | <100ms |
| 推荐生成 | 3.5ms | 3.8ms | <800ms |
| 学习报告 | 0.5ms | 0.7ms | <3000ms |
| 系统指标 | 51ms | 56ms | <3500ms |

页面交互（服务端重跑，bench_pages 实测）：

| 页面 | 耗时 |
|------|------|
| Dashboard | ~7ms |
| 主页 Home | ~5ms |
| 路径列表 | ~2ms |
| 语言做题页 | ~3ms |
| 错题本 | ~2ms |

---

## 8. 运维脚本

| 脚本 | 用途 |
|------|------|
| `health_check.py` | 环境检查（核心依赖缺失时退出码 1） |
| `audit_content.py` | 内容质量检查（含路径 topic 引用校验） |
| `audit_content_deep.py` | 内容深度校验（SQL setup 试跑 / starter 语法 / id 唯一性 / 结构） |
| `perf_baseline.py` | 性能基准 |
| `bench_pages.py` | 页面重跑成本基准 |
| `prof_pages.py` | 页面热点剖析 |
| `bench_imports.py` | 模块导入成本 |
| `smoke_boot.py` | 无头启动冒烟测试 |
| `find_port.py` | start.bat 用空闲端口探测 |
| `prune_old_data.py` | 数据保留策略清理（干跑/apply） |
| `backup_data.py` | 数据备份/恢复（progress.db 打包 zip，零依赖） |
| `generate_system_report.py` | 系统指标（整词匹配校验） |
| `backfill_events.py` | 历史事件回填（本地时区 + attempt_id 去重） |
| `create_shortcut.ps1` | 桌面快捷方式（.venv 优先） |

---

## 9. 版本历史

| 版本 | 主要变更 |
|------|----------|
| v0.1 – v0.5.4 | 骨架、扩展、复习、推荐、成就、质量治理（见 README） |
| v0.6.0 | 错题本专项 + 推荐效果面板 + 复习健康度 + 维度趋势 |
| v0.6.1 | cross_recommend 修复 + 路径事件 + 推荐漏斗v2 |
| v0.6.2 | 漏斗SQL修复 + DAO聚合 + recommendation_id + 漏斗测试 |
| v0.6.3 | 推荐归因全链路 + 复习健康度v2 + 逾期分桶 + 高风险题 |
| v0.6.4 | 性能大修（签名 memo，页面重跑提速 50-100×）+ 启动优化 + 4 个 bug + 人性化改进 |
| **v0.6.5** | **四路深度审计修复：判题正确性 11 项、数据层 8 项、启动器/脚本 9 项、交互体验 5 项，新增 17 个回归测试，0 xfail** |

---

## 10. 后续方向

| 优先级 | 方向 |
|--------|------|
| P1 | AI 调用进程复用（常驻 llm 服务，省每次 100-300ms 子进程启动） |
| P1 | AI 调用进程复用（需改仓库外 D:/code/scripts/llm_call.py） |
| P3 | （无） |

---

*单人使用，本机运行，不需要正式发布流程。*
