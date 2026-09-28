# A／B／B′ 变式题三选一的终版裁决材料（l927-41，只读 · 不动桩 · 不动生产码 · 零 git）

> **卷宗**：`zcode-bridge/inbox/l927-41.task.md`（收口时移 `done/`）｜上游＝`zcode-bridge/done/l924-04.result.md`
> 遗留 1 与 `docs/insights/learn-editor-key-spec-20260924.md` §五／§七 C-1（「案 A/B/B′ 三选一未拍」）。
> **本班**：`qoder-executor-20260929-0345-learn61`，只读位，2026-09-29T03:5x 全部读数现取。
> **盘态**：HEAD `18c6d2d`、`git status --porcelain` ＝ **0 项**（开工／收班两点同值）。
> **红线自证**：`ui/pages/language.py` sha1 `bb940bd6…` 与 `core/ai_review.py` sha1 `d9ee8e22…` 在**变异跑前／跑后**
> 逐字同值；四份在册测试件一字未动；strict-XFAIL 两桩（`test_sql_roworder_fragile.py`／
> `test_paths_order_consistency.py`）未碰；**判定留人工／主班**，本档只出材料与推荐，不下裁决。

## 〇、结论先行（五条，第三条否证设计稿的核心论据）

1. **三案在 HEAD 全部仍可实施，锚点未漂但行号已漂**。设计稿按 `38ad3bb`＋l924-03 在途工作树取号，
   现号：生成 `:41`、LRU 判据 `:73`/`:75`、retire 判据 `:114`/`:116`（旧 :41/:69/:71/:110/:112）。
2. 🔴 **B′ 的断言翻转面不是 3 条，实测 20 例**（跨 5 份在册测试件；复现见 §三／§四）。
   膨胀的成因不是设计稿算错，而是它之后**又落了两批建立「人扫有效」的在册桩**：
   l924-03 的 `tests/test_retire_variant.py`（本域 10 例）与 l927-40 的 `TestVariantSecondEndState`（3 例）。
3. 🔴 **「B′ 是省成本的最小形态」这条核心论据被实测否证**：案 B 与 B′ 的翻转集**逐例同一**
   （同一 20 例、同一顺序、同一红因）。⇒ B 与 B′ 的取舍**不在测试成本**，只在
   「要不要那张登记表」（B 买回 E5 盲区的登记式解法，B′ 不买）。
4. **实测出一个零翻面出口（本档新增＝案 D「登记不删扫」）**：只落三张表、两处清扫循环一字不动 ⇒
   点名 8 件 **147 passed、红 0**。设计稿没有这一格，而它恰好把「查登记」的收益先拿到手、
   把「删清扫」的判据风险留到真浏览器证据到位之后。
5. **推荐**（供拍板，不代拍）：默认**维持现状**；若人工要推进 key 规范，**推案 D 而非 B′**——
   B′ 用 20 条在册判据换 16 行代码瘦身、且不留登记；**不建议案 A**（实测 29 例红，且至少 2 例
   会退化成「空转型绿」，见 §二 末）。判分口径不涉本域，但**删在册清扫＋改写 20 条判据属
   「放宽判据」相邻面**，按波次纪律只出材料。

## 一、前提复点（设计稿四条实测前提在 HEAD 的现状，逐条命令）

| # | 设计稿前提 | HEAD 复点读数 | 判定 |
|---|---|---|---|
| P1 | `editor_*` 命名空间里全局 UI 键＝0（`editor_theme` 盘上不存在） | `$ rg -n "editor_theme" --glob '!tmp/**' --glob '!docs/**' .` → **3 命中，全在非生产侧**：`tests/test_language_lru_eviction.py:143`/`:146`（假件自造的全局键）、`tests/test_retire_variant.py:430`（docstring 举例）⇒ 生产写入方仍 **0** | ✅ 未漂 |
| P2 | `code_editor` 的 theme／font_size 是硬编码、不落 session_state | `$ rg -n "theme=\|font_size=" ui/components.py` → `111: theme="tomorrow_night"`、`113: font_size=15`（与设计稿同号） | ✅ 未漂 |
| P3 | 「widget 键不累积」只在 AppTest 下成立，**真浏览器仍未目检** | 设计稿 §三 括注的适用边界原样在册；本单**未新增**任何真机证据（只读位、无浏览器） | ⚠ 仍欠，见遗留 R-2 |
| P4 | C-4：`dashboard` 注释仍写「editor_* 无界增长那类」 | `$ rg -n "editor_\* 无界增长" ui/pages/dashboard.py` → **`:365`**（旧号 :334，前人在上方插过行） | ⚠ 账仍在，非本单可改 |
| P5 | C-6：变式题「从不点退回」那半边无终点 | **已闭**：`ui/pages/language.py:121 _touch_variant`／`:59` 路由／`:161` 逐出走 `_retire_variant`（随 `e9a1606`＝l927-40 入库）⇒ 设计稿 §五 的改动面数字**不能照抄**，清扫循环现在被**两条**生命周期共用 | 🔴 已过期，本档按现体重算 |

## 二、三案现值（设计稿口径 vs HEAD 实测；变异探针两向对照见 §四）

| 案 | 生产码面（设计稿 9-24） | 生产码面（HEAD 实测） | 测试面（设计稿） | **断言翻转（HEAD 实测）** |
|---|---|---|---|---|
| **A** 前缀改名（widget 键让出 `editor_`） | 必改 5 行＋注释 3 行 | 必改 **5 行**＝`:41`/`:73`/`:75`/`:114`/`:116`；点名键形的注释 **`:70`、`:111-112`** ＋ docstring **`:85`**（另 `:82`/`:137` 两处散文提及「widget 残键」，无键形字面量） | 50 行 / 7 文件 | **29 例红 / 147**（跨 6 件）；字面量面现值 **110 行 / 8 文件**（`$ rg -n "editor_" tests/ -g '*.py' \| rg -v "editor_epoch::" \| wc -l`） |
| **B** 显式登记表（零改名） | 新件 ~30–40 行＋生产 18 行＋测试 9 行 / 3 文件 | 新件（三张 frozenset）＋本文件 `:44-45` 改 import；两处 rsplit 循环改查表 ⇒ 本档替身实测 **−13 行** | 6 站点钉 `_PROBLEM_STATE_PREFIXES`：`test_editor_variant_keys.py:231`、`test_language_lru_eviction.py:66`/`:70`、`test_retire_variant.py:275`/`:276`/`:281`（若 B 保留该模块级名字 ⇒ 这 6 站不红，实测如此） | **20 例红 / 147**，与 B′ **同一集** |
| **B′** ＝ B ＋ 删两处 widget 清扫 | 共删 14 行（`:66-73`＋`:107-113`）、生产净减 ~5 行 | **删 16 行**＝`:70-77`（8）＋`:111-118`（8），变异体 642 行 vs 原 658 行（−16） | 「翻 3 条在册断言」（l924-04 遗留 1） | **20 例红 / 147**，逐条清单见 §三 |
| **D**（本档新增出口）登记不删扫 | — | 只加三张表（替身在本文件 ＋5 行；正式形态是新文件 ~30 行），两处循环**一字不动** | 无需改 | **0 例红 / 147 passed** |

**A 与 B′ 的集合关系（不是包含）**：交集 **16** 例、A 独有 **13** 例、B′ 独有 **4** 例
（`comm -12/-13/-23` 对 `tmp/l927-41/a_ids.txt`／`bprime_failures.txt`，配方在 §四）。
⚠ A 独有 13 例里有一类**反向风险**：改名后 `tests/test_editor_variant_keys.py:81`
`test_back_to_original_zeroes_both_key_families` 与 `:107` `test_touch_problem_still_skips_variants` 的
辅助函数 `_widget_keys()`（按 `startswith("editor_" + vid)` 计数）会**数不到任何东西**——
前者因此「空转型绿」（断言仍成立但零判别力），后者红。这正是纪律档 §廿七「静默失明的绿」的形状，
写单执行 A 时必须连同夹具一起改名，不能只改生产侧。

## 三、B′ 的三条断言翻转清单 → HEAD 现值 20 例（逐条，含红因）

红因只有两类：**行为面**（断言「人扫把 widget 残键清掉了」）与**文本面**（源文本桩钉 rsplit 判据在位）。

### `tests/test_retire_variant.py`（10 例：l924-03 ＋ l927-40 两批）

| 行 | 例 | 类别 | 红因（B′ 下的失效点） |
|---|---|---|---|
| :114 | `test_retire_variant_empties_all_six_prefixes_and_widgets` | 行为 | 例名自带「and_widgets」；`_pid_keys` 把 3 个 widget 残键计入应清面 |
| :120 | `test_widget_sweep_clears_every_stale_epoch` | 行为 | **本域最直白的一根钉子**：5 个 epoch 残键要求清空 |
| :125 | `test_retire_is_idempotent_and_tolerates_absent_keys` | 行为 | 末行 `_pid_keys(...) == set()` 含 widget |
| :133 | `test_regenerated_variant_starts_clean` | 行为 | 「只取 key 就留下残键」断言 |
| :149 | `test_shim_clears_all_six_families_too` | 行为 | 薄壳清键面＝六族＋widget |
| :216 | `test_neighbour_variant_keeps_all_six_families` | 行为 | 红在 :222「VID 应已清空」那半 |
| :279 | `test_retire_iterates_the_shared_table` | **文本** | `assert 'rsplit("_", 1)' in src` ⇒ 删循环即红（B 若保留 rsplit 则不红） |
| :329 | `test_leaving_variants_without_back_button_evicts_only_beyond_cap` | 行为 | l927-40 第二终点：被逐出变式要求「`_pid_keys == set()`」 |
| :373 | `test_eviction_is_exact_and_spares_neighbour_and_base` | 行为 | 同上（队列路径的精确拼键断言） |
| :402 | `test_evicted_variant_is_left_in_ai_variants_on_purpose` | 行为 | 代价面钉子，前半「VID 应已被逐出」含 widget |

### `tests/test_editor_variant_keys.py`（6 例：l923-15）

| 行 | 例 | 类别 | 红因 |
|---|---|---|---|
| :81 | `test_back_to_original_zeroes_both_key_families` | 行为 | **设计稿点名的那一条**：`_widget_keys == []` |
| :87 | `test_clear_is_idempotent_and_tolerates_missing_counter` | 行为 | 同上 |
| :97 | `test_regenerated_variant_starts_at_epoch_zero` | 行为 | 同上 |
| :110 | `test_other_variants_keep_their_keys_and_epoch_value` | 行为 | 红在 :117「VID 的 widget 键应清空」 |
| :124 | `test_base_problem_editor_state_survives` | 行为 | 红在 :135 同一形状 |
| :137 | `test_similar_variant_id_not_collateral_damaged` | 行为 | 红在 :143「VID 自己的 epoch 残键没清掉」 |

### `tests/test_language_lru_eviction.py`（2 例：l922-113）／`tests/test_language_editor_epoch.py`（1 例）／`tests/test_ui_behavior.py`（1 例）

| 行 | 例 | 类别 | 红因 |
|---|---|---|---|
| :51 | `TestSixPrefixCensus::test_all_six_prefixes_cleared_for_evicted_problem` | 行为 | :60 明确要求 `editor_<pid>_` 零残留 |
| :103 | `TestEditorEpochKeyPrecision::test_similar_pid_not_collateral_damaged` | 行为 | 该例的**存在理由**就是 rsplit 精确匹配（:114 断言 victim 多 epoch 残键全清） |
| :145（文件内） | `test_language_editor_epoch.py::TestCrossTalkWithLruEviction::test_revisit_after_eviction_restarts_at_epoch_zero` | 行为 | 其断言消息原文写着「旧 epoch 残键应由 LRU 的 rsplit 清扫带走」 |
| :—（文件内） | `test_ui_behavior.py::test_problem_state_lru_prunes_old_problems` | 行为 | l922-113 建档前就存在的那份**粗覆盖**，同样按「editor 键消失」断言 |

**仍绿且必须原样保留的相邻桩**（勿顺手改）：`test_language_lru_eviction.py:137`
`test_undiscussed_editor_widget_keys_are_left_alone`（全局键 `editor_theme` 不被扫）、
`test_retire_variant.py:434` `test_suffixless_editor_key_still_survives`（E5 盲区现状钉）、
六前缀表的 6 处站点钉（B 若保留名字则全绿）、`test_retire_variant.py:258` 的 `editor_epoch::{` 恰 2 处。

> **口径对照**：设计稿的「3 条」＝`test_back_to_original_zeroes_both_key_families` ＋
> l922-113 的 LRU 残键断言（当时 2 条）。HEAD 现值 **20**：新增的 17 例全部来自 9-24 之后
> **合法入库**的后续账（l924-03 的 10 例、l927-40 的 3 例、`test_ui_behavior` 的粗覆盖、
> `test_editor_variant_keys` 的另外 5 例）。⇒ done 档不可回改，请主班在 l924-04 那行台账加注。

## 四、取证配方（每条可复算；cwd `D:/code/learning-system`）

变异纪律：l927-56／l924-09 同型——**内存／tmp 副本注入**，零改生产文件、零改测试文件。
探针三件（`tmp/` 已 gitignore：`.gitignore:19:/tmp/`，`git check-ignore -v tmp/` rc=0）：
`tmp/l927-41/make_variants.py`（五份变异体）、`tmp/l927-41/l927_41_plugin.py`（把变异体 exec 进
`ui.pages.language.__dict__` 并把 `__file__` 指过去，使**源文本桩**读到与真实裁决后一致的文本）、
`tmp/l927-41/make_cache_variants.py`＋`l927_41_cache_plugin.py`（§六 缓存域复点）。

点名 8 件＝`rg -l` 全量复点后确定的**唯一消费者集合**（`tests/` 内命中 `_touch_problem|_retire_variant|_clear_variant_editor_keys` 的只有 5 件，另 3 件是 editor_ 字面量的外部消费者）：
`test_editor_variant_keys.py`／`test_language_editor_epoch.py`／`test_language_lru_eviction.py`／
`test_retire_variant.py`／`test_ui_behavior.py`／`test_app_flow.py`／`test_judge_result_per_pid.py`／
`test_parser_boundary_inputs_20260925.py`。

```bash
$ sha1sum ui/pages/language.py
bb940bd607417c579cd09a4261665979c48a3ae7 *ui/pages/language.py      # 跑前＝跑后
$ PYTHONIOENCODING=utf-8 python tmp/l927-41/make_variants.py
language_a.py: 658 行（原 658 行，差 +0）
language_b.py: 645 行（原 658 行，差 -13）
language_bprime.py: 642 行（原 658 行，差 -16）
language_control.py: 658 行（原 658 行，差 +0）
language_d.py: 663 行（原 658 行，差 +5）
$ F="tests/test_editor_variant_keys.py tests/test_language_editor_epoch.py tests/test_language_lru_eviction.py tests/test_retire_variant.py tests/test_ui_behavior.py tests/test_app_flow.py tests/test_judge_result_per_pid.py tests/test_parser_boundary_inputs_20260925.py"
$ PYTHONIOENCODING=utf-8 PYTHONPATH=tmp/l927-41 L927_41_VARIANT=control python -m pytest $F -q -p l927_41_plugin
147 passed in 5.84s          # 两向对照的绿侧：插件本身中性
$ ... L927_41_VARIANT=bprime python -m pytest $F -q --tb=no -rf -p l927_41_plugin
20 failed, 127 passed in 5.44s
$ ... L927_41_VARIANT=b python -m pytest $F -q --tb=no -rf -p l927_41_plugin
20 failed, 127 passed in 5.42s
$ PYTHONIOENCODING=utf-8 PYTHONPATH=tmp/l927-41 L927_41_VARIANT=b ... | rg "^FAILED" | sed 's/^FAILED //' | sort > tmp/l927-41/b_ids.txt
$ ... 同法产 tmp/l927-41/bprime_ids.txt
$ diff tmp/l927-41/b_ids.txt tmp/l927-41/bprime_ids.txt && echo "同一集：逐例一致"
同一集：逐例一致            # 🔴 §〇.3 的证据：B 与 B′ 翻的是同 20 例，差集空
$ ... L927_41_VARIANT=a python -m pytest $F -q --tb=no -rf -p l927_41_plugin
29 failed, 118 passed in 6.43s
$ ... L927_41_VARIANT=d python -m pytest $F -q -p l927_41_plugin
147 passed in 5.39s          # 案 D 零翻面
$ git status --porcelain | wc -l
0                            # 变异跑完仍零脏件（探针件全在 gitignore 的 tmp/）
```

未跑全量套件（波次纪律：同刻 5 路兄弟班；全量现值 1206/7/2 由主班 03:3x 取，本档不引用为判据）。
定向合跑数与 §〇 一致：4 件 73 passed（控制）⇒ 8 件 147 passed。

## 五、推荐与出口（判定留人工／主班）

| 出口 | 一句话 | 实测代价 | 本班态度 |
|---|---|---|---|
| 维持现状 | 三案都不拍，key 规范停在设计稿 | 0（20 例判据继续有效） | **可作默认**：现状已被 20 例钉死，泄漏面在假件世界里有人扫 |
| **案 D**（登记不删扫） | 先落三张表把 E5 盲区从「猜形态」改成「查登记」，清扫照旧 | **0 例红** ＋ 新件 ~30 行 | **推荐**（本档新增出口，实测支撑） |
| 案 B | 登记表＋人不扫 widget 键 | 20 例红（含 1 文本桩） | 若人工接受「假件不再钉人扫」，B 严格优于 B′（同成本、多买 E5 解法） |
| 案 B′ | 同 B，另物理删 16 行 | 20 例红 | **不再推荐**：设计稿给它的「省成本」理由经实测不成立（与 B 同集），收益只剩 16 行瘦身 |
| 案 A | widget 键形改名让出 `editor_` | 29 例红 ＋ 至少 2 例空转型绿 ＋ 110 行字面量面 | **不建议**：收益对象（`editor_` 下的全局 UI 键）实测仍为 0（§一 P1） |

**若拍 B/B′，写单必须同笔做的三件事**（防「新桩红着入库」）：
① 20 例逐条改写或降级为「Streamlit 自回收」说明桩，**不得用 xfail／不得删文件**充数；
② `test_retire_variant.py:279` 的文本桩要同步换判据（它钉的是 `rsplit` 在位）；
③ `_retire_variant` docstring `:82`「六族题目状态键 + editor widget 残键一次清净」与
`_touch_variant` 的 `:137` 同句属**注释文本义务**，不改即留假台账（在册无哨兵拦，靠人盯）。

**待人工清单**：
1. 三案（或本档的 D／现状）选一——**裁决授权仍不在盘**（本班 03:5x 现点三处）：
   `$ rg -n "三选一仍在主班手上" docs/insights/` → 唯一出处 `l927-40-lifecycle2.md:73`
   （09-28 入库，晚于 l924-04 ⇒ 至今未拍，且它自己确认「没删 rsplit 那两处 widget 清扫」）；
   `$ rg -n "已拍|拍板通过|选案已" docs/ -g '*.md'` → 3 命中全属**别域**（去重链／r 降级／末档难度），无一条是 key 规范；
   信箱侧 `ls D:/code/zcode-bridge/{inbox,done,outbox}/l927-41*` → 只有本班卷宗与本结果件。
   ⚠ 更正一处上游口径：l927-56 引的待人工台账 `docs/insights/drain-20260923-pending-human.md`
   **不在本仓**（`ls docs/` ⇒ 只有 `insights/` ＋三份 `system-report-v0.6.x.md`；`rg` 该路径报 os error 2），
   本仓也无 `docs/decisions/` 目录 ⇒ 授权查盘只能走上面三条，台账类文件执行手一律不代登。
2. **真浏览器目检**「widget 键不累积」（§一 P3）——这是删清扫那一半的唯一前置，执行手做不了。
3. 案 A 若被重新提名，先认「夹具连带改名」的口径（§二 末）。
4. C-4（`ui/pages/dashboard.py:365` 注释口径）仍挂他单账。
5. 本产出件**未自登索引** ⇒ `tests/test_insights_index_closure.py` 预期红两格（C 多出本档）。
   本班收班实测：写档前 **3 passed**（A=125／B=125／C 空），登索引后须复跑。

## 六、点名：派单提示词与本卷宗不同域（口径串案）

派单提示词给本单写了「⚠ 在册事实：**案 B（LRU-rw）** 需同改 3 条在册桩（`:120`＋`:134`＋`:216`），
l927-56 的六枚新桩已随 `6323fde` 在册 ⇒ HEAD 时点改写面＝**7 条断言＋1 处注释文本义务**」。
**那组编号属 `core/ai_review.py` 点评缓存的 FIFO⇄LRU 两案（l927-35／l927-56／l924-20），
不属本卷宗（l924-04 遗留的 A／B／B′ `editor_*` 键规范三案）**——两域都叫「案 B」、都涉及「变式题」，
且 `test_ai_review_strategy.py` 的新 4 正是 `test_variant_pid_entries_are_evicted_by_same_fifo_rank`，
极易串案（l927-56 §二 已就 `_problem_lru`／`_variant_lru` vs LLM 点评缓存做过「勿串案」登记）。
**按波次纪律以卷宗为准**，本档正文因此全部走 key 规范域；提示词那组数字另行独立复点如下，**复现成立**：

```bash
$ rg -n "def test_cache_feedback_trim_boundary|def test_cache_feedback_reinsert|def test_code_and_open_caches_share" tests/test_ai_review_strategy.py
120:...  134:...  216:...                       # 旧三桩现号未漂（与 l927-56 逐一对齐）
$ rg -n "def test_cache_read_hit_does_not_refresh|def test_open_result_reinsert|def test_both_write_paths_share|def test_variant_pid_entries|def test_feedback_cache_capacity_constant|def test_cache_section_comment" tests/test_ai_review_strategy.py
267:  286:  305:  333:  367:  382:              # l927-56 六枚新桩现号未漂，且已随 6323fde 在册（git merge-base --is-ancestor ⇒ YES）
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_ai_review_strategy.py -q
25 passed in 0.05s
$ sha1sum core/ai_review.py
d9ee8e22cf12cdf8b6d3e91a696002dd63a4949d        # 与 l927-56／l927-35 登记值同，跑前＝跑后
$ PYTHONIOENCODING=utf-8 PYTHONPATH=tmp/l927-41 L927_41_CACHE_VARIANT=control python -m pytest tests/test_ai_review_strategy.py -q -p l927_41_cache_plugin
25 passed in 0.05s                               # 控制：插件中性
$ PYTHONIOENCODING=utf-8 PYTHONPATH=tmp/l927-41 L927_41_CACHE_VARIANT=lrurw python -m pytest tests/test_ai_review_strategy.py -q --tb=no -rf -p l927_41_cache_plugin
7 failed, 18 passed in 0.05s
  红＝:120 /:134 /:216（旧三桩）＋:267 /:286 /:305 /:333（l927-56 新 1/2/3/4）
  绿＝:367（容量常量桩）/:382（FIFO 注释文本桩）⇒ 二者即"第 8 项义务"的两个靶
```
⇒ **「7 条断言＋1 处注释文本义务」在本班独立变异下逐例复现**（本班用 tmp 副本＋`__file__` 重指，
故文本桩读到的是未改注释的副本 ⇒ :382 仍绿；真实改注释时它必红，与 l927-35 §二 同判）。
该域的裁决仍属 l927-35 的材料（其推荐＝维持 FIFO），**本单不重复裁决、不新增数值结论**。

## 七、产出与盘态（交主班按精确路径代提交）

| 文件 | 状态 |
|---|---|
| `docs/insights/l927-41-variant3cases.md` | `??` 本档（新建） |
| `docs/insights/learn-insights-index-20260918.md` | **未改**（索引由主班单点写；建议行文本见 result） |
| `tmp/l927-41/*` | 探针件，gitignore 内，零入库 |

复算等式（写档前后）：写档前 A=125／B=125／C 空／哨兵 3 passed；本档落盘后 A=126／B=125 ⇒
`test_闭合等式_A等于B_且C为空_且无重复` 与 `test_新档漏登记必红_改名必红_有牙自检` **预期红**，
须与索引行同笔入库才闭合。

**收班读数（2026-09-29T03:56+08:00 现取）**：

```
$ git status --porcelain
?? docs/insights/l927-41-variant3cases.md          # 脏件恰 1 项＝本档，零夹带
$ sha1sum ui/pages/language.py core/ai_review.py
bb940bd607417c579cd09a4261665979c48a3ae7           # 与开工同值（生产码零改动）
d9ee8e22cf12cdf8b6d3e91a696002dd63a4949d           # 与 l927-56／l927-35 登记值同
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_editor_variant_keys.py tests/test_language_editor_epoch.py \
  tests/test_language_lru_eviction.py tests/test_retire_variant.py tests/test_ui_behavior.py \
  tests/test_app_flow.py tests/test_judge_result_per_pid.py tests/test_parser_boundary_inputs_20260925.py -q
147 passed in 5.96s                               # 产出档落盘后点名件全绿（未动任何桩）
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q
2 failed, 1 passed in 0.09s                       # 预期红＝本档未自登索引（主班补登后转绿）
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_ai_review_strategy.py -q
25 passed in 0.05s                                # §六 缓存域复点用件，一字未动
```

