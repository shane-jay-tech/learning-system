# learning SQL 行序题处置设计稿：出口 A/B/C 可行性对照（l923-23，2026-09-23，零改动）

- 任务：`l923-23`（cwd `D:\code\learning-system`，执行班 `qoder-executor-20260923-0022-learn7`，软预算 ≤30 分钟）
- 性质：**只出设计稿**。本档不改判分码、不改题面、不动 `tests/`；出口 B 命中判分红线，**只给建议，等拍板**。
- 上游：`docs/insights/learn-sql-roworder-census-20260922.md`（l922-129 普查）给出三类清单与三条出口的**雏形**；
  本档把三条出口做成可比项，并修正上游三处口径（见 §六）。
- 基线：HEAD `c3ac33a`；取数时刻 2026-09-23T12:40+08:00；工作树含本班 l923-21/22 在途件（与本档目标无交集）。
- **所有数字绑磁盘实取、可整段复算**：复跑 `PYTHONPATH=. PYTHONIOENCODING=utf-8 python tmp/l923-23/census_probe.py`
  （探针直接 import l922-129 桩自己的 `_measure` / `_multi_row_sql_problems` / `_strip_toplevel_order`，**不另起口径**）。

## 一、决策要解决的问题（一句话＋判分实现锚点）

判分器按**位置**逐行逐格比对（`core/judge.py:96-100` `_rows_equal`，`:219` 调用，`:215` 的分支门是
`pdict.get("expected_rows") is not None`），而无 top-level `ORDER BY` 的查询 sqlite **不保证行序** ⇒
题面写了排序要求、`expected_rows` 又按位置比，等于在考「学员猜中引擎返回序」。
现状由 `tests/test_sql_roworder_fragile.py::test_多行SQL题行序全部承重`（`xfail(strict=True)`）钉着。

**本单复核的判分面锚点（全部有效，无漂移）**：

| 锚点 | 磁盘实况 | 用途 |
|---|---|---|
| `core/judge.py:96-100` | `def _rows_equal` → `:97` 行数不等先短路、`:99-100` `zip()` 逐行逐格 | 三出口共同改动点 |
| `core/judge.py:215` | `if pdict.get("expected_rows") is not None:` 分支门 | B 的落点（**语言无关**，见 §二.2） |
| `core/judge.py:219-227` | 不等时给 `diff_hint`，末句「请检查 SELECT 字段顺序与 ORDER BY」 | A/B 都会牵动这条反馈文案 |
| `core/judge.py:103` | `_first_diff_cell()` 首差定位（按行号/列号） | B 改集合比较后**该函数语义要重定义** |
| `core/loader.py:33`／`:218` | `Problem.reference_answer` 字段与装配 | C 的落点，**零 schema 改动** |

## 二、三出口共同的事实底座（本单现取读数）

1. **覆盖面**：sql 题 54 道，`expected_rows >= 2` 者 **42** 道；行数直方
   `{1:12, 2:10, 3:14, 4:7, 5:9, 6:1, 7:1}`（12＋42＝54 自洽）。与上游 42 逐字一致。
2. 🔴 **`expected_rows` 是 sql 独占字段**（本单新查，上游未记）：python 125 题／cpp 62 题／r 84 题／agent_dev 78 题
   带 `expected_rows` 者**全为 0**。⇒ 出口 B 动 `:215` 分支的爆炸半径**只在 sql**，
   且这条不变量已被两处在册守卫钉住：`tests/test_content_census_python.py:76`（「python 题库不产出 expected_rows」）、
   `tests/test_content_census_r.py:46`（机判字段 schema 版本 1＝不引入）。
3. **机验面 11/42**：只有 11 道多行题的 `hints` 里有可整条执行且逐行等于期望的参考解。其中
   - **不承重（fragile）7 道**：`03_orderby_having/03_distinct_grades`、`04_joins/05_join_groupby`、
     `05_subqueries_case/01_above_avg`、`05_subqueries_case/02_in_subquery`、
     `06_window_functions/01_rank_in_class`、`06_window_functions/04_lag`、`07_cte/01_simple_cte`；
   - 承重已证 **3 道**：`03_orderby_having/01_order_desc`、`06_window_functions/02_class_avg`、`09_string_funcs/01_length`；
   - **不可剥 1 道**：`03_orderby_having/02_lowest_2`（参考解含 top-level `LIMIT`，剥 `ORDER BY` 会换行集 ⇒ 不可比）。
   ⇒ 三出口都要回答「余下 31 道未测」这段失明面由谁收。
4. **`reference_answer` 现状**：sql 侧 **54/54 全空**；但它**不是新字段**——agent_dev 38 题、python 8 题、r 14 题在用，
   cpp 0 题。⇒ 出口 C 是**内容补录**，不是工程新建。
5. **骨架与提示面**：42 道多行题里 `starter_code` 真代码含 `ORDER BY` 的 **0** 道（剔 `--` 注释后），
   `hints` 含 `ORDER BY` 的 **26/42** ⇒ 「题面要某个序、骨架与提示都不给」的 16 道是误判高发区。

## 三、三出口对照表（完成标准 ①）

| 维度 | **A 补题面排序键＋方向** | **B 排序语义题绑 ORDER BY／集合题改行集合比较** | **C 补 `reference_answer`** |
|---|---|---|---|
| 动的东西 | `content/sql/*/*.yaml` 的 `statement` 文案（乙类 6 条） | `core/judge.py:215-227` 比较分支 ＋ 受影响题的题面／`expected_rows` | `content/sql/*/*.yaml` 新增键值（42 道多行题，或全 54 道） |
| 判分口径 | **不变**（红线不动） | 🔴 **变更**＝命中红线，需产品拍板 | **不变** |
| 工作量估计 | **极小**：6 条 × 1 句文案；0 处代码；0 处测试改写 | **大**：判分分支改写 ＋ 首差定位重定义 ＋ 反馈文案改写 ＋ 下节 15 例测试重做 ＋ 42 道题逐题归类（有语义／集合） | **中且可分批**：42 条参考解（其中 11 条 hints 里已有可执行解，可直接搬；余 31 条要写）；0 处代码 |
| 消除的误判面 | 只消「乙类 6 条题面含糊」；**7 道 fragile 一条不消** | 唯一真正消除 fragile 误判面的出口（含 `01_rank_in_class`／`04_lag` 两条语义题） | **不消除**任何误判，只把「是否承重」从 11/42 测到 42/42 |
| 引入的新风险 | 文案改了但判分照旧 ⇒ **假收口**（读者以为题面已承重） | 「行集合比较」会把**真该有序**的题判松（l921-03 正是为此自纠过一条假发现）；`_first_diff_cell` 的行列号反馈在集合语义下失真 | 参考解写错＝把机验面变成**错答案的自证**；补录需内容授权 |
| xfail 桩后果 | 桩**仍红**（`fragile` 集合不含乙类，命中数 7 不变）⇒ 现状保持，但上游 §五「命中 7 题」读数继续有效 | 🔴 桩的**前提整体失效**（不再逐行比）⇒ **必须删桩并回写普查档**，不许只摘 `strict` | 桩**仍红但命中集合会变大**（新覆盖题里还会有一批不承重）⇒ 档 §二/§三 与桩 reason 的「7 题」读数当场过期，需回写 |
| 回滚方式 | 单文件 `git revert` 题面提交即可；判分未动 ⇒ **无行为残留** | 判分分支改动必须**与题面改动同进同退**（否则老题按新比较口径判松）；回滚＝revert 判分提交 ＋ 恢复被删桩 | 逐题 revert；`reference_answer` 是**新增键**，loader 侧有默认 `None` ⇒ 删内容不炸判分，回滚最干净 |
| 可分批性 | 可（6 条互不依赖） | **不可**（判分口径全 sql 共享，半套口径＝同一语言两种判分） | 可（按 topic 分批，每批 6～9 题） |
| 前置依赖 | 无 | **依赖 C**（见 §四） | 无 |

## 四、依赖声明与推荐次序（完成标准 ①的「推荐次序」）

**推荐：C → A → B，且 B 单独立项。** 理由三条，每条可复核：

1. **B 被 C 挡在前面**：出口 B 点名的 6 道「排序有语义」题里，只有 2 道当前可机验
   （`01_rank_in_class`、`04_lag`，两者恰好都在 fragile 集合＝已被证不承重）；
   另 4 道（`05_top2_per_class`、`03_running_sum`、`05_order_two_cols`、`11_null_handling/05_order_null`）
   **不可机验**（`hints` 里没有可整条执行的参考解，本单探针实测 `可机验=False`）。
   ⇒ 不先做 C，B 改完之后**有 4/6 条题连"改对了没有"都测不出来**，只能靠人工读题面担保。
2. **A 单独做会造「假收口」**：A 只补乙类 6 条题面，而 7 道 fragile 一条不消
   （乙类里唯一在 checkable 内的 `02_lowest_2` 还属"不可剥"）⇒ 做完 A，`xfail` 桩照旧红。
   这不否证 A 有价值（题面含糊本身就是缺陷），但要**明确它不解决承重问题**，否则规划班会误勾。
3. **C 是唯一零红线、零判分风险、且能把失明面从 31/42 收到 0 的出口**，
   同时它把 B 的验收面从"人工读题"升级为"机验 42/42" ⇒ 顺序上先做 C，B 的决策成本最低。

**依赖图（单向）**：`C（补参考解，内容授权）` → `B（判分口径变更，产品拍板）`；
`A（题面文案，内容授权）` 与两者**并行无冲突**，但 A 不得作为 B 的替代出口被勾销。

## 五、出口 B 的判分影响面：受影响用例逐名清单（完成标准 ②）

取数口径：`rg -n 'expected_rows|_rows_equal' tests/` 命中 11 件文件（本单实跑），
再按「该用例是否依赖**行的位置语义**」筛。逐名如下（文件名:函数名，`rg -n 'def <函数名>' <文件>` 可复核）：

**必红（行序契约被改，共 5 例）**

| 文件 | 用例 | 为什么必红 |
|---|---|---|
| `tests/test_sql_judge_column_order.py` | `test_sql_judge_is_row_order_sensitive_and_needs_order_by` | 直钉「行序敏感、必须写 ORDER BY」＝ B 要改的东西 |
| 同上 | `test_sql_judge_end_to_end_positional_reject_and_accept` | 走端到端「位置不符即拒」，集合比较下会**误判通过** |
| `tests/test_sql_roworder_fragile.py` | `test_多行SQL题行序全部承重` | `xfail(strict=True)` 桩，前提失效 ⇒ **转 XPASS＝红**（见 §七） |
| 同上 | `test_机验口径未失效` | 取数按「逐行等于期望」筛参考解，判分改集合后该桩的比法与生产不同源 |
| `tests/test_judge.py` | `test_sql_expected_rows` | 端到端钉 `expected_rows` 判定结果，行序用例需重述 |

**需复核（不必然红，但契约要重新表述，共 10 例）**

| 文件 | 用例 | 复核点 |
|---|---|---|
| `tests/test_judge_rows_characterization.py` | `test_行数不等直接False`、`test_空表与空表相等_空表对非空False`、`test_列数不等的行_判False`、`test_全等表True`、`test_首差定位_值不同`、`test_首差定位_行缺失_以None表示`、`test_首差定位_列缺失_以None表示`、`test_无差异返回None` | 这 8 例**直接测 `_rows_equal`／`_first_diff_cell` 纯函数**。若 B 新增比较分支而**保留** `_rows_equal` 原语义，8 例不动；若改写该函数本体，`_first_diff_cell` 的「行号」在集合语义下无定义 ⇒ 4 例首差定位要重定义 |
| `tests/test_core_edges.py` | `test_rows_comparison_tolerates_numeric_types_and_reports_exact_cell`、`test_run_test_cases_reports_output_runtime_and_row_differences` | 钉的是「单元格等值口径＋差异上报」，与行序正交，**预期不动**；上报文案改动会牵动 `:222-227` 那串 ⇒ 属文案耦合，非语义耦合 |
| `tests/test_sql_judge_column_order.py` | `test_sql_judge_is_column_order_sensitive` | **列**序，B 改的是**行**序 ⇒ 预期不受影响；列序契约须原样保留（防 B 顺手把列也集合化） |

**不受影响（明确划出去，防"重做面"被夸大）**：`test_sql_judge_cell_equality_caliber`、
`test_sql_setup_statements_all_execute_locally`、`test_sql_setup_census_two_independent_calibers_agree`（同文件，测单元格口径与 setup 可执行性）、
`tests/test_content_census_sql.py::test_expected_rows形态与行数直方图精确`（只校 yaml 字段形态与直方图，不判行序）、
`tests/test_scripts.py` 三例（`test_content_audit_reports_problem_and_path_failures`／`test_content_audit_open_question_requires_rubric`／
`test_deep_content_audit_flags_syntax_setup_and_stdin_gaps`，audit 侧字段校验）、
`tests/test_content_fuzz_pins.py:183 test_expected_rows_not_list_is_error`（audit 的形态负例）。
`tests/test_content_census_r.py` / `_python.py` 的 `expected_rows` 命中是**"不得出现该字段"的反向守卫**，B 不触。

> 上游 l922-129 把 B 的测试成本写成「要连同 l921-03 的 **6 例**一起重做」——**本单否证**：
> 那 6 例里按位置语义只有 **2 例必红**（另 1 例是列序，1 例是单元格口径，2 例是 setup 面）。
> 真实重做面是「必红 5 例（含本桩 2 例）＋需复核 10 例」，比上游口径**更大也更可定位**。

## 六、对上游普查档的三处口径修正（否证，按实况收窄）

1. **「agent_dev 48 道开放题在用 `reference_answer`」→ 数错了**：`tests/test_content_census_agent_dev.py:93`
   现值为 `{"expected_output": 30, "tests": 1, "rubric": 48, "reference_answer": 38}` ＋ `judge_mode` 的
   `{"run": 30, "ai_open": 48}` ⇒ **48 是 ai_open／rubric 数，38 才是带参考解的题数**。
   本探针复算 agent_dev 带 `reference_answer` ＝ **38**（与 38 一致），另 python 8／r 14。
   对结论的影响：**正向**——字段在用且跨 3 种语言，出口 C 的"零 schema 改动"比上游说法更硬。
2. **「出口 B 点名 6 道排序有语义题」→ 4 道当前不可机验**（见 §四.1）。上游把它们与 `01_rank_in_class`／`04_lag`
   并列成"改完即可验"的同一批，实况是**只有那 2 道能自证**。⇒ B 的前置必须显式写成 C。
3. **「B 要连同 l921-03 的 6 例一起重做」→ 收窄为 2 例**（见 §五）。上游口径过宽会把 B 的成本说高，
   反向漏算的是**它没提 `_first_diff_cell` 与 8 例 characterization 桩**（这才是 B 真正的实现耦合面）。

## 七、`xfail` 桩的删除条件（完成标准 ③，引上游档 §五 原文）

`docs/insights/learn-sql-roworder-census-20260922.md` §五 原文：

> - `test_多行SQL题行序全部承重` 以 **`xfail(strict=True)`** 钉住现状：断言"不存在不写 ORDER BY 也能逐行判对的多行题"，
>   现值命中 7 题 ⇒ 必红 ⇒ 标 xfail。**任一修复让命中集合清空，该例会转 XPASS 而报错**——这就是提醒，
>   不许改成永绿断言、也不许把 `strict` 摘掉。
> - `test_机验口径未失效` 是普通断言：机验子集必须 >= 1 题且能取到期望行，防止将来 `hints`/字段形态变化把上一条变成假绿。
> - 取数与判据全部在测试件内从磁盘实算（`content/sql/*/*.yaml`），不写死题号清单；改动题面后重跑即反映新状态。

桩自身 `reason` 文本（`tests/test_sql_roworder_fragile.py:130-138`，被引句在 `:137`）另加一条同义约束：
「命中集合清空即 XPASS＝本例转红，届时请删桩并回写普查档，勿放宽断言。」

**本单按三条出口分别推演删除条件是否触发**（这是选出口时的隐性成本）：

| 出口 | `fragile` 命中集合变化 | 桩会怎样 | 必须配套的动作 |
|---|---|---|---|
| A | 不变（仍 7） | 继续 XFAIL，现状钉得住 | 只需回写普查档 §二 的乙类描述 |
| C | **变大**（11 → 至多 42 里再挑） | 继续 XFAIL，但 reason 里「命中 7 题」失效 | 回写普查档 §二/§三 ＋ 桩 reason 文本（**不得摘 strict**） |
| B | 前提失效（不再逐行比） | **转 XPASS＝红** | **删桩 ＋ 回写普查档**，并同步 §五 那 15 例 |

⇒ 三出口里**只有 B 会当场弄红全量**（本仓现役 `2 xfailed` 会掉一条），所以 B 的执行单必须自带"删桩＋回写"三步，
不能只交判分改动。**A 与 C 都不会让本波收班变红**——这也是把 A/C 排在前面的一条非技术性理由。

## 八、本档不做的事（红线自证）

- 未改 `core/judge.py`／`core/runners/sql_runner.py`／任何 `content/sql/**.yaml`（判分口径与题面＝红线，出口 B 只建议）。
- 未改 `tests/**`（含那个 `xfail(strict=True)` 桩——摘 `strict` 属放宽判据，超出执行手授权）。
- 未碰 `NON_THIN_RATIO_FLOOR`、`test_scripts.py:312`、`test_insights_index_closure.py:18`、FakeStreamlit 基类、`dashboard.py` 写序。
- 未新增题目内容 ⇒ 无需跑 `tmp/l923_verify_new_questions.py` 参考解探针。
- 唯一新增件是本档 ＋ `tmp/l923-23/census_probe.py`（未入库探针，无 `.orig` 备份——本档零改既有文件，不需要回滚位）。
- ⚠ **索引欠账在册**：按本波派单口径「新增 `docs/insights/*.md` 先不改索引档，收班统一补列」，
  本档**未登记**进 `docs/insights/learn-insights-index-20260918.md` ⇒ `tests/test_insights_index_closure.py`
  会因 A（磁盘数）＝ B（索引条目）＋1 而**报红**。这是**在册欠账、不是回归**，收班时补列即绿；不得放宽哨兵。
