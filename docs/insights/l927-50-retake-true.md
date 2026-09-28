# retake_intent「兼容旧布尔 True」口子两案裁决材料（l927-50，只出材料 · 零生产码改动 · 零 git 操作）

> **卷宗**：`zcode-bridge/inbox/l927-50.task.md`。上游依据＝`zcode-bridge/done/l923-14.result.md` 遗留问题 1：
> 「**兼容 `True` 是一处刻意的口子**：若主班认为「旧协议一律判失效」更可取，改法是 `_retake_intent_state` 里把
> `raw is True → "expired"`，代价是**必须同改** `tests/test_diagnostic_ui_branches.py:91/98` 与 `TestRouteTruthTable`
> 的 True 行（两个文件都超出本单产出）⇒ 本单按「不外溢改动」选了兼容。」
> **本班性质**：只读位裁决材料班（shift `qoder-executor-20260929-0500-learn63`，2026-09-29 05:0x 全部读数现取，
> 仓 HEAD `31840db`、`git status --porcelain` 行数 0）。**判定留人工，本班只出材料＋推荐。**
> 🔴 **开工即发现锚点有一处可复算的否证**（见 §三-3）：l923-14 预告的「必须同改 ui_branches:91/98」实测**不成立**，
> 两案的真实改动外溢面比在册档案里写的更小。

## 一、锚点与前提复核（每条都改成命令实测）

| # | 前提 | 现取读数 | 取数命令（cwd `D:/code/learning-system`） | 判定 |
|---|---|---|---|---|
| 1 | 兼容口仍在原处、语义未变 | `ui/pages/diagnostic.py:43-44` 逐字 `if raw is True:` / `return "active"`；TTL 常量 `:21`＝`600.0` | `grep -n 'if raw is True' -A1 ui/pages/diagnostic.py` | ✅ 锚点有效（行号现值 :43，非 l923-14 时的 :33） |
| 2 | 「生产码已不再写 True」 | 生产侧 `retake_diagnostic` 字面站点 4 处：读 `:40`、消费 pop `:54`、提交复位 `:103`＝`False`、置位 `:141`＝`_now()` ⇒ **写 True 的站点 0 处** | `grep -rn 'retake_diagnostic' ui core app.py launcher.pyw scripts` | ✅ 前提成立 |
| 3 | 全仓引用面 | 排除 `tmp/`、`.git` 后 `retake_diagnostic` 命中 **31 行 / 3 个文件**：`tests/test_diagnostic_retake_state.py` 23、`ui/pages/diagnostic.py` 5、`tests/test_diagnostic_ui_branches.py` 3；**docs/ 零命中**（该口子在文档侧无在册表述，只有 l923-14 的 done 档） | `grep -rn --exclude-dir=tmp --exclude-dir=.git --exclude-dir=__pycache__ "retake_diagnostic" . \| awk -F: '{print $1}' \| sort \| uniq -c` | ✅ 影响面天然封在 3 件内 |
| 4 | 「旧数据」到底存不存在（关键） | 该键**只活在 Streamlit `session_state`，零磁盘持久化**：① `data/`＋`content/`＋`logs/`＋`assets/` 里搜 `retake` → rc=1 零命中；② `progress.db` 8 张表（attempts/problems_status/meta/review_state/rubric_scores/learning_events/schema_meta＋sqlite_sequence）**无会话表**，`meta` 现有键只有 5 个（achievements_earned／ai_pulse_monthly／ai_pulse_quarterly／all_mistakes_cleared／security_notice_seen）；③ 全仓 py 无 `save_session`／`SESSION_FILE`／`session_state` 序列化（grep rc=1） | `grep -rln "retake" data content logs assets`；`PYTHONIOENCODING=utf-8 python -c "import sqlite3;c=sqlite3.connect('file:data/progress.db?mode=ro',uri=True);print([r[0] for r in c.execute(\"select name from sqlite_master where type='table'\")]);print([r[0] for r in c.execute('select key from meta')])"` | 🔴 **「旧数据形态」仅存在于内存会话与测试夹具，盘上零存量** ⇒ 任何一案都不涉及数据迁移面 |
| 5 | 现役启动方式决定「旧会话能否活到新代码里」 | `start.bat:27` 用 `--server.fileWatcherType none` 起 app ⇒ 生产路径**不热重载**：进程要么整段跑旧代码（旧代码写 True、旧代码读 True，自洽），要么重启（重启即新 session、`session_state` 清空）。真正能把 True 递到新代码手里的只有**开发模式手启 `streamlit run app.py`（热重载，launcher.pyw:14 提及）** | `grep -n "streamlit run" start.bat launcher.pyw` | ⚠ 兼容口的现实服役场景＝开发者热重载窗口，非生产用户 |
| 6 | True 写端的历史窗口 | `git log -S 'st.session_state["retake_diagnostic"] = True' -- ui/pages/diagnostic.py` → 两笔：`b14a136`（2026-07-14，建仓基线，写端在此）→ `1bafa0c`（2026-09-23，l923-14 移除）⇒ 存活 **71 天**，移除至今 **6 天** | `git log --oneline --date=short --pretty='%h %ad %s' -S '...= True' -- ui/pages/diagnostic.py` | ✅ 时间窗可复算；因 §一-4（无持久化）该窗口**不留存量** |
| 7 | 定向基线（未挂探针） | `tests/test_diagnostic_retake_state.py`＋`test_diagnostic_ui_branches.py`＋`test_diagnostic.py` 三件合跑 **43 passed / 0 failed in 1.98s**（与 l923-14 收工读数同值，未漂） | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_diagnostic_retake_state.py tests/test_diagnostic_ui_branches.py tests/test_diagnostic.py -q` | ✅ 基线可复算 |
| 8 | 索引闭合哨兵基线（本单要落新档，先取改前值） | `tests/test_insights_index_closure.py` **3 passed**；A（磁盘 `docs/insights/*.md`）＝**127**、B（索引 `^| docs/insights/` 行）＝**127** | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q`；`ls docs/insights/*.md \| wc -l`；`grep -c '^| docs/insights/' docs/insights/learn-insights-index-20260918.md` | ✅ 本档落盘后 A=128/B=127 ⇒ 哨兵必红，见 §五「必须同笔」 |

## 二、旧数据形态统计（完成标准①：先命令后数字）

统计口径＝「`st.session_state["retake_diagnostic"]` 能取到的值形态 × 谁能造出来 × 各形态计数」。

| 形态 | 现网生产写端（计数） | 测试夹具造点（计数） | 造史（git） | 盘上存量 |
|---|---|---|---|---|
| 键不存在 | 1 处（`:54` pop） | 真值表「未设过该键」行 1 | 一直有 | **0**（§一-4） |
| `None` | 0 | 真值表 1 行 | — | 0 |
| `False` | 1 处（`:103` 提交复位） | 断言 3 处（`retake_state:226`、`ui_branches:98` 等） | 一直有 | 0 |
| **`True`（本案主角）** | **0 处** | 写站 **3 处**：`retake_state:220`、`:232`、`ui_branches:91`；行为依赖格 **3 格**：真值表 `(SAVED_RESULT,True,"quiz")`:129、参数化 `结果页分支后意图键的状态[True]`:146、四态单测 `(True,"active")`:319 | 生产写端存活 71 天（`b14a136`→`1bafa0c`） | **0** |
| 正浮点时间戳（现行协议） | 1 处（`:141` `_now()`） | `fresh`/`edge`/`stale` 三态夹具 | 2026-09-23 起 | 0 |
| 脏值（不可解析） | 0 | `garbage`＝`"昨天点过"` 1 处（`:98`）＋真值表 2 格 | — | 0 |
| 「像数字但不是时间戳」的边界形态 | 0 | 现役夹具**未覆盖**（本单探针补测：`0.0`、`-1.0`、`"1758000000"`、`"1"`、`["x"]`、`{"k":1}` 共 6 形） | — | 0 |

三条由此表直接落下的事实（都是本案的地基，不是解释）：

1. **兼容口只对「对象身份 `is True`」生效，不对「所有真值」生效**：`0.0`/负数/数字串/`"1"` 走 `float()` 分支判 expired，脏串/容器判 invalid，两案同判（§三矩阵一，15 形里只有 True 一形变）。
2. **测试夹具是兼容口当今唯一消费者**：生产写 True 站点 0，盘上存量 0 ⇒ 「维持兼容」保护的既不是用户数据也不是历史库行，只是 3 格测试真值。
3. §一-3 已证影响面封闭：全仓只有 3 个文件提到该键，两案的改动面都能当场列尽（§四）。

## 三、行为差异矩阵（完成标准①的下半：两案差在哪，实测不是推理）

探针：`tmp/l927-50/state_matrix.py`（B 案＝对真源码 `return "active"`→`return "expired"` **单行字面替换后 exec**，
`assert count==1` 保证除该处外两案逐字相同；留痕 `tmp/l927-50/matrix.log`）。
路由矩阵驱动的是真 `render_diagnostic()`，`_render_quiz`/`_render_result` 换成记账桩，冻结 `_now`＝`2026-09-23 10:00:00`。

**矩阵一（判定态，15 形 × 2 案）**：15 个形态里**只有 1 个**判定不同——

| 形态 | A 案（现网） | B 案（True→expired） |
|---|---|---|
| `True` | `active` | `expired` |
| 其余 14 形（含 absent/None/False/fresh/edge/over/stale/0.0/-1/数字串/"1"/脏串/list/dict） | 同判 | 同判 |

**矩阵二（真路由 ＋ 意图键归宿，15 形 × 2 库态 × 2 案＝60 格）**：差异**只有 1 格**——

| 库态 × 形态 | A 案（分支/键归宿） | B 案（分支/键归宿） | 用户侧语义 |
|---|---|---|---|
| 有存档结果 × `True` | `quiz` / 键**留在**（`True`） | `result` / 键被 `pop` | A：旧协议残留会把用户**无限期**按在问卷页（True 无时间戳⇒永不过 TTL），须完整提交一次问卷才挣脱；B：立刻回到已存结果页、键清干净，代价是那次（旧协议形态的）重测请求被**静默丢弃一次** |
| 其余 59 格 | 逐格同值 | 逐格同值 | 含「无结果 × True」两案都走 quiz 且都不清键（`:131` 真值表行两案同绿） |

**矩阵三（现役测试档波及面，实测非纸面）**：挂 B 案插件 `tmp/l927-50/optionb_plugin.py`（`PYTHONPATH=tmp/l927-50 python -m pytest -p optionb_plugin …`，三件合跑）：

| 组 | 读数 | 红名 |
|---|---|---|
| A（现网码，未挂插件） | **43 passed in 1.98s** | — |
| B（挂插件，同三件） | **3 failed, 40 passed in 1.08s**（留痕 `tmp/l927-50/optionb-run.log`） | `TestRouteTruthTable::test_branch_matches_condition[existing2-True-quiz]`（:142）、`TestRouteTruthTable::test_结果页分支后意图键的状态[True]`（:153）、`TestInterruptionResidue::test_意图状态函数四态且只读不写[True-active]`（:330） |

1. 三格红名**全在 `tests/test_diagnostic_retake_state.py` 一枚件内**；`tests/test_diagnostic.py`、`tests/test_diagnostic_ui_branches.py` 零红。
2. 另有 3 处「写了 True 但不依赖兼容口」的夹具（`retake_state:220/:232`、`ui_branches:91`）：它们直接调 `_render_quiz()`，不经过路由判定，提交即写 `False` ⇒ B 案下照绿（实测计入上面 40 passed）。
3. 🔴 **否证锚点一条**：l923-14 遗留 1 写「代价是必须同改 `tests/test_diagnostic_ui_branches.py:91/98`」，实测把 True 判失效后该文件**零红名**（该两行只是把 True 当"重测场景"的气氛值，断言的是提交后复位为 False，与 `_retake_intent_state` 无调用关系）。⇒ 该 done 档不可回改，**请台账加注**；两案的改动外溢面因此比在册口径小一个文件。

## 四、两案矩阵（完成标准②）

| 维度 | 案 A：维持兼容口（`raw is True → active`，＝现状） | 案 B：严格失效（`raw is True → expired`） |
|---|---|---|
| 收益 | ①零改动、零测试同改、零文档义务；②开发模式热重载窗口里，旧会话点过「重新测试」的用户仍能如愿进问卷（意图不被吞）；③l923-14 当初「不外溢改动」的选择无需翻案 | ①消灭「唯一无 TTL 的 active 形态」：`_retake_intent_state` 的契约变成**任何值都有界**，active 只可能来自 TTL 内时间戳；②l923-14 修的那条中断残留（点重测→中途切走→永久停在问卷）在 True 形态上不再可达（§三矩阵二那一格）；③测试真值表回归单一协议，夹具不再靠旧协议气氛值 |
| 成本 | ①一处**永久性**语义例外留在判分面之外的路由判定里，且它兜的形态生产码已写不出来（§二-2）；②契约有洞：docstring 与 `:34` 注释得一直解释「为什么 True 不过期」；③若将来有人（外部件/别的页/调试脚本）写 True，l923-14 修的 bug 原样复发且**不受 600s 保护** | ①测试同改 3 格（§三矩阵三：:129 真值表行翻 `result`、:146 参数化 True 格语义翻、:319 四态单测 `(True,"expired")`）——**都在同一枚测试件**；②源码 docstring `:34-35` 与测试档头注 `:20-22` 两处文本义务（**无断言钉文本**，实测形状桩 `:336-350` 只钉四站点字面与 `!= "active"` 守卫，不钉 True 分支，故不改注释不会当场红，属注释债非测试债）；③开发热重载窗口里的旧 True 意图被静默吞一次（用户再点一次即恢复，可自愈） |
| 风险面 | 低（不动即无风险），但风险是**长尾**的：无界 active 形态 | 低且**有界**：一次改 1 生产行＋3 测试格＋2 处注释；生产用户不可达（§一-4 无持久化、§一-5 生产不热重载） |
| 可逆性 | 天然可逆（什么都不做） | 可逆：单行回退＋3 格回退；因零存量，回退无数据后果 |
| 与红线关系 | 不碰判分口径、不碰答案内容域；`core/diagnostic.py`（判分/存结果）在两案下都**零接触** | 同左；但改路由判定属 `ui/pages/diagnostic.py` 生产码改动，按 CLAUDE.md 需 GPT 独立评审＋主班派写单，**本班不下判定** |

## 五、推荐（完成标准③）

**推荐：案 B（旧协议一律判失效），以「有界化」为唯一理由；若主班优先零改外溢，案 A 也完全站得住——两案实测代价都极小，差异只在一处语义洞。**

理由按权重：

1. **兼容口当今没有受保护的真实对象**：生产写 True 站点 0（§一-2）、盘上存量 0（§一-4）、唯一消费者是 3 格测试真值（§二-2）。它换来的"兼容"收益全在纸面。
2. **它留下的洞恰好是本单上游想修的那条**：§三矩阵二那一格＝「旧 True 把用户无限期按在问卷页」，与 l922-112 建档钉的中断残留同形，只是入口换了个值。案 B 把这个入口封掉，且行为差异实测**仅此一格**（15 形判定 1 变、60 格路由 1 变）。
3. **外溢面比在册档案承诺的小**：l923-14 因预判「要连改两枚超出产出的文件」而放弃 B；实测该预判不成立（§三-3 否证），B 的真实成本＝1 生产行＋1 枚测试件内 3 格＋2 处注释。当年拦路的前提高效已不存在。
4. 案 A 的可辩护点也只有一条，且已被 §一-5 限定：它保的是**开发模式热重载**那一次点击。真要保这个场景，更稳的做法是让夹具与开发态都写时间戳，而不是让生产契约留一个无界分支。

**判据（何时应改判案 A）**——出现任一改推荐方向：① 盘上/会话存储出现 True 形态的真实存量（例如将来给 `session_state` 加持久化）；② 出现无法改的外部写端仍在写 True（第三方页/脚本）；③ 该测试件被要求冻结（B 案要动 `test_diagnostic_retake_state.py` 3 格，若该件进在途禁改名单则 B 不可执行）。

**案 B 落地的最小同改清单**（若主班拍 B，一次入库必须齐）：
`ui/pages/diagnostic.py:43-44`（`return "active"`→`"expired"`）＋ docstring `:34-35` ＋
`tests/test_diagnostic_retake_state.py` 的 :129（期望翻 `result`）、:146-154（True 格语义翻：进结果页且键被 pop）、:319（`(True,"expired")`）＋ 该件头注 :20-22。
本班**未执行**其中任何一项（只读位）。

## 六、必须同笔入库的件 ＋ 待人工

1. **必须同笔**：本产出件 `docs/insights/l927-50-retake-true.md` ＋ `docs/insights/learn-insights-index-20260918.md` 的索引行。
   哨兵基线实测改前 3 passed／A=B=127（§一-8）；本档落盘后实测 **A=128、B=127 ⇒ 2 failed, 1 passed in 0.09s**
   （红的正是 `test_闭合等式_A等于B_且C为空_且无重复` 与 `test_新档漏登记必红_改名必红_有牙自检` 两格，分笔即 HEAD 红），
   由主班代登索引后与产出件同笔入库。**索引件本班未动一字**（纪律：learning 索引件主班单点写）。
   建议索引行文本（列序与表头同型：档路径｜日期｜主题摘要｜状态｜引用数）：

   ```
   | docs/insights/l927-50-retake-true.md | 20260929 | retake_intent 兼容旧布尔 True 口子两案材料：盘上零存量（session_state 无持久化＋progress.db 八表无会话表）＋生产写 True 站点 0＋全仓仅 3 文件引用；B 案用真源码单行替换 exec 实测，15 形判定仅 True 一形变、60 格路由仅 1 格变（有结果×True：quiz/键留 → result/键清），挂插件三件合跑 43 passed→3 failed 40 passed 且红名全在 test_diagnostic_retake_state 一枚件；🔴 否证 l923-14 锚点一条——预告「必须同改 ui_branches:91/98」实测该件零红，done 档不可回改请台账加注。推荐 B（有界化），判据三条；不动生产码、不动桩、不放宽判据（l927-50，2026-09-29） | 待人工（裁决材料选案未拍） | 0 |
   ```

2. **待人工①**：两案拍板（推荐 B）。选 B 属生产码＋测试件改动 ⇒ 需主班另派写单并按 CLAUDE.md 走 GPT 独立评审，本单不代做。
3. **待人工②**：`zcode-bridge/done/l923-14.result.md` 遗留 1 的「必须同改 ui_branches:91/98」需台账加注（§三-3 实测否证）。
4. **待人工③（探针边界，如实说明）**：§三 的 B 案矩阵是**运行时/exec 派生**，不是改码后全量实跑——
   探针局限：①`st` 用自制最小桩（只给 `session_state`），不跑 Streamlit 运行时；②两个渲染函数换记账桩，判的是「走哪支＋键归宿」；
   ③`optionb_plugin` 只包返回值，不改源码文本，故钉源码形状的那支桩（`:336-350`）在两案下同绿，真改码时的注释义务要靠人守。
   主班复跑同源命令（`python tmp/l927-50/state_matrix.py`、`PYTHONPATH=tmp/l927-50 python -m pytest -p optionb_plugin --tb=line -q tests/test_diagnostic_retake_state.py tests/test_diagnostic_ui_branches.py tests/test_diagnostic.py`）**不算独立复算**，
   若要独立读数请在拍板后按 §五 清单真改码跑定向三件。
5. 探针残留：`D:\code\learning-system\tmp\l927-50\`＝`state_matrix.py`、`optionb_plugin.py`、`matrix.log`、`optionb-run.log`。`tmp/` 已 gitignore（`.gitignore:19`），未删未提交。

## 七、复算配方（本档读数取数链）

```bash
cd D:/code/learning-system
# 1 兼容口现值＋四站点
grep -n 'if raw is True' -A1 ui/pages/diagnostic.py
grep -rn 'retake_diagnostic' ui core app.py launcher.pyw scripts
# 2 全仓引用面（31 行 / 3 文件）
grep -rn --exclude-dir=tmp --exclude-dir=.git --exclude-dir=__pycache__ "retake_diagnostic" . | awk -F: '{print $1}' | sort | uniq -c
# 3 盘上零存量：文本面＋库面
grep -rln "retake" data content logs assets
PYTHONIOENCODING=utf-8 python -c "import sqlite3;c=sqlite3.connect('file:data/progress.db?mode=ro',uri=True);print([r[0] for r in c.execute(\"select name from sqlite_master where type='table'\")]);print([r[0] for r in c.execute('select key from meta')])"
# 4 生产启动方式（决定旧会话能否跨码存活）
grep -n "streamlit run" start.bat launcher.pyw
# 5 True 写端历史窗口
git log --oneline --date=short --pretty='%h %ad %s' -S 'st.session_state["retake_diagnostic"] = True' -- ui/pages/diagnostic.py
# 6 两案行为矩阵（判定态 15 形＋路由 60 格）
PYTHONIOENCODING=utf-8 python tmp/l927-50/state_matrix.py
# 7 测试波及面：对照组 → B 案组
PYTHONIOENCODING=utf-8 python -m pytest tests/test_diagnostic_retake_state.py tests/test_diagnostic_ui_branches.py tests/test_diagnostic.py -q
PYTHONPATH="D:/code/learning-system/tmp/l927-50" PYTHONIOENCODING=utf-8 python -m pytest -p optionb_plugin --tb=line -q tests/test_diagnostic_retake_state.py tests/test_diagnostic_ui_branches.py tests/test_diagnostic.py
# 8 索引闭合哨兵（本档落盘后预期红 2 格）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q
```
