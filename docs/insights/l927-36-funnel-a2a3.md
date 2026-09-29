# A2 残余风险量化／A3 计数口径变更影响／两区写序一致性——l923-06 三条待裁决的汇编材料（l927-36，只读、零写数据）

- 卷宗：`zcode-bridge/inbox/l927-36.task.md`（做什么原文＝「汇编三条裁决材料，每条两案＋推荐，供拍板」）。
- 锚点：`zcode-bridge/done/l923-06.result.md` 遗留问题 1 的三条 ＋ 其设计稿 `docs/insights/learn-shown-writeorder-design-20260923.md` §八「待裁决 1／2／3」。
- 执行：波次 85 只读材料班 `learn70`（前手 `learn69` 服务侧中止、盘上零足迹，本单从零重做），cwd `D:\code\learning-system`，2026-09-30。
- 纪律：**只出材料、不选路、不改判据、不动一字节生产码、不登记索引行、零写库**。三条里最硬的 A3 属计数口径变更（历史不可回）＝人工闸，本档只给可批形状。
- 盘态现取：HEAD `0f0b39a`、`git status --porcelain` **0 行**；本档写完后的工作树终值应恰为本档一行（见 §七 复算命令 ①）。

---

## 〇、三条各自的推荐（一句话，细节见各节）

| 条 | 推荐 | 一句话理由 |
|---|---|---|
| 待裁决 1（A2 残余风险） | **接受**，但**先把"上限不是 1 条而是本帧失败条数"这句改对**再批 | 跨路径区自 `e9a1606` 起**已经在跑 A2**，这条今天不是"要不要接受"，是"追认已生效的形态"；而风险量级被档内旧表述低估了 |
| 待裁决 2（A3 幂等唯一索引） | **不做**（甲案） | 设计稿 §三 字面形态在盘上**建不起来**（三腿共用同一 rid，实测 `IntegrityError`）；可行的部分索引形态换来的只有跨会话去重，代价是 CTR 类派生率机械上涨＋口径断裂那一天不可回 |
| 待裁决 3（按档＝两区同批） | 原形态**已关单**，现在要拍的是它的**反向遗留**：两区写序不一致；推荐**拉齐到 A2**（甲案） | l923-07 做了前半（加 try）、l927-37 做了后半但**只做半区** ⇒ 今日推荐仍是 B 型；不同型会让后人照抄错，这格主班 09-28 已标「🔴 人工项·主班不签」 |

---

## 一、盘上现值 vs 档内旧值（先看这张表，否则三条会裁错对象）

设计稿 §一 的行号与结论**大部分已过期**，三条里有一条已被执行掉半条。逐格现取：

| 站点 | 档内旧值（2026-09-23） | 盘上现值（2026-09-30，HEAD `0f0b39a`） | 形态 |
|---|---|---|---|
| 今日推荐 · 曝光记账循环 | `dashboard.py:169-183` | `ui/pages/dashboard.py:211-225` | **B 型未变**：`:215 add` → `:218-220 impressions` → `:221-223 emit`（per-item try 由 l924-01 补，写序由 l927-49 加了预检前缀 `:203-210`） |
| 跨路径 · 曝光记账循环 | `:349-359`（整段裸奔无 try） | `ui/pages/dashboard.py:429-461` | 🔴 **已是 A2**：`rec_id`/`payload` 提到 try 外（`:450-452`）→ `:454-455 emit` → `:456 add` → `:457-459 impressions`；per-item try 由 l923-07 落、写序由 **l927-37＝`e9a1606`（09-28 13:17 入库）** 落 |
| 今日推荐 · 点击 | `:196-209`（navigate 在 try 外） | `:246-262` | **l927-29 裁决后＝送达门控**：`reported` 旗标 ⇒ 失败不跳 |
| 跨路径 · 点击 | `:374-386` | `:476-490` | **失败仍跳**（`navigate_to_problem` 在 `:490`、try 外）⇒ 与上格不一致 |
| 曝光 rid 公式 | `:19-21` | `ui/pages/dashboard.py:19-22` | `{YYYYMMDD}_{surface}_{reason}_{lang}_{pid 末段}_{rank}`，**无会话分量** ⇒ 跨会话同日同 rank 同题＝同一个 rid |
| 事件写入 | `core/progress.py:525-540` | `core/progress.py:547-562` | 仍是裸 `INSERT INTO learning_events`，`return cur.lastrowid` |
| 表与索引 | `:90-101` | `core/progress.py:116-130` ＋ `:136-141` | `sqlite_master` 实测 learning_events 上 **4 枚普通索引、0 枚唯一索引**（A3 至今不存在） |
| 漏斗取数 | `:562-583` | `core/progress.py:588-609`（分组 `:611-634`） | 仍是 `SELECT event_type, COUNT(*) ... GROUP BY event_type`＝**裸行数**，不按 rid 去重 |
| 漏斗面板 | 未列行号 | `ui/pages/dashboard.py:605-643` | 🔴 派生率住在码里：CTR `:620`、完成率 `:621`、点击→完成 `:631`、按策略表 `:637-643` |
| 应用侧幂等先例 | 未在册 | `ui/pages/path.py:202-216` | `_emit_path_started`／`_emit_milestone_completed` 用 **meta 表 key 去重**（"once per path (dedup via meta table)"）＝不改 schema、不改计数口径的第三种去重形状，A3 讨论必须对照它 |

复算命令见 §七 ②③④⑤。

---

## 二、材料一：A2 的残余风险要不要接受（待裁决 1）

### 2.1 事实

1. **这条已被执行掉一半**：跨路径区自 `e9a1606` 起就是 A2 形态，`docs/insights/l927-37-writeseq.md` §三.1 白纸黑字登记「A2 的已知残余风险落地了」，并把它写成"该红就红"的用例 `tests/test_dashboard_event_failures.py:585-586`（`recommendation_id == ""` 且 `rank == 0`）。⇒ 今天批的不是"要不要引入"，而是**"要不要追认＋要不要把另一半也换成它"**。
2. 🔴 **风险量级被档内旧表述低估**：设计稿 §四 表 1 给 A2 的「空 rid 点击面＝1」，那是**只注入第 3 条失败**那一格。真实上限是**本帧失败条数**——per-item try 下每条各丢各的，凡 `emit` 失败的那条都不写 impressions，点击时 `imp.get(..., "")`（`:481`）就退化成空 rid。一帧上限＝该区条数：今日推荐 `recommend(n=5)`（`:171`）＝**5**、跨路径 `cross_recommend(n=3)`（`:418`）＝**3**，两区合计一帧最多 **8** 条空 rid 面。"最多 1 条"这句**不能作为批准前提**，要改成"最多＝本帧失败条数，单区 ≤5／≤3"。
3. **窗口长度＝故障帧到恢复帧**：rid 由 `:19-22` 确定性生成，恢复帧补报的 shown 带同一个 rid ⇒ 归因链事后可闭合（设计稿 §七 理由 2 成立，盘上仍成立）。
4. **同一次故障在两区留下两种脏形态**（这才是现在最难对账的一格）：今日推荐是 B 型，失败那条**本地已记** ⇒ 它的 clicked 带一个事件库里永不出现的**悬空 rid**（`tests/test_dashboard_event_failures.py:355` 正钉着这个）；跨路径是 A2 型，失败那条**本地未记** ⇒ clicked 带**空 rid**。⇒ 对账脚本要写两套判据，"点击是否带 rid"这一层只能查出跨路径那一型，查不出今日推荐那一型。
5. **本机库给不出量级外推**（与设计稿 §八 同口径，读数值未变）：`recommendation_shown` **10 行**、`clicked` **0 行**、`completed` **0 行**、shown 的 distinct rid **10**、空 rid **0**、重复 rid 组 **0**、`learning_events` 总 **81 行**、`payload_json IS NULL` **19 行** ⇒ 上面 1／2／4 全是**代码路径推演**，不是生产观测。取数命令见 §七 ⑥。

### 2.2 两案

- **甲案（接受，并按现值改写批准文本）**：追认跨路径区既有形态 ＋ 承认"故障帧留空 rid／rank=0 的 clicked 行"是**可观测标志而非脏数据**（漏斗对账时按 `json_extract(payload_json,'$.recommendation_id')=''` 计数即闭合）；不加 `st.warning`、不改 except 粒度、不动计数口径。可见反馈那一格按 `docs/insights/l927-29-note.md` §三.1 留给另单（它已实测：加 `st.warning` 不破 §七 例 3，因为那条只注曝光侧）。
- **乙案（不接受）**：把跨路径区写序**回退**成 B 型（撤销 `e9a1606` 的写序半批，`git revert` 摘不动——同笔还带着测试件 +178/-12）。换来空 rid 归零，代价是把每 episode 的**永久丢失 1 条＋悬空 rid 1 条**重新装上（设计稿 §四 表 2 的 B 行），且 `test_l927_37_*` 两枚新桩（`:939`／`:982`）当场红。

### 2.3 推荐

**甲案**，但批准文本必须**改掉"最多 1 条"这句**（§2.1.2）；否则批下来的不是盘上那个东西。乙案的"零空 rid"是用更坏的一格换的（悬空 rid 骗过对账），设计稿 §七 理由 2 已论证过一次，盘上现值仍支持它。

---

## 三、材料二：A3（幂等唯一索引）做不做（待裁决 2）

### 3.1 事实

1. **设计稿 §三 的字面 A3 形态在盘上建不起来**（本单实测，非推演）：`recommendation_clicked` **复用** shown 的 rid（`dashboard.py:253`／`:481`），`recommendation_completed` **再复制一次**同一个 rid（`core/judge.py:166-181`，它先 `SELECT ... WHERE event_type='recommendation_shown' ORDER BY rowid DESC LIMIT 1` 再原样带出）。⇒ 一条"对 `json_extract(payload_json,'$.recommendation_id')` 建唯一索引"的**全表形态**语句，在三腿跑通一遍后当场 `sqlite3.IntegrityError: UNIQUE constraint failed`；即便建成，同 rid 的 clicked `rowcount=0`、completed `rowcount=0` ＝**点击腿与完成腿被 `INSERT OR IGNORE` 静默吞光**，漏斗只剩 shown。复现见 §七 ⑦。
2. **全表形态还会顺手抹掉材料一那个"肉眼可辨的缺口"**：空 rid 是 `''`（空串）不是 NULL，唯一约束**照样咬**——实测第 2 条空 rid clicked 的 `rowcount=0`。⇒ 两案直接冲突：A3 全表形态会把 A2 赖以闭合的证据链删掉。
3. **可行的只有部分索引形态**：`... WHERE event_type='recommendation_shown'` 实测可建、可挡二次曝光（`rowcount 0`），且不动 clicked/completed 两腿、不吞空 rid 行。但两个连带事实要一起批：
   - **历史可能挡住建索引**：若已有同 rid 的 shown 重复行，连部分索引也 `IntegrityError`（实测）。本机现值**重复组 0** ⇒ 本机可建；**真实用户机不可外推**，乙案前置必须先普查重复组（语句在 §七 ⑥ 末行），普查非空就先决定"合并还是保留"，那本身又是一次口径决定。
   - **NULL 豁免**：SQLite 唯一索引里 NULL 互不相等 ⇒ `payload_json IS NULL`（本机 19 行）与不带该键的行**不受影响**，A3 只作用于带 rid 的行。
4. **改 `emit_event` 走 `INSERT OR IGNORE` 的爆炸半径＝12 枚调用点**：`dashboard.py:221/250/454/479`、`language.py:309`、`path.py:207/216`、`achievements.py:147`、`judge.py:175/203/206/351`（`grep -rn "\.emit_event(" --include=*.py ui/ core/`＝**12**）。其中 **4 枚在 `core/judge.py`＝判分口径红线域**，本单只登记不签。好消息：这 12 枚**无一枚消费返回值**（`grep -E "[A-Za-z_]+ *= *[a-z_]+\.emit_event\(" ui/ core/`＝**0**），所以 `lastrowid` 语义变化不构成现网回归——但要注意实测读数：被 IGNORE 时 `lastrowid` 回的是**旧行的 id**（探针回 `(rowcount=0, lastrowid=1)`），将来谁要拿它当"插入成功"的凭据就会拿到假成功。
5. **口径变更的真实代价在派生率上，不在行数上**：`dashboard.py:620-621/631/637-643` 的 CTR／完成率／点击→完成全按 `shown` 行数当分母。A3 只削分母 ⇒ **同一批用户行为下 CTR 机械上涨**，而"7 天／30 天／全部"三档窗口（`:609-611`）里，建索引那一天会表现成**同一个窗口内的台阶**，跨期不可比；历史行不可回改（合并历史＝造第二份真相）。
6. **盘上已有一枚不改口径的去重先例**：`ui/pages/path.py:202-216` 的 meta-key 去重在**写入之前**就不发第二次 emit ⇒ 库里根本不产生重复行，漏斗"裸行数"的语义**不变**。若真要跨会话去重，这条路线比库侧索引少一次 schema 迁移、少一次全表普查，也**可回滚**（删 key 即回）；代价是它同样会让"曝光"这一列不再涨（口径影响与 A3 同向，只是不动库）。

### 3.2 两案

- **甲案（不做 A3）**：漏斗维持"裸行数"口径，会话内去重继续只靠 `shown` 集合；跨会话二次曝光**算 2 条**是**在册既有语义**（设计稿 §七 理由 5），与本缺陷无关。零 schema 迁移、零改 emit 路径、零红线接触。
- **乙案（做 A3）**：必须钉死三个限定，缺一条就不可批——① **部分表达式唯一索引**（`WHERE event_type='recommendation_shown'`），**禁止**设计稿 §三 的全表形态（§3.1.1 已实测否证）；② 建索引前先普查重复组，非空则另裁"合并还是保留"；③ 明示口径生效日＋跨期不可比的台阶声明，并同步 `tests/test_dashboard.py:97/109/120`（三例漏斗期望）与 `:135`（`completed_carries_full_attribution` 依赖"shown 里已有一条同 rid 行"）。落点＝`core/progress.py:116-130` 加 DDL ＋ `:149-165` `_migrate()` 容错加索引 ＋ `:547-562` 换 `INSERT OR IGNORE`；**替代实现**＝§3.1.6 的 meta-key 路线（不动 schema，需先拍"曝光数该不该停涨"）。

### 3.3 推荐

**甲案（不做）**。理由：A2 已把"永久丢失"归零（跨路径区已生效），A3 剩下的收益只有"跨会话同日同 rank 去重"，而它要同时付：一次不可逆的计数口径断裂＋派生率台阶＋12 枚调用点里 4 枚踩在 `core/judge.py` 判分红线＋**抹掉材料一赖以闭合的空 rid 证据**（若走全表形态）。若将来真要，走**部分索引＋三限定齐**或 **meta-key 路线**，别在 A2 批次里顺手塞去重。

> 红线声明：本条属**计数口径变更／统计数值结论**，本档**只登记不签**；上面所有比率类推论都是"形状"，不是数值结论。

---

## 四、材料三：按档＝l923-06 §八 待裁决 3（两区同批）——原形态已关单，反向遗留在册

### 4.1 事实

1. **原形态**：「跨路径区 `:357` 的 emit 裸奔在渲染主路径上；两区同型若被拆开执行，先执行加 try 那一半（l923-07 正在做），写序那一半随 A2 同批。」
2. **两半都执行了，但写序那半只做了一个区**：
   - 加 try ＝ `l923-07`（`b575e0d`，09-23 02:13 done，claims 原话「写序未动（A2 未放行）」）✓
   - 写序＝`l927-37`（`e9a1606`，09-28 13:17 主班代提交）**只换跨路径区**；同一批 note 里主班已标 🔴【人工项·主班不签】：「该班明写没照办：l923-06 §六／l923-07 遗留1 要求『两区同批』……两区曝光写序自此不一致」✓（取数见 §七 ⑧）
   ⇒ **待裁决 3 的原始问题已无对象**；现在要拍的是它的**反向遗留**。
3. **反向遗留是两格，不是同一格**（`docs/insights/l927-37-writeseq.md` §三.2 与 `l927-29-note.md` §三.2 各自点名）：
   - 曝光写序：今日推荐 `:211-225` B 型 vs 跨路径 `:429-461` A2 型。
   - 点击语义：今日推荐 `:246-262` 送达门控（失败不跳）vs 跨路径 `:476-490` 失败仍跳。
   ⇒ 两案可并案裁，但**方向不同**：曝光侧该向 A2 拉，点击侧该向门控拉；`l927-37-writeseq.md` §三.2 明写「别照抄 l924-01 的拉齐方向，那次是新向旧看齐」。
4. **拉齐是有主的、且桩确有牙**：`tests/test_dashboard_event_failures.py:787` 的对照例已**逐表面钉值**（`:807` `expected_local = 3 if surface=="dashboard" else 2`），其 docstring `:801` 自证「把今日推荐区也换成 A2 ⇒ 只有 dashboard 支红」。按字节把跨路径区写回旧序 ⇒ 只有 cross_path 支红（`l927-37-writeseq.md` §四 M1 变异实测）。⇒ 拉齐这一改**不会静默通过**，改桩清单是现成的。
5. 同族还有一格在册不一致没进本条：`l927-49` 有意**没把畸形项预检搬到跨路径区**（`dashboard.py:201-202` 注释点名"两区对畸形项的容错自此不一致"）。它和写序无关，但同属"两区不同型"这一族，拍一致性时值得一并知情。

### 4.2 两案

- **甲案（拉齐，一单两文件一批）**：今日推荐区 `:211-225` 换 A2（emit 先、成功后 `add`、再 impressions），同批改桩：`:210`（钉缺陷本体那例，名字本身就得换）、`:259`（本地领先 1 → 领先 0）、`:332`（悬空 rid → 空 rid）、`:756`（`SHOWN_KEY==5`/`IMPR==5` → 4/4）、`:787`（dashboard 支 3→2）。点击侧另笔同批或紧随：跨路径 `:476-490` 换 `reported` 门控（补丁形状与 l927-29 **逐字同型**，需同步 §五/§六 3 例，清单在 `l927-29-note.md` §三.2）。**属 UI 生产码写位单，本单不执行。**
- **乙案（维持不一致＋把它写成制度）**：不改码，在设计稿/索引/两区注释三处明写"两区不同型是**有意**的，禁止照抄其中一处"，并给对账脚本两套判据（空 rid 判跨路径、悬空 rid 判今日推荐）。代价：l923-06 §六 当年论证的"后人照抄错"这条风险**原样留在盘上**，而且已经真发生过一次（l927-37 就是照卷宗点名只做半区）。

### 4.3 推荐

**甲案**，且**先做曝光侧那一格**（拉齐到 A2）、点击侧随后单独一笔——理由是两格里"该向哪边拉"的答案不同，混在一笔里容易又被照抄错。⚠ 注意拉齐后今日推荐区会**新增**材料一那格空 rid 面（一帧最多 5 条），所以**材料一的批准文本必须先改对**，否则甲案会把一个被低估的风险量级搬进第二个区。

---

## 五、台账缺口（顺带盘出，只登记）

本族三条自 09-23 起**从未进待人工台账**：`docs/insights/drain-20260923-pending-human.md`（现值 196 行表行、最大行号 254）里 `l923-06`／`learn-shown-writeorder`／`写序`／`曝光`／`recommendation_shown` 相关命中**只有 1 行**，即 254 行本身在讲 l927-36 的重派处置。⇒ 三条只活在 `done/l923-06.result.md` 遗留问题＋设计稿 §八，无人按台账追踪，结果就是 §一/§四 看到的"被写位单蚕食掉半条而无人纠偏"。台账 223 行另有一条同族在册项值得一起看：「learning 重复点击＝重复计分（`attempts`／`learning_events` 无任何 key/dedupe 列、真幂等只在状态表与成就层）」——它与 A3 是同一个"要不要给事件表加幂等键"的问题，只是打在判分层。

---

## 六、本单作废／订正（必填栏的正文）

1. **作废**：初读时把设计稿 §三 的 A3 字面形态（"对 rid 建唯一索引＋`INSERT OR IGNORE`"）当成可行方案来盘点影响面。读完 `dashboard.py:253`／`:481` 与 `judge.py:166-181` 才发现三腿共用同一个 rid，实测建索引当场 `IntegrityError` ⇒ A3 只剩"部分索引"一种可批形状，§三 整节据此重写。
2. **订正档内表述（不改档）**：「故障帧最多 1 条空 rid 点击」（`done/l923-06.result.md` 遗留 1 与设计稿 §八 待裁决 1）不是上限，真上限＝本帧失败条数（单区 ≤5／≤3，两区一帧合计 ≤8）。见 §2.1.2。
3. **订正自己的一次读数**：先用 `grep -c "^|"` 数索引表条目得 **138**，那是把表头与分隔行算进去了；按索引件档头指定的原式 `grep -c '^| docs/insights/'` 复算才是 **136**。下文一律用 136。

---

## 七、复算命令（cwd `D:\code\learning-system`，python 类一律带 `PYTHONIOENCODING=utf-8`）

① 盘态与本档体积：
`git rev-parse --short HEAD && git status --porcelain | wc -l` → `0f0b39a`／`0`（写完本档后应为 `1`）
`wc -l -c docs/insights/l927-36-funnel-a2a3.md`

② 两区形态行号：
`grep -n "for rank, it in\|\.add(pid_key)\|impressions_key\[\|emit_event(\"recommendation\|except Exception\|navigate_to_problem(it\|reported" ui/pages/dashboard.py` → 曝光 `:211/215/218/221/224` 与 `:429/454/456/457/460`，点击 `:246/250/258/259/261/262` 与 `:476/479/486/490`

③ rid 公式与每帧条数：`sed -n '19,22p' ui/pages/dashboard.py`；`grep -n "recommend(n=5)\|cross_recommend(n=3)" ui/pages/dashboard.py` → `:171`／`:418`

④ DAO 侧现值：`grep -n "def emit_event\|def recommendation_funnel\|CREATE TABLE IF NOT EXISTS learning_events\|CREATE INDEX IF NOT EXISTS idx_events" core/progress.py` → `:547`／`:588`／`:611`／`:116`／`:128-130`／`:139`

⑤ 唯一索引缺位与调用点半径：
`grep -rn "\.emit_event(" --include=*.py ui/ core/ | wc -l` → `12`
`grep -rnE "[A-Za-z_]+ *= *[a-z_]+\.emit_event\(" --include=*.py ui/ core/ | wc -l` → `0`
`grep -n "dedup via meta table" ui/pages/path.py` → `:203`／`:212`

⑥ 本机库只读现取（**零写**，用 `mode=ro&immutable=1`；库 `journal_mode=delete`、122,880 B）：
`PYTHONIOENCODING=utf-8 python -c "import sqlite3;g=lambda s:sqlite3.connect('file:D:/code/learning-system/data/progress.db?mode=ro&immutable=1',uri=True).execute(s).fetchone()[0];print('total',g('SELECT COUNT(*) FROM learning_events'));print('shown',g(\"SELECT COUNT(*) FROM learning_events WHERE event_type='recommendation_shown'\"));print('clicked',g(\"SELECT COUNT(*) FROM learning_events WHERE event_type='recommendation_clicked'\"));print('completed',g(\"SELECT COUNT(*) FROM learning_events WHERE event_type='recommendation_completed'\"));print('null_payload',g('SELECT COUNT(*) FROM learning_events WHERE payload_json IS NULL'))"`
→ `total 81`／`shown 10`／`clicked 0`／`completed 0`／`null_payload 19`
重复组普查（A3 乙案的硬前置）：`SELECT json_extract(payload_json,'$.recommendation_id') rid, COUNT(*) n FROM learning_events WHERE event_type='recommendation_shown' GROUP BY rid HAVING n>1;` → 本机 **0 行**

⑦ A3 两形态探针（**纯 `:memory:`，不落任何文件**；三腿共用 rid＋两条空 rid clicked 的最小重现）：
建表照 `core/progress.py:116-127`，依次插 `recommendation_shown(rid)`／`recommendation_clicked(rid)`／`recommendation_completed(rid)`／二次 `shown(rid)`／两条 `clicked(rid='')`，然后
`CREATE UNIQUE INDEX ux_all ON learning_events(json_extract(payload_json,'$.recommendation_id'))` → 实测 `sqlite3.IntegrityError: UNIQUE constraint failed`
`CREATE UNIQUE INDEX ux_shown ON learning_events(json_extract(payload_json,'$.recommendation_id')) WHERE event_type='recommendation_shown'` → 实测**可建**；此后二次曝光 `INSERT OR IGNORE` 的 `(rowcount,lastrowid)=(0,1)`、空 rid 第 2 条 `(0,…)`
全表形态若先建成：同 rid 的 clicked／completed 均 `rowcount=0`（两腿被吞），落库行数 `shown=1/clicked=1/completed=0`，第 2 条空 rid clicked 也被吞。
历史有重复行时连部分索引也 `IntegrityError`（实测）。

⑧ 两条已入库单的归属（**判归属用 claims 单号，别用作者名**，w85 §A.3）：
`grep -n "l923-07\|l927-37" D:/code/zcode-bridge/logs/claims.log | grep -v "l927-3[0-6]"` → `l923-07 done 09-23T02:13`（写序未动）＋ `l927-37 note 09-28T13:17`（`e9a1606`，🔴 人工项·主班不签）

⑨ 在册看守与闭合哨兵现值：
`grep -c "^def test_" tests/test_dashboard_event_failures.py` → `25`
`grep -n "^def test_recommendation" tests/test_dashboard.py` → `:97/:109/:120/:135/:154`
`PYTHONIOENCODING=utf-8 python -m pytest tests/test_dashboard_event_failures.py tests/test_dashboard.py tests/test_insights_index_closure.py -q` → **49 passed**（本档落盘前）
`ls docs/insights/*.md | wc -l` → `136`；`grep -c '^| docs/insights/' docs/insights/learn-insights-index-20260918.md` → `136`；C 与重复均空 ⇒ 现值闭合
