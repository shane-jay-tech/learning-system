# l1023-008 薄题复核·r 域（第二批补题候选·文件级薄形态）

- 独立扫描（本单自扫，未复用 l1023-001 census 中间产物）：content/r/ 全量 92 yaml，三型薄形态判据：tests 键缺／hints 键空／difficulty 键空。
- 扫描结论：difficulty缺＝0 件；**tests缺＝92 件（全域）**——r 域零 tests 键为域级设计（判分走 judge_mode 双轨：run→expected_output 对拍／ai_open→rubric＋reference_answer，l1023-003 已留痕），其中 89 件答案键替代齐属 schema 合法（run＋expected_output 75 件／ai_open＋rubric 14 件），**非薄**；hints缺＝2 件。真第二批候选＝**3 件**（全 P1：答案四键全空）。

## 第二批补题候选清单（文件×薄型×优先级）

### P1（高优先）：答案四键全空（判分链断裂，与 validator WARN 3 一一对应）

| # | 文件 | topic | judge_mode | 薄型 | 难度 |
|---|---|---|---|---|---|
| 1 | content/r/14_real_world_data/05_outlier_detect.yaml | 14_real_world_data | run | tests缺＋expected_output 缺（四键全空；hints 2 条在） | 3 |
| 2 | content/r/14_sem_basics/05_sem_model_fit.yaml | 14_sem_basics | ai_open | tests缺＋hints缺（四键全空） | 4 |
| 3 | content/r/15_cfa/05_modification_indices.yaml | 15_cfa | ai_open | tests缺＋hints缺（四键全空） | 4 |

三件全部为 l1011 补题新增 05_ 件（l1011-09/10/11）。

## 域×topic 聚合（优先级视图）

| topic | P1 | 合计 | 补题建议 |
|---|---|---|---|
| 14_real_world_data | 1 | 1 | run 轨：按同 topic 01-04 口径补 expected_output（IQR 法具体输出值） |
| 14_sem_basics | 1 | 1 | ai_open 轨：按同 topic 01-04 口径补 rubric（3-4 条）＋reference_answer＋hints |
| 15_cfa | 1 | 1 | 同上（01-04 ai_open＋rubric 4＋ref） |
| **合计** | **3** | **3** | — |

## 注记（非候选，schema 合法）

- 89 件 tests缺 但答案键替代齐：judge=run＋expected_output 具体值（75 件）或 judge=ai_open＋rubric 在位（14 件）——判分链完整，不列第二批候选。
- 域级先例一致性：l1023-003 补题验收已点名此 3 件（当时结论「3/5 topic 局部不合格」）；本单文件级扫描与该结论互为交叉印证，候选集合一致。
- 域级观察：r 域高难度偏薄（全域 4 档仅 3 件、无 5 档），属难度梯度规划面非文件薄形态，不列入本单候选。
