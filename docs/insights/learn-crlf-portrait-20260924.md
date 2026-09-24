# learning 全仓 CRLF 逐目录×类型透视（l924-30 · 只读增量档）

> 任务：`zcode-bridge/inbox/l924-30.task.md`｜执行班：`qoder-executor-20260925-0450-learn33`｜取数时刻：2026-09-25 04:50–05:0x（+08:00）
> 性质：**只读画像＋分批建议**。本单零行尾转换、零 `.gitattributes` 写入、零生产码改动，净改动只有本档 ＋ 索引 1 行。
> 取数仓：`D:\code\learning-system`，`HEAD = 93d9969`（`09-25 04:40:32`），`git status --porcelain` 取数前现值 **0 项（干净）**。
> ⚠️ 该仓有信箱写手活动 ⇒ 本单**不跑任何测试套件**（纪律 §四.2），唯一例外是判据点名的索引闭合哨兵（见 §9）。

## 0. 本档的定位：只做前手没做的部分

同题的**根仓在册档** `D:\code\docs\insights\learning-crlf-profile-20260924.md`（单 `n924-32`，班 `pipe22`，已入库）已经把"多少件／为什么是 CRLF／autocrlf 从哪来／CSV 被谁钉"四件事取证到位。本档**不重贴**那些结论，只做它没做的四件：

| # | 本档增量 | 节号 |
|---|---|---|
| I-1 | **逐目录 × 类型透视表**（含"该目录该类型总件数"作分母 ⇒ 看得出众寡） | §2 |
| I-2 | **四类风险定性**：真必要 CRLF / 被钉成必要的 CRLF / 同目录混行风险件 / 中性件 ＋ 同目录 LF 并存明细 | §3 |
| I-3 | **`core/achievements.py` 逐行实测**（判据②点名） | §5 |
| I-4 | **≤3 批迁移建议**，每批带前置门禁、受影响件数、验证口径、回滚面 | §6 |

### 0.1 与 n924-32 的读数对表（一致 5 ／ 递进 1 ／ 订正 2）

| 读数 | n924-32 | 本档现取（09-25 04:5x） | 结论 |
|---|---|---|---|
| `git ls-files --eol` 的 `w/crlf` | 53 | **53** | ✅ 一致（本档独立复跑） |
| `i/crlf`＋`i/mixed` | 0 | **0** | ✅ 一致 ⇒ 仓库对象里零 CRLF |
| 字节轨：含 CR 55 − 二进制 2 | 53 | **53** | ✅ 一致，且本档给出 **750 件四分类完全闭合**（§1.1） |
| `.gitattributes` 份数 | 0 | **0** | ✅ 一致 |
| `core.autocrlf` 来源 | system 级 `C:/Program Files/Git/etc/gitconfig` | **同**（local/global 各 rc=1 未设，system=true） | ✅ 一致 |
| population | 746 tracked ＋ 1 untracked = 747 | **750 tracked ＋ 0 untracked** | ↗ 递进非矛盾：`e828dfe → 93d9969` 期间 l924-26/27/28/29 四份洞察入库（含原 untracked 那份） |
| CSV 的 CRLF 由哪一行钉 | 「`tests/test_hr_dataset_determinism.py:192` 把 CSV 必须 CRLF 钉成断言」 | **`:192` 其实对行尾免疫**；真正钉死的是 **`:191 raw == repo_raw`**、**`:194 repo_raw.endswith(b"\r\n")`**、**`:173` md5 钉值** | 🔴 **订正行号归属**（结论"CRLF 被当代码不变量钉"不变，本档 §3.3 三处复算全部支持） |
| 「按列断言者免疫，按字节断言者不免疫」 | 同 | **`tests/test_hr_dataset_columns_snapshot.py:200` 也显式 `assert ...endswith(b"\r\n")`** ⇒ 该"列级桩"同样不免疫 | 🔴 **订正**：全仓 CRLF 断言是**两处**不是一处（§3.3 表 R-c） |
| 「任何一班编辑过该件就把它变成 CRLF」（其 §2.4 机制） | 同 | **收窄为"取决于写入通道"**：波次 11 四份新档（l924-26/27/28/29 产物）现值全 `w/lf`，而同期被反复追加的索引件 `learn-insights-index-20260918.md` 仍是 `w/crlf`（133 行） | ⚠ 机制描述收窄（§7-P5） |

> 本档与 n924-32 **无任何互相矛盾的数字**；两处订正是"同一事实的更准行号/更全覆盖面"，其 53／0／52／30507 等读数本档逐条复算并背书。

---

## 1. 两轨现值与判据①的替代码径

### 1.1 轨道闭合表（本次现场重取，两轨集合逐字相同）

| 口径 | 取数 | 读数 |
|---|---|---|
| 人群 | `git ls-files` ∪ `git ls-files --others --exclude-standard` | **750**（tracked 750，未忽略 untracked 0） |
| 字节轨 | 逐件读字节分类 | 纯 CRLF **53** ／ 纯 LF **689** ／ 无行尾件 **6** ／ 二进制 **2** ⇒ **750 闭合** |
| git 轨 | `git ls-files --eol` | `w/crlf` **53** ／ `w/lf` **689** ／ `w/none` **6** ／ `w/-text` **2** ⇒ **750 闭合** |
| 两轨差集 | `set(rg) - set(bytes)` | `w/crlf` 与"纯 CRLF"**交集即全集**，差集 **∅** |
| 索引轨 | `i/crlf\|i/mixed` | **0**（`i/lf 742 ＋ i/none 6 ＋ i/-text 2 = 750`） |
| 件级混行尾 | 同档 LF 与 CRLF 并存 | **0 件**；孤立 CR **0 件**；BOM **0 件** |
| CRLF 行总量 | `sum(\r\n)` over 53 | **7957 行** |

`w/none` 6 件＝`core/__init__.py`、`core/runners/__init__.py`、`data/.gitkeep`、`tests/__init__.py`、`ui/__init__.py`、`ui/pages/__init__.py`；`-text` 2 件＝`assets/app.ico`、`assets/app.png`（含 0x0D 但与行尾无关，凡"含 CR 文件数"式统计会虚高到 55）。

### 1.2 🔴 判据①那条命令**不可门禁化**（本会话同一命令三态读数）

判据①原文：`rg -l $'\r$' --glob '!logs/**' --glob '!tmp/**' --glob '!data/**' --glob '!__pycache__/**' | wc -l` ＝「输出 48」。实测：

| 同一语义的四种写法 | 读数 | rc | 判定 |
|---|---|---|---|
| 判据①原文（数组式调用，无重定向） | **52** | 0 | 可用但**漏 1 件**（`.streamlit/config.toml`，rg 默认跳点目录） |
| 判据①原文 `> 文件` 重定向态 | **0** | **1** | ❌ **假零**——文件存在且空；stdout 被吞，rc 还是"无命中" |
| `c=$(rg -l $'\r$' .)` 命令替换态 | **739** | 0 | ❌ **假全命中**——CR 在 argv 传递中丢失，模式退化成 `$` |
| `rg -lP '\x0d' .`（python `subprocess` 直传 argv） | **52** | 0 | ✅ 稳态（ASCII 安全的字面 `\x0d`） |
| `rg -l -f <内含 CR 的模式文件>` | **20**（扫 `core/`） | 0 | ❌ rg 读模式文件时**剥掉行尾 CR** ⇒ 模式变空 ⇒ 全命中 |

⇒ **本档的"行数对平"口径改为两轨**：`git ls-files --eol` 的 `w/crlf` 计数 与 逐件字节读，两轨**同为 53 且集合逐字相同**（§1.1）。这条与纪律 §十二.1／§十三.4 同族（重定向与 argv 里的控制字符都不可信），**首次在 learning 仓实测到"同一命令三态"**。
⇒ 另记：`rg -l --hidden -P '\x0d' .` 读 **57** ＝ 52 ＋ `.streamlit/config.toml` ＋ **4 件 `.git/objects/**` 松散对象**（0x0D 落在压缩字节里）⇒ 想靠 `--hidden` 补那点漏计会顺手把 `.git` 拖进人群，**不是正确修法**；正确修法仍是"人群由 `git ls-files` 定义"。

### 1.3 票面「48」怎么处理

票面 48 是**投料时刻（09-24 00:40）的快照数**，现值两轨 **53**。差额分解 n924-32 §2.4 已给（51 → ＋2 新档 → 53；剩 −3 归"以人工核为准"），本档**不重复归因**，只背书两件事：① 现取仍是 53，未再涨；② 53 件的**集合与 n924-32 §4 桶表逐字相同**（16 py/pyw ＋ 3 csv ＋ 24 yaml ＋ 6 md ＋ 2 txt ＋ 1 bat ＋ 1 toml）。

---

## 2. 逐目录 × 类型透视表（增量 I-1）

### 2.1 主表：分母＝该目录该类型的**文本件数**（剔除二进制，含无行尾件）

| 目录 | 类型 | CRLF 件 | 该目录该类型总件 | 占比 | CRLF 行合计 |
|---|---|---|---|---|---|
| `(仓根)` | bat | 1 | 1 | 100% | 28 |
| `(仓根)` | pyw | 1 | 1 | 100% | 405 |
| `(仓根)` | txt | 2 | 2 | 100% | 208 |
| `.streamlit` | toml | 1 | 1 | 100% | 31 |
| `content/datasets` | csv | 3 | 3 | 100% | **1003** |
| `content/python/13_scipy_stats` | yaml | 3 | 6 | 50% | 69 |
| `content/python/14_sklearn_intro` | yaml | 4 | 5 | 80% | 93 |
| `content/python/15_ab_text` | yaml | 1 | 5 | 20% | 26 |
| `content/r/05_lm_anova` | yaml | 2 | 5 | 40% | 42 |
| `content/r/06_mixed_apa` | yaml | 4 | 6 | 66.7% | 91 |
| `content/r/07_glm` | yaml | 5 | 5 | 100% | 112 |
| `content/r/11_survival` | yaml | 3 | 5 | 60% | 73 |
| `content/r/12_clustering` | yaml | 2 | 5 | 40% | 47 |
| `core` | py | 4 | 16 | 25% | 1673 |
| `core/runners` | py | 1 | 6 | 16.7% | 132 |
| `docs/insights` | md | 6 | 84 | **7.1%** | 1076 |
| `scripts` | py | 1 | 16 | 6.2% | 128 |
| `tests` | py | 5 | 101 | **5.0%** | 1293 |
| `ui` | py | 1 | 3 | 33.3% | 349 |
| `ui/pages` | py | 3 | 7 | 42.9% | 1078 |
| **合计** | — | **53** | — | — | **7957** |

行数对平：`1+1+2+1+3+3+4+1+2+4+5+3+2+4+1+6+1+5+1+3 = 53` ✅（＝§1.1 两轨读数）

**读表三条**：
1. **众数在 yaml 而非 py**：24/53 ＝ 45% 的 CRLF 件是题面 yaml，但按"行量"看 py 桶（16 件 5673 行）才是主体——票面把 yaml 单列一批是对的，它的**分母最小、占比最高**（题面族 24/410 ＝ 5.9%，但落点全挤在 8 个簇里的 2 个簇）。
2. **`docs/insights` 是"越用越脏"的典型**：84 份 md 里只有 6 份 CRLF（7.1%），且这 6 份的 mtime 逐条早于其余 78 份 ⇒ 它不是"格式选择"，是**当年写入通道**的化石（§7-P5）。
3. **`tests` 5/101、`scripts` 1/16** ——测试族几乎全 LF，那 5 件是异类；而**恰好**是全仓最大的 5 个测试件（`test_ui_behavior.py` 596 行、`test_scripts.py` 486 行）⇒ 谁被改得最多，谁的行尾最可能翻转。

### 2.2 逐目录汇总（并存面＝同目录既有 CRLF 又有 LF 文本件）

| 目录 | CRLF | 同目录 LF/无行尾 | 形态 |
|---|---|---|---|
| `(仓根)` | 4 | 6 | 并存 |
| `.streamlit` | 1 | 0 | **整目录 CRLF**（且 rg 默认看不见它） |
| `content/datasets` | 3 | 1 | 并存 |
| `content/python/13_scipy_stats` | 3 | 3 | 并存（半数） |
| `content/python/14_sklearn_intro` | 4 | 1 | 并存 |
| `content/python/15_ab_text` | 1 | 4 | 并存 |
| `content/r/05_lm_anova` | 2 | 3 | 并存 |
| `content/r/06_mixed_apa` | 4 | 2 | 并存 |
| `content/r/07_glm` | 5 | 0 | **整目录 CRLF** |
| `content/r/11_survival` | 3 | 2 | 并存 |
| `content/r/12_clustering` | 2 | 3 | 并存 |
| `core` | 4 | 12 | 并存 |
| `core/runners` | 1 | 5 | 并存 |
| `docs/insights` | 6 | 78 | 并存 |
| `scripts` | 1 | 15 | 并存 |
| `tests` | 5 | 96 | 并存 |
| `ui` | 1 | 2 | 并存 |
| `ui/pages` | 3 | 4 | 并存 |

⇒ 19 个有 CRLF 的目录里 **17 个是并存态**，只有 `.streamlit` 与 `content/r/07_glm` 是整目录 CRLF。**并存才是风险本体**：同目录两种行尾 ⇒ 编辑器/patch 交错时整档重排 ⇒ 假 diff（见 §3.2 明细）。

### 2.3 逐类型汇总（分母＝全仓该类型文本件）

| 类型 | CRLF | 全仓该类型 | 占比 |
|---|---|---|---|
| yaml | 24 | 410 | 5.9% |
| py | 15 | 151 | 9.9% |
| md | 6 | 174 | 3.4% |
| **csv** | **3** | **3** | **100%** |
| **txt** | **2** | **2** | **100%** |
| **toml** | **1** | **1** | **100%** |
| **pyw** | **1** | **1** | **100%** |
| **bat** | **1** | **1** | **100%** |

⇒ `csv/txt/toml/pyw/bat` 五类**分母即 1 ＝ 全类沦陷**（这些类型的"另一形态"根本不存在，谈不上并存）；真正的"类型内并存"只有 yaml／py／md 三类。**这个分母就是 §6 分批的依据**：只有存在 LF 同类的类型，统一行尾才有"消除并存"的收益。

---

## 3. 风险分类：真必要 / 被钉必要 / 混行风险 / 中性（增量 I-2）

### 3.1 四类计数（和 ＝ 53）

| 类 | 件数 | 成员 | 依据 |
|---|---|---|---|
| **N 真必要 CRLF** | **1** | `start.bat` | cmd.exe 对 LF-only 批处理 `if (...)` 块解析有坑；且 `bat` 类分母 1 无 LF 同类 ⇒ **零并存收益** |
| **P 被钉成必要** | **19** | 3 csv ＋ 16 `content/r/**.yaml` | 测试按**字节/endswith** 断言（§3.3 R-a/R-b/R-c）＋ 与 gitignored 的 pre-D6 基线互锁（R-d） |
| **M 混行风险件** | **24** | 15 py ＋ 1 pyw ＋ 8 `content/python/**.yaml` | 同目录存在 LF 同类（§3.2 明细）＝票面点名的"编辑器/patch 交错易出假 diff"面 |
| **Z 中性低收益** | **9** | 6 md ＋ 2 txt ＋ 1 toml | 无测试按字节读；txt/toml 类分母 1（无 LF 同类），md 并存但零承重 |

> 票面把「csv 数据件」列入"必要 CRLF"——**按磁盘现状对，按成因不对**：CSV 的 CRLF 既不是数据要求也不是 git 要求（仓库 blob 是 LF），是**测试把它钉成断言**＋**生成器自己写 `\r\n`** 两件事的合力（§3.3 R-a/R-b）。⇒ 归到 P 类才可直接指导下一步（要动它必须先动测试/生成器）。

### 3.2 同目录 LF/CRLF 并存明细（M 类逐件，py 与 yaml 两桶）

| 目录 | 类型 | CRLF | LF | 并存 CRLF 件 |
|---|---|---|---|---|
| `core` | py | 4 | 12 | `achievements.py` `ai_review.py` `loader.py` `progress.py` |
| `core/runners` | py | 1 | 5 | `r_runner.py` |
| `scripts` | py | 1 | 15 | `backup_data.py` |
| `tests` | py | 5 | 96 | `test_ergo_h912_13.py` `test_judge_contract_edges.py` `test_judge_pure.py` `test_scripts.py` `test_ui_behavior.py` |
| `ui` | py | 1 | 2 | `styles.py` |
| `ui/pages` | py | 3 | 4 | `dashboard.py` `mistakes.py` `path.py` |
| `content/python/13_scipy_stats` | yaml | 3 | 3 | `02_two_sample_t` `03_paired_t` `05_correlation` |
| `content/python/14_sklearn_intro` | yaml | 4 | 1 | `01_lin_reg_coef` `02_r_squared` `03_predict` `05_kmeans` |
| `content/python/15_ab_text` | yaml | 1 | 4 | `02_cohens_d` |
| `content/r/05_lm_anova` | yaml | 2 | 3 | `02_lm_r2` `03_anova_p` |
| `content/r/06_mixed_apa` | yaml | 4 | 2 | `01_lmer_fixef` `03_cohens_d` `04_eta_squared` `05_apa_t` |
| `content/r/11_survival` | yaml | 3 | 2 | `02_survfit_median` `03_logrank` `04_cox_hr` |
| `content/r/12_clustering` | yaml | 2 | 3 | `03_cluster_size` `05_silhouette` |

> `launcher.pyw` 归 M 类的理由：`pyw` 类分母虽是 1，但它与仓根 `app.py`（LF，py 类）**同目录且同为 Python 源码**，假 diff 面成立。
> `content/r/07_glm` 的 5 件虽整目录 CRLF（无目录内存续），但与 `content/r` 其余四簇（12 CRLF / 10 LF）构成**簇间并存**，故仍随 r 族一起落在 P 类的门禁里（R-d 的备份基线覆盖 `content/r/**` 全 84 件）。

### 3.3 行尾承重台账（迁移前必须逐条过闸）

| 编号 | 承重件 | 现值实测 | 若把该族转 LF |
|---|---|---|---|
| **R-a** | `tests/test_hr_dataset_determinism.py`（该件自身 LF） | `:63 PINNED` md5 三件 **全命中**（`579f97fb…`/30507、`a1e6d988…`/13570、`578c8547…`/16660）；`:84 PINNED_LINES` = 501/201/301；**`:173`** 断言仓内现件 md5＋size ＝ 钉值；**`:191`** `assert raw == repo_raw`（raw 为再生成件，恒 CRLF）；**`:194`** `assert repo_raw.endswith(b"\r\n")` | **红三处**：md5 变（沙盒 LF 化实测 `2a4feb0f`/30006、`f3f42892`/13369、`f72ffa52`/16359）、`:191` 逐字节不等、`:194` endswith 假。⇒ 这是"环境红"：`core.autocrlf=false` 的机器 checkout 出 LF 就当场红 |
| **R-b** | 生成器 `content/datasets/generate_hr_data.py:44/71/100`（自身 LF） | `open(path,"w",newline="",…)` ＋ `csv.DictWriter` 未给 `lineterminator` ⇒ 默认 `\r\n`。**沙盒实跑复证**：把脚本 copy 到 `D:\code\tmp\learn33\regen`（`OUT_DIR` 跟 `__file__` 走 ⇒ 零触碰仓内）执行 rc=0，三件产出 bytes 30507/13570/16660、crlf 501/201/301、**与仓内现件逐字节相同 = True**、"与仓内 LF 化后相同 = False"；跑完仓内三件 md5 前后不变 | 与 autocrlf 无关：**任何平台重跑都产 CRLF** ⇒ 只改工作树不改生成器＝重跑即脏 |
| **R-c** 🔴 | `tests/test_hr_dataset_columns_snapshot.py:200` | `assert (DATASET_DIR / name).read_bytes().endswith(b"\r\n")`，同函数 `:199` 用的是 `count(b"\n")`（行尾免疫）。注释 `:196` 自述"本三件纯 CRLF 且以 CRLF 收尾" | **第二处 CRLF 断言**，且**意图与写法不符**：作者想钉"末尾有换行"，钉成的却是"末尾是 CRLF" ⇒ LF 化后即使真以 `\n` 收尾也照样红。n924-32 R5 判该件"免疫"，本档否证 |
| **R-d** 🔴 | `tests/test_mark_r_judge_plain.py:588-614` ＋ **gitignored** 的 `data/backups/content-20260920-133722/` | 备份在盘（`manifest-before.txt` 87 行；`content/r` 下 **84 件**，其中**纯 CRLF 16 件**）；`:606` 断言 `sha256(备份字节) == manifest`；`:609` 断言 `现状字节 == _expected_after_insert(old, MARK_LINE)`（old 即 CRLF 备份字节）；`:614` `changed == 70`。`data/backups/` 命中 `.gitignore:9` ⇒ `git ls-files data/backups` 读 **0** 件 | 本机红（16 件 r/ yaml 若 LF 化 ⇒ `new != old+一行`）；**异地 `:592 pytest.skip`**（备份不在盘）。⇒ 这条**不会在 CI 上暴露**，只咬本机：本机承重型门禁。另：`tests/test_content_crlf.py` 的 docstring（l922-04）**已自述过这处坑**并说明为何放弃钉"零 CR"——它给的 24 件 CRLF yaml／16 件 r/ 读数与本档 §2.1 逐字相同（独立复证） |
| **R-e** | `tests/test_content_crlf.py`（钉"裸 CR=0"＋"单档内不混行尾"） | 人群 `content/**/*.yaml` 现值 410 件，本档实测 **lone CR 0 件／单档混行尾 0 件** | 整档 LF 化后该桩**照绿**（它允许"要么全 LF 要么全 CRLF"）⇒ **yaml 族迁移唯一不撞的桩**，故 §6 批 2 可行 |
| **R-f** | py / md / txt / toml 族 | 全仓测试的 `read_bytes()` 目标**只**命中 `content/datasets/*.csv`、`content/r/**.yaml`、以及 `data/backups/**`（§3.3 R-a…R-d）＋ 沙盒临时件 ⇒ **无一按字节读 py/md/txt/toml** | 转 LF **零测试门禁**；只有编辑器层面的一次性 churn |

---

## 4. `.gitattributes` 与 `core.autocrlf` 核对（判据③，命令原文见 §8）

| 检点 | 现取读数 |
|---|---|
| 全仓 `.gitattributes`（排除 `.git/`、`.venv/`） | **0 份** |
| `git config --local --get core.autocrlf` | 无输出，**rc=1**（仓内未设） |
| `git config --global --get core.autocrlf` | 无输出，**rc=1**（用户级未设） |
| `git config --system --get core.autocrlf` | **true**，来源 `file:C:/Program Files/Git/etc/gitconfig` |
| `git ls-files --eol` 的 `attr/` 列 | 750 行全带 `attr/` 标签、值全空 ⇒ 无任何 eol 属性规则 |
| 归一是否已在发生（`hash-object --path` vs `rev-parse HEAD:<f>`） | 7 件抽样（bat/csv/yaml×2/py/md/pyw 各覆盖一类）**7/7 SAME**，且 `--no-filters` 全 DIFF ⇒ 套 filter 后的 blob 就等于 HEAD blob：**仓库里存的本来就是 LF** |

⇒ 与 n924-32 §3 完全一致（本档独立复跑、样本从 5 件扩到 7 件并把 yaml/md 纳入）。**行尾行为由"这台机器"决定，不由"这个仓"决定**，且"归一到 LF 入库"已经在发生——这是 §6 全部批次"零 blob 变化"的前提。

---

## 5. `core/achievements.py` 逐行实测（判据②，增量 I-3）

锚点复核：`:1` = `"""Achievement system: badges, streaks, milestones."""`（`rg -n` 命中，**0 漂移**；首 40 字节 `b'"""Achievement system: badges, streaks, '`）。

| 口径 | 读数 |
|---|---|
| 字节数 | 11079（md5 `639f9b5906bc37d3c312ca6d56aeedd5`） |
| `\r\n` 计数 | **250** |
| `\r` 计数 / `\n` 计数 / 差 | 250 / 250 / **0** ⇒ 零孤立 CR |
| 以 LF 切分的段数 | **251**（末段 `b''` ⇒ 文件以换行收尾） |
| 前 251−1 段中以 CR 结尾的段数 | **250**；非 CRLF 行号集合 **`[]`（空）** |
| `wc -l` / `rg -c ''` | 250 / 250 |
| `b.splitlines()` | 250 |
| `split(b'\r\n')` 片段数 | 251（末片段 `b''`） |

⇒ **票面「250/251」两个数都成立，是两种口径**：真实文本行 **250**（每行都以 CRLF 收尾）；按 `\n` 切段得 **251**（末段是收尾换行留下的空段）。**件内混行尾 = 0** ⇒ 该件是"纯 CRLF"，与 n924-32 R8"件级零混行尾"一致；风险不在件内，在 `core/` 目录内 4 CRLF ／ 12 LF 的并存（§3.2）。

---

## 6. 规范化迁移分批建议（≤3 批，增量 I-4）

> 大前提（沿用 n924-32 R2，本档 §4 的 7 件抽样独立复证）：**仓库 blob 已是 LF ⇒ "为清理而转换"在 git 视角是 no-op，churn 53 件、收益 0**。所以这三批的实质**不是转行尾，而是"把行尾口径从 system 级 gitconfig 收进仓库"**（`.gitattributes`），转换只是它的副作用。
> 🔴 **本单一律不执行**：三批都要写仓内跟踪件、批 1/3 还要 `git add --renormalize`（＝改 750 件属性口径），全部落在人工/主班闸后。

| 批 | 范围（受影响件数） | 前置门禁 | 落地动作 | 验证口径（现取基线） | 回滚面 |
|---|---|---|---|---|---|
| **批 1 · 非承重类属性入仓** | **25 件**：M 类 py/pyw 16 ＋ Z 类 9（6 md ＋ 2 txt ＋ 1 toml） | 无测试门禁（R-f 已逐件排除）；只需独占写窗 | 新建 `.gitattributes`：`*.py/*.pyw/*.md/*.txt/*.toml → text eol=lf`、`*.bat/*.cmd → text eol=crlf`、`*.ico/*.png → binary`；**这一批故意不写 `*.csv`／`*.yaml`** | `git ls-files --eol \| grep -c w/crlf` 应从 **53 → 28**；`i/crlf` 仍 **0**；`git status --porcelain` 收尾应回 **0 项**；测试面**一条都不用改** | 删 `.gitattributes` 一行即恢复该类现状；blob 零变化 ⇒ 无数据回滚需求 |
| **批 2 · `content/python` 8 件 yaml** | **8 件**（13_scipy_stats 3 ＋ 14_sklearn_intro 4 ＋ 15_ab_text 1） | R-d 的 pre-D6 备份基线**只覆盖 `content/r/**`**，实测 python 簇 **0/8 命中**；R-a/R-c 只作用 csv ⇒ 无门禁 | `.gitattributes` 追加 `content/python/**.yaml text eol=lf`（按簇收窄，**不要写全局 `*.yaml`**） | `tests/test_content_crlf.py` 仍绿（R-e：整档 LF 合规）；`tests/test_content_census_python.py` 绿；`w/crlf` 从 28 → **20** | 删该行；题面值零变化（`yaml.safe_load` 对 CRLF/LF 同解） |
| **批 3 · 承重组（r/ 16 yaml ＋ csv 3 ＋ bat 1）——闸后，不派** | **20 件** | 🔴 三处硬门禁：**R-a**（3 个 md5 钉值＋`PINNED_LINES`）、**R-c**（两处 `endswith(b"\r\n")`）、**R-d**（gitignored 的 pre-D6 字节基线，改它＝改证据件） | 二选一，**不可混着做**：<br>**3A（推荐，零 churn）** 承认现状：`*.csv text eol=crlf` ＋ `content/r/**.yaml text eol=crlf` ＋ `*.bat text eol=crlf` ⇒ 与生成器默认 `lineterminator`、两处 endswith、备份基线**全部天然对齐**，只是把"本机偶然"写成"仓内规定"。<br>**3B（动数据）** 先改 `generate_hr_data.py:44/71/100` 加 `lineterminator="\n"` → 重生成 → 重钉 3 个 md5/size（LF 现值实测 `30006/13369/16359`）＋ 放宽 `determinism:191/194` 与 `columns_snapshot:200` 的断言 ＋ 重建 pre-D6 备份基线 | 3A：`w/crlf` 从 20 → **20**（csv3＋r16＋bat1 ＝ 20 件保持 CRLF 且**从此与机器无关**）；测试零改。3B：全量红名集须与改前逐条比对，且**异地从 skip 变真跑**（新增信号面） | 3A 删属性行即回。3B 是**真改数据集字节**（`30507 → 30006`），属纪律点名"会真删/真改数据行"的形态 ⇒ **必须独占窗＋人工放行**，本单未做也不建议先做 |

**批次顺序**：**1 → 2 → （人工裁决 3A/3B）**。反序会撞两处：先写全局 `*.yaml eol=lf` ⇒ r/ 16 件当场红（R-d）；先写 `*.csv eol=lf` 而不改生成器 ⇒ checkout 与重跑互相打脸（R-b）。
**为什么不并成一批全做**：批 1/2 的红名集是"空"，批 3 的红名集是"数据/字节基线族"——混一批会让批 1 的零风险属性也被拖进人工闸，且失败时不可归因。

---

## 7. 否证／收窄清单（判据与前提逐条实测）

| # | 票面前提 | 实测 | 处理 |
|---|---|---|---|
| P1 | 「实测 48 件 CRLF 存盘」／判据①「输出 48」 | 两轨现值 **53**；票面原命令形态读数 **52／0(rc=1)／739** 三态漂移（§1.2） | 判据①**改口径为两轨**，不判 failed（纪律 §五.2）；"48" 归因沿用 n924-32 §2.4，不重复 |
| P2 | 判据①的四个 `--glob` 起排除作用 | 加与不加读数不变；`logs/` 本就是空目录、`__pycache__/.venv/*.log` 已被 `.gitignore` 挡住而 rg 默认尊重 | 记为**无效前提** |
| P3 | 「散布 core/ui/content/根」四类落点 | 实测 **19 个目录**，其中票面未点名的 `content/python/*` 3 簇 ＋ `content/r/*` 5 簇 ＝ **8 簇 24 件 yaml 才是最大块**（占 45%） | 画像按 §2.1 补全 |
| P4 | 「必要 CRLF（csv 数据件）」 | csv 的 CRLF 与"数据"无关：blob 是 LF，是 `determinism:191/194`＋`columns_snapshot:200`＋生成器默认值三处合力 | 重新归类为 **P 被钉必要**（§3.1） |
| P5 | 「混行风险件＝py 与同目录 LF 件并存」 | 成立且**不止 py**：yaml 12 件同样目录并存（§3.2）。另 n924-32 §2.4 的"任何编辑都产 CRLF"机制**收窄为"取决于写入通道"**：l924-26/27/28/29 四份新档现值 `w/lf`，同期索引件仍 `w/crlf` | 分类按 §3.1/§3.2 扩面 |
| P6 | 「content yaml 单列一批防 md5 钉桩连锁红」 | **成立且比票面更硬**：r 族 16 件与 gitignored 备份基线互锁（R-d），且该桩**异地 skip**、只咬本机 | 落成 §6 批 2/批 3 的簇级切分 |
| P7 | 「`core/achievements.py` 250/251 行 CRLF」 | 250 行全 CRLF；251 是 `split('\n')` 段数；件内混行尾 0 | 两口径并存，§5 留档 |
| P8 | 判据④「零文件改动」 | 见 §9 | 成立（净改动仅 2 份文档件） |

---

## 8. 复算命令（本单实际用法；一律取 rc 不接管道）

```bash
# —— 人群与两轨（本档口径的权威替代，判据①不可用）——
$ git -C D:/code/learning-system ls-files --eol | wc -l                     # 750
$ git -C D:/code/learning-system ls-files --eol | rg -c " w/crlf "          # 53
$ git -C D:/code/learning-system ls-files --eol | rg -c "i/(crlf|mixed)"    # 0（rc=1 属"零命中"，非错误）
$ python D:/code/tmp/learn33/eol_scan.py                                    # 字节轨：53/689/6/2 四分类闭合
$ python D:/code/tmp/learn33/setdiff.py                                     # rg 轨 52 ⊂ 字节轨 53，缺且仅缺 .streamlit/config.toml

# —— 判据①原文的三态失真（§1.2）——
$ rg -l $'\r$' --glob '!logs/**' --glob '!tmp/**' --glob '!data/**' --glob '!__pycache__/**' > f.txt; echo $?; wc -l < f.txt   # 0 / 空文件（假零）
$ c=$(rg -l $'\r$' .); echo $(printf '%s\n' "$c" | wc -l)                                                                  # 739（假全命中）
$ rg -lP '\x0d' . | wc -l                                                                                                  # 52（稳态，仍漏点目录）

# —— 分类与门禁 ——
$ python D:/code/tmp/learn33/pivot.py                                       # §2/§3 透视与并存明细、四类计数
$ python D:/code/tmp/learn33/pins.py                                        # §3.3 R-a…R-d：md5 现值/LF 化推演/hash-object/备份覆盖面/沙盒重跑
$ git -C D:/code/learning-system check-ignore -v data/backups/              # .gitignore:9:data/backups/
$ rg -n "PINNED|count\(b|endswith" D:/code/learning-system/tests/test_hr_dataset_determinism.py       # :63/:84/:173/:191/:192/:194
$ rg -n "endswith\(b" D:/code/learning-system/tests/test_hr_dataset_columns_snapshot.py               # :200
$ rg -n "现状字节|sha256" D:/code/learning-system/tests/test_mark_r_judge_plain.py                    # :588/:589/:606/:609/:614
$ rg -n "open\(|DictWriter" D:/code/learning-system/content/datasets/generate_hr_data.py              # :44/:45 :71/:72 :100/:101

# —— 判据②：core/achievements.py 逐行 ——
$ rg -n "Achievement system: badges" D:/code/learning-system/core/achievements.py                      # 命中 :1
$ python -c "b=open(r'D:/code/learning-system/core/achievements.py','rb').read();print(len(b),b.count(b'\r\n'),b.count(b'\r'),b.count(b'\n'))"   # 11079 250 250 250

# —— 判据③ ——
$ (cd D:/code/learning-system && find . -name .gitattributes -not -path "./.git/*" -not -path "./.venv/*" | wc -l)   # 0
$ git -C D:/code/learning-system config --system --get core.autocrlf      # true
$ git -C D:/code/learning-system config --list --show-origin | rg -i autocrlf
```

临时件：`D:\code\tmp\learn33\{eol_scan,pivot,pins,setdiff}.py` ＋ `bytescan.tsv` ＋ `regen/`（沙盒生成器产物）——全在根仓 gitignored 的 `tmp/` 下，learning 仓**零写入**。

---

## 9. 本档自身的行尾读数（§7-P5 机制的现场复验，已实测）

| 检点 | 读数 |
|---|---|
| 登记前 `git status --porcelain` | **0 项**（干净，HEAD `93d9969`） |
| 本档经 **Write 工具**落盘 | 28728 字节、`\r\n` = **0**、`\n` = 303 ⇒ **纯 LF** |
| 索引件经 **Edit 工具**插入 1 行后 | `git diff --numstat` = **`1 0 docs/insights/learn-insights-index-20260918.md`**（恰 1 增 0 删）；字节复验 33839 B／crlf **134**／lf **134**／lone CR **0** ⇒ **仍纯 CRLF，未被打散** |
| 登记后 `git status --porcelain` | **2 项**：`?? docs/insights/learn-crlf-portrait-20260924.md`、` M docs/insights/learn-insights-index-20260918.md` |
| `git ls-files --eol` 新档 | 不出现在列表里（**未跟踪**），故 §2.1 的 53 与本单产出**无耦合** |

⇒ **机制坐实（比 n924-32 §2.4 更准的口径）**：本仓工作树行尾**由写入通道决定，不由"是否被编辑过"决定**——
① Write/新建通道产 **LF**（本档 ＋ 波次 11 四份新档一致）；② Edit 单行插入**保形**（CRLF 件仍是 CRLF、零整档重排）；③ Python 文本模式 `open(...,'w')` 写盘产 **CRLF**（索引件 09-25 04:34 的 mtime 与它 134 行 CRLF 同时成立，正是上一路 `learn32` 用脚本追加登记留下的化石）。
⇒ 下传口径：**别再用"谁编辑过"解释 CRLF 增量**；要判来源只看写入通道。这条同时说明 §6 批 1 若落地，新产档天然合规，不需要额外约束工具。

> **追记（同班下一单 l924-31 取数时撞到的旁证，09-25 05:0x）**：给 `docs/system-report-v0.6.3.md`／`v0.6.4.md` 各加 1 行头部指针后跑 `git diff --numstat`，git 主动警告
> `warning: in the working copy of 'docs/system-report-v0.6.3.md', LF will be replaced by CRLF the next time Git touches it`（两件各一条）。
> ⇒ 这是 §7-P5 的**机器自证**：`core.autocrlf=true` 下 git 认为这两件"下次被我碰到就该是 CRLF"，而它们现值 `w/lf` 正是"上次由工具写"的结果。
> ⇒ 一条前瞻读数：**53 不是稳定值**——本批 4 件文档被主班提交后，任何一次 `git checkout`/`git add` 触碰到它们就会把它们（以及那 4 份 LF 新档）翻成 CRLF，`w/crlf` 会随之上涨。复算该读数时**先记 HEAD 再记 status**，别把"数字变了"当回归。§6 批 1 的 `.gitattributes` 正是终结这种漂移的手段。


