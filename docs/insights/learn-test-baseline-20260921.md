# learning 测试资产基线（l922-03，2026-09-21）

- 任务：l922-03-learn-test-baseline（cwd `D:\code\learning-system`，软预算 ≤30 分钟）
- 性质：**基线刷新**，源码与测试实现零改动（本单只新增本档 + 给旧档加 superseded 指针）
- 取代：`docs/insights/learn-tests-baseline-20260915.md`（368 时代，已标 superseded）
- 上游口径档：`docs/insights/learn-384-7-caliber-20260918.md`（「7 是 skipped 不是 failed」的表述纪律，本档沿用）

## 一、实跑（先命令后数字）

```
$ PYTHONIOENCODING=utf-8 python -m pytest -q
566 passed, 7 skipped in 57.92s                      rc(${PIPESTATUS[0]})=0
$ PYTHONIOENCODING=utf-8 python -m pytest --collect-only -q
573 tests collected in 1.38s                          # 566 + 7 = 573 自洽
$ ls tests/*.py | wc -l                               → 67（= 65 个 test_*.py + __init__.py + mutation_mark_r_judge_plain.py）
$ 采集模块数                                            → 65
```

**闭合校验（增量可复算，不是抄来的数）**：l921-02 自述全量 560 → 本单 566，差 **6** 恰为 l921-03 新增的
`tests/test_sql_judge_column_order.py` 采集数（`--collect-only` 逐文件计数为 6）。560 + 6 = 566 ✅

**7 条 skip 的归属（订正交接口径）**：不是「7 条 R-runner」，而是**两族**——

| 模块 | skip 数 | 原因（pytest 原文） |
|---|---:|---|
| `tests/test_cpp_runner.py` | 4（:16/:27/:34/:44） | `g++ not available; skipping C++ runner tests` |
| `tests/test_r_runner.py` | 3（:13/:19/:25） | `Rscript not available; skipping R runner tests` |

即 **cpp 与 r 两条 runner 的真跑面在本机为 0 验证**，且 skip 数与 09-15/09-18 两档完全相同（7 → 7），
六个批次零变化。解除方式是日间装 g++/Rscript，本单按「禁止装依赖」不碰。

## 二、增量盘点：2026-09-15 后新增的测试文件（30 个，采集 213 例）

口径：`git log --diff-filter=A --since=2026-09-15T00:00 --name-only -- tests/`（21 个提交、30 个新增文件），
逐文件用例数取本单 `--collect-only -q` 实况。

| 主题族 | 文件（采集例数） | 合计 | 覆盖点 |
|---|---|---:|---|
| **判分内核** | `test_mark_r_judge_txn`(29) `test_mark_r_judge_plain`(28) `test_judge_mode_equivalence`(10) `test_judge_rows_characterization`(9) `test_judge_contract_edges`(8) `test_judge_pure`(7) `test_sql_judge_column_order`(6) | **97** | mark_r 的 WAL 事务/备份/启动恢复/信任边界；judge_mode 等价性四层证明；行比较 _rows_equal 与 _first_diff_cell 的宽松 cell、None 语义；SQL 判分**位置敏感**（列序+行序）钉桩（l921-03） |
| **题库内容普查** | `test_content_census_r`(9) `test_content_census_sql`(6) `test_content_census_agent_dev`(5) `test_content_census_cpp`(5) `test_content_census_python`(5) `test_content_census`(4) `test_content_ids_unique`(3) `test_content_numeric_consistency`(2) | **39** | 五语言纵向逐字段断言（statement/答案键集/difficulty/hints）、语言内 id 唯一与前缀一致、跨语言 slug 冲突、statement 自陈期望值一致性 |
| **UI 行为** | `test_dashboard_page_render`(15) `test_home_next_action`(5) `test_home_ai_pulse`(5) `test_mistakes_edges`(3) `test_path_focus_expand`(3) `test_language_topic_nav`(3) `test_language_chats`(4) | **38** | dashboard 渲染主路径（覆盖率 9%→59%）、next_action 三区、AI pulse 30/90 天三档、mistakes 逾期边界与 missing 禁用、topic nav 三位置、中问 AI 历史 |
| **paths 元数据/覆盖** | `test_paths_coverage`(6) `test_paths_reconcile`(5) | **11** | header 时数==里程碑合计（无白名单）、时数为正数、同 path 重复引用、prereq 无环、topic 引用零悬空；42 个孤儿专题全进线后的覆盖钉 |
| **报告渲染契约** | `test_report_markdown_contract`(6) `test_report_goals`(5) | **11** | report_to_markdown 的段落契约与 goals 拼装（l921-01 把重复实现并轨 `_build_goals`） |
| **配置与可移植** | `test_data_portability_guards`(8) `test_config_env`(5) `test_achievements_branches`(4) | **17** | local_only/public 模式与 `PUBLIC_DEPLOY=1` 旁路、`LLM_SCRIPT` 覆盖、数据文件可移植守卫、成就分支 |
| **非采集脚本** | `mutation_mark_r_judge_plain.py`(0) | 0 | 变异测试挂具，**pytest 不采集**——见遗留问题 2 |
| **合计** | 30 文件 | **213** | 占全量采集 573 的 **37.2 个百分点** |

**与 384 档的界差（别把 213 当 384→566 的差额）**：本表 `--since` 取 09-15，而 384 档实测于 09-18，
其中 09-16/09-17 落地的 5 个文件（`test_judge_contract_edges`+`test_dashboard_page_render`+
`test_achievements_branches`+`test_data_portability_guards`+`test_judge_pure` = **42 例**）在 384 里已计过。
按采集口径对齐：384/7 = **391** collected（本仓 v0.6.5 注记即以 391 记该态，commit `a66d604`），
573 − 391 = **182**；其中 09-18 之后新增的 25 个文件贡献 213 − 42 = **171**，余 **11** 例来自
**存量文件内部增长**（如 l921-02 给 `test_paths_reconcile` 加悬空零桩、l920-01..08 逐语言普查展开）。
skip 恒 7 故 passed 侧同界：384 + 182 = 566 ✅。182 的构成是「新增文件 171 + 存量内部 11」，
本档不把它笼统记成「新写了 182 个测试」。

## 三、与旧档的衔接

| 档 | 数字 | 状态 |
|---|---|---|
| `learn-tests-baseline-20260915.md` | 368 passed / 7 skipped（09-16 实跑） | **superseded**（已在其头部加指针） |
| `learn-384-7-caliber-20260918.md` | 384 passed / 7 skipped | 保留（口径澄清档，非基线档） |
| 本档 | **566 passed / 7 skipped / 573 collected**（09-21 实跑） | 现役基线 |

## 四、剩余缺口（按可执行性排序）

1. **cpp/r runner 真跑面零验证（7 例恒 skip）**：判分链路里只有 python 与 sql 两条在本机真跑过；
   cpp 与 r 的 runner 断言从未在本机执行。出口＝日间装 `g++` 与 `Rscript` 后复跑本档命令，期望 573 collected 全 passed。
2. **薄模块**：`test_content_numeric_consistency` 仅 2 例（强/宽两模式各 1）、`test_app_flow`/`test_ai_followup`/
   `test_ai_review_offline` 各 3-4 例——启发式类断言的分支覆盖明显偏薄，是下一批补测的廉价目标。
3. **变异挂具不入采集**（`tests/mutation_mark_r_judge_plain.py`）：跑它需要显式命令，全量 pytest 绿**不代表**变异面被验过。
4. **覆盖率档过期**：`learn-coverage-reconcile-20260917.md` 的 77%/4327 语句绑定 09-16 代码面，
   与 566 例的测试面已不同界；该档自己也写了「基线文件应刷新」。本单未跑 coverage（需 `--cov`，属另一口径）。

## 五、声明

- 本单**零源码/零测试改动**，只新增本档 + 旧档头一行 superseded 指针；未改任何判分逻辑与题库内容（红线域未触碰）。
- 所有数字均来自本机实跑，复现命令见 §一；未 push。
