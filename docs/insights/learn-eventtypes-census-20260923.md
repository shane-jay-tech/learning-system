# learning emit_event 全写点 census：11 类事件 × 12 写点 × 存量对账 × 读侧检索（l923-30，纯只读，2026-09-23）

- 任务：`l923-30`｜执行班：`qoder-executor-20260923-0022-learn11`｜取值时刻：2026-09-23T15:2x+08:00｜HEAD `f0c883c`
- **零源码改动单**：本文是分区唯一产物。事件库存量按**副本法**读取（见第二节），`data/progress.db` 本体未开写、未生成 `-wal`/`-shm` 侧车。
- 与 `l923-33` 边界：那单补 path 事件测试，本单只做全域 census 出档。

## 〇、前提复核：卷宗锚点 4 条全中，但 3 处数值前提被磁盘实况否证

| 卷宗「背景与锚点」 | 复核结论 |
|---|---|
| `core/judge.py:330` `d.emit_event("ai_open_scored", …)` | ✅ 行号与文本逐字对平 |
| `ui/pages/path.py:207` `dao.emit_event("path_started", …)` | ✅ 对平 |
| `core/progress.py:575` 漏斗 `WHERE event_type IN (…3 类…)` | ✅ 对平（另确认 `:595` 是同型第二处） |
| `ui/pages/language.py:209` `dao.emit_event("lesson_viewed", …)` | ⚠️ 文本对平，**行号实为 `:239`**（漂移 +30） |

**否证 1（类型数）**：卷宗标题与「做什么」都写 **10 类**，磁盘实况是 **11 类事件 / 12 个生产调用点**。卷宗自己括号里列的就是 12 个 `文件:行`，且 `core/judge.py:184-185` 一处写点经三元式产出 **2 个类型名**（`problem_passed`／`problem_failed`），故「10」在任何口径下都不成立。本档按实况收窄为 **11 类 × 12 点**。

**否证 2（零行类数）**：卷宗写「4 类零行：`recommendation_completed`／`ai_open_scored`／`path_started`／`path_milestone_completed`」。实测零行是 **5 类**，漏了 **`recommendation_clicked`**（存量 0 行）。这不是小笔误——它直接决定「推荐漏斗现在显示的是 `shown=10 / clicked=0 / completed=0`」这个判读，见第三、四节。

**否证 3（行号漂移面）**：`做什么` 括号内 12 个锚点中 **5 个已漂移**（`achievements.py:146→147`、`dashboard.py:179→191`、`:199→211`、`:357→404`、`:377→426`，另加锚点 4 的 `language.py:209→239`，共 6 处）。根因是 `84d76ed`／`1ff0ae1`／`c3ac33a` 三笔对 `ui/pages/dashboard.py` 与 `ui/pages/language.py` 的在途改动。**本档全部按磁盘现值登记。**

**否证 4（「heatmap/recent 读侧」这条检索面）**：卷宗要求「对每类型 rg 读侧（progress.py:575/:595 漏斗、**heatmap/recent 读侧**逐一检索式列出）」。实况是 `core/progress.py:538 events_by_date()`（唯一按 `event_type` 分组的日期聚合读侧）**在生产码零调用方**，唯一命中是 `tests/test_core_edges.py:370`；而 `ui/pages/dashboard.py:491 _render_heatmap()` 的热力图 SQL（`:495-499`）**读的是 `attempts` 表、不碰 `learning_events`**。⇒ 「heatmap 读侧」这个栏位在现仓不存在，本档改为登记该缺口（第五节 D-1）。

**未坐实 1（写点年代）**：卷宗要「零行类每类给最近可能触发条件推断」。年代证据取不到：`git log -S"<事件名>"` 对 9 个具名写点**全部**返回同一笔 `b14a136`（`2026-07-14 12:36:10 +0800 chore: establish local baseline`，仓库首笔），即历史被压平 ⇒ **无法据此判定任一写点是否晚于某次数据写入**。下文的条件推断一律以「代码门控 + 存量数据自身时序」为据，不假托 git 年代。

## 一、写点 census（12 点 / 11 类；`rg -n "emit_event\(" core ui scripts` 命中 13 行 = 12 调用点 + 1 处 `def`）

| # | 文件:行 | 事件类型 | payload 键 | 触发门控 | 存量行数 |
|---|---|---|---|---|---|
| 1 | `core/judge.py:154` | `recommendation_completed` | recommendation_id, reason_code, surface, rank | 三元式上游 `judge.py:186-187`：仅 `passed=True` 时进 `_check_recommendation_completed`，且**必须**先在同 `(lang, problem_id)` 上命中一条 `recommendation_shown`（`:145-150`） | **0** |
| 2 | `core/judge.py:182` | `attempt_submitted` | passed | `_record_attempt`；`pid` 为空或 `AI_VARIANT::` 前缀整块 return（`:171-176`） | 15 |
| 3 | `core/judge.py:185` | `problem_passed` \| `problem_failed`（由 `:184` 三元式二选一） | 无 payload | 同上 | 14 + 1 |
| 4 | `core/judge.py:330` | `ai_open_scored` | score, passed | 开放题 `_judge_open`，硬门控 `res.get("llm_ok")` 为真 **且** pid 非 `AI_VARIANT::`（`judge.py:318`） | **0** |
| 5 | `core/achievements.py:147` | `achievement_unlocked` | achievement_id | `_mark_earned` 后逐个补发；`except` 吞错（`:148-149`，成就发放不受影响） | 7 |
| 6 | `ui/pages/path.py:207` | `path_started` | 无（只 `path_id` 列） | 路径详情页每次渲染（调用方 `:102`）＋ meta 键 `path_started:<path_id>` 幂等去重 | **0** |
| 7 | `ui/pages/path.py:216` | `path_milestone_completed` | 无（`path_id`+`milestone_id` 列） | `milestone_progress()["pct"] >= 1.0`（`:114/:118`）＋ meta 键 `milestone_done:<path>:<ms>` 去重 | **0** |
| 8 | `ui/pages/dashboard.py:191` | `recommendation_shown` | reason_code, surface=`dashboard`, rank, recommendation_id | 今日推荐区 `for` 循环 + 会话态 `_rec_shown_ids` 去重；`try` 包整个循环（`:181-195`，写序在册缺陷见 `learn-shown-writeorder-design-20260923.md`） | 10（全部 `surface=dashboard`） |
| 9 | `ui/pages/dashboard.py:211` | `recommendation_clicked` | recommendation_id, reason_code, surface=`dashboard`, rank | `st.button("去做 →", key=reco_*)` 按下（`:207`） | **0** |
| 10 | `ui/pages/dashboard.py:404` | `recommendation_shown` | reason_code=`cross_path`, surface=`cross_path`, rank, recommendation_id | 跨路径推荐块 + 会话态去重，per-item `try`（`:398-408`） | 0 行（该写点自身零命中，见 `surface` 分布） |
| 11 | `ui/pages/dashboard.py:426` | `recommendation_clicked` | 同上，surface=`cross_path` | `st.button("去做 →", key=cross_*)`（`:422`） | **0** |
| 12 | `ui/pages/language.py:239` | `lesson_viewed` | 无（只 `topic_id` 列） | 语言主页切到具体 topic 时 | 4 |

**点级零行（比类型级更细一层）**：`recommendation_shown` 有两个写点（#8 dashboard、#10 cross_path），存量 10 行的 `surface` 全为 `dashboard` ⇒ **`dashboard.py:404` 这个写点从未产出过一行**。同类：`recommendation_clicked` 的两个写点均零。

> **口径防漂移**：判据①不用「全仓裸 `rg -n emit_event` 命中数」——该数会被**本档自己**的引用推着漂。建档前分段是 `core 6 + ui 7 + scripts 0 + tests 32 + docs 6 = 51`，本档落盘后 `docs` 段变 14（本档自身贡献 8 行）⇒ 同一式现读 **59**。census 一律用 `core ui scripts` 显式路径 ＋ `emit_event\(` 这条**闭口径**（恒 13 行，与本档内容无关）。

**旁路写者（不走 `emit_event` 的入库口，census 必须计入）**：
- `scripts/backfill_events.py:85` 裸 `INSERT INTO learning_events`，只回灌 `attempt_submitted`/`problem_passed`/`problem_failed` 三类（`:48`），并用 `event_count()` 与既有事件行做幂等（`:36-58`）。
- `core/data_portability.py:107-111` 导入路径整表回写 `learning_events`（列名白名单 `:109`）。
⇒ 「11 类」是**具名写点口径**；这三类事件另有第二条来源，判定「停写」前必须一并看。

## 二、存量对账（总数 51，与卷宗给的 6 类分布逐位相符）

> **取数改道留痕**：本机 Git Bash 无 `sqlite3` CLI（`command -v sqlite3` 返回非零），故完成标准②的「sqlite3 一行 group by」按**同口径**改道 python 标准库 `sqlite3`；且**不直开主库**——纪律档 §十三 已实测 `mode=ro` 仍会造 `-shm`/`-wal` 侧车，本单走「`shutil.copy2` 副本 ＋ `file:...?mode=ro&immutable=1`」。落盘后主库 sha256 前 8 位与 mtime **逐位未动**（见 result 证据节）。

```
event_type              n
attempt_submitted      15
problem_passed         14
recommendation_shown   10
achievement_unlocked    7
lesson_viewed           4
problem_failed          1
                       --
                       51   = COUNT(*) 全表
```

辅助读数（同一次副本连接内取得）：
- `MIN(created_at)=2026-07-05 05:23:57`、`MAX(created_at)=2026-08-24 04:09:55`；`created_at IS NULL` 行数 **0**（列有 `DEFAULT CURRENT_TIMESTAMP`，`core/progress.py:99`）。
- 按 `local_date`：`attempt_submitted`/`problem_passed`/`problem_failed` 全在 **2026-05-30**（`attempts` 表也仅此一天，15 条，`MAX(ts)=2026-05-30 15:03:25`）；`achievement_unlocked` 2026-07-15；`recommendation_shown` 2026-07-15（5）＋2026-08-24（5）；`lesson_viewed` 2026-08-14／2026-08-24。
- `meta` 表现存 5 个键：`achievements_earned`、`ai_pulse_monthly`、`ai_pulse_quarterly`、`all_mistakes_cleared`、`security_notice_seen`——**不含任何 `path_started:*`／`milestone_done:*`**。
- `recommendation_shown` 覆盖 5 个不同 `(lang, problem_id)`；这 5 题与 `attempt_submitted` 的题集**交集为 0**。
- 同库旁表行数：`attempts` 15／`problems_status` 14／`review_state` **0**／`rubric_scores` **0**。

**「是不是被 `prune_old_data.py` 删掉的」这条替代解释，已排除**：`scripts/prune_old_data.py:55` 只按 `created_at < datetime('now', ?)` 整批 `DELETE`，无类型选择性；若曾以任何 ≤116 天的窗口跑过，**最旧的 2026-05-30 那 30 行必然先没了**，而它们在。⇒ 零行 5 类是「未触发」，不是「触发后被清」。

## 三、零行 5 类逐类取证（触发条件推断 + 读侧检索式 + 命中/零命中）

| 类型 | 最近可能触发条件（推断，含依据） | 类型级读侧检索式 | 命中 |
|---|---|---|---|
| `recommendation_clicked` | 需在推荐卡上按「去做 →」（`dashboard.py:207` 或 `:422`）；按下即无条件 emit（`imp` 缺键也只写空串，不会跳过）⇒ **零行＝零次点击**，不是代码吞了。`recommendation_shown` 有 10 行证明页面确实渲染过 | `rg -n "recommendation_clicked" core ui scripts` | 命中 6 行：`progress.py:575/581/595/606`（漏斗读）＋`dashboard.py:211/426`（写） |
| `recommendation_completed` | 三门串联：①题目被推荐过（有 `recommendation_shown` 同 `(lang,pid)` 行）②之后**作答且 passed**③`_check_recommendation_completed` 不抛。存量里 ①的 5 题与 ②的题集**交集 0**，且 `attempts` 全停在 2026-05-30、首条推荐在 2026-07-15 ⇒ 这份快照内**结构上不可能**产生该事件，与写点是否有 bug 无关 | 同上式 | 命中 6 行：`progress.py:575/582/595/608`＋`judge.py:154`＋`judge.py:187`（调用点） |
| `ai_open_scored` | 唯一硬门是 `res.get("llm_ok")`（`judge.py:318`）⇒ 需 LLM 真通且做过**开放题**。同库 `rubric_scores` 表 **0 行**（第二节读数）与之相容，但只是**旁证非硬证**：`judge.py:324` 的 `if dimensions and attempt_id` 只闸 rubric 那条写入，`ai_open_scored` 的 emit 不以 dimensions 为条件，故「LLM 打分跑过但无维度」这一路径仍会产生事件而无 rubric 行 | 同上式 | **零命中**（`core/ui/scripts` 全无第二处引用，仅 `judge.py:330` 自身） |
| `path_started` | 需进入某条已存在路径的详情页（`path.py:102` 在 `path` 不是「路径不存在」分支时才执行）。`meta` 无 `path_started:*` ⇒ 与「emit 在 `set_meta` 之前」（`path.py:205-208` 顺序：查 meta → emit → 写 meta）互证为**从未触发**，若曾触发必有 meta 键 | 同上式 | **零命中**（除 `path.py:207` 自身） |
| `path_milestone_completed` | 需某里程碑 `pct>=1.0`（`path.py:114/118`）⇒ 该里程碑题目全部通过。存量中除 2026-05-30 那批作答外无更晚作答，且路径页从未进（上一条已证）⇒ 双重不满足 | 同上式 | **零命中**（除 `path.py:216` 自身） |

## 四、读侧对账总表（「写而不读」判定按**类型级具名读侧**，泛化读侧另列）

生产码里读 `learning_events` 的口子只有 5 处：`progress.py:540`（`events_by_date`，按类型分组）、`:552-560`（`event_count`，可选类型）、`:573-583`（漏斗）、`:592-610`（漏斗×reason）、`judge.py:145-150`（`recommendation_shown` 归因回查）。

| 事件类型 | 类型级具名读侧 | 泛化读侧（不分类型） | 判定 |
|---|---|---|---|
| `recommendation_shown` | `progress.py:575/595/604`、`judge.py:147` | `event_count()`（`dashboard.py:290` 导出缓存键、`backfill_events.py:36/92`） | **有读** |
| `recommendation_clicked` | `progress.py:575/595/606` | 同上 | 有读但**恒 0** |
| `recommendation_completed` | `progress.py:575/595/608` | 同上 | 有读但**恒 0** |
| `attempt_submitted` | 仅 `scripts/backfill_events.py:48/67/69`（幂等自证，不是分析读侧） | 同上 | **写而不读**（分析面） |
| `problem_passed` | 同上 `backfill_events.py:48/74` | 同上 | **写而不读**（分析面） |
| `problem_failed` | 同上 `backfill_events.py:48/74` | 同上 | **写而不读**（分析面） |
| `achievement_unlocked` | **零**（成就真源是 `meta['achievements_earned']`，`achievements.py:231/250`，事件表只是平行副本） | 同上 | **写而不读** |
| `lesson_viewed` | **零** | 同上 | **写而不读** |
| `ai_open_scored` | **零**（评分读侧走 `rubric_scores` 表） | 同上 | **写而不读** |
| `path_started` | **零** | 同上 | **写而不读** |
| `path_milestone_completed` | **零**（里程碑进度真源是 `dao.milestone_progress()`，`path.py:112`） | 同上 | **写而不读** |

⇒ **8 类写而不读 / 3 类有读（其中 2 类恒 0）/ 5 类零行**（三组有交叠：零行的 5 类里 3 类恰是「有读侧却无数据」＝`clicked`/`completed` 有读，`ai_open_scored`/`path_started`/`path_milestone_completed` 连读侧都没有）。

## 五、处置建议（**仅建议，本单一处未改**；标注是否需要越红线域裁决）

| # | 对象 | 建议 | 归属 |
|---|---|---|---|
| D-1 | `progress.py:538 events_by_date()` 生产零调用方，而热力图直读 `attempts`（`dashboard.py:495-499`） | **补读侧优先**：要么把它接进热力图（事件口径），要么明确「事件表不参与热力图」并考虑下线该函数。现状是**函数活着、类型维度无人看**——静默腐烂风险面 | 普通工程裁决 |
| D-2 | `achievement_unlocked`：meta 与事件表**两套真源** | **留观测 ＋ 补一条对账**（`meta` 计数 vs `event_count('achievement_unlocked')`），不合并真源、不停写 | 普通工程裁决 |
| D-3 | `lesson_viewed`：写侧活、读侧零、存量 4 行 | **候选停写**（唯一可无损停的类）。但停写属数据面行为改动 ⇒ 交人工，不在执行手授权内 | **需裁决** |
| D-4 | `path_started` / `path_milestone_completed`：读侧零（进度真源在 `milestone_progress()`） | 同 D-3 形态，但**涉学习路径域＝红线**，本单只登记缺口，不建议也不实施任何停写/补读改动 | **需裁决（红线域）** |
| D-5 | `ai_open_scored`：读侧零 | **留观测**（它是 LLM 用量的唯一审计流水；`rubric_scores` 不含 llm_ok/耗时语义）。停写会丢审计面，不建议 | 普通工程裁决 |
| D-6 | 推荐漏斗 `clicked=0 / completed=0` 恒显示 | **不要为了让它非零去改判据或放宽在册 xfail**。`completed` 的零已由数据时序解释（第三节）；`clicked` 的零是真实用户行为。另：`clicked > shown` 的产生机制已在 `learn-shown-writeorder-design-20260923.md`／`test_dashboard_event_failures.py:157` 在册（本单不重复立项） | 在册，只引不修 |
| D-7 | `dashboard.py:404`（cross_path shown）写点零行 | 补一条**跨路径曝光**数据面验证（需真实使用或 fixture），非缺陷 | 观察 |

## 六、遗留问题

1. 索引件 `docs/insights/learn-insights-index-20260918.md` 本单**未改**（多班同改必互相覆盖，主班单点写）⇒ 本档落盘后 **A=68、B=67**，`tests/test_insights_index_closure.py` 实测 **2 failed / 1 passed**：`test_闭合等式_A等于B_且C为空_且无重复` 红在 `:101`（缺项＝本档一个路径，extra/dupes 均空），`test_新档漏登记必红_改名必红_有牙自检` 红在 `:118`（它的「现值本身闭合」前置断言被本档命中）。**待主班随批代登**；不放宽、不摘例。
2. `rubric_scores` 与 `review_state` **同为 0 行**而 `attempts` 有 15 条（`_record_attempt` 里 `update_review_state` 与 `record_attempt_and_status` 同批调用，`judge.py:180-181`）。这属**学习数据正确性**域、不在本 census 判定链上，本单**只登记不核**，交该域负责人。
3. 写点年代**未坐实**（否证 1 一节已说明原因：历史压平在 `b14a136`）。
4. `event_count(event_type=…)` 带参分支（`progress.py:554-557`）生产码零调用方（只有 `tests/test_core_edges.py:369` 用），与 D-1 同族，本单只登记。
5. `tmp/l923-30/progress.db`（114,688 B 副本）留在 gitignore 的 `tmp/` 下未删：它会计入 `core/report.py count_source_lines()`（该函数 `_SKIP_DIRS` 不含 `tmp/`，属在册未修缺陷），对全仓规模口径请一律用 `git ls-files`。

## 附、复算命令（本机全部实跑，读数见正文）

```bash
# 写点 census（13 行 = 12 调用点 + 1 def）
$ rg -n "emit_event\(" core ui scripts
# 类型级读侧（把 <T> 换成 11 个事件名之一）
$ rg -n "\"<T>\"|'<T>'" core ui scripts
# 泛化读侧与热力图真相
$ rg -n "events_by_date|event_count\(" core ui scripts
$ rg -n -A14 "CREATE TABLE IF NOT EXISTS learning_events" core/progress.py
# 副本法（不碰主库）
$ python -c "import shutil;shutil.copy2('data/progress.db','tmp/l923-30/progress.db')"
$ python -c "import sqlite3;c=sqlite3.connect('file:tmp/l923-30/progress.db?mode=ro&immutable=1',uri=True);print(c.execute('SELECT event_type,COUNT(*) FROM learning_events GROUP BY event_type ORDER BY 2 DESC').fetchall());print(c.execute('SELECT COUNT(*) FROM learning_events').fetchone())"
# 替代解释排除：meta 键与 prune 语义
$ python -c "import sqlite3;c=sqlite3.connect('file:tmp/l923-30/progress.db?mode=ro&immutable=1',uri=True);print(c.execute('SELECT key FROM meta ORDER BY key').fetchall())"
$ rg -n "DELETE FROM learning_events|WHERE event_type IN" scripts/prune_old_data.py scripts/backfill_events.py
# 写点年代（全落同一首笔，故不可用）
$ git log --format='%ai %h %s' --reverse -S'"path_started"' -- ui/pages/path.py | head -1
```
