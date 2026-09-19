# agent_dev 48 道 rubric 题 R1-R3 规范对账（2026-09-19 晨间执行班，任务 l918-17，只读）

> 锚点：`agent-dev-rubric-review-20260905.md:49` R1/R3 定义。方法论：R1=评分项含模糊词（清晰/深入/合理/准确/良好/恰当/适当/完善/充分/有效）且无数值兜底＝裸用违例；R3=全部评分项均无可引用文本特征锚（含/列出/提及/≥/行/条/清单…）＝违例。

## 一、总判定

| 项 | 值 |
|---|---|
| rubric 题总数 | **48** |
| R1 违例（模糊词裸用） | **2** |
| R3 违例（无文本特征锚） | **21** |

## 二、R1 违例清单

| id | 裸用词 |
|---|---|
| agent_dev/09_decompose/04_dependency_order | 合理 |
| agent_dev/10_debug_logs/01_read_traceback | 合理 |

## 三、R3 违例清单（21）

- content/agent_dev/05_modular_config/06_why_layers
- content/agent_dev/07_data_security/01_spot_pii
- content/agent_dev/07_data_security/02_hardcoded_key
- content/agent_dev/07_data_security/03_anon_vs_pseudo
- content/agent_dev/07_write_spec/01_feature_spec
- content/agent_dev/08_read_code/02_find_bug_mutable
- content/agent_dev/08_review_pr/01_spot_missing_test
- content/agent_dev/08_review_pr/02_spot_security_issue
- content/agent_dev/08_review_pr/03_review_naming
- content/agent_dev/08_review_pr/04_review_error_handling
- content/agent_dev/09_decompose/01_split_login
- content/agent_dev/09_decompose/02_split_dashboard
- content/agent_dev/09_decompose/03_estimate_effort
- content/agent_dev/09_decompose/05_decompose_simple
- content/agent_dev/10_debug_logs/02_layer_diagnosis
- content/agent_dev/10_debug_logs/03_interpret_error_codes
- content/agent_dev/11_real_tasks/02_write_bug_report
- content/agent_dev/11_real_tasks/06_emergency_rollback
- content/agent_dev/12_spec_iteration/01_diagnose_bad_spec
- content/agent_dev/13_multi_round/04_scope_negotiation
- content/agent_dev/13_multi_round/05_full_iteration

聚集性：08_review_pr 4/4 全违例、07_data_security 3/4、09_decompose 4/5、10_debug_logs 3/4——「评审/找茬/拆解」类主观题最缺证据锚，整改优先补「回复须含三分类清单/行号引用」式锚。

## 四、48 题逐题判定表

| 题 | R1 | R3 |
|---|---|---|
| content/agent_dev/03_spec_writing/06_open_write_spec | ✓ | ✓ |
| content/agent_dev/05_modular_config/06_why_layers | ✓ | ⚠ |
| content/agent_dev/05_modular_config/07_coupling | ✓ | ✓ |
| content/agent_dev/05_modular_config/08_change_safely | ✓ | ✓ |
| content/agent_dev/07_data_security/01_spot_pii | ✓ | ⚠ |
| content/agent_dev/07_data_security/02_hardcoded_key | ✓ | ⚠ |
| content/agent_dev/07_data_security/03_anon_vs_pseudo | ✓ | ⚠ |
| content/agent_dev/07_data_security/04_minimization_case | ✓ | ✓ |
| content/agent_dev/07_write_spec/01_feature_spec | ✓ | ⚠ |
| content/agent_dev/07_write_spec/02_api_spec | ✓ | ✓ |
| content/agent_dev/07_write_spec/03_bug_report_spec | ✓ | ✓ |
| content/agent_dev/07_write_spec/04_refactor_spec | ✓ | ✓ |
| content/agent_dev/07_write_spec/05_spec_for_bugfix | ✓ | ✓ |
| content/agent_dev/08_read_code/01_what_does_it_do | ✓ | ✓ |
| content/agent_dev/08_read_code/02_find_bug_mutable | ✓ | ⚠ |
| content/agent_dev/08_read_code/03_edge_case | ✓ | ✓ |
| content/agent_dev/08_read_code/04_silent_error | ✓ | ✓ |
| content/agent_dev/08_review_pr/01_spot_missing_test | ✓ | ⚠ |
| content/agent_dev/08_review_pr/02_spot_security_issue | ✓ | ⚠ |
| content/agent_dev/08_review_pr/03_review_naming | ✓ | ⚠ |
| content/agent_dev/08_review_pr/04_review_error_handling | ✓ | ⚠ |
| content/agent_dev/09_decompose/01_split_login | ✓ | ⚠ |
| content/agent_dev/09_decompose/02_split_dashboard | ✓ | ⚠ |
| content/agent_dev/09_decompose/03_estimate_effort | ✓ | ⚠ |
| content/agent_dev/09_decompose/04_dependency_order | ⚠ 合理 | ✓ |
| content/agent_dev/09_decompose/05_decompose_simple | ✓ | ⚠ |
| content/agent_dev/10_debug_logs/01_read_traceback | ⚠ 合理 | ✓ |
| content/agent_dev/10_debug_logs/02_layer_diagnosis | ✓ | ⚠ |
| content/agent_dev/10_debug_logs/03_interpret_error_codes | ✓ | ⚠ |
| content/agent_dev/10_debug_logs/04_write_debug_prompt | ✓ | ✓ |
| content/agent_dev/11_real_tasks/01_review_pr_diff | ✓ | ✓ |
| content/agent_dev/11_real_tasks/02_write_bug_report | ✓ | ⚠ |
| content/agent_dev/11_real_tasks/03_diagnose_error | ✓ | ✓ |
| content/agent_dev/11_real_tasks/04_iterative_instruction | ✓ | ✓ |
| content/agent_dev/11_real_tasks/05_decompose_feature | ✓ | ✓ |
| content/agent_dev/11_real_tasks/06_emergency_rollback | ✓ | ⚠ |
| content/agent_dev/11_real_tasks/07_scope_creep | ✓ | ✓ |
| content/agent_dev/11_real_tasks/08_end_to_end | ✓ | ✓ |
| content/agent_dev/12_spec_iteration/01_diagnose_bad_spec | ✓ | ⚠ |
| content/agent_dev/12_spec_iteration/02_rewrite_vague_spec | ✓ | ✓ |
| content/agent_dev/12_spec_iteration/03_agent_went_wrong | ✓ | ✓ |
| content/agent_dev/12_spec_iteration/04_spec_vs_agent_bug | ✓ | ✓ |
| content/agent_dev/12_spec_iteration/05_iterative_refinement | ✓ | ✓ |
| content/agent_dev/13_multi_round/01_requirement_change | ✓ | ✓ |
| content/agent_dev/13_multi_round/02_regression_fix | ✓ | ✓ |
| content/agent_dev/13_multi_round/03_priority_triage | ✓ | ✓ |
| content/agent_dev/13_multi_round/04_scope_negotiation | ✓ | ⚠ |
| content/agent_dev/13_multi_round/05_full_iteration | ✓ | ⚠ |

## 五、零改动声明

只读 yaml 解析；content 零改动；python -m pytest tests -q 数值不变（404 passed, 7 skipped）；未 push。
