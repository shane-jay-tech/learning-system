# FIFO→LRU 升级影响面与测试改写清单·两案裁决材料（l927-35，只出材料 · 不动桩 · 不动生产码 · 零 git）

> **卷宗**：`zcode-bridge/inbox/l927-35.task.md`（本班收口时已移 `done/`）。上游依据＝`zcode-bridge/done/l923-05.result.md` 遗留问题 1（「FIFO 本身没改……复写同键不刷新顺位这个 FIFO 语义是否要升级成真 LRU（move_to_end）本单无权决定」）。
> **在册前案两份**：① l924-20 裁决稿 `docs/insights/learn-review-cache-lru-verdict-20260924.md`（三态定义、合成 trace 命中率、案 0/A/B/C/D 案序）；② l927-56 衔接档 `docs/insights/l927-56-note.md`（断言面补齐 6 例已入库、三态变异矩阵、否证 l924-20「同改 2 例」口径）。本档不重复二者设计，补的是**两案对照＋推荐＋按 HEAD 现值重算的改写清单**。**判定留人工，本班不下通过判定。**
> **本班**：`qoder-executor-20260929-0307-learn60`，只读位，2026-09-29 03:1x 全部读数现取（HEAD `6323fde`）。

## 一、锚点与前提复核（每条实测）

| # | 前提 | 现取读数 | 命令（cwd `D:/code/learning-system`） | 判定 |
|---|---|---|---|---|
| 1 | 锚点句仍在 | `zcode-bridge/done/l923-05.result.md` 遗留 1 逐字含「是否要升级成真 LRU（move_to_end）本单无权决定」 | `head -40 zcode-bridge/done/l923-05.result.md` | ✅ |
| 2 | 现状＝FIFO，注释与实现一致 | `core/ai_review.py:44-52` 头注释明示「淘汰语义是 FIFO」；写路径 `_cache_feedback :59-66`／`_cache_open_result :95-102` 复写同键不 `move_to_end`，淘汰 `popitem(last=False)`；读路径 `:69-71`／`:105-109` 无任何刷新 | `sed -n '40,110p' core/ai_review.py` | ✅ 全仓 `OrderedDict`+`popitem` 形态仅这只缓存（l927-56 §二 复核过，本班 sha1 复点 `d9ee8e22…` 未变） |
| 3 | 三枚在册旧桩行号未漂 | `tests/test_ai_review_strategy.py` `:120` `trim_boundary_is_strictly_over_capacity`／`:134` `reinsert_updates_value_but_not_eviction_rank`／`:216` `share_one_trim_budget` | `grep -n "def test_cache_feedback_trim_boundary\|def test_cache_feedback_reinsert\|def test_code_and_open_caches_share" tests/test_ai_review_strategy.py` | ✅ 行号与 l927-56 档逐一对齐 |
| 4 | 该件现役全绿 | **25 passed, 0.06s**（l927-56 入库后 19→25 例口径吻合） | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_ai_review_strategy.py -q` | ✅ |
| 5 | 裁决授权仍不在盘 | 本班开工前 `outbox/done` 均无 `l927-35.result.md`；l924-20／l927-56 两档抬头均明写「选案交人工」 | `ls zcode-bridge/done/l927-35* zcode-bridge/outbox/l927-35*`（收口时点仅本班骨架在位） | ✅ 未拍板属实，本档即那张材料 |

## 二、🔴 复点「案 B 需同改几条在册桩」（在册现值 3 条的独立复现，不抄旧数）

复现手段：重放 l927-56 的内存假件驱动器（零改生产文件、零改测试文件，纪律 §十三.7 同型）：

```bash
$ sha1sum core/ai_review.py
d9ee8e22cf12cdf8b6d3e91a696002dd63a4949d  core/ai_review.py     # 跑前＝跑后，逐字未动
$ PYTHONIOENCODING=utf-8 python D:/code/tmp/qoder-executor-20260928-1620-learn59/mut_probe.py
```

本班 09-29 03:1x 实跑矩阵（🔴＝红）：

| 例（归属） | FIFO（现役） | LRU-w（写刷新） | LRU-rw＝案 B（读写都刷新） |
|---|---|---|---|
| 在册旧三桩 :120 `trim_boundary` | 绿 | 绿 | 🔴 |
| 在册旧三桩 :134 `reinsert…not_eviction_rank` | 绿 | 🔴 | 🔴 |
| 在册旧三桩 :216 `share_one_trim_budget` | 绿 | 绿 | 🔴 |
| l927-56 新 1 `cache_read_hit_does_not_refresh`（:267） | 绿 | 绿 | 🔴 |
| l927-56 新 2 `open_result_reinsert`（:286） | 绿 | 🔴 | 🔴 |
| l927-56 新 3 `both_write_paths_share_one_insertion_rank`（:305） | 绿 | 🔴 | 🔴 |
| l927-56 新 4 `variant_pid_entries_are_evicted_by_same_fifo_rank`（:333） | 绿 | 🔴 | 🔴 |
| l927-56 新 5 `capacity_constant`（:367）／新 6 `comment_still_self_describes_fifo`（:382） | 绿 | 绿 | 绿（两桩的靶分别是常量与**文件文本**：内存假件不动文件 ⇒ 三态皆绿是设计使然，见下"注释同笔"） |

| 在册 :177 `isolates_dimensions`／:233 `namespaces_never_collide` | 绿 | 绿 | 绿（与顺位正交，勿顺手改） |

**读数结论**：
1. **旧档核对**：l924-20 §三 的「改 LRU-rw 需同改 2 例（:120＋:134）」被本班复跑**否证**（:216 在 LRU-rw 下红，红因：`:225` 读命中把 o0 救到队尾 ⇒ `:228` 断言反）。
2. **在册现值「案 B 需同改 3 条在册桩」复现成立**：按 l927-56 的口径（"在册桩"＝l922-10 批次旧三桩），LRU-rw 红 **3** 条＝`:120＋:134＋:216`，与主班 9-28 实测一致。✅ 数字复现，非抄写。
3. ⚠ **本班给出更宽一格的本征读数（不冲突，是口径差）**：l927-56 那 6 枚新桩**已随 6323fde 入库成为在册**，其中 4 枚（新 1/2/3/4）钉的正是 FIFO 顺位 ⇒ **以 HEAD 时点算，拍 LRU-rw 的断言改写面是 7 例**（旧三桩＋新 4 枚），拍 LRU-w 是 4 例；另有第 8 项义务——`core/ai_review.py:49-52` 头注释的**文本**必须同笔订正，且订正后新 6 必红（它逐字要求注释仍明示 FIFO＋保留两句历史指涉句式，函数体 :382-398）⇒ "改语义不改注释"由新 1/2/3/4 与旧三桩红兜住、"改了注释"由新 6 红兜住——两侧都强制升级必须**当面处理这枚文本桩**，不存在无声漂移通道；本班复跑三态皆绿恰因内存假件不动文件文本，靶位由此自证。引"3 条"没错但**只说"3 条"会漏**——写单若执行裁决，改写清单以本表 7＋1 为准。

## 三、影响面分析（完成标准①）

**行为差异面（缓存命中语义，FIFO→LRU-rw）**——数字全部引 l924-20 §四合成 trace（内存沙盒，`random.seed(20260925)` 可复算；本班未重算数值、不下新数值结论）：

- trace-1（工作集 403 题 ≫ 容量 64，现役常态）：命中率 FIFO 15.2% → LRU-rw **15.2%（+0.0pp）**——工作集远超容量时策略被容量瓶颈淹没。
- trace-2（单会话聚焦，工作集 ≤ 容量）：43.2% → **46.0%（+2.8pp）**，浪费 LLM 调用 −109/4000 事件。
- **LRU-w（只加写路径 `move_to_end`）收益实测恰为 0**（写只发生在 miss 之后，"写时刷新"＝没刷新）——l924-20 案 D「不建议」的数据根。
- 对比项：同一 trace 里容量 64→192 使 trace-1 命中 +31.7pp——**策略改动的收益被容量杠杆碾压一个数量级**。
- 结构性事实：两类键（代码点评／开放题）共用一只 `OrderedDict` 共用 64 容量（`:47-48` 注释自述），升 LRU **不解决**跨类挤占（那是案 A 分池的靶，`:216` 钉的就是它）；键形是全码 sha1（l924-20 §〇 否证「改一个字再跑一次也命中」的注释口径，已由 l923-05 订正为"逐字重复提交才命中"）——LRU 改变不了"改一字必新键"。

**测试改写清单（若拍案 B LRU-rw，HEAD 现值）**：

| # | 件:行 | 例名 | 需要的动作 | 口径 |
|---|---|---|---|---|
| 1 | `tests/test_ai_review_strategy.py:134` | `reinsert_updates_value_but_not_eviction_rank` | 反向改名＋断言（复写刷新顺位） | 语义翻转，属裁决面 |
| 2 | `:120` | `trim_boundary_is_strictly_over_capacity` | 改"不经读路径的顺序断言"（`list(cache)` 直读），**或**给测试开一个非刷新读接口 | 后者是**新口径决策**（l924-20 §三 明示须人工先认） |
| 3 | `:216` | `share_one_trim_budget` | 同 2（读探针被 move_to_end 污染） | 同上 |
| 4-7 | `:267/:286/:305/:333` | l927-56 新 1/2/3/4 | 删除或反向改写（它们专职钉 FIFO） | 与旧桩同笔，防"新桩红着入库" |
| 8 | `core/ai_review.py:49-52` | 头注释 | 同笔订正为 LRU 自述 | 新 6（:382）有牙，不改必红 |
| — | `:177`／`:233`／新 5（:367） | 顺位正交／命名空间／容量桩 | **一字不动** | 勿顺手改 |
| — | 消费面 11 枚同吃 `ai_review` 的测试件 | — | l927-56 §六 配方 2 定向 12 件（基线 136 passed）须复跑 | 禁跑全量的波次纪律仍有效 |

## 四、两案矩阵（完成标准②）

| 维度 | 案一：升级真 LRU（LRU-rw，l924-20 案 B） | 案二：维持 FIFO（现状） |
|---|---|---|
| 收益 | 工作集 ≤ 容量时 +2.8pp 命中（trace-2）；"热条目不因早插入而被踢"的心智模型正确性 | 零改动；顺位＝首次插入，可预测、已被 10 例在册桩（旧 3＋新 4＋正交 3）钉死 |
| 成本 | 上表 7 断言＋1 注释＋"非刷新读接口"口径先例（**放宽判据风险相邻**：改 :120/:216 属改测试判据，红线域，须人工先认修法形状） | 无 |
| 风险 | 读写都刷新改变淘汰对象 ⇒ 真实会话里"僵尸条目续命"行为变化需回归面；两类键共用一只缓存的挤占问题**原样保留**（不解决 :216 类事故面） | 工作集 ≫ 容量时冷启动挤热数据（现役事实，但 trace-1 显示 LRU-rw 在该场景**也无收益**，不构成维持的成本） |
| 替代覆盖 | l924-20 案 A（容量＋分池）在命中率上直接碾压案 B（+31.7pp vs +0~2.8pp）；案 0（注释）已随 l923-05 落地 | 同左 |
| 数据支撑强度 | trace 为**合成**沙盒数据（seed 固定可复算，但非真实用户 trace） | 现役 25 passed |

## 五、推荐（完成标准③）

**推荐：维持 FIFO（案二），不拍 LRU-rw。** 理由：
1. **收益小且条件化**：+2.8pp 只在工作集 ≤ 容量时出现，而现役常态工作集 403 ≫ 64（trace-1 +0.0pp）；LRU-w 态实测 0 收益连"折中方案"都不成立。
2. **成本不对称**：要动 3 条 l922-10 旧桩＋4 条 l927-56 新桩＋1 处注释，且前置"给测试开非刷新读接口／改读探针桩"是**测试判据形状的新口径**（红线相邻）——为条件化的 2.8pp 付这个价，两案矩阵里没有支持它的格。
3. **真痛面在别处**：跨类挤占（案 A 分池靶）与"改一字不命中"（案 C 键形靶）才是命中率与事故面的大头，LRU 两个都不治。若人工想把缓存这张牌打出去，**案 A（容量＋分池）优先于案 B**——但那是数值裁决，判据全在 l924-20 §四/§五，本班不代拍、不新增数值。
4. **维持≠搁置**：FIFO 现状已被 10 例断言＋注释自述桩钉死，未来任何升级都要过本档改写清单这道账——材料闭合，随时可翻案。

## 六、待人工清单

1. 两案拍板（本班推荐案二）；若否，按 §三 改写清单 7＋1 执行，先认"非刷新读接口"口径。
2. 案 A/案 C 是否排期（数值依据在 l924-20，属性能域非判分域，但仍建议人工拍）。
3. 产出件 `docs/insights/l927-35-fifo-lru.md` **未自登索引** ⇒ 落盘后 `tests/test_insights_index_closure.py` 预期红（开工基线 3 passed），须主班登索引后与产出件同笔入库（l927-56 同型先例）。

## 七、复算配方

```bash
cd D:/code/learning-system
# 1 三态矩阵（内存假件，跑前跑后 core/ai_review.py sha1 不变 d9ee8e22…）
sha1sum core/ai_review.py
PYTHONIOENCODING=utf-8 python D:/code/tmp/qoder-executor-20260928-1620-learn59/mut_probe.py
# 2 定向现状 25 passed
PYTHONIOENCODING=utf-8 python -m pytest tests/test_ai_review_strategy.py -q
# 3 旧三桩行号
grep -n "def test_cache_feedback_trim_boundary\|def test_cache_feedback_reinsert\|def test_code_and_open_caches_share" tests/test_ai_review_strategy.py
# 4 命中率数值出处（本档未重算）
grep -n "trace-1\|trace-2\|+2.8\|46.9" docs/insights/learn-review-cache-lru-verdict-20260924.md
```
