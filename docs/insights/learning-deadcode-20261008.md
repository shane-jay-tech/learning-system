# learning-system 死码候选普查（l1010-39，2026-10-08）

> 口径：core/＋ui/＋scripts/＋app.py/launcher.pyw 全部模块级 `def/class`（非下划线开头），
> 全仓词边界引用（py/md/pyw，排除 tmp），外引=0 者入围。四层＝A 全死 / B 仅内部用 /
> C tests-only / D 内部+tests。判题域（core/judge、core/runners、core/loader）删前须材料单。
> 零删码——本档只交裁决。复现：rg -U -c "\b<sym>\b" --glob "!tmp/**" -g "*.py" -g "*.md" .

## 总计

零外引符号 **64**：A 1／B 22／C 2／D 39。抽验 60 个 rg 全量复核（超 ≥40 门槛），低命中复核一致。

## A 类（确认死，1）

| 符号 | 位置 | 说明 |
|---|---|---|
| apply_all | scripts/mark_r_judge_plain.py | own=1/tests=0；同文件实际批处理走 prepare_all→commit_all 链，apply_all 为孤儿分支 |

## C 类（tests-only，2）

| 符号 | 位置 | 说明 |
|---|---|---|
| get_load_diagnostics | core/loader.py:own=1/tests=12 | **生产面零调用**（app/ui 均不取）——12 例测试在养一个没人用的诊断口；删须先裁测试去向 |
| apply_one | scripts/mark_r_judge_plain.py | 单条迁移入口，仅测试引用 |

## B 类（仅内部用，22 摘要）

scripts 工具函数为主：generate_system_report 系 7（count_lessons/count_paths/count_problems/count_source_lines/get_paths_detail/get_version/print_metrics）、mark_r_judge_plain 系 5（begin_commit/prepare_one/r_dir/txn_root/recover_pending）、probe_tags 系 3（canon2/distinct/lev）、backup 系 2（list_backups/prune_backups）、bench_pages 2（bench/Ctx）、audit_paths 2（disk_topics/load_paths）、core 1（to_editor_line）。均「脚本自用＋零测试」，删除收益低（脚本工具面）。

## D 类（内部+tests，39 摘要）

大头是**判题域内部构件**（headline/locate/locate_column/timeout_budget＝error_feedback 解析链；JudgeResult/LoadDiag/Problem＝核心数据类；launcher 生命周期函数）与 scripts 的「实现函数＋对应测试」对（mark_r_judge_plain 的迁移事务族、import_dry_run 校验族、generate_system_report.check_readme 等）。**判读**：Python 脚本/应用无 export 概念，own>1 即「被本模块主流程消费」——D 类在本仓不构成过度导出问题，反是测试挂接点；**不建议作为收窄对象**。

## 判题域红线

core/judge.py、core/loader.py、core/runners/*（含上表 JudgeResult/LoadDiag/Problem/get_load_diagnostics/headline/locate/locate_column/timeout_budget/backfill/to_editor_line）一律**删前须材料单**（判分链路，r5 口径红线延伸）。

## 与 kaoyan 批方法的关系

kaoyan k1010-36 方法档四轴（own/外引/tests/scripts）在本仓的适配版；差异＝Python 无 export 关键字，own>1 即视同内部消费（无「过度导出」形态），故本仓 A/C 才有处置意义。
