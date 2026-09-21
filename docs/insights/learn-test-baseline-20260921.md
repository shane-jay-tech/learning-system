# learning 测试资产基线（l922-03，2026-09-21）

- 任务：l922-03-learn-test-baseline（cwd `D:\code\learning-system`，软预算 ≤30 分钟）
- 性质：**基线刷新**，源码与测试实现零改动（本单只新增本档 + 给旧档加 superseded 指针）
- 取代：`docs/insights/learn-tests-baseline-20260915.md`（368 时代，已标 superseded）
- 上游口径档：`docs/insights/learn-384-7-caliber-20260918.md`（「7 是 skipped 不是 failed」的表述纪律，本档沿用）

## 一、实跑（先命令后数字）

> ⚠️ **本节数字是 l922-03 于 2026-09-21 实跑的时点值，已被本档 §六 取代**（09-22 复跑为
> 597 passed / 7 skipped / 604 collected）。原文按「基线档不回改」保留，不删不改。
> 例行取数请直接看 §六。主题归类（§二）与缺口清单（§四）不受影响，仍有效。

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

---

## 六、复跑刷新（n922-10，2026-09-22 00:3x，cwd `D:\code\learning-system`）

- 任务：`n922-10-learn-baseline-file`（软预算 ≤30 分钟）；性质：**同档复跑刷新**，源码与测试实现零改动。
- 取数时点：`HEAD = 1632f91`（工作树 `git status --porcelain` 空）。基线绑定 commit，不绑定日期——同日仍有别的班在往 `tests/` 追加用例。

### 实跑

```
$ PYTHONIOENCODING=utf-8 python -m pytest tests -q          # 第一遍
597 passed, 7 skipped in 46.09s                              rc(${PIPESTATUS[0]})=0
$ PYTHONIOENCODING=utf-8 python -m pytest tests -q          # 第二遍（重跑稳定性）
597 passed, 7 skipped in 44.25s                              rc=0
$ PYTHONIOENCODING=utf-8 python -m pytest tests --collect-only -q
604 tests collected in 1.08s                                 # 597 + 7 = 604 自洽
```

两遍 passed/skipped 完全一致（仅墙钟 46.09s → 44.25s 抖动），**重跑稳定**。

### 与 §一 的界差（增量可复算，不是抄来的数）

`0564042`（l922-03 落 566 的那个提交）到 `1632f91` 之间，逐提交净增 `def test_`：

| commit | 单 | 净增用例 |
|---|---|---:|
| `7451474` | l922-04 content yaml 行尾普查 | +1 |
| `304ddc7` | l922-05 topic 双号对账 | +1 |
| `5e266ae` | l922-06 难度末档下限桩 | +5 |
| `5b6bd03` | l922-08 recommend 私有纯函数直钉 | +9 |
| `fee9dc6` | l922-09 achievements 私有对直钉 | +4 |
| `1632f91` | l922-10 ai_review 缓存层直钉 | +11 |
| **合计** | 6 提交（l922-07 纯文档，未触及 `tests/`） | **+31** |

566 + 31 = **597** ✅ 采集侧同界：573 + 31 = **604** ✅ 两条界差与 passed 增量三者互洽，无一例消失、无一例凭空出现。
（`def test_` 计数与采集数在此区间相等，说明这 31 例里没有 parametrize 展开；若将来出现展开，本表口径要改用 `--collect-only -q` 逐文件差值。）

### skip 归属：与 §一 逐行相同，零变化

```
$ PYTHONIOENCODING=utf-8 python -m pytest tests -q -rs | grep "^SKIPPED" | sort
SKIPPED [1] tests\test_cpp_runner.py:16: g++ not available; skipping C++ runner tests
SKIPPED [1] tests\test_cpp_runner.py:27: g++ not available; skipping C++ runner tests
SKIPPED [1] tests\test_cpp_runner.py:34: g++ not available; skipping C++ runner tests
SKIPPED [1] tests\test_cpp_runner.py:44: g++ not available; skipping C++ runner tests
SKIPPED [1] tests\test_r_runner.py:13: Rscript not available; skipping R runner tests
SKIPPED [1] tests\test_r_runner.py:19: Rscript not available; skipping R runner tests
SKIPPED [1] tests\test_r_runner.py:25: Rscript not available; skipping R runner tests
```
cpp 4 + r 3 = 7，行号与 §一 表格完全一致 → 「cpp/r 两条 runner 真跑面在本机为 0 验证」这条缺口（§四.1）在 09-21→09-22 之间**未被解除**（本单按禁止事项不装依赖）。

### 测试文件面

```
$ ls tests/test_*.py | wc -l        → 68     # §一 记 65 个 test_*.py；09-21 后新增 3 个（crlf / difficulty / 双号对账 等，见上表）
$ ls tests/*.py   | wc -l           → 70     # 含 __init__.py 与非采集挂具 mutation_mark_r_judge_plain.py
```
`tests/mutation_mark_r_judge_plain.py` 仍不被 pytest 采集（§四.3 未解除）。

### 本档口径提示（防止下一班再抄错）

- **基线数字绑 commit**：引用本档时写「597 passed / 7 skipped @ `1632f91`」，不要只写日期。
- §二 的主题归类表与 §四 的缺口清单是**结构分析**，不随用例数漂移，本单复核后仍有效：cpp/r runner 零真跑、薄模块（`test_content_numeric_consistency` 2 例等）、变异挂具不入采集、覆盖率档过期——四条缺口**全部仍开放**。
- 旧档 `learn-tests-baseline-20260915.md` 头部的 superseded 指针（l922-03 所加）指向本档，本单刷新后该指针依然落点正确，未重复添加。

### 声明

本单**零源码、零测试实现改动**，只在本档追加本节 + §一 头部一行「本节数字已被取代」提示；未改判分逻辑、题库内容、旧档 `learn-tests-baseline-20260915.md`（其 superseded 指针经核已存在，不重复添加）；未 push。

