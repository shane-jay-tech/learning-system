# learning `ai_open_scored` 零行事件处置三案：门控链路图＋消费面/存量现值＋推荐案判据（l924-29，只出稿 · 零生产码改动）

> **卷宗**：`zcode-bridge/inbox/l924-29.task.md`（现址 `zcode-bridge/done/`）。产出面＝本档一份；`core/judge.py` 零 diff（自证见 §六）。
> 取数时刻 2026-09-25T04:3x+08:00、learning HEAD `cc7e4d5`、工作树 `git status --porcelain` 只列本单产物。
> 🔴 **本档是三案裁决材料，一律"建议稿、未选案"**：A／A′／B／C 的取舍与阈值全部交人工，执行手不代拍板；本单零生产码改动、零写库。
> 探针在 gitignore 的 `tmp/qoder-executor-20260925-0420-learn32/`（`git check-ignore -v` → `.gitignore:19:/tmp/`）：`probe_events.py`（**严格只读**：真库 `mode=ro`＋`PRAGMA query_only=ON`，可比对快照走 `sqlite3` 的 `backup()` 单文件并**开两次比对**，照纪律档 §十二；copy2 三件套已作废不用）。

## 〇、锚点与前提复核（卷宗每条前提都实测）

| 卷宗前提 | 实测 | 命令 | 判定 |
|---|---|---|---|
| `core/judge.py:318` 为 `if res.get("llm_ok") and not str(pdict.get("id") or "").startswith("AI_VARIANT::"):` | 逐字一致（行号 318） | `$ rg -n "AI_VARIANT::\"\)" core/judge.py` → `173:`／`318:` | ✅ 零漂移（⚠ 该 `startswith` 在同文件有 **2 处**：`:173` 是 run 题的 `_record_attempt` 守卫，别混） |
| `core/judge.py:330` 为 `d.emit_event("ai_open_scored", lang=lang, problem_id=pid,` | 逐字一致（行号 330） | `$ rg -n "emit_event\(\"ai_open_scored\"" core/judge.py` → `330` | ✅ |
| census `learn-eventtypes-census-20260923.md:33` 那一行 | 行号与整行文本逐字对平（含"存量 **0**"） | `$ rg -n "ai_open_scored" docs/insights/learn-eventtypes-census-20260923.md` → :11/:18/:33/:83/:101/:105/:115 | ✅ |
| 存量 0 行（census 的结论） | 真库当下值 **0**，且 `backup()` 快照两次独立连接复算同为 0 | `probe_events.py` 输出 `"ai_open_scored": 0`（三次读取一致） | ✅ 复算成立（现值见 §三） |
| 「`ai_judged` 族字段」（案 B 的落点名） | 🔴 **全仓零命中**——`ai_judged` 这个事件/字段名在盘上不存在 | `$ rg -c "ai_judged" -g '!tmp/**' .` → 无输出，`rg_rc=1` | ❌ **否证**：B 案必须先选一个真实存在的落点，见 §四 B 行 |
| census 的「写而不读」标签 | ⚠ **不精确**：该 type 无点名句柄，但有 **3 处间接读面**（`event_count()` 总数口径） | `$ rg -n "event_count\(" core/ ui/ scripts/ tests/` | 见 §二末，直接影响 C 案"零影响"论断 |

## 一、门控链路图（`:318` 为轴，八道门）

```
用户点「提交」
  └─ core/judge.py:266  judge(lang, problem, code, dao)
       ├─ G0 :269  `if not (code or "").strip():`  → 空答案**早退**：不落 attempt、不 emit、不 logger、不计数
       ├─ G1 :279  `if pdict.get("judge_mode") == "ai_open":`   精确等值匹配 → 才进 _judge_open
       │            （content 侧取值实测只有 run/ai_open 两种，非规范值 0 处 ⇒ 暂无静默漏道，见 §三 E3）
       └─ G1' 否则走 run 题路：_record_attempt(:168) → 必 emit attempt_submitted + problem_passed/failed
                                          ⇩ 开放题路
     core/judge.py:307  _judge_open(lang, pdict, answer, dao)
       ├─ :309  res = core/ai_review.py:430 grade_open_answer(...)   # 契约「绝不抛异常」
       │        ├─ :435 缓存命中（_cached_open_result，只缓存 llm_ok=True 的结果 :96）
       │        │        ⇒ **返回 llm_ok=True 但零 LLM 调用**（G2b，见下）
       │        ├─ :452 text, responding_model = _call_chain(prompt, AI_OPEN_SYSTEM, _QUALITY_CHAIN)
       │        │        └─ ai_review.py:535/538/542 超时/失败/non-zero → logger.warning（**全仓无 FileHandler/basicConfig** ⇒ 不进任何持久文件，控制台一关就没）
       │        ├─ :453-458 `if not text:` → **llm_ok=False**（网络/服务异常），无 log、无计数
       │        └─ :510-517 `except Exception` → :511 logger.error + **llm_ok=False**
       ├─ G2 :318  `res.get("llm_ok")`                     假 → 整块跳过（attempt/review_state/rubric/event **全不写**）
       ├─ G3 :318  `not pid.startswith("AI_VARIANT::")`     假 → 同上整块跳过（设计意图：伪 ID 防污染，与 :173 同族）
       └─ 门内 :319-336（own_dao 生命周期 + try/except/finally）
            :323 record_attempt_and_status(...)   ┐
            :324 update_review_state(...)         │ 任一条抛异常 → :333 logger.warning 后
            :326 if dimensions and attempt_id:    │ **整块中止** ⇒ G5：event 也写不出来，且 rc 正常返回给用户
            :330-331 emit_event("ai_open_scored") ┘   （score/passed 进 payload）
```

**这条链给出的三个硬事实**（案 A premise 的证据基础，也是对"静默无痕"的定量收窄）：

1. `llm_ok=False` 期间**不是"只有 event 无痕"，而是整条落库链无痕**——`attempts`／`problems_status`／`review_state`／`rubric_scores`／`learning_events` 一张都不写（G2 在 :318 就把 :319-336 全包了）。⇒ 卷宗案 A 说的"基础设施故障与没人做开放题在遥测上不可区分"**成立且比卷宗写的更强**：连"有人做过开放题"这个分母都拿不到。
2. 反过来 **`llm_ok=True` 也不一定真调了 LLM**（G2b 缓存命中直接复用上次结果）⇒ 案 C 引用的"它是 LLM 用量的唯一审计流水"（census D-5）**语义不成立**：它既漏计（真调用失败的那一次不留行）又重计（同一答案重复提交每次都留行），是"评分完成事件"而非"用量流水"。
3. 全仓**没有日志落盘面**：`rg -n "basicConfig|FileHandler|log_file|\.log" app.py ui/ core/ scripts/` → 0 命中 ⇒ G2/G3/G5 的失败只活在 `logger` 的 stderr 里，事后无从复原。

## 二、消费面证据（`ai_open_scored` 全仓命中清单，判据 ①）

```
$ rg -n "ai_open_scored" --glob '!tmp/**' .
core/judge.py:330                                    ← 唯一写侧
docs/system-report-v0.6.3.md:110                     ← 事件表（历史快照档）
docs/system-report-v0.6.4.md:110                     ← 事件表（历史快照档）
docs/insights/learn-eventtypes-census-20260923.md    :11/:18/:33/:83/:101/:105/:115  ← 普查档自身
```

| 面 | 读数 | 命令 |
|---|---|---|
| 写侧 | **1 处**（`core/judge.py:330`）；同文件 emit 共 4 处（`:154/:182/:185/:330`） | `$ rg -n "emit_event\(" core/ ui/ scripts/`（全仓 13 处、**9 个类型字面量＋1 个动态 `event_type`**，`attempt_submitted` 与 `problem_passed/failed` 同路写出） |
| 点名读侧 | **0 处**（`core/ui/scripts` 无第二处引用） | 同上（`ai_open_scored` 只出现在 `:330`） |
| **间接读侧** | **3 处**：`ui/pages/dashboard.py:299-300` 的导出缓存键 `_exp_key = "_".join(str(n) for n in (dao.total_attempts(), dao.event_count(), …))`（:305/:307 与 `session_state["_export_cache_key"]` 比对，键一变即重算导出快照）；另 `scripts/backfill_events.py:36/92` 用 `event_count()` 做幂等基线。<br>⚠ `tests/test_export_cache_invalidation.py:5` 的自述把这个键写在 `dashboard.py:213`，**实测已在 :299**（在册桩自身行号漂移，与 §八 末行同形态） | `$ rg -n "event_count\(" core/ ui/ scripts/ tests/` |
| 泛聚合读侧 | `core/progress.py:538 events_by_date()`（按 `local_date × event_type` 分组）会把它算进去，但**全仓无 UI 调用者**（只有 `tests/test_core_edges.py:370` 在用）⇒ 这条是"有实现无消费" | `$ rg -n "events_by_date" core/ ui/ scripts/ tests/` |
| 迁移/清理工具 | `core/data_portability.py:46/65/107` 按**整表**搬运（不按 type）；`scripts/prune_old_data.py:43/55` 按 `created_at` 整批 DELETE（**无类型选择性**）⇒ 该 type 的存废对导入导出/清理**零改动** | `$ rg -n "learning_events" core/ scripts/` |
| 测试面 | **0 处**：没有任何用例点名 `ai_open_scored`（含 `tests/test_dashboard.py`、`tests/test_scripts.py`）⇒ 下线它**不会当场撞红**，但也**没有任何桩会拦住误删** | `$ rg -n "ai_open_scored" tests/` → 无输出 |

⇒ 对卷宗案 B/C 的直接影响：**"零点名"≠"零影响"**。C 案的准确说法是"当前零行 ⇒ 间接读面（总数口径/缓存键）**当下无差异**，但保留 type 会给未来的 `event_count()` 与导出缓存键增加扰动源"。

## 三、存量与流量面现值（全部只读取证）

**E1 真库当下值 + `backup()` 单文件快照两次比对**（纪律 §十二 配方；本仓库为 WAL，`journal_mode=wal`）

```
$ PYTHONIOENCODING=utf-8 python tmp/qoder-executor-20260925-0420-learn32/probe_events.py
== profile[real-ro#1]:  events_total=51  ai_open_scored=0  attempts_total=15  attempts_last30=0
                        rubric_scores=0  review_state=0（表内 0 行）  events_last30_by_type=[]
   events_by_type: attempt_submitted 15 / problem_passed 14 / recommendation_shown 10 /
                   achievement_unlocked 7 / lesson_viewed 4 / problem_failed 1     ← 共 6 类
   events 时间轴: local_date 2026-05-30 → 2026-08-24；created_at 2026-07-05 05:23:57 → 2026-08-24 04:09:55
== 快照 sha256 与两次独立只读连接比对：12/12 字段"一致"（含 events_total / ai_open_scored / by_type）
== 快照 vs 真库当下值：events_total 51 vs 51 ; ai_open_scored 0 vs 0
```

- 11 个 emit 类型里**盘上只有 6 类有行** ⇒ 5 类零行，`ai_open_scored` 是其中之一（与 census「5 类零行」逐字对平）。
- 最后一条事件距本单取数已 **32 天**（`created_at` 最大 2026-08-24，今天 2026-09-25）⇒ **近 30 日整库零事件**。

**E2 零行不是"被清理"所致**（替代解释排除，三条独立证据）

```
$ 仓内只有 1 个库：find . -name "*.db" -not -path "./tmp/*" -not -path "./.venv/*" → ./data/progress.db
$ PYTHONIOENCODING=utf-8 python -c "…两份历史备份各自 backup() 出 progress.db 后 SELECT…"
0815备份 events=43 ai_open_scored=0 range=('2026-05-30','2026-08-14') attempts=15
0904备份 events=51 ai_open_scored=0 range=('2026-05-30','2026-08-24') attempts=15
$ rg -n "prune_old_data" -g "*.bat" -g "*.ps1" -g "*.txt" .   → 无输出（无排程；只能手跑）
```
⇒ 2026-08-15 / 09-04 两份 `data/backups/progress-*.zip` 里**同样是 0 行、同样 6 类**；`prune_old_data.py` 默认 `--days 365`（`:36/:88`）且 `DELETE` 无类型选择性（`:55`），最早那批 2026-05-30 的行仍在 ⇒ **零行＝未触发**，不是触发后被清。（census 第四节已用"最旧 30 行必然先没了"排除过同一替代解释，本单从备份侧再钉一遍。）

**E3 流量上限（content 侧，双轨）**

```
$ PYTHONIOENCODING=utf-8 python -c "load_language × 5 语言，按 Problem.judge_mode 计数"
python 8 / sql 0 / cpp 0 / r 14 / agent_dev 48  → 开放题合计 70 道（占 403 题的 17.4%）
$ python -c "直扫 content/**/*.yaml 的 judge_mode 行"   # 第二轨，不经 loader
Counter({'run': 70, 'ai_open': 66, '"ai_open"': 4})  → ai_open 合计 70 ✅ 与 loader 轨逐位对平
非 {ai_open, run} 取值：0 处
$ PYTHONIOENCODING=utf-8 python -c "attempts 的 14 个去重 problem_id ∩ 70 道开放题"
→ 交集 0（problems_status 的 14 个去重题号 ∩ 开放题 也 = 0）
```
⇒ **上限存在且不小**（70/403 题、agent_dev 一门就 48 道），但**历史痕迹为 0**：这套库里"从来没有一道开放题留下过 attempt 行"。所以"零行"有两种可能——① 用户真没做（无流量），② 做过但每次 `llm_ok=False`（G2 全拦）——**当前遥测无法区分**（§一 硬事实 1）。这正是案 A 的核心 premise，也是**不能在今天判 C（下线）的理由**。

## 四、三案对照表（判据 ②：每案含「动哪个文件／几行／回滚方式」）

行数为**估算**（锚在唯一文本而非行号，纪律 §十.4），落地时会因上下文增删 ±2 行；标注"跨文件数"以 `rg` 实测点名为准。

| 案 | 内容 | 动哪个文件 | 几行（估） | 回滚方式 | 主要风险 / 证据依赖 |
|---|---|---|---|---|---|
| **A 保留等流量**（零改动） | 维持 `:318` 门与 `:330` emit 原样，等真实开放题流量出现 | **无** | **0 行**（只出本档） | 无需回滚（本档可撤销） | 静默期不可区分（§一 事实 1）；census 给的"LLM 用量审计"留值理由**已被 §一 事实 2 否证** ⇒ 纯 A 是"零成本但零信息"，等到的可能只是缓存重计 |
| **A′ 保留＋补失败侧计数**（推荐主案） | 在 `:318` 判假时补写一条"开放题提交但被门挡住"的事件，payload 带 `reason ∈ {llm_unavailable, variant, write_failed}` | `core/judge.py`（只动 `_judge_open`：把 `:318` 的复合条件拆成 llm_ok / variant 两道分别判，各 emit） | **约 +8～14 行、1 个文件**；`core/progress.py` 0 行（`emit_event` 已泛型，新 type 无需 schema 迁移） | `git revert` 单提交即可；**无数据迁移**（新 type 一旦有行需一并说明保留策略，但 `prune`/`data_portability` 均按整表运作，不改代码） | 拆分 `:318` 时**极易误放** attempt 落库（现状 G2 是全拦）⇒ 必须配"门为假时 attempts 仍 0 增量"的负例桩（属新建测试件，本单不做）；成本=每次失败多 1 行 `learning_events`（append-only，靠 `prune_old_data` 兜） |
| **B 降频采样／降级为族字段** | 卷宗原名"`ai_judged` 族字段"**全仓不存在**（§〇 否证）⇒ 只能选真实落点：<br>**B1** 并入 `attempts` 的新列/新 payload 键<br>**B2** 并入 `rubric_scores`（该表 `:326` 的 `if dimensions and attempt_id:` 之下已有 `prompt_version`/`model` 列，天然同族）<br>**B3** 采样：`:330` 外包一个按 `pid`/日期的丢弃条件 | B1：`core/progress.py`（`CREATE TABLE attempts` 列定义＋`_migrate` 分支 `:109-113` 同族）＋`core/judge.py`（`record_attempt_and_status` 调用 `:323` 与 `core/progress.py` 内该方法签名）<br>B2：`core/judge.py:326` 放宽为"无维度也写一行哨兵"＋`record_rubric_scores` 签名<br>B3：`core/judge.py:330` 外包 1 个条件 | B1 **约 6～10 行、2 文件＋1 次表迁移**（⚠ 本仓最高风险形态：动 schema、`data_portability` 的导出列清单 `:46-47` 需同步，否则**导入导出丢字段**）<br>B2 约 3～6 行、1 文件<br>B3 约 2～4 行、1 文件 | B1：revert 代码**不足以回滚**——已写入的新列/新行需另出迁移说明（本仓纪律：迁移幂等、保留旧行）<br>B2/B3：`git revert` 单提交 | 采样（B3）会把"唯一可能的 LLM 侧痕迹"再乘以一个概率 ⇒ 与 §五 判据直接冲突（分母更小、更不可测）；B1 是**唯一会学习数据安全的形态**，命中本仓"写库/改数"闸面 |
| **C 下线＋出迁移说明** | 删 `:330-332` 三行（**注意 `:318` 门不能删**，它还闸着 attempt 落库与 review_state）；`docs/insights/learn-eventtypes-census-20260923.md` D-5 行由人工加注"已下线" | `core/judge.py`（`-3` 行）＋ 新建 1 份迁移说明档（`docs/insights/`）；`docs/system-report-v0.6.3.md:110`／`v0.6.4.md:110` 属**历史快照档，按"原样保留"不改**，只在迁移说明里声明失效 | **3 行删除＋1 份新档、1 个文件改** | `git revert` 单提交；存量 0 行 ⇒ **无数据回滚需求**（这正是 C 唯一的"便宜"处） | 🔴 下线后开放题评分在遥测上**永久不可见**（连 `llm_ok=True` 的正常流量也不留）；且 §一 事实 1 意味着**分母本就不存在** ⇒ 今天的 0 行**不能证明**"没人做开放题"。census 的"写而不读"也不完全准（§二 间接读侧 3 处） |

## 五、推荐案与判据（判据 ③）

### 5.1 先把"不可执行的判据"按实测收窄（不判 failed，照实况报）

卷宗建议"如按**近 30 日 attempts 开放题占比**阈值"——**当下不可算**，两条硬理由：

1. **分母与分子同时为 0**：`attempts` 近 30 日新增 0 行、`learning_events` 近 30 日 0 行（§三 E1，`events_last30_by_type=[]`）⇒ 占比是 0/0。
2. **口径不可得**：`attempts` 表**没有 `judge_mode` 列**（实测列集 `[id, lang, problem_id, code, passed, ai_feedback, ts]`），开放题身份只能靠"题号 ∈ 70 道开放题白名单"反推；而 §一 事实 1 说明 **`llm_ok=False` 的开放题根本不写 attempt** ⇒ 用 attempts 反推开放题流量是**右删失（censored）样本**，占比只会系统性偏高，拿它当下线依据是循环论证。

⇒ 判据必须换成"**先造分母、再算占比**"的两段式（下表），或明确承认今天无法裁决 C。

### 5.2 推荐案：**A′（保留＋补失败侧计数）为唯一当下可动项；C 判据延后自动生效**

- **第 0 步（A′）**：落 §四 A′ 的 `reason` 事件 ⇒ 造出"开放题提交总数"这个分母（`llm_ok=False` 与 `AI_VARIANT` 与写库失败三类各自可数）。
- **观测窗（启动条件）**：`learning_events` 自 A′ 落地日起累计新增 **≥200 行**或满 **2 个自然月**，先到为准。
  ⚠ 启动条件里必须带"库有活动"这一条：本仓最后一条事件距今已 32 天（§三 E1），**库若整月不动，任何窗口判据都等于零样本**。
- **判据表（阈值是建议值，样本为 0 时给不出统计依据，主班可改）**：

| 观测窗内读数 | 结论 | 下一步 |
|---|---|---|
| `ai_open_scored ≥ 30 行` | 有真流量 | 转 **A**（不再动码），并按 census 口径把它登记进漏斗/审计面 |
| `1 ≤ ai_open_scored < 30` | 有流量但稀 | 转 **B2**（并入 `rubric_scores` 同族字段，**不建新表、不动 attempts schema**）；B1/B3 明确不推荐（B1 触迁移与导出面，B3 采样会把分母 further 缩小） |
| `ai_open_scored = 0` 且 `reason=llm_unavailable` 计数 > 0 | 门在拦（有提交、LLM 不通） | **先修 LLM 侧或门的顺序**，禁止判 C（此刻下线＝把可修的基础设施问题当成"无价值事件"埋掉） |
| `ai_open_scored = 0` 且 门内写库异常计数 > 0 | `:320-334` 有 bug（G5） | 先修 `try` 块顺序/兜异常，再回本表重判 |
| `ai_open_scored = 0` 且 开放题提交计数（A′ 分母）= 0 | **真无流量**（这次是可证的） | 才允许走 **C 下线＋迁移说明**（§四 C 行，3 行删除＋1 档） |

- 为什么不是"现在就 C"：C 的净收益是省 3 行代码与未来每开放题 1 行事件；净损失是**唯一能证明"开放题这条路到底有没有人走"的写侧痕迹**。在分母本身不可测（§5.1）的盘态上下线，等于用"看不见"当"不存在"。
- 为什么不是 A（纯保留）：census D-5 给 A 的理由（"LLM 用量的唯一审计流水"）**已被 §一 事实 2 否证**（缓存命中也写、真失败不写）——保留一个语义名不副实的 type 而不修语义，是下一浪再次误读的源头。

## 六、完成标准 ④：`core/judge.py` 零 diff（兼全线只读自证）

| 时点 | `git status --porcelain` | `core/judge.py` |
|---|---|---|
| 本单全部取证跑完（含 §三 的只读连库与备份解包）后 | **3 行**：`?? docs/insights/learn-checkreadme-run-20260924.md`（同班 l924-28 产物）、` M docs/insights/learn-insights-index-20260918.md`、`?? docs/insights/learn-aiopenscored-disposition-20260924.md` | **不在列表 ⇒ 零改动**；`$ git diff --stat -- core/judge.py` 亦无输出 |

`$ git status --porcelain`、`$ git diff --stat -- core/judge.py`
⚠ 一处**只在文件系统层**的副作用（不进 git 视野）：只读连 WAL 库会触生 `data/progress.db-wal`（0 B）与 `data/progress.db-shm`（32 KB），`$ git check-ignore -v data/progress.db-wal data/progress.db-shm` → `.gitignore:18`／`:17` ⇒ `git status` 读不到它们，SQLite 语义正常产物。**本单未删**（删 `-shm` 若有他进程正连库属危险动作），收班时若确认库空闲可清。
只读连库证据：全程 `uri=True, mode=ro` + `PRAGMA query_only=ON`，快照用 `src.backup(dst)` 出**单文件**（非 copy2 三件套），未跑任何仓内 backup/prune 脚本，未做任何 `DELETE`/`checkpoint`/`VACUUM`。

## 七、复算配方（逐字可跑）

```bash
cd /d/code/learning-system
# ① 消费面（判据 ①）
rg -n "ai_open_scored" --glob '!tmp/**' .
rg -n "emit_event\(" core/ ui/ scripts/          # 写侧全景（13 处 / 9 个字面量 type）
rg -n "event_count\(|events_by_date" core/ ui/ scripts/ tests/   # 间接读侧
rg -n "ai_judged" . ; echo "rc=$? (1=不存在)"     # 案 B 原名的否证
# ② 门控与 llm_ok 语义
rg -n "AI_VARIANT::\"\)|emit_event\(\"ai_open_scored\"" core/judge.py
sed -n '430,460p;490,518p' core/ai_review.py      # llm_ok True/False 三出处 + 「绝不抛异常」契约
rg -n "basicConfig|FileHandler|log_file|\.log" app.py ui/ core/ scripts/   # 期望 0 命中＝无日志落盘面
# ③ 存量（严格只读，纪律 §十二 配方）
PYTHONIOENCODING=utf-8 python tmp/qoder-executor-20260925-0420-learn32/probe_events.py
# ④ 零行非清理所致：两份历史备份各自只读 SELECT（解包件在 tmp/<班名>/zip*/）
rg -n "prune_old_data" -g "*.bat" -g "*.ps1" -g "*.txt" .   # 期望 0＝无排程
```

> ⚠ 本档所有读数都是 **2026-09-25T04:3x+08:00 @ HEAD `cc7e4d5` 的现值，不是断言对象**：库是活的（WAL），开放题题数会随补题增长（本单 content 实测 70 道），引用前请现取。

## 八、与 census（`learn-eventtypes-census-20260923.md`）的差异清单（追加证据，不改那份档）

| census 说法 | 本单实测 | 影响 |
|---|---|---|
| §四 D-5：`ai_open_scored` 是"LLM 用量的唯一审计流水"，故不建议停写 | 缓存命中路径（`ai_review.py:435` 读 `_feedback_cache`，`:96` 只缓存 `llm_ok=True`）**也写事件**；`llm_ok=False` 的那一次真调用**反而不留痕** | D-5 的留值理由不成立（但不等于结论要反过来——见 §五） |
| §三：`ai_open_scored` 读侧「零」⇒"写而不读" | 无点名句柄，但 `event_count()` 总数口径被 `dashboard.py:299-300`（导出缓存键 `_exp_key`）＋`backfill_events.py:36/92`（幂等基线）**间接**消费，共 3 处 | C 案的"零影响"要改成"当前 0 行故无差异、未来有语义影响" |
| §二/§三：存量 0 行 | 复算成立，且**两份历史备份（0815／0904）同为 0**、无排程清理 ⇒ 零行是**跨时点稳定**读数 | 加强 census，但**不加强"无流量"推论**（§一 事实 1 的删失） |
| §二 表格内引用「`judge.py:324` 的 `if dimensions and attempt_id`」 | 🔴 **行号已漂 2 行**：实测该条件在 `:326`（`:323` 是 `record_attempt_and_status`、`:324` 是 `update_review_state`）；同形态的第二处漂移在 `tests/test_export_cache_invalidation.py:5`——它自述 `_exp_key` 在 `dashboard.py:213`，实测已在 `:299` | 印证纪律 §十.4/§十二——同文件 `:318/:330` 两个锚本单复测**未漂**，但中间块漂了 ⇒ 交接一律**只锚唯一文本**，别抄 census 的行号 |
| §三 census 把 `ai_open_scored` 归入「写而不读」的读侧口径 | 下线动作的连带面要按"缓存键会少一个扰动源"评估，不能按"无消费方"评估（间接读面 3 处，见 §二） | 与上一行同一结论，不重复展开 |
