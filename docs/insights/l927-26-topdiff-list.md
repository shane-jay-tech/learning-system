# l927-26 cpp / sql / r 末档难度上抬补题清单（内容侧，只出清单不写题）

> 波次 78 文档位 `learn67`，2026-09-29 磁盘实取。上游：`zcode-bridge/done/l922-06-learn-difficulty-round3.result.md` 遗留 1。
> 姊妹设计稿：`docs/insights/learn-tail-difficulty-design-20260923.md`（l923-28）。**本档与它在 cpp 落点上分歧，分歧已在 §〇.3 摊开。**
>
> 🔴 **本档的边界（越界即白做）**：只出**缺口读数**与**补题清单的形状／题量分配**。
> **不自拟任何题干内容、不自拟任何标准答案／`expected_output`／`expected_rows`**——出题面与题源授权属人工。
> 每道题位的「题干／输入输出／判分标准」三要素在本档只写**该栏必须满足什么**，不写**内容是什么**。
> 题库 yaml、`core/`、`tests/`、`plan.md`、数据库**零改动**（本档只新增此一枚 `.md`）。

---

## 〇、锚点复核（三条成立、三条漂移、一条撞规范）

取数时刻 2026-09-29 07:5x，仓 `D:\code\learning-system`，分支 `main`，HEAD `9a2e6be`，`git status --porcelain` 现值 **0 行**（干净）。

### 0.1 成立的部分

| 卷宗锚点 | 磁盘现值 | 判定 |
|---|---|---|
| 「cpp 收官 10-13 号 topic 各挑 1-2 题」的前提＝这四个 topic 停在 3 档 | 逐 topic 实测 `max difficulty` 全为 3（§二.2） | ✅ 成立，零漂移 |
| 「sql/r 各只有 1 题真 4 档，＝单点，任何一次改标就清零」 | sql d4=1、r d4=1，cpp d4=0（§一.1 逐格对平） | ✅ 成立 |
| 「cpp 该分支永久不可达」（指 `difficulty >= 4` 的 SRS ease 惩罚） | cpp d4＋d5 实测 0 题 | ✅ 成立 |

### 0.2 漂移的部分（按磁盘实况修正并留痕）

| 锚点原值 | 磁盘现值 | 漂移原因 |
|---|---|---|
| 全库 399 题 | **403** | l923-03 于 2026-09-23 给 `python/20_numpy_basics`＋`21_datetime_ts` 各补 2 题（121→125）。`399` 作为**等值断言已消失**，只剩 `tests/test_scripts.py:310 assert total_problems >= 399` 一条下界护栏（纯增量补题不红） |
| SRS 惩罚在 `core/progress.py:378` | **`core/progress.py:404`**（`if difficulty >= 4:`，惩罚体在 `:405`） | 行号 +26；断言面本身成立 |
| `PINNED_TOP_TIER` 17 题（4 档 16＋5 档 1） | 仍 **17 题**，逐 id 实测对平（§一.2） | 末档名单零漂移，只有总数漂 |

### 0.3 🔴 与姊妹稿 l923-28 的落点分歧（必须先裁，不定则清单落不了地）

同一件事有两份在册档给了**不同的 cpp 落点**：

- **l922-06 遗留 1（＝本单卷宗的锚点）**：「cpp 收官 **10-13 号 topic** 各挑 1-2 题」⇒ 落点＝`10_templates` / `11_exceptions` / `12_file_io` / `13_move_semantics`，动词是「**挑**」。
- **l923-28 §三.2**：cpp 候选选的是 `09_operator_overload` / `07_pointers_class` / `08_inheritance` / `04_functions`（选择器＝「3 档题最多的 topic」），并明说「**新增，不从 3 档改档**」，动词是「**补**」。

两组的 topic **交集为空**。本档按**卷宗**（§九 冲突口径：卷宗正文优先）以 **10-13 ＋ cpp 走「挑」＝改档**为主形状出清单，同时把 l923-28 的「新增」路线作为**并列备选**给出代价对照（§三）。
⇒ **这条落点与机制之争属人工裁决**，本档不替它拍（§六.1）。

### 0.4 🔴 撞在册规范：`plan.md` 现在写的是「新题难度建议 ≤3」

```
$ grep -n "新题难度建议" plan.md
62:- **新题难度建议 ≤3**：`difficulty >= 4` 会扩宽 `core/progress.py` 的 SRS ease 惩罚可达面并连带要求改 `PINNED_TOP_TIER`（…）。SRS/判题属红线域，补题不得顺手扩。
```

⇒ **本单的使命（上抬到 4 档）与 `plan.md:62` 的在册口径正面冲突**；而 `plan.md:37` 自称是「『补题』这一类改动的**唯一授权口径落点**」。
本档**不改 `plan.md`**（改在册件＝越权），只点名：**sql／r 的新增题位（§三 B 组）在 `plan.md:62` 被放行之前一律不可开工**；
cpp 的改档题位（§三 A 组）不新增题、不受该条约束（该条管的是「新题」），但受 §六.2 的人工闸。

---

## 一、缺口读数（全为磁盘实跑，无抽样）

### 1.1 逐语言 × 逐档直方（现值）

```
$ PYTHONIOENCODING=utf-8 python -c "…load_language 遍历计数…"
python     d1=27 d2=58 d3=33 d4=7  d5=0  n=125
sql        d1=12 d2=22 d3=19 d4=1  d5=0  n=54
cpp        d1=10 d2=31 d3=21 d4=0  d5=0  n=62
r          d1=15 d2=37 d3=31 d4=1  d5=0  n=84
agent_dev  d1=11 d2=32 d3=27 d4=7  d5=1  n=78
TOTAL 403
```

与 `tests/test_content_difficulty_pins.py:32 PINNED_HIST` **25 格逐格对平**，快照未过期。

| 语言 | d3→d4 断层比 | 末档占比 | 缺口定性 |
|---|---|---|---|
| **cpp** | 21 → **0** | **0.0%** | **整档空洞**（d4、d5 皆空） |
| **sql** | 19 → 1 | 1.9% | **单点**（改标即清零） |
| **r** | 31 → 1 | 1.2% | **单点**（同上） |
| python | 33 → 7 | 5.6% | 参照系（形状正常） |
| agent_dev | 27 → 7 | 10.3% | 参照系（唯一有 5 档的语言） |

**填平目标**（对齐 python／agent_dev 的 4:1～5:1 自然比）：cpp／sql／r 各把 d4 抬到 **≥4～5 题**即不再异常。

### 1.2 末档 17 题的分解与 d5 空洞

`python 7 ＋ agent_dev 8 ＋ sql 1 ＋ r 1 ＋ cpp 0 ＝ 17`（`PINNED_TOP_TIER` 逐 id 实测对平）。
**5 档全库仅 1 题**（`agent_dev/11_real_tasks/08_end_to_end`）⇒ 「cpp／sql／r 无 5 档」是**第二层空洞**，本档按卷宗只做 4 档，5 档列为遗留（§六.5）。

### 1.3 🔴 工具链现值（决定性约束，且**只挡新增路线**）

```
$ python -c "import shutil;print('g++',shutil.which('g++'));print('Rscript',shutil.which('Rscript'))"
g++ None
Rscript None

$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_cpp_runner.py tests/test_r_runner.py -rs -q
7 skipped（g++ not available ×4 ＋ Rscript not available ×3）
```

⇒ 本机 **g++／Rscript 双缺**（与 2026-09-23 l923-28 实测同值，未变）。全量基线里那 7 skipped 就是这个集合。
⇒ 新增 cpp／r 的 `run` 题需要**真跑**才能产出 `expected_output` ⇒ 无工具链＝只能猜 ⇒ 撞「不猜期望输出」红线。

**本档对 l923-28 §二 的一处精确化**：该稿把「工具链」排成「cpp／r 末档上抬**整体**不可开工」。
按机制拆开看并不成立——**改档（A 组）不动答案面**，现有 `expected_output` 原样保留 ⇒
**cpp 的 7 个改档题位今天就能落地，不需要 g++**。真正被工具链挡住的只有「新增 `run` 型题」：
sql 3 题位（走 python 内置 `sqlite3`，当场跑真库取期望值）**不受挡**，r 侧只有 `ai_open` 路线不受挡。
⇒ 直接改变批次次序（§四.3）。

### 1.4 🔴  learner 侧影响面实测＝**零**（本档最有用的新读数）

改档会让被改的题从「无 ease 惩罚」变成「有 ease 惩罚」，代价取决于**有多少人已做过这道题**。现值：

```
$ PYTHONIOENCODING=utf-8 python -c "sqlite3 connect file:…?mode=ro"
review_state 0     attempts 15     problems_status 14     rubric_scores 0
attempts by lang: [('python', 6), ('r', 5), ('sql', 4)]     ← cpp 零条
```

`data/progress.db` 全部 `attempts` 明细（14 个不同 problem）：
`python/01_hello_and_vars/01_hello_world`、`python/24_real_world_data/01…04`、
`r/03_dplyr/01_filter`、`r/14_real_world_data/01…04`、`sql/12_people_analytics/01…04`。

⇒ **三条硬结论**：
1. `review_state` **0 行** ⇒ `difficulty >= 4` 的 ease 惩罚**当前对任何人都还没生效过**（一张卡都没有）。
2. **cpp 侧 attempts ＝ 0 条** ⇒ §三 A 组 7 个改档题位**全部零学员历史**，改档无既有学习记录可扰动。
3. sql／r 的既有记录只落在 `12_people_analytics` 与 `14_real_world_data`／`03_dplyr`／`24_real_world_data`，
   与本档候选 topic（sql 的 `06`/`08`/`07`、r 的 `11`/`07`/`16`）**交集为空** ⇒ 新增题位也零影响。

这**否证了 l923-28 §三.1 拒绝改档的第二条理由**（「把学员已做过的题的判分期望一并改掉」）——
按盘上现值，那批「学员已做过的题」只有 14 道，且一道都不在候选里。
（该稿的第一条理由——改档会掏空 3 档——仍成立，本档在 §三 A 组逐题位标注 d3 余量。）

⚠ 口径注意：`ease` 在 `progress.py:396-405` 是**每次复习时从库里读旧值再改**，不是回溯重写 ⇒
改档只影响**该题之后的复习**，不改历史行。

---

## 二、「真 4 档」的档内口径（实测：目前**没有**机读判据）

卷宗要求「按档内口径产出」。本档把「4 档」的可用口径先量了一遍，结论是**结构特征不分离**：

逐语言对照 `difficulty` 3 档 vs 4/5 档的题面结构（中位数，单位＝字符／行数／条数）：

| 语言 | 特征 | 3 档中位 | 3 档 **max** | 4/5 档 | 分离？ |
|---|---|---|---|---|---|
| sql | `statement` 长度 | 115 | **272** | 183 | ❌ 3 档最长者比唯一 4 档题还长 |
| sql | `setup_sql` INSERT 数 | 1 | **15** | 15 | ❌ 3 档 max 已等于 4 档值 |
| sql | `expected_rows` 行数 | 3 | **7** | 1 | ❌ **反向**（4 档反而更少） |
| r | `statement` 长度 | 97 | **322** | 230 | ❌ 同上 |
| r | `hints` 条数 | 3 | 4 | 3 | ❌ 无差 |
| python | `statement` 长度 | 154 | 466 | 171（min **99**） | ❌ 4 档最短者低于 3 档中位 |
| agent_dev | `rubric` 长度 | 157 | 214 | 197.5 | ❌ 区间重叠 |
| 全语言 | `tags`／`starter_code` 行数 | — | — | — | ❌ 无稳定差 |

⇒ **判定：盘上不存在任何一条可机读的「4 档」结构特征**；`difficulty: 4` 是**纯人工语义标**，
唯一载体是 yaml 第 3 行的 `difficulty:` 字段（`content/` 下 `难度\s*[1-5]` 题面标号 0 命中，与 l923-28 §四.10 一致）。

**⇒ 本档对「题量分配」的直接推论**：清单只能钉**落点＋语义要求＋验收形状**，
「这道题到底算不算 4 档」**必须由人工判定并署名**——这与本单「不自拟题目／标准答案」的红线是同一件事的两面。
可交给出题面的**语义下限**（从在册 17 题的实际形态归纳，非机判据）：
① 需要**组合**两个以上已学机制（如 LEFT JOIN ＋ IS NULL ＋ 排序），不是单机制的直接套用；
② 题面必须自带**常见错法辨析**（在册 4 档 sql 题的 `statement` 里就明写「普通 JOIN 会把没交问卷的人直接丢掉」）；
③ 期望输出**短**而推理**长**（4 档题 `expected_rows` 行数中位 1 ＜ 3 档的 3，答案薄、思考厚）。

---

## 三、补题清单（13 题位，每题三要素规格齐）

图例：**A 组＝改档**（挑现有 3 档题改标，零新题、零答案面改动）；**B 组＝新增**（新 yaml，需人工出题＋题源授权）。
「三要素」＝卷宗点名的 题干／输入输出／判分标准 三栏，本档只写**该栏的约束**，不写内容。

### A 组：cpp 10-13 各 1-2 题（7 题位，动词按卷宗＝「挑」）

| # | 落点（现成题，逐字对盘） | 现 d | 目标 | 该 topic 改档后 d3 余量 | 三要素规格（约束，非内容） | 牵连面（会红的桩） | 风险 |
|---|---|---|---|---|---|---|---|
| A1 | `cpp/10_templates/05_specialization` | 3 | 4 | 2→1 | 题干／输入输出／判分标准 **三栏全不动**（沿用现 `expected_output` 与 `judge_mode: run`）；唯一改动＝yaml 第 3 行 `difficulty: 3`→`4` | pins 直方 `:75`／末档名单 `:98`／cpp 现状桩 `:117`／census_cpp 直方 `:52` | 该题 `tests=0`（仅固定输出）⇒ 判分面薄，4 档却只有 1 组断言，人工要认可这个匹配度 |
| A2 | `cpp/10_templates/04_sum_template` | 3 | 4 | 1→0（若与 A1 同做） | 同 A1（三栏不动） | 同 A1 | ⚠ 与 A1 同做 ⇒ `10_templates` 的 **d3 清零**；语言级 d3 仍 21→19 不触 `:89` 下限桩，但 topic 内梯度塌一截，属内容判定 |
| A3 | `cpp/11_exceptions/05_multi_catch` | 3 | 4 | 2→1 | 同 A1 | 同 A1 | 多 catch 顺序类题易出「输出顺序不确定」；现答案面是否承重需人工复核（本档不改答案面，只点名） |
| A4 | `cpp/11_exceptions/03_custom_exception` | 3 | 4 | 1→0（若与 A3 同做） | 同 A1 | 同 A1 | 该题 `tests=1`（有 stdin/stdout 对）⇒ 形态最完备，A 组里最稳的一枚 |
| A5 | `cpp/12_file_io/03_sum_words` | 3 | 4 | **1→0（该 topic 只有这 1 道 3 档题）** | 同 A1 | 同 A1 | 🔴 **`12_file_io` 无第二道 3 档题可挑** ⇒ 卷宗「各挑 1-2 题」的「2」在这一格**靠改档达不到**，只能靠新增（补 B7 位）或承认该 topic 只抬 1 题 |
| A6 | `cpp/13_move_semantics/02_lvalue_rvalue` | 3 | 4 | 2→1 | 同 A1 | 同 A1 | `tests=0`，同 A1 风险 |
| A7 | `cpp/13_move_semantics/03_move_count` | 3 | 4 | 1→0（若与 A6 同做） | 同 A1 | 同 A1 | 「数移动构造发生几次」的输出由**实现细节**决定 ⇒ 人工须确认现 `expected_output` 在任何合规解下都稳定（本档不判、不改） |

**A 组小计**：cpp 4 个 topic，`10`→2、`11`→2、`12`→**最多 1**、`13`→2 ＝ **7 题位**（在「各 1-2 题」窗内）。
**A 组零写题、零新题 ⇒ 不触 §〇.4 的 `plan.md:62`、不需要 g++（§一.3）、learner 影响面 0（§一.4）。**
代价：cpp d3 由 21 → 14（若全做），末档仍只有 4 档一档、d5 空；且「上抬」不增加任何新题面，
**cpp 的题库厚度与覆盖面停在原地**——这是改档路线的固有限额，不是执行问题。

### B 组：sql／r 各 2-3 题（6 题位，动词按卷宗＝「补」）

新增题位一律给「下一个空闲编号」，`06_` 号位在全部 6 个候选 topic 上实测**空闲**（各 topic 现为 `01…05`）。

| # | 落点（新题位） | 目标 d | 选题依据（磁盘实取） | 三要素规格（约束，非内容） | 工具链门 | 牵连面 | 风险 |
|---|---|---|---|---|---|---|---|
| B1 | `sql/06_window_functions/06_*` | 4 | d3=3（全 sql 最厚并列）n=5 | 题干：排序／分组／帧边界的要求**必须逐字写明**（含并列 tie 处理）；输入输出：`setup_sql` 建表＋`expected_rows` 值列表（列序固定）；判分：`judge_mode: run`，**必须带 top-level ORDER BY 且题面排序要求承重** | ✅ 无门（python 内置 sqlite3，期望值可当场跑真库得到） | census_sql `:18`(54)／`:19` 直方／`:20 ROWS_LEN`／`:61`／`:82`(160 total_rows)／`:64` 首行样例 ＋ pins 两处 ＋ `census.py:27` ＋ README | 🔴 行序在册缺陷（`test_sql_roworder_fragile.py` 的 strict-XFAIL）：新题若「剥掉 ORDER BY 仍逐行等于期望」会**加重该名单**；命中集合清空即 XPASS 转红。**该桩不许撤** |
| B2 | `sql/08_exists/06_*` | 4 | d3=3（并列最厚）n=5 | 同 B1；反连接／相关子查询的**语义差**须在题干点明 | ✅ 无门 | 同 B1 | 与现题 `05_except_via_not_exists` 主题相邻 ⇒ 须换新场景（§五 零重复） |
| B3 | `sql/07_cte/06_*` | 4 | d3=2，n=5；备选池 `04_joins`／`10_date_funcs`／`05_subqueries_case`（各 d3=2） | 同 B1 | ✅ 无门 | 同 B1 | 🔴 现题 `07_cte/04_recursive_cte` 已占「递归 CTE」主题 ⇒ 新题**不得再做同名场景**（l923-28 §三.2 同判） |
| B4 | `r/11_survival/06_*` | 4 | d3=4（全 r 最厚并列）n=5 | 题干：精度／小数位须写死；输入输出：`expected_output` **stdout 文本比对**；判分：`judge_mode: run`（取值域只有 `run`／`ai_open`） | ❌ **需 `Rscript`**（否则期望值无从产出＝猜答案，撞红线） | 🔴 r 牵连面最密：census_r `:37`(84)／`:38` 直方／`:90`(fields 70/14/14 ＋ judge 70/14)／`:70` 用例名含 84 ＋ **`test_judge_mode_equivalence.py` 的 7 处计数桩**（`:129` 70、`:130` 14、`:134` 84、`:154` 14、`:262` 70、`:272` 140、`:314` 数据层 84）＋ `test_mark_r_judge_plain.py:568`(84) ＋ pins ＋ `census.py:27` ＋ README | 浮点抖动（§四.4）；survival 输出位数随包版本变 |
| B5 | `r/07_glm/06_*` | 4 | d3=3，n=5 | 同 B4 | ❌ **需 `Rscript`** ＋ MASS 等包 | 同 B4 | 同 B4 |
| B6 | `r/16_mediation/06_*` | 4 | d3=3，n=5；**该 topic 5/5 题全是 `ai_open`**（rubric 长 94～139，均带 `reference_answer`） | 题干：开放题须可被 rubric 逐条判；输入输出：**无 `expected_output`**（`ai_open` 题声明 `expected_output` 会被 `:124` 契约桩判红）；判分：`judge_mode: ai_open` ＋ `rubric` ＋ `reference_answer` | ✅ **不需 Rscript**（机判面本来就不跑 R） | 同 B4，且 `ai_open` 计数 14→15 动 4 处（`:130`/`:154`/`:90` 两字典／`:314`） | 拿不到机验桩；`16_mediation` 现题含 bootstrap CI，随机性属已知不可机验 |

**sql／r 各 3 题 ＝ B1–B3、B4–B6，共 6 题位。** B6 是 r 侧**唯一今天就绕得过工具链门**的题位（走 `ai_open`，代价是永远不进机验面）。

**合计 7 ＋ 6 ＝ 13 题位 ≥ 完成标准 ① 的 10。**

### 题量分配的两条上限（为什么不是一次补 20 题）

1. **每 topic 目标题数＝5** 是 `plan.md:40` 的在册口径（「补到 5 即止，不是补到 6 消除薄」）。
   A 组不新增题 ⇒ 零冲突；**B 组每一题位都把它落点 topic 从 5 抬到 6**，属对 `plan.md:40` 的**有意越界**，须人工点头（`plan.md:40` 也说厚于 5 的 8 个 topic 属「合理厚、不削」⇒ 不是禁止，而是需明示理由）。
2. 卷宗给的是「cpp 各 1-2 题、sql/r 各 2-3 题」＝**8～14 题**窗。本档取 **13**，是窗内可行解中**唯一同时满足 ≥10 与「12_file_io 只能 1 题改档」这条磁盘硬约束**的形状（cpp 若各取 1 ＝4，＋sql 3＋r 3＝10 也达标，但 cpp 抬到 4 题不解决「单点」——cpp 从 0 起，4 题＝比 19:1 断层仍差，见 §一.1 目标比）。

---

## 四、落地代价与批次（形状，不是排期承诺）

### 4.1 三条路线的同批必改点数（机械复算，单位＝处）

| 路线 | 总题数等值点（`census.py:27`＋`pins:84`＋README＋用例名） | 逐语言 census 等值点 | 难度快照／末档 | 现状桩 | r 等价桩 | **合计** |
|---|---|---|---|---|---|---|
| A 组（cpp 改档 7） | **0**（403 不变、cpp 题数 62 不变） | 1（`census_cpp:20 EXPECTED_DIFF`）＋ `:9` 注释 | 3（直方 `:75`／末档 `:98`＋快照 `:41`／census_cpp 直方 `:52`） | 1（**删** `pins:117`） | 0 | **5** |
| sql 新增 3 | 4（403→406 ×2 ＋ README ＋ `census_sql:36` 用例名「题数54」） | 6（`:18`/`:19`/`:20`/`:61`/`:82`/`:64`） | 2（直方＋末档） | 0 | 0 | **12** |
| r 新增（run 型 B4/B5） | 4（403→407 ×2 ＋ README ＋ `census_r:70` 用例名「题数84」） | 4（`:37`/`:38`/`:90` 两字典/`:107`） | 2 | 0 | **7** | **17** |
| r 新增（`ai_open` 型 B6） | 4 | 4 | 2 | 0 | 7（其中 4 处动 `ai_open` 计数） | **17** |

⇒ **单价排序：cpp 改档（5 处，且不动总题数）≪ sql 新增（12）＜ r 新增（17）**。
l923-28 §五.③ 说「r 的牵连面单价最高」——本档把它**从 7 处上修为 17 处**，因为该稿漏了
`tests/test_judge_mode_equivalence.py`（7 个计数桩）与 `tests/test_mark_r_judge_plain.py:568`（§五 复算）。

### 4.2 「删桩」这一处不是可选项

`tests/test_content_difficulty_pins.py:117 test_cpp_无4到5档_是现状而非用例失效()` 的 docstring 原话：
「这样将来补 cpp 难题时这条会红，逼改动者回来改判定档而不是默默留着不一致」。
⇒ A 组一落地它**必红**，正解是**删桩或改写判定档**（不是把断言值改成一个数字蒙过去）。
**本档不撤、不改该桩**——改测试语义属人工闸。
（另注：本档也**不碰**两条 strict-XFAIL 桩 `test_sql_roworder_fragile.py`／`test_paths_order_consistency.py`；现跑 **36 passed ＋ 2 xfailed**，rc=0，见 §五.3。）

### 4.3 建议批次（按「同批必改点数」与「门」排，不按难度排）

| 批次 | 内容 | 前置门 | 为什么先／后 |
|---|---|---|---|
| **〇 裁决** | 人工裁三件事：§〇.3 落点与机制之争、§〇.4 `plan.md:62` 与末档上抬的冲突、§六.2 的 4 档定档署名 | 无 | 三件事任一没裁，下面任何一批都不该动 |
| **一 cpp A 组 7 题位** | 只改 7 行 `difficulty`，同批 5 处 | `pins:117` 处置方案定下来 | **唯一同时满足「不需工具链／不新增题／learner 影响面 0／不动 403」的批次**，把 cpp 从 0 拉到 4～7，直接消掉「整档空洞」 |
| **二 sql B1–B3** | 新 3 题 | `plan.md:62` 放行 ＋ 行序约束（题面排序须承重） | 期望值可当场跑真库，不猜；牵连 12 处但**无外部依赖** |
| **三 r B6**（`ai_open` 1 题） | 新 1 题 | `plan.md:40` 越界点头 | r 侧**不需装 R** 就能做的唯一题位；先拿它把 r 的 d4 从 1→2 解除「单点」 |
| **四 r B4／B5** | 新 2 题 | **装 `Rscript`**（现值 None，7 skipped） | 工具链没装就只能停在纸面；本档只登记缺口，**未安装任何东西** |
| **五 收口** | 全量复跑 ＋ README/口径同步 | 前四批完成者 | — |

与 l923-28 §五 的差别只有一处、但很关键：**该稿把 cpp 排在批次三（最慢）**，理由是「cpp 高档题需要 g++ 取期望值」。
按机制拆开看，**cpp 走改档就不需要 g++**（§一.3）⇒ 本档把 cpp 提到批次一。若人工裁的是「cpp 也走新增」，则 l923-28 的排序回位、cpp 重新被工具链挡死。

### 4.4 判分形态约束（出题面必须吃的形状，本档不代答）

- **sql**：判分是 `expected_rows` **按位置逐行比对**（`core/judge.py` 的 `_rows_equal`）⇒ 题面若不写死排序，判分就依赖引擎返回序。这是 §四.6 在册缺陷，新题**不得再往里加**。
- **r／cpp**：期望输出必须是**确定性可打印量**，浮点一律写死到固定小数位（现题做法：题面显式 `round(...)`）；指针地址、`anova()` 行序、bootstrap CI 天然不可机验 ⇒ 这类主题要么改题意，要么走 `ai_open`。
- **r 的取值域**：`judge_mode` 合法值**只有 `run`／`ai_open`**（`test_契约_judge_mode取值合法()`），且「机判多结果」这条路是用户 **D6 拍板关掉的**（`scripts/mark_r_judge_plain.py` docstring：「r 实际判定面是 expected_output 70 ＋ rubric/journal 14」）⇒ 想要「多对象机判」＝翻拍板，**不在补题单授权内**。

---

## 五、零重复自证（完成标准 ②）

1. **A 组 7 题位**：落点是 **7 道现存题本身**（改档＝不新增，定义上无重复对象）。逐题 id 对盘存在性已验：
   `cpp/10_templates/{04_sum_template,05_specialization}`、`cpp/11_exceptions/{03_custom_exception,05_multi_catch}`、
   `cpp/12_file_io/03_sum_words`、`cpp/13_move_semantics/{02_lvalue_rvalue,03_move_count}` ＝ **7/7 命中，零虚构**。
2. **B 组 6 题位**：编号一律取该 topic 的**下一个空闲位** `06_`。磁盘 `ls` 实测 6 个候选 topic
   （`sql/06_window_functions`、`sql/08_exists`、`sql/07_cte`、`r/11_survival`、`r/07_glm`、`r/16_mediation`）
   现有文件均为 `01…05` ⇒ **`06_` 号位 6/6 空闲，零碰撞**。
3. **主题级避让**（题面未写，故这里钉的是「不得重复的场景」）：
   `sql/07_cte` 已占递归（`04_recursive_cte`）、`sql/08_exists` 已占 EXCEPT 反连接（`05_except_via_not_exists`）、
   `cpp/13_move_semantics` 已占移动计数（`03_move_count`）与左值右值重载（`02_lvalue_rvalue`）、
   `r/16_mediation` 已占有调节中介（`04_moderated_mediation`）⇒ 对应题位**必须换新场景**，人工出题时在出处行里写明参照的是哪一道同族题。
4. **在库题 id 唯一性**：`cpp+sql+r` 现共 **200 题**，id 全不重复（`core/loader.py` 的 id ＝ `<lang>/<topic>/<prob>` 三段拼接，`tests/test_content_ids_unique.py` 在册守着；跨语言同名裸 slug 由 l918-28 拍板允许）。
5. **定向基线现跑**（本档只跑点名件，未跑全量，守并行纪律）：
   `PYTHONIOENCODING=utf-8 python -m pytest tests/test_content_difficulty_pins.py tests/test_content_census.py tests/test_content_census_cpp.py tests/test_content_census_sql.py tests/test_content_census_r.py tests/test_content_thin_topic_p0.py tests/test_sql_roworder_fragile.py tests/test_paths_order_consistency.py -q`
   ⇒ **36 passed, 2 xfailed in 3.25s**（rc=0；两条 xfail 均在册、未撤桩）。

---

## 六、待人工（超出执行手授权，本档一律不动）

1. 🔴 **落点与机制之争**（§〇.3）：cpp 到底按 l922-06 走「10-13 改档」，还是按 l923-28 走「04/07/08/09 新增」。
   两组 topic 交集为空，且本档已量出两条路线的必改点数差 **5 vs 12～17**——这个差不该由执行手消化。
2. 🔴 **「这道题算 4 档」的定档署名**（§二）：盘上无机读判据，只能人工判。每枚改档／新增题位的 d 值需人工签字，
   并同步 `PINNED_TOP_TIER`（`tests/test_content_difficulty_pins.py:41`）。
3. 🔴 **`plan.md:62`「新题难度建议 ≤3」与 `plan.md:40`「每 topic 目标题数＝5」两条在册口径，B 组同时越界**（§〇.4、§三末）。
   本档不改 `plan.md`。放行则需在该节留一次明示例外，否则下一班执行手会照 §〇.4 停手。
4. 🔴 **`pins:117` 现状桩的处置**（删桩 vs 改写判定档），§四.2。本档不撤桩。
5. **5 档空洞**：cpp／sql／r 三语言 d5 全空，全库仅 agent_dev 1 道 5 档。卷宗只交代 4 档 ⇒ 5 档本档不动，登记为下一层缺口。
6. **工具链安装**（`g++`／`Rscript`）：卷宗「禁止下载安装依赖」⇒ 本档**只登记缺口（现值双 None ＋ 7 skipped）**，未装。批次四依赖它。
7. **r 的 `ai_open` 路线是否接受**「上抬一档但永远进不了机验面」（B6）。属内容口径，交人工。
8. **并发提醒**：姊妹单 `l927-27`（thin-topic P0 9 题，落点 `content/cpp/01_io_and_vars`／`02`）**仍在 inbox 未认领**，
   其 2026-09-28「答案域授权自拟」拍板**限定那 9 题与那两个目录**，**不覆盖**本档的 cpp 10-13 与 sql／r 题位。
   若 `l927-27` 先落地，cpp 总题数 62 会变 ⇒ 本档 §四.1 的「不动总题数」对 A 组仍成立（A 组不新增），
   但 `EXPECTED_PROBLEMS=62`／`census.py:27` 的 403 会被它先改掉，届时所有行号需现取。

---

## 附：复算命令（每条都能独立跑出本档引用的读数）

```bash
cd /d/code/learning-system

# F1 25 格直方 ＋ 全库 403（§一.1）
PYTHONIOENCODING=utf-8 python -c "import collections;from core.loader import load_language;[print(l,collections.Counter(p.difficulty for t in load_language(l,'content') for p in t.problems)) for l in ('python','sql','cpp','r','agent_dev')]"

# F2 末档逐 id（§一.2）
PYTHONIOENCODING=utf-8 python -c "from core.loader import load_language;print({l:[p.id for t in load_language(l,'content') for p in t.problems if p.difficulty>=4] for l in ('cpp','sql','r','python','agent_dev')})"

# F3 工具链（§一.3）
python -c "import shutil;print('g++',shutil.which('g++'),'Rscript',shutil.which('Rscript'))"
PYTHONIOENCODING=utf-8 python -m pytest tests/test_cpp_runner.py tests/test_r_runner.py -rs -q

# F4 learner 影响面（§一.4；只读连接，零写）
PYTHONIOENCODING=utf-8 python -c "import sqlite3;c=sqlite3.connect('file:D:/code/learning-system/data/progress.db?mode=ro',uri=True);print([ (t,c.execute('select count(*) from '+t).fetchone()[0]) for t in ('review_state','attempts','problems_status','rubric_scores') ])"

# F5 cpp 10-13 逐 topic ＆ 候选题（§二.2、§三 A 组）
PYTHONIOENCODING=utf-8 python -c "from core.loader import load_language;[print(t.slug,{p.id.split('/')[-1]:(p.difficulty,p.judge_mode,len(p.tests or [])) for p in t.problems}) for t in load_language('cpp','content') if t.slug in ('10_templates','11_exceptions','12_file_io','13_move_semantics')]"

# F6 3 档 vs 4/5 档结构对照（§二，逐语言不池化）
#   探针：tmp/learn67/probe_tier_caliber2.py（不入库，tmp/ 已在 .gitignore）

# F7 牵连面计数（§四.1、§五）
grep -n "PINNED_HIST = {\|PINNED_TOP_TIER = {\|^def test_\|== 403" tests/test_content_difficulty_pins.py
grep -n "^EXPECTED\|def test_" tests/test_content_census_cpp.py tests/test_content_census_sql.py tests/test_content_census_r.py
grep -n "assert len(stripped) == 70\|assert len(kept) == 14\|== 84\|== 140\|def test_" tests/test_judge_mode_equivalence.py
grep -n "== 84" tests/test_mark_r_judge_plain.py
grep -n "assert total == 403" tests/test_content_census.py
grep -n ">= 399" tests/test_scripts.py
grep -n "403 题" README.md
grep -n "新题难度建议\|每 topic 目标题数" plan.md

# F8 定向基线（§五.5）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_content_difficulty_pins.py tests/test_content_census.py tests/test_content_census_cpp.py tests/test_content_census_sql.py tests/test_content_census_r.py tests/test_content_thin_topic_p0.py tests/test_sql_roworder_fragile.py tests/test_paths_order_consistency.py -q
```
