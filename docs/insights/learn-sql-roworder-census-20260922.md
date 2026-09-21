# learning SQL 多行题行序判读普查（l922-129，2026-09-22，只读零改动）

- 任务：`l922-129-sql-roworder-census`（执行班 qoder-executor-20260922-0000-learn10，软预算 35 分钟）
- 取数时点：HEAD `157d201`（工作树另有本班 l922-127/128 两件在制），题库 `content/sql/*/*.yaml` **54 题**
- **本单零改动生产内容**：未改任何题面 yaml、未改 `core/judge.py`、未给任何 SQL 加 `ORDER BY`。
  判分口径变更属产品/规划拍板面（l921-03 已点名），本单只出清单与出口。

## 一、取数口径（绑磁盘，可复跑）

```bash
# 多行题定义：expected_rows 列表长度 >= 2（sql 题的判分契约就是这个列表，无 expected_stdout 字段）
PYTHONIOENCODING=utf-8 python -c "import yaml,glob; \
 c=[len(yaml.safe_load(open(f,encoding='utf-8'))['expected_rows']) for f in glob.glob('content/sql/*/*.yaml')]; \
 print(len(c), sum(1 for n in c if n>=2))"
```

- 54 题全覆盖，`expected_rows >= 2` 者 **42 题**（行数直方 `{2:10, 3:14, 4:7, 5:9, 6:1, 7:1}`，和 12 题单行相加＝54）。
- 42 这个数与锚点 `zcode-bridge/outbox/l921-03-learn-sql-judge-census.result.md` 自述的「本班实数 42 题」**逐字一致**（锚点未漂）。
- sql 题的 yaml 字段集实测恒为 9 个：`title/topic/difficulty/tags/statement/starter_code/setup_sql/expected_rows/hints`
  —— **没有** `solution`/`reference_sql` 字段，参考解只散落在 `hints` 文本里（l921-03 自纠的那条假发现，本单再证一次）。

## 二、三类计数（合计 42，与覆盖数闭合）

判读方式：42 条题面**逐条读**（不用字段 grep 代替判读，l921-03 的前科）。
排序词识别式：`排序|排列|顺序|次序`；方向词识别式：`升序|降序|从高到低|从低到高|从大到小|从小到大|倒序`。

| 类 | 判据 | 题数 |
|---|---|---|
| **甲 已含排序要求**（题面给排序键 **且** 给方向，行序唯一确定） | 键＋方向双明示，且排序是考点语义的一部分 | **31** |
| **乙 缺要求建议补提示**（题面有排序词但没方向，或干脆没有排序词） | 学生无法从题面唯一推出行序 | **6** |
| **丙 建议改行集合比较**（题面明示排序，但该序无语义负载，实测不写 `ORDER BY` 也能逐行判对） | 判分依赖引擎返回序 | **5** |
| 合计 | — | **42** |

### 乙类 6 条（逐条给题号与建议出口）

| 题号 | 行数 | 题面现状（摘录） | 缺什么 | 建议出口 |
|---|---|---|---|---|
| `sql/01_select_where/01_select_all` | 5 | 「期望**按 id 顺序**返回 5 行」 | 无方向词（升/降未写） | 题面补「按 id **升**序」一句；或并入丙类改集合比较（此题 `SELECT * FROM students` 本就没有 ORDER BY，靠扫描序） |
| `sql/01_select_where/02_score_filter` | 3 | 「期望**按 id 顺序**返回 3 行：Alice、Bob、Eve」 | 同上 | 同上（已列期望姓名序，属"清单隐含序"，补方向词最省） |
| `sql/03_orderby_having/02_lowest_2` | 2 | 「成绩最低的 2 名学生……期望返回 2 行（David 60、Cathy 75）」 | **完全无排序词**，只靠期望清单隐含 score 升序 | 题面补「按 score 升序输出」；`hints` 已含 `ORDER BY score ASC LIMIT 2`，属"提示有、题面无"的错位 |
| `sql/07_cte/04_recursive_cte` | 5 | 「生成数字 1 到 5（每行一个数）。期望 5 行：1, 2, 3, 4, 5」 | 无排序词；`starter_code` 骨架 `SELECT n FROM seq;` **本身不含 ORDER BY**，`hints` 也没提 | 题面补「按 n 升序」并在 hints 里加 `ORDER BY n`；否则判分完全依赖递归 CTE 产出序 |
| `sql/12_people_analytics/01_avg_by_dept` | 3 | 「……**按部门名排序**」 | 有排序词、无方向词 | 题面补「升序」（`hints` 有 `ORDER BY department`）；或改集合比较（分组均值题的序无语义） |
| `sql/12_people_analytics/03_headcount` | 3 | 「……**按部门名排序**」 | 同上 | 同上 |

### 丙类 5 条（实测「不写 ORDER BY 也判对」，见第三节机验口径）

| 题号 | 行数 | 题面排序要求 | 为什么建议改行集合比较 |
|---|---|---|---|
| `sql/03_orderby_having/03_distinct_grades` | 4 | 「按字母升序」 | `SELECT DISTINCT grade` 的去重序 sqlite **不保证**；实测去掉 ORDER BY 结果仍逐行等于期望 ⇒ 要求形同虚设，学员写 `GROUP BY` 也能过 |
| `sql/04_joins/05_join_groupby` | 2 | 「按部门名升序」 | 分组计数字典序＝期望序，实测无 ORDER BY 仍匹配 ⇒ 考点（JOIN+GROUP BY）被"猜对返回序"污染 |
| `sql/05_subqueries_case/01_above_avg` | 3 | 「按 id 升序」 | 高于均值的姓名集合才是考点，3 行全出即语义正确；实测无 ORDER BY 仍匹配 |
| `sql/05_subqueries_case/02_in_subquery` | 2 | 「按 id 升序输出」 | 同上（同部门姓名集合） |
| `sql/07_cte/01_simple_cte` | 3 | 「（按 id 升序）」 | 同上（CTE 选 name，集合语义） |

**丙类未机验的候选 2 条**（题面明示排序、结构上同属"分组/去重枚举"，但 `hints` 里没有可整条执行的参考解，故未计入丙类计数）：
`sql/02_aggregate/03_pass_fail_count`（GROUP BY category，题面「按 category 字母升序排（即 fail 行在 pass 行之前）」）、
`sql/03_orderby_having/04_union_names`（UNION 去重后字母升序）。若规划班要一次性收口，应把这 2 条一起纳入。

## 三、判分侧交叉证据（"缺 ORDER BY 却依赖返回序"的结构面）

1. **判分器是位置敏感的**：`core/judge.py:96-100` `_rows_equal()` 用 `zip(actual_rows, expected_rows)` 逐行逐格比对（`:219` 调用），
   行数不等先短路（`:97`）。l921-03 已为此单独钉了 `tests/test_sql_judge_column_order.py`（6 例，含"行序敏感"一例）⇒ 行序**确实参与判分**。
2. **骨架侧全裸**：42 道多行题里 `starter_code` 真代码含 `ORDER BY` 的 **0 道**（31 道只在 `--` 注释里出现该词，剔注释后为 0）。
3. **提示侧不齐**：`hints` 明确出现 `ORDER BY` 的 **26/42**；⇒ 16 道题「题面要求某个行序，但骨架与提示都不给 ORDER BY」，其中 6 道即上表乙类。
4. **可机验子集（11/42）实测**：只有 11 道题的 `hints` 里存在能整条执行且结果逐行等于 `expected_rows` 的参考解。
   对这 11 题做「剥掉深度 0 的 `ORDER BY`（窗口函数 `OVER (ORDER BY …)` 不剥）后重跑」对比：

   | 结果 | 题数 | 题号 |
   |---|---|---|
   | 去掉 ORDER BY 后**仍**逐行等于期望 ⇒ 行序不承重、判分靠引擎返回序 | 7 | 上表丙类 5 条 ＋ `06_window_functions/01_rank_in_class`、`06_window_functions/04_lag` |
   | 去掉 ORDER BY 后顺序变 ⇒ 排序要求承重、题面提示有效 | 3 | `03_orderby_having/01_order_desc`、`06_window_functions/02_class_avg`、`09_string_funcs/01_length` |
   | 含 top-level `LIMIT`，不可剥（剥了会变行集） | 1 | `03_orderby_having/02_lowest_2` |

   ⇒ 丙类那 5 条是"实测不写 ORDER BY 也能过"；`01_rank_in_class` / `04_lag` 两条**排序有语义**（排名/前一行），
   实测却不强制，属**真误判面**（学员忘写 ORDER BY 也判对，学到的是错的），已单列进第四节的出口 B。
5. **覆盖面限制（自曝失明面）**：机验只覆盖 11/42。余 31 题的参考解不可整条执行（hints 是文字提示），
   其"是否依赖返回序"未测；这不是"没问题"，是"没测"。要闭合需给多行题补参考解——
   **落点字段仓里已有**：`core/loader.py:33` 的 `Problem.reference_answer`（`core/judge.py:45/314` 已消费，agent_dev 48 道开放题在用，见 `tests/test_content_census_agent_dev.py:93` 的 38 处计数），
   而 sql 侧实测 **54/54 题为空** ⇒ 补 `reference_answer` 不必改 schema，属内容补录（仍需授权）。

## 四、三条出口（交规划/产品拍板，执行班不实施）

- **出口 A（最省）**：只补题面文案——乙类 6 条各补一句排序键＋方向；丙类不判分改动。
  代价：0 处判分逻辑变更，但"不写 ORDER BY 也判对"的误判面（丙类＋2 条排名/滞后题）继续存在。
- **出口 B（推荐）**：把**排序有语义**的题（`01_rank_in_class`、`04_lag`、`05_top2_per_class`、`03_running_sum`、`05_order_two_cols`、`11_null_handling/05_order_null` 等）
  的期望行序与 `ORDER BY` 绑定，并在题面写明"必须写 ORDER BY，否则行序不保证"。排序无语义的集合题（丙类 5＋候选 2）改**行集合比较**。
  代价：动 `core/judge.py` 的 sql 比较分支＝判分口径变更，需 l921-03 那 6 例一起重做，且要防"集合比较"把**真该有序**的题判松（l921-03 曾因此自纠一条假发现）。
- **出口 C（工程侧长期）**：把参考解填进已有字段 `reference_answer`（sql 侧 54 题现全空），
  之后"行序是否承重"可 42/42 机验，不必再靠人工读题面——本文件的机验面即可自动扩到全量。

## 五、本单留下的桩（改齐即转红）

`tests/test_sql_roworder_fragile.py`（本单新增，2 例）：

- `test_多行SQL题行序全部承重` 以 **`xfail(strict=True)`** 钉住现状：断言"不存在不写 ORDER BY 也能逐行判对的多行题"，
  现值命中 7 题 ⇒ 必红 ⇒ 标 xfail。**任一修复让命中集合清空，该例会转 XPASS 而报错**——这就是提醒，不许改成永绿断言、也不许把 `strict` 摘掉。
- `test_机验口径未失效` 是普通断言：机验子集必须 >= 1 题且能取到期望行，防止将来 `hints`/字段形态变化把上一条变成假绿。
- 取数与判据全部在测试件内从磁盘实算（`content/sql/*/*.yaml`），不写死题号清单；改动题面后重跑即反映新状态。
