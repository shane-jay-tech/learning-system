# 编程 + Agent 开发学习平台 — 系统报告 v0.6.3

> 生成日期：2026-07-05 | 版本：0.6.3

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
| 代码行数 | ~8,131 行 |
| 测试函数 | 184 个（177 passed, 7 skipped） |
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
- **AI**：多模型 fallback 链（Flash → Kimi → GPT 快档；Pro → GPT → Kimi 质量档）
- **内容**：YAML 题目 + Markdown 讲解

### 核心模块

```
core/
├── loader.py        # 内容加载（YAML + mtime 缓存）
├── progress.py      # 数据持久化（7 tables + DAO 聚合方法）
├── judge.py         # 判题（代码运行 + AI 开放题 + 推荐归因）
├── ai_review.py     # AI 评分（schema 校验 + prompt 版本）
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

推荐效果面板：
- DAO 方法 `recommendation_funnel(days)` 和 `recommendation_funnel_by_reason(days)` 封装聚合逻辑
- 支持 7 天 / 30 天 / 全部 时间窗口
- 按 reason_code 策略分组展示 CTR

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

## 4. v0.6.3 变更

| 变更 | 说明 |
|------|------|
| 推荐归因全链路 | clicked/completed 事件携带同一 recommendation_id + surface + rank |
| session 印象缓存 | 推荐展示时存入 session_state，点击时查回同一 ID |
| completed 全属性复制 | judge.py 从最近一次 shown 复制 recommendation_id/surface/rank |
| 复习健康度 v2 | 新增 DAO `review_health_stats()` 返回逾期分桶 + 高风险题 |
| Dashboard 逾期分桶 | 展示 1-3天/4-7天/>7天 分布 |
| 高风险题展示 | 上次失败且逾期的题单独列出 |
| 归因回归测试 | 新增 4 个测试覆盖 completed 全属性、无 shown 不触发、逾期分桶 |

---

## 5. 代码执行安全

| 语言 | 机制 | 限制 |
|------|------|------|
| Python | subprocess + 隔离 | 5s timeout, env 清洗 |
| C++ | g++ 编译运行 | 10s timeout |
| R | Rscript | 10s timeout |
| SQL | sqlite3 in-memory + authorizer | 只允许 SELECT/WITH |

定位：本机单人可信环境，非公网部署。

---

## 6. 测试

| 类别 | 数量 |
|------|------|
| 核心逻辑 | 47 |
| Runner 安全 | 14 |
| SQL authorizer | 10 |
| 推荐系统 | 12 |
| 跨路径推荐 | 6 |
| 成就系统 | 17 |
| 热力图 | 8 |
| Rubric 评分 | 14 |
| Golden set + schema | 10 |
| Schema 迁移 | 6 |
| Dashboard + 漏斗 + 归因 | 16 |
| 报告 | 4 |
| 其他 | 20 |
| **合计** | **184**（177 passed, 7 skipped） |

7 个 skip：4 C++ runner + 3 R runner（无编译器）。

---

## 7. 性能

| 操作 | 中位数 | P95 | 目标 |
|------|--------|-----|------|
| 内容加载（冷） | 102ms | 103ms | <800ms |
| 内容加载（缓存） | 4ms | — | <100ms |
| 推荐生成 | 217ms | 233ms | <800ms |
| 学习报告 | 30ms | 31ms | <3000ms |
| 系统指标 | 64ms | 70ms | <3500ms |

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
├── core/          # 业务逻辑（~2,898 行）
├── ui/            # Streamlit 前端（~2,094 行）
├── content/       # 400 题 + 85 知识点 + 3 路径
├── tests/         # 184 测试（~2,245 行）
├── scripts/       # 6 个运维脚本（~695 行）
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
| **v0.6.3** | **推荐归因全链路 + 复习健康度v2 + 逾期分桶 + 高风险题** |

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
