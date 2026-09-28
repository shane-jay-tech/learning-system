# learning＋kaoyan 在册红归因台账（l927-57，2026-09-29 05:4x）

- 任务：`zcode-bridge/done/l927-57.task.md`（原 inbox 件，本班收口时已移 done）｜cwd＝`D:\code\learning-system`
- 执行班：`qoder-executor-20260929-0528-learn64`（Qoder 执行班；卷宗 frontmatter 的 `model: flash` 仅投递意向）
- 性质：**只汇编、零消红**（完成标准③）。kaoyan 侧**只读**：零写入、零移件、零 add；learning 侧零生产码／零测试判据改动
- 盘态：learning HEAD `93fd384` ｜ kaoyan HEAD **开工时 `b91006f`（05:20）→ 收口时 `713c74a`（05:40:53，兄弟班/主班把 k927-120/121/122 三枚 docs 入库）**，**本班未做任何 git 写**；脏项数随之由 153 → **150**（`scripts` 88／`docs` 30／`src` 14／`tests` 12／`data` 2／其它 4），系前手消费者 `dsh-exec-20260929-0055` 在途件
- ⚠️ HEAD 中途挪动对本台账**无影响**，已复核：`git log fddbc89..713c74a -- tests/ src/ scripts/ package.json` 仍为 5 条，且 K1–K7 与 k921-01 五件所在文件在该区间**零提交**（`git log fddbc89..HEAD -- <十枚点名文件>` 输出空）⇒ §三 的「红名集对 HEAD 成立」推断在新 HEAD 上同样成立
- ⚠️ 本班**未跑任何全量套件**（learning 全量约 127 s、kaoyan 全量 TS 2030 例）；全部读数为**定向点名件**，`PYTHONIOENCODING=utf-8` 已带
- ⚠️ 兄弟班 `qoder-executor-20260929-0522-kaoyan116` 此刻仍在 kaoyan 写产出档（k927-120/121/122，末条 done 05:38）⇒ 本班 kaoyan 读数为**单次定向**，主班复跑时若该班未完，读数可能因并发漂移

---

## 一、一页清单（供主班排消红；共 15 行 ≥ 完成标准①的 8 条）

| # | 侧 | 红名（file:line） | HEAD 版 | 工作树版 | 归因 | 归属／消红口径 |
|---|---|---|---|---|---|---|
| K1 | kaoyan TS | `corpus-index-invariant.test.ts:237` | 🔴 红 | 🟢 绿 | **在途覆盖**（k927-26 已修未入库） | 产物重建：`data/corpus-sentence-index.json` HEAD `builtAt 2026-09-21T10:45:08.920Z / hitWords 251` → 工作树 `2026-09-28T13:20:58.741Z / 287`。**须与产物同笔入库**，否则 HEAD 恒红 |
| K2 | kaoyan TS | `corpus-index-invariant.test.ts:264`（有牙自检 2） | 🔴 红 | 🟢 绿 | **在途覆盖**，同 K1 根 | 与 K1 同笔（同一产物） |
| K3 | kaoyan TS | `corpus-index-invariant.test.ts:310`（有牙自检 3c） | 🔴 红 | 🟢 绿 | **在途覆盖**，同 K1 根 | 与 K1 同笔（同一产物） |
| K4 | kaoyan TS | `english2-2016-option-order.test.ts:59`（Q30 `usable_for_exam`） | 🔴 红（期望写死 `'yes'`） | 🟢 绿（期望订正为 `'no'`） | **在途覆盖**（`tests/english2-2016-option-order.test.ts` 属 153 脏项之一） | ⚠️ 消红法＝**改测试期望**，依据 9/13 用户拍板＋9/20 人工收口只落 `correct_answer`/`answer_audit_status`。**涉题库数据语义，判定留人工**，本班只登记不改 |
| K5 | kaoyan TS | `mobile-pwa.test.ts:48`（`production launcher can skip unchanged builds`） | 🔴 红（陈旧字符串期望 `/kaoyan-build-inputs\.sha256/`） | 🟢 绿 | **在途覆盖**（期望跟随 `1f96592` 一族构建指纹重构） | 随 k927-26 入库即消 |
| K6 | kaoyan TS | `politics-daily-choice-mix.test.ts:72-92`（两条同根） | 🔴 红（`SQLITE_ERROR: no such column passage_text`） | 🟢 绿 | **在途覆盖**（夹具建表补 `passage_text TEXT DEFAULT ''`） | 夹具缺列，非生产缺陷；随 k927-26 入库即消 |
| K7 | kaoyan TS | `practice-weighted-pick-wiring.test.ts:94`（test 起于 `:79`） | 🔴 红 | 🔴 **仍红** | **自漂移按预言兑现（非回归）** | 本班实测 `actual: 9 / expected: 2`；夹具 `:87 answers.created_at='2026-09-20 03:00:00'` 绝对日期 ⇒ 逐日 +1（k924-21 于 09-25 读 5，本班 09-29 读 9，**斜率与预言逐日吻合**）。文件在工作树**未被触碰**⇒ HEAD 与工作树同字节、两侧同红。修法属 **k921-67** 负责人改判面（相对日期化夹具），k927-26 已显式转介未修 |
| K8 | kaoyan TS | 在册红全集规模本身 | 现值＝**8 条**（非卷宗锚点的 7 或 5） | 现值＝**1 条**（K7） | **锚点已过期**（见 §四.1） | 主班排期请用 §四.1 的现值口径 |
| P1 | kaoyan py | unmark-orphan 族「`PYTHONIOENCODING=utf-8` 致 10 errors」 | 🟢 绿 | 🟢 绿 | **已修未刷** | 修它的单号＝**k923-25**，commit **`a18fe76`**（`test(kaoyan): unmark-orphan 族 6 处 subprocess 调用双侧钉死编码（3 件）`）。本班 A/B 实测：带 env 与不带 env 各 **12 tests OK rc=0** ⇒ k922-42 遗留 2 的敏感性问题**已不存在**，其「另开单根治」建议应作废 |
| R1 | kaoyan TS | `review.test.ts:263`（`completion_target` 5 vs 7） | 🟢 不在红名集 | 🟢 实测绿 | **已修未刷** | 修它的单号＝**k923-08**（免修名单核销），生产侧根因＝**pd03 归一**，入库件 **commit `86213f3`**（`src/lib/planner.ts` 改调 `readingRoutineCompletionTarget`）。⇒ **`k927-107` 消红单的目标红已不存在**，而该单**至今仍在 inbox、claims.log 零认领记录**（见 §四.3） |
| R2 | kaoyan TS | `review.test.ts:272`（k921-44 同族钉子） | 🟢 | 🟢 | **已修未刷**，同 R1 | k927-107 的「顺带核 :272 是否同族」问题：**同族且同已修**，无需再处理 |
| L1 | learning | `test_insights_index_closure.py::test_闭合等式_A等于B_且C为空_且无重复` | 🟢（HEAD A==B） | 🔴 **2 failed 之一** | **在途覆盖（本班自己造成）** | 缺项＝`['docs/insights/l927-54-note.md']`；落 l927-57 台账后 **A 领先 B 2** ⇒ 主班代登索引即消 |
| L2 | learning | `test_insights_index_closure.py::test_新档漏登记必红_改名必红_有牙自检` | 🟢 | 🔴 **2 failed 之二** | 同 L1（同根） | 同笔：索引代登＋两枚产出档 |
| L3 | learning | `test_sql_roworder_fragile.py::test_多行SQL题行序全部承重` | `xfail(strict=True)` | 同 | **预期红（在册 XFAIL 桩）** | 现状计入 `2 xfailed`（非红）。红条件＝「命中集合清空 ⇒ XPASS 转红」；届时**删桩并回写** `docs/insights/learn-sql-roworder-census-20260922.md`。**禁令：本班未撤桩**，主班亦勿放宽断言 |
| L4 | learning | `test_paths_order_consistency.py::test_路径内milestone顺序与语言页顺序一致` | `xfail(strict=True)` | 同 | **预期红（在册 XFAIL 桩）** | 真倒置 2 处（`python_advanced` p4/p5），属规划域（重排 yaml 或加 `order:` 字段）⇒ **写单，非消红单**；同样未撤桩 |

> **合计**：需排期的真红＝**1 条**（K7，转介 k921-67）；等入库即消＝**6 条**（K1–K6，须与 k927-26 四文件＋一产物同笔）；已修待刷档＝**3 条**（P1/R1/R2）；learning 索引代登即消＝**2 条**（L1/L2）；预期红不动＝**2 条**（L3/L4）；口径行 1 条（K8）。

## 二、learning 侧在册现状（非红项，认路线索）

- 全量在 HEAD `93fd384` 由主班 05:2x 测为 **1206 passed / 7 skipped / 2 xfailed，rc=0** ⇒ **HEAD 零真红**。本班未复跑全量（禁令），只跑定向：`test_paths_reconcile + test_paths_coverage + test_content_thin_topic_p0` ＝ 17 passed（l927-54 证据⑨）；`test_sql_roworder_fragile + test_paths_order_consistency + test_readme_version_gate` ＝ **5 passed / 2 xfailed，rc=0**。
- 7 skipped **不是红**：cpp 4 例（`:16/:27/:34/:44`）＋ r 3 例（`:13/:19/:25`），成因见 `docs/insights/l927-51-skip7-handoff.md`——cpp 侧是 `D:\tools\mingw64\bin` 缺 `g++.exe`/`ld.exe` 两枚别名（本体在位），r 侧盘上无件须 winget 装；须人工放行装机。
- 严格 XFAIL 桩**共三处文件被 grep 命中，但现役只有两枚在册**：第三处 `tests/test_readme_version_gate.py` 的 xfail 桩**已由 l927-46 删除并转常驻绿门禁**（该文件 `:20`/`:27` 自述），其 docstring 里「XPASS 转红」是**退役说明语态**。⇒ 提示词写「strict-XFAIL 两枚」与盘上一致（现役两枚），但 grep 会命中三处，排期时别把 readme_version_gate 当红。

## 三、双报口径说明（为什么 kaoyan 侧「HEAD 版」多为推导而非复现）

- 本班在 kaoyan **只执行三类动作**：`git -C D:/code/kaoyan-system {status,log,ls-tree,show,diff}`、`grep`、`npx tsx --test <点名文件>`／`python -m unittest <点名模块>`。**零写入、零移件、零 add、零 git 写操作**。
- 「工作树版」＝**实测**（见 §五 命令与读数）。「HEAD 版」＝**文档坐实＋静态推断**：k924-21 于 `fddbc89` 跑出的全量红名集，到 `b91006f` 之间 5 枚提交只触及 `backup-auto / backup-prune-exempt / chain-parity-columns / migration-registry-consistency` 四件测试（`git log fddbc89..HEAD -- tests/ src/ scripts/ package.json`），**未触及 K1–K7 所在任何文件**（`git log fddbc89..HEAD -- <五文件＋产物>` 输出空）⇒ 红名集对 HEAD 成立。
- ⚠️ **未坐实项（如实标注）**：严格的 HEAD 复现须干净检出（`git stash`/`checkout`＝git 写，本班禁），故 K4/K5/K6 的「HEAD 红」是**由工作树脏态反推**（三文件均在 153 脏项内、期望/夹具改动尚未入库）；R1/R2 与 k921-01 另三条的「HEAD 绿」依赖 k924-21 全量读数＋文件零改动，**未做 HEAD 直跑**。若主班要坐实，唯一无写路径＝`git show HEAD:<file>` 导出到 kaoyan **之外**的沙盒再跑（缺 node_modules，多半跑不起来）。

## 四、否证与订正（卷宗／提示词 vs 盘上）

1. **卷宗「7＋5 族」两个锚点都已过期，且互不自洽**。k922-42 的 7 fail 出自 1664 例规模（09-22），k921-01 的 5 fail 出自 1417 例规模（09-21）；现役权威口径＝**k924-21（09-25 22:1x，`npx tsx --test "tests/*.test.ts"` → 2030 例 / 2022 pass / 8 fail）**。两枚卷宗锚点的名单与 k924-21 的 8 条**交集为空**（k921-01 五条已全部转绿、k922-42 的 review/plan/choice 族被 k924-21 重新拆分为 K1–K7）。⇒ 按卷宗字面「7＋5＝12 族」汇编会得出一张**盘上不存在的红单**；本台账以 8 条现值＋3 条已修未刷为准。
2. **`complete-evidence-task.test.ts:103`／`english-reading-group.test.ts:150`／`plan-get-readonly.test.ts:26`／`:64`／`review.test.ts:263`**（k921-01 全 5 条）：本班定向实跑四文件 → **`ℹ tests 55 / pass 55 / fail 0`，rc=0** ⇒ **五条全绿，无一条在册**。四文件在工作树**均未被改动**（`git status --porcelain -- <四文件>` 空）⇒ 绿不是本班或前手改测试造出来的。
3. **k927-107 未执行，「已修一条」的说法不成立**。`k927-107.task.md` 仍在 `D:\code\zcode-bridge\inbox\`，`grep -c k927-107 claims.log` ＝ **0**，`outbox`/`done` 无该 id 的 result ⇒ **它一条也没修**。它要消的那条（`review.test.ts:263`）实际早由 **pd03（commit `86213f3`）＋ k923-08 核销** 修掉，k924-21 §四 已记「该红已不存在」⇒ 属**已修未刷**：修它的单号与 commit 如上，而卷宗锚点 `k922-128`「带 `KAOYAN_COMPLETION_SPEC_OFF=1` 复跑即绿」的开关**已零消费方**（k924-21 §五.1 已把该指引改写为退役说明）。
4. **k922-42 遗留 2（py 编码敏感性）已被 k923-25（`a18fe76`）根治**，本班 A/B 否证成立（P1 行）。该遗留的「建议另单给 unmark-orphan 显式 `encoding='utf-8'`」应作废——**已经做了**。
5. 卷宗路径不符：锚点写 `zcode-bridge/done/...` 相对 cwd（`D:\code\learning-system`）不存在，真身 `D:\code\zcode-bridge\done\`（三枚 task＋result 均在位，已复核）。
6. 横幅与盘上相符处（确认非否证）：learning 全量 `1206/7/2 rc=0`、strict-XFAIL 两枚、kaoyan 153 枚在途脏项、`PYTHONIOENCODING=utf-8` 对 learning 定向件无害——四条前提均实测为真。

## 五、复现命令包（主班可直接复跑；均为定向，零全量）

```bash
# —— kaoyan 侧（cwd=D:\code\kaoyan-system；本班未做任何 git 写）——
git -C D:/code/kaoyan-system rev-parse --short HEAD            # 本班开工 b91006f → 收口 713c74a（兄弟班 docs 提交，非本班）
git -C D:/code/kaoyan-system status --porcelain | wc -l        # 153（开工）→ 150（收口，因 3 枚 docs 入库）
git -C D:/code/kaoyan-system status --porcelain -- tests/      # 12 项（5 M ＋ 7 ??）
git -C D:/code/kaoyan-system log --oneline fddbc89..HEAD -- tests/ src/ scripts/ package.json   # 5 条，均不触及 K1–K7 文件
git -C D:/code/kaoyan-system show HEAD:data/corpus-sentence-index.json | grep -oE '"builtAt"|"hitWords": *[0-9]+'   # 251
PYTHONIOENCODING=utf-8 npx tsx --test tests/corpus-index-invariant.test.ts tests/english2-2016-option-order.test.ts \
  tests/mobile-pwa.test.ts tests/politics-daily-choice-mix.test.ts tests/practice-weighted-pick-wiring.test.ts
  # → ℹ tests 31 / pass 30 / fail 1（唯一红＝K7）
PYTHONIOENCODING=utf-8 npx tsx --test tests/review.test.ts tests/complete-evidence-task.test.ts \
  tests/english-reading-group.test.ts tests/plan-get-readonly.test.ts
  # → ℹ tests 55 / pass 55 / fail 0（k921-01 五条全绿）
PYTHONIOENCODING=utf-8 npx tsx --test tests/practice-weighted-pick-wiring.test.ts
  # → AssertionError「最近作答距今按 answers.created_at 实算」 actual 9, expected 2（:94:10）
PYTHONIOENCODING=utf-8 python -m unittest tests.test_unmark_orphan_wrongq tests.test_unmark_orphan_backup_guard tests.test_unmark_orphan_wrongq_apply   # 12 OK rc=0
  python -m unittest tests.test_unmark_orphan_wrongq  tests.test_unmark_orphan_backup_guard  tests.test_unmark_orphan_wrongq_apply                   # 12 OK rc=0（无 env 对照同绿）
# 局限：K1–K6 的 HEAD 侧红**未直跑**（须干净检出＝git 写，禁）；上述均为工作树读数。

# —— learning 侧（cwd=D:\code\learning-system）——
PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q        # 2 failed, 1 passed（L1/L2，本班产出件未登索引）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_sql_roworder_fragile.py tests/test_paths_order_consistency.py tests/test_readme_version_gate.py -q -rxX
  # → 5 passed, 2 xfailed（L3/L4 为 XFAIL 非红；readme_version_gate 的 xfail 桩已退役为常驻绿）
ls docs/insights/*.md | wc -l; grep -c '^| docs/insights/' docs/insights/learn-insights-index-20260918.md   # 132 vs 130
```

## 六、消红排序建议（**材料，非判定**）

1. **最高优先**：把 **k927-26 的在途批**（`tests/{english2-2016-option-order,mobile-pwa,politics-daily-choice-mix}.test.ts` ＋ `data/corpus-sentence-index.json` ＋ 其产出档 ＋ 索引行）**同笔入库**——一次性消 K1–K6 共 6 条。⚠️ K4 涉 Q30 数据语义（改期望 vs 补收口），本班**未判定**，入库前请人工确认改期望一侧仍是 9/13 拍板口径。
2. **learning 侧**：主班代登 insights 索引两行（l927-54＋l927-57）⇒ L1/L2 同笔即消。
3. **文档刷新型（零代码）**：k922-42 遗留 2、k921-01 五条清单、k922-128 的 `KAOYAN_COMPLETION_SPEC_OFF` 指引——三处 done 档不可回改，请**台账加注**「已由 k923-25/`a18fe76`、pd03/`86213f3` 修掉」，避免下波再次照旧名单排消红（本波 l927-57 就差点这样干）。
4. **`k927-107` 建议撤单或改判**：其目标红已不存在。若仍要完成「双口径用例」，需先重定义——现在 `:263` 无红可消，写它等于给绿态加桩（属写单，须放行）。
5. **K7（唯一真在册红）**：转介 **k921-67**，修法＝夹具绝对日期改相对（`datetime('now','-2 day')` 一类）。属改测试件，另批放行。
6. **L3/L4 不动**：strict-XFAIL 桩按纪律保留（撤桩＝掩盖判分面跨层矛盾，且 L3 撤桩前须先做判分口径的人工裁决）。

## 七、遗留

- 工作树版绿／HEAD 版未直跑（见 §三），主班若要 HEAD 直跑需自行处理检出与 node_modules。
- kaoyan 153 枚在途脏项中 `scripts/` 88 枚未纳入本班红名集核对范围（本班只核 `tests/` 12 枚＋K1 产物），若前手批入库带来新红，需另单复认。
- 兄弟班 kaoyan116 仍活跃，本班 kaoyan 读数为单时点快照。
- 本班未跑 learning 全量，全量现值沿用主班 05:2x 读数。

## 八、索引登记建议（learning 索引件由主班单点写，本班未自登）

本档落盘后实测：`ls docs/insights/*.md | wc -l` ＝ **132**、`grep -c '^| docs/insights/' learn-insights-index-20260918.md` ＝ **130**、`pytest tests/test_insights_index_closure.py -q` ＝ **2 failed / 1 passed，rc=1**（缺项含本档与 l927-54-note.md）。建议索引行（五列形状同实表）：

```
| docs/insights/l927-57-reds-ledger.md | 20260929 | learning＋kaoyan 在册红归因台账（只汇编零消红，15 行）：🔴 否证卷宗「7＋5 族」两锚点——现役权威口径＝k924-21（09-25，2030 例/8 fail），k921-01 五条本班定向实跑全绿（55 pass/0 fail）；真在册红仅 1 条＝practice-weighted-pick-wiring.test.ts:94 自漂移按预言兑现（实测 actual 9 vs expected 2，斜率逐日 +1 与 k924-21 预言吻合，转介 k921-67）；6 条＝k927-26 已修未入库（含 corpus 产物 builtAt 251→287 的 HEAD/工作树双报）⇒ 同笔入库即消；3 条已修未刷＝review.test.ts:263/:272（pd03 commit 86213f3＋k923-08 核销）与 kaoyan py 编码敏感性（k923-25 commit a18fe76，A/B 实测带 env 与不带 env 均 12 OK）；🔴 k927-107 一条也没修——仍在 inbox、claims 零认领，且其目标红早已不存在，建议撤单或改判；learning 侧 2 条索引哨兵红系本班两枚未登索引产出件（中间态非回归），strict-XFAIL 两枚 L3/L4 未撤桩；kaoyan 全程只读零写零 add，未跑任何全量套件（l927-57，2026-09-29） | 待主班代登索引＋代提交 | 0 |
```

**必须同笔集合（本单）**：本档 ＋ l927-54 的两枚 ＋ 主班的索引代登行（三枚产出件同批，索引补两行后哨兵回 3 passed）。
