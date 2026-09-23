# learn CALIBER_NOTE「阅读合并」前提交叉取证＋learning_events 账本重建量化（l923-24，纯只读）

> 班 `qoder-executor-20260923-0022-learn8`，2026-09-23。**本档零源码改动**（受版件只此一份 md），
> 只出取证＋三选一结论建议，交主班裁决。判据所引命令全部可复算，读数取值时刻 12:58–13:0x。
> 结论一句话：**注记的因果前提在本仓全量 git 历史里不成立**——「阅读合并」规则从未存在，
> 而注记所忧的「任务条数」在报告里根本没有对应指标（`period_attempts` 一直是提交次数）。

## 一、锚点复核（4 条锚点 **3 条漂移**，其中 1 条语义已变）

任务书页头给的锚点是 09-23 01:15 时点数，动手前逐条复跑：

| # | 书页头写的 | 磁盘现值 | 判定 |
|---|---|---|---|
| 1 | `core/report.py:15` CALIBER_NOTE | **`:16`**（`:15` 是上一行注释「文案改动须与 a-47/c-04 的面板同步…」） | 行号漂 +1 |
| 2 | `ui/pages/dashboard.py:217` `st.caption("口径提示：…")` | **`:232` 且已是 `st.caption(CALIBER_NOTE)`**——字面文案**不在此处**；`:228` 只是携带同一句话的注释 | 行号漂 +15 **且语义已变** |
| 3 | `core/report.py:18` `def generate_report(...)` | **`:19`** | 行号漂 +1 |
| 4 | `core/progress.py:542` `FROM learning_events WHERE local_date >= date('now', ?)` | **`:542` 逐字命中** | 未漂移 |

锚点 2 的语义变化不是背景噪声，它**就是本单要取证的对象之一**：`l923-10`（已入账 `84d76ed`，
2026-09-23 09:57）把面板那行硬编码副本改成了引用 `core.report.CALIBER_NOTE` 单源。
所以「同一句话写了两遍」这个历史风险面**已被消灭**，今天只剩一份文案＋一份 HTML/MD 渲染。

## 二、完成标准①：`rg -n "阅读合并"` 全仓命中清单（书页头「应仅两处」**被否证，实为三处**）

复算：`rg -n "阅读合并" --stats .`（本机 rg 15.0.0 可用，照 §十四 口径原式跑）→ **3 matches / 3 files / 717 files searched**：

```
ui\pages\dashboard.py:228:    # a-47/c-04：周报卡常驻口径提示（纯文案；p912-40 遗留——任务条数口径随阅读合并规则变更，跨期直比会失真）
core\report.py:16:CALIBER_NOTE = "口径提示：任务条数口径随阅读合并规则变更，不同期的周报/月报条数不可直接纵向比较。"
docs\insights\weekly-card-note-20260913.md:3:- 改动：`ui/pages/dashboard.py:160-163` 学习报告导出节标题下新增一行常驻 `st.caption` 口径提示：「任务条数口径随阅读合并规则变更，不同期的周报/月报条数不可直接纵向比较。」
```

书页头「仅此两处文案」漏了第三处（那份 09-13 的落地记录档）。**三处全是文案/记录，零规则实现命中**——
这一半前提成立。三条命中的性质分别是：常量定义、引用该常量的注释、历史落地记录，
没有一条是 `if 合并`／`GROUP BY` 之类的行为代码。

### 「零实现」的补强取证（不止靠一个词）

单靠「阅读合并」四字搜不到实现，可能是换了措辞，故补三条独立口径（复算见第六节）：

1. `rg -n "合并|merge" core/ ui/` 的全部命中都属**另一件事**——`core/data_portability.py` 的
   导入合并（`INSERT OR REPLACE` 按业务键覆盖），与「阅读」无关；其余命中是注释。
2. **全量 git 历史**里 `git log --all --oneline -S "merge" -- core/` → **零输出**。
   `core/` 从建立基线到现在没有任何一笔提交增删过 "merge" 字样。
3. `rg -n "lesson_viewed" .`：`lesson_viewed` 只有一个发射点
   `ui/pages/language.py:239 dao.emit_event("lesson_viewed", lang=lang, topic_id=topic.slug)`，
   **带 topic_id、不带 problem_id、不进任何计数**；而 `core/report.py` 对 `learning_events`
   **零引用**（`rg -n "learning_events" core/report.py` 无命中）。
   ⇒ 阅读事件与报告数字之间**没有任何数据通路**，「阅读合并影响任务条数」在结构上不可达。

### 完成标准②：`git log --all --oneline -S "阅读合并"` 溯源

```
84d76ed 09-23 09:57 fix(learning): l923-08..11 四单合并入账（dashboard.py 被三单共改，累计 +55/-16）
a0ee9b9 09-22 01:19 l922-106: 口径注记随导出件走（report_to_markdown/report_to_html 头部脚注＋5 例契约测试）
4c112eb 09-19 08:09 refactor(learning): ①UI 改造族——app 入口与 ui 组件/六页/样式（9/13 批在途件,l918-10 分组一）
7088f7b 09-17 03:17 docs(insights): 20 份 learning 洞察报告成批入库（916p-a3-017 收口；mtime 均 ≤9/16 无在写风险）
```

`git show 4c112eb -- ui/pages/dashboard.py` 的增行原文就是那两行（注释＋`st.caption(硬编码文案)`），
**该提交之前本仓不存在这句话**。书页头「4c112eb UI 改造带入，疑似旧版/kaoyan 家族移植」的猜测
**成立且可加强**：这句话自带三个任务号 `a-47` / `c-04` / `p912-40`，而
`rg -n "p912-40|a-47|c-04" .` 在本仓的命中**全部落在这条注记自己的文案/注释/记录档里**，
本仓任何台账、计划、测试都没有这三个号——它们是**外部家族的号**，随 9/13 在途件一起被搬运进来。
（本单授权只读 cwd，未去他仓对号，故此项到「外部家族」为止，不进一步指认是哪个仓。）

## 三、完成标准③④：learning_events 账本重建 ＋ 口径差量化

库：`data/progress.db`，实测 `pragma journal_mode = delete`（**非 WAL**），`data/` 下无 `-wal`/`-shm` 侧车。
本单所有读用 `file:…?mode=ro&immutable=1`（§二十 python 侧正解），复跑前后 `data/` 目录逐项未变、
`git status --porcelain` 恒 0 行。书页头那条裸 `sqlite3.connect('data/progress.db')` 未照抄执行——
在 delete 日志库上以读写方式打开不是本仓口径要求的只读法；两者读出的数一致（分布见下）。

### 账本规模（书页头 6 类 51 行的分布 **逐类对平，成立**）

| event_type | 行数 |
|---|---|
| `attempt_submitted` | 15 |
| `problem_passed` | 14 |
| `recommendation_shown` | 10 |
| `achievement_unlocked` | 7 |
| `lesson_viewed` | 4 |
| `problem_failed` | 1 |
| **合计** | **51**（类型数 6） |

`local_date` 只覆盖 4 个不同日期，区间 `2026-05-30 … 2026-08-24`。

### 覆盖率 ＆ 口径差（完成标准④）

- `attempts` 表行数 = **15**；账本 `attempt_submitted` = **15** ⇒ 覆盖 **15/15 = 100%**（无漏报、无虚报）。
- **全表**：`COUNT(*) = 15` vs `COUNT(DISTINCT problem_id) = 14` ⇒ **口径差 = 1**。
  唯一被重复提交的题：`python/01_hello_and_vars/01_hello_world` ×2。
- **周窗口**（`attempts_by_day` 的同一条 `COUNT(*)` 口径，按本地日期周分组）：

  | 周 | 提交次数 | 去重题数 | 口径差 | 通过次数 |
  |---|---|---|---|---|
  | 2026-W21 | 15 | 14 | 1 | 14 |

  现库只有 **1 个** 有数据的周窗口，跨周无从比较。

### 关键量化结论：**这个口径差与「阅读合并」无关**

差值 1 **完全来自同一道题被提交两次**（做错了再交一次），不是任何阅读/课程条目被合并的结果。
换句话说：即便把注记设想的「合并规则」删到零，`15 vs 14` 这个差照样存在。

另有一层：**报告今天根本取不到数**。`attempts_by_day` 用
`WHERE ts >= datetime('now', ?)` 比较，而 `attempts.ts` 区间是 `2026-05-30 13:16:51 … 15:03:25`，
距今已 4 个月 ⇒ `days=7`（周报按钮）、`days=30`（月报按钮）、`days=90` 三种窗口下
`period_attempts` **全为 0**。注记所警告的「不同期纵向比较」，在现库状态下一次都发生不了。

## 四、完成标准②的另一半：报告字段里有没有「任务条数」

`core/report.py:19 generate_report` 的返回字典共 12 键
（`period_days / generated_date / streak / total_attempts / period_attempts / period_passed /
grand_solved / grand_wrong / weak_topics / lang_progress / mistakes_count / due_reviews`），
**没有任何一键是「任务条数」**。书页头「报告字段只有 period_attempts/period_passed 等，无任何『任务条数』指标」**成立**。

更要紧的是**渲染层的措辞已经和注记自相矛盾**：

- `core/report.py:42` `period_attempts = sum(r["attempts"] for r in daily)`，而 `r["attempts"]`
  来自 `progress.py:276` 的 `COUNT(*)` ⇒ **它就是提交次数**。
- HTML 卡片 `:166` 标签为 `本周期提交（{period} 天）`；Markdown `:231` 为
  `| 📝 本周期提交 | {…} 次 |`——**两处都写「提交／次」，没有一处写「条」**。
- 真正接近「任务数」的只有 `grand_solved`（`:233` 「累计通过题数」），它来自
  `progress.py:227` `SELECT lang, status, COUNT(*) FROM problems_status GROUP BY lang, status`，
  而 `problems_status` 是**每题一行**的状态表 ⇒ 天然按题去重，与提交次数无关，也无合并可言。

口径稳定性反证：`git log --all -S "COUNT(*) AS n, SUM(passed)" -- core/progress.py` 只命中
**`b14a136 chore: establish local baseline`（仓库第一笔）** 一条 ⇒ 提交次数的算法**自建库以来从未变过**。
注记说的「随…规则变更」在本仓历史里**没有对应的变更事件**。

## 五、完成标准⑤：结论三选一

三个候选出口，逐条按证据打分：

| 出口 | 与证据的契合度 | 代价 |
|---|---|---|
| (a) 保留原措辞 | ✗ 要同时接受三点不实：规则不存在、指标不存在、口径从未变过 | 对用户**主动误导**——它承诺了一个从未发生的口径变化 |
| (b) 改写为「提交次数」口径 | ◐ 方向对（报告确实只给提交次数），但要动 `tests/test_report_markdown_contract.py:136` 钉的位置断言之外的**文案本体** | 中：`CALIBER_NOTE` 已是单源，改一处即同步 md/html/面板三出口；但那 5 例契约测试只钉「位置/前缀/唯一性」，**不钉句内实词**，改文案不会红 |
| (c) 删注记 | ✓ 与「零实现/零变更」最一致，且信息量归零——它没有告诉用户任何会真实影响读数的东西 | 高：要同时动 `tests/test_report_markdown_contract.py` 的 5 例（`:129/:144/:152/:161/:169`），其中 `:169` 的判据①钉的就是 l922-106 完成标准③「面板 caption 保留不删」——删注记等于**撤他人在册完成标准＋摘 5 例测试**，超出执行手授权 |

**给主班的建议：(b)**，且建议理由不是「(b) 比 (a) 真」这么简单，而是——
**(a) 与 (c) 都会留下一处不可复算的账**：(a) 让三条否证继续以官方口径的形态挂在导出件头部；
(c) 要删 5 例在册测试，本夜纪律明令「改计数口径／摘用例一律停手交人工」。
(b) 是唯一既不动判分口径、不删测试、又能让文案与 `:166/:231` 已有措辞自洽的出口，
例如收敛为一句真话：「口径提示：『本周期提交』按提交次数计（同一题多次提交逐次累加），
不随去重题数口径比较。」

**但本单不动手**（书页头「本单不动 dashboard 不动文案，仅取证＋建议」，且 `CALIBER_NOTE`
是用户可见串——按纪律档警示，往用户可见串里加数字会击穿数字计数型解析式，
改写要由主班派单并让 `test_report_markdown_contract.py` 的同句用例先跑一次）。

## 六、复算命令清单（本仓无 rg 缺失问题，全部原式可跑）

```bash
# ① 三处文案命中（书页头「两处」不成立）
rg -n "阅读合并" --stats .
# ② 溯源四笔
git log --format='%h %ad %s' --date=format:'%m-%d %H:%M' -S "阅读合并" --all
# ③ 账本分布（对平 6 类 51 行）——只读法，不造侧车
PYTHONIOENCODING=utf-8 python -c "import sqlite3;c=sqlite3.connect('file:data/progress.db?mode=ro&immutable=1',uri=True);print(c.execute('select event_type,count(*) from learning_events group by event_type').fetchall());print(len(c.execute('select 1 from learning_events').fetchall()))"
# ④ 周窗口 提交次数 vs 去重题数（一行 sql 可复跑）
PYTHONIOENCODING=utf-8 python -c "import sqlite3;c=sqlite3.connect('file:data/progress.db?mode=ro&immutable=1',uri=True);print(c.execute(\"select strftime('%Y-W%W',ts,'localtime'),count(*),count(distinct problem_id) from attempts group by 1\").fetchall())"
# ⑤ 口径从未变更（只命中仓库第一笔）
git log --all --oneline -S "COUNT(*) AS n, SUM(passed)" -- core/progress.py
# ⑥ core/ 全历史无 merge 字样
git log --all --oneline -S "merge" -- core/
# 本单全部读数的一次性出口
PYTHONIOENCODING=utf-8 python tmp/l923-24/probe.py
```

## 七、边界与遗留

- 与 `l923-10` 边界：本单**未动** `dashboard.py` / `report.py`，只取证。
- 与 `l922-106`（注记传播批）边界：那批管「注记去哪」（已随导出件走并落成单源），
  本单管「注记内容本身是否成立」——答案是不成立。
- 遗留 1：**索引欠账**。本档新增于 `docs/insights/` 而按本波指令**未登记**
  `docs/insights/learn-insights-index-20260918.md`，故 `tests/test_insights_index_closure.py` 的
  闭合哨兵（A 磁盘数 == B 表条目数、C 差集为空）会**恰红这一档**。
  收班补列时只需在表内追加一行 `| docs/insights/learn-caliber-note-premise-20260923.md | 20260923 | … | 未入库 | 0 |`
  （**未自行放宽哨兵、未摘用例**）。
- 遗留 2：`a-47 / c-04 / p912-40` 的确切出处需跨仓查证，本单授权止于 cwd。
- 遗留 3：`attempts.ts` 停在 05-30 而 `learning_events.local_date` 到 08-24，
  两表时间面不同步——这使周报/月报长期输出全 0 计数。属**数据面**观察，不在本单范围，
  也**不是**注记所声称的合并规则所致，一并交主班判断是否另立单。
