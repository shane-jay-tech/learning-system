# l1023-005 补题验收·cpp 域（补题 topic 现值验收·67 文件）

- 复扫基线：artifacts/l-census-1023.json（l1023-001，commit 56aaea7）；content/cpp/ 现值 67 yaml 与锚点一致。
- 上批补题定位（锚点漂移修正，留痕）：l1011-02..19 批 result 中**无 cpp 行**——cpp 域 5 件补题实源为 fd7c6dd（2026-10-21 工作区快照）带入的他班新题：01_io_and_vars 补 3 件（03_swap_two_ints / 04_total_price / 05_seconds_hms）、02_branch_loop 补 2 件（04_factorial / 05_sum_even），该归属已被 l1023-015（commit 06dc7fc）留痕确认（EXPECTED_PROBLEMS 62→67 翻正）。本单按此 2 个补题 topic 验收。
- 验收基准：每 topic ≥5 题；difficulty 1-5 分布非退化；tests 的 stdin/expected 自洽抽检 2 题/topic。
- 运行级口径（留痕）：本机无 g++（command not found），run 级判分执行不可复演；自洽抽检以结构面（tests stdin/expected 齐＋与顶层 expected_output 经 core.judge._normalize 归一化一致）＋l1023-015 同日钉值测试全绿（judge_mode run×67、expected_output 67/67 覆盖）为判据。

## topic 级验收表（三面）

| topic | 题量(≥5) | 难度直方(非退化) | tests 自洽抽检（2 题/topic） | 判定 |
|---|---|---|---|---|
| 01_io_and_vars | 5 ✓（含补题 3 件） | {1:1, 2:3, 3:1} ✓ | 03_swap_two_ints：tests n=1 stdin/expected 齐＋与顶层一致 ✓；05_seconds_hms：同 ✓ | 合格 |
| 02_branch_loop | 5 ✓（含补题 2 件） | {1:1, 2:3, 3:1} ✓ | 04_factorial：tests n=1 stdin/expected 齐＋与顶层一致 ✓；05_sum_even：同 ✓ | 合格 |

## 域级门禁与观察

- `python scripts/validate_content.py --domain cpp` → PASS｜文件 67／解析错误 0／字段 ERROR 0／**字段 WARN 0**／同名组 0——六域中唯一零 WARN 域。
- `python -m pytest tests/test_content_census_cpp.py -q`（l1023-015 同日翻正后 5 passed 全绿留痕，commit 06dc7fc）：judge_mode 全 run×67、expected_output 67/67 全覆盖、tests 形态 50 list＋17 缺键。
- 域级观察（非补题 topic 缺陷，记录备查）：17 件缺 tests 键（12_file_io 4、13_move_semantics 4、07_pointers_class 2、08_inheritance 2、09_operator_overload 1、10_templates 1、01_io_and_vars/01、03_arrays_strings/06、06_iter_algo/06 各 1）——judge.py:261 `tests or [{}]` 退化为「空 stdin 单例＋顶层 expected_output」判分，功能不失效但无多 case stdin 覆盖；是否补 tests 属内容班规划面。

## 处置建议（本单零改动）

- 补题 topic 两面全绿，无需处置。
- 17 件缺 tests 键件若需多 case 覆盖，按同 topic 已有 tests 件口径补 stdin/expected 列表；与 l1023-015 钉值「50+17」联动翻新。
