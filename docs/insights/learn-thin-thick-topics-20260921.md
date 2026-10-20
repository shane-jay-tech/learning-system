# learning 薄/厚 topic 比例失衡分析与增题优先级（l922-07，2026-09-21）

- 任务：`l922-07-learn-thin-topics`（cwd `D:\code\learning-system`，软预算 ≤30 分钟）
- 性质：**纯只读**。未新增题目、未改题面、未改 paths yaml、未改代码、未写库。
  唯一落盘产物是本档。判据口径：薄 = 该 topic 题数 **<=3**，厚 = **>=6**（任务书给定）。
- 复跑口径：`core.loader.load_language` 取题数 + `core.paths.load_all_paths` 取 milestone 引用，
  两路都在内存里读盘，零副作用。

## 一、锚点复核：任务书四条比率**逐字成立，零漂移**

| 语言 | topics | lessons | questions | 题/课 | 任务书标称 | 判定 |
|---|---|---|---|---|---|---|
| agent_dev | 15 | 15 | 78 | **5.20** | 5.2 | ✓ |
| cpp | 13 | 13 | 62 | **4.77** | 4.77 | ✓ |
| r | 18 | 18 | 84 | **4.67** | 4.67 | ✓ |
| sql | 12 | 12 | 54 | **4.50** | 4.5 | ✓ |
| python | 27 | 27 | 121 | **4.48** | 4.48 | ✓ |
| 合计 | 85 | 85 | 399 | 4.69 | — | — |

**结构事实（本单新增，任务书没写但影响口径解读）**：`topics == lessons == content/<lang>/ 目录数`
对五语言**全部成立**（每个 topic 目录恰好一份 `*_lesson.md`），且 `core.loader.Topic` 只有一个
`lesson_md` 字段。所以「题/课」在现仓里**恒等于「题/专题」**，两者不是两个独立维度——
任何按「加课不加题」思路做的平衡调整在当前数据结构下**无法表达**。

## 二、五语言薄/厚双清单（含进线状态列）

**进线定义**：该 topic 至少被一个 `content/paths/*.yaml` 的 milestone `topics:` 引用。
实测全仓 6 条 path / 41 个 milestone，**85 个 topic 全部进线（未进线 = 0）**；
反向亦成立（paths 引用了盘上不存在的 topic = 0）。⇒ 任务书设问「薄 topic 是否进线」的答案是
**12/12 全进线，无一例外**，因此不存在「薄但是自由练习、可以不管」的豁免路径。

### 薄清单（题数 <=3，共 12 个 topic）

| # | 语言 | topic | 题数 | 进线（path:milestone，多引用全列） | 该 milestone 总题数 / 标称小时 |
|---|---|---|---|---|---|
| 1 | python | `01_hello_and_vars` | 2 | `agent_mastery:a0` + `people_analytics:m1` | a0=20/4h；m1=15/6h |
| 2 | python | `02_conditionals` | 3 | `agent_mastery:a0` + `people_analytics:m1` | 同上 |
| 3 | python | `20_numpy_basics` | 3 | `python_advanced:p3` | **p3=6/3h** |
| 4 | python | `21_datetime_ts` | 3 | `python_advanced:p3` | **p3=6/3h** |
| 5 | python | `22_statsmodels` | 3 | `python_advanced:p4` | p4=17/6h |
| 6 | python | `23_sklearn_advanced` | 3 | `python_advanced:p4` | p4=17/6h |
| 7 | sql | `01_select_where` | 2 | `people_analytics:m5` | m5=20/6h |
| 8 | sql | `02_aggregate` | 3 | `people_analytics:m5` | m5=20/6h |
| 9 | cpp | `01_io_and_vars` | 2 | `cpp_foundation:c1` | **c1=5/3h** |
| 10 | cpp | `02_branch_loop` | 3 | `cpp_foundation:c1` | **c1=5/3h** |
| 11 | r | `01_vectors_and_basics` | 2 | `people_analytics:m7` + `quick_stats:s1` | m7=15/5h；**s1=5/2h** |
| 12 | r | `02_logic_and_summary` | 3 | `people_analytics:m7` + `quick_stats:s1` | m7=15/5h；**s1=5/2h** |

### 厚清单（题数 >=6，共 8 个 topic）

| 语言 | topic | 题数 | 进线 |
|---|---|---|---|
| agent_dev | `05_modular_config` | 8 | `agent_mastery:a5` |
| agent_dev | `11_real_tasks` | 8 | `agent_mastery:a7` |
| agent_dev | `03_spec_writing` | 6 | `agent_mastery:a3` |
| cpp | `03_arrays_strings` | 6 | `cpp_foundation:c2` |
| cpp | `06_iter_algo` | 6 | `cpp_foundation:c3` |
| python | `13_scipy_stats` | 6 | `python_advanced:p4` |
| r | `06_mixed_apa` | 6 | `people_analytics:m8` + `quick_stats:s3` + `quick_stats:s4`（三引用，与 `r/05_lm_anova` 并列全仓最高） |
| r | `10_stringr_lubridate` | 6 | `r_advanced:r3` |

## 三、失衡的真实形状：不是「两极分化」，是「众数 5 之外的长尾」

全 85 topic 的题数直方（实算）：

| 题数 | 2 | 3 | 4 | **5** | 6 | 8 |
|---|---|---|---|---|---|---|
| topic 数 | 4 | 8 | 10 | **55** | 6 | 2 |

- **64.7%（55/85）的 topic 题数恰好为 5** —— 这才是仓内的事实口径。
  但**没有任何文档声明过 5**：`README.md` 只在功能描述里出现「每题」，`plan.md` 里
  `grep 专题|题库|topic` **零命中**，paths yaml 只有 `estimated_hours` 没有题数目标。
  ⇒ 补题目标位应钉在 **5**（回到众数），而不是「补到 6 消除薄」。
- 厚档只有 8 个且封顶 8，薄档 12 个下探到 2 ⇒ 分布是**左偏长尾**，
  失衡主要发生在「入门 topic 被少写了 2-3 题」，不是「难题堆太多」。
- 语言维度：`python` 薄 6 个最多（但 27 个 topic 基数也最大），
  **cpp/sql/r 的薄全部落在各自的 01/02 号入门专题**，agent_dev **零薄档**（它是唯一 5.2 题/课的语言，也是 l922-06 里唯一有 5 档的语言）。
  五语言的题/课差（5.20 → 4.48）**几乎完全由入门 topic 是否写满 5 题解释**，不是中后段差异。

## 四、增题优先级建议表（**本单不写题**，只排序与给落点）

排序指标：所在 milestone 的 **题/小时**（补题后学习者实际拿到的密度）＞ 是否入门位 ＞ 是否多路径复用（补一次多线受益）。

| 优先级 | 目标 topic（各补到 5 题） | 净增题数 | 现状痛点（实测） | 补后 |
|---|---|---|---|---|
| **P0** | `cpp/01_io_and_vars`(2→5)、`cpp/02_branch_loop`(3→5) | +5 | `cpp_foundation:c1` 整条里程碑只有这 2 个 topic，**5 题 / 3 小时 = 1.67 题/时，全仓最稀**；且是 C++ 线的门面 | c1=10 题/3h ≈ 3.3 |
| **P0** | `python/20_numpy_basics`(3→5)、`python/21_datetime_ts`(3→5) | +4 | `python_advanced:p3` 只有这 2 个 topic，**6 题 / 3 小时 = 2.0 题/时**；两者都是 l922-05 记录的**双号受害者**（同号的 HR 侧 `20_hr_pandas`/`21_hr_viz` 各 5 题，p3 侧被挤压） | p3=10 题/3h ≈ 3.3 |
| **P1** | `r/01_vectors_and_basics`(2→5)、`r/02_logic_and_summary`(3→5) | +5 | `quick_stats:s1` = **5 题 / 2 小时**，且 s1 只有这 2 个 topic；两题同时被 `people_analytics:m7` 复用 ⇒ 补一次**双路径受益**，是投产比最高的一笔 | s1=12 题/2h |
| **P1** | `python/22_statsmodels`(3→5)、`python/23_sklearn_advanced`(3→5) | +4 | p4 内部**厚薄并存**：`13_scipy_stats` 6 题 vs 这两个 3 题，同一里程碑题差 2 倍；且 `22_statsmodels/03_significance`、`23_sklearn_advanced/02,03` 是 l922-06 认定的 python 4 档题集中地（python 7 道 4 档题里占 3 道，另 4 道在 `20/21/22_hr_model/24`）——薄+难叠加，学员在最高门槛上题量最少 | p4 结构齐平 |
| **P2** | `sql/01_select_where`(2→5)、`sql/02_aggregate`(3→5) | +5 | m5 有 5 个 topic 共 20 题，**里程碑层面不稀（3.33 题/时）**，稀释后可延后；但 `sql/01_select_where` 是 2 题，是 SQL 语言的第一屏，建议至少补到 4 消除极端值 | 直方左尾 -2 |
| **P2** | `python/01_hello_and_vars`(2→5)、`python/02_conditionals`(3→5) | +5 | 同 m5 情形：a0（20 题）/m1（15 题）都被兄弟 topic 稀释，**里程碑密度不是问题**；但这两个是**全系统的第一屏**（`agent_mastery:a0` 起点），2 题属观感问题，排在题量问题之后 | 直方左尾清零 |
| 不建议 | 厚档 8 个 topic | 0 | 6 与 8 都各有其成（`agent_dev/11_real_tasks` 是综合实战、`r/06_mixed_apa` 三路径复用）——**本单的「厚」是合理厚，不该削**。削题会同时打断 `test_content_census.py` 的 399 口径与 l922-06 新钉的 `PINNED_HIST` | — |

P0+P1 合计净增 **18 题**（399→417）即可消掉「里程碑层面题/时 < 2.5」的全部三处（c1、p3、s1）；
P2 的 10 题属直方美观度，可随下一轮内容班做。

## 五、跨单关联与提醒（不动手，只点名）

1. **双号挤压**是本单薄档的成因之一（p3/p4 四个薄 topic 全是 l922-05 记录的双号目录）。
   若先按 l922-05 的建议重排号数再补题，本表第 3/4/5/6 行的目录名会变，**建议在先补题后改号**。
2. **薄 + 末档难 叠加**：`python/22_statsmodels`、`23_sklearn_advanced`、`agent_dev/11_real_tasks`
   在 l922-06 的 4/5 档名单里，题数却只有 3-8。补题时若只补 1-3 档的易题，会稀释末档名单（`PINNED_TOP_TIER` 不受影响，
   但 `PINNED_HIST` 会变红——那是设计，见 l922-06 桩 docstring）。
3. 本单**未新增测试桩**（任务书完成标准只要求 insight 含双清单＋进线列）。
   若规划班要把「薄 topic 数 <=12 / 题/时 >=1.67」钉成门禁，应单开一单；
   现成落点建议：与 `tests/test_content_census.py` 同族的 topic 级普查（该文件目前只在**题**级断言，无 topic 级）。

## 六、落地进度续登记（2026-09-23 l923-03；本节是增量，上面 §四 表保持 09-21 快照原样）

`tests/test_content_thin_topic_p0.py` 的失败信息要求「补题时把本表落点一起刷新」，本即该指令的落点。
**本表不逐格回改**（历史快照原则，同 §五 第 3 条与 colony 侧口径），进度改记在本节：

| §四 行 | 09-21 现状 | 09-23 进度 | 全库口径 |
|---|---|---|---|
| P0 第 2 行 `python/20_numpy_basics`、`python/21_datetime_ts` | 3 题 / 3 题 | **已补至 5 题**（各 +2，难度 2、3 档） | 399 → **403** |
| P0 第 1 行 `cpp/01_io_and_vars`、`cpp/02_branch_loop` | 2 题 / 3 题 | **未落地**：本机无 g++，`expected_output` 无法机验，留日间班 | 停在 403，不预支 408 |
| （同上，2026-09-30 加注）`cpp/01_io_and_vars`、`cpp/02_branch_loop` | 各 5 题 | **已落地（l927-27，答案域经 2026-09-28 用户授权自拟）**：难度 2/3 档、出处行在各 yaml 首行注释；本机仍无 g++，参考解按算术事实自证未编译对拍 | 403 → **408**（等值点 4 处＋精确桩 2 件同批已刷） |
| P1/P2 四行（r×2、python×4、sql×2） | 2-3 题 | 未动（本夜只按「python 侧可机验」范围收口） | — |

- 规范授权位已在 `plan.md`「题库内容规范」钉下（**每 topic 目标题数＝5**，对齐全仓众数；下限哨兵另计），
  本表 §四 第 73 行的「目标位应钉在 5（回到众数）」由文字建议升格为在册规范——**下一班补题不必再因「未钉授权」落 partial**。
- 补的 4 题参考解全部经本仓真实链路对拍（`core.runners.python_runner.PythonRunner` 跑参考解 →
  `core.judge._normalize` 归一化 → 与 `expected_output` 逐字节相等），并在系统 python（numpy 2.3.5）
  与 `.venv`（numpy 2.5.1）两个解释器下各跑一遍全等 ⇒ `expected_output` 不随 numpy 版本漂。
- 补题后全仓 topic 题数直方：`{2:4, 3:6, 4:10, 5:57, 6:6, 8:2}`（85 topic / 403 题，众数仍 5），
  薄于 5 的目录由 22 个降到 **20 个**。§四 的「P0+P1 净增 18 题」总数不变，剩 14 题待后续批次。

