# l927-18 期望答案大小写／口径不一清单与裁决材料（只读，零写库、零判题改动）

- 班次：`qoder-executor-20260927-1820-learn47`（波次 22 只读位），现点 2026-09-27T18:2x（本机 `date`）
- 仓现值：HEAD `bbceef5`；开工 porcelain 0 行（brief §5 表里的 `2665f0a` 已漂移，主班 17:5x 代收 `f80b89e`＋索引 `bbceef5` 之后）
- 锚点：`zcode-bridge/outbox/20260925-154245-6130.result.md` → **实取于 `D:\code\zcode-bridge\done\20260925-154245-6130.result.md`**（15,918 B；路径搬家非缺陷，按 brief §3a）
- 🔴 **本档不签任何一边**：「改期望值」与「改判题归一化层」都是判题口径面，「改题面」是可见承诺面——三案全部只写成给人拍的判断题（后果／可复算入口／回滚成本），本班**未改任何期望值、未改判分逻辑、未动题面、未动测试**。
- 「影响判题与否」这一列**一律按 §0 的现役判分口径注明依据**，不引任何档的旧读数。

---

## 0. 现役判题口径（这是全部"影响判题与否"的判定依据，逐行可核）

| 口径 | 代码位置 | 实测行为（纯函数直调，未跑 runner、未开库） |
|---|---|---|
| 串面比较 | `core/judge.py:259`：`case_passed = case_run.ok and (expected_out == actual_out)`，两侧先过 `_normalize`（`:257-258`） | **大小写敏感**：`_normalize("CoT","agent_dev")` 与 `_normalize("COT","agent_dev")` 比较 → **False**；`Engineering` vs `engineering` → **False**；`"2.0"` vs `"2"` → **False** |
| `_normalize` 契约 | `core/judge.py:57-78` | 仅 `\r\n→\n` ＋ 去尾部换行；**不做空白去除／折叠**；**只有 `lang=="r"`** 才去 `[1] ` 前缀并把行内空白折叠为单空格（**R 侧也不折大小写**）⇒ 空白宽容是**单语言特权**，跨语言口径天然不对称 |
| 行面比较 | `core/judge.py:81-101` `_cell_eq`／`_rows_equal` | 两侧都是数值 ⇒ `float(a)==float(b)` ⇒ **`2.0 == 2` 相等**；一侧是串 ⇒ `str(a)==str(b)` **严格**（含空白与大小写）；任一侧是 `bool` ⇒ 按真值比 ⇒ `_cell_eq(True,"Engineering")` → **True**（在册"反直觉点"注释自陈"实测校正 916-02"在 `:84-86`，bool 分支在 `:88-89`） |
| 谁赢 | `core/judge.py:255-256` | `tests[i].expected_output` 非 None 时**遮蔽**题级 `expected_output`；但 `:282 _build_display` 的展示仍读**题级**值 ⇒ 两者不等会出现"看到的期望≠判题用的期望"（本仓实测 0 例，见 §1 计数） |
| 开放题 | `core/judge.py:300-301`、`:328-335` | `judge_mode=="ai_open"` ⇒ 走 `_judge_open`→LLM rubric；`reference_answer` **只进 `expected_display`，不进判分** |
| 历史重判 | 全仓 | `judge(` 唯一调用点 `ui/pages/language.py:356`（提交时）；`attempts.code` 无任何读回重判／回填路径（`rg "SELECT .*code.* FROM attempts"` 只命中导出与 dry-run 只读面）⇒ **改期望不会回翻存量 `passed`**，代价落在"可复现性"而不是"数据被改"（§3） |

---

## 1. 扫描命令与计数（全库只读）

统一口径：题＝`content/**/*.yaml` 顶层为 mapping 且含 `statement` ⇒ **403**（与 `learn-tag-vocab-spec-20260925.md`／154244／154245 三档对平）；读法＝`yaml.safe_load(io.open(..., encoding="utf-8"))`，**不经 `core.loader`／DAO／judge 写入路径**。

| 扫描 | 命令（可整段重跑，脚本见 §4） | 现取读数 |
|---|---|---|
| 期望答案载体分布 | `scan_expected.py` | `expected_output` 非空 **279** 件／`expected_rows` **54** 件／`tests` **92** 件／`setup_sql` **54** 件／`reference_answer` **60** 件／`rubric` **70** 件／`judge_mode=ai_open` **70** 件 |
| 双真源检查 | 同上 | `expected_rows` 与 `expected_output` **同时非空 0 件** ⇒ 没有"一道题两套机判期望"的题 |
| 题级 vs test 级 | 同上 | `tests[i].expected_output` 共 **92** 条，与题级值**不等 0 条** ⇒ §0 那条"遮蔽＋展示不同源"的风险**今天无实例**（属"绿但零覆盖"家族，登记不夸） |
| SQL 数据面 vs 期望行 | 同上（`setup_sql` 单引号字面量 ∩ `expected_rows` 单元格，同形异写） | **0 对** ⇒ 锚点担心的"库里存 `Engineering`、期望写 `engineering`"不存在 |
| 近重复题对（锚点 154245 宽档口径复现） | `scan_pairs.py`（`norm`＋3-gram Jaccard≥0.30 预筛＋`SequenceMatcher.ratio()≥0.75`） | **16 对**，其中期望答案**非「完全相同」7 对** ⇒ 与锚点逐位对平（16／7） |
| 语料级同形异写 token | `scan_internal.py`（把 279 串面＋54 行面＋92 条 test 面的期望值切词，按 `lower()` 归组） | **13 个 token 族**存在 ≥2 种写法（逐族清单见 §2-C） |
| 题面样例 vs 期望答案同形异写 | `scan_internal.py` 第 1 段（题面反引号与代码围栏内容 vs 期望值） | **11 条命中**（逐条分类见 §2-B/§2-F；其中 2 条是**题面明写"也接受"而判题不接受**） |
| 宽容承诺普查 | `rg -n "也接受\|不区分大小写\|忽略大小写\|大小写不敏感\|大小写无关\|case[- ]?insensitive" content -g "*.yaml"` | **3 件**：`agent_dev/06_frontier/05_cot.yaml:9`、`agent_dev/01_git_basics/05_revert.yaml:9`（两句都用「也接受」）、`python/06_strings/02_count_vowels.yaml:6`（"不区分大小写"说的是**任务语义**，期望值是数字 `3` ⇒ 非冲突） |
| 载体间数值口径 | `scan_rows_caliber.py` | `expected_rows` 单元格类型＝`int 121／str 193／float 11／None 3`；**bool 单元格 0**、**"float 但整值"（会用到 `2.0==2` 宽容的）0** ⇒ §0 的三条反直觉分支**今天零 exercised**；串面 `expected_output` 含小数的行 **63** 条（如 `python/10_pandas_filter_group/02_groupby_mean` 的 `A 86.0`）⇒ 同一数值在串面 `86.0≠86`、在行面 `86.0==86`，**口径分叉由载体决定而不是由题意决定** |
| 存量作答（`mode=ro` 直连，未走 DAO） | `db_ro.py` | `attempts` 15 行；**8 行落在本案 B 类冲突对上**（`python/24_real_world_data/{01,02,03,04}` ＋ `r/14_real_world_data/{01,02,03,04}` ＋ `sql/12_people_analytics/01_avg_by_dept` 等），`passed` 全 1（唯一 0 是 `python/01_hello_and_vars/01_hello_world`，与大小写无关）⇒ 现状两侧都"被答对过"，**不一致不是坏题，是两套口径各自自洽** |

---

## 2. 不一致清单（逐行；「影响判题」按 §0 口径注明）

### A 类｜题面承诺宽容、判题不宽容（2 件，🔴 影响判题＝**是，直接判错**）

| # | 题 id | 题面原值（逐字） | 期望原值 | 影响判题与依据 |
|---|---|---|---|---|
| A-1 | `agent_dev/06_frontier/05_cot` | `:9` 「期望：`CoT`（**也接受 `COT`**，但题目锁定 `CoT`）。」 | `expected_output: "CoT"`（`:13-14`） | 🔴 **是**。`judge.py:260` 精确串等；实测串比 `CoT` vs `COT` → False（§4 纯函数复算） ⇒ 学生照题面输出 `COT` **判错**，而题面明写"接受"。这是**题面↔判题承诺冲突**，不是跨题口径问题 |
| A-2 | `agent_dev/01_git_basics/05_revert` | `:9` 「期望：`git checkout .`（**也接受 `git restore .`**，但题目锁定 checkout 写法）。」 | `expected_output: "git checkout ."`（`:13-14`） | 🔴 **是**。同口径；且这不是大小写而是**同义异形串**，归一化层**无法**用大小写规则解决 ⇒ 见 §3 案二的边界说明 |

> 对照（**非**冲突，登记以免被误并）：`python/06_strings/02_count_vowels:6` 的「不区分大小写」修饰的是**学生代码要做的处理**，判题只比 `3`；`tests[0].stdin="Hello World\n"`、`expected_output="3\n"` 与题级值一致（§1）。

### B 类｜近重复题对之间期望答案不一致（7 对，锚点口径复现）

`ratio`＝`SequenceMatcher`（归一化题干）；「影响判题」＝**否**（两题各自题面与期望自洽，学生按本题题面作答可通过），但**任何一侧被改写都会改该题判题结果**——这正是 §3 两案的入口。

| # | ratio | 题对 | 两侧原值（逐字，`⏎`＝换行） | 差在什么 | 影响判题 |
|---|---|---|---|---|---|
| B-1 | 0.9275 | `cpp/02_branch_loop/03_sum_1_to_n` ↔ `python/03_loops/03_sum_1_to_n` | `55` ↔ `5050` | 题面相似但**题不同**（1..10 vs 1..100），非大小写可解释 | 否（各自自洽）；🔴 **抄答案会判错**，是 7 对里唯一"看起来像重复题其实差一个数量级"的 |
| B-2 | 0.8516 | `python/24_real_world_data/04_dept_avg` ↔ `r/14_real_world_data/04_group_avg` | `Engineering: 2.0⏎Hr: 3.5⏎Sales: 4.33` ↔ `engineering: 2⏎hr: 3.5⏎sales: 4.33` | 🔴 **双重口径差**：大小写（title vs lower）**且**数值格式（`2.0` vs `2`，R `cat(round(2))` 掉尾零） | 否（python 侧题面 `:?`「例如 `Sales: 4.33`」＋指令「首字母大写」；r 侧题面「例如 `sales: 4.33`」＋指令 `tolower(trimws(...))` ⇒ **两侧题面各自与期望一致**）；但 `2.0`/`2` 这差在行面口径下会**相等**、在串面**不等**（§0） |
| B-3 | 0.8333 | `cpp/05_stl_basics/01_sort_vector` ↔ `cpp/06_iter_algo/01_sort_desc` | `1 1 3 4 5` ↔ `5 4 3 1 1` | 升序 vs 降序（不同操作，同语言） | 否；**不可按"重复"合并**（锚点建议 A 同判） |
| B-4 | 0.8235 | `cpp/06_iter_algo/01_sort_desc` ↔ `cpp/06_iter_algo/04_reverse` | `5 4 3 1 1` ↔ `5 4 3 2 1` | 排序 vs 反转（数据不同） | 否；同上 |
| B-5 | 0.7815 | `python/24_real_world_data/03_clean_category` ↔ `r/14_real_world_data/03_clean_dept` | `Engineering⏎Hr⏎Sales` ↔ `engineering⏎hr⏎sales` | 🔴 **纯大小写**（锚点点名的 `Engineering/Hr/Sales` vs 小写就是这一对） | 否（同 B-2 理由） |
| B-6 | 0.7597 | `python/15_ab_text/02_cohens_d` ↔ `r/06_mixed_apa/03_cohens_d` | `2.349` ↔ `2.35` | **有效数字位数**（3 位 vs 2 位） | 否；但这是"同题不同精度"，跨语言学生最容易在这里被判错 |
| B-7 | 0.7561 | `cpp/03_arrays_strings/03_reverse_string` ↔ `python/06_strings/03_reverse_str` | `dlroW olleH` ↔ `olleH` | 反转整句 vs 反转单词 | 否；`dlroW/olleH` 的大小写形态同时进 §2-C 的 `dlrow`/`olleh` 族 |

（另有 9 对期望答案**完全相同**：`02_dedup↔02_dedup`、`01_missing↔01_missing`、`11_matplotlib/02_bar_sum↔r/04_ggplot/02_bar`、`01_vector_sum↔01_list_sum`、`02_word_freq↔01_word_freq`、`r/02b_dataframe/05_add_column↔r/03_dplyr/03_mutate`、`03_set_unique↔03_dedup_sorted`、`cpp/02/01_odd_even↔python/02/01_odd_even`、`cpp/01_io_and_vars/02_sum_two_ints↔cpp/02/02_max_of_three`。⇒ **16 对里 9 对无口径问题**，不一致率 7/16，锚点的"16 对／7 冲突"逐位复现。）

### C 类｜语料级同形异写 token 族（13 族，逐族列变体与题号样本）

判定口径：把**全部期望答案面**（279 串面＋54 行面＋92 条 test 面）切词后按 `lower()` 归组，组内写法 >1 者入列。

| token（小写键） | 变体（出现次数） | 题号样本 | 影响判题 | 本班分类 |
|---|---|---|---|---|
| `alice` | `Alice`(35 题)／`ALICE`(2)／`alice`(1) | 大写面：`r/10_stringr_lubridate/01_str_upper`、`sql/09_string_funcs/05_upper_concat`；小写面：`python/19_regex/01_find_emails` | 否（大写面是 `str_to_upper`/`UPPER()` **任务结果**，小写面是正则原文） | **伪不一致**：变体由题意解释，不该归一 |
| `bob` | `Bob`(29)／`BOB`(2)／`bob`(1) | 同上 | 否 | 伪不一致 |
| `cathy` | `Cathy`(26)／`CATHY`(2) | 同上 | 否 | 伪不一致 |
| `hello` | `Hello`(7)／`hello`(1)／`HELLO`(1) | `hello`：`cpp/10_templates/02_class_template`；`HELLO`：`python/06_strings/01_to_upper` | 否 | 伪不一致（`to_upper` 任务） |
| `world` | `World`(7)／`WORLD`(1) | 同上 | 否 | 伪不一致 |
| `true` | `true`(4)／`True`(2)／`TRUE`(1) | `true`：cpp 4 题；`True`：`python/04_functions/04_is_prime`、`python/16_classes_oop/02_method`；`TRUE`：`r/13_rmarkdown/01_write_rmd` | 否（各语言字面量真名） | 🔴 **真口径分叉但不可归一**：布尔字面量本就该随语言（`cpp`→`true`、`py`→`True`、`R`→`TRUE`）；若加"大小写不敏感"会把这些**跨语言区分**抹平 |
| `hr` | `HR`(11)／`Hr`(2)／`hr`(2) | `HR`：`python/20_hr_pandas/05_pivot_analysis`、`r/08_tidyr/03_separate`、`sql/04_joins/*`；`Hr`：`python/24_real_world_data/{03,04}`；`hr`：`r/14_real_world_data/{03,04}` | 否（各自题面自洽） | 🔴 **最需要人看的一族**：同一 HR 数据集在三处给出三种写法；`Hr` 是 pandas `.str.title()` 对缩略语 `HR` 的产物（题面 `python/24/03:35` hint 明写用 `title()`）⇒ 语义上"部门名应显示 HR 还是 Hr"是内容裁决 |
| `engineering` | `Engineering`(4)／`engineering`(2) | `Engineering`：`python/24_real_world_data/{03,04}`、`sql/12_people_analytics/{01,03}`；`engineering`：`r/14_real_world_data/{03,04}` | 否 | 🔴 与 B-2／B-5 同源，**sql 站 python 一边**（⇒ 折向小写会孤立 sql） |
| `sales` | `Sales`(7)／`sales`(2) | `Sales`：`python/16_classes_oop/04_super`、`python/20_hr_pandas/01_dept_headcount`、`python/24/*`、`sql/12/*` | 否 | 同上 |
| `error` | `error`(2)／`Error`(1) | `error`：`cpp/11_exceptions/{01,03}`；`Error`：`cpp/11_exceptions/02_what` | 否 | 🔴 同语言（cpp）内部不统一，属**同语言口径漂移**，最值得单看 |
| `olleh` | `olleH`(2)／`olleh`(1) | `olleH`：`cpp/03_arrays_strings/03_reverse_string`、`python/06_strings/03_reverse_str`；`olleh`：`cpp/03_arrays_strings/06_reverse_words` | 否 | 反转产物，伪不一致（但 `olleH`↔`olleh` 与 B-7 重叠） |
| `dlrow` | `dlroW`(1)／`dlrow`(1) | `cpp/03_arrays_strings/{03,06}` | 否 | 同上 |
| `hi` | `hi`(2)／`Hi`(1) | `hi`：`cpp/10_templates/05_specialization`、`python/17_decorators_props/05_param_decorator`；`Hi`：`cpp/08_inheritance/01_basic_inheritance` | 否 | 轻（问候语大小写随题面） |

⇒ **13 族里 4 族属"可由题意解释的伪不一致"**（alice/bob/cathy/hello/world/olleh/dlrow 属数据变换与反转产物）、**4 族属真口径分叉**（`hr`/`engineering`/`sales`/`error`），**1 族属"绝不该归一"**（`true`，跨语言字面量真名）。

### D 类｜载体间口径不对称（影响判题＝**取决于写在哪一侧**）

| 事实 | 依据 | 今天是否 exercised |
|---|---|---|
| 同一数值：行面 `2.0 == 2` 判过，串面 `2.0 ≠ 2` 判不过 | `_cell_eq` 数值分支（`core/judge.py:90-91`）vs 串面 `:259` | 串面含小数 **63 行**（`python/10_pandas_filter_group/02_groupby_mean` 的 `A 86.0` 等）；行面"float 整值"单元格 **0** ⇒ 宽容侧今天**没有实例**，严格侧有 |
| 空白：R 题折叠、python/cpp/sql 题**一个空格都不容** | `_normalize` 的 `if lang == "r"` 分支（`:70-77`） | 🔴 这是现役**唯一**的大小写无关之外的宽容，且**按语言分裂**；B-2 的 `2.0`/`2` 差恰好落在 r 侧 |
| `bool` 单元格与任意非空串相等 | `_cell_eq` `:88-89`（注释自陈"实测校正 916-02"） | 行面 bool 单元格 **0** ⇒ 零实例，但案二若把"归一化"扩到行面会撞上它 |

### E 类｜开放题面（影响判题＝**否**）

`judge_mode=ai_open` 70 件、带 `reference_answer` 60 件 ⇒ 按 `core/judge.py:300-301`/`:328-335`，`reference_answer` 只进 `expected_display`，判分交 LLM rubric ⇒ **本类的大小写/口径差都不进机判**，属"展示与提示面"，**不列入 §3 两案的必改面**（只登记，因为改它同样会改变学生看到的"标准答案长相"）。

---

## 3. 两案（＋一个对照形状）裁决材料

### 案一｜改期望值（把某一侧的字面统一到选定写法）

- **动的是什么**：`content/**/*.yaml` 的 `expected_output`／`expected_rows` 字面 ⇒ **直接改判题结果**（同一份学生代码可能从过变不过或反之）。属 brief §4「内容正确性」＋「判分口径」双红线，**必须人工放行**。
- **影响面（现取，`fold_surface.py`）**：HR 数据集三字族（`hr`／`engineering`／`sales`）在期望答案面共涉及 **18 个不同题件**（`hr` 15 题、`sales` 9 题、`engineering` 6 题；按语言＝sql **10** 题、python **5** 题、r **3** 题、cpp／agent_dev 0）。⇒
  - 若**只**把锚点点名的那两对（B-2／B-5：`python/24_real_world_data/{03,04}` ↔ `r/14_real_world_data/{03,04}`，共 4 题）折平，只需动**一侧 2 题**——但结果会是 python/24 变小写、而 sql/12_people_analytics 仍是 `Engineering`/`Sales` ⇒ **不一致只是换了对手**（从"r vs python"变成"r＋python vs sql"）。
  - 若要**全语料一套写法**：折向小写＝动 15 题（python 5＋sql 10），折向标题式＝动 3 题（r 侧）＋把 `HR` 这 11 题（sql/04、sql/08、sql/09、sql/12、python/20、r/08 的 `HR` 字面量）一并定性——**这 11 题里的 `HR` 属数据/表名原样，不是 title-case 产物**，把它们卷进"大小写归一"是错误扩大，必须先由人工划清"`HR`（缩略语原样）"与"`Hr`（`.str.title()` 产物）"是不是同一件事。
  - B-2/B-6 的**数值格式**差（`2.0` vs `2`、`2.349` vs `2.35`）**不是大小写问题**，案一若只"统一大小写"不会消除它们，需要额外定"保留几位"这条**新规则**（属内容裁决，且要逐题重算期望值）。
- **可复算入口**：`scan_internal.py` 的族表（每族带题号）＋ `four_families.py`（四族逐变体全题号）＋ `fold_surface.py`（并集与按语言拆分）＋ `scan_pairs.py` 的 16 对。本班实扫：`rg -l "expected_output" tests/` → **22 件**测试文件提及期望值面（改字面前要逐件过）；census 系列不读期望内容（l927-17 已证其对 tag 零断言）。
- **回滚成本**：`content/` 有 git 还原点 ⇒ 一次反向 commit 可回；但**存量学习记录不回翻**（§0 末行：全仓零重判路径，`attempts` 里 8 行落在本案冲突题且 `passed` 全 1）⇒ 代价不是"数据被改坏"，而是**"当初判对的那份代码现在不再复现"**（审计／可复现面），这一条不可由 git 还原（库在 `.gitignore` 覆盖的 `data/` 下）。

### 案二｜改判题归一化层（`_normalize`／`_cell_eq` 加宽容）

- **动的是什么**：`core/judge.py:57-101` 的**输出归一化契约**——它被注释显式声明为「现状描述，零行为改动」的契约档（`:57-65`），且由 `tests/test_judge_pure.py` 钉着"不做空白去除"的反直觉点。⇒ **一处改动同时改 333 道机判题的判题**（串面 279 ＋ 行面 54；403−333＝70，正好是 `judge_mode=ai_open` 的 70 件），是本案影响面最大的形状。
- **能解决什么／不能解决什么**（这是关键，别把案二当万灵药）：
  - ✅ 能：B-5／B-2 的**大小写**差（若加 `lower()`），A-1 的 `COT`/`CoT`。
  - ❌ **不能**：A-2 的 `git checkout .` vs `git restore .`（同义异形串，大小写规则无法覆盖 ⇒ 只能改题面或引入"多期望值"新字段，那是**新功能**）；B-1（`55` vs `5050`，本来就该不同）；B-3/B-4/B-7（不同操作）；D 类里"行面已宽容、串面不宽容"的分叉要**分两处**改。
  - 🔴 **副作用可复算**：加大小写不敏感会把 §2-C 里**本应保留**的跨语言区分一起抹掉——`true`/`True`/`TRUE`（布尔字面量真名）、`olleH`（反转结果）、`ALICE`（`str_to_upper` 任务结果）；实测这些差异现在都是**判分依据**（学生输出 `alice` 在 `to_upper` 题里现在判不过）。
  - 🔴 与 `R 折叠空白` 的既有特权叠加 ⇒ 语言间宽容度进一步不对称（或反过来被迫统一到"最宽"，那会放宽 279 题的通过条件，属**放水向**判分变更）。
- **可复算入口**：`_normalize`／`_cell_eq`／`_rows_equal` 三个纯函数可在不开库、不跑 runner 的前提下直接验（§4 的最后一条命令给出读数），任何候选改法都能先在纯函数层列出"哪些题的通过集会变"。定向回归面：`tests/test_judge_pure.py`（契约钉桩）＋ `tests/test_judge_mode_equivalence.py:140`（逐题比对 `to_dict()`）＋ `tests/test_review_mastery_bounds.py`（判分口径不动的另一面）。
- **回滚成本**：低（纯代码一处，git 可逆），**但**：判分口径变更会让"改动窗口内的作答"落在旧口径上（`attempts.passed` 不回翻 ⇒ 同一学生在改前改后交同一份代码得到不同判定），这是**教学公平面**，不是代码回滚能抹掉的。

### 对照形状｜改题面承诺（最便宜，但属可见承诺面）

- 只针对 **A 类 2 件**：把 `:9` 那句「也接受 X」删掉或改成"锁定单写法"，承诺与判题即一致；不动期望值、不动判分逻辑 ⇒ 影响面 2 行文案。
- 代价：文案面**可见**（学生看得到），且与 l927-09 在册结论"「暂时不可用」子串哨兵漏掉「暂时连不上」⇒ 改文案＝改行为"同族——文案在这里就是承诺本身，需人工认这一笔；`tests/` 里是否有子串哨兵覆盖这两句，本班实扫见 §4。
- **本班不选边**：三形状的选择权在人工；本班只保证"影响面已量出来"。

---

## 4. 零改动自证 ＋ 可复算入口

- **零写库／零判题改动**：`git status --porcelain` 仅 3 行＝本班三件 `?? docs/insights/l927-*.md`；`content/` 零 diff；未跑任何仓内 backup／import／mark_* 脚本；**未调用任何 `dao=None` 路径**（在册前科：`core/judge.py:199` 与 `:342` 的 `d = dao or ProgressDAO()` 会开生产库）。
- **主库两点取样未变**：`data/progress.db` **122,880 B ／ sha8 `cd2dbce4`**（18:15:51 与 18:2x 本单收单各一次，另 17:59:20 开工一次；`certutil -hashfile data/progress.db SHA256` 取前 8 位；mtime 恒 `Sep 25 20:49`）＝在册基线同值。
- **只读主证**：`db_ro.py` 用 `mode=ro` 打开后当场试写 `CREATE TABLE` ⇒ `sqlite3.OperationalError: attempt to write a readonly database`（**未**用 `cp` 取副本，未逐枚开真库；`journal_mode` 未改）。
- **探针**（班名目录，收班自清）：`D:\code\tmp\qoder-executor-20260927-1820-learn47\`＝`scan_expected.py`、`scan_pairs.py`、`scan_internal.py`、`scan_rows_caliber.py`、`four_families.py`、`fold_surface.py`、`db_ro.py`。
- **纯函数口径复算**（不开库、不跑 runner）：
  `python -c "from core.judge import _normalize,_cell_eq,_rows_equal; print(_normalize('CoT','agent_dev')==_normalize('COT','agent_dev'), _cell_eq(2.0,2), _cell_eq('2.0','2'), _rows_equal([['engineering']],[['Engineering']]))"` ⇒ `False True False False`（§0 表第三行的四条读数即出自这里）。
- 本单**未跑** pytest（无码改动，判据不需；并发窗禁跑全量，定向也未起，避免同刻 `colony40`／`quant48`／`psy76` 负载不可归因）。
- **A 类两件的改动半径（供人工估代价，本班不据此选边）**：`rg -l "05_cot|05_revert" tests/` → **无命中**（rc=1）；`rg -l "也接受" tests/` → **无命中**（rc=1）；`rg -n "COT|git restore \." tests/` → **无命中**（rc=1）；`content/paths/` 内也**无**这两道题的 id 级引用（题面引用按 topic 粒度）。⇒ 改这两行文案**今天不会让任何测试变红**，其代价全部落在"学生看到的承诺变严"这一可见面。

---

## 5. 遗留与登记

1. **A 类 2 件是"承诺与行为不符"的真缺陷形状**（题面写明可接受、判题写死单值）；与 l927-11 登记的 `README.md:64`「带安全与超时边界」／`ui/pages/home.py:55`（串在 `:57`）「subprocess 隔离」属同一家族（**自述面 vs 实装面**）。该在册冲突本班照旧**只登记不选边**。
2. **数值精度口径不存在成文规则**：B-2 的 `2.0`/`2`、B-6 的 `2.349`/`2.35` 说明"保留几位"目前**随语言执行器的默认打印形状**决定，而不是题面约定 ⇒ 若要立规则属新口径（人工裁）。
3. `expected_rows` 面 `bool` 单元格 0／整值 float 0 ⇒ §0 三条反直觉分支今天**零 exercised**，属"绿但零覆盖"家族在册形态；不因"没实例"就断言它无风险。
4. 锚点 154245 的合并闸（31 道组成员里 10 道被历史记录引用、18 专题全部被 `content/paths/*.yaml` 的 85 条 topic 引用）本班**未重复评估**，只复用了它的题对读数并把 16/7 两数独立复现；合并属写库面＝人工闸。
5. `agent_dev/01_git_basics/05_revert` 与 `05_cot` 的「也接受」句式提示**语料里可能还有未穷尽的同族**（本班只扫了 `也接受|不区分大小写|忽略大小写|大小写不敏感|大小写无关|case-insensitive` 六个词形）；若人工要穷尽，需要再加「亦可|等价写法|同样算对|都算对」等词面重扫，本班未做（超预算内未展开，如实登记）。
6. 本班未代登 insights 索引（真哨兵 `tests/test_insights_index_closure.py`，写本档前 A=B=95 闭合）；本班三档落盘后该桩红 3 例＝主班的账。
