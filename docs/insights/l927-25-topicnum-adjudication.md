# 专题号数语义三案裁决材料（l927-25，2026-09-29｜只读，零写数据）

- 任务：l927-25（cwd `D:\code\learning-system`，软预算 ≤25 分钟）
- 性质：**只出材料、不下判定**。本单零改目录名、零改题面、零改判分、零改库、零 git 写。
  `data/progress.db` 全程 `sqlite3.connect('file:...?mode=ro', uri=True)` ＋ 读前读后 sha256 一致
  （`cd2dbce45109c9ed…`，122880 字节，两次读数相同）。
- 上游：`docs/insights/learn-topic-dualnum-20260921.md`（l922-05）§三 的 A/B/C 方案稿 ＋
  其「遗留问题 #1」留下的待拍板口径「号数到底承诺第几课，还是仅作分组标签」。
- 复跑本档全部读数：见 §〇 与 §三 内联命令（一律带 `PYTHONIOENCODING=utf-8`）。

## 〇、31 条错位现值复核：**仍在，一条没少**（否证「可能已被前几枚单改掉」）

取数口径与 l922-05 完全同型：**展示序 = `core/loader.load_language(lang)` 返回序**（生产通道），
号数 = 目录名前导数字段（`re.match(r'^(\d+)([a-z]*)', slug)`），错位 = `位置+1 != 号数`。

```
$ PYTHONIOENCODING=utf-8 python -c "... load_language 遍历，逐位比 int(号数) 与 i+1 ..."
python dirs 27 mismatch 7
r dirs 18 mismatch 16
agent_dev dirs 15 mismatch 8
sql dirs 12 mismatch 0
cpp dirs 13 mismatch 0
TOTAL mismatch = 31
```

| 语言 | 目录数 | 题数 | 错位条数 | 首条错位 | 末条错位 | 最大漂移（位置−号数） |
|---|---:|---:|---:|---|---|---:|
| python | 27 | 125 | **7** | 第 21 位 `20_numpy_basics` | 第 27 位 `24_real_world_data` | **+3** |
| r | 18 | 84 | **16** | 第 3 位 `02b_dataframe` | 第 18 位 `16_mediation` | +2 |
| agent_dev | 15 | 78 | **8** | 第 8 位 `07_write_spec` | 第 15 位 `13_multi_round` | +2 |
| sql | 12 | 54 | 0 | — | — | — |
| cpp | 13 | 62 | 0 | — | — | — |
| 合计 | **85** | **403** | **31** | | | |

三条配套前提也逐条复测过（**未漂**）：

1. **双号仍是 6 组 12 目录**——现状桩定向跑绿即等于磁盘实况与 `DUAL_GROUPS` 逐字相等：
   ```
   $ PYTHONIOENCODING=utf-8 python -m pytest tests/test_topic_dualnum_pins.py tests/test_content_ids_unique.py tests/test_paths_reconcile.py -q
   10 passed in 0.48s        rc=0
   ```
   ⚠ 与 l922-05 归档读数不同的只有一处：当时同三件是 **9 passed**，现为 10 passed（`test_content_ids_unique.py`
   自 09-21 后多了一例）。**passed 数不是本单判据**，桩的等价断言才是。
2. **排序通道未换**：`core/loader.py:139` 仍是 `sorted(glob.glob(os.path.join(lang_dir, "*/")))`。
3. **全仓仍零代码解析号数**：
   ```
   $ rg -n "lstrip\(['\"]0['\"]\)|int\(slug|split\('_'\)\[0\]" 全仓（排除 tests）
   仅命中 docs/insights/learn-topic-dualnum-20260921.md:39（文档自述，不是代码）
   ```

**一处必须点名的锚点漂移**：l922-05 引 UI 标签在 `ui/pages/language.py:370`，现值为
**`ui/pages/language.py:471`**（`f"第 {idx + 1} / {total} 个知识点 · …"`）。属行号漂移、通道与文案语义未变，
但下一班照抄 370 会查无此句。

## 一、C 案改名对象 == 31，且错位条数与改名目录数**逐条同构**

`位置+1 != 号数` 的目录，恰好就是需要改名成「自己位置号」的目录——两个计数**同一批对象**，
所以「31」既是症状计数也是改名计数（旧档没说清这点，容易被读成「31 条错位 ⇒ 只改 12 个双号目录」）。

| 语言 | 旧目录名 | 新目录名 |
|---|---|---|
| python | `20_numpy_basics` / `21_datetime_ts` / `21_hr_viz` / `22_hr_model` / `22_statsmodels` / `23_sklearn_advanced` / `24_real_world_data` | `21_numpy_basics` / `22_datetime_ts` / `23_hr_viz` / `24_hr_model` / `25_statsmodels` / `26_sklearn_advanced` / `27_real_world_data` |
| r | `02b_dataframe` / `03_dplyr` / `04_ggplot` / `05_lm_anova` / `06_mixed_apa` / `07_glm` / `08_tidyr` / `09_purrr_map` / `10_stringr_lubridate` / `11_survival` / `12_clustering` / `13_rmarkdown` / `14_real_world_data` / `14_sem_basics` / `15_cfa` / `16_mediation` | `03_dataframe` / `04_dplyr` / `05_ggplot` / `06_lm_anova` / `07_mixed_apa` / `08_glm` / `09_tidyr` / `10_purrr_map` / `11_stringr_lubridate` / `12_survival` / `13_clustering` / `14_rmarkdown` / `15_real_world_data` / `16_sem_basics` / `17_cfa` / `18_mediation` |
| agent_dev | `07_write_spec` / `08_read_code` / `08_review_pr` / `09_decompose` / `10_debug_logs` / `11_real_tasks` / `12_spec_iteration` / `13_multi_round` | `08_write_spec` / `09_read_code` / `10_review_pr` / `11_decompose` / `12_debug_logs` / `13_real_tasks` / `14_spec_iteration` / `15_multi_round` |

**一处与直觉相反的实测结论（对「必须先降序／两阶段改名」这个常见假设的否证）**：改名顺序**自由**，
不需要临时名中转。因为目录名是 `NN_<后缀>` 且**后缀在同语言内唯一**（实测 `后缀唯一性 True` × 5 语言），
所以 31 个目标名既不撞保留目录、也不撞另一条待改名的源：

```
$ PYTHONIOENCODING=utf-8 python - <<'PY'   （逐语言算 targets∩保留名 / targets∩待改名单据集）
python targets唯一: True | targets∩保留名: set() | targets∩待改名(需换序): set() | 后缀唯一性: True
sql  同上全清；cpp 同上全清；r 同上全清；agent_dev 同上全清
```

⚠ 该性质**只对「同语言内后缀唯一」成立**，属可失效前提：将来同语言内出现两个同后缀专题
（如再插一个 `16_mediation`）就会当场撞名，迁移脚本执行前**必须重跑这段自检**而不是引用本档结论。
跨语言同名现值仍只有 `04_functions`（python×cpp，已由 `tests/test_content_ids_unique.py` 钉成已知例外；
题目 id 天然带 `<lang>/` 前缀 ⇒ 不构成迁移障碍）。

## 二、三案矩阵

| 维度 | A 维持双轨（号数降级为「路径内分组标签」） | B 手动映射（加一层显式号数/顺序映射） | C 顺移重排＋数据迁移 |
|---|---|---|---|
| 语义收益 | 无（歧义长期存在：「20 号那课」两解） | 有（展示号数可等于位置，目录名不动） | **有且最干净**：号数==第几课，31 条一次归零 |
| 目录改名 | **0** | **0** | **31** |
| 题目 yaml | 0 | 0（`topic:` 字段不动） | **148** 份需同步改 `topic:`（实测全库 403 份都带该字段，31 目录内 148 份当前与目录名一致） |
| `content/paths/*.yaml` 引用 | 0 | 0 | **36 处**（5 个文件：`agent_mastery` 8 / `people_analytics` 9 / `python_advanced` 5 / `quick_stats` 5 / `r_advanced` 9） |
| 生产码改动 | **1 处 UI 文案**（`ui/pages/language.py:471` 加「按当前顺序」限定语） | 新增映射数据＋改 `core/loader.py` 排序通道＋改 UI 取号（**动的是判分无关但属排序契约的生产码**） | `core/recommend.py:212` 2 处硬编码（`agent_dev/09_decompose`、`agent_dev/10_debug_logs`）＋ `scripts/audit_content.py:17` `ACCEPTED_TOPICS` 2 处（`r/11_survival`、`r/14_sem_basics`） |
| DB 迁移行数 | **0** | 0 | 本机 **54 行 / 3 张表**（见 §三），用户端未知 |
| 测试件同改 | 0（若改 UI 文案需复核钉该文案的用例） | 需**新增**一致性哨兵（映射覆盖 85 专题＋号数唯一） | **13 个测试文件**带这 31 个 slug 的字面量（见 §四） |
| 是否消解「两条顺序通道并存」 | 否 | 名义上可，但实际**再造第三套判据**（见下） | **否**，现值仍 2 处跨层倒置（见 §五） |
| 可回滚 | 无成本 | 删映射层即可 | 目录名可逆（`git mv` 反向），DB 靠迁移前快照；导出包不可逆 |
| 主要风险 | 语义债继续挂着；用户口头「第 N 课」与号数继续两解 | 🔴 与 `tests/test_paths_order_consistency.py` 头部写死的告诫同型：「刻意不在测试里重跑一遍 sorted(glob)——那会造出与生产通道并存的第二份顺序判据（l922-05 取证自纠的同款教训：两套判据会各自漂移）」。B 案＝把这条告诫反着做 | 一次性改动面最大；跨机迁移面（导出包）本机看不见 |

## 三、迁移面现值：**旧档「本机 8 行」在 C 案口径下不成立，现值 54 行 / 3 张表**

```
$ PYTHONIOENCODING=utf-8 python - <<'PY'  （sqlite3 mode=ro，逐表按 31 个 slug 过滤）
attempts.problem_id:              rows_hit=9
problems_status.problem_id:       rows_hit=9
review_state.problem_id:          rows_hit=0
rubric_scores.problem_id:         rows_hit=0
learning_events.problem_id:       rows_hit=36
learning_events.topic_id:         rows_hit=0    （全库 topic_id 非空仅 1 个值 '01_hello_and_vars'，且是裸 slug 不带 lang）
```

按 id 归并的实测明细（三张命中表都是同一批专题）：

| 受影响专题目录 | attempts | problems_status | learning_events |
|---|---:|---:|---:|
| `python/24_real_world_data`（→27） | 4 | 4 | 16 |
| `r/14_real_world_data`（→15） | 4 | 4 | 16 |
| `r/03_dplyr`（→04） | 1 | 1 | 4 |
| 合计 | 9 | 9 | 36 |

**与 l922-05 归档的差 = 46 行，归因三条（都是口径而非数据变化）**：

1. l922-05 §三 只统计了 **12 个双号专题**（当时结论「只有 `r/14_real_world_data` 带历史 ⇒ 方案 A 可零迁移」），
   而 C 案要改的是 **31 个目录**，多覆盖 `python/24_real_world_data` 与 `r/03_dplyr` 两个**带历史但不是双号**的专题；
2. l922-05 未统计 `learning_events`（现值 36 行，是三张表里最大的一块）；
3. 库本身在长：`learning_events` 从 09-21 的 51 行 → 现值 **81 行**；`attempts` 15 / `problems_status` 14 两值未变。

⇒ **下一班别再把「8 行」当迁移面引用**；该数只对「A 案规避 12 双号」那个旧问题成立。

另外三条旧档没写、但直接影响 C 案可执行性的口子（全部实测）：

- **导出包**：`core/data_portability.py` `FORMAT_VERSION = 1`，`export_all` 按字面存 `problem_id`，
  `_validate` 只校验 `format` / `version` / 表是否齐，**不校验 id 是否存在于 content**。
  ⇒ 迁移前导出的 JSON 在迁移后导入即写入孤儿行且**不会报错**（本机看不见、跨机才现形）。
- **本机备份树**：`data/backups/content-20260920-*/content/<lang>/<旧 slug>/…`（`.gitignore` 第 9 行 `data/backups/`
  已忽略，不入版本库）整树仍是旧目录名，且题目 yaml 里带旧 `topic:` 字段 ⇒ 用迁移前快照恢复＝静默回退。
- **yaml `topic:` 字段是 `Problem.topic` 的实际来源**（`core/loader.py:206` `topic=str(data.get("topic") or slug)`），
  改目录名不改 yaml ⇒ `Problem.topic` 仍指旧 slug；检查器已存在：`scripts/audit_content_deep.py:138-139`
  报「yaml 内 topic 与目录不一致」。它**不是 pytest**，全量套件不会替本单把关。

## 四、C 案迁移脚本设计（**设计，本单未写脚本、未落盘、未执行**）

**步序（每步都带前后断言，任一步不符即中止并保持原状）**

0. **自检前置**（防 §一 的「改名顺序自由」前提失效）：重跑 targets 唯一性／无碰撞检查；
   不通过则脚本必须改用两阶段（先全部 `os.rename` 到 `__mig_<slug>`，再全部落到目标名）。
1. **快照**：整库 `sqlite3 .backup`（WAL 库**不能用 `cp`**，现值 `journal_mode=wal`，
   旁边已存在 `progress.db-shm`/`-wal`）＋ 记 sha256 与逐表行数
   （现值 attempts 15 / problems_status 14 / review_state 0 / rubric_scores 0 / learning_events 81）。
2. **映射表单一来源**：31 条 `(lang, 旧 slug, 新 slug)` 由「位置+1」现算，
   **不硬编码**（照 `tests/test_insights_index_closure.py` 的「断言里零条目数字面量」同风格），
   并把表同时喂给文件侧与 DB 侧，禁止两处各写一份。
3. **目录改名**：`git mv` 保历史；逐条校验目标不存在再动。
4. **题目 yaml 同步**：148 份的 `topic:` 行改值。**只改这一行，不碰 statement / tests / starter_code /
   expected_output 等任何题面与判分字段**（红线：判分口径与答案内容域不由本单裁决）。
   题目 id 由目录名推导（`core/loader.py:184` `pid = f"{lang}/{slug}/{problem_slug}"`），
   **yaml 里没有 id 字段** ⇒ 不存在「改 id」这件事，只改 `topic:`。
5. **引用侧同步**：`content/paths/*.yaml` 36 处 + `core/recommend.py:212` 2 处 +
   `scripts/audit_content.py:17` 2 处 + §四表 13 个测试件的字面量。
6. **DB 迁移**：**逐条精确 UPDATE**，禁止 `LIKE '%旧slug%'` 模糊替换
   （`r/03_dplyr` 会同时命中 `r/03_dplyr` 与任何以它为前缀的 id）。事务内完成，
   前断言「命中 54 行」＝§三 现值，后断言「旧串残留 0 / 新串命中 54」。
   覆盖列：`attempts.problem_id`、`problems_status.problem_id`、`learning_events.problem_id`、
   `learning_events.topic_id`（现值 0 命中但**形状不同**：存裸 slug 不带 `lang/`，须单独一条规则）。
7. **版本闸**：`data_portability.FORMAT_VERSION` 1→2，`import_all` 对 `version==1` 的包
   **按同一映射表做 id 重写后再入库**（否则 §三 第一条口子落地＝静默产孤儿数据）。
   这一步属生产码改动，需与迁移同笔。
8. **校验闸门**（全绿才算完成）：
   ```
   PYTHONIOENCODING=utf-8 python -m pytest tests/test_topic_dualnum_pins.py tests/test_content_ids_unique.py \
     tests/test_paths_reconcile.py tests/test_content_census.py tests/test_content_census_python.py \
     tests/test_content_census_r.py tests/test_content_census_agent_dev.py tests/test_content_difficulty_pins.py \
     tests/test_content_thin_topic_p0.py tests/test_cross_recommend.py tests/test_hr_dataset_determinism.py \
     tests/test_mistakes_redo_lifecycle.py tests/test_scripts.py -q
   PYTHONIOENCODING=utf-8 python scripts/audit_content_deep.py     # topic vs 目录名一致
   ```
   外加三条「归零断言」：错位条数 == 0；双号组数 == 0（`DUAL_GROUPS` 需显式改成空 dict）；
   paths 引用悬空 == 0。
9. **回滚**：文件侧走 git；DB 侧走步 1 快照；**回滚也须同时回退 `FORMAT_VERSION`**，
   否则 v2 包会被 v1 代码拒收（`_validate` 的「版本过新」分支）。

**必须同笔入库的清单（分开提＝HEAD 红，供主班代提交判定）**：
31 个目录改名 ＋ 148 份题目 yaml 的 `topic:` 行 ＋ 5 个 paths yaml ＋ `core/recommend.py` ＋
`scripts/audit_content.py` ＋ 13 个测试件（下表） ＋ DB 迁移脚本与其读数断言 ＋ `data_portability` 版本闸。
其中**测试件与目录改名强耦合**（测试里是字面 slug），任何拆分都会让 HEAD 变红。

带这 31 个 slug 字面量的 13 个测试件（现值，命中次数／slug 个数）：

| 测试件 | 命中 | 性质 |
|---|---|---|
| `tests/test_content_census_r.py` | 16 / 16 | 🔴 清单型硬钉（每个 r 专题名列举） |
| `tests/test_content_census_python.py` | 9 / 7 | 🔴 清单型 |
| `tests/test_content_census_agent_dev.py` | 8 / 8 | 🔴 清单型 |
| `tests/test_content_census.py` | 2 / 2 | 🔴 清单型 |
| `tests/test_topic_dualnum_pins.py` | 15 / 11 | 🔴 `DUAL_GROUPS` 必须显式改空（C 案后 6 组归零） |
| `tests/test_content_difficulty_pins.py` | 17 / 11 | 🔴 难度钉桩按 slug 索引 |
| `tests/test_content_thin_topic_p0.py` | 6 / 2 | 🔴 薄专题清单按 slug |
| `tests/test_paths_reconcile.py` | 4 / 2 | 悬空引用钉桩（改错即红） |
| `tests/test_cross_recommend.py` | 3 / 1 | 跨路径推荐夹具 |
| `tests/test_hr_dataset_determinism.py` | 2 / 2 | — |
| `tests/test_mistakes_redo_lifecycle.py` | 2 / 1 | — |
| `tests/test_content_ids_unique.py` | 1 / 1 | 仅在 `KNOWN_CROSS_SLUG_CONFLICTS` 注释里 |
| `tests/test_scripts.py` | 1 / 1 | — |

## 五、C 案**不解决**的那一条（免得拍板时被当成附带收益）

l922-05 遗留 #2 的「两条独立顺序通道」（语言页字典序 vs `ui/pages/path.py:143` 的 yaml 列表序）
在 C 案后**原样保留**——C 案只把号数对齐到位置，相对序一动不动。现值复算（直接复用在册桩的取数函数，未改桩）：

```
$ PYTHONIOENCODING=utf-8 python -c "import sys; sys.path.insert(0,'tests'); from test_paths_order_consistency import _collect_divergences; print(len(_collect_divergences()))"
divergences 现值 = 2
   python_advanced/p4 [python] yaml=['13_scipy_stats','22_statsmodels','14_sklearn_intro','23_sklearn_advanced'] loader_pos=[12,24,13,25]
   python_advanced/p5 [python] yaml=['24_real_world_data','15_ab_text']                                        loader_pos=[26,14]
```

`tests/test_paths_order_consistency.py` 是 **strict-XFAIL 在册桩**（本单未撤、未改、未放宽），
它的 xfail reason 里已经写明消解手段是「重排 yaml 或给专题加显式 `order:` 字段」——
**那属规划域**，与本单的号数语义是两个问题。

## 六、推荐（供拍板，本单不代拍）

**默认推荐 A**（号数降级为「路径内分组标签」＋ UI 标注「按当前顺序」），**C 只在日间明确答
「号数 == 第几课」并且接受 §三 的迁移面时才走**。三条实测支撑：

1. **C 买到的是语义，不是正确性**。l922-05 已判「双号不改变展示顺序」，本单复测三条前提全部未漂
   （通道未换、零代码解析号数、号数位数齐平）⇒ 现状没有排序正确性缺陷，C 的 31 目录改名＋54 行迁移
   买到的只是「号数与位置对齐」这一件事。
2. **C 的真实成本比旧档口径大一圈且含不可见跨机面**：148 份题 yaml ＋ 36 处 paths ＋ 13 个测试件 ＋
   2 处生产码硬编码 ＋ 本机 54 行（旧档写的是 8 行）＋ **导出包/备份两条只在别的机器或恢复时才现形的口子**；
   而 A 案的全部改动是 1 行 UI 文案。
3. **B 案与在册判据正面冲突**：`tests/test_paths_order_consistency.py` 的注释把「另造一份顺序判据」
   明确当成事故教训写死。B 的映射层就是第三份判据，且它承诺的收益（号数==位置）A 用一句文案就能
   让用户「不再被误读」，C 用改名能真正达成——B 卡在中间两头不到岸。

⇒ 若日间的答案是「号数只是标签」→ **A（零迁移，1 行文案）**；
若是「号数＝第几课，且这是给用户的承诺」→ **C（按 §四 全量执行，不许拆笔、不许跳 §步 7 的版本闸）**；
B 案建议**直接出局**。

## 七、待人工拍板（一句话）

「`ui/pages/language.py:471` 显示『第 N 个知识点』而目录号数与它不等——这个号数到底是不是对用户的
『第几课』承诺？」这一句定案即选案；本单不替用户定，也不改判分口径、不补题面、不写标准答案。

## 八、声明

零题面改动、零判分改动、零答案内容改动、零数据写入（DB 全程 `mode=ro`，读前读后 sha256 一致）、
零 git 写、零目录改名、未落任何脚本、未撤任何 strict-XFAIL 桩、未跑全量套件、未自登 insights 索引。
本档产出的 31 条映射表、迁移设计与 §三 读数均为**材料**，执行与否由日间拍板。
