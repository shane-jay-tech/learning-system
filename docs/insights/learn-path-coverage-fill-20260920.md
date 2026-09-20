# learning 补学习路径：42 个未引用 topic 全部进线（D5 落地）

- 任务：D5（用户 2026-09-20 拍板「按推荐进行」）— 依据 `docs/decisions/2026-09-20-user-decisions-partials.md` 第 14 行
- 上游事实：l920-08 只读对账（`zcode-bridge/done/l920-08-learn-paths-prereq-consistency.result.md`）
  ——磁盘 85 个 topic 仅 43 个被任何 path 引用（50.6%），**cpp 13/13 零引用（0.0%）**
- 日期：2026-09-20 ｜ 仓库：D:\code\learning-system ｜ 起点 HEAD：`283629b`
- 性质：**内容数据（paths yaml）改动**——改前已备份、改后有回读断言（见 §四）
- 复跑命令：`python scripts/audit_paths_prereq.py`（只读对账，口径不另立）
  与 `python -m pytest tests/test_paths_coverage.py tests/test_paths_reconcile.py -q`

## 一、补齐方案（先出方案，再落地）

用户口径：**补学习路径**（内容已在库，补路径比砍内容便宜）。逐项取舍如下：

| # | 落点 | 覆盖 | 取舍依据（为什么是它、为什么不是别的） |
|---|---|---|---|
| C1 | **新增** `content/paths/cpp_foundation.yaml`（5 里程碑 / 13 topic / 21h） | cpp 13/13（0% → 100%） | cpp 是唯一「零引用孤儿语言」（62 题在盘）。既有三条线主题分别是 Agent 协作、People Analytics、统计速成——把 C++ 塞进任何一条都会让主线跑题；而 cpp 01→13 自带「起步→STL→指针与类→模板与资源」完整梯度，独立成线零拼接成本 |
| P1 | **新增** `content/paths/python_advanced.yaml`（5 里程碑 / 14 topic / 21h） | python 14 项（48.1% → 100%） | 未引用的 14 项集中在第 08 章之后（文件异常→正则→OOP/装饰器/生成器→numpy/时间→统计建模/ML→实战）。它们与 PA 主线的 HR 主线题（09–11、20–22_hr）主题不同；塞进 PA 会把 48h 主线撑到 70h+ 且主题发散，故另立「进阶级」 |
| R1 | **新增** `content/paths/r_advanced.yaml`（4 里程碑 / 9 topic / 14.5h） | r 9 项（50% → 100%） | `quick_stats` 只有 10h，定位就是「速成」，塞 9 个进阶 topic 会破坏该定位；这 9 项（ggplot/tidyr/purrr/stringr/glm/survival/clustering/rmarkdown/real_world）自成「R 进阶工具箱 + 交付」 |
| S1 | **既有** `people_analytics` 插入 `m6b`「SQL 实战补强」（4 topic / 5h，位于 m6 SQL 高级 之后） | sql 4 项（66.7% → 100%） | 这 4 项是 SQL 自身的补强段，其中 `sql/12_people_analytics` **题名即本线主题**，域内归属无歧义；单独开一条 4 topic（≈5h）的新线太薄，没人会把它当主线 |
| A1 | **既有** `agent_mastery` 追加 `a10`「Agent 前沿与数据安全」（2 topic / 3h，prereq `a7`） | agent_dev 2 项（86.7% → 100%） | `06_frontier`（MCP/工具调用/多 Agent/RAG/CoT）与 `07_data_security`（PII/密钥/脱敏/最小化）本就属 Agent 主线；接在 `a7` 实战之后作为「前沿 + 底线」，与 a8/a9 同构（单里程碑、prereq 指向 a7/a8/a9 系） |

**没动的**：`quick_stats`（其 5 个引用于磁盘全部有效，且它顶着「速成」定位）；跨 path 的 10 条重复引用（属既有设计，见 §五）；`agent_mastery` 的 header 22h 失配（既有遗留，见 §五）。

小时数口径：新增里程碑按既有线实测密度 `≈1.3–1.5h/topic`（people_analytics 3 topic≈4h、quick_stats 2 topic≈2–3h）取整；C++ 的指针/模板/移动语义按难度上浮。

## 二、落地明细

新增三条线（新文件，零改既有行）：

| path | 里程碑（id 标题 · topic 数 · 时数） |
|---|---|
| `cpp_foundation` | c1 起步（2·3h）→ c2 数组/字符串/函数（2·3.5h）→ c3 STL/迭代算法（2·3.5h）→ c4 指针/类/继承（3·5h）→ c5 模板/异常/资源管理（4·6h）｜header 21h |
| `python_advanced` | p1 文件/异常/文本（3·4.5h）→ p2 Pythonic/OOP（3·4.5h）→ p3 数值与时间（2·3h）→ p4 统计建模与 ML（4·6h）→ p5 真实数据与实验（2·3h）｜header 21h |
| `r_advanced` | r1 整形与可视化（2·3h）→ r2 回归与生存（2·4h）→ r3 函数式与文本（2·3h）→ r4 聚类/报告/实战（3·4.5h）｜header 14.5h |

既有两处（**仅增量行**，题干/文案零改写）：

- `people_analytics.yaml`：header `estimated_hours: 48 → 53`（与里程碑合计保持一致，该线原本 header==合计）；m6 之后插入 `m6b`，topics = sql/09_string_funcs、10_date_funcs、11_null_handling、12_people_analytics。
- `agent_mastery.yaml`：a9 之后追加 `a10`，topics = agent_dev/06_frontier、07_data_security；**header 22h 有意不动**（见 §五 遗留 1）。

## 三、复跑输出（`python scripts/audit_paths_prereq.py`，原样粘贴）

```markdown
## 一、口径与总量

| 项 | 值 |
|---|---|
| 磁盘 topic 目录总数 | 85 |
| 其中 python / r / cpp / sql / agent_dev | 27 / 18 / 13 / 12 / 15 |
| paths 文件数 | 6 |
| milestone 总数 | 41 |
| topic 引用次数（含重复） | 97 |
| topic 去重后被引用数 | 85 |
| 悬空 topic 引用 | 0 |
| 悬空 prereq 引用 | 0 |
| 未被任何 path 引用的 topic | 0 |

### 各 path 概况

| path | 标题 | header 时数 | milestone 数 | topic 引用次数 | 去重 |
|---|---|---|---|---|---|
| agent_mastery | Agent 指挥主线 | 22 | 11 | 20 | 20 |
| cpp_foundation | C++ 从入门到现代 | 21 | 5 | 13 | 13 |
| people_analytics | People Analytics 主线 | 53 | 11 | 34 | 34 |
| python_advanced | Python 进阶级 | 21 | 5 | 14 | 14 |
| quick_stats | 统计速成线 | 10 | 5 | 7 | 5 |
| r_advanced | R 统计进阶线 | 14.5 | 4 | 9 | 9 |

## 二、方向 A：path → content（悬空引用）

**悬空 topic 引用：0 条。** 全部 85 个去重 topic 引用都能在 content/<lang>/<slug>/ 找到实目录。

prereq 引用：**悬空 0 条**

## 三、方向 B：content → path（未被引用 topic）

| lang | 磁盘 topic | 被引用 | **未被引用** | 覆盖率 |
|---|---|---|---|---|
| python | 27 | 27 | 0 | 100.0% |
| r | 18 | 18 | 0 | 100.0% |
| cpp | 13 | 13 | 0 | 100.0% |
| sql | 12 | 12 | 0 | 100.0% |
| agent_dev | 15 | 15 | 0 | 100.0% |
| **合计** | **85** | **85** | **0** | **100.0%** |

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

内容审计（path 引用存在性由它兜底）：

```
$ python scripts/audit_content.py
PASS: 0 errors, 4 accepted, 0 warnings
```

## 四、回读断言与验收

| 完成标准 | 状态 | 证据（真实命令输出） |
|---|---|---|
| 改前备份 | **达成** | `data/backups/content-20260920-133722/`（87 文件：3 paths + 84 r，含 `manifest-before.txt` 逐文件 sha256） |
| 未被引用 topic 归零 | **达成** | 审计脚本「未被任何 path 引用的 topic \| 0」；五语言逐语言 100.0% |
| cpp 13/13 | **达成** | 同上表 cpp 行 `13 \| 13 \| 0 \| 100.0%` |
| 悬空 topic / prereq 归零 | **达成** | 审计脚本方向 A：均 0 条；`audit_content.py` PASS 0 errors |
| 结构自洽（header==合计、无同 path 重复、prereq 无环） | **达成** | 三新线 header==sum（21 / 21 / 14.5）；people_analytics 48→53 同步；agent_mastery 为既有失配（钉桩翻新，见下） |
| 里程碑 → 题目可解析 | **达成** | 冒烟：6 条线 41 个里程碑逐条解析 topic，题数全部 >0；`_detect_completed_milestones`/`_path_next_problems`/`check_achievements` 空库不崩 |
| 测试 | **达成** | `python -m pytest -q` → **487 passed / 7 skipped / 0 failed**（基线 481/7，本单 +6 例） |
| 有意翻桩有留痕 | **达成** | `tests/test_paths_reconcile.py`：`KNOWN_HOURS_MISMATCH` `(22,26)` → `(22,29)`，注释写明 D5 由来 |

新增守卫：`tests/test_paths_coverage.py`（5 例）——**未被引用 == 0 / cpp 13/13 / 悬空归零 / 三新线可加载 / 全库 85==85**。口径直接复用 l920-08 的只读脚本，不另立第二套。将来新增 topic 而不进任何 path，该用例立即红（逼显式决策）。

## 五、遗留问题

1. **`agent_mastery` header 22h ≠ 里程碑合计 29h**（原 22 vs 26）：既有失配，l918-16 已钉桩待拍板（修 header 还是改里程碑时数）。本单只补路径、**不夹带修 header**，只把合计钉到新真值 29。
2. **跨 path 重复引用 10 项**：既有设计（同一 topic 出现在多条线，如 `r/05_lm_anova` 3 处），本单未动；口径与 l920-08 报告一致。
3. **`quick_stats` 同 path 内重复 2 项**（`r/05_lm_anova`、`r/06_mixed_apa`）：l918-16 已钉桩（`_path_overall_progress` 会重复计数致进度虚高），属独立单，未动。
4. **新增的三条线是设计方案，未经真人试跑**：里程碑顺序/时数是按既有线密度推的，试跑后可调；调整只涉及 paths yaml，无代码耦合。
5. 本机 **无 g++ / Rscript**（`test_cpp_runner.py` 4 例、`test_r_runner.py` 3 例 skip），C++/R 的判题路径未在真机执行——本单只改 paths 数据，不触及判题代码，但相关语言的实际运行验证仍缺。
