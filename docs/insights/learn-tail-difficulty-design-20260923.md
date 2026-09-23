# cpp / sql / r 末档（4/5 档）难度上抬补题设计稿（l923-28，2026-09-23）

> **本班否证一条纪律档交底**：纪律档 §十七 写「learning＝全量 ~57s（现值 731）」，磁盘现取全量是
> **823 passed / 7 skipped / 2 xfailed（rc=0，68.66s）**。引用前一律现取。
>
> 🔴 **本档有第一稿，且第一稿被整体作废重做**。第一稿里「`starter_code` 自带『难度 N』标号 2668 处」
> 以及据此派生的 4 条主张（cpp 61/62、sql 54/54、python 357/399 标号一致、scripts 里 14/15 件残留
> `repeat(`）**按磁盘实况全部不成立**（全库 `难度\s*[1-5]` 只有 11 处命中、分布在 5 个文件，
> **content/ 下 0 处**）。作废原因见第六节第 1 条，复算命令见附录 A9/A11。
> 本档正文只留**能在磁盘上重新跑出同一读数**的行。
>
> 取数时刻：2026-09-23 13:58–14:05，HEAD `6c7cd28`（工作树除本班 `tests/test_hr_dataset_determinism.py`
> 外与 HEAD 逐字节相同）。**行号一律 `grep -n` 口径**（本仓多个 .py 是 CRLF 主导，python
> `splitlines()` 会把 lone CR 也当换行 ⇒ 与 `sed`/`grep` 的行号可能不等，见第六节第 4 条）。
> 纪律档 §廿三 自己就说「盘在动」是常态：**引本档行号前先跑附录 A1 那一组复算命令。**

---

## 〇、卷宗锚点复核（前提即待验命题）

| 卷宗锚点 | 卷宗行号 | 磁盘现值 | 判定 |
|---|---|---|---|
| `tests/test_content_difficulty_pins.py:29` `PINNED_HIST = {` | 29 | **:32** | ✅ 成立，行号 +3 |
| 同件 `:31` sql 行（`{1: 12, 2: 22, 3: 19, 4: 1, 5: 0},    # 54`） | 31 | **:34**（五行均在，逐字相符） | ✅ 成立，行号 +3 |
| `docs/insights/learn-difficulty-histogram-20260921.md:1` 标题 | 1 | :1 逐字相符 | ✅ 成立 |
| 三语言实测 cpp `{1:10,2:31,3:21}` / sql `{…,4:1}` / r `{…,4:1}` | — | 与 `PINNED_HIST` **逐格对平** | ✅ 成立（见 §一） |
| 「4 档 cpp 0 / sql 1 / r 1，5 档三门全 0」 | — | 逐语言实测同值 | ✅ 成立 |
| 「census 399 等值点（若 l923-03 已落地则 403）」 | — | 现读 **403**，且在**两处**（`test_content_census.py:27`、`test_content_difficulty_pins.py:84`）；**399 已无等值断言**，只剩 `tests/test_scripts.py:310 assert total_problems >= 399` 一条**下界护栏**（补题不红）＋ 若干历史注释 | ✅ **l923-03 已落地**；卷宗说的"399 等值点"已不存在 |
| `core/judge.py:97` `_rows_equal` / `:220` 调用 | 97 / 220 | **:96 / :219** | ✅ 断言面成立，行号 −1 |
| `tests/test_sql_roworder_fragile.py:30` `_top_level_positions` | 30 | **:27**（xfail 桩函数在 **:140**） | ✅ 件与函数在册，行号 −3 |
| sql / r 末档题 `difficulty: 4` 在 :4 | 4 | **:3**（两件皆然） | ✅ 值在册，行号 −1 |
| `scripts/mark_r_judge_plain.py:53` `def detect(` | 53 | **无此函数**。实际：`_judge_mode_lines` :255 / `scan` :311 / `prepare_one` :363 | ❌ **锚点不成立**（不影响前提结论，见 §三.7） |

**另三条不在卷宗清单内、但比清单更硬的发现：**

1. 卷宗的牵连面清单**漏了本仓专门为「补 cpp 难题」立的一条拦路桩**：
   `tests/test_content_difficulty_pins.py:117 test_cpp_无4到5档_是现状而非用例失效()`，
   其 docstring 原话：「cpp 末档=3 是本单判定的**内容空洞**（不是设计口径），单独钉一条，
   这样将来补 cpp 难题时这条会红，逼改动者回来改判定档而不是默默留着不一致」。
   ⇒ 补 cpp 4 档题**当场必红两条**（`:75` 直方 + `:117` 现状桩），且 `:117` 的正解是**删桩**，不是改断言值。
2. `test_content_difficulty_pins.py:89 test_分布下限_每语言覆盖1到3档()` ⇒ 上抬若是「把 3 档题**改成** 4 档」，
   当该 topic/语言 3 档被掏空时会连带踩这条。**挪档比新增更容易红。**
3. `test_content_difficulty_pins.py:98 test_末档_ge4_题id名单_钉死()`（快照在 `:41 PINNED_TOP_TIER`）
   ⇒ 新增 4/5 档题**必须逐 id 登记**，docstring 自己承认「新增难题是好事，但必须显式动这个快照
   （连带 SRS ease 惩罚的可达面一起扩大）」。

---

## 一、三语言末档现状量化（现值复算，与 `PINNED_HIST` 逐格对平）

### 1.1 复算命令与读数（完成标准 ①）

```
$ PYTHONIOENCODING=utf-8 python -c "import collections;from core.loader import load_language;H={'python':{1:27,2:58,3:33,4:7,5:0},'sql':{1:12,2:22,3:19,4:1,5:0},'cpp':{1:10,2:31,3:21,4:0,5:0},'r':{1:15,2:37,3:31,4:1,5:0},'agent_dev':{1:11,2:32,3:27,4:7,5:1}};G={l:{d:sum(1 for t in load_language(l,'content') for p in t.problems if p.difficulty==d) for d in range(1,6)} for l in H};[print(l,'实算',G[l],'钉',H[l],'对平',G[l]==H[l]) for l in H];print('全库题数',sum(sum(v.values()) for v in G.values()))"
python    实算 {1: 27, 2: 58, 3: 33, 4: 7, 5: 0}  钉 同  对平 True
sql       实算 {1: 12, 2: 22, 3: 19, 4: 1, 5: 0}  钉 同  对平 True
cpp       实算 {1: 10, 2: 31, 3: 21, 4: 0, 5: 0}  钉 同  对平 True
r         实算 {1: 15, 2: 37, 3: 31, 4: 1, 5: 0}  钉 同  对平 True
agent_dev 实算 {1: 11, 2: 32, 3: 27, 4: 7, 5: 1}  钉 同  对平 True
全库题数 403
```
⇒ **五语言 × 五档 25 格逐格对平，全库 403 与 `test_content_census.py:27` 一致。快照未过期。**

### 1.2 末档形状（5 科对照）

| 语言 | 题数 | d1 | d2 | d3 | **d4** | **d5** | 末档（≥4）占比 | 与上档断层 |
|---|---|---|---|---|---|---|---|---|
| cpp | 62 | 10 | 31 | 21 | **0** | **0** | **0%** | d3=21 → d4=0（**整档空洞**） |
| sql | 54 | 12 | 22 | 19 | **1** | **0** | **1.9%** | d3=19 → d4=1（19:1） |
| r | 84 | 15 | 37 | 31 | **1** | **0** | **1.2%** | d3=31 → d4=1（31:1） |
| python | 125 | 27 | 58 | 33 | 7 | 0 | 5.6% | d3=33 → d4=7（4.7:1） |
| agent_dev | 78 | 11 | 32 | 27 | 7 | 1 | 10.3% | d3=27 → d4=7（3.9:1） |

**末档 17 题的全库分解**（= `PINNED_TOP_TIER` 的 16 个 4 档 + 1 个 5 档，逐 id 实测对平）：
`python 7` + `agent_dev 8` + `sql 1` + `r 1` + `cpp 0` = **17**。

### 1.3 两个末档独苗的判分面（`grep -n` + loader 实测）

| 题 | difficulty | judge_mode | 答案面 | 判分依赖 |
|---|---|---|---|---|
| `sql/12_people_analytics/04_never_submitted` | :3 `difficulty: 4` | `run` | `expected_rows=True` / `expected_output=False` | **行序逐行比对**（sqlite 无 top-level ORDER BY 不保证序）⇒ 见 §四.6 |
| `r/14_real_world_data/04_group_avg` | :3 `difficulty: 4` | `run` | `expected_output=True` / `expected_rows=False` | **stdout 文本比对**（r 侧 D6 已拍板「降级为普通题」，见 §四.7） |

### 1.4 判分器可用性（**这是全案最强的约束**）

| 语言 | runner 依赖 | 本机可用性 | 实测证据 |
|---|---|---|---|
| sql | python 内置 `sqlite3` | ✅ 可用 | `test_content_census_sql.py` **6 例真跑绿**（`:64 test_expected_rows形态与行数直方图精确()` 逐题跑内存 sqlite 取 160 行读数） |
| python | `python` + 沙箱 | ✅ 可用 | 全量 823 例绿 |
| **cpp** | **`g++`** | ❌ **缺失** | `test_cpp_runner.py:13 pytestmark = skipif(not _gpp_available())` → **4 例 SKIPPED**，reason `g++ not available` |
| **r** | **`Rscript`** | ❌ **缺失** | `test_r_runner.py:10` 同型 → **3 例 SKIPPED**，reason `Rscript not available` |

```
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_cpp_runner.py tests/test_r_runner.py -rs -q
7 skipped （g++ not available ×4 / Rscript not available ×3）
```
⇒ 全量基线里那 **7 skipped 就是这个集合**（与 823 基线同型，非本班引入）。
⇒ **cpp 4/5 档题在本机无法机验，r 同理。** 后果见 §二（这是本设计稿的主结论）。
  **在册旁证**（不是本班新发现的口径）：`tests/test_content_thin_topic_p0.py:51` 注释原话「cpp 两目录仍是薄的（**本机无 g++，参考答案无法机验，留日间班**）」——cpp 侧补题被工具链挡住这件事，l922-07/l922-128 已经登记过，本档把它**升格为排序第一键**。

---

## 二、末档为什么一直空着：一条行为事实 + 一条工具链事实

**行为事实（卷宗点到的那一条，实测复核成立）**
`core/progress.py:378-379`：
```python
            if difficulty >= 4:
                ease = max(1.5, ease - 0.1)
```
（同函数 `:383` 另有 `ease = max(1.5, ease - 0.2)` 分支，属另一条件，本档不判。）
末档（≥4）可达面实测：cpp **零题**、sql/r **各 1 题**、python 7、agent_dev 8。

**⇒ 本班对 l922-06 那句判定做一处精确化**：「cpp 侧该分支永久不可达」成立，但「补 4/5 档 = 无声扩大
SRS 惩罚面」这个担忧**已被 `test_末档_ge4_题id名单_钉死`(:98) + `test_cpp_无4到5档`(:117) 两道桩拦住**
——新增即红、且必须逐 id 登记。所以真实成本不是"无声"，而是**「要同批改 4 处快照 + 删 1 条现状桩」**
（清单见 §四）。设计口径因此可以是「可控地扩」，而不是「不敢扩」。

**工具链事实（卷宗未提，是本案的决定性约束）**
cpp/r 的 `expected_output` 需要**真跑**才能得到。本机无 g++/Rscript ⇒ 任何 cpp/r 高档题的期望输出
只能**手算/猜** ⇒ 直接撞本分区红线（「不猜期望输出」）+ 台账 73（全仓无一条测试把 `expected_output`
绑参考解）。**⇒ cpp/r 的末档上抬在装好工具链之前不可开工**，否则产出的是一批「绿但可能错」的题。
这是 §五 批次次序的第一排序键。

---

## 三、目标形状与候选 topic（12 条，每条附磁盘实测）

### 3.1 目标形状（方案，未拍板）

| 语言 | 现状 4/5 档 | 建议目标 4/5 档 | 新增题量 | 前置门 |
|---|---|---|---|---|
| sql | 1 / 0 | **4 档 ≥5，5 档 1** | 4 + 1 = **5 题** | 无（sqlite 可用）⇒ **唯一现在就能开工的** |
| r | 1 / 0 | **4 档 ≥5，5 档 1** | 4 + 1 = **5 题** | 装 `Rscript`（且须回应 D6 拍板，§四.7） |
| cpp | 0 / 0 | **4 档 ≥5，5 档 1–2** | 5 + 1~2 = **6~7 题** | 装 `g++`（MinGW-w64/MSYS） |

- **新增，不从 3 档改档**：改档会同时掏空 3 档，撞 `test_分布下限_每语言覆盖1到3档`(:89)，
  且把学员已做过的题的判分期望一并改掉（属行为改动）。**每语言 6 题量级即可填平，不必扩库。**
- 目标值取「≥5」而非「≥10」：三门现有 d3 分别是 21/19/31 题，5 题即把断层比从 19:1~31:1 降到 ≈4:1，
  与 python（4.7:1）/agent_dev（3.9:1）**自然对齐**，不引入新的形状异常。
- **5 档三门各 1 题试水**（共 3 题）：agent_dev 已验证「4 档 ≥5 + 5 档 1」这套形状可用。
- 若只补 4 档，三门仍无 5 档 ⇒ 「5 档空洞」保留在三门。属**部分达标**，本档如实标注，不粉饰。

### 3.2 候选清单（按「3 档题最多的 topic」排序；d3 题号与判分面均磁盘实取）

**cpp（全部 `judge_mode: run` + `expected_output`）**

| topic | n | d1/d2/d3 | 现有 3 档题（实测名） | 其中带 `tests`（stdin/stdout 对） | 4/5 档候选主题 | 风险 |
|---|---|---|---|---|---|---|
| 09_operator_overload | 5 | 0/2/3 | `03_stream_out` `04_subscript` `05_functor` | 2（03、05） | 4：复数/矩阵类型全套运算符 + 转换运算符；5：表达式模板雏形 | 与 `05_functor` 主题重叠 |
| 07_pointers_class | 5 | 0/2/3 | `03_class_basic` `04_unique_ptr` `05_shared_ptr` | 1（03） | 4：自定义删除器 + 循环引用 weak_ptr 断环；5：手写 Rule-of-Five + 移动语义联动 13 | 输出含指针地址 ⇒ **不可机验**，须设计成确定性可打印量 |
| 08_inheritance | 5 | 0/2/3 | `02_virtual` `04_abstract_class` `05_virtual_dtor` | 1（04） | 4：虚基类/菱形继承偏移与调用序；5：多态克隆 + 类型擦除小容器 | 同上，须避免地址/顺序不确定输出 |
| 04_functions | 5 | 1/1/3 | `03_factorial_recursion` `04_is_prime` `05_swap_ref` | **3/3** | 4：模板函数 + 递归 + 记忆化；5：手写 `std::function` 组合器 | **3/3 已带 tests** ⇒ 该 topic 是 cpp 侧形态最完备的落点 |

**sql（全部 `run` + `expected_rows`，`tests` 均为 0）**

| topic | n | d1/d2/d3 | 现有 3 档题 | 4/5 档候选主题 | 风险 |
|---|---|---|---|---|---|
| 08_exists | 5 | 0/2/3 | `03_correlated_count` `04_exists_and` `05_except_via_not_exists` | 4：三段相关 NOT EXISTS + 反连接对比；5：用 EXISTS 改写窗口题并互验 | 判分期望是**行集**，须带 top-level ORDER BY |
| 06_window_functions | 5 | 0/2/3 | `03_running_sum` `04_lag` `05_top2_per_class` | 4：`NTILE`+帧边界 `ROWS BETWEEN`；5：会话切分（gap-and-sessions） | **行序承重**（§四.6），且 `05_top2_per_class` 与既有 `05_*` 主题部分重叠 |
| 07_cte | 5 | 1/2/2 | `03_cte_window` `04_recursive_cte` | 4：带环防护的递归 + 物化多引用；5：递归 + 窗口 + EXISTS 综合 | `04_recursive_cte` 与 `07_cte/04` 现题**同名主题** ⇒ 必须换新场景 |
| 04_joins | 5 | 1/2/2 | `04_three_table_join` `05_join_groupby` | 4：自连接 + 外连接差集；5：多对多桥表 + 分组去重计数 | 无 |

**r（全部 `run` + `expected_output`，除 16_mediation；`tests` 均为 0）**

| topic | n | d1/d2/d3 | 现有 3 档题 | 4/5 档候选主题 | 风险 |
|---|---|---|---|---|---|
| 11_survival | 5 | 0/1/4 | `02_survfit_median` `03_logrank` `04_cox_hr` `05_cox_multivar` | 4：分层 baseline + `cox.zph` 假设检验读数；5：时依协变量 | **d3=4，与 `06_mixed_apa` 并列全 r 最厚**；4 道 3 档题全 `run`+`expected_output`，但 survival 输出精度位数 ⇒ 浮点抖动（§四.9） |
| 06_mixed_apa | 6 | 1/1/4 | `01_lmer_fixef` `03_cohens_d` `04_eta_squared` `05_apa_t` | 4：`emmeans` 对比 + 简单效应；5：跨模态交互解释（APA 表） | `anova()` 行序、随机效应报告格式随 lme4 版本变 ⇒ 期望不稳 |
| 07_glm | 5 | 0/2/3 | `02_odds_ratio` `04_predict_prob` `05_pseudo_r2` | 4：偏差残差诊断 + 离群杠杆点；5：正则化/`stepAIC` 序列 | 需 MASS/nnet 等包（本机无 R ⇒ 不可验） |
| 16_mediation | 5 | 1/1/3 | `02_bootstrap_test` `03_report_mediation` `04_moderated_mediation`（**整 topic 5 题全是 `ai_open`**，rubric 长 120/94/130，均带 `reference_answer`） | 4/5：有调节的并行多重中介（只能走 `ai_open`+rubric） | **bootstrap CI 随机 ⇒ 天然不可机验**；本 topic 已在开放题路线上，上抬不新增机验债，但也拿不到 `expected_output` 类机桩 |

**12 条候选（cpp 4 + sql 4 + r 4），满足完成标准 ②「≥6 条附实测算据」。**

⚠️ **候选选择器必须按「题数/判分形态」手工指定，不能按字符串排序**：三门的 3 档题最多的 topic 恰是
`09_operator_overload` / `08_exists` / `11_survival`，若按字典序取 top-4 会漏掉它们。本班实测踩过一次，
复算命令用显式 topic 名单（附录 A5），并在 §三.3 把 12 条落点全部列出。

---

## 四、牵连面清单（逐条文件:行号 + 磁盘复核）

### 4.1 难度快照与现状桩（`tests/test_content_difficulty_pins.py`）
- `:32 PINNED_HIST` → `:75 test_逐语言难度直方_钉死()`（任一档增删即红）
- `:41 PINNED_TOP_TIER` → `:98 test_末档_ge4_题id名单_钉死()`（4 档 16 个 id / 5 档 1 个，**须逐 id 登记**）
- `:117 test_cpp_无4到5档_是现状而非用例失效()` → **补 cpp 4 档即红，正解是删桩**（docstring 原话）
- `:89 test_分布下限_每语言覆盖1到3档()` → 改档（而非新增）时踩
- `:80 test_合计403与直方自洽()` → 403 等值点之二

### 4.2 全库题量等值点（403）与 README
```
$ git grep -n "== 403" -- tests/ ; git grep -n "403" -- README.md | head -3
tests/test_content_census.py:27:    assert total == 403, f"题库总量漂移：{total} != 403（README 官方口径，变更须有意）"
tests/test_content_difficulty_pins.py:84:    assert sum(per_lang.values()) == 403, per_lang
README.md:52:- 5 种语言并行学，进度独立；403 题、85 知识点、6 条学习路径（…补题需同批同步的等值点清单见 `plan.md`「题库内容规范」）。
```
⇒ 补 13 题（4+5+…）要同批改 **census 1 处 + pins 2 处 + README 口径 1 处**；
`git grep -n "399" -- tests/` → 11 处（实测 `wc -l`），**全是注释/历史叙述 + 一条下界护栏**：`tests/test_scripts.py:310 assert total_problems >= 399`（下界，补题不红；`test_content_thin_topic_p0.py:60` 的注释也明说「补题无需改它」）。⇒ **399 作为等值断言已消失**，403 的等值点在 `census.py:27` 与 `pins:84` 两处。
**注**：`test_report.py` 与 insights 数量**无关**（该文件现跑 5 例、全是报告用例，无 insights 计数断言，
现读 `def test_report_markdown_format():` 在 :34）——本班第一稿把它写成「钉 27 份」是错的，已作废（§六.1）。

### 4.3 cpp 侧必改清单（`tests/test_content_census_cpp.py`，**5 处**）
`:18 EXPECTED_TOPICS=13` / `:19 EXPECTED_PROBLEMS=62` / `:20 EXPECTED_DIFF={1:10,2:31,3:21}`（**无 4/5 键**）
→ `:52 test_difficulty直方图精确()` 必红；另 `:44 test_topic_slug集合精确()`（若新建 topic 目录）、
`:57 test_tests形态_stdin_stdout对精确()`（现钉 `{"list[dict]":45,"NoneType":17}` 与 keyset
`{"expected_output,stdin":45}` ⇒ **新题带不带 `tests` 都会动这两个数**）、
`:75 test_expected_output全覆盖_且judge与hints完备()`（新题缺 expected_output/hints 即红）。

### 4.4 sql 侧必改清单（`tests/test_content_census_sql.py`，**6 处**）
`:17 EXPECTED_TOPICS=12` / `:18 EXPECTED_PROBLEMS=54` / `:19 EXPECTED_DIFF` / **`:20 EXPECTED_ROWS_LEN={1:12,2:10,3:14,4:7,5:9,6:1,7:1}`**
→ `:36 test_题数54_且topic12()`、`:51 test_difficulty直方图精确()`、
`:64 test_expected_rows形态与行数直方图精确()` —— 这一条**一次钉四个量**：`shape=={"list":54}`、
行数直方图 `EXPECTED_ROWS_LEN`、`total_rows == 160`、以及 `01_select_all` 首行样例（列数口径）。
⇒ **sql 每补一道多行题，最多同批要改 4 个数字**（54 / 直方图 / ROWS_LEN / 160）。这是三门里牵连最密的。

### 4.5 r 侧必改清单（`tests/test_content_census_r.py`，**7 处，含一整套 D6 契约桩**）
`:36/:37/:38` 三常量；`:90 test_census_答案面字段与判定模式分布()` 一次钉三个字典：
`fields=={"expected_output":70,"rubric":14,"reference_answer":14}`、`judge=={"run":70,"ai_open":14}`、
hints 无缺失名单；`:107 test_契约_每道题显式judge_mode()`（新题 yaml **必须显式写 judge_mode**）、
`:116 test_契约_judge_mode取值合法()`（**取值域只有 run / ai_open**）、
`:124 test_契约_判定模式与答案字段匹配()`、`:140 test_机判字段_业务语义规则()`、
- `:162 test_机判字段_版本1快照_出现即提示升级而非永久封杀()`。
  ⇒ **r 的 14 道 `ai_open` 落点实测**（loader 复算）：`16_mediation` 5/5、`14_sem_basics` 4/4、`15_cfa` 4/4、`06_mixed_apa` 1 —— **三个统计建模 topic 已整体走开放题路线**。所以 r 上抬有两条互斥路径：落在 `11_survival`/`07_glm`（`run` 型，需 Rscript 才能取期望值）或落在 `16_mediation`/`14_sem_basics`/`15_cfa`（`ai_open` 型，只需 `rubric`+`reference_answer`，但**永远进不了机验面**）。本档 §五 批次二按「先 open 后 run」排，就是这个读数的直接后果。

### 4.6 SQL 行序裁决（卷宗点名 l923-23）
`tests/test_sql_roworder_fragile.py`：`:27 def _top_level_positions`、`:130 @pytest.mark.xfail(`、
`:140 def test_多行SQL题行序全部承重()`。现跑 **1 PASSED + 1 XFAIL**；xfail reason 原话：
> 「判分按 expected_rows 位置逐行比对，而无 top-level ORDER BY 的查询 sqlite 不保证行序；
> 实测有多道多行题『剥掉 ORDER BY 后仍逐行等于期望』⇒ 题面排序要求不承重、判分依赖引擎返回序。
> 清单与三条出口见 `docs/insights/learn-sql-roworder-census-20260922.md`；**命中集合清空即 XPASS＝本例转红**」

⇒ 对 sql 4/5 档补题的**硬约束**：新题若走 `expected_rows`，**题面必须写明确排序、且必须真带 top-level
ORDER BY**，否则要么进这张"不承重"名单（加重在册缺陷），要么被判分器位置比对坑。
配套：`docs/insights/learn-sql-roworder-design-20260923.md`（l923-23，**已入库 `1ff0ae1`**）
给的是三条出口的选择框架 ⇒ **本档不重述其结论，只登记"sql 上抬与它的裁决先后关系"**：
若 sql 4/5 档新题沿用现状比对，则本案与那次裁决解耦；若新题依赖行序，须先落出口二/三。

### 4.7 r 的 plain 降档前科（卷宗点名 l922）
`scripts/mark_r_judge_plain.py` docstring 原文（**这是 D6 的权威留痕，比卷宗的说法更硬**）：
> 「content/r 下 84 个题目的 yaml 无一含 expected_rows / tests 键（grep 0 命中），即 r 题库根本没有
> 『多 DataFrame 机判题』这种形态；r 实际判定面是 expected_output 70（stdout 比对＝普通题）＋
> rubric/journal 14（judge_mode: ai_open）。**用户拍板 D6：降级为普通题，不硬补测试用例。**」
> 「合法值枚举 run / ai_open——**出现第三种取值即异常（不是静默放过）**」

⇒ **r 侧「机判多结果」这条路是用户拍板关掉的**，不是技术做不到。r 4/5 档补题因此**只能在
`run`+`expected_output`（stdout 比对）与 `ai_open`+`rubric`+`reference_answer` 两条既有形态里选**；
若设计稿想要"多对象/多表机判"，那是**翻 D6 决定** ⇒ 必须走人工，不在补题单授权内（本档按前者设计）。

### 4.8 工具链（**本档新增的最强牵连面**）
`core/runners/cpp_runner.py:44 which = shutil.which("g++")`、`core/runners/r_runner.py:33 shutil.which("Rscript")`
⇒ 本机两者皆缺（§一.4 实测 7 SKIPPED）。**后果不是"测试少跑 7 例"，而是"cpp/r 高档题的期望输出无从产出"。**
另注 `test_cpp_runner.py:45` / `test_r_runner.py:26` 各有一例把 `shutil.which` 打成 `None` 来验降级路径
⇒ **CI 在无编译器机器上也能跑，但这不等于本机能出题**。

### 4.9 判分归一与浮点
`core/judge.py:56 def _normalize(s, lang="")`（按语言归一）、`:80 _cell_eq`、`:96 _rows_equal`、
`:103 _first_diff_cell`。r/python 高档题普遍输出 `0.123456789` 类浮点 ⇒ 期望必须写成**四舍五入到固定小数位**
的形式（与三门现有 3 档题的做法一致，实测 r 题输出行均带显式 `round(...)`）。
**这是「不可机验风险」的主要来源，本档把它判为**题面设计约束**而不是判分缺陷。**

### 4.10 difficulty 值的真实消费面（替代第一稿作废的「starter_code 难度标号」主张）
磁盘实测：`难度\s*[1-5]` 在 content/ 下 **0 命中**（全库仅 11 处，在 `tests/test_content_difficulty_pins.py`
×4、`docs/insights/learn-difficulty-histogram-20260921.md` ×4、`tests/test_home_next_action.py`、
`tests/test_content_thin_topic_p0.py`、`docs/insights/learn-thin-thick-topics-20260921.md` 各 1）。
⇒ **yaml 里唯一有效的难度载体是 `difficulty:` 字段（本仓全部题都在第 3 行）**，没有需要同步的题面标号。
消费方实测（`git grep -n difficulty -- core/ scripts/`）：
`core/loader.py:191-207`（读取，`raw_diff is None → 1`）、`core/judge.py:294`（`or 3` 兜底）→
`core/progress.py:378`（SRS ease）、`core/ai_review.py:187/189/278`（**讲评 prompt 按 `difficulty <= 2` 分档**）、
`core/ai_generate.py:38/103`（AI 变体题继承原题难度）。
⇒ 上抬 4/5 档**同时**改变：① SRS ease 惩罚可达面（≥4）；② AI 讲评的话术档位（≤2 与 >2 两条路径）；
③ AI 生成变体题携带的难度。**②③是第一稿没发现的牵连面**（②属 LLM 行为面，不入库即无读数）。

### 4.11 在册 xfail 与薄 topic 现状桩
- 全量基线的 2 条 xfail 现读为：`test_paths_order_consistency.py::test_路径内milestone顺序与语言页顺序一致`
  （reason：2 处 yaml 顺序 vs loader 字典序真倒置，python_advanced p4/p5）与
  `test_sql_roworder_fragile.py::test_多行SQL题行序全部承重`（§四.6）。
  **命中集合清空即 XPASS＝转红**（纪律档 §廿三），本档不动它们。
- `tests/test_content_thin_topic_p0.py:42 P0_DIRS = cpp/01_io_and_vars, cpp/02_branch_loop,
  python/20_numpy_basics, python/21_datetime_ts` + `:62 P0_SNAPSHOT`（`cpp/01 [1,2]`、`cpp/02 [1,2,2]`）
  ⇒ **若 cpp 上抬选点落在 `01`/`02` 两个薄目录，须同步 `P0_SNAPSHOT`**（本档 §三.2 的 4 个候选
  都是满编 topic，不踩；但"顺便补薄"的冲动要付这条改账）。该文件现跑 **5 passed（含
  `test_里程碑题时密度_下限绑磁盘`——绑磁盘、比例式 ⇒ 新增题不红）**。

### 4.12 insights 索引（纪律档 §廿三：主班单点写）
本档新增 1 份 insights ⇒ 闭合哨兵必红 2 例（A/B/C 三条对账里的 C 非空）。**本班不改索引表**，
交主班随代提交当场补行（口径见 result 的「改动清单」）。

---

## 五、落地次序与工作量估计（分 3 批，批次一含前置门）

| 批次 | 内容 | 工作量 | 前置门（不满足则**不开批**） |
|---|---|---|---|
| **〇（工具链，先于一切 cpp/r 出题）** | 本机装 `g++`（MinGW-w64，进 PATH）与 `Rscript`（R for Windows）；复跑 `pytest tests/test_cpp_runner.py tests/test_r_runner.py -q` 应 **7 passed / 0 skipped** | 0.5h（纯环境）+ 0.2h 复验 | 这是 §一.4 的实测缺口；不装就只能出 sql |
| **一（sql，立即可做）** | 4 档 +5、5 档 +1：主落点 `08_exists` / `06_window_functions`，备落点 `07_cte`（换场景）/ `04_joins` | 出题+跑真库取期望值 5 题 × ~12min ≈ **1h**；改快照/契约 **6 处**（§四.4）≈ 15min；`test_content_census_sql.py`+`difficulty_pins`+`census.py`+`sql_roworder` 复跑 ≈ 5min ⇒ **≈1.3h** | 行序裁决（§四.6）：新题必须带 top-level ORDER BY 且题面写明确排序 |
| **二（r）** | 4 档 +5、5 档 +1：主落点 `11_survival` / `06_mixed_apa`，备落点 `07_glm`；`16_mediation` 走 `ai_open` 形态扩 1 题 | 出题 ≈ **1.5h**；**D6 冲突面** ≈ 1h；改快照/契约 **7 处**（§四.5，形态字段计数最密）≈ 25min ⇒ **≈2.9h** | 批次〇 的 `Rscript`；**且 D6 未被翻案**（若要"多表机判"须先走人工） |
| **三（cpp）** | 4 档 +5、5 档 +1~2：主落点 `09_operator_overload` / `07_pointers_class`（先消地址类不确定输出），备落点 `08_inheritance`；`04_functions` 因 3/3 已带 `tests` 是形态最完备的落点 | 出题 ≈ **1.8h**；**删 `test_cpp_无4到5档` 桩 + 改 5 处**（§四.3）≈ 25min ⇒ **≈2.2h** | 批次〇 的 `g++`；`04_recursive_cte` 与 `05_functor` 类**同名主题必须换新场景** |
| 四（收口） | 全量复跑 + 台账/README 同步 | ≈ **0.3h** | 前三批中已完成者 |
| **合计** | 13~14 题、三语言形状对齐 | **≈6.9h（含工具链）**；仅 sql 则 **≈1.3h** | — |

**次序理由（按本档实测排，不按卷宗假设排）**：
① **sql 唯一现在就能开工**——sqlite 走 python 内置，期望值可当场跑真库得到，不触"不猜期望输出"红线；
cpp/r 排在批次〇 之后是**硬约束不是偏好**。
② cpp 虽空洞最严重（占比 0.0%），但它还多背一条**专门立的拦路桩**（§四.1 `:117`）与
"指针地址/输出不确定"这一 r/cpp 共有的机验障碍 ⇒ 不是先做它。
③ r 的牵连面**单价最高**（7 处，含 `fields`/`judge_mode` 双字典逐键对账 + 一整套 D6 契约桩），
放中段：既给 sql 让出首批，又避免 cpp/r 同时开工时把两套契约混在一个 commit。
④ **cpp 与 r 不可同批**：两者分别动 `census_cpp.py` 与 `census_r.py` 的**同一族常量**，
同批会让一次 commit 里混入两套判分形态变更，回滚粒度太粗。

---

## 六、本班否证与自我更正清单（完成标准④的证据面）

1. 🔴 **本班第一稿的整批读数作废**（**自查发现，非卷宗之过**）：第一稿称
   「starter_code 自带『难度 N』标号 2668 处、cpp 61/62、sql 54/54、python 357/399、
   scripts 14/15 件含 `repeat(`」，并称 `test_report.py:35` 钉 `len(docs_files)==27`、
   `mark_r_judge_plain.py:53 def detect(`、`rubric_dims.py:24 DIMENSIONS`、
   topic 名 `03_smart_ptr`/`03_km_plot`/`01_overload+`、r topic 名单含 `02_logic_and_summary`/`13_rmarkdown` 等。
   **以上每一项按磁盘实况均不成立**：`难度\s*[1-5]` content/ 0 命中（A9）；`test_report.py` 无该断言（A10）；
   `mark_r_judge_plain.py` 无 `detect()`；`core/rubric_dims.py:10` 实为 `DIMENSION_CANON`；
   `content/cpp/09_operator_overload/` 实际题号是 `01_money_add…05_functor`、`content/r/11_survival/` 是
   `01_surv_obj…05_cox_multivar`（**`03_smart_ptr.yaml` / `03_km_plot.yaml` 不存在**，`test -f` → No such file）；
   `content/r/` 实际 18 个 topic 目录见 A2。
   **作废处理方式**：本档正文改用可复算的 `grep -n` / loader 口径重取（13:58–14:05），
   上表每一项都给了复算命令；第一稿独有的主张一律不再出现。
   ⇒ 给主班的一条通用坑：**同一台机器上"看起来跑成功"的批量扫描，输出可能与磁盘不符；
   凡进入结论的数字要能被第二条独立命令复核（本档的 403/17/25 格对平就是互验过的）。**
2. **否证卷宗**：牵连面清单里的 `mark_r_judge_plain.py:53 def detect(` 不存在（实际 `scan` :311 /
   `prepare_one` :363 / `_judge_mode_lines` :255）。前提（r 有 plain 降档前科）仍成立，且**脚本
   docstring 就是权威证据**（§四.7 已逐字引）。
3. **否证卷宗**：「census 399 等值点（若 l923-03 已落地则 403）」——现读 **403 有两条等值断言**（`census.py:27`、`pins:84`），399 只剩 `test_scripts.py:310` 的 `>= 399` **下界护栏**与注释；
   （l923-03 已落地，403 等值点有**两处**：census 与 pins，卷宗只列了一处）。
4. **否证卷宗**：「cpp 4/5 档需本机 g++」这句被本班**坐实并升级为主约束**——不是"要注意"，而是
   **本机 g++/Rscript 双缺（7 SKIPPED），cpp/r 高档题当前无法产出可信 `expected_output`**（§二）。
5. **精确化 l922-06**：「末档可达面无声扩大」⇒ 实际有 `:98`/`:117` 两道桩拦住，成本是**改快照+删桩**，
   不是无声。据此 §五 才敢给"可控地扩"的次序。
6. 未坐实（本档不下结论，留给批次班）：各候选 topic 现有 3 档题的**实际内容重叠度**（本班按 topic 名与
   d3 题号推断，未逐题读题干）；`12_file_io` 是否真有 3 题（A5 未列，本班不据此排序）。
7. **盘在动的一次实录**：本班取数期间 learning 工作树被外部回退过一次（13:52→13:58 之间），
   表现为：`test_content_difficulty_pins.py` 的 `PINNED_HIST` 行号从 29 变 32、`tests/test_paths_coverage.py`
   mtime 跳到 13:52:31、`docs/insights/` 从 39 份变 66 份（HEAD 未动、porcelain 只剩本班 1 件）。
   ⇒ 本档所有行号是 **14:0x 对 HEAD `6c7cd28` 的读数**，动题前先跑 A1。
8. **learn10 班（14:31–14:36 接手复核）：判定本档为「完成态」，逐读数独立复算后修 4 处锚点**
   前班 `learn9` 14:1x 被服务拒绝时**未写 result、未移件、未记 claim**，learn10 按信箱纪律接手判定完成度：
   - **判完成态的依据**：卷宗四条完成标准 ①②③④ 全可复算（① 25 格直方对平 + 全库 403；② 12 条候选 topic 的
     n / d1–d5 向量 / d3 题名 / d3 带 tests 数**逐条**复算相符；③ 牵连面 文件:行号 除下述 4 处外全对；
     ④ `git status --porcelain` 只含本档 + 前单 l923-27 测试件）。⇒ 属「成品缺 result」而非「断在中途」，**不重做**。
   - **learn10 复核时按磁盘实测改掉的 4 处读数**（前档原值 → 现值，均 `grep -n` 口径、HEAD 仍是 `6c7cd28` 未动）：
     ① §〇 sql 行现值 `:35` → **:34**（`grep -n '"sql"'`；行号增量 +4 → +3）；
     ② 403 第二等值点 `pins:85` → **`pins:84`**（§〇、§四.2 命令块与正文、§六.3 共 4 处）；
     ③ §四.2 的 README 锚点 `README.md:3` → **`README.md:52`**，且原引文「面向「心理学 + 数据分析 + AI 全栈」…
       **5 语言 21 专题路径 · 403 题**」**磁盘上不存在**（README:3 实为「面向中文零基础用户的 **Python · SQL · C++ · R · Agent 开发**
       交互式学习系统，当前版本 v0.6.5…」），已换成 :52 原文 —— **这正是 §六.1 那条「批量扫描输出可能与磁盘不符」的坑在本班自己身上的复现**；
     ④ §四.2「399 在 tests/ 10 处」→ **11 处**（`git grep -n "399" -- tests/ | wc -l`）。
   - **learn10 复算且确认成立的关键读数**（不必重跑，留此备查）：`pytest tests/test_cpp_runner.py tests/test_r_runner.py -rs -q`
     = **7 skipped**（g++ ×4 @:16/:27/:34/:44、Rscript ×3 @:13/:19/:25），`shutil.which` 双 None；
     末档 17 题逐 id 分解 = cpp 0 / sql 1 / r 1 / python 7 / agent_dev 8；census_cpp :18/:19/:20 + 5 个 test 行号、
     census_sql :17–:20 + :36/:51/:64、census_r :36/:37/:38 + :90/:107/:116/:124/:140/:162 全对；
     sql `shape={"list":54}` / ROWS_LEN 七格 / `total_rows=160` 全对；cpp `NoneType:17`+`list:45`、keyset `expected_output,stdin:45` 全对；
     r `ai_open` 14 题落点 = `16_mediation` 5 + `14_sem_basics` 4 + `15_cfa` 4 + `06_mixed_apa` 1，fields/judge 双字典全对；
     §六.1 作废清单的 6 项「不存在」断言（content/ 难度标号 0 命中、`test_report.py` 无 insights 计数、
     `mark_r_judge_plain.py` 无 `detect()`、`rubric_dims.py:10 DIMENSION_CANON`、`03_smart_ptr`/`03_km_plot` 不存在）逐项复算成立。
   - **learn10 未采信的旧读数**：§六.7 记的 `docs/insights/` 份数现读 **67 份**（含本档；索引表仍 66 条 ⇒ 哨兵红 2 例，待主班代登）。
     本档 §六.7 那句「66 份」是前班当时观察窗的记录，**不作修正**（它是历史而非结论）。

---

## 七、待裁决清单（超出执行手授权）

1. **红线停手登记**：完成标准 ①②③④ 全部达成，但**本档不做一件事**——它不替三门写出任何
   `difficulty: 4/5` 题、不猜任何 `expected_output`，也不建议放宽 `test_cpp_无4到5档`(:117) 或两条在册
   xfail。理由：判分期望值 + 学习路径判分期望是本分区红线（卷宗亦点名"不猜期望输出"）。
   本档只给形状、落点、牵连面与批次。
2. **§三.1 目标阈值（每语言 4 档 ≥5、5 档各 1）是本档推荐，非既成口径**。落地会一次性扩大
   SRS ease 惩罚可达面（cpp 零→非零、sql/r 各 1→6）并改变 AI 讲评分档（§四.10）——
   属「学习数据正确性 / 判分行为」范畴，**须人工点头后另开补题单**。
3. **批次〇（装 g++/Rscript）不在任何卷宗授权内**（「禁止下载安装依赖」）⇒ 本班**只登记缺口、未安装**。
   没有这一步，cpp/r 两批只能停在纸面 ⇒ 请主班转交人工。
4. **r 侧形态约束**：D6「降级为普通题」是用户 2026-09-20 的拍板（§四.7 原文），且 `judge_mode` 取值域被
   `test_契约_judge_mode取值合法()` 锁在 `{run, ai_open}`。⇒ 若设计想要"多对象机判"，那是**翻拍板决定**，
   本档按"不翻"设计（`ai_open` 路线要求 `rubric` + `reference_answer`，现成样本仅 r 14 题）。
5. **cpp/r 题的浮点与不确定输出**（`0.123456789`、指针地址、`anova()` 行序、bootstrap CI）是否接受
   "题面强制要求 `round(...)`/确定性可打印量"这一约束，还是干脆把这类主题只出到 `ai_open`。
   本档采前者，**但这是内容口径**，交人工。
6. **是否扩 `agent_dev` 之外的第二道 5 档**（§三.1 的 5 档试水共 3 题）：补与不补都留下形状缺口，
   属产品选择。
7. 索引代登（§四.12）＋ 本档不新增测试/题面，故 §四 列出的 25 处"必改点"**全部未改**，
   属后续批次工单内容（见 result「遗留问题」）。

---

## 附录：复算命令（每条都能独立跑出本档引用的读数）

```
# A1 行号锚点（一次跑完 §〇 全部行号）
cd /d/code/learning-system
grep -n "PINNED_HIST = {\|PINNED_TOP_TIER = {\|^def test_" tests/test_content_difficulty_pins.py
grep -n "assert total == 403" tests/test_content_census.py
grep -n "if difficulty >= 4\|ease = max(1.5" core/progress.py
grep -n "def _rows_equal\|if not _rows_equal\|def _normalize\|def _cell_eq" core/judge.py
grep -n "def _top_level_positions\|def test_多行SQL题行序全部承重\|pytest.mark.xfail" tests/test_sql_roworder_fragile.py
grep -n "^def \|^EXPECTED" tests/test_content_census_cpp.py tests/test_content_census_sql.py tests/test_content_census_r.py
grep -n "P0_DIRS\|P0_SNAPSHOT" tests/test_content_thin_topic_p0.py
git grep -n "shutil.which" -- core/runners/

# A2 三门真实 topic 目录名单（§三.2 与 §六.1 用）
python -c "from pathlib import Path;[print(l, sorted(p.name for p in Path('content',l).iterdir() if p.is_dir())) for l in ('cpp','sql','r')]"

# A3 逐 topic 难度向量（§三.2 的 d1/d2/d3 列，12 条候选的实测源）
PYTHONIOENCODING=utf-8 python -c "import collections;from core.loader import load_language;[print(f'{l}:{t.slug} n={len(t.problems)}', {d:sum(1 for p in t.problems if p.difficulty==d) for d in range(1,6)}) for l in ('cpp','sql','r') for t in load_language(l,'content')]"

# A4 「按题数排序会假判空洞」的反例 + 3 档最厚 topic 的正确选择器（§三.2）
PYTHONIOENCODING=utf-8 python -c "import collections;from core.loader import load_language;[(print('['+l+']'),[print(f'  {len([p for p in t.problems if p.difficulty==3]):2} {t.slug} n={len(t.problems)}', [p.id.split(\"/\")[-1] for p in t.problems if p.difficulty==3]) for t in sorted(load_language(l,'content'), key=lambda t:-len([p for p in t.problems if p.difficulty==3]))[:4]]) for l in ('cpp','sql','r')]"

# A5 12 条候选的逐题判分面（§三.2 的 tests/rubric/reference_answer 列）
PYTHONIOENCODING=utf-8 python -c "
from core.loader import load_language
cand={'cpp':{'04_functions','07_pointers_class','08_inheritance','09_operator_overload'},'sql':{'06_window_functions','08_exists','04_joins','07_cte'},'r':{'11_survival','06_mixed_apa','07_glm','16_mediation'}}
[print(f'{p.id:52} d={p.difficulty} mode={p.judge_mode:8} tests={len(p.tests or [])} rubric={len(p.rubric or \"\")} ref={bool(p.reference_answer)}') for l,ss in cand.items() for t in load_language(l,'content') if t.slug in ss for p in t.problems if p.difficulty>=3]"

# A6 25 格直方对平 + 全库 403（§一.1 主命令）
# A7 末档 17 题分解（§一.2）
PYTHONIOENCODING=utf-8 python -c "from core.loader import load_language;print({l:[p.id for t in load_language(l,'content') for p in t.problems if p.difficulty>=4] for l in ('cpp','sql','r','python','agent_dev')})"

# A8 工具链缺失实证（§一.4 / §四.8）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_cpp_runner.py tests/test_r_runner.py -rs -q
python -c "import shutil;print('g++', shutil.which('g++'), '| Rscript', shutil.which('Rscript'))"

# A9 「难度 N 标号」真实分布（§四.10 / §六.1 作废依据）
python -c "
import re,collections
from pathlib import Path
pat=re.compile(r'难度\s*([1-5])')
tot=collections.Counter(); t=0
for f in Path('.').rglob('*'):
    if f.is_file() and f.suffix in {'.yaml','.py','.md'} and '__pycache__' not in f.parts:
        n=len(pat.findall(f.read_text(encoding='utf-8',errors='replace')))
        if n: tot[f.as_posix()]=n; t+=n
print('全库命中',t,'分布',dict(tot.most_common(6)))
print('content/ 命中', {k:v for k,v in tot.items() if k.startswith('content/')})"

# A10 test_report.py 里没有 insights 计数断言（§四.2 / §六.1）
grep -n "def test_\|docs_files\|insights" tests/test_report.py
# A10b 两份第一稿点名的文件其实不存在
ls content/cpp/09_operator_overload/ content/r/11_survival/

# A11 r D6 拍板原文（§四.7）
sed -n '1,20p' scripts/mark_r_judge_plain.py
grep -n "run\|ai_open" tests/test_content_census_r.py | sed -n '1,12p'

# A12 difficulty 消费面（§四.10）
git grep -n "difficulty" -- core/ scripts/

# A13 sql 行序 xfail 桩现跑（§四.6 / §四.11）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_sql_roworder_fragile.py tests/test_content_thin_topic_p0.py tests/test_paths_order_consistency.py -v

# A14 完成标准 ④：零题面改动、零测试改动（git diff 只含本档）
git status --porcelain | cat -n          # 期望恰 2 行：本档 + 本班 l923-27 测试件
```

> ⚠️ **附录 A4/A5 里的多行 python -c 请改成落 tmp 脚本再跑**（9/22 §十五.6）：
> 嵌套引号在 bash→python 二次转义下会炸。A3/A7/A9 的单行式已实测可直接跑。
> 另：**本仓跑测一律带 `PYTHONIOENCODING=utf-8`**（中文用例名在 cp936 控制台会炸码，纪律档 learning 口径）。
> 本机 **rg 可用**（ripgrep 15.0.0，纪律档 §十四）；本档计数一律走 python，理由见 §六.1。
