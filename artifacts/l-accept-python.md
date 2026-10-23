# l1023-002 补题验收·python 域（l1011 批 5 个补题 topic 现值验收）

- 复扫基线：artifacts/l-census-1023.json（l1023-001，commit 56aaea7）；content/python/ 现值 136 yaml 与锚点一致。
- 上批补题 topic 定位：l1011-02..06（done/ result 执行摘要），共 5 个 python topic。
- 验收基准：每 topic ≥5 题；difficulty 1-5 分布非退化（非单值）；tests stdin/expected 自洽抽检 2 题/topic。

## topic 级验收表（三面）

| topic | 题量(≥5) | 难度直方(非退化) | 测试/答案面抽检（2 题/topic） | 判定 |
|---|---|---|---|---|
| 02_conditionals | 5 ✓ | {1:2, 2:2, 3:1} ✓ | 01_odd_even：tests n=1，stdin/expected 齐，与顶层 expected_output 归一化一致 ✓；04_max_of_three：无 tests，expected_output=「最大的那个数」占位文本 ✗ | 局部不合格（点名 04/05，见下） |
| 22_hr_model | 5 ✓ | {2:1, 3:3, 4:1} ✓ | 01_logistic_turnover：judge_mode=ai_open，rubric 4 条＋reference_answer ✓；05_salary_prediction：答案四键全空＋缺 hints ✗ | 局部不合格（点名 05） |
| 22_statsmodels | 5 ✓ | {2:1, 3:3, 4:1} ✓ | 02_r_squared：expected_output=「R² = 0.9994」具体值＋hints ✓；05_logit_formula：四键全空＋缺 hints ✗ | 局部不合格（点名 04/05） |
| 23_sklearn_advanced | 5 ✓ | {3:2, 4:3} ✓（两档，非单值） | 01_cross_validation：expected_output=「平均准确率: 0.960」＋hints ✓；04_grid_search：四键全空＋缺 hints ✗ | 局部不合格（点名 04/05） |
| 24_real_world_data | 5 ✓ | {2:2, 3:2, 4:1} ✓ | 01_missing：expected_output=「1」＋hints ✓；05_groupby_agg：四键全空＋缺 hints ✗ | 局部不合格（点名 05） |

## 不合格明细（7 件，validator WARN/占位交叉印证）

1. content/python/02_conditionals/04_max_of_three.yaml — 无 tests；expected_output 为占位文本「最大的那个数」，judge-by-output 不可判；无 rubric/reference_answer/judge_mode。
2. content/python/02_conditionals/05_positive_check.yaml — 无 tests；expected_output 为描述性文本「positive / negative / zero 三选一」；无 rubric/reference_answer/judge_mode。
3. content/python/22_hr_model/05_salary_prediction.yaml — 答案四键（expected_output|expected_rows|tests|rubric）全空＋缺 hints（validator WARN 在册）。
4. content/python/22_statsmodels/04_multiple_ols_summary.yaml — 同上（WARN 在册）。
5. content/python/22_statsmodels/05_logit_formula.yaml — 同上（WARN 在册）。
6. content/python/23_sklearn_advanced/04_grid_search.yaml — 同上（WARN 在册）。
7. content/python/23_sklearn_advanced/05_classification_report.yaml — 同上（WARN 在册）。
8. content/python/24_real_world_data/05_groupby_agg.yaml — 同上（WARN 在册）。

（1、2 件逃过 validator WARN 是因为 expected_output 键非空——占位文本也能过「四键非全空」检查；语义占位需人工面验收，本单点名。）

## 域级门禁证据

- `python scripts/validate_content.py --domain python` → PASS｜文件 136／解析错误 0／字段 ERROR 0／字段 WARN 6／同名组 2（6 个 WARN 与上表 3-8 号不合格件一一对应；2 组 basename 同名＝by design）。
- 合格面结论：题量与难度两面 5/5 topic 全达标；测试/答案面 25 件补题文件中 8 件存在答案键缺陷（6 件四键全空＋2 件占位 expected_output），且全部集中在 l1011 新增件（01-04 老件无此问题）。

## 处置建议（留待内容班，本单零改动）

- 6 件四键全空件：按同 topic 老件口径补 judge_mode/rubric/reference_answer 或 expected_output＋hints。
- 02_conditionals/04、05 两件：补 tests（stdin/expected 具体值）或改 expected_output 为具体输出。
- 修复后复跑 `python scripts/validate_content.py --domain python` 应 WARN 6→0。
