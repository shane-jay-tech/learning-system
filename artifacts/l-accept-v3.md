# 补题验收三版（l1025-015 · 2026-10-26 · 批2 落地后五域抽检）

> 基准：三键齐（statement/topic/difficulty）／答案四键非空／hints 在／难度非退化；抽样 seed=42 每域 2 件。零改档零改码。

## 一、批2 落地面验收（l1025-001..004，8 件）

| 件 | 处置 | 验收 |
|---|---|---|
| 22_statsmodels/04、05 | 补三键＋新建数据基座 2 CSV | 三键在位；ref 实跑（OLS p<0.05=True／logit age 系数正）✓ |
| 23_sklearn_advanced/04、05 | 补三键＋新建 ml_dataset.csv | ref 实跑（grid best 0.905／f1 0.878）✓ |
| 22_hr_model/05、24_real_world_data/05 | 补三键（＋sales_data.csv） | ref 实跑 ✓（R²=-0.038 系合成数据诚实输出，ai_open 轨） |
| 02_conditionals/04、05 | 占位 expected_output→tests 多用例 | 正解全用例过（4/4、3/3）✓ |

python 域薄面 **6→0**（validator python WARN 0，census_python 5/5）；答案字段计数钉/直方钉/judge 钉全部翻正至实测终值。

## 二、五域抽检表（10 件 seed=42）

| 域 | 抽样 | 必填 | 答案键 | hints | 难度 | 判 |
|---|---|---|---|---|---|---|
| python | 04_replace／02_grade | 齐 | expected_output+tests | 有 | 2/2 | 合格 |
| r | 06_interpret_output／02_tidy_coef | 齐 | rubric／expected_output | 有 | 1/2 | 合格 |
| agent_dev | 08_change_safely／02_name_collision | 齐 | rubric／expected_output | 有 | 3/2 | 合格 |
| cpp | 04_word_count／02_vector_max | 齐 | expected_output+tests | 有 | 2/2 | 合格 |
| sql | 03_correlated_count／03_running_sum | 齐 | expected_rows | 有 | 3/3 | 合格 |

**抽样 10/10 合格**；难度 1-3 非退化。

## 三、域级不合格点名（13 件，批2 范围外存量）

- python **0**、cpp **0**（批2 后清零域）
- r **3**：14_real_world_data/05（四键全空）、14_sem_basics/05、15_cfa/05（四键全空＋缺 hints）
- agent_dev **4**：07_data_security/05、08_read_code/05、08_review_pr/05、10_debug_logs/05（四键全空＋缺 hints）
- sql **6**：01_select_where/03、04、05＋02_aggregate/04、05＋12_people_analytics/05（缺 hints）

## 四、结论

批2 获批面（python 8 件）**全达标**；五域抽检 10/10 合格、无新增退化；不合格面＝r/ad/sql 13 件存量薄（批1/批2 范围外，l1023-019 档扩题候选车道），python census 钉已与盘面闭合（l1025-003/004），其余域钉翻正归 l1025-006 归因档的「域 census 钉值翻正批」。
