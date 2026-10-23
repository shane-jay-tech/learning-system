# l1023-009 薄题复核·agent_dev 域（第二批补题候选·文件级薄形态）

- 独立扫描（本单自扫，未复用 l1023-001 census 中间产物）：content/agent_dev/ 全量 82 yaml，三型薄形态判据：tests 键缺／hints 键空／difficulty 键空。
- 扫描结论：difficulty缺＝0 件；**tests缺＝81 件（82 件中仅 05_modular_config/02_named_constant.yaml 带 tests 键）**——agent_dev 零 tests 键为域级判分双轨设计（judge=run→expected_output 对拍／judge=ai_open→rubric＋reference_answer，l1023-004 已留痕「ai_open 单轨」口径指题面形态、非 schema），其中 77 件答案链替代齐属 schema 合法（默认 run 轨 29 件全部 expected_output 在位／ai_open 轨 52 件中 48 件 rubric 在位），**非薄**；hints缺＝4 件。真第二批候选＝**4 件**（全 P1：答案四键全空＋hints缺叠加）。
- 占位疑点排除：06_frontier/01_mcp.yaml expected_output「Model Context Protocol」经人工面核验为**合法答案**（题面即要求输出英文全称且期望值写在题干），不属 python 域 l1023-002 型占位缺陷。

## 第二批补题候选清单（文件×薄型×优先级）

### P1（高优先）：答案四键全空×hints缺叠加（ai_open 轨无判分锚，与 validator WARN 4 一一对应）

| # | 文件 | topic | judge_mode | 薄型 | 难度 |
|---|---|---|---|---|---|
| 1 | content/agent_dev/07_data_security/05_prompt_injection_defense.yaml | 07_data_security | ai_open | tests缺＋rubric缺＋ref缺＋hints缺（四键全空） | 4 |
| 2 | content/agent_dev/08_read_code/05_read_code_flow.yaml | 08_read_code | ai_open | tests缺＋rubric缺＋ref缺＋hints缺（四键全空） | 3 |
| 3 | content/agent_dev/08_review_pr/05_pr_review_checklist.yaml | 08_review_pr | ai_open | tests缺＋rubric缺＋ref缺＋hints缺（四键全空） | 3 |
| 4 | content/agent_dev/10_debug_logs/05_log_level_strategy.yaml | 10_debug_logs | ai_open | tests缺＋rubric缺＋ref缺＋hints缺（四键全空） | 3 |

四件全部为 l1011 补题新增 05_ 件（6ccb551＝l1011-11/15 补 07_data_security/05；0ed67cc＝l1011-16/17/18 补 08_read_code、08_review_pr、10_debug_logs 各 1 题），与 l1023-004 补题验收「4 件新增 05_件 rubric/ref/hints 全空」点名互为交叉印证。

## 域×topic 聚合（优先级视图）

| topic | P1 | 合计 | 补题建议 |
|---|---|---|---|
| 07_data_security | 1 | 1 | ai_open 轨：按同 topic 01-04 口径补 rubric（3-4 条）＋reference_answer＋hints |
| 08_read_code | 1 | 1 | 同上 |
| 08_review_pr | 1 | 1 | 同上 |
| 10_debug_logs | 1 | 1 | 同上 |
| **合计** | **4** | **4** | — |

## 注记（非候选，schema 合法）

- 77 件 tests缺 但答案链替代齐：默认 judge=run＋expected_output 具体值（29 件，缺 expected_output 者为 0）或 judge=ai_open＋rubric 在位（48 件）——判分链完整，不列第二批候选；05_modular_config/02_named_constant.yaml 1 件带 tests 键另属完整形态。
- 域级观察：ai_open 轨缺 reference_answer（rubric 在位）共 14 件（上述 4 件 P1＋12_spec_iteration 5 件＋13_multi_round 5 件）——reference_answer 属可选辅助键、validator 不 WARN，不构成文件薄形态候选；若要统一补 ref 属增强面，留待内容班。
- 域级交叉印证：validate_content.py --domain agent_dev WARN 4 件与 P1 清单一一对应（本单实测）；占位疑点 1 件经题面核验排除，agent_dev 无 P2。
