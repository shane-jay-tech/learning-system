# 「· 至多」口径联动确认单：HEAD 复点＝**不多余**，据此终结 l924-09 遗留 1 的疑点（l927-44，只读 · 不动桩 · 不动生产码 · 零 git）

> **卷宗**：`zcode-bridge/inbox/l927-44.task.md`（收口时移 `done/`）｜上游＝`zcode-bridge/done/l924-09.result.md`
> 遗留问题 1（🔴「与 `82b45c1`（l924-08『· 至多』）的口径联动——交主班裁」），链条再上是
> `82b45c1`（l924-08，标签侧补标记）→ `e76461b`（l924-09，COUNT 伴生查询实装）→ `c3ac33a`（l923-20，汇总行标下限）→ l922-123。
> **本班**：`qoder-executor-20260929-0345-learn61`，只读位，2026-09-29T03:58–04:0x 读数现取。
> **盘态**：HEAD `18c6d2d`；两文件自 l924-09 入库后**零改动**（`git log -- ui/pages/mistakes.py` 与
> `-- tests/test_mistakes_tabs_contract.py` 的末笔同为 `e76461b`）⇒ 不存在"前人顺手改"导致的联动漂移。
> **红线**：本域是**显示面文案口径**，不涉判分逻辑（判分在 `core/judge.py`／`core/rubric*.py`）；
> 本班**未改任何在册断言、未改生产码、未放宽任何判据**，判定留人工／主班。

## 一、结论（先给可拍板的那句）

**「· 至多」仍不多余 ⇒ 按卷宗走"登记确认档"分支，疑点就此终结；不需要"回退 2 处"清单。**

三条实测依据（全部出自变异探针，跑法见 §四；控制侧 81 passed 证明插件中性）：

1. **三处同屏标记各自独立承重，摘掉任何一处都有在册判据当场红**：
   摘 tab 的「 · 至多」⇒ **9 例红**；摘汇总行的「最近 50 条内」⇒ **12 例红**；摘提示行
   「实际到期共 N 道」⇒ **1 例红**。⇒ 三者**不是同义重复**，而是分属三个 UI 面（标签／汇总行／补充行），
   删任意一处都会拆掉一根判据钉子。
2. **提示闸的严格 `>` 有牙**：把 `due_total > overdue_count` 放宽成 `>=` ⇒ 恰 **1 例红**
   （`test_打满但真数恰等页内条数_查了而不提示`）。⇒ 「真数恰等 50 那一屏没有提示行」不是推测，
   而是被钉住的现状 ⇒ 「· 至多」在**那一屏、那一格**仍独自承担下限语义。
3. **查询闸「打满才查」也有牙**：拆掉它（`if overdue_count == 50:` → `if True:`）⇒ **3 例红**。
   这条决定了**出口 B（标签随真数改口径）的前置代价**：标签要用真数，COUNT 就必须无条件发 ⇒
   先付 3 例（查询闸）＋9 例（标签字面与双向断言）＝**12 例**的账，且属"改在册判据"面。

## 二、订正上游一处措辞（不影响结论，但会误导下一步动作）

l924-09 遗留 1 原句：「……真数恰等 50 的场景里没有提示行，那正是 l924-08 那句标记**唯一**还在独自承担说明义务的时刻」。

- **就 tab 那一格而言成立**，但那一屏其实有**两处**标记在场：汇总行 `:79`「最近 50 条内到期复习 50 道」＋
  标签 `:95`「到期复习 (50 · 至多)」；提示行 `:87` 缺席。⇒ "唯一"应读作"**标签面的唯一**"。
- ⚠ 实操后果：若有人据"唯一"二字去动**汇总行**那段标记，实测会红 **12 例**（§一.1 的 `no_summary_mark`），
  比动标签那一处（9 例）更贵。done 档不可回改 ⇒ 请主班在 l924-09 那行台账加注本条订正。
- 另：l924-09 说的"打满那一屏出现三处同义标记"**在 HEAD 仍成立**（三处同屏只在「打满且真数 > 页内条数」
  这一种组合出现），但"同义"≠"可互替"——判据面它们分属三根独立的钉子。

## 三、HEAD 现值锚点表（l924-09 登记号 → 本单复点号；两文件均未动，故只重锚不改数）

**生产侧（`ui/pages/mistakes.py`，201 行，sha1 `d4723127…`，纯 CRLF）**

| 现号 | 内容 | 角色 |
|---|---|---|
| `:75` | `due_reviews = dao.get_due_reviews(limit=50)` | 页内条数来源（l924-09 的 :75，**未漂**） |
| `:79` | `st.markdown(f"**错题 {wrong_count} 道 · 最近 50 条内到期复习 {overdue_count} 道**")` | 标记①汇总行（l923-20 起） |
| `:84` | `if overdue_count == 50:  # 50 与 :75 的 limit 同源…` | 查询闸（打满才 COUNT） |
| `:85-86` | `due_total = dao.get_due_reviews_total()` / `if due_total > overdue_count:` | 提示闸（严格 `>`） |
| `:87` | `st.caption(f"实际到期共 {due_total} 道 · 上面只列出最先到期的 {overdue_count} 道")` | 标记③提示行（l924-09 新增） |
| `:95` | `tab_labels.append(f"到期复习 ({overdue_count} · 至多)")` | **标记②「· 至多」本体**（`82b45c1`） |

**测试侧（`tests/test_mistakes_tabs_contract.py`，321 行，纯 LF，16 passed）**

| l924-09 登记号 | HEAD 现号 | 断言 |
|---|---|---|
| :146 | `:146` | `labels == ["到期复习 (5 · 至多)", "错题重做 (3)", "弱项专练"]`（未漂） |
| :152 | `:152` | `labels == ["到期复习 (4 · 至多)", "弱项专练"]` |
| :178 | `:178` | `page_cap == 50`（文案页大小 ⇄ `limit=50` 跨源同源） |
| :183 | `:183` | 标签解析式含**可选组** `( · 至多)?` |
| :196 | `:196` | `mark.get("到期复习") == (" · 至多" if s_due > 0 else None)`＋`:197` 错题侧必须 None（**双向**） |
| :231 | `:231` | `labels == ["到期复习 (50 · 至多)", "错题重做 (60)", "弱项专练"]` |
| :233/:234 | `:233`/`:234` | `get_due_reviews.call_args.kwargs == {"limit": 50}`／`list_mistakes.call_args.kwargs == {}` |
| （l924-09 新例） | `:238-248` `:251-256` `:259-264` | 打满且真数更大（含 `:247` 标签字面含「· 至多」）／未打满不查不提示／打满真数相等查而不提示 |

⇒ **l924-09 登记的六个易撞锚点行号在 HEAD 逐位未漂**（它自己算的就是 e76461b 后的现值），
`$ rg -n "至多\|page_cap == 50\|call_args.kwargs" tests/test_mistakes_tabs_contract.py` 可复算。

**DAO 侧（`core/progress.py`）**：`get_due_reviews` 现号 **`:423`**、伴生查询 `get_due_reviews_total` 现号 **`:638`**，
谓词逐字同源（两侧同 `date.today().isoformat()`、同 `WHERE next_due_date <= ?`，页侧多 `ORDER BY … LIMIT ?`）⇒
「页内条数是下限」这个语义前提在 HEAD 仍成立。
⚠ 顺带登记一处**文本漂移**（属他单文案，本班一字未碰）：`:639` docstring 自述「:397 `get_due_reviews` 的伴生查询」
与 `tests/test_mistakes_tabs_contract.py:211` 的「`core/progress.py:397-406`」、
`tests/test_recommend_review_state.py:226` 的「`core/progress.py:418`」均已漂 **+26 行**（三处都在 docstring／注释里，
**不是断言** ⇒ 套件仍绿，但下一班按这些号定位会拿错函数）。

## 四、复算配方（每条可重跑；cwd `D:/code/learning-system`）

探针纪律＝l927-56／l927-41 同型：**tmp 副本＋`exec` 注入模块命名空间**，零改生产文件、零改测试文件；
`_body()` 用 `mistakes_page._render_mistakes_body(dao)` 的**属性查找**调用，故注入即时生效。
探针件（gitignore 内，`.gitignore:19:/tmp/`）：`tmp/l927-44/make_atmost_variants.py`、`l927_44_plugin.py`、
五份变异体＋四份红名单。

```bash
$ sha1sum ui/pages/mistakes.py
d472312787102a58464e501366252e5b1a8eccd5     # 跑前＝跑后（生产码零改动）
$ PYTHONIOENCODING=utf-8 python tmp/l927-44/make_atmost_variants.py
no_mark / caption_ge / no_summary_mark / gate_always / caption_off: 单点替换 OK   # 每刀一个锚点，锚点命中数断言 ==1
$ F="tests/test_mistakes_tabs_contract.py tests/test_mistakes_edges.py tests/test_mistakes_lookup_cache.py tests/test_mistakes_redo_lifecycle.py tests/test_ui_behavior.py tests/test_format_local_ts.py"
$ PYTHONIOENCODING=utf-8 PYTHONPATH=tmp/l927-44 L927_44_VARIANT=control python -m pytest $F -q -p l927_44_plugin
81 passed in 2.37s                              # 两向对照绿侧：插件中性（点名面＝全仓 6 个 mistakes 消费者）
$ … L927_44_VARIANT=no_mark …
9 failed, 72 passed in 2.44s                    # 摘「· 至多」
$ … L927_44_VARIANT=no_summary_mark …
12 failed, 69 passed in 2.28s                   # 摘「最近 50 条内」
$ … L927_44_VARIANT=caption_off …
1 failed, 80 passed in 2.30s                    # 摘提示行
$ … L927_44_VARIANT=caption_ge …
1 failed, 80 passed in 2.30s                    # 提示闸 > 放宽成 >=（红＝打满真数相等那例）
$ … L927_44_VARIANT=gate_always …
3 failed, 78 passed in 2.30s                    # 拆「打满才查」闸（出口 B 的前置代价）
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_mistakes_tabs_contract.py -q
16 passed in 1.17s                              # 未变异现状（与 l924-09 交付时同数）
$ git status --porcelain | wc -l
1                                               # 收班＝本单单产（?? docs/insights/l927-44-atmost-confirm.md）
```

**9 例红名单**（`no_mark`，逐条）：`test_双有_到期复习在前错题在后弱项收尾`／`test_只有到期_标签两级且无错题项`／
`test_汇总行数字与tab标签数字逐值相等` 的 `[0-1] [1-1] [7-13] [0-50] [1-2]` 五个参数点／
`test_下限语义已标出_到期侧仍是页内条数而错题侧是全量真数`／`test_打满且真数更大_汇总行下方补一行真数提示`。
⇒ 其中 `[1-0]` 参数点**不红**是设计使然：到期侧为 0 时不建标签，双向断言 `:196` 期望的正是 `None`。

**未跑全量套件**（波次纪律：同刻 5 路兄弟班）；点名 6 件合跑 81 passed 已覆盖判据面。

## 五、若人工仍要撤「· 至多」（回退清单的 HEAD 现值，本班**未执行**）

l924-08 遗留 1 给的配方是"回滚只需 2 处"，按 HEAD 重锚后**已不是 2 处**：

1. 生产侧 **1 行**：`ui/pages/mistakes.py:95` 去掉 ` · 至多`。
2. 测试侧 **6 类站点 / 9 例**：`:146`、`:152`、`:231`、`:247` 四处标签字面 ＋ `:183` 解析式去可选组 ＋
   `:196-197` 两条双向标记断言（该例 6 个参数点里 5 个会跟着变）。
3. ⚠ **不牵第三张判据文件**：`$ rg -n "到期复习 \(" --glob '!tmp/**' .` 现值命中＝
   `ui/pages/mistakes.py` **1 行** ＋ `tests/test_mistakes_tabs_contract.py` **7 行**（`:23/:146/:152/:168/:175` 一族），
   其余全在 `docs/insights/*.md` 的登记文字（含本档自身 5 行）与 gitignored 旧探针里。
   `$ rg -n "到期复习 \(" ui/ core/ tests/ scripts/ -g '*.py' | wc -l` → **8**（复算命令）。

**本班建议**：走"确认档"分支，即**维持现状、疑点结案**，把上面这份清单留在档里备查即可；
若要撤，须与 `82b45c1` 那一笔**合并裁决**（§廿三"两笔一体"型）并同批改 6 类站点，禁分笔入库。

## 六、遗留

1. 🔴 **判定留人工／主班**：本档只证明「不多余」与三处标记的独立承重面，**不裁"该不该继续三处同屏"**——
   那属可见文案与判据形状的决定，且出口 B 实测要付 12 例（§一.3）。
2. `mistakes.py` 里**三处字面量 50**（`:75` 查询实参／`:79` 汇总行文案／`:84` 提示闸）仍如 l924-09 遗留 2 所述：
   在册断言只覆盖前两处的同源（`:178` `page_cap == 50`、`:233` `call_args == {"limit": 50}`），`:84` 那道闸
   只被 `:251-256`／`:259-264` 两例间接钉住 ⇒ 提 `_DUE_PAGE_LIMIT` 常量三处共用的理想解**仍未做**（会撞 :75）。
3. `core/progress.py` 三处 docstring／注释锚点漂 +26 行（§三 末），属**文本义务**，无哨兵拦，留给下一班。
4. 本产出件**未自登索引**（w58-brief §C：索引由主班单点写）⇒ `tests/test_insights_index_closure.py` 预期红，
   须与索引行同笔入库。
5. l924-09 遗留 5（两次独立查询非同一事务快照，理论上"真数 < 页内条数"时提示闸关闭不说谎）**仍按登记不处置**；
   本单的 `caption_ge` 探针顺带证明：一旦把 `>` 放宽成 `>=`，那一格就会被"重复信息"占掉 ⇒ 现状 `>` 是有判据依据的。

## 七、收工读数（2026-09-29T04:04+08:00 现取）

```
$ git status --porcelain
?? docs/insights/l927-41-variant3cases.md        # 同班上一枚
?? docs/insights/l927-44-atmost-confirm.md       # 本档，恰＝本单单产，零夹带
$ sha1sum ui/pages/mistakes.py core/progress.py
d472312787102a58464e501366252e5b1a8eccd5        # 与开工同值 ⇒ 生产码零改动
670e0ae668a23fadbceed0bb53fedd7e9f0d67e4        # DAO 侧同样未动
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_mistakes_tabs_contract.py tests/test_mistakes_edges.py \
  tests/test_mistakes_lookup_cache.py tests/test_mistakes_redo_lifecycle.py tests/test_ui_behavior.py \
  tests/test_format_local_ts.py -q
81 passed in 2.83s                               # 未变异现状（点名面＝全仓 mistakes 消费者 6 件）
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q
2 failed, 1 passed in 0.08s                      # 预期红＝本班两枚产出档未自登索引（A=127／B=125）
```

