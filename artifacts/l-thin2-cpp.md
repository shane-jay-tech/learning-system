# l1023-010 薄题复核·cpp 域（第二批补题候选·文件级薄形态）

- 独立扫描（本单自扫，未复用 l1023-001 census 中间产物）：content/cpp/ 全量 67 yaml，三型薄形态判据：tests 键缺／hints 键空／difficulty 键空。
- 扫描结论：difficulty缺＝0 件；hints缺＝0 件；tests缺＝17 件——**17 件全部为 schema 合法替代（judge=run＋expected_output 具体字面值在位，缺 expected_output 者为 0），非薄**，与 l1023-005「17 件缺 tests 键退化判分观察备查」对位一致；答案四键全空＝0 件；expected_output 占位疑点 5 件经题面核验全部为合法程序输出（如 01_hello_world 题面即指定输出「Hello, World!」）。
- **真第二批候选＝0 件——本域无第二批候选。**

## 第二批补题候选清单（文件×薄型×优先级）

**无。** 三型薄形态（tests缺／hints缺／difficulty缺）经答案键替代复核后真候选清零；域内 67 件判分链完整（run 轨 100%：50 件带 tests 多 case＋17 件 expected_output 单 case 替代），validator --domain cpp WARN 0（本单实测复跑，与 l1023-005「六域唯一零 WARN」结论一致）。

## 域×topic 聚合（优先级视图）

| topic | P1 | P2 | 合计 | 说明 |
|---|---|---|---|---|
| —（全域） | 0 | 0 | 0 | 无补题候选；17 件 tests缺 属 run＋expected_output 合法替代，仅注记 |

## 注记（非候选，schema 合法）

- 17 件 tests缺 清单（run 轨单 case 替代，答案全为具体字面输出）：01_io_and_vars/01_hello_world（Hello, World!）、03_arrays_strings/06_reverse_words（olleh dlrow ppc）、06_iter_algo/06_custom_sort（-1 -1 3 4 5 -9）、07_pointers_class/04_unique_ptr（42）、07_pointers_class/05_shared_ptr（2）、08_inheritance/02_virtual（Woof!Meow!）、08_inheritance/05_virtual_dtor（Wrapper freed/Resource freed）、09_operator_overload/04_subscript（30）、10_templates/05_specialization（value: 42/value: "hi"）、12_file_io/02_count_lines（4）、12_file_io/03_sum_words（40）、12_file_io/04_check_open（not found）、12_file_io/05_append（first/second）、13_move_semantics/02_lvalue_rvalue（lvalue/rvalue）、13_move_semantics/03_move_count（1 1）、13_move_semantics/04_moved_state（5/true）、13_move_semantics/05_emplace（Hello/1）。
- 17 件若未来要升级为多 case tests 覆盖属**判分增强面**（单 case→多 case），非文件薄形态补题；l1023-005 已作「退化判分观察备查」在档，本单不重复列候选。
- 占位疑点核验记录：启发式 flagged 5 件（01_hello_world、03_reverse_string、08_inheritance/05_virtual_dtor、11_exceptions/02_what、12_file_io/01_write_read），逐件对照题面均为程序真实输出（01_hello_world 题面原文即含「Hello, World!」期望行），无一属 l1023-002 python 型占位文本缺陷。
- 域级观察：cpp 域无 ai_open 轨件（0/67），题面全为可机判程序输出题——域设计使然，非薄形态。
