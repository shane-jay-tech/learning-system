# l927-14 复习「暂停」态：甲案／乙案裁决材料（只读，零码改动）

- 班次：`qoder-executor-20260927-1820-learn47`（波次 22 只读采集位），取数现点 2026-09-27T18:0x（本机 `date`）
- 仓现值：HEAD `bbceef5`、`git status --porcelain` 行数 0（本班未 add／commit／checkout／restore／stash／clean）
- 锚点：`zcode-bridge/outbox/20260925-154240-8c05.result.md` → **实际在 `D:\code\zcode-bridge\done\20260925-154240-8c05.result.md`**（13,103 B，路径搬家非缺陷，按 brief §3a 口径取用）
- 判据面：**「改不改第三态」是产品裁决，不是本班能签的口径改动**。本班不改状态机、不改 `next_due_date` 语义、不改判分／调度口径、不改任何测试断言。
- 生产库未被本班写过：`data/progress.db` 三点取样 **122,880 B ／ sha8 `cd2dbce4`**（开工 17:59:20、探针后 18:03、收稿 18:04:46 全等；在册基线同值）。只读探针见「可复算入口」P-0，试写两条均得 `sqlite3.OperationalError: attempt to write a readonly database`。

---

## 0. 锚点复核：在世的部分与已收窄的部分

| 锚点断言（8c05） | 本班复核读数 | 结论 |
|---|---|---|
| 「本仓无『暂停』实体」：`暂停\|paused\|suspend\|archive` 在 `core/**` `ui/**` 0 命中 | 固定串普查（`rg -F`，`--glob '!tmp/**'`，扫 core ui scripts tests）：`暂停`／`pause`／`suspend`／`archive` 各命中 **1 个文件**，且**全部是同一件** `tests/test_review_state_machine_rules.py`（:10 说明行、:202 注释、:204 测试名、:211 那条自查正则本身）。`停用`／`suspended`／`archived` 0 命中。 | ✅ **成立且更强**：唯一的命中就是 8c05 自己下的否证桩（它扫 `core`／`ui`，测试件在 `tests` 所以不自命中）。生产码里仍零暂停实体。 |
| 「`last_result` 取值域只有 pass／fail」 | `core/progress.py:420` 仍是 `"pass" if passed else "fail"`；全仓 `last_result\s*(==\|!=)` 读者只有 `core/progress.py:468` 的 `== "fail"` 一处。真库 `SELECT DISTINCT last_result FROM review_state` → **空集**（表 0 行）。 | ✅ 成立 |
| 「甲案：把 `next_due_date` 推远等价于暂停或不动（**间隔本就只影响推荐位**）」 | 见 §2 —— 括号这半句**过宽**：`next_due_date` 的读者不止推荐位。 | ⚠️ **按实况收窄**，等价性只在两个限定条件下成立（§2 的 E-1／E-2） |
| 「乙案 ⇒ `test_复习态取值域只有pass与fail没有第三态` 与 `test_review_mastery_bounds` 一族会同时红」 | 前者确认存在（`tests/test_review_state_machine_rules.py:216`，源码字面断言 `vals == {("pass","fail")}`）。后者**按字面不成立**：`test_review_mastery_bounds.py` 钉的是公式串与 DDL 默认值（`:183-186`），新增 `suspended` 列不会让它红；只有当乙案改动 `update_review_state` 的公式／默认值／三元组时才连带红。 | ⚠️ **收窄**：真正的第一批红项是 §4 清单里那两件**否证桩**，`mastery_bounds` 属「改公式才红」的第二批 |
| 「`data_portability` 的导入校验要跟着改」 | `core/data_portability.py:42-43`（导出列名串）与 `:133-138`（8 个占位符 INSERT）都是**硬编码列**；`scripts/import_dry_run.py:55` 另有第三处列名清单。 | ✅ 成立，且实为 **3 处**（不是 1 处） |

---

## 1. 两案矩阵

| 维度 | **甲案（窄）**：不改状态机，用「推远 `next_due_date`」或「干脆不动」表达暂停 | **乙案（宽）**：新增第三态（`last_result` 加值 或 新列 `suspended`） |
|---|---|---|
| 语义保真度 | **近似**。到期队列里消失＝「现在不催」，不等于「用户声明不要复习这题」；`review_state` 行仍在，`total_pool` 仍计数（E-4） | 高。暂停是显式意图，可与「未到期」区分，统计面能把分母一起摘掉 |
| 可达性（有没有入口能做） | 🔴 **产品面上做不到**：全仓除 `update_review_state`（`core/progress.py:388`，唯一写 `next_due_date` 的生产函数）与导入侧（`core/data_portability.py:133`）外，**没有任何 UI／脚本能设 `next_due_date`** —— `rg "UPDATE review_state"` 在 core／ui／scripts **0 命中**，3 处命中全在 `tests/test_recommend_review_state.py:34/:40/:65`。⇒ 所谓「推远」＝**人手 SQL 直改生产库** | 需要新建入口（按钮＋一个写函数＋一条列），全部是常规增量开发 |
| 持久性 | 🔴 **不持久**：`next_due = date.today() + interval`（`:412`）在每次作答时重写，而练习入口完全不读到日期（`ui/pages/language.py` 对 `review_state`／`next_due_date`／`get_due_reviews`／`due_review_ids` **0 命中**）⇒ 用户一旦被暂停的题从别的通道（错题本／链接／首页）答一次，暂停**当场蒸发**（E-3 实测） | 持久，作答不覆盖显式暂停位（前提是新态不被 `update_review_state` 顺手改写——这本身要写代码钉） |
| 覆盖面 | 只覆盖「已进复习循环（有 `review_state` 行）且非错题」的题。真库 `review_state` **0 行** ⇒ 现网**没有任何一行可推**（E-5）。错题身份的题即使推远仍从 `wrong_retry`／`path_blocking` 回到推荐里（E-2） | 全量（可对任意题建显式暂停位），但要先回答「暂停态存在哪：`last_result` 还是新列」 |
| 迁移／DB 面 | 零 schema 迁移，**但不是零 DB 写**：推远本身是一次 `UPDATE review_state`；对无行的题则要先 `INSERT`，等于伪造 `interval_days=3/ease=2.0/streak=0` 的复习态 | 迁移：`_migrate()`（`core/progress.py:149-166`）有现成 `ALTER TABLE ... ADD COLUMN` 先例（rubric_scores 三列）；若走 `last_result` 加值则无迁移、但撞取值域哨兵 |
| 测试面代价 | 表面零代价（不动断言就能跑），实际是**把不变量藏在人手 SQL 里**：没有任何测试能钉住「用户暂停了这题」这件事，未来任何改动都可能悄悄把它变成永久暂停或悄悄解除 | 见 §4 清单：2 件否证桩**按设计必红**（要人工重新钉），19 件测试引用 `review_state`／12 件引用 `last_result` 要过一遍，3 处硬编码导出／导入列名串要同步 |
| 统计口径连带 | 静默改 5 个消费点的读数（到期数、分桶、high_risk、报告 due 计数、首页「今日复习」），且 `total_pool` 不跟着减 ⇒ 复习健康度**被无声美化** | 要不要把这些消费点口径改成「排除暂停」是一次**明确的口径选择**（要人工拍，改了是可审计的） |
| 回滚成本 | 低但**不可自动**：`data/*.db` 与 `data/backups/` 都在 `.gitignore`（本仓 `.gitignore:6-11`）⇒ git 里没有还原点；撤销一次推远只能靠再次人肉 SQL 或备份恢复。且推远不落审计事件，事后无法知道哪些题被谁推过 | 中：SQLite `ADD COLUMN` 不能靠简单 DROP 回退（需表重建），且**回退本身也是新写入**；若走 `last_result` 加值，回滚＝改回三元组＋重钉哨兵，代码面可回滚、数据面已写进真库的那几行回不了 |
| 谁能在本波做 | 都不能。甲案的执行形态（人肉写生产库）＝人工闸；乙案＝迁移＋取值域变更＋新增 UI 入口＝人工闸 | 同左 |

---

## 2. 甲案等价性论证（这是本班新取证的部分）

甲案的原话是两个断言：**(A) 推远 `next_due_date` 等价于暂停**；**(B) 间隔本就只影响推荐位**。实测结论：

### E-1 断言 B 过宽：`next_due_date`／到期队列的读者不止推荐位

现役读者（全部在 `next_due_date <= today` 这一条谓词上）：

| 读者 | 位置 | 推远后的可见后果 |
|---|---|---|
| 推荐引擎「到期复习」来源 | `core/recommend.py:63`（`due_review_ids(limit=1000)`）→ `:91` `review` → `:134 _fill(review, "到期复习", "review_due", 2)` | 该题退出这个配额位 |
| 首页「今日复习」计数 | `ui/pages/home.py:306`（`get_due_reviews(limit=5)`）＋ `:310 review_count = len(due_reviews)+len(mistakes)` | 「N 题待复习」变小；错题部分不受影响（E-2） |
| 错题本页「到期复习」tab 与汇总行 | `ui/pages/mistakes.py:75`（`limit=50`）、`:85`（`get_due_reviews_total()`）、`:129-131`（按 `next_due_date` 算逾期天数） | tab 消失／汇总行数字降 |
| 复习健康度 | `core/progress.py:449 review_health_stats()`（`total_due`、`buckets`、`high_risk`）→ `ui/pages/dashboard.py:606`、`:612`（`AVG(interval_days)` 另算） | `total_due` 与三个逾期分桶一起降为 0；`total_pool` **不变** |
| 周报 | `core/report.py:33`（`len(d.get_due_reviews(limit=100))`） | 报告里的「到期」数下降 |
| 到期真数出口 | `core/progress.py:638 get_due_reviews_total()`（谓词与 `get_due_reviews` 逐字同源，注释自证） | 同上 |

⇒ **「只影响推荐位」不成立**，至少 6 个消费面会跟着动。其中 `review_health_stats` 的 `total_pool = COUNT(*) FROM review_state`（`:470`）**不看日期**，所以推远＝分子掉、分母不掉 ⇒ 健康度指标被静默改善，而用户并没有做任何复习动作。这就是「暂停」与「推远」的第一处真实语义差。

### E-2 断言 A 的第一处破产：错题身份让暂停失效（结构性的，非边角）

`core/recommend.py:91` 的到期来源**显式排除错题**（`... in due_review and ... not in wrong_ids`），错题另有两路：`:133 _fill(blocking, "路径阻塞错题", "path_blocking", 2)` 与 `:137 _fill(other_wrong, "错题复习", "wrong_retry")`（无配额限制），而 `list_mistakes()`（`core/progress.py:227-241`）只看 `problems_status.status='wrong'`，**完全不看 `next_due_date`**。

实测（P-2，真题目录里的真实 pid）：把一道答错过的题的 `next_due_date` 推到 3650 天后 →
- 到期队列读数 `get_due_reviews` 从 1 → **0**（暂停看起来生效了）；
- 但 `recommend(n=300)` 里该题**仍在**，`reason_code = path_blocking`；`list_mistakes()` 仍返回它。

⇒ 对「答错过的题」，推远**不产生暂停效果**。既有的 `tests/test_recommend_review_state.py:29`（`test_wrong_included_in_recommendations`）与 `:50` 附近其实已经把这一面钉成断言了——不是本班新造的结论。

### E-3 第二处破产：暂停不持久，答一次就蒸发

`core/progress.py:412` 每次 `update_review_state` 都把 `next_due` 重算成 `date.today() + interval`；`core/judge.py:202`（与 `:345` 开放题路径）在**每一次作答**后调它；而练习入口不 gate 到期（`ui/pages/language.py` 对四个复习面关键词 0 命中）。

实测（P-1）：推远到 `2036-09-26` 后再答一次 → `next_due_date` 变回 `2026-10-09`、`interval_days` 6→12。

⇒ 甲案得到的不是「暂停」，是「**到下一次作答为止的静音**」。而且这条静音没有入口、没有事件（`emit_event` 里没有暂停类事件），事后不可审计。

### E-4 第三处破产：`interval_days`／`ease` 与日期解耦留下不一致体

推远只动 `next_due_date`，`interval_days`、`ease`、`review_streak` 一律不动（P-1 S2 实测 `(6, 2.0, 1)` 原样）。后果：`dashboard.py:612` 的 `AVG(interval_days)`、`update_review_state` 的下次间隔、以及 `review_health_stats` 的 `total_pool` 仍把这题当**活跃复习题**统计，只有队列把它摘掉。⇒ 同一题在两套读数里身份相反。

### E-5 现网适用面：真库 `review_state` **0 行**

只读探针（P-0）：`review_state` 行数 **0**、`next_due_date IS NULL` 行数 0、`attempts` 15 行、`problems_status` 14 行（全 `solved`，与 8c05 一致）、`DISTINCT last_result` 空集。

⇒ 现网**没有任何一行可以「推远」**；对未进复习循环的题（`get_due_reviews` 只查有行的，SQL 里 `NULL <= today` 恒不成立），它们本就不出现在到期队列——对这些题「暂停」是无定义操作，除非先 `INSERT` 一行伪造 `(interval=3, ease=2.0, streak=0)`（`core/progress.py:399` 的兜底值，且 `tests/test_review_mastery_bounds.py:175` 已把 `"interval, ease, streak = 3, 2.0, 0"` 钉成源码断言）。伪造行的代价：`data_portability` 导出会把它带走、`import_dry_run.py:226` 的负值／零值体检会把它算进 `review_state` 体检项。

### E-6 「干脆不动」这一支

甲案原话给了个更窄的备选：「或干脆不动（间隔本就只影响推荐位）」。E-1 已否证这半句的前提——不动的话，**到期队列会持续催**，用户的「我不想复这题」在产品面上没有任何表达位，只能靠不点。这支的真实含义是「**不做暂停功能**」，不是「用现有机制等价实现暂停」。请按「做／不做这个功能」来拍，别按「等价」来拍。

### E-7 一种甲案变体（登记供拍，不推荐）：把 `next_due_date` 置 NULL

`next_due_date <= ?` 对 NULL 恒不成立 ⇒ 效果与推远相同但**永久**，且 `ui/pages/mistakes.py:129` 已有 `if r.get("next_due_date")` 的 None 保护、`review_health_stats` 的 `date.fromisoformat` 只作用于被匹配到的行（NULL 不入），不会崩。代价：NULL 与「行由导入产生但没带日期」**不可区分**（`core/data_portability.py:138` 允许 NULL；`tests/test_import_dry_run.py:95` 的夹具里就有 `"next_due_date": None`），语义上把「暂停」和「未排期」混成一格；`import_dry_run.py:226` 的体检也不报它。⇒ 若拍这支，必须先定义「暂停 vs 未排期」怎么区分，否则是把问题藏进 NULL。

---

## 3. 推荐（给人拍的判断题，不是本班结论）

**推荐形态：既不签甲案原话、也不签乙案，先拍「暂停到底要什么语义」，两案都不满足它。**

理由（全部可复算）：
1. 甲案按字面**不等价**（E-2 错题回涌、E-3 答一次蒸发、E-4 双身份、E-5 现网 0 行无从施力），且它的执行形态是「人手 UPDATE 生产库」——本仓 `.gitignore` 覆盖 `data/*.db` 与 `data/backups/`，**git 无还原点**，这属于写库面＝人工闸，不该被写成"零 DB 面"的轻松选项。
2. 甲案的另一支「干脆不动」＝**不做该功能**，那就该按需求登记处理，不该记作"已等价实现"。
3. 乙案代价可枚举（§4），但它是**唯一能给出"持久 + 可审计 + 统计面可解释"暂停语义**的形状；其中「存在哪」还需先拍：`last_result` 加值（撞取值域哨兵、语义污染"上次结果"字段）vs 新列 `suspended`（不污染语义、但要动 3 处硬编码导出／导入列名串）。

**拍板需要人工回答的四个前置问题**（任一未答，两案都不该开工）：
- Q1 暂停是否要**跨作答持久**？（决定 E-3 是否可接受 → 不可接受就基本排除甲案）
- Q2 暂停的题**算不算复习池分母**？（`total_pool` 现不看日期，E-1）
- Q3 暂停是否要**压住错题通道**？（E-2；若要，暂停就必须进 `list_mistakes` 的谓词，那是行为面改动）
- Q4 暂停要不要**用户可见的入口与解除**？（现状零入口；解除方式若靠"再答一次"，等于 Q1 否决甲案的那条）

**若必须二选一（人工只给这两个选项时的最小伤害取向）**：选**乙案的新列支**，且实现期一律**不改** `update_review_state` 的公式串与 `last_result` 三元组（避免 `test_review_mastery_bounds.py:183-186` 与 `:216` 取值域哨兵被动随动），把第三态放进**独立列**，并同批改 3 处硬编码列名串。这只是形状取向，不是本班放行。

---

## 4. 乙案代价清单（逐条给文件／行号，落地前先人工认这笔）

**A. 按设计必红的两件（否证桩，8c05 自己下的桩）**
- `tests/test_review_state_machine_rules.py:204 test_暂停态在本仓不存在将来加了要先红` —— 扫 `core`／`ui` 源码正则 `暂停|paused|suspend|\barchive[_d]?\b`，任何乙案实现都必然命中其中之一 ⇒ **红是设计意图**，重钉＝人工决定"这态在世"。
- `tests/test_review_state_machine_rules.py:216 test_复习态取值域只有pass与fail没有第三态` —— 两处硬断言：`core/progress.py` 的 `"pass" if passed else "fail"` 三元组集合必须恰为 `{("pass","fail")}`（`:222`），且全仓 `last_result ==/!= "x"` 读者集合 ⊆ `{pass, fail}`（`:232`）。**走「`last_result` 加值」的乙案必红**；走「新列」则不红这一条。

**B. 「改公式才红」的第二批**（只有乙案顺手动了间隔／ease／默认值才红）
- `tests/test_review_mastery_bounds.py:175`（`interval, ease, streak = 3, 2.0, 0`）、`:183-186`（`min(int(interval*ease),30)`／`max(1.5,ease-0.1)`／`max(1.5,ease-0.2)`／`interval = 1` 四行逐字）；同文件 8 例现全绿。

**C. 引用面盘点（现值本班实取，非估算）**
- `rg -l review_state tests/` → **19 件**测试文件；`rg -l last_result tests/` → **12 件**。二者是乙案的回归审查面（不等于都会红）。
- 硬编码 `review_state` 列名串 **3 处**：`core/data_portability.py:42-43`（导出 SELECT）、`core/data_portability.py:133-138`（8 占位 INSERT OR REPLACE）、`scripts/import_dry_run.py:55`（COLUMNS 清单）；`scripts/import_dry_run.py:48/:75` 另有主键映射两处。

**D. 迁移形状**（只给形状，未执行）
- `core/progress.py:149-166 _migrate()` 已有 `ALTER TABLE rubric_scores ADD COLUMN ...` 的先例与"列存在才跳过"的幂等写法；乙案新列可复用该模式（新列须带 `DEFAULT`，否则 `data_portability` 导出的旧包在新库导入会缺键）。
- 现网 `review_state` 0 行 ⇒ 迁移**无历史行要回填**（这是乙案在本仓少见的低成本点，但一旦有真实用户数据就不再成立）。

**E. 回滚成本**：SQLite 加列后回退需重建表；`data/` 被 gitignore ⇒ 回滚只能靠 `data/backups/`（该目录同样 gitignore），且**回滚本身是一次新写入**。本班未做任何备份／恢复动作。

---

## 5. 可复算入口（全部只读或走 `LS_PROGRESS_DB` 隔离，零生产库写）

- **P-0 生产库只读体检**：`sqlite3.connect("file:.../data/progress.db?mode=ro", uri=True)` 后先试写两次求 `attempt to write a readonly database`，再取 `review_state` 行数／`next_due_date IS NULL` 行数／`DISTINCT last_result`／`attempts`／`problems_status`／DDL。
- **P-1 甲案等价性主探针**：`D:\code\tmp\qoder-executor-20260927-1820-learn47\jia_eq_probe.py`（S1 作答建行 → S2 推远 → S3 健康度读数 → S4 再答蒸发 → S5 错题回涌 → S6 无行题）。
- **P-2 真题目录版**：`...\jia_eq_probe3.py`（A 到期 vs B 推远，两次 `recommend(n=300)` 的 `reason_code` 对照）。
  ⚠️ 复算坑（本班踩过一次）：探针里用**不存在的假 pid** 时，`recommend` 的 `other_wrong`／`blocking` 都是从 `items = all_problems()`（`core/recommend.py:76`）里筛的，假 pid 会被静默丢掉、误得出「暂停生效」的假结论；必须用目录里的真 pid。另：`all_problems` 定义在 `core/recommend.py:11`，不在 `core/loader.py`。
  两个探针都靠 `os.environ["LS_PROGRESS_DB"]` 把库指到本班 tmp 目录（隔离机制是 `core/progress.py:54-58` 自带的），**绝不能用 `dao=None` 调 judge 侧函数**——`core/judge.py:199` 的 `d = dao or ProgressDAO()` 会开默认路径＝生产库（在册前科）。
- 定向基线读数（现点全绿，非全量）：
  `python -m pytest tests/test_review_state_machine_rules.py tests/test_review_mastery_bounds.py tests/test_recommend_review_state.py -q` → **37 passed / rc=0**（分别 15／8／14）。
  `python -m pytest tests/test_insights_index_closure.py -q` → **3 passed / rc=0**，磁盘 `docs/insights/*.md` **95** 份（写本档前实测，闭合等式成立）。
- 关键词普查复算：`for w in 暂停 pause suspend archive 停用 suspended; do rg -c -F -e "$w" --glob '!tmp/**' core ui scripts tests; done` —— **必须 `-F`**：8c05 的 C 组已记录一次因 `\|` 在双引号里塌成字面量导致的假零命中，本班沿用逐词 `-F` 的写法。

---

## 6. 遗留与登记（不在本班裁决范围内）

1. `暂停` 的**需求侧**证据（用户是否真被到期队列打扰）取不到数：真库 `review_state` 0 行、`attempts` 仅 15 行 ⇒ 无历史复习队列，任何"暂停有多少真实需求"的效果评估在现网**无数据可算**（与 8c05 D 组同结论，本班复核后仍成立）。
2. 8c05 遗留第 3 条（`(1, 1.5, 0)` 通过后间隔原地踏步）与本案**耦合**：若甲案靠"答一次"解除暂停，原地踏步格会让该题**立刻重新到期**，等价性更差；本班未动该口径。
3. `_render_due_reviews` 的 `limit=50` 与「至多」字样在册旧账（`ui/pages/mistakes.py:71-85` 注释自陈）——本班未碰、未重复登记，仅指认存在于册；它影响 E-1 里"到期数"读数的口径解释。
4. 本班**未代登 insights 索引**：本仓有真闭合哨兵 `tests/test_insights_index_closure.py`（现值 A=B=95 闭合），本班连开 3 档后该桩会 missing 3 例——那是主班的账（代登），本班不去消红，也不因此落 partial。
5. 未裁决的内容面冲突（只登记不选边）：`ui/pages/home.py:55`「subprocess 隔离」＋`README.md:64`「带安全与超时边界」与 F-1 实测（生产库写句柄被接受、`core/` 内 rlimit／Job Object／seccomp／chroot 零命中）正面冲突——见 `D:\code\learning-system\docs\insights\l927-11-fs-constraint-adjudication.md` 与 `done/l927-11` 终态行，主班已登记，本班不重复裁。
   - 行号口径（本班实取，供引用者对齐，不改在册写法）：在册两档都写 `home.py:55`，那是 `render_info_notice(` 这一**调用起点行**；被引的那句字面串在 `ui/pages/home.py:57`（`"本系统的代码执行器使用 subprocess 隔离，适合本机单人学习。\n"`）。`README.md:64` 逐字复核为真（「支持多种语言并带安全与超时边界」）。
