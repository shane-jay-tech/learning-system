# l1023-003 补题验收·r 域（l1011 批 5 个补题 topic 现值验收）

- 复扫基线：artifacts/l-census-1023.json（l1023-001，commit 56aaea7）；content/r/ 现值 92 yaml 与锚点一致。
- 上批补题 topic 定位：l1011-07..11（done/ result 执行摘要），共 5 个 r topic。
- 验收基准：每 topic ≥5 题；difficulty 1-5 分布非退化；测试自洽抽检 2 题/topic。
- 口径修正（留痕）：r 域全 92 件零 tests 键＝域级判分走 judge_mode 双轨（run→R runner 与 expected_output 对拍；ai_open→rubric＋reference_answer），任务书「tests 的 stdin/expected 自洽」按域实况修正为「判分键自洽」（judge_mode 在位＋expected_output 具体值 或 rubric/reference_answer 齐备）。

## topic 级验收表（三面）

| topic | 题量(≥5) | 难度直方(非退化) | 判分键自洽抽检（2 题/topic） | 判定 |
|---|---|---|---|---|
| 01_vectors_and_basics | 5 ✓ | {1:1, 2:4} ✓ | 01_hello_world：run＋expected_output「Hello, World!」具体值＋hints ✓；05_vector_filter：run＋「[1] 15 22 17」＋hints ✓ | 合格 |
| 02_logic_and_summary | 5 ✓ | {1:1, 2:4} ✓ | 01_mean：run＋「87.6」＋hints ✓；05_ifelse_vector：run＋「[1] "Fail" "Pass" …」＋hints ✓ | 合格 |
| 14_real_world_data | 5 ✓ | {2:2, 3:2, 4:1} ✓ | 01_missing：run＋「1」＋hints ✓；05_outlier_detect：judge_mode=run 但答案四键全空 ✗ | 局部不合格（点名 05） |
| 14_sem_basics | 5 ✓ | {2:3, 3:1, 4:1} ✓ | 01_sem_concept：ai_open＋rubric 4 条＋reference_answer ✓；05_sem_model_fit：ai_open 但四键全空＋缺 hints ✗ | 局部不合格（点名 05） |
| 15_cfa | 5 ✓ | {1:1, 2:1, 3:2, 4:1} ✓ | 01_alpha_concept：ai_open＋rubric 4 条＋reference_answer ✓；05_modification_indices：ai_open 但四键全空＋缺 hints ✗ | 局部不合格（点名 05） |

## 不合格明细（3 件，validator WARN 交叉印证）

1. content/r/14_real_world_data/05_outlier_detect.yaml — 答案四键全空（hints 2 条在）；judge_mode=run 无 expected_output 可对拍（validator WARN 在册）。
2. content/r/14_sem_basics/05_sem_model_fit.yaml — 答案四键全空＋缺 hints；ai_open 无 rubric/reference_answer（validator WARN 在册）。
3. content/r/15_cfa/05_modification_indices.yaml — 答案四键全空＋缺 hints；同上（validator WARN 在册）。

三件全部是 l1011 新增 05_ 件；l1011-07/08 三件新增（03_vector_ops/04_vector_names/05_vector_filter、04_median_range/05_ifelse_vector）抽检全过。

## 域级门禁证据

- `python scripts/validate_content.py --domain r` → PASS｜文件 92／解析错误 0／字段 ERROR 0／字段 WARN 3／同名组 0（3 个 WARN 与上表不合格件一一对应）。
- 合格面结论：题量与难度两面 5/5 topic 全达标；判分键面 25 件补题文件中 3 件四键全空，全部集中在 l1011 新增 05_ 件。

## 处置建议（留待内容班，本单零改动）

- 05_outlier_detect：按同 topic run 轨口径补 expected_output（IQR 法的具体输出值）；05_sem_model_fit、05_modification_indices：按 sem/cfa 老件 ai_open 轨口径补 rubric（3-4 条）＋reference_answer，并补 hints。
- 修复后复跑 `python scripts/validate_content.py --domain r` 应 WARN 3→0。
