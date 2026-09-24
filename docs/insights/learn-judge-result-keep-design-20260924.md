# learning「回访上一题保留判题结论」行为改动裁决稿（l924-05，只读，零生产码改动）

- 任务：`zcode-bridge/inbox/l924-05.task.md`（收工后在 `done/`）｜班：`qoder-executor-20260924-0955-learn22`
- 取数盘态：`D:\code\learning-system` @ HEAD `38ad3bb` ＋ **同批 l924-03 的未提交改动**
  （`ui/pages/language.py` 已含 `_retire_variant`，**行号按工作树取**）
- 待裁的原始出口：`zcode-bridge/done/l923-16.result.md` 遗留问题 1 ——
  「要兑现这个 UX，需要去掉 4 个切换点的 `drop_shown_judge_result()`，并**同时**把该键挂进
  LRU 前缀表防无界——两件事一体，属行为改动，交主班裁决」
- 口径：只读。零生产码／零测试件／零库改动。

## 〇、结论先行

1. **「去掉 4 个切换点的清理」这件事本身不危险；危险的是它顺带要求放宽读侧展示门。**
   现状回访上一题之所以看不到旧结论，是**两道锁**：切换点 pop 掉那一格（锁 1），
   以及读侧 `last_judge_pid == active_id` 的展示门（锁 2）。
   **只去锁 1 ⇒ UX 完全不改变**（锁 2 还在，`last_judge_pid` 已被后一道题覆盖）。
   这是 l923-16 出口句里**没有说**的一层，也是本稿的主要增量。
2. ⇒ 真正的裁决点不是"删不删 4 行"，而是**展示门的语义重定义**（§三 方案 P／方案 E）。
   展示门被在册桩明确钉为**失效面 C**（`tests/test_judge_result_per_pid.py:106-108`），
   且其注释写着「判题展示面，红线相邻，不得放宽」⇒ **放宽属人工授权**，本班不动码。
3. **「同时挂进 LRU 前缀表」这一半，实测是必需的，且有一个坑**：
   若把字面量 `"last_judge_result::"` 写在 `_PROBLEM_STATE_PREFIXES` 的**续行**上，
   在册哨兵 `test_prefix_defined_exactly_once_repo_wide`（判据是"同一行里既有 `=` 又有引号"）
   **不会把它计成第二个定义点 ⇒ 假绿**（§四 实测四条）。⇒ 落地时必须
   **`import JUDGE_RESULT_PREFIX` 进表**，并顺手把该哨兵改成不依赖换行。
4. 推荐出口：**分两步走，第一步（锁 1 ＋ LRU 挂表）可以立刻做且零 UX 风险；
   第二步（锁 2 重定义）单独裁决**。理由见 §五 成本表——第一步只翻 2 条在册桩，
   第二步要翻 3 条且其中 1 条是红线相邻的展示门。

## 一、四个切换点：rg 复核后内联（完成标准 ①）

卷宗/l923-16 给的行号是 `ui/pages/language.py:154 / :207 / :227 ＋ ui/components.py:89`。
**实测复核**（`$ rg -n "drop_shown_judge_result" ui/`，工作树）：

| # | 站点 | 卷宗行号 | 收工盘实测 | 触发条件（何时会清） |
|---|---|---|---|---|
| D1 | `ui/components.py:54` 定义 | `:54` | **`:54` 零漂移** | —— 定义处 |
| D2 | `ui/components.py:89` `navigate_to_problem()` 末尾 | `:89` | **`:89` 零漂移** | 任何跨页导航（home/path/diagnostic → language） |
| D3 | `ui/pages/language.py:176` selection 分支 | `:154` | **`:176`（+22）** | 带 `selection` 进入且命中 `target_slug` 时 |
| D4 | `ui/pages/language.py:229` 切专题 | `:207` | **`:229`（+22）** | `new_topic_idx != selected_topic_idx` |
| D5 | `ui/pages/language.py:249` 切题目 | `:227` | **`:249`（+22）** | `new_problem_idx != selected_problem_idx` |

⇒ **4 个调用点的计数不变**（D2–D5），**行号漂移 +22 由本班同批的 l924-03 造成**
（`_retire_variant` 插在该文件 :77-116，位于这些站点之上）。
漂移归因**已用 HEAD 反证坐实**（不是"盘在动"，是本班自己的未提交改动）：
`$ git show HEAD:ui/pages/language.py | grep -n "drop_shown_judge_result()"`
→ **`:154 / :207 / :227`** 三个行号与卷宗逐字相同 ⇒ **卷宗行号在 HEAD `38ad3bb` 上至今成立**，
只有工作树（l924-03 未提交）落后 22 行。派单/卷宗的旧行号**主班若按 HEAD 复核会全中**，
按工作树复核则要取 :176/:229/:249 —— 两套数都记在本节，避免下一班再绕一次。

顺带把**另外三类站点**也复核一遍（本稿的行为变化表要用，卷宗未列全）：

| 类别 | 站点（实测行号） | 表达式 |
|---|---|---|
| 原地动作清自己那格（3 处，**不动**） | `:301` 生成变式 / `:314` ↩ 回到原题 / `:340` ↺ 重置 | `st.session_state.pop(judge_result_key(active_id), None)` |
| 写（1 处） | `:357` | `st.session_state[judge_result_key(active_id)] = result` |
| **指针写**（1 处） | `:358` | `st.session_state.last_judge_pid = active_id` |
| 读（2 处） | `:370` 判空 / `:373` 取值 | 展示门 `:369-372`，条件含 `:371` `last_judge_pid == active_id` |
| **指针读**（2 处） | `ui/components.py:62`（drop 定位）／`language.py:371`（展示门） | —— |

在册桩钉的站点计数：`test_three_plus_three_sites`（`len(drop) == 3` ＋ `len(own) == 3`）与
`test_language_page_reads_and_writes_only_via_helper`（`src.count("judge_result_key(active_id)") == 6`，
＝ 1 写 ＋ 2 读 ＋ 3 原地清）⇒ **删 D3/D4/D5 三处会把前者从 3 打成 0**；
`count == 6` 不受影响（切换点走 `drop_shown_judge_result()` 不写键名）。

## 二、行为变化表（去掉切换点清理之后，逐场景对照）

设「格」＝ `last_judge_result::<pid>`；「门」＝ `last_judge_pid == active_id`（`:371`）。
现状：门**一字未松**（l923-16 §执行摘要）。

| 场景 | 现状（门在） | 只删 D2–D5（锁 1 去、门在） | 删锁 1 ＋ 方案 E（门改为"该题自己的格存在即展示"） | 删锁 1 ＋ 方案 P（指针换成 visited 栈） |
|---|---|---|---|---|
| A 题判题 → 切到 B → 回 A | 不显示（A 格已被 D4/D5 清） | **仍不显示**：A 格在，但 `last_judge_pid` 已是 B ⇒ 门拦 | **显示 A 的旧结论** ✅（目标 UX） | 显示（A 在 visited 里） |
| A 判题 → 跨页导航（D2）→ 回 A | 不显示 | 仍不显示（同上门拦） | 显示 ✅ | 显示 |
| A 判题 → A 上点「↺ 重置」 | 不显示（`:340` 清自己） | 不显示（原地清**保留**） | 不显示 ✅（重置后就该没了） | 不显示 |
| A 判题 → 生成变式 → 退回原题 | 不显示（`:301`＋`:314` 清变式格；A 格从未写） | 不显示 | 不显示（A 若判过则显示 A，变式格已清） | 同左 |
| A 判题 → 切 B → **在 B 上判题** → 回 A | 不显示 | 不显示 | **显示 A 的结论**（可能就是"很久以前的"）⚠️ | 显示，但可加"仅最近 N 题"窗口 |
| A 判题 → 切 B → B 未判题 → 回 A | 不显示 | 不显示 | 显示 A ✅ | 显示 |
| 变式题判题 → 退回原题（`AI_VARIANT::…` 格） | 已清 | 已清 | 已清（`:314` 保留 ＋ l924-03 `_retire_variant` 兜底） | 同左 |
| **LRU 逐出 31 号题**（`_LRU_CAP=30`） | 该题格从未进表 ⇒ **不清** | 不清 ⇒ **无界**（见 §四.2 实测 S1） | 不清 ⇒ 无界 | 不清 ⇒ 无界 |
| 会话末态 `last_judge_result::*` 格数（刷 40 题） | **0**（l923-16 实测，本班 S0 复算＝0） | **40**（实测 S1，每题一格无人清） | **30**（实测 S2：挂表后由 `_LRU_CAP` 封顶） | 30 ＋ visited 列表 |

> 上表末两行的 **0 / 40 / 30 是本班离线实测**，不是推算：
> 探针 `tmp/l924-05/slot_count.py` 用真函数（`_touch_problem` ＋ `drop_shown_judge_result`）
> 跑 40 道题三态，原文读数见 §四.2 的代码块。**注意**：S2 的 30 而不是 29，是因为**当前题那一格不该被清**
> （它还在屏幕上），逐出只作用在被挤出 `_problem_lru` 窗口的题上——这正是"挂表"应有的形状。

⇒ **本表最重要的一行是第 2 行**：只删切换点清理，用户看不到任何变化。
所以 l923-16 那句"两件事一体"要改写成**三件事**：
①去锁 1 ＋ ②挂 LRU 防无界 ＋ ③重定义展示门。①② 是**技术包**（一起做才有意义），
③是**产品决定**（决定用户会不会看到旧结论）。把 ③ 混在"去掉 4 处调用"里交付，
会出现"改了代码但行为没变"的**假改动**；把 ①② 拆开交付，会出现**无界泄漏**。

## 三、`last_judge_pid` 处置专节（完成标准 ②；l923-16 遗留 2 的正面回答）

### 3.1 它今天是什么

- 唯一写入点 `language.py:358`（判题成功即写，与结果同批）；**从不 pop**（全仓零 pop 点，实测）。
- 唯一两个读取点：`components.py:62`（`drop_shown_judge_result` 靠它指认"正要离开的那题"）、
  `language.py:371`（展示门）。
- 语义：「**屏幕上此刻展示的是谁的结论**」——一个全局 UI 事实（按 l924-04 的三类判据，
  它属 **G 全局 UI 键**，任何清扫器都不得触及）。

### 3.2 「指针＋信箱」关系在去掉锁 1 后为什么破

l923-16 遗留 2 的原话是「若遗留 1 落地，指针语义需要重新定义（否则回访时 `last_judge_pid`
已指向别题）」。实测这条**成立且方向有两个**：

- **指针变得无人写、但有人读**：去掉 D2–D5 后，`last_judge_pid` 只在判题时前进，
  **切题不再回退它**。于是 `:371` 的门在"回访"场景**必然为假** ⇒ 信箱里明明有 A 的结果，
  门却因指针指着 B 而拦死。**这就是 §二 第 2 行的机制**。
- **反向的破**：`drop_shown_judge_result()` 若还保留在任何一处（比如只删 D3/D4/D5 而留 D2），
  它清的是**指针指着的题**而不是**正要离开的题**——两个语义在现状等价（因为每次切换都清），
  去掉部分切换点后就**分叉**了。⇒ 半删比全删更糟，会产生"清错题"的新缺陷。

### 3.3 三个可选语义（本稿只列，不实施）

| 方案 | `last_judge_pid` 的新语义 | 展示门 | 需要新增的键 | 在册桩影响 | 用户可见后果 |
|---|---|---|---|---|---|
| **保持现状（N）** | 「此刻展示的是谁」 | 不动 | 无 | 零 | 回访看不到旧结论（＝当前行为，改动无收益） |
| **指针即历史（P）** | 改为 `_recent_judge_pids` 有序列表（LRU 语义，容量与 `_LRU_CAP` 对齐） | 门改成 `active_id in _recent_judge_pids` | 1 个全局键（G 类） | 翻 `test_language_page_reads_and_writes_only_via_helper:106` 的门桩 ＋ `test_three_plus_three_sites` | 回访最近 N 题都显示各自结论；"很久以前"的被窗口挡掉 ⇒ **最贴近 l923-16 想守住的东西** |
| **信箱自证（E）** | 保留单值指针，但**只服务原地清理定位**，不再进展示条件 | 门放宽成 `judge_result_key(active_id) 存在` | 无 | 翻同一门桩 ＋ `test_read_side_guard_still_pairing_pid` 两条 | 实现最省；但**回访任意旧题都会把它当时的结论当刚判的显示**（正是门桩注释警告的失效面 C） |

**本班取向（仅供主班参考）**：P。
它把"红线相邻"的那道门**从"删"改成"换成有界集合"**，既给 UX 又保住"很久以前的不被当新的"；
代价是多一个全局键和一条 LRU 语义，而这条 LRU 恰好与本题的**第三件事**（挂 LRU 前缀表）同构，
可以共用一次实现与一次测试改动。

## 四、挂进 LRU 前缀表的改法（含一个会假绿的哨兵坑）

`_PROBLEM_STATE_PREFIXES`（`ui/pages/language.py:44-45`，现 **6 项**）是逐出清扫的唯一数据源，
真题侧由 `_touch_problem:64-65` 遍历、变式侧由 `_retire_variant:105-106` 遍历（同批 l924-03）。
挂第 7 项的**正确写法**：

```
from ui.components import (..., JUDGE_RESULT_PREFIX, ...)        # 已 import judge_result_key，同批加
_PROBLEM_STATE_PREFIXES = ("code::", "chat_ctx::", "chat_history::", "preask_hist::",
                           "show_preask::", "editor_epoch::", JUDGE_RESULT_PREFIX)
```

**为什么必须用常量而不是字面量**（实测四条，脚本 `tmp/l924-05/defsite.py`）：

| 写法 | `test_prefix_defined_exactly_once_repo_wide` 是否计为定义点 | 结论 |
|---|---|---|
| `ui/components.py:40` `JUDGE_RESULT_PREFIX = "last_judge_result::"` | **是**（现状唯一命中） | 基准 |
| 字面量写在元组**续行**（现格式） | **否** ⇒ 字面量实际两处、哨兵仍报"恰 1 处" | 🔴 **假绿**，禁 |
| 字面量写在**同一行** | 是 ⇒ 命中 2 处当场红 | 会红，但格式一改就失效 |
| `JUDGE_RESULT_PREFIX` 常量入表 | 否（行内无该字面量） | ✅ 正解，且天然单源 |

⇒ 顺带产出一条**独立于本裁决的可改进项**：该哨兵的判据（"同行含 `=` 且有引号"）**依赖换行格式**，
建议改为 AST 级判定（找 `ast.Assign` 且 value 是 `Constant` 等于该前缀）。
它属"改判据"，本班不动，登记在 §六 L-4。

### 4.1 连带要同步的在册桩（挂表的真实成本）

| 桩 | 位置 | 现断言 | 挂 7 项后 |
|---|---|---|---|
| 六元组全等 | `tests/test_editor_variant_keys.py:231` | `== (6 项)` | 必改 |
| 六元组全等 | `tests/test_retire_variant.py`（`SIX_PREFIXES` ＋ `test_prefix_table_is_the_single_source_of_truth` 等 5 处命中） | `== 6 项`、`len(...) == 6` | 必改（**本班自己档，改动成本已知**） |
| LRU 前缀清点 | `tests/test_language_lru_eviction.py`（3 处） | 逐出后逐族断言 | 必改 ＋ **新增一例**：逐出某题时它的判题结论格一并消失 |
| 键形单源 | `test_judge_result_per_pid.py:89` | 恰 1 定义点 | 用常量则不变；用字面量**且写在续行 ⇒ 假绿** |
| 站点计数 | `test_judge_result_per_pid.py:180` | `len(drop)==3` | 去锁 1 后变 0 ⇒ 必改 |
| 展示门 | `test_judge_result_per_pid.py:106` | 门串必须在源码里 | 方案 P/E ⇒ 必翻（**红线相邻**） |
| 展示门 | `test_judge_result_per_pid.py:202` | 同上另一路 | 方案 P/E ⇒ 必翻 |
| 五步重置链 | `test_language_editor_epoch.py:102` 与 `test_editor_variant_keys.py:174` | 顺序与步数 | **不受影响**（原地清理三点未动） |

### 4.2 为什么"不挂表"不是一个可接受选项

l923-16 当时实测「连做 40 道题后活着的格数 **0**」⇒ 不挂表。**那个 0 完全由锁 1 供给**
（每次切题都清掉刚展示那一格）。本班把同一实验在三态下重跑（`tmp/l924-05/slot_count.py`，
真函数、离线、零写盘）：

```
态        刷 40 题后活着的 last_judge_result::* 格数   _problem_lru 长度(应≤30)
S0                                        0   30      ← 现状（锁 1 在）
S1                                       40   30      ← 去锁 1、不挂表
S2                                       30   30      ← 去锁 1 且把 JUDGE_RESULT_PREFIX 挂进表
```

⇒ **「不挂表」的前提与「去锁 1」互斥**，这就是 l923-16 说"两件事一体"的实质，本稿复核成立。
且 S2 的封顶值恰等 `_LRU_CAP`，说明挂表后无需另设机制。

## 五、可执行验收断言草案（完成标准 ③；≥3 条，写成可直接落进 tests/ 的形状）

以下 5 条都是**判别式**断言（变异检验在 §五.末给出预期红名），不是"跑通即可"的现状桩。

**A-1 回访保留结论（锁 1 去 ＋ 方案 P 的正面用例）**
```python
def test_revisit_previous_problem_still_shows_its_own_verdict(fake):
    """判 A → 切 B → 回 A：A 的结论格还在 **且门放行**。
    前置不成立时本例是空转，所以先钉格在、再钉门在、最后钉"能渲染"。"""
    fake.session_state[components.judge_result_key(PID_A)] = "verdictA"
    fake.session_state[components.judge_result_key(PID_B)] = "verdictB"
    fake.session_state["_recent_judge_pids"] = [PID_A, PID_B]      # 方案 P 的新指针语义
    assert language_page._verdict_is_displayable(PID_A) is True, (
        "回访上一题仍看不到旧结论：锁 1 未真正去掉，或门没换成语义正确的集合判据")
```

**A-2 久远的结论不得当"刚判的"显示（守住失效面 C 的有界版）**
```python
def test_verdict_outside_the_recent_window_is_not_shown(fake):
    cap = language_page._JUDGE_WINDOW          # 与 _LRU_CAP 对齐或显式更小
    pids = [f"python/t/p{i}" for i in range(cap + 5)]
    for p in pids:
        fake.session_state[components.judge_result_key(p)] = "v"
    fake.session_state["_recent_judge_pids"] = pids[-cap:]
    assert language_page._verdict_is_displayable(pids[0]) is False, (
        "窗口外的旧结论仍会展示＝把很久以前的判题当刚判的显示（l923-16 门桩警告的失效面）")
```

**A-3 逐出必须连带清判题结论格（防无界的判别式，不靠数活格）**
```python
def test_eviction_also_drops_the_verdict_slot(fake):
    assert components.JUDGE_RESULT_PREFIX in language_page._PROBLEM_STATE_PREFIXES, (
        "第 7 族未进表：删掉切换点清理后 last_judge_result::* 会按访问过的题数无界增长")
    pid = "python/t/gone"
    fake.session_state[components.judge_result_key(pid)] = "v"
    language_page._touch_problem(pid)
    for i in range(language_page._LRU_CAP + 2):
        language_page._touch_problem(f"python/t/ev{i}")
    assert components.judge_result_key(pid) not in fake.session_state, "已逐出题的结论格残留＝泄漏回归"
```

**A-4 键名单源不得靠换行侥幸（钉住 §四 那个假绿）**
```python
def test_judge_prefix_has_exactly_one_ast_definition():
    """AST 级：赋值右侧字面量等于 last_judge_result:: 的站点全仓恰 1 处，
    且 _PROBLEM_STATE_PREFIXES 的元素必须是**名字**（导入常量）而非该字面量。"""
    tree = ast.parse(LANG_PY.read_text(encoding="utf-8"))
    tup = next(n for n in tree.body
               if isinstance(n, ast.Assign) and n.targets[0].id == "_PROBLEM_STATE_PREFIXES")
    kinds = {type(e).__name__ for e in tup.value.elts}
    assert "Constant" not in kinds or all(
        e.value not in components.JUDGE_RESULT_PREFIX for e in tup.value.elts if isinstance(e, ast.Constant)), (
        "前缀表里出现了 last_judge_result 字面量：应 import JUDGE_RESULT_PREFIX，"
        "否则键名两处定义、且续行写法会骗过按行数的在册哨兵")
```

**A-5 半删禁止（§三 3.2 那条"清错题"的新缺陷）**
```python
def test_no_partial_removal_of_switch_point_cleanup():
    """4 个清理点要么全在、要么全不在，不得出现"删了切题却留着跨页导航"。
    站点判据与在册桩 test_three_plus_three_sites 同型（整行 strip 相等，故 def 不算）。"""
    sites = [f"{f.name}:{n}" for f in sorted((REPO_ROOT / "ui").rglob("*.py"))
             for n, ln in enumerate(f.read_text(encoding="utf-8").splitlines(), 1)
             if ln.strip() == "drop_shown_judge_result()"]
    assert len(sites) in (0, 4), (
        f"切换点清理半删（现 {len(sites)} 处：{sites}）＝ drop 清的是指针指着的题、"
        "不是正要离开的题，会新增『清错题』缺陷")
```
> 现状实测读数：`len(sites) == 4` ＝ `components.py:89 / language.py:176 / :229 / :249`
> （与 §一 表逐位一致）。⚠️ 若改用"子串计数"会得到 **5**（多算 `components.py:54` 的 def 行），
> 那种写法会把"只删 def 之外的 4 处"误判成违规——**判据必须整行相等**，与在册桩保持一致。

**这五条在"只删锁 1、不动门"的错误实现下的预期红名**：A-1 红（门拦死）、A-3 若也没挂表则红、
A-5 红（若漏删一处）；A-2/A-4 在正确实现下也必须绿——A-2 是**反向守卫**，
专门拦"为了让 A-1 绿而把门整个删掉"这种过修。

## 六、遗留与交裁决出口

| # | 事项 | 为何不自行处置 |
|---|---|---|
| L-1 | **展示门是否放宽**（方案 N／P／E 三选一） | 在册桩注 :107 自述"判题展示面，红线相邻，不得放宽" ⇒ 人工授权项，本班不动码 |
| L-2 | **锁 1 ＋ 挂表要不要同批**（§〇.4 的第一步技术包） | 技术上必须同批；但落地会翻 `test_three_plus_three_sites` 与六元组桩（含本班 l924-03 的 5 处），跨 3 个测试档＝跨单归属，交主班派工 |
| L-3 | `_recent_judge_pids` 的窗口容量取值（与 `_LRU_CAP=30` 对齐？另立常数？） | 纯产品判断，无实测依据可定 |
| L-4 | `test_prefix_defined_exactly_once_repo_wide` 的**按行判据依赖换行**（§四 实测假绿） | 属"改判据"，本班只登记不修；本稿给 AST 版草案（A-4） |
| L-5 | 方案 P 引入的新全局键 `_recent_judge_pids` 与 l924-04 三类判据的一致性 | 已按 G 类归它（永不清扫）；若主班认为它应随逐出收缩，需回改 l924-04 的判据表 |
| L-6 | 卷宗行号 `:154/:207/:227` 在收工盘已 `+22` | 由本班 l924-03 造成，已在 §一 内联更正；主班引用时按实测行号取 |

## 七、本档改了哪些文件（交主班代提交；本班**未 add、未 commit**）

| 文件 | 状态 |
|---|---|
| `docs/insights/learn-judge-result-keep-design-20260924.md` | `??`（本档，新建 274 行 / 纯 LF） |
| `docs/insights/learn-insights-index-20260918.md` | ` M`（**同单登记**：表内 1 行 ＋ 档头对账读数 1 条 ＝ 本档 +2；含 l924-04 后累计 `git diff --numstat` 读数 **4 / 0**） |

索引闭合复算：l924-04 登记后 A=69/B=69 ⇒ 本档登记后 **A=70、B=70、C=空、重复=0**；
哨兵 `PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q` → **3 passed**。

探针残留（不入库，`tmp/` 已 gitignore）：
`tmp/l924-05/slot_count.py`（§二末两行 ＋ §四.2 的 S0/S1/S2 三态活格实测，跑真函数、离线、零写盘）、
`tmp/l924-05/defsite.py`（§四 定义点判据的五种写法实测）。
