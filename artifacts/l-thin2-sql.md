# l1023-011 薄题复核·sql 域（第二批补题候选·文件级薄形态）

- 独立扫描（本单自扫，未复用 l1023-001 census 中间产物）：content/sql/ 全量 60 yaml，三型薄形态判据：tests 键缺／hints 键空／difficulty 键空。
- 扫描结论：difficulty缺＝0 件；**tests缺＝60 件（全域）**——sql 域零 tests 键为域级设计（judge=run 全轨，答案键走 expected_rows 结果集对拍，60/60 在位），属 schema 合法替代**非薄**；答案四键全空＝0 件（expected_rows 即答案键）；hints缺＝6 件（与 validator WARN 6 一一对应，全部为 l1011 补题新增件 fc1a5cf＝l1011-12/13/14）。真第二批候选＝**6 件**（P1 1 件＋P2 5 件）。
- P1 特记：12_people_analytics/05_turnover_by_dept 除 hints缺 外另带 l1023-006 实锤缺陷——题面要求「按离职率降序」而 expected_rows 为 [sales 100.0, hr 0.0, eng 50.0] 非降序，判分不可通过；本单复核该矛盾**仍在**（文件自我1011 落库后未改动，git log 仅 fc1a5cf 一笔）。

## 第二批补题候选清单（文件×薄型×优先级）

### P1（高优先）：hints缺＋判分矛盾叠加（判分链断裂，修复前该题不可能通过）

| # | 文件 | topic | judge_mode | 薄型 | 难度 |
|---|---|---|---|---|---|
| 1 | content/sql/12_people_analytics/05_turnover_by_dept.yaml | 12_people_analytics | run | hints缺＋题面降序×expected_rows 行序矛盾（l1023-006 实锤，本单复核仍在） | 3 |

### P2（中优先）：hints缺 单型（答案链 expected_rows 完整，validator WARN 对应）

| # | 文件 | topic | 薄型 | 难度 |
|---|---|---|---|---|
| 2 | content/sql/01_select_where/03_where_gt.yaml | 01_select_where | hints缺 | 1 |
| 3 | content/sql/01_select_where/04_where_and.yaml | 01_select_where | hints缺 | 1 |
| 4 | content/sql/01_select_where/05_order_limit.yaml | 01_select_where | hints缺 | 2 |
| 5 | content/sql/02_aggregate/04_group_by.yaml | 02_aggregate | hints缺 | 2 |
| 6 | content/sql/02_aggregate/05_having_avg.yaml | 02_aggregate | hints缺 | 3 |

六件全部为 l1011 补题新增件（fc1a5cf：sql/01 +3、sql/02 +2、sql/12 +1——l1011-12/13/14）；同 topic 老件（01/02 等基础件）hints 在位，缺失集中于 l1011 批。

## 域×topic 聚合（优先级视图）

| topic | P1 | P2 | 合计 | 补题建议 |
|---|---|---|---|---|
| 12_people_analytics | 1 | 0 | 1 | 修 expected_rows 行序为降序（sales 100.0 → eng 50.0 → hr 0.0）或改题面为升序口径，二选一对齐；并补 hints |
| 01_select_where | 0 | 3 | 3 | 补 hints（参照同 topic 老件 01/02 口径 2-3 条） |
| 02_aggregate | 0 | 2 | 2 | 同上 |
| **合计** | **1** | **5** | **6** | — |

## 注记（非候选，schema 合法）

- 60 件 tests缺 但答案键 expected_rows 全在位（60/60，含 setup_sql 建表脚本），判分链结构完整——sql 域零 tests 键与 r 域同属域级设计（r 走 expected_output/rubric 双轨、sql 走 expected_rows 单轨），不列候选。
- 域级交叉印证：validate_content.py --domain sql WARN 6 件（全部「缺 hints」）与 P1＋P2 清单六件一一对应（本单实测）；l1023-006 补题验收「6 件补题件缺 hints WARN」与「05_turnover_by_dept 题面降序与 expected_rows 行序矛盾判分不可通过实锤点名」两结论均与本单文件级扫描对位一致。
- 占位疑点：启发式扫描 expected_output 占位 0 件（sql 域无 expected_output 键使用）。
