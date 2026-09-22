# dashboard 推荐曝光写序缺陷修法设计稿：emit 前 vs emit 后 ＋ 幂等键（l923-06，只出设计零改码）

- 任务：`zcode-bridge/inbox/l923-06.task.md`（班 `qoder-executor-20260923-0022-learn2`，2026-09-23）
- 上游实测：`zcode-bridge/done/l922-101-dash-event-fail.result.md`（后果实测）、`l922-102-dash-click-nav`、`l922-103-dash-cross-except`
- 纪律：本稿**不动一行源码**；处置方向由规划班/仲裁拍板后另派单。
- 复算工具：`PYTHONIOENCODING=utf-8 python tmp/l923_06_writeorder_model.py`（写序语义推演器，只读模型、不落库、不改码；下表全部数字由它产出）

## 一、缺陷与行号现值（磁盘实取，@ HEAD `8f511c5` ＋ 本夜 l923-04/05 未提交改动，dashboard.py 未被那两单触碰）

| 站点 | 现值行号 | 形状 |
|---|---|---|
| 今日推荐 · 记账循环 | `ui/pages/dashboard.py:169-183` | `:169 try` → `:170 for` → `:172 if pid_key not in shown` 门控 → `:173 add(shown)` → `:176-178 impressions[...]=` → `:179-181 dao.emit_event("recommendation_shown")` → `:182 except Exception` → `:183 logger.debug("dashboard: 推荐展示数据异常")` |
| 今日推荐 · 卡片渲染 | `:184-195` | **在记账循环之后、不受其异常影响**：记账循环中途出圈，五张卡照样全渲 |
| 今日推荐 · 点击 | `:196-209` | `:196 try` → `:197-198 查 impressions` → `:199-206 emit(clicked)`（rid 取 `imp.get("recommendation_id","")`、rank 取 `imp.get("rank",0)`）→ `:207 except` → `:209 navigate_to_problem`（**在 try 外**，l922-102 钉的死键防线） |
| 跨路径 · 记账循环 | `:349-359` | 同型写序（`:352 add` → `:354-356 impressions` → `:357-359 emit`），**但整段没有任何 try** |
| 跨路径 · 点击 | `:374-386` | `:384 except` 包的是点击上报，`:385` 文案却写「跨路径推荐展示异常」（名实不符，l923-07 处理） |
| 页面入口 | `:90-97` | `render_dashboard` 只 `try/finally`，**不 catch** ⇒ 跨路径区一抛，整页后半段（成就/热力图/报告导出/学习数据/最近活动）全不渲染（l922-103 例 C 实测） |
| 曝光 rid | `:19-21` | `_make_rec_id = f"{YYYYMMDD}_{surface}_{reason_code}_{lang}_{pid尾}_{rank}"` ⇒ **同日同 rank 确定性可复现**，天然可做幂等键的值，但库里没有任何唯一约束 |
| 事件写入 | `core/progress.py:525-540` | `with self.conn:` 包 INSERT，返回 `lastrowid`；`learning_events` 表（`:90-101`）只有 4 个普通索引，**无唯一列** |
| 漏斗取数 | `core/progress.py:562-583` | `SELECT event_type, COUNT(*) ... GROUP BY event_type` ⇒ **裸行数计数，不按 recommendation_id 去重**；按策略分组同理（`:585-610`） |

会话态前提（推演要用）：`_rec_shown_ids` / `_rec_impressions` 都在 `st.session_state` 里 ⇒ 去重域是**单个浏览器会话**，会话结束即清零。streamlit 任何交互都会整段重跑渲染体，所以「下一帧」几乎总会到来。

## 二、后果（l922-101 实测，本稿不重述为猜测）

1. `:173/:176` 两件本地账都在 `:179` 送达**之前**写完 ⇒ 失败那条已进 shown，下一帧被 `:172` 门控永久跳过 ⇒ 该条曝光**永久丢失且不自愈**，本地口径与事件库从此恒差 1。
2. `:182` 的 try 包整段 for ⇒ 一条失败把该帧**其余条目一起**变成"本帧不试"（实测：5 条中第 3 条炸，首帧只尝试 3 次）。
3. 展示侧炸了卡片仍渲、按钮仍可点 ⇒ 未记进 impressions 的卡点击时 rid 退化成**空串**、rank 退化成 0 ⇒ 事件库出现 `clicked > shown`。

## 三、两案（含一个必要的第三案）的定义与代码落点

伪码均只针对 `dashboard.py:169-183` 这一块；跨路径区 `:349-359` 是否同批同改见第六节。

### 现状（基线，便于对照）
```
try:
    for rank, it in enumerate(plan, 1):
        if pid_key in shown: continue
        shown.add(pid_key)            # 本地先记
        impressions[k] = {...}
        dao.emit_event("recommendation_shown", ...)   # 后送达
except Exception:
    logger.debug(...)                 # 一条炸 → 整批出圈
```

### A 案『emit 成功后再落 shown』（任务书 A）
落点 `:173-181` 三行次序换成「先 emit，成功后 add/写 impressions」；`:182` 保留。
```
        dao.emit_event(...)           # 先送达
        shown.add(pid_key)            # 成功后才记
        impressions[k] = {...}
```
- **A1 = A 的字面形态**（仍批级 try）：解决永久丢失，未解决连带半径。
- **A2 = A ＋ per-item try**（把 `:182` 的 except 挪进循环体）：两者都解决。本稿推荐形态。
- **A3 = A2 ＋ 库侧幂等键**：`learning_events` 增 `dedup_key`（或直接对 `json_extract(payload_json,'$.recommendation_id')`）建**唯一索引**、`emit_event` 走 `INSERT OR IGNORE` 并以 `cursor.rowcount` 判是否新增。落点 `core/progress.py:525-540` ＋ `_migrate()`（`:122+`，现成先例是 `PRAGMA table_info` ＋ `ALTER TABLE ADD COLUMN` 的容错式加列）。

### B 案『try 收到单条循环体内』（任务书 B）
只把 `:182-183` 的 except 移进 for 体（照 `:207-208` 点击侧同型），写序 `:173→:176→:179` **一字不动**。

## 四、事件计数影响推演（模型输出；现状列已按 l922-101 实测校准：首帧送达 2／本地 3／未试 2 逐位相同）

注入条件：5 条推荐，第 1 帧第 3 条 `emit_event` 抛错，第 2 帧故障恢复。

〔表 1 · 故障那一帧〕

| 变体 | 事件库送达 | 本地记账 | 本帧未试条数 | 空 rid 点击面 |
|---|---|---|---|---|
| 现状（本地先记＋批级 try） | 2 | 3 | 2 | 2 |
| A1（emit 先记＋批级 try） | 2 | 2 | 2 | 3 |
| **A2（emit 先记＋per-item try）** | 4 | 4 | **0** | **1** |
| B（本地先记＋per-item try） | 4 | 5 | **0** | 0 |

〔表 2 · 两帧后，看自愈〕

| 变体 | 事件库送达 | 本地记账 | 永久丢失 | 悬空本地账（本地记了、库里永无） |
|---|---|---|---|---|
| 现状 | 4 | 5 | **1** | **1** |
| A1 | 5 | 5 | 0 | 0 |
| A2 | 5 | 5 | 0 | 0 |
| B | 4 | 5 | **1** | **1** |

读法与量级口径：

- **永久丢失量级**：现状与 B 恒为「每次事件库故障 episode 恰 1 条」（首炸那条），A1/A2 为 0。不是"整批丢"——其余条目只是晚一帧，`shown` 门控没记下它们。
- **连带半径**：批级 try（现状/A1）= 首炸点之后全部本帧不试（最多 4 条）；per-item（A2/B）= 0。
- **漏斗 `shown` 行数**：稳态（无故障）四案完全相同 ⇒ **本改动不改正常态计数口径**。故障期 A/B 都会让 `shown` 比现状**多**（B 多 2，A2 多 2），A1/A2 之后还会再补回永久丢的那 1 条。差值上限＝「故障帧数 × ≤5」。
- **脏 clicked 的两种形态要分清**：A2 在故障帧留 1 条**空 rid** 点击（rid 为空＝肉眼可辨的缺口，且因 rid 确定、下一帧 shown 会补上，事后归因可闭合）；B 留的是**悬空 rid**——点击事件带着一个事件库里永远不会出现的 `recommendation_id`，漏斗对账看着完整、实则断裂，比空串更坏。
- **A3 的代价不在故障期而在稳态**：唯一索引会把「同一会话/不同会话同日同 rank 的二次曝光」一并吞掉 ⇒ 这是**计数口径变更**（`shown` 从现在的"行数"变成"去重行数"），漏斗、`_render_recommendation_funnel`（`dashboard.py` 内 `dao.recommendation_funnel`）与 `test_dashboard.py:97/109/120` 三例的期望值都会跟着动。按本工作区纪律「改计数口径一律停手交人工」，A3 **不并入本批**。

## 五、受影响已钉测试清单（例名逐条，`grep -n '^def test_'` 复核在盘；行号为现值）

`tests/test_dashboard_event_failures.py`（l922-101 八例 ＋ l922-102 两例 ＋ l922-103 三例）

| 例（file:line） | 现钉内容 | A1 | A2 | B |
|---|---|---|---|---|
| `test_shown_event_failure_still_renders_all_five_cards:115` | 卡片全渲 ✓ ＋ `kinds()==[shown]`（首炸即出圈） | 绿 | **红**（尝试 5 次） | **红** |
| `test_shown_event_failure_logs_debug_with_exc_info:126` | `SHOWN_MSG` 恰一条 | 绿 | **红**（每炸一条） | **红** |
| `test_local_state_is_written_before_emit_so_one_failure_loses_that_impression_forever:143` | 写序缺陷本体 | **红** | **红** | **红** |
| `test_local_impression_state_and_emitted_events_match_when_nothing_fails:168` | 无故障 1:1 | 绿 | 绿 | 绿 |
| `test_failure_on_third_item_leaves_local_state_ahead_of_events_by_one:187` | 本地领先 1 | **红**（本地不再领先） | **红** | 绿（该例只注入第 3 条，per-item 后 `n==3` 变 5 ⇒ 亦**红**） |
| `test_click_event_failure_still_navigates_to_problem:211` | 点击炸不影响跳转/展示 | 绿 | 绿 | 绿 |
| `test_click_report_reuses_the_impression_id_written_at_shown_time:234` | rid 归因链（无故障） | 绿 | 绿 | 绿 |
| `test_shown_side_failure_yields_clicked_events_with_no_matching_shown_event:248` | clicked>shown ＋ 空 rid | **红** | **红** | **红** |
| `test_click_emit_failure_leaves_navigate_called_exactly_once:280`（l922-102） | navigate 在 try 外 | 绿 | 绿 | 绿 |
| `test_navigate_runs_after_the_failed_emit_not_instead_of_it:310`（l922-102） | 尝试序 [2] | 绿 | 绿 | 绿 |
| `test_cross_click_failure_still_renders_records_navigates_and_logs:368`（l922-103 例 A） | 跨路径点击 except | 绿 | 绿 | 绿（文案改则 `CROSS_MSG:343` 需同步） |
| `test_cross_shown_event_failure_escapes_the_function_entirely:401`（l922-103 例 B·现状桩） | shown 抛错窜出函数 | 绿（本区不改则不动） | 绿 | **红**（若跨路径区同批改） |
| `test_cross_shown_event_failure_takes_down_every_section_below_it:422`（l922-103 例 C·现状桩） | 整页后半段消失 | 绿 | 绿 | **红**（同上） |

`tests/test_dashboard_page_render.py`

| 例 | A1/A2/B |
|---|---|
| `test_render_cross_recommend:105` | 绿（正常流，写序不显形） |
| `test_render_dashboard_recommend_plan_impressions_and_events:169` | 绿（2 记 2 报，终态一致） |
| `test_render_dashboard_recommend_empty_plan_shows_info:189` | 绿 |
| `test_render_dashboard_recommend_button_click_emits_clicked_and_navigates:199` | 绿 |
| `test_render_dashboard_recommend_second_run_no_duplicate_shown:217` | 绿（去重仍靠 shown 集合，A 案只是把它挪到 emit 之后） |

`tests/test_ergo_h912_13.py`

- `test_dashboard_no_silent_except:77`：源级 `src.count("logger.debug(") >= 3`。**三案都判绿**——它是松下界，per-item try 多出一处 `logger.debug` 也不会红。⇒ 本稿登记一个**看守缺口**：这条断言不能证明"写序"或"try 粒度"有任何变化，改桩时不要误以为它兜住了行为面（收紧它属改测试语义，与 `tests/test_paths.py:29` 同性质，需人工）。

`tests/test_dashboard.py`：`test_recommendation_funnel_uses_created_at:97`／`_all_time:109`／`_by_reason:120`／`test_recommendation_completed_carries_full_attribution:135`／`_no_shown_no_event:154` 五例都在 DAO 层直插事件、不经渲染路径 ⇒ A1/A2/B 全绿；**只有 A3（唯一索引＋INSERT OR IGNORE）会改它们的语义**（`completed_carries_full_attribution` 依赖"shown 已有一条同 rid 行"这一事实）。

改造工作量小结：A1 需改桩 4 例、A2 需改桩 5 例、B 需改桩 5 例（含把"缺陷现状"改成的目标断言）——**三案的测试改造量相近，不构成选型依据**。

## 六、与同批 l923-07 的耦合（必须一起裁决，否则留下更坏的第二种脏）

l923-07 正在做的是：给跨路径区 `:349-359` 补 per-item try（＝B 型粒度）＋改 `:385` 文案，并把 l922-103 的例 B/例 C 现状桩改成修好版。
- 若本稿按字面在 dashboard 区选 **B**，两区都只解决连带半径，**永久丢失与悬空 rid 在两区各留 1 条/episode**；
- 若 dashboard 区选 **A2**、跨路径区只做 B（l923-07 的字面范围），两区写序**不一致**，后人照抄其中一处就会抄错；
- 因此**推荐出口要求两区同型**：跨路径区在补 per-item try 的同一批把写序也换成 emit 先、成功后记账（`:352/:354-356` 挪到 `:357-359` 之后）。这一句是 l923-07 落地时必须读到的约束。

## 七、推荐出口

**推荐 A2（emit 成功后落本地账 ＋ per-item try），A3 另开单交人工。** 理由：

1. A2 是唯一同时消灭「永久丢失」和「连带半径」的形态（表 2 两格归零），而 B 连 l922-101 的核心后果（不自愈）都没解决——选 B 等于把这条在册重话留在盘上。
2. A2 的残余风险是**可事后闭合**的：rid 由 `:19-21` 确定生成，下一帧补齐的 shown 带同一个 rid，归因链自动接上；B 留下的悬空 rid 无法事后闭合，且骗过"点击是否带 rid"这一层对账。
3. A2 **不动稳态计数**（表 1/2 的无故障路径与现状逐位相同），因此不改漏斗口径、不动 `learning_events` schema、不需要迁移——A3 才动，故 A3 单独走人工（改计数口径是本工作区的在册停手项）。
4. 改动面最小：`dashboard.py` 一个代码块换序 ＋ except 下沉一层；跨路径区同型一处；改桩 5 例。
5. 幂等键在 A2 下**不是必需**（会话内 shown 集合已挡重复；跨会话重复曝光是**现状既有**语义，与本缺陷无关）。若将来要真幂等，走 A3 并连带声明漏斗口径变更，别在 A2 里顺手塞去重逻辑。

落地批次建议（放行后另派单，一单两文件一批）：
① `dashboard.py:169-183` 换序＋except 下沉、`:349-359` 同型（与 l923-07 合并同批，避免两区形态漂移）；
② `test_dashboard_event_failures.py` 五例改修好版断言，并**新增**一条「故障帧失败、恢复帧补报同一 rid」的自愈例（今天这条线只有"钉坏"没有"钉好"）；
③ 若担心 `:182` 出圈语义被误读，同步把 `test_ergo_h912_13.py:83` 的 `>= 3` 松下界另单交人工收紧（本稿不主张顺手改）。

## 八、取证局限与待裁决

- **本机库无法给量级外推**：`data/progress.db` 只读实取（`file:...?mode=ro&immutable=1`）`recommendation_shown` 仅 **10 条、clicked 0 条、rid 重复 0、rid 缺失 0** ⇒ 上表的"多少条/episode"只能按代码路径推演，真实用户机器上的差值取决于事件库故障频次，本仓无数据可估。
- 待裁决 1：是否接受 A2 的"故障帧最多 1 条空 rid 点击"作为残余风险（本稿判断可接受，因 rid 确定 ⇒ 可事后闭合）。
- 待裁决 2：A3（幂等唯一索引）要不要做——做了漏斗才真正"按曝光去重"，但这是计数口径变更，历史数据不可回改，跨端会话同日二次曝光将从漏斗里消失。
- 待裁决 3：跨路径区 `:357` 的 emit 现在**裸奔在整个渲染主路径上**（`render_dashboard:94-97` 不 catch），本稿建议的"两区同型"若被拆开执行，请先执行"给 `:349-359` 加 try"这一半（l923-07 正在做），另一半（写序）再随 A2 同批。
- 本稿零源码改动：`git status --porcelain` 只应出现本文件与索引登记行（详见 result「证据」）。
