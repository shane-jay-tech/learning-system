# learning `editor_*` 键规范设计稿：全局 UI 键 vs 题态键 vs 变体残键（l924-04，只读，零生产码改动）

- 任务：`zcode-bridge/inbox/l924-04.task.md`（收工后在 `done/`）｜班：`qoder-executor-20260924-0955-learn22`
- 取数盘态：`D:\code\learning-system` @ HEAD `38ad3bb` ＋ **同批 l924-03 的未提交改动**
  （`ui/pages/language.py` 已含 `_retire_variant`，行号按**工作树**取，非 HEAD）
- 口径：只读。零生产码／零测试件／零生产库改动；探针在 `tmp/l924-04/`（`tmp/` 已 gitignore）。
- 上游：`zcode-bridge/done/l923-15.result.md` 遗留问题 1（「要真闭需要先定 `editor_*` 的 key 规范」）
  与 `l922-113` 遗留 2、`l922-114` 遗留 2。

## 〇、结论先行（四条，后三条都推翻或收窄了上游假设）

1. **`editor_*` 命名空间里今天一个「全局 UI 键」都没有。** 卷宗举的 `editor_theme` 是**假设句**，
   盘上不存在：全仓 `editor_` 命中只有两族（`editor_<pid>_<epoch>` widget 键、`editor_epoch::<pid>`
   计数器），其余全是 Python 标识符（`_editor_key` / `_clear_variant_editor_keys` / `_retire_variant`）
   与注释。⇒ 「无法区分全局 UI 键与泄漏残键」这一条**在 editor_ 侧不成立**，
   「前缀改名案」因此失去主要动因（见 §五 案 A 的成本/收益倒挂）。
2. **`editor_<pid>_<epoch>` 不是泄漏。** 真实会话实测（AppTest 跑真 `app.py`）：同一题连点 5 次
   「↺ 重置」盘上只留 **1 个** widget 键（`_5`），跨 6 道题之后 widget 键仍是 **1 个** ⇒
   Streamlit 在 widget  unregister 时**自己回收**该键。上游三档（l922-113／l922-114／l923-15）
   所说「每按一次重置多留一个永久残键」只在 **FakeStreamlit 单测里成立**（假件不做 widget 回收），
   是「测试侧失明」反向污染了缺陷定性。
3. **真正无界的只有"显式写入"的那一族：`editor_epoch::<pid>`。** 实测 6 道题 ⇒ 6 个计数器键、
   6 个 `code::<pid>`，**1:1 随访问题数线性增长**，与 widget 键的"恒为 1"形成决定性对照。
   它已被 `_PROBLEM_STATE_PREFIXES` + LRU 覆盖（真题侧 30 题封顶），**唯一漏口是变式题**
   ——而那个漏口已由同批 l924-03 的 `_retire_variant` 在「↩ 回到原题」处闭掉。
4. **规范该解决的其实不是"改名"，而是"三件事被混在一个前缀里"**：
   ① widget 副产物键（Streamlit 自回收，人不该扫它）；② 人工写入的题态状态键（人必须扫）；
   ③ 全局 UI 键（谁都不该扫）。现状 ①② 共用 `editor_` 前缀，所以清扫代码必须靠
   `rsplit("_", 1)` 这种**形态猜测**来区分 ① 与全局键 —— 这才是 l922-113 遗留 2 的**真盲区**：
   `editor_<pid>`（缺 epoch 后缀）与假想中的 `editor_theme` 在语法上同形，无法区分。

⇒ 推荐给主班的出口是 **§五 案 B′（键形分层 + 显式登记表，零改名）**，
并**不建议**案 A（前缀改名）：案 A 要动 7 个测试文件 50 行耦合，换来的收益案 B′ 零改名就能拿到。

## 一、取证口径（每条都可复算；命令均在仓库根执行）

```bash
# (1) editor_ 全量命中（含测试），按文件
rg -c "editor_" --glob '!tmp/**' .
# (2) 生产码侧（剥注释后）
rg -n "editor_" ui/ core/ scripts/ -g '*.py'
# (3) 会话内真实键名（AppTest 跑真 app.py，LS_PROGRESS_DB 指 tmp 沙盒）
PYTHONIOENCODING=utf-8 python tmp/l924-04/runtime_probe.py
PYTHONIOENCODING=utf-8 python tmp/l924-04/accum_probe.py
# (4) 静态键形普查（session_state 触点 97 处 / widget key= 39 处 / 10 份 ui 文件）
PYTHONIOENCODING=utf-8 python tmp/l924-04/key_census.py
# (5) 两案耦合面分母
PYTHONIOENCODING=utf-8 python tmp/l924-04/coupling2.py
```
只读自证：探针期间生产库 `data/progress.db` 指纹 **写前 = 写后**
（`b07f512a` / 114,688 B，sha256 前 8 位，探针一律 `LS_PROGRESS_DB` 指 `tmp/l924-04/probe*.db`）；
`core/`、`scripts/` 下 `editor_` **零命中**（`rg -c` 只回 `ui/pages/language.py` 与 `ui/pages/dashboard.py`）。

## 二、`editor_*` 键清单（完成标准 ①②：逐键带 rg 命中行号 ＋ 三类归属）

三类归属定义见 §四。**行号为工作树实测**（`ui/pages/language.py` 现 610 行）。

| # | 键形 | 归属 | 生产码站点（`rg -n` 实测） | 写入方 | 真实会话是否累积 |
|---|---|---|---|---|---|
| E1 | `editor_<pid>_<epoch>` | **题态键（W：widget 副产物）** | 生成 `:41` `return f"editor_{active_id}_{epoch}"`；LRU 清扫判据 `:69` `startswith("editor_")` / `:71` `k[len("editor_"):]`；retire 清扫判据 `:110` / `:112` | Streamlit（经 `key=` 注册） | **否**，实测恒 1 个（§三 Q1/Q2） |
| E2 | `editor_<AI_VARIANT::原题>::<epoch>` | **变体残键（W）** | 同 E1 五个站点（`active_id` 取到变式 id 时） | Streamlit | 否（同 E1） |
| E3 | `editor_epoch::<pid>` | **题态键（S：人工状态）** | 读 `:40` `setdefault(f"editor_epoch::{active_id}", 0)`；写 `:338` `epoch_key = f"editor_epoch::{active_id}"`；表项 `:45`；遍历清键 `:64-65`（LRU）/ `:105-106`（retire） | 应用自己 | **是**，1 键/题（§三 Q2 实测 6 题 6 键） |
| E4 | `editor_epoch::<AI_VARIANT::原题>` | **变体残键（S）** | 同 E3；逐出**只**由 `_retire_variant` 负责（`:55-56` 变式豁免 LRU） | 应用自己 | 是；l924-03 后有「↩ 回到原题」终点 ⇒ 有界 |
| E5 | `editor_<pid>`（**缺 epoch 后缀**的假想/历史形态） | **未分类 ⇒ 正是盲区本身** | 无生产写入方（拼键必带 `_{epoch}`）；清扫判据对它**不命中**：`:72`/`:113` 的 `body.rsplit("_", 1)[0] == pid` 要求末段有 `_` | —— | 若出现则永久残留 |
| E6 | `editor_theme` 之类「全局 UI 键」 | **全局 UI 键 —— 盘上不存在** | 全仓零命中（§〇.1）。`code_editor` 的 theme/font_size 是**硬编码字面量**（`ui/components.py:111/:113`，`theme="tomorrow_night"`、`font_size=15`），**不落 session_state** | —— | n/a |

`editor_` 前缀下的**非键**命中（改前缀案要一起看，因为它们钉的是同一批字面量）：
`ui/pages/language.py:32`（`def _editor_key`）、`:81`（本单新档 docstring）、
`:95`、`:117`（`def _clear_variant_editor_keys`）、`:123`、`:313`（「↩ 回到原题」调用点，
由 `:126` 转调 `_retire_variant`）、`:322`/`:326`（两处 `key=_editor_key(active_id)`）、
`ui/pages/dashboard.py:334`（**注释**，引用「§十二 点名的 editor_* 无界增长那类」——
按本档 §〇.2 的实测该说法**需修正**，但改它属别的单的账，本档不动）。

### 邻域键普查（规范要成立必须一起归类；来自 `key_census.py` 的 97 个 session_state 触点 / 39 个 `key=`）

| 键形 | 归属 | 站点（首个命中） | 真实会话是否累积 |
|---|---|---|---|
| `code::<pid>` | 题态键（S） | `:29` 生成 / `:269-271` 读写 / `:45` 表项 | **是**，1 键/题（实测 6 题 6 键） |
| `chat_ctx::<pid>`、`chat_history::<pid>`、`preask_hist::<pid>`、`show_preask::<pid>` | 题态键（S） | `:44-45` 表；写 `:361/:367/:344/:539` | 是（用到才写），LRU 覆盖真题、retire 覆盖变式 |
| `lesson_chat::<lang>::<slug>` | 题态键（S，**按专题而非题**） | 实测末态 3 个（3 个专题） | 是，1 键/专题，**不在任何表内** ⇒ 见遗留 R-3 |
| `run_<pid>`、`reset_<pid>`、`preask_<pid>`、`gen_<pid>` | 题态键（W） | `:333/:335/:343/:296` | **否**，实测只留当前题 ⇒ l924-03 遗留 3 的担忧被本档**否证**（见 §六） |
| `chat_input_<pid>`、`preask_input_<pid>`、`chat_ask_<pid>`、`chat_clear_<pid>`、`preask_send_<pid>`、`preask_close_<pid>` | 题态键（W） | `:463/:529/:470/:472/:536/:538` | 否（同上）；其中 `chat_input_`/`preask_input_` 另有发送后显式 pop（`:500/:554`） |
| `problem_select_<lang>_<slug>` | 题态键（W，专题粒度） | `:182/:240` | 是（实测 3 专题 3 键），**不在表内** |
| `topic_select_<lang>`、`back_home_<lang>`、`next_topic_<lang>`、`prev_topic_<lang>`、`side_<lang>`、`_lesson_viewed_<lang>_<slug>` | 全局 UI 键（会话级，按语言/专题有界） | `:219/:209/:418/:428`、`ui/components.py:79-83` | 有界（≤ 语言数×常数） |
| `route`、`selected_lang`、`selected_topic_idx`、`selected_problem_idx`、`selection`、`ai_variants`、`_problem_lru`、`last_judge_pid`、`last_judge_result::<pid>` | 全局 UI 键（G，除末项按 pid） | `:21-25/:57`、`ui/components.py:62-64` | `last_judge_result::<pid>` **按 pid 增长**，由 l923-16 的 LRU 挂键收口 |

**三类互斥性自检**：上表 24 个键形全部可归入 G/T-W/T-S 之一且仅一个（判据见 §四），
唯一例外是 E5 —— 它**不可判定**，而不可判定的原因正是「形态猜测」而非「登记」，这构成 §五 两案的共同前提。

## 三、真实会话实测（本档的核心否证证据）

探针：`tmp/l924-04/accum_probe.py`（AppTest 跑真 `app.py`，`LS_PROGRESS_DB` 沙盒，零网络，
变式题用直接注入 `ai_variants` 构造）。

**Q1 同一题连点 5 次「↺ 重置」**（考察 widget 残键是否逐次堆积）
```
   第 1 次重置后：widget 键 1 个 ['editor_python/01_hello_and_vars/01_hello_world_1']
   第 2 次重置后：widget 键 1 个 ['editor_python/01_hello_and_vars/01_hello_world_2']
   ...        第 5 次重置后：widget 键 1 个 ['..._5']
   计数器键: ['editor_epoch::python/01_hello_and_vars/01_hello_world'] 值: [5]
```
⇒ **旧 epoch 的 widget 键不堆积**（Streamlit 在 widget 消失后回收）。E1/E2 的「无界」定性不成立。

**Q2 经 selectbox widget 键连刷 6 道题**（跨 3 个专题，每题都渲染编辑器）
```
   第 1 题 之后：editor_ 共 2 个（widget 1 / 计数器 1）
   第 2 题 之后：editor_ 共 3 个（widget 1 / 计数器 2）
   ...
   第 6 题 之后：editor_ 共 7 个（widget 1 / 计数器 6）
   末态全部 editor_ 键: 6 个 editor_epoch::<pid> ＋ 1 个 editor_<当前题>_0
```
⇒ 增量**全部**来自 E3（人工写的计数器）；widget 键恒 1。会话末态 44 键。
（第一轮探针曾误用「直接写 `selected_topic_idx`」导航，被 selectbox 的 widget 状态覆盖，
读数是"6 次都停在同一题"的**假不累积**；上表是改用 `topic_select_<lang>` /
`problem_select_<lang>_<slug>` widget 键导航后的真值 —— 这条踩坑记入 §七 C-2。）

> ⚠️ **本节的适用边界（本班自己给 §〇.2 的结论打的折扣）**：AppTest 与真实浏览器会话**共用**
> Streamlit 的 `SessionState` widget 登记/回收路径，但「回收」是否在每个 rerun 末尾**无条件**发生，
> 本班只在 AppTest 下实测（未做真浏览器目检，本机不便免人工验证）。
> 因此 §〇.2 的准确表述是「**在 AppTest 真渲染下不累积**」，而非「真机上一定不累积」。
> 主班若要把这条当"删清扫代码"的依据，应先在真浏览器会话里点一轮（或按 §五 案 B′ 保留清扫代码，
> 只把判据从"猜形态"换成"查登记"——那才是零风险的一半）。

**Q3 末态按族归类（6 道题之后）**
```
   其它无 :: 前缀   28 个   ← 其中 run_/reset_/preask_/gen_/editor_<pid>_<epoch> 均只有"当前题"那一份
   code::            6 个   ← 1/题，线性
   editor_epoch::    6 个   ← 1/题，线性
   lesson_chat::     3 个   ← 1/专题，线性且无表管
   editor_<pid>_<epoch> 1 个
```

**Q4 变式题族（注入 `AI_VARIANT::<pid>` 后点「↩ 回到原题」，验 l924-03）**
```
   变式打开后（含变式 id 的键）: code:: / chat_history:: / preask_hist:: / show_preask:: /
       editor_epoch:: / editor_<vid>_0 / preask_ / preask_input_ / preask_send_ /
       preask_close_ / reset_ / run_  —— 12 个
   退回后 editor_ 键: 只剩原题 2 个；「仍含变式 id 的键」= []
   原题 editor 键幸存: ['editor_epoch::python/01_hello...','editor_python/01_hello..._1']
```
⇒ l924-03 的 `_retire_variant` 在**真实 Streamlit** 下把变式族清到 0 且未连坐原题
（这是它单测之外的独立复证）。

## 四、三类归属的**判据**（规范本体；不是命名偏好，是可执行判据）

一个键 K 的归属由三个问题决定，顺序固定：

- **Q1：K 的名字里含不含「题/专题身份」？** 不含 ⇒ **G 全局 UI 键**。
  例：`route`、`ai_variants`、`_problem_lru`、`topic_select_python`、`side_cpp`、`back_home_python`。
  处置：**任何清扫器都不得触及**。清扫器的白名单应当是「G 全集」的**补集**，而不是逐个猜形态。
- **Q2：含身份，且该键是 Streamlit 因 `key=` 参数自动写的 widget 状态？** ⇒ **T-W 题态键（widget 副产物）**。
  可执行判据：**该键名只出现在 `key=` 实参或 `_editor_key()` 返回值里，从不出现在
  `st.session_state[...]` 的赋值左侧**。例：E1/E2、`run_<pid>`、`reset_<pid>`、`chat_input_<pid>`。
  处置：**不需要人扫**（实测自回收）。人扫它是**冗余成本**，且正是 E5 盲区的来源。
- **Q3：含身份，且由应用显式 `st.session_state[K] = …` / `setdefault` 写入？** ⇒ **T-S 题态键（人工状态）**。
  例：`code::`、`chat_ctx::`、`chat_history::`、`preask_hist::`、`show_preask::`、**E3**。
  处置：**必须**有逐出终点。真题侧终点＝LRU（`_LRU_CAP=30`）；变式侧终点＝「↩ 回到原题」（l924-03）。
- **R 变体残键** ＝ Q1 判含身份（身份段为 `AI_VARIANT::…`）且 T-W/T-S 的**逐出表未覆盖该身份**时的那部分。
  今天 T-S 那一半已由 l924-03 闭掉；T-W 那一半按 §三 实测**本就不需要闭**。

> 判据的意义：它把「能不能清」从**猜字符串形态**改成**查登记**。E5（`editor_<pid>` 缺后缀）
> 之所以今天不可判定，就是因为仓里只有形态、没有登记。

## 五、两案与迁移成本（完成标准 ③）

成本分母来自 `coupling2.py` 实测（`ui 生产 7 / tests 50`，行数为**命中行数**，含断言与夹具）。

### 案 A：前缀改名（把 widget 副产物键改名让出 `editor_`，例如 `editor_<pid>_<epoch>` → `wdg_editor_<pid>_<epoch>`）

| 改动面 | 行数量 | 明细 |
|---|---|---|
| 生产码必改 | **5 行** | `:41` 生成、`:69/:71` LRU 判据、`:110/:112` retire 判据 |
| 生产码顺带改注释 | 3 行 | `:66/:107` 注释、`:81` docstring |
| 测试侧必改 | **50 行 / 7 个文件** | `test_language_editor_epoch.py` 13、`test_retire_variant.py` 13、`test_editor_variant_keys.py` 12、`test_language_lru_eviction.py` 8、`test_ui_behavior.py` 2、`test_app_flow.py` 1、`test_judge_result_per_pid.py` 1 |
| 语义要重写的断言 | ≥3 条 | `test_key_format_is_underscore_joined_not_prefixed`、`test_helper_does_not_add_third_epoch_brace_literal` 的「恰 2 处」口径、`test_revisit_after_eviction_restarts_at_epoch_zero` |
| 若连 E3 一起改名（案 A2） | 再 +3 生产 / +35 测试行 | `editor_epoch::` 字面量站点，含 `test_epoch_counter_sites_are_exactly_two` |
| 合计 | **A1 ≈ 5+3 生产 / 50 测试；A2 ≈ 8+3 生产 / 85 测试** | 约 90 处 diff 行 |

**收益评估**：改名后 `editor_` 前缀**空出来**可留给未来的全局 UI 键。但 §二 E6 已实测
全局 UI 键**一个都没有**，且 `code_editor` 的 theme 是硬编码（`ui/components.py:111/:113`）
⇒ 案 A 花 90 行 diff 买的是一个**当前不存在、且没有登记也仍然会撞**的东西。**结论：不划算，不推荐。**

### 案 B：显式登记表（零改名，把「谁负责清这个键」写成数据）

新增一个纯声明件（例：`ui/session_keys.py`），三张表：

```
GLOBAL_UI_KEYS   = {route, selected_lang, ai_variants, _problem_lru, ...}      # 永不清扫
WIDGET_STATE_PATTERNS = ("editor_", "run_", "reset_", "preask_", "gen_", ...)  # 登记为"Streamlit 自回收，人不扫"
PROBLEM_STATE_PATTERNS = ("code::", "chat_ctx::", "chat_history::",
                          "preask_hist::", "show_preask::", "editor_epoch::")   # 现 _PROBLEM_STATE_PREFIXES 的继任
```
清扫器改为：`if k in GLOBAL_UI_KEYS: continue` → `if 命中 WIDGET_STATE_PATTERNS: continue` →
其余按 `PROBLEM_STATE_PATTERNS`（含 pid 段精确匹配）清 ⇒ **E5 盲区当场消失**
（`editor_theme` 之类一旦写进 GLOBAL 就绝不会被误清，不靠形态猜）。

| 改动面 | 行数量 | 明细 |
|---|---|---|
| 新文件 | ~30–40 行 | `ui/session_keys.py`（三张 frozenset ＋ 60 行 docstring 说明判据） |
| 生产码改动 | **约 18 行**（净增 ~12） | `:44-45` 表定义改为 re-export/import；`:64-73`、`:105-113` 两处清扫循环改为查表 ⇒ 删 `rsplit` 猜测（`:72/:113` 两行） |
| 测试侧必改 | **9 行 / 3 个文件** | 钉 `_PROBLEM_STATE_PREFIXES == 6 项元组` 的三处：`test_editor_variant_keys.py:231`、`test_language_lru_eviction.py`（3 处）、`test_retire_variant.py`（5 处，含本单新档） |
| 语义要重写的断言 | 1–2 条 | 「widget 残键由 rsplit 精确匹配清掉」类断言（`test_revisit_after_eviction_restarts_at_epoch_zero` 的残键部分）——按 §三 实测它们**本来就不必成立** |
| 合计 | **~50 行净改动，其中生产码 18 行 / 测试 9 行** | 约为案 A 的 **1/2**，且**不动任何键名**（无兼容/迁移问题，会话中途不炸） |
| 风险 | 低 | 键名不变 ⇒ 在册字面量桩（`editor_epoch::{` 恰 2 处等）**不受影响**；只把「猜」换成「查」 |

**B′（推荐给主班的最小形态）**：只落 GLOBAL/PROBLEM 两张表，把 WIDGET 那一类**登记为「不扫」**
—— 即案 B 的实现，但**顺带删掉两处 `rsplit` widget 清扫**（`:66-73`、`:107-113` 共 14 行），
依据就是 §三 Q1/Q2 的实测：Streamlit 自己回收，人扫它是冗余。
⇒ 生产码净**减**约 5 行，`_retire_variant` 的六前缀循环保持不变（E3/E4 仍要人清）。
需要主班裁决的点：这会**翻掉 l923-15 的 `test_back_to_original_zeroes_both_key_families`
与 l922-113 的 LRU 残键断言**（它们用 FakeStreamlit 断言"人扫有效"），属"改判据"，
超出执行手授权 ⇒ 本档只出设计，不动码。

## 六、与同批 l924-03 的接缝（并**否证**其一条遗留）

- l924-03 已落地的 `_retire_variant` 同时清了 **E1/E2（widget 形）＋ E3/E4（计数器）＋ 五族状态键**。
  按 §三 实测，其中 E1/E2 那一刀在真实会话里是**冗余但无害**的（Streamlit 反正会回收），
  E3/E4 与五族那一刀是**必要**的。⇒ l924-03 不需要回退；本档只是说清「哪一半在真机上才有效」。
- **否证 l924-03 遗留问题 3**（同班自报，本班实测推翻）：该条担心
  `run_<pid>`/`reset_<pid>`/`chat_input_<pid>` 等「既不在表内也不以 editor_ 开头 ⇒ 无界增长」。
  §三 Q3 末态实测：这类 widget 键**只存在当前题那一份**（28 个"其它"键里 `run_/reset_/preask_/gen_`
  各 1 个，对应最后访问的那道题）⇒ **不累积，无需立单**。本班已在 result 里回写该更正。
- **真正的无登记漏口另有两处**（本档新发现，见遗留 R-3）：
  `lesson_chat::<lang>::<slug>` 与 `problem_select_<lang>_<slug>` **按专题线性增长**且不在任何表内。

## 七、遗留与交裁决出口

| # | 事项 | 为何不自行处置 |
|---|---|---|
| C-1 | 案 A / B / B′ 三选一 | 案 B′ 要**删两处在册清扫**并翻 3 条在册断言，属"改判据"，超出执行手授权 ⇒ 交主班 |
| C-2 | 「导航必须经 widget 键，写 `selected_*_idx` 会被覆盖」 | 属**测试夹具知识**，值得进仓内约定或 `tests/` 帮助件；本档只记录（§三 Q2 括注），不改测试 |
| C-3 | `lesson_chat::` / `problem_select_` 专题粒度键无逐出表 | 增长速率是"1/专题"，量级远小于"1/题"，**是否值得进表**属产品判断，未动 |
| C-4 | `ui/pages/dashboard.py:334` 注释仍写「editor_* 无界增长那类」 | 按 §三 该定性只对 `editor_epoch::` 成立。改它=改他单文案，未动 |
| C-5 | `editor_<pid>`（E5）历史形态是否**曾**在盘上存在 | 本档只证"今天无生产写入方"。若要确证历史从未出现，需翻 `git log -p ui/pages/language.py` 的旧拼法，本单预算内未做 |
| C-6 | 变式题「从不点退回」那半边（l923-15 遗留 3） | 需要第二终点（独立有界队列），不属 key 规范范围 |

## 八、本档改了哪些文件（交主班代提交；本班**未 add、未 commit**）

| 文件 | 状态 |
|---|---|
| `docs/insights/learn-editor-key-spec-20260924.md` | `??`（本档，新建） |
| `docs/insights/learn-insights-index-20260918.md` | ` M`（**同单登记**：表内新增本档 1 行 ＋ 档头对账读数追加 1 条，照 `l922-129 起生效`的"同班追加规则"） |

索引闭合复算（哨兵 `tests/test_insights_index_closure.py` 判的同一组量）：
登记前 A=68/B=68/C=空/重复 0 ⇒ 登记后 **A=69、B=69、C=空、重复=0**，等式闭合。
