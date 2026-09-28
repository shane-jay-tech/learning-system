# 变式题六族键的第二生命周期终点：独立有界队列 `_variant_lru`——l927-40，2026-09-28

> 执行：波次 43 代码写位子班 `qoder-executor-20260928-0300-learn54`，cwd `D:\code\learning-system`。
> 盘态：开班现取 HEAD `22a5325`、`git status --porcelain` 0 行；本单开工前该三件均为干净版。
> 卷宗：`zcode-bridge/inbox/l927-40.task.md`（做什么＝"补第二终态（离开/换题时清理六族键——
> 按档内设计的第二终点形态），补 1 例离开路径用例"）。
> 上游三处点名同一个修法（"出口一：独立有界队列"）：`done/l923-15.result.md` 遗留 3、
> `done/l924-03.result.md` 遗留 1、`docs/insights/learn-editor-key-spec-20260924.md` 遗留 C-6。

---

## 一、改了哪些行、为什么（生产码 `ui/pages/language.py`，+49 / −1）

| 现值行号 | 变化 | 内容 |
|---|---|---|
| `:55-61` | 改写（原 1 行 `return` → 3 行注释＋1 行转调） | `_touch_problem` 里 `AI_VARIANT::` 那支**不再直接 return**，改 `_touch_variant(active_id)` 后再 return ⇒ 真题侧 LRU 一概不认变式 id（两把队列互不打搅） |
| `:121-162` | 新增函数 `_touch_variant(variant_id)` | 第二终点本体：`_variant_lru` 队列，**先摘再挂**去重，`keep_ids = set(queue[-_LRU_CAP:])`，溢出项逐条 `_retire_variant(vid)`，末态 `st.session_state["_variant_lru"] = queue[-_LRU_CAP:]` |

三点照抄真题侧 `_touch_problem`、不另创口径：① 封顶沿用 `_LRU_CAP`（30），不新造第二个阈值；
② 逐出动作只调 `_retire_variant` ⇒ 清键面（六族 + `editor_<vid>_<epoch>` widget 残键）与
终点一「↩ 回到原题」**逐字同形**，判据由共享表 `_PROBLEM_STATE_PREFIXES` 单源给出；
③ 函数体内**不出现** epoch 计数器前缀的花括号字面量形态（在册桩 `test_brace_literal_sites_stay_exactly_two`
钉它恰 2 处，l923-15 实测踩过一次）。

为什么用队列而不是"离开当场清"：`ai_variants` 不因换题而弹出，用户切回来 `_active_problem`
取到的还是那道变式；当场清键＝把他刚写的代码换成 `starter_code`，比泄漏更重（与 l924-03
"只清被退回的那一道"同一判断）。队列把"无界"变成"≤30 道变式"，同时保留最近题态。

## 二、用例（判据②「补 1 例离开路径用例」＝本单给了 7 例）

新增 `tests/test_retire_variant.py::TestVariantSecondEndState`：

| 例 | 钉的失效面 |
|---|---|
| `test_leaving_variants_without_back_button_evicts_only_beyond_cap` | **判据②点名的离开路径**：刷 `cap+2` 道变式、一道都不点退回 ⇒ 只有最旧 2 道被清净（六族＋widget 全空），窗口内 30 道逐格完好，队列自身封顶 30 |
| `test_entering_a_variant_never_clears_its_own_state` | 进题当帧不清自己（用户代码不被 `starter_code` 覆盖） |
| `test_repeated_reruns_of_one_variant_do_not_flood_the_queue` | 同一 id 反复 rerun 只占一格 ⇒ "有界"不按交互次数漂移 |
| `test_back_and_forth_navigation_keeps_one_slot_per_variant` | A↔B 来回各 30 次 ⇒ 队列仍是 `[a, b]`（旧 `_problem_lru` 那套"只看队尾"会堆重复项） |
| `test_eviction_is_exact_and_spares_neighbour_and_base` | 逐出走精确拼键：以被逐 id **开头**的兄弟变式（`NEIGHBOUR_VID`）与原题六族零连坐 |
| `test_second_end_state_does_not_disturb_the_real_problem_lru` | 两把队列独立：35 道变式不得把真题挤出 `_problem_lru`，真题六族完好 |
| `test_evicted_variant_is_left_in_ai_variants_on_purpose` | **代价面钉子**（见 §三）：逐出后 `ai_variants` 仍挂着、重访 `_active_problem` 仍返回变式、epoch 归 0 |

动了的在册断言**只有两条**，另加一处连带翻面（逐字留痕在 `tests/test_retire_variant.py` 末尾
「🔴 l927-40 改桩记录」）：
1. `test_retire_defined_once_and_called_once`：`src.count("_retire_variant(") == 2`（字面量计数代理）
   → AST 点名调用者 `== ["_clear_variant_editor_keys", "_touch_variant"]`。**变严不是变松**——
   "多一处就红"这个代理被本单正当的第三处否证了，写回 `== 3` 只是把巧合当规矩；
   「不得挂进↺重置／✨生成变式分支」那半原意由同节 `test_not_wired_into_reset_or_generate_branches`
   一字未动地继续钉着。
2. `test_touch_problem_still_skips_variants`：**只订正 docstring**（旧半句"清理只发生在退回那一刻"
   不再完整），断言面一字未动且仍绿。
3. `tests/test_language_lru_eviction.py::TestAiVariantExemption::test_crowd_of_variants_cannot_push_real_problems_out`
   末段翻面（旧＝「`v0` 六族必须全在，生命周期短交页面自己管」这条**现状桩**；新＝`v0` 必须全空）
   ＋新增一格「窗口内最后一道 `v{cap+4}` 仍须全在」，防止有人改成"一律清光"也拿绿。
   前两格（`_problem_lru == [real]`、真题六族不被连坐）逐字照旧。

**没有**删例、**没有** xfail、**没有**放宽任何恒真断言；`tests/test_editor_variant_keys.py`
（l923-15 的 15 例，含按源文本字面量钉的「↩ 回到原题」调用式与顺序）**一字未动仍全绿** ⇒ 判据③
"退回原题路径不回归"。

## 三、代价与在册影响（如实登记）

1. 🔴 **被逐出的变式仍留在 `ai_variants` 里**（本单刻意不扩权）：30 道变式之后切回那道题，
   题面仍是变式，但 `code::` 回 `starter_code`、对话/提示/epoch 全部归零。与真题侧被 LRU
   逐出后重访**同形**，所以不算新发明；但它是可见的"回来代码没了"。要连 `ai_variants` 一起弹
   （重访直接回到原题）＝可见行为变更 ⇒ 交主班裁。该代价已由 §二 最后一例钉成"该红就红"
   （M5 变异：顺手弹 `ai_variants` ⇒ 恰 1 例红）。
2. **数量口径**：变式题态的在场上限从「本会话刷过的变式数（无界）」变成 `≤ _LRU_CAP = 30` 道，
   每道最多 6 族键＋若干 epoch widget 残键 ⇒ 长会话 session_state 里变式侧最多多出 30×6 键。
   `l924-04` §三 Q2/Q3 实测的"1 键/题线性增长"这一半（`editor_<pid>_<epoch>` widget 键）
   在真机上由 Streamlit 自回收，本终点清的是**人工写入那半**，两侧不重复计量。
3. **与 l924-04 案 B/B′ 的接缝**：本单没动键名、没建登记表、没删 `rsplit` 那两处 widget 清扫 ⇒
   案 A/B/B′ 三选一仍在主班手上（C-1）。本终点用的是 `_retire_variant` 现成判据，
   将来落 B′ 时这里**不用改形态**（同一函数），只换它内部的匹配方式。
4. **在册盲区未扩权**：缺 epoch 后缀的 `editor_<vid>` 形态依旧清不掉（要先定 key 规范，l924-04），
   本单不碰；`TestKnownBlindSpotPinned` 那条钉子原样在。
5. `_touch_variant` 的去重比真题侧 `_touch_problem` 严（先摘再挂 vs 只看队尾）。**没去改真题侧**
   （w42 §B.1，那是另一案的账；`test_repeat_visit_does_not_append_duplicate` 钉的就是它现有形态）。

## 四、判别力实验（`D:\code\tmp\qoder-executor-20260928-0300-learn54\mutate_l927_40.py`，
按原始字节改坏 → 跑五件定向 → `finally` 逐字节还原）

五件口径：`test_retire_variant / test_language_lru_eviction / test_editor_variant_keys /
test_language_editor_epoch / test_ui_behavior`。基线 `99 passed` rc=0，
末次 `还原校验 byte-identical: True`（工作树行尾实测 LF、bareLF 0 混入）。

| 变异 | 含义 | 结果 | 转红的例 |
|---|---|---|---|
| M1 | 回到旧形态（变式完全豁免、不摸队列） | `6 failed, 93 passed` | 离开路径／堆队列／来回切题／精确不连坐／代价钉子 ＋ lru 件那条翻面例 |
| M2 | 队列照维护但逐出时不清键（第二终点空转） | `5 failed, 94 passed` | 上述 4 类中的 4 例 ＋ **AST 调用点钉子**（`test_retire_defined_once_and_called_once`） |
| M3 | 去掉队列去重 | `2 failed, 97 passed` | 堆队列／来回切题 |
| M4 | 窗口收窄成 1 格 | `1 failed, 98 passed` | 离开路径（"窗口内 30 道必须完好"那格独立有牙） |
| M5 | 逐出时顺手弹 `ai_variants` | `1 failed, 98 passed` | 代价面钉子（唯一 keeper） |

## 五、复算命令（cwd `D:\code\learning-system`，需 `PYTHONIOENCODING=utf-8`）

```
$ git rev-parse --short HEAD && git status --porcelain | wc -l
22a5325 / 0                                   # 开班基线
$ python -m pytest tests/test_retire_variant.py tests/test_language_lru_eviction.py \
    tests/test_editor_variant_keys.py tests/test_language_editor_epoch.py \
    tests/test_ui_behavior.py tests/test_ai_generate.py tests/test_judge_result_per_pid.py \
    tests/test_progress_recovery_consistency.py tests/test_app_flow.py -q
133 passed                                    rc=0        # 判据②③
$ python -m pytest tests/test_retire_variant.py tests/test_language_lru_eviction.py --collect-only -q
45 tests collected                            # 本文件 34（HEAD 27 ＋ 本单 7）＋ lru 件 11
$ python -m pytest tests/test_insights_index_closure.py -q
预期红（本班新增 l927-37／l927-39／l927-40 三份档未登记）⇒ 交主班随代提交补登
```
未跑全量（w40 §5 同仓并发不可归因；全量口径交主班收班取）。
零写库：全程 `FakeStreamlit` 会话态，`data/progress.db` 未连接；
题件 `*.yaml`／`core/judge.py`／分值判分**一字未碰**（本单只动 session_state 键生命周期）。
