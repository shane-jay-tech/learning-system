# learning 五语言 lessons 与 paths prereqs 引用一致性（l920-08）

- 任务：l920-08-learn-paths-prereq-consistency
- 日期：2026-09-19
- 仓库：D:\code\learning-system
- 性质：**只读对账**，正文与 yaml 零改动（本单只新增 1 个只读脚本 + 本报告）
- 复跑命令：`python scripts/audit_paths_prereq.py`（脚本：`scripts/audit_paths_prereq.py`，零网络零写盘）
- ⚠️ **本文数字是 2026-09-19 快照**：2026-09-20 D5 补学习路径后（42 个未引用 topic 全部进线、
  cpp 13/13 不再是孤儿语言），§一/§三 的计数已变化——**当前真值请看**
  `docs/insights/learn-path-coverage-fill-20260920.md`（同脚本复跑输出）。本文保留为改前基线。
- 上游：l918-16 已钉 estimated_hours 失配与「同 path 内重复引用」（`tests/test_paths_reconcile.py`）；
  **prereqs/topics 引用 slug 与 content/ 目录的一致性当时未核**——本报告补的正是这一块。

## 结论速览

| 方向 | 口径 | 结果 |
|---|---|---|
| A. path → content | 43 个去重 topic 引用是否有实目录 | **悬空 0 条**（干净） |
| A. path → content | prereq 是否都指向同 path 内存在的 milestone id | **悬空 0 条**（干净） |
| B. content → path | 85 个磁盘 topic 中被任何 path 引用者 | **仅 43 个（50.6%）**；**42 个未被引用** |
| B. content → path | 五语言覆盖 | **cpp 13/13 全部未被任何 path 引用（覆盖率 0.0%）** |

两条与直觉相反、需要内容作者决策的现状：

1. **cpp 是「孤儿语言」**：13 个 topic、62 道题在盘，但三条学习路径（agent_mastery / people_analytics / quick_stats）**一条都不引用**。cpp 题只能靠自由练习进入，路径推荐（`core/recommend.path_next_problems` 等）永远不会把它排进来。
2. **python 有 14 个 topic 未被引用**，且集中在第 08 章之后（文件异常处理→正则→numpy→sklearn 进阶→实战），包括 people_analytics m10 之外的全部进阶内容。people_analytics 只吃到 `python/20_hr_pandas`、`21_hr_viz`、`22_hr_model`，中间的 `09→19` 有 8 个 topic 悬空。

**都不算 bug、也不算数据错误**——路径是「精选主线」，不追求覆盖全库。但 42/85 这个比例与 cpp 的 0% 意味着「路径推荐」和「题库」目前是两个基本不相交的世界，这一点此前没有任何一处记录，本报告首次钉下。

## 复跑输出（`python scripts/audit_paths_prereq.py`，原样粘贴）

```markdown
## 一、口径与总量

| 项 | 值 |
|---|---|
| 磁盘 topic 目录总数 | 85 |
| 其中 python / r / cpp / sql / agent_dev | 27 / 18 / 13 / 12 / 15 |
| paths 文件数 | 3 |
| milestone 总数 | 25 |
| topic 引用次数（含重复） | 55 |
| topic 去重后被引用数 | 43 |
| 悬空 topic 引用 | 0 |
| 悬空 prereq 引用 | 0 |
| 未被任何 path 引用的 topic | 42 |

### 各 path 概况

| path | 标题 | header 时数 | milestone 数 | topic 引用次数 | 去重 |
|---|---|---|---|---|---|
| agent_mastery | Agent 指挥主线 | 22 | 10 | 18 | 18 |
| people_analytics | People Analytics 主线 | 48 | 10 | 30 | 30 |
| quick_stats | 统计速成线 | 10 | 5 | 7 | 5 |

## 二、方向 A：path → content（悬空引用）

**悬空 topic 引用：0 条。** 全部 43 个去重 topic 引用都能在 content/<lang>/<slug>/ 找到实目录。

prereq 引用：**悬空 0 条**

## 三、方向 B：content → path（未被引用 topic）

| lang | 磁盘 topic | 被引用 | **未被引用** | 覆盖率 |
|---|---|---|---|---|
| python | 27 | 13 | 14 | 48.1% |
| r | 18 | 9 | 9 | 50.0% |
| cpp | 13 | 0 | 13 | 0.0% |
| sql | 12 | 8 | 4 | 66.7% |
| agent_dev | 15 | 13 | 2 | 86.7% |
| **合计** | **85** | **43** | **42** | **50.6%** |

### python 未被引用 14 项

- `python/08_files_exceptions`
- `python/12_io_excel`
- `python/13_scipy_stats`
- `python/14_sklearn_intro`
- `python/15_ab_text`
- `python/16_classes_oop`
- `python/17_decorators_props`
- `python/18_generators_iter`
- `python/19_regex`
- `python/20_numpy_basics`
- `python/21_datetime_ts`
- `python/22_statsmodels`
- `python/23_sklearn_advanced`
- `python/24_real_world_data`

### r 未被引用 9 项

- `r/04_ggplot`
- `r/07_glm`
- `r/08_tidyr`
- `r/09_purrr_map`
- `r/10_stringr_lubridate`
- `r/11_survival`
- `r/12_clustering`
- `r/13_rmarkdown`
- `r/14_real_world_data`

### cpp 未被引用 13 项

- `cpp/01_io_and_vars`
- `cpp/02_branch_loop`
- `cpp/03_arrays_strings`
- `cpp/04_functions`
- `cpp/05_stl_basics`
- `cpp/06_iter_algo`
- `cpp/07_pointers_class`
- `cpp/08_inheritance`
- `cpp/09_operator_overload`
- `cpp/10_templates`
- `cpp/11_exceptions`
- `cpp/12_file_io`
- `cpp/13_move_semantics`

### sql 未被引用 4 项

- `sql/09_string_funcs`
- `sql/10_date_funcs`
- `sql/11_null_handling`
- `sql/12_people_analytics`

### agent_dev 未被引用 2 项

- `agent_dev/06_frontier`
- `agent_dev/07_data_security`

## 四、跨 path 重复引用

| topic | 引用处 |
|---|---|
| `python/01_hello_and_vars` | agent_mastery/a0; people_analytics/m1 |
| `python/02_conditionals` | agent_mastery/a0; people_analytics/m1 |
| `python/03_loops` | agent_mastery/a0; people_analytics/m1 |
| `python/04_functions` | agent_mastery/a0; people_analytics/m1 |
| `python/05_lists` | agent_mastery/a0; people_analytics/m2 |
| `r/01_vectors_and_basics` | people_analytics/m7; quick_stats/s1 |
| `r/02_logic_and_summary` | people_analytics/m7; quick_stats/s1 |
| `r/05_lm_anova` | people_analytics/m8; quick_stats/s2; quick_stats/s3 |
| `r/06_mixed_apa` | people_analytics/m8; quick_stats/s3; quick_stats/s4 |
| `r/15_cfa` | people_analytics/m9; quick_stats/s5 |
```

## 口径说明（避免与 l918-16 混淆）

- 本报告「重复引用」= **跨 path** 重复（同一 topic 被 >1 条路径引用，10 个）。
- `tests/test_paths_reconcile.py` 钉的是 **同 path 内**重复（quick_stats 的 `r/05_lm_anova`、`r/06_mixed_apa` 各 2 次）。两者口径不同、互不替代，都保留。
- `r/05_lm_anova` 三处被引用（people_analytics/m8、quick_stats/s2、quick_stats/s3），是本库被引用最多的 topic。
- topic 存在性以**目录**为准（`content/<lang>/<slug>/`），不以题目数为准——空目录也算存在。

## 遗留与建议（未执行，需授权）

1. cpp 是否要进路径属**学习路径设计决策**（learning-system 的升级硬触发之一），本单只登记不改。
2. 42 个未引用 topic 是否需要「自由练习/进阶选修」的显式入口，同样是设计决策。
3. 若要自动化防护：可在 `tests/test_paths_reconcile.py` 补一条「悬空 topic 引用数 == 0」用例（现状本就为 0，属零风险翻桩）——本单未做，避免改动他单锚定的测试文件。
