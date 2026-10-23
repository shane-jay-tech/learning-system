# l1023-007 薄题复核·python 域（第二批补题候选·文件级薄形态）

- 独立扫描（本单自扫，未复用 l1023-001 census 中间产物）：content/python/ 全量 136 yaml，三型薄形态判据：tests 键缺／hints 键空／difficulty 键空。
- 扫描结论：difficulty缺＝0 件；tests缺＝88 件（其中 84 件属 schema 合法替代——judge=run＋expected_output 或 judge=ai_open＋rubric，**非薄**，仅注记不列候选）；hints缺＝6 件。真第二批候选＝**8 件**（P1 6 件＋P2 2 件）。
- 判定口径：答案四键（expected_output|expected_rows|tests|rubric）全空＝真薄（P1）；expected_output 为占位文本（l1023-002 人工面发现，逃过 validator）＝语义薄（P2）。

## 第二批补题候选清单（文件×薄型×优先级）

### P1（高优先）：答案四键全空×2 型叠加（tests缺＋hints缺，judge_mode=ai_open 无判分锚）

| # | 文件 | topic | 薄型 | difficulty |
|---|---|---|---|---|
| 1 | content/python/22_statsmodels/04_multiple_ols_summary.yaml | 22_statsmodels | tests缺＋hints缺（四键全空） | 3 |
| 2 | content/python/22_statsmodels/05_logit_formula.yaml | 22_statsmodels | tests缺＋hints缺（四键全空） | 3 |
| 3 | content/python/23_sklearn_advanced/04_grid_search.yaml | 23_sklearn_advanced | tests缺＋hints缺（四键全空） | 4 |
| 4 | content/python/23_sklearn_advanced/05_classification_report.yaml | 23_sklearn_advanced | tests缺＋hints缺（四键全空） | 4 |
| 5 | content/python/22_hr_model/05_salary_prediction.yaml | 22_hr_model | tests缺＋hints缺（四键全空） | 3 |
| 6 | content/python/24_real_world_data/05_groupby_agg.yaml | 24_real_world_data | tests缺＋hints缺（四键全空） | 3 |

### P2（中优先）：expected_output 占位文本（tests缺，hints 在，judge=run 但输出不可判）

| # | 文件 | topic | 薄型 | 占位值 |
|---|---|---|---|---|
| 7 | content/python/02_conditionals/04_max_of_three.yaml | 02_conditionals | tests缺＋占位 expected_output | 「最大的那个数」 |
| 8 | content/python/02_conditionals/05_positive_check.yaml | 02_conditionals | tests缺＋占位 expected_output | 「positive / negative / zero 三选一」 |

## 域×topic 聚合（优先级视图）

| topic | P1 | P2 | 合计 | 补题建议 |
|---|---|---|---|---|
| 22_statsmodels | 2 | 0 | 2 | 补 rubric＋reference_answer＋hints（ai_open 轨，同 topic 01-03 老件为 run＋expected_output 形态，可二选一） |
| 23_sklearn_advanced | 2 | 0 | 2 | 同上 |
| 22_hr_model | 1 | 0 | 1 | 同 topic 01-04 为 ai_open＋rubric 4＋ref，照抄口径最稳 |
| 24_real_world_data | 1 | 0 | 1 | 同上（01-04 run＋expected_output） |
| 02_conditionals | 0 | 2 | 2 | 补 tests（stdin/expected 具体值）或改 expected_output 为具体输出 |
| **合计** | **6** | **2** | **8** | — |

## 注记（非候选，schema 合法）

- 84 件 tests缺 但答案键替代齐：judge=run＋expected_output 具体值（76 件）或 judge=ai_open＋rubric 在位（8 件：22_hr_model/01-04＋21_hr_viz/01-04）——判分链完整，不列第二批候选；其中 02_conditionals/04、05 两件因占位 expected_output 被 P2 单列，纯合法注记实为 82 件。若未来要做多 case stdin 覆盖属增强非补薄。
- 域级交叉印证：validate_content.py --domain python WARN 6 件与 P1 清单一一对应（l1023-002 证据在册）；P2 2 件为 validator 盲区（expected_output 键非空即过），已由 l1023-002 人工面点名。
