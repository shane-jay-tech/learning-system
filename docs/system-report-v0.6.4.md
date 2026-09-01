# 编程 + Agent 开发学习平台 — 系统报告 v0.6.4

> 生成日期：2026-08-15 | 版本：0.6.4

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
| 代码行数 | ~10,057 行 |
| 测试用例 | 269 个（262 passed, 7 skipped, 0 xfail） |
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
- **数据库**：SQLite + WAL 模式
- **AI**：多模型 fallback 链（Flash → Kimi → GPT 快档；Pro → GPT → Kimi 质量档），带 45s 链级总预算
- **内容**：YAML 题目 + Markdown 讲解

### 核心模块

```
core/
├── loader.py        # 内容加载（YAML + mtime 缓存 + 签名 memo TTL）
├── progress.py      # 数据持久化（7 tables + DAO 聚合方法 + 本地时区）
├── judge.py         # 判题（代码运行 + AI 开放题 + 推荐归因）
├── ai_review.py     # AI 评分（schema 校验 + prompt 版本 + 链预算）
├── recommend.py     # 推荐（6 级优先级 + reason_code + 去重）
├── achievements.py  # 成就（22 徽章 + 三态）
├── paths.py         # 学习路径（跨路径推荐）
├── report.py        # 学习报告
└── runners/         # 沙箱（Python / SQL / C++ / R）
```

### 数据库表

| 表 | 用途 |
|----|------|
| `attempts` | 作答历史 |
| `problems_status` | 题目状态缓存 |
| `meta` | 键值元数据（成就、streak、路径事件去重） |
| `review_state` | 间隔复习 |
| `rubric_scores` | 维度评分（含 prompt_version, model） |
| `learning_events` | 学习事件（11 种，全部已实现） |
| `schema_meta` | Schema 版本 |

---

## 3. 核心功能

### 学习闭环

| 功能 | 说明 |
|------|------|
| 多语言做题 | 5 种语言，400 题 |
| AI 代码点评 | 难度分层 + 多轮追问 |
| 开放题评分 | rubric 逐维度打分 |
| 间隔复习 | SM-2 变体 |
| 智能推荐 | 6 级优先级 + recommendation_id 全链路归因 + 去重 |
| 成就系统 | 22 枚徽章 |
| 热力图 | 90 天活动日历 |
| 学习报告 | 天/周/月维度 |
| AI 变式题 | 基于原题生成 |
| 跨路径推荐 | 里程碑后推荐互补内容 |
| 错题本专项 | 三种练习模式 |
| 推荐效果面板 | 漏斗 + reason_code 分组 + 时间窗口 |
| 复习健康度 v2 | 逾期分桶、高风险题、平均间隔 |
| 能力维度趋势 | rubric 各维度平均分 + 薄弱维度识别 |
| 路径事件 | path_started + milestone_completed |

### 学习事件（11 种，全部已实现）

| 事件 | 触发时机 | payload 关键字段 |
|------|----------|-----------------|
| `attempt_submitted` | 提交作答 | passed |
| `problem_passed` | 通过题目 | — |
| `problem_failed` | 未通过 | — |
| `ai_open_scored` | 开放题评分完成 | score, passed |
| `achievement_unlocked` | 成就解锁 | — |
| `recommendation_shown` | 推荐展示 | recommendation_id, reason_code, surface, rank |
| `recommendation_clicked` | 点击推荐 | recommendation_id, reason_code, surface, rank |
| `recommendation_completed` | 完成被推荐的题 | recommendation_id, reason_code, surface, rank |
| `lesson_viewed` | 浏览课程 | — |
| `path_started` | 首次进入路径 | — |
| `path_milestone_completed` | 里程碑首次完成 | — |

### 推荐系统

| 填充顺序 | 策略 | reason_code | 限额 |
|----------|------|-------------|------|
| 1 | 路径阻塞错题 | `path_blocking` | 2 |
| 2 | 到期复习 | `review_due` | 2 |
| 3 | 路径下一题 | `path_next` | 2 |
| 4 | 弱项巩固 | `weak_topic` | 不限 |
| 5 | 错题复习 | `wrong_retry` | 不限 |
| 6 | 探索新题 | `explore` | 不限 |
| 独立区域 | 跨路径推荐 | `cross_path` | 3 |

推荐归因（v0.6.3 补齐全链路）：
- 每条推荐携带唯一 `recommendation_id`（格式 `YYYYMMDD_surface_reason_lang_pid_rank`）
- shown→clicked→completed 三阶段均携带同一 `recommendation_id` + `surface` + `rank`
- 可精确计算单条推荐的 impression→click→completion 转化

### 复习健康度 v2

| 指标 | 说明 |
|------|------|
| 复习池 | 进入间隔复习的题目总数 |
| 到期待复习 | 已到期未完成 |
| 逾期分桶 | 1-3天 / 4-7天 / >7天 |
| 高风险题 | 上次失败 + 已逾期 |
| 平均间隔 | 全池平均复习间隔天数 |

### AI 评分保障

- Score clamp [0,100]
- Passed/score 一致性（<40 强制 fail，>=80 强制 pass）
- 空维度过滤
- Prompt 版本 + Model 记录
- 20 条 golden set 回归测试

---

## 4. v0.6.4 变更（性能与体验大修）

### 性能：签名 memo 化（根因修复）

单次 dashboard 渲染曾调用 `_signature()`（os.walk 全库扫描）184 次、`load_language` 174 次，
占页面渲染时间 98%（2.3s/2.34s）。加 2 秒 TTL 的签名 memo 后：

| 页面（每次交互的服务端重跑） | 修复前 | 修复后 | 提升 |
|------------------------------|--------|--------|------|
| Dashboard | ~1208ms | ~12ms | 100× |
| 主页 Home | ~388ms | ~7ms | 55× |
| 学习路径列表 | ~394ms | ~4ms | 100× |
| 语言做题页（打字触发重跑） | ~14ms | ~3ms | 4.7× |
| 错题本 | ~2ms | ~2ms | — |

核心操作（perf_baseline 实测）：recommend 412.8ms → **3.5ms**；generate_report 52.8ms → **0.5ms**；
load_language 冷载 192.8ms → 122.4ms。

### 启动与加载

| 变更 | 说明 |
|------|------|
| streamlit_ace 惰性加载 | ~0.5s 的组件 import 从首屏挪到首次渲染编辑器时 |
| WebView 持久 profile | 桌面 App 用独立 `data/webview_profile`，跨启动缓存 Streamlit 前端静态资源（~10MB），后续启动显著更快；仍与心理系统完全隔离 |
| pywebview 进 requirements | 修复新环境按 README 装依赖后桌面模式直接崩溃的问题；缺依赖时给出友好弹窗 |

### 人性化修复（反人类设计清理）

| 变更 | 说明 |
|------|------|
| 「↺ 重置」真正生效 | 带 key 的编辑器 widget 状态优先级高于 value 参数，旧实现重置后会被旧值覆盖。现在 epoch 计数使 key 变化 → 组件重建 |
| AI 等待诚实化 | 3 模型 × 60s 最坏等待 3 分钟 → 链级 45s 总预算 + 单模型 30s；spinner 文案如实告知最长等待 |
| 提问后清空输入框 | 三个 AI 问答区发送后不再残留文字 |
| 时间本地化 | 最近活动/错题时间、14 天趋势、90 天热力图从 UTC 改为本地日期（UTC 下凌晨提交会归到"昨天"） |

### Bug 修复

| Bug | 修复 |
|-----|------|
| 学习诊断三个按钮写 `session_state.page`（路由系统不认）→ 点了没反应 | 改用 `route` |
| 错题本「弱项专练 → 练习」写 `lang/topic` 无效键 → 跳转到空白页 | 走统一 `navigate_to_problem` |
| R 版本回退路径按字典序排序（4.9 赢过 4.10） | 数值元组排序 |
| xfail 清零 | 2 个 xfail 测试全部转正 |

---

## 5. 代码执行安全

| 语言 | 机制 | 限制 |
|------|------|------|
| Python | subprocess + 隔离 | 5s timeout, env 清洗 |
| C++ | g++ 编译运行 | 10s timeout |
| R | Rscript | 5s timeout |
| SQL | sqlite3 in-memory + authorizer | 只允许 SELECT/WITH |

定位：本机单人可信环境，非公网部署。

---

## 6. 测试

| 类别 | 数量 |
|------|------|
| 单元 / 集成测试（pytest 收集，含参数化） | 269 |
| 通过 | 262 |
| 跳过（无 g++ / Rscript） | 7 |
| xfail（已知 bug 遗留） | **0** |
| AppTest 端到端流程 | 3 |

7 个 skip：4 C++ runner + 3 R runner（无编译器）。

新增 AppTest 端到端回归（真实跑 app.py，不碰真实数据库）：
- 重置按钮恢复 starter + epoch 递增
- 诊断「跳过」导航到学习路径
- 错题本弱项「练习」走统一导航

---

## 7. 性能

| 操作 | 中位数 | P95 | 目标 |
|------|--------|-----|------|
| 内容加载（冷） | 122ms | 160ms | <800ms |
| 内容加载（缓存） | 0ms | — | <100ms |
| 推荐生成 | 3.5ms | 3.8ms | <800ms |
| 学习报告 | 0.5ms | 0.7ms | <3000ms |
| 系统指标 | 51ms | 56ms | <3500ms |

页面交互（服务端重跑，bench_pages 实测）：全部 < 15ms。
所有指标远低于目标阈值。

---

## 8. 内容质量

```
$ python scripts/audit_content.py --strict
PASS: 0 errors, 3 accepted, 0 warnings
```

3 个 accepted warning（均为专题定位，统一难度是有意设计）：

| 目标 | 原因 |
|------|------|
| `cpp/12_file_io` | 文件 IO 专题，偏中高级 |
| `r/11_survival` | 生存分析专题，统计进阶 |
| `agent_dev/04_review_agent` | Review Agent 专题，系统设计导向 |

---

## 9. 运维脚本

| 脚本 | 用途 |
|------|------|
| `health_check.py` | 环境检查 |
| `audit_content.py` | 内容质量检查 |
| `perf_baseline.py` | 性能基准 |
| `bench_pages.py` | 页面重跑成本基准（新增） |
| `prof_pages.py` | 页面热点剖析（新增） |
| `smoke_boot.py` | 无头启动冒烟测试（新增） |
| `generate_system_report.py` | 系统指标（`--json` / `--check` / `--strict`） |
| `backfill_events.py` | 历史事件回填 |
| `create_shortcut.ps1` | 桌面快捷方式 |

### 自检命令组

```bash
python scripts/health_check.py            # 环境和依赖
python scripts/audit_content.py --strict   # 内容质量
python -m pytest tests -q                  # 全量测试
python scripts/perf_baseline.py            # 性能
python scripts/generate_system_report.py   # 系统指标
```

---

## 10. 文件结构

```
learning-system/
├── core/          # 业务逻辑（~2,959 行）
├── ui/            # Streamlit 前端（~2,127 行）
├── content/       # 400 题 + 85 知识点 + 3 路径
├── tests/         # 269 测试（~3,789 行）
├── scripts/       # 9 个运维脚本（~982 行）
├── docs/          # 系统报告
├── data/          # SQLite 数据库
└── README.md
```

---

## 11. 版本历史

| 版本 | 主要变更 |
|------|----------|
| v0.1 | 骨架：每语言 1 topic + 2 题 |
| v0.2 | 扩展：每语言 5+ topic + 30 题 |
| v0.3 | 间隔复习 + AI 出题 + 学习路径 + 82 topics + 359 题 |
| v0.3.1–0.3.7 | 安全守卫、推荐增强、性能、内容补全、报告校验 |
| v0.4.0 | Agent 真实任务包 + 多路径交叉推荐 |
| v0.5.0 | 成就系统 + 热力图 + 开放题维度评分 |
| v0.5.1 | 验收测试 + 三态成就 + 6 级推荐 + 事件表 |
| v0.5.2 | 推荐结构化 + AI Schema 校验 + 迁移管理 |
| v0.5.3 | 内容质量治理 + golden set + 400 题 |
| v0.5.4 | 推荐完成追踪 + 过度工程清理 |
| v0.6.0 | 错题本专项 + 推荐效果面板 + 复习健康度 + 维度趋势 |
| v0.6.1 | cross_recommend 修复 + 路径事件 + 推荐漏斗v2 |
| v0.6.2 | 漏斗SQL修复 + DAO聚合 + recommendation_id + 漏斗测试 |
| v0.6.3 | 推荐归因全链路 + 复习健康度v2 + 逾期分桶 + 高风险题 |
| **v0.6.4** | **性能大修（签名 memo，页面重跑提速 50-100×）+ 启动优化 + 4 个 bug 修复 + 人性化改进** |

---

## 12. 后续方向

| 优先级 | 方向 |
|--------|------|
| P1 | 能力维度标准化（dimension_id） |
| P2 | PDF 报告导出 |
| P2 | AI 变式题质量增强（草稿区 + 自测） |
| P2 | 数据备份与导入导出 |
| P3 | 课程管理后台 |

---

*单人使用，本机运行，不需要正式发布流程。*
