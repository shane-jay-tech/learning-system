# l927-42 展示门 N／P／E 三案终版裁决材料（不选路、不改判据、不动展示门代码）

> 波次 78 文档位 `learn67`，2026-09-29 磁盘实取。上游：`zcode-bridge/done/l924-05.result.md` 遗留 1／遗留 2／遗留 4，
> 案源本体在 `docs/insights/learn-judge-result-keep-design-20260924.md` §三.3。
>
> 🔴 **本档性质＝裁决材料**：把三案各自的**代价、影响面、可批形状**摆到能点头的程度，交人工选。
> **不选路**（§六 的推荐是材料的一部分，不是裁决，也不代人工点头）、**不改判据**、**不动 `ui/` 一行码**。
> `git status --porcelain` 收工终值 **恰 1 行＝本档自身**（本班另一枚产出档 `l927-26-topdiff-list.md` 已由主班在 `e81af75` 入库），零在册件改动。

---

## 〇、锚点复核：三案**全部未落地**，在册行号已漂；两条在册主张被本档否证

取数 2026-09-29 08:0x，分支 `main`，HEAD `9a2e6be`，porcelain 开工前 **0 行**。
⚠ **取数期间 HEAD 前移过一笔**：主班于 08:02:59 提交 `e81af75`（＝本班第一枚单 `l927-26` 的产出档＋索引代登一行，
**2 files / +332 / `ui`·`core`·`tests` 零命中**）⇒ 本档所有 `ui/` 行号不受该笔影响，可继续引用；
复核命令：`git show --numstat e81af75 -- ui/ core/ tests/`（回空）。

### 0.1 现状确认（＝方案 N 仍在位，谁都没动过）

| 对象 | l924-05 记的行号 | **磁盘现值** | 状态 |
|---|---|---|---|
| 展示门（两条件 `if`） | `language.py:369-372` | **`:417-420`**（判空 `:418`／门串 `:419`／取值 `:421`） | ✅ 门一字未松，条件仍是 `last_judge_pid == active_id` |
| 结果格写 | `:357` | **`:405`** | 未动 |
| 指针 `last_judge_pid` 写 | `:358` | **`:406`** | 未动，**全仓仍零 pop** |
| 原地清自己那格（3 处） | `:301`/`:314`/`:340` | **`:349`/`:362`/`:388`** | 未动 |
| 切换点 `drop_shown_judge_result()`（3 处） | `:176`/`:229`/`:249` | **`:224`/`:277`/`:297`** | 未动 |
| `drop` 定义／其指针读 | `components.py:54`/`:62` | **`:54`/`:62`** | ✅ **零漂移** |
| 第 4 个调用点（跨页导航） | `components.py:89` | **`:89`** | ✅ 零漂移 |
| `JUDGE_RESULT_PREFIX` | `components.py:40` | **`:40`** | 零漂移 |
| **锁 1（＝4 个切换点清理）** | 未删 | **未删**（4 处全在） | 🔴 技术包 ① **没落地** |
| **`JUDGE_RESULT_PREFIX` 挂进前缀表** | 6 项 | **仍 6 项**（`language.py:44-45`） | 🔴 技术包 ② **没落地** |
| `_recent_judge_pids`（方案 P 的新键） | 未建 | **全仓 0 命中** | 🔴 方案 P **没落地** |
| `_LRU_CAP` | 30 | **`language.py:46` ＝ 30** | 未变 |

⇒ **三案现值的第一条结论：盘上仍是 N（＝现状），两件事都没做，本单的裁决点没有被前几班蚕食。**
（锚点自 09-24 起整体下移约 +48 行，是同批 l927-40 等单插码所致；**断言面全部成立，只有行号漂**。）

### 0.2 🔴 本档否证两条在册主张（都会直接改变人工的成本估计）

**否证一：l924-05 §4.1 说「展示门桩 `test_judge_result_per_pid.py:202` ⇒ 方案 P/E 必翻」——不翻。**

该桩**名字**叫 `test_read_side_guard_still_pairing_pid`（「门仍在配对 pid」），但**函数体三条断言里没有一条检查 pid 配对**：

```
$ sed -n '202,206p' tests/test_judge_result_per_pid.py
    def test_read_side_guard_still_pairing_pid(self):
        src = Path(language_page.__file__).read_text(encoding="utf-8")
        assert 'st.session_state.get(judge_result_key(active_id)) is not None' in src
        assert "r = st.session_state[judge_result_key(active_id)]" in src
        assert "st.session_state.last_judge_result" not in src, "属性式裸全局读写复活"
```

P／E 都**保留**这两行读侧形状（改的是第三个条件、不是这两行），第三行查的是另一种病 ⇒
**P 与 E 都不碰它**。机械验证实证见 §二（S3／S5／S4／S6 四格该列全 PASS）。
⇒ 影响面比档上记的**少一条**；但代价是**这条桩是个名不副实的守卫**——它声称守「配对 pid」，实际守不住（§四.3）。

**否证二：l924-05 §4.1 漏了一条**真正会挡「去锁 1」的桩——`test_navigate_to_problem_routes_through_the_helper`（`:164`）。

它**正向要求**跨页导航块里**必须有** `drop_shown_judge_result()`：

```
$ sed -n '164,168p' tests/test_judge_result_per_pid.py
    def test_navigate_to_problem_routes_through_the_helper(self):
        block = c[c.index("def navigate_to_problem"):c.index("def code_highlight_lang")]
        assert "drop_shown_judge_result()" in block, "跨页导航没走统一清理口：清键口径会两处漂移"
```

⇒ 「去锁 1」把 4 个调用点删干净时，`:164` 与 `:180` **两条同时红**，而档上只记了 `:180`。
更要紧的是这两条桩合起来构成一个**自相矛盾的对局**：`:180` 要求 language.py 恰 3 个 drop 点、
`:164` 要求 components.py 的导航块里 drop **不许少** ⇒
**只删 language.py 那 3 处（＝l924-05 §五 A-5 警告的「半删」）恰好是 `:164` 全绿、只剩 `:180` 一条红的形态**，
而那条红只要把 `== 3` 改成 `== 0` 就消掉——**清错题的缺陷就此带着绿灯入库**。这是本档认为人工最该先看的一条（§四.2、§五.3）。

---

## 一、三案终表

先把口径钉清：三案说的是**门（③）**，而 ①去锁 1、②挂 LRU 前缀表 是**三案共用的技术前置**。
l924-05 把它们混排过，本档拆开——因为拆开之后才能看清「哪些组合是有意义的」。

| 方案 | 门条件（`:419` 那一行会变成什么） | 新增全局键 | ①②前置 | 用户可见结果 | 在册桩翻转（**机械实测**，见 §二） | 回滚成本 |
|---|---|---|---|---|---|---|
| **N 保持现状** | `last_judge_pid == active_id`（不动） | 无 | **不需要** | 回访上一题看不到结论（＝今天的行为） | **0 条** | 0 |
| **P 指针即历史** | `active_id in st.session_state.get("_recent_judge_pids", [])` | **1 个**（`_recent_judge_pids`，G 类） | 必须（①②） | 回访最近 N 道**判过**的题各自显示；更早的被窗口挡住 | **3 条**：`:106` 门串＋`:164` navigate＋`:180` 三加三；**`:202` 不翻**（否证一） | 单点可回滚（改 1 行门＋删 1 键） |
| **E 信箱自证** | 删掉 `:419` 整个条件，门＝「该题自己的格存在即展示」 | 无 | 必须（①②） | 任意有格的题都显示其结论；有界性**全靠②的 30 题逐出**间接给 | 同 P：**3 条**（`:106`/`:164`/`:180`），**`:202` 不翻** | 单点可回滚（加回 1 行） |

### 1.1 组合矩阵：三案里只有三格是「活」的

| 组合 | 门 | 锁 1 | 挂表 | 判定 | 依据 |
|---|---|---|---|---|---|
| **现状** | N | 在 | 否 | ✅ 唯一自洽的 N 形态 | 零成本、零收益、零红 |
| 门 N ＋ 去锁 1（±挂表） | N | 删 | 删/是 | 🔴 **假改动**：代码变了、UX 一分不变（门仍拦死），却白翻 2 条桩；不挂表还多 40 格无主 | l924-05 §二 第 2 行 ＋ 本档 §二 S1 列 |
| 门 N ＋ 只删 language.py 3 处 | N | 半删 | — | 🔴🔴 **清错题**（最坏形态）：`drop` 清的是「指针指着的题」而非「正要离开的题」，**且 4 条桩里只红 1 条** | §二 S2 行 |
| 门 P ＋ 锁 1 留在 | P | 在 | — | 🔴 无意义：锁 1 在切换时已把格清了，门换成集合也**无格可显示** | §二 S4（桩翻 1 条、UX 增益＝0） |
| 门 E ＋ 锁 1 留在 | E | 在 | — | 同上，无意义 | §二 S6 |
| **P ＋ ①②同批** | P | 删 | 是 | ✅ **活案一** | §二 S3 |
| **E ＋ ①②同批** | E | 删 | 是 | ✅ **活案二** | §二 S5 |

⇒ **裁决的真实形状不是「三选一」，而是「N（不动）／P＋技术包／E＋技术包」三选一**，
且 P／E 任取其一都**必须与 ①② 同批**（否则拿到的是假改动或无界泄漏）。

### 1.2 P 与 E 的差别到底在哪（本档把它缩到一条路径上）

l924-05 给的对照是「P 有窗口、E 没有」。但 **②挂表一旦落地，格的生命周期本身就等于「最近 30 道访问过的题」**
（`_touch_problem:64-69` 逐出时按前缀表清格），所以 E 也**被间接有界**了。二者的差**只剩一格**：

> **一道很久以前判过、但刚才被重访的题**——它的格还活着（在 30 道访问窗内）。
> **E 会把它当年那份结论当刚判的显示出来；P 不会**（`_recent_judge_pids` 按「判题」收缩，早把它挤出窗口）。

- 窗口收缩的**计数单位**不同：E 按 `visit` 收缩，P 按 `judge` 收缩。
- 而这条差异恰好就是 `:107` 桩注释点名的**失效面 C** 的**剩余部分**：②把「无限久」压成「≤30 次访问」，P 进一步压成「≤30 次判题」。

### 1.3 🔴 三条在册门都不防的另一格（人工点头前请知）

**判完题、就地改代码、不重判 ⇒ 屏上仍是旧结论**。因为门只查「格存在 ＋ 是指针那道题」，
**没有任何一处**在代码变化时 `pop(judge_result_key(active_id))`：
`editor_epoch::{active_id}` 自增**只在 ↺ 重置**处（`:386`；全文件 `editor_epoch` 命中 4 行＝`:40` 读／`:45` 前缀表项／`:386` 写自增／`:104` 注释提及，代码站点 3 处），
生成变式／回原题／重置三处清的是**它们自己的格**（`:349`/`:362`/`:388`）。

⇒ **「旧结论当刚判的」这一风险在今天的 N 形态下就已经存在，且 N／P／E 三案都不修它。**
所以三案的取舍**不该被表述成「P／E 会不会引入陈旧」**——陈旧已经在卖；
真正的差是**「别题的结论」与「更老的结论」能被显示的范围**。
（此条不改变三案的排序，但会改变人工对收益的预期，故单列。修法属另一单，本档不动码。）

---

## 二、机械判定（不是推演：把 6 条在册断言跑在 6 种假设源码上）

探针 `D:\code\tmp\learn67\probe_gate_matrix.py`：读**真源文件文本**，只做内存字符串变换（不写文件、不改 `ui/`），
把 `tests/test_judge_result_per_pid.py` 的 6 条判据**逐字照抄**后跑在「门 × 锁 1」的 6 个假设形态上。
S0 是**现状**，用来验探针自身不失真——S0 必须全 PASS，实测确实全 PASS。

```
基线实读：language.py drop 行数=3 own 行数=3 ｜ components.py drop 行数=1

场景                                    :99a count==6  :99b 门串在源码  :164 navigate含drop  :180 三加三  :202 读侧形状  :208 写侧格名
S0 现状 N＋锁1全留                            PASS          PASS          PASS              PASS        PASS          PASS
S1 N＋锁1全删(4处)                            PASS          PASS          **翻红**          **翻红**    PASS          PASS
S2 N＋锁1半删(只删 language 3 处)             PASS          PASS          PASS              **翻红**    PASS          PASS
S3 P＋锁1全删                                 PASS          **翻红**      **翻红**          **翻红**    PASS          PASS
S4 P＋锁1全留                                 PASS          **翻红**      PASS              PASS        PASS          PASS
S5 E＋锁1全删                                 PASS          **翻红**      **翻红**          **翻红**    PASS          PASS
S6 E＋锁1全留                                 PASS          **翻红**      PASS              PASS        PASS          PASS
```

四件可复算的事：
1. **`count==6` 与 `:208` 在全部 6 形态下不动** ⇒ 读写同源面与写侧格名**不在争议面上**，三案都无需碰。
2. **`:202` 在全部 6 形态下不动** ⇒ 否证一坐实（它不参与本裁决）。
3. **P／E 的「门」成本恰＝1 条桩（`:106`）**，与 E 相比 P **不多翻任何一条** ⇒ 「P 比 E 贵」这件事**不在桩上**，只在「多一个全局键」那一项。
4. **S2 比 S1 少翻一条**（`:164` 在 S2 全绿）⇒ 危险形态反而**更安静**，这就是 §四.2 的坑。

配套定向基线（真跑，未跑全量）：

```
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_judge_result_per_pid.py tests/test_retire_variant.py \
    tests/test_editor_variant_keys.py tests/test_language_lru_eviction.py tests/test_language_editor_epoch.py \
    tests/test_app_flow.py -q
93 passed in 2.83s          # 门族现状全绿；test_judge_result_per_pid.py 单件 17 例
```

---

## 三、方案 P 的实现草案细化（完成标准 ②；卷宗点名的那一半）

### 3.1 键的形状（照抄仓内既有先例，不自创）

| 项 | 取值 | 依据（盘上） |
|---|---|---|
| 键名 | `_recent_judge_pids` | l924-05 §3.3 原名沿用 |
| 类型 | `list[str]`，**队尾最新** | 与 `_problem_lru`（`:62`）／`_variant_lru`（`:152`）同形 |
| **去重策略** | 🔴 **先摘再挂**（`while x in q: q.remove(x)` 后 `append`），**不是** `_touch_problem` 的「只看队尾」 | 同一个文件 `:149-151` 的注释把这条教训写死了：「来回切题会把同一个 id 反复堆进队列，30 个名额被重复项吃满 ⇒『有界』退化成『按 rerun 次数逐出」。**P 会在同一题上反复重判**，正是「重复项吃满」的形态，故必须用先摘再挂 |
| **容量** | **`_LRU_CAP`（＝30），不另设第二个阈值** | `language.py:134` 原文：「封顶沿用 `_LRU_CAP`（30），不自造第二个阈值——『保留最近 N 道题』的口径全仓只有一处」 |
| 写入点 | **唯一 1 处**：`language.py:405-406` 旁（判题成功、与格写／指针写同批） | 与「格写＝指针写＝同一处」的既有不变量对齐（`:405`/`:406` 相邻） |
| 读取点 | **唯一 1 处**：门 `:419` | 门是 `:419` 这半行 |
| 三类归属 | **G 全局 UI 键**（Q1：名字不含题身份 ⇒ G ⇒ 任何清扫器不得触及） | `docs/insights/learn-editor-key-spec-20260924.md` §四 判据原文 |
| 与 `last_judge_pid` 的关系 | 见 §3.3（**这里有取舍，必须人工点头**） | — |

### 3.2 🔴 本档否证一条「P 的省钱捷径」：不能拿 `_problem_lru` 当那个集合

看上去最自然的实现是「不加新键，门直接用现成的 `_problem_lru`」——**语义上它等于 E，不是 P**。实测链：

1. `language.py:303` 每次渲染当前题都无条件调 `_touch_problem(active_id)`；
2. `_touch_problem:62-63` `if not lru or lru[-1] != active_id: lru.append(active_id)`，且 `:64` 的 `keep_ids` 显式并入 `{active_id}`、`:78` 截尾后当前题必在队尾 ⇒
3. **`active_id` 恒属于 `_problem_lru`** ⇒ 门 `active_id in _problem_lru` **恒真** ⇒ 整个 `if` 退化成「格存在即展示」＝**方案 E 原文**。

⇒ 想要 P 的语义，**必须有一个「只在判题时前进」的独立历史集合**，无法搭 `visit` 队列的便车。
这条是本档对「P 草案」最重要的收窄：**新增 1 个全局键是 P 的必要成本，不是可选优化。**

### 3.3 P 与 `last_judge_pid` 的三种收法（人工选，代价不同）

| 收法 | 做法 | 代价 |
|---|---|---|
| **P-全换** | 删 `last_judge_pid`（`:406` 写、`components.py:62` 读、`:419` 门读三处都改），drop 改按集合队尾或随 ① 一起消失 | 最干净；但 `components.py:54-64` 的 `drop_shown_judge_result` **失去定位器**，必须与 ① 同批（否则 drop 无从定位 ⇒ 直接踩 §四.2 的坑）。`:164` 桩必改语义 |
| **P-双键** | `last_judge_pid` 留着只服务 drop，`_recent_judge_pids` 只服务门 | 少改一处、`:164` 可原样留；但**两个全局键描述同一件事**，正是 l924-05 §3.2 说的「指针＋信箱关系双向破」的温床，后续漂移难查 |
| **P-窗口收缩联动** | 在 3.1 基础上，让 `_recent_judge_pids` 在 `_problem_lru` 逐出时同步剔除已死 id | 逻辑最一致，但**实测是冗余的**：门是「在集合 ∩ 格存在」的合取，格被 ② 清掉后残留 id 显示不出来 ⇒ 白改一处逐出循环。**建议不做**，登记为「知道可以不做」 |

### 3.4 P 专属的判别式断言草案（3 条，可直接落 `tests/`；不替人工落）

写这 3 条的理由：l924-05 §五 的 A-1…A-5 里**没有一条能区分 P 与 E**（它们都只查「在集合里」，
而 E 也满足「格存在」）。按 §二 的实测，P 落码后若被偷偷简化成 E，**没有任何一条在册桩会红**。
⇒ 下列三条是 P 的**唯一定位守卫**，缺它们＝P 不可验收。

```python
# P-1 门必须是「判题历史集合」，不接受 visit 队列（专治 §3.2 那条捷径）
def test_gate_window_is_judged_only_not_visited_lru():
    src = Path(language_page.__file__).read_text(encoding="utf-8")
    assert '_recent_judge_pids' in src, "P 退化：门没有自己的判题集合"
    gate = [ln for ln in src.splitlines() if "_recent_judge_pids" in ln]
    assert not any("_problem_lru" in ln for ln in gate), \
        "门用了 visit 队列 ⇒ active_id 恒在其中 ⇒ 语义已退化成方案 E"

# P-2 窗口只在判题成功时前进（重访不前进）——反向守卫，拦「顺手把 _touch_problem 也接上」
def test_window_advances_only_at_judge_site():
    src = Path(language_page.__file__).read_text(encoding="utf-8")
    sites = [ln.strip() for ln in src.splitlines() if "_recent_judge_pids" in ln]
    assert len(sites) == 2, f"P 的站点应恰 2 处（1 写 1 读），实得 {sites}"   # 口径同 :102 的 count==6

# P-3 容量必须复用 _LRU_CAP，不许出现第二个字面量阈值
def test_window_capacity_reuses_the_single_lru_cap():
    src = Path(language_page.__file__).read_text(encoding="utf-8")
    assert "_recent_judge_pids[-_LRU_CAP:]" in src or "[-_LRU_CAP:]" in src, "P 自造了第二个阈值"
    nums = re.findall(r"_recent_judge_pids[^\n]*?\[\s*-\s*(\d+)\s*:", src)
    assert nums == [], f"窗口容量写成了字面量 {nums}——全仓只应有一处『最近 N 题』口径（:46）"
```

⚠ **P-2 的 `len(sites)==2` 口径与 `:102` 同型**（整行/子串计数会得到不同数字）：
`:102` 用的是 `src.count("judge_result_key(active_id)")` 的**子串**计数，
`:180` 用的是 `ln.strip() == ...` 的**整行相等**计数，两者不可混。本档 §二 全部走整行判据，
落 P-2 时**必须先明确用哪一种**并写进 docstring（历史上这类口径差被踩过两次）。

---

## 四、影响面与牵连面（逐条文件:行号，均本档现取）

### 4.1 门本体（三案共 1 处）

| 落点 | 现值 | N | P | E |
|---|---|---|---|---|
| `ui/pages/language.py:419` | `and st.session_state.get("last_judge_pid") == active_id` | 不动 | 换成 `and active_id in st.session_state.get("_recent_judge_pids", [])` | **整行删除** |
| `ui/pages/language.py:418` | 判空 `get(judge_result_key(active_id)) is not None` | 不动 | 不动 | 不动（成为唯一条件） |

### 4.2 技术包 ①（去锁 1，4 个调用点）——P／E 的共同前置

| 落点 | 处置 | 桩后果 |
|---|---|---|
| `ui/pages/language.py:224`/`:277`/`:297`（整行 `drop_shown_judge_result()`） | 删 | `:180 test_three_plus_three_sites` 的 `len(drop)==3` 翻红 |
| `ui/components.py:89`（`navigate_to_problem` 块内） | 删 | 🔴 **`:164` 翻红**（该桩**正向要求**它存在）——l924-05 §4.1 漏计 |
| `ui/components.py:54-64 def drop_shown_judge_result` | ① 落地后**无人调用** | 死码；P-全换下它连定位器都没了。**留／删要人工点一句**（留＝死码，删＝动公共 API 形状） |
| `language.py:349`/`:362`/`:388`（原地清自己那格） | **三案都不动** | `:180` 的 `len(own)==3`、`:186` 五步重置链、`:208` 写侧 全不受影响（§二 实证） |

🔴 **半删陷阱（§二 S2 的实证形态）**：只删 language.py 三处、留 `components.py:89`
⇒ `:164` **全绿**、只红 `:180`，而 `:180` 只要把 `== 3` 改成 `== 0` 就消；
此时 drop 清的是「指针指着的题」而不是「正要离开的题」＝**清错题**，**可以带着绿灯入库**。
⇒ 本档认为**这是三案落地过程中最可能发生的一种坏终态**，建议人工在放行语里写死「4 处必须同批」。

### 4.3 桩自身的质量问题（本档登记，不修——改判据属人工）

| 桩 | 问题 |
|---|---|
| `test_judge_result_per_pid.py:202` | **名不副实**：docstring／桩名讲「still pairing pid」，函数体三条断言**无一检查 pid 配对**（§〇.2 否证一）。三案都不翻它，也就是说**它声称防的东西它防不住** |
| `test_judge_result_per_pid.py:106` | 判据是**源码字面串** `'…get("last_judge_pid") == active_id' in src`，把门钉死成一行具体文本。三案任取其一都必须**改写**而非删除它；改写后的新门串应换成 §3.4 P-1 那种**语义判据**，否则下一案还要再改一遍 |
| `:164` ＋ `:180` | **互相对立**：一条要求导航必须有 drop、一条要求 language.py 恰 3 个 drop ⇒ 「去锁 1」不存在只改一条桩的走法（§〇.2 否证二） |
| `test_prefix_defined_exactly_once_repo_wide`（`:89`，判据 `:95`） | 与 ②挂表 相关：**把字面量 `"last_judge_result::"` 写在元组续行上不会被计成第二个定义点 ⇒ 假绿**（l924-05 §四 实测四写法）。正解＝`from ui.components import JUDGE_RESULT_PREFIX` 入表；该哨兵建议改 AST 判定——**属改判据，本档只登记** |

### 4.4 技术包 ②（挂第 7 项前缀）的在册桩＝5 条硬钉（本档现取）

```
tests/test_editor_variant_keys.py:231   assert language_page._PROBLEM_STATE_PREFIXES == (…)  # :233 列到 "editor_epoch::"
tests/test_language_lru_eviction.py:66  assert set(_PROBLEM_STATE_PREFIXES) == set(SIX_PREFIXES) ＋ :70 len == 6
tests/test_retire_variant.py:275        assert _PROBLEM_STATE_PREFIXES == SIX_PREFIXES ＋ :276 len == 6
（SIX_PREFIXES 定义在 tests/test_retire_variant.py:57；:60 FULL_COUNT 是派生量 ⇒ 自适应，不算硬钉）
```
＋ 建议**新增一例**：逐出某题时它的 `last_judge_result::<pid>` 一并消失（这是 ② 唯一的行为证据）。

### 4.5 汇总：三案各自的改动面

| 案 | 生产码 | 必翻在册桩 | 新增断言 | 新全局键 | 净 diff 量级（材料，非承诺） |
|---|---|---|---|---|---|
| **N** | 0 行 | 0 | 0 | 0 | 0 |
| **P** | `language.py` 门 1 行＋写侧 1 处（约 4–6 行新码）；`components.py:89`＋`language.py` 3 处 drop（① 的 4 处）；`:44-45` 前缀表 +1（②） | **`:106`、`:164`、`:180` 三条** ＋ ②的 5 条 ＝ **8 条** | §3.4 三条（**P 缺它们不可验收**） | **1**（G 类） | ≈ 生产 8–12 行／测试 8 处＋3 例 |
| **E** | 门删 1 行；① 的 4 处；② 的 1 项 | 同 P ＝ **8 条** | 至少 1 条（证明门确实只看格，且**接受** §1.2 那条剩余风险） | 0 | ≈ 生产 6–8 行／测试 8 处 |

⇒ **P 比 E 的全部实价 ＝ 1 个全局键 ＋ 2 条额外断言**（桩翻转数相同，§二第 3 条实证）。
这比 l924-05 §3.3 给人的印象（P 明显更贵）要小，值得人工据此重估。

---

## 五、可批形状（三案各给一条能被直接点头或打回的表述）

1. **批 N（不动）**：一句话＝「回访看不到结论是可接受的，且我们不接受任何旧结论被当新结论显示」。
   零改动、零红、可复算证据＝本档 §〇.1（4 处 drop 全在、前缀表 6 项、`_recent_judge_pids` 全仓 0 命中）。
   **代价**：l923-16 想守住的那个 UX 目标继续不成立。
2. **批 E**：一句话＝「门放宽成『这道题自己有结论就显示』，有界性完全交给 ②的 30 题逐出；
   我们接受 §1.2 那条剩余风险（重访老题会把它当年的结论当刚判的显示）」。
   前置必须同批写进放行语：① 4 处 drop 全删（**不许半删**）＋ ② 前缀表挂第 7 项（用常量不用字面量）。
3. **批 P**：一句话＝「同 E，但窗口按**判题**收缩，重访老题不显示其陈旧结论；
   为此接受新增 1 个 G 类全局键 `_recent_judge_pids`，容量复用 `_LRU_CAP=30`，去重用先摘再挂」。
   额外前置＝§3.4 三条断言一起落（否则 P 与 E 在盘上不可区分）。
4. 🔴 **关于「分两单」（l924-05 遗留 4 建议技术包与门决定分单）——本档补一条它的实价，供人工重估**：
   技术包（①＋②）**单独交付时用户可见收益恰为 0**（§1.1 第一行红格：门 N 还在，格照样不显示），
   却会把会话末态活格从 **0 抬到 30**（l924-05 实测 S0＝0／S2＝30）、并白翻 2 条桩（`:164`/`:180`）。
   ⇒ 分单的**唯一真实收益是红名归因**（l924-05 给的就是这条），不是价值本身；
   分单中途停手就留下「30 格活着但一格不显示」的纯负债形态。
   **同批**则反过来：一次改 8 条桩、红名混在一起，但落地的就是终态。**这条差成本档不替人工裁。**
5. 无论选哪条，本档建议放行语里写死三件**已在盘上量出来的**约束：
   ① 4 处 drop **同批**（防半删，§4.2）；
   ② 前缀表用 `JUDGE_RESULT_PREFIX` 常量入表（防 §4.3 的假绿）；
   ③ 三案都**不修** §1.3 的「改代码不失效」那一格——它要么是另一单，要么明确接受，别让它混进这次的验收。

---

## 六、推荐（材料的一部分，**不代拍**）

**排序：P ＞ E ＞ N。** 三点依据，全部指得到本档的行：

1. **P 相对 E 的实价比档案里看起来小得多**：桩翻转数**相同**（§四.5、§二第 3 条实证＝8 条对 8 条），
   差集只有「1 个 G 类全局键 ＋ 2 条断言」。l924-05 §3.3 给人的「P 更贵」印象在本档实测下不成立。
2. **P 守的恰好是门桩自己命名的那个东西**：`:107` 的失效面 C 原文是「回访上一题会把它**很久以前**的结论当成刚判的」，
   ②＋E 只把它从「无限久」压到「≤30 次访问」，**P 才是把它压到「≤30 次判题」**（§1.2 是这单唯一实质的语义差）。
3. **P 有可验收的形状，E 没有**：§3.4 三条断言能把 P 钉住；而 **P 落码后被偷简化成 E，在册 6 条桩一条都不红**
   （§二 实证）⇒ 不配那三条断言的「P」在盘上与 E 不可区分。选 P 就必须连断言一起选。

**会推翻本推荐的两件事**（人工若认这两条，排序就换）：
- 若「绝不新增全局 session 键」是硬约束（或与 `l927-41` 那路的 key 登记案冲突）⇒ **E 胜**。
  （同仓另有一路在做会话键登记：`docs/insights/l927-41-variant3cases.md` 案 D「登记不删扫」实测 **0 例红**、推荐位。
  ⚠ 那是 **变式题 key 规范域**（l924-04 遗留），与本档**不同域**，本档只作为「若 D 落地，P 的新键该登记进 `GLOBAL_UI_KEYS`」的
  **耦合点**引用，**不作本档前提**——跨域引数串过案，见 `tmp/w60-brief.md` §A.3。）
- 若人工认「回访看不到结论」根本不是要修的产品问题 ⇒ **N 胜**，且 §一 里 ①② 全部撤销（它们单独做零收益）。

🔴 本推荐**不选路**：本档未改 `ui/`、未改任何桩、未新增键。落哪个都由人工点头后另开写码单。

---

## 七、本档不做什么（边界自证）

- 不改 `ui/pages/language.py`／`ui/components.py` 任何一行（§〇.1 的行号全是**只读 grep** 得到）。
- 不改判据：`:106`/`:164`/`:180`/`:202`/`:89` 五条桩**原文照读、一字未动**，§四.3 的问题只登记不修。
- 不新增键、不删 drop、不挂前缀表、不动 `core/judge.py` 与判分口径。
- 探针为**纯内存字符串变换**（§二），`tmp/` 下三个文件，**零写 `ui/`、零 sqlite 连接、未跑任何 backup**。
- 红线相邻（判题展示面）⇒ 按纪律**只出只读材料**；本档唯一落盘产物＝这个 `.md`。
- **未跑全量套件**（并行纪律），定向基线 93 passed 见 §二。

## 八、复算命令（每条独立可跑；cwd `D:/code/learning-system`）

```bash
# G1 三案未落地 ＋ 门本体现值（§〇.1）
grep -n "last_judge_pid\|judge_result_key\|_recent_judge_pids" ui/pages/language.py
grep -n "last_judge_pid\|JUDGE_RESULT_PREFIX\|def drop_shown_judge_result\|judge_result_key" ui/components.py
grep -n "_PROBLEM_STATE_PREFIXES" -A 2 ui/pages/language.py | head -8      # 现值 6 项
grep -n "_LRU_CAP" ui/pages/language.py | head -3                          # :46 = 30
grep -rn "_recent_judge_pids" --include=*.py . | grep -v __pycache__       # 0 命中

# G2 锁 1 的 4 个调用点（§4.2）
grep -rn "drop_shown_judge_result" ui/ --include=*.py | grep -v __pycache__ # 6 行＝定义 1（components:54）＋调用 4（components:89、language:224/277/297）＋import 1（language:12）

# G3 六条断言原文（§二 照抄源）
sed -n '89,110p;164,168p;180,215p' tests/test_judge_result_per_pid.py
sed -n '43,47p' tests/test_judge_result_per_pid.py                          # PROD_SRC / _NAMESPACED / _BARE

# G4 机械矩阵（§二；纯内存，不写文件）
PYTHONIOENCODING=utf-8 PYTHONPATH=D:/code/learning-system python D:/code/tmp/learn67/probe_gate_matrix.py

# G5 ②挂表的 5 条硬钉（§4.4）
grep -rn "_PROBLEM_STATE_PREFIXES" tests/*.py

# G6 定向基线（§二末）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_judge_result_per_pid.py tests/test_retire_variant.py \
  tests/test_editor_variant_keys.py tests/test_language_lru_eviction.py tests/test_language_editor_epoch.py \
  tests/test_app_flow.py -q

# G7 「改代码不失效」那一格（§1.3）
grep -n "editor_epoch" ui/pages/language.py                                  # 4 行命中（:40/:45/:104/:386），代码站点 3 处
sed -n '400,425p' ui/pages/language.py

# G8 盘态（§七）
git status --porcelain                                                       # 期望恰 1 行＝本档（l927-26 档已由主班 e81af75 入库）
```
