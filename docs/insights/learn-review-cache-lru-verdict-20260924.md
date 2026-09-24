# learning 点评缓存 FIFO→LRU 与分池两案裁决材料（l924-20，只出稿＋案序 · 零生产码改动）

> **卷宗**：`zcode-bridge/inbox/l924-20.task.md`（现址 `zcode-bridge/done/`）。上游依据＝`zcode-bridge/done/l923-05.result.md` 两条"本单无权决定／未处理"：
> ①「『复写同键不刷新顺位』这个 FIFO 语义是否要升级成真 LRU（`move_to_end`）本单无权决定」；②「两类缓存共用 64 容量、互相挤占**未处理**……是否需要分池/分容量，属规划域」。
> 🔴 **本单只出裁决材料与案序，选案交人工**。所有命中率/淘汰行为都出自 `tmp/l924-20/cache_sandbox.py` 的**内存假件**（零网络、零写盘、零 LLM 调用、不改生产码、不放宽任何在册断言）。

## 〇、锚点复核（卷宗每条前提都实测）

| 卷宗前提 | 实测 | 命令 | 判定 |
|---|---|---|---|
| `core/ai_review.py:50` 的 FIFO 自述注释 | 该行逐字为 `# OrderedDict 对已存在的键赋值不会 move_to_end ⇒ 复写同键只改值、不刷新顺位，` | `sed -n '48,52p' core/ai_review.py` | ✅ 零漂移 |
| 在册桩 `:134`／`:216` | `:134 test_cache_feedback_reinsert_updates_value_but_not_eviction_rank`、`:216 test_code_and_open_caches_share_one_trim_budget` | `rg -n "def test_cache|def test_code_and_open" tests/test_ai_review_strategy.py` | ✅ 行号零漂移 |
| 共用一只缓存、共用容量 64 | `_feedback_cache: _OrderedDict` 与 `_FEEDBACK_CACHE_MAX = 64` 各**只有一个**；代码点评与开放题结果两条写路径各自 `while len(...) > MAX: popitem(last=False)` | `rg -n "_feedback_cache\|_FEEDBACK_CACHE_MAX\|popitem" core/ai_review.py` → `:55/:56/:63-65/:99-101` | ✅ |
| 🔴 否证（头注释两行自相矛盾） | `:44` 写「同一道题 + **相同代码**重复提交时直接复用上次点评」（与键形一致），紧邻 `:45` 却写"避免学生「**改一个字**再跑一次」反复触发 LLM 调用"——键是 `(lang, pid, sha1(code))` **全码哈希** ⇒ 改一个字＝新键＝**必然不命中**，:45 这句收益陈述不成立（缓存只吃逐字重复提交） | `sed -n "44,45p" core/ai_review.py` ＋ `rg -n "sha1" core/ai_review.py` | ❌ 见 §六-1（属注释订正，非行为改动） |

## 一、现值容量占用（完成标准①的"现值"部分）

现网无 LLM 流量日志可取，唯一可用的真实负载样本是 `data/progress.db` 的 `attempts`（只读取证，`mode=ro&immutable=1`，跑完无侧车）：

| 量 | 现值 | 命令 |
|---|---|---|
| 历史提交条数 / 去重后缓存键数 | **15 / 15**（一条都没重复过） | `select count(*), count(distinct lang\|\|problem_id\|code) from attempts` |
| 缓存命中次数 / 淘汰触发次数 | **0 / 0** ⇒ 64 容量占用 **0%**，`popitem` 分支在有史以来未执行过 | 同上推论（无重复键 ⇒ 无第二次写） |
| 同题最多提交次数 | 2（`python/01_hello_and_vars/01_hello_world`，两份 code **不同**） | `select lang,problem_id,count(*) c from attempts group by 1,2 order by c desc limit 3` |
| 点评文本长度（字符） | min **6** / 中位 **13** / max **470** | `select min(length(ai_feedback)),avg(...),max(...) from attempts where ai_feedback<>''` |
| 代码长度（字符） | min 32 / 中位 392 / max 751 | 同表换 `code` |
| 两类题的宇宙（**双轨**） | 运行时轨 `judge_mode` 分布 **run 333 / ai_open 70**（共 403）；正则轨严格串 `judge_mode: ai_open` 只 **66** 处 ⇒ 差额 4 全部来自带引号写法 `judge_mode: "ai_open"`（实测 4 处）；两轨归因后**闭合** | `PYTHONIOENCODING=utf-8 python -c "from core.loader import load_language;from collections import Counter;c=Counter();[c.__setitem__(p.judge_mode,c[p.judge_mode]+1) for l in ('python','sql','cpp','r','agent_dev') for t in load_language(l) for p in t.problems];print(c)"` |

🔴 **这条现值决定了全稿的读法**：FIFO⇄LRU、共用⇄分池四个开关在**真实负载下全部不可观测**（占用 0/64）。任何"LRU 更省"的断言都只能来自合成 trace，因此 §四 把 trace 参数、随机种子、口径全部写死可复算，并且**不拿它当改码理由**，只当"改与不改的差别有多大"的标尺。

## 二、三态而非两态（裁决前必须先接受的区分）

`move_to_end` 放在哪里，是三个不同的方案，不是一个：

| 态 | 写路径 | 读路径 | 语义 |
|---|---|---|---|
| **FIFO**（现役） | `c[k]=v` ＋ 超限 `popitem(last=False)` | `c.get(k)` | 复写同键只改值、不刷新顺位；淘汰"最早插入" |
| **LRU-w** | `c[k]=v; c.move_to_end(k)` | `c.get(k)` | 只有"重新写过"才算最近使用 ⇒ 命中**不**续命 |
| **LRU-rw** | 同上 | `v=c.get(k); c.move_to_end(k)` | 真 LRU：命中也续命 |

**为什么必须摆开**：`lru-rw` 会让"用读来验淘汰"的在册桩**自己改变被淘汰对象**（读操作把被测键救活），这是 §三 那两条红里最不对称的一条的成因。

## 三、改哪态会红哪例（完成标准②，逐条行号＋沙盒重放）

沙盒把三条桩的**动作序列**逐条重放（`tmp/l924-20/cache_sandbox.py` → `A_*`）：

| 在册桩（`tests/test_ai_review_strategy.py`） | 行号 | FIFO | LRU-w | LRU-rw | 为什么会红 |
|---|---|---|---|---|---|
| `test_cache_feedback_reinsert_updates_value_but_not_eviction_rank` | **:134** | ✅ 绿 | 🔴 **红** | 🔴 **红** | 整例就是钉"复写不刷新顺位"，写时 `move_to_end` 直接反义（重放读数：首键仍是 p0 `False`、值已改 `False`、p0 被踢 `False`） |
| `test_cache_feedback_trim_boundary_is_strictly_over_capacity` | **:120** | ✅ 绿 | ✅ 绿 | 🔴 **红** | 只在"读也刷新"下红：桩用 `_cached_feedback(...)` **读**来判断谁被淘汰，`lru-rw` 下这次读把 p0 移到队尾 ⇒ 被淘汰的变成 p1，末三行断言全部反向 |
| `test_code_and_open_caches_share_one_trim_budget` | **:216** | ✅ 绿 | ✅ 绿 | ✅ 绿 | 三态都把 `code-p` 挤掉（它只写一次且最早）⇒ **跨类挤占不是 LRU 能解决的问题**，它是容量分配问题（见 §五） |
| `test_cache_feedback_write_read_roundtrip_and_miss_never_raises` :85／`skips_all_three_unusable_inputs` :96／`key_shape_is_lang_pid_sha1_of_code` :110／`open_key_is_stable...` :148／`open_result_cache_roundtrip...` :164／`isolates_dimensions_on_both_sides` :177／`取缓存结果后就地_append_sort...` :197／`namespaces_never_collide` :233 | — | ✅ | ✅ | ✅ | 不含"顺位/淘汰序"断言；:177/:197 钉的是**深复制隔离**，与顺位正交（勿顺手改） |

⇒ **改 LRU-w 需同批改 1 例（:134）；改 LRU-rw 需同批改 2 例（:120 ＋ :134）**。🔴 且 :120 的修法**不能是把断言放宽**（纪律：不许为了让数好看放宽断言），只能改成"不经读路径的顺序断言"（如暴露一个不刷新的 `_peek_keys()` 供测试，或直接断言 `list(cache)` 的键序）——**这属于给测试开新接口，需人工先认这条口径**。

## 四、两案对拍读数（完成标准①的后半：合成 trace）

参数（全部写死可复算）：`random.seed(20260925)`、4000 事件、`open` 占比 `70/(70+333)=0.174`、键形与生产同型、代码 payload 逐字复用（只有重复提交才可能命中）。

**trace-1「全景重放」**（工作集 = 403 题 ≫ 容量 64）｜**trace-2「单会话聚焦」**（α=1.4、工作集 ≤100 ≲ 容量 64）：

| 配置（**等总容量**才可比） | trace-1 FIFO / LRU-w / LRU-rw | trace-2 FIFO / LRU-w / LRU-rw |
|---|---|---|
| 共用 64（现役） | 15.2 / 15.2 / 15.2 %（miss 3394/3394/3391） | 43.2 / 43.2 / **46.0** %（miss 2270/2270/2161） |
| 分池 48(代码)/16(open) | 15.0 / 15.0 / 15.0 % | 44.1 / 44.1 / 45.4 % |
| 分池 32/32 | 15.0 / 15.0 / 15.0 % | （同上量级，未单列） |
| 扩到 128+64（总 192，非等容量） | **46.9 / 46.9 / 46.7** %（miss 2125） | — |
| "被踢掉后又重算"次数（＝纯浪费 LLM 调用） | 2991 / 2991 / 2988 | 2071 / 2071 / 1962 |

三条结论（都带读数，不取单个数）：
1. **LRU-w 相对 FIFO 的收益实测恰为 0**（两 trace 的 hit%/miss/浪费数逐位相同）——因为本缓存的写只发生在 miss 之后，"写时刷新"等于没刷新。⇒ **若有人提议只加 `move_to_end` 到写路径，数据不支持**（它唯一的实际作用是把 :134 改红）。
2. **LRU-rw 只在"工作集 ≤ 容量"时有意义**：trace-2 **+2.8pp**（43.2→46.0，浪费 −109 次）；trace-1 只有 +0.0pp（miss −3）。⇒ 升 LRU 的前提是**同时**接受"容量至少要覆盖一次会话的工作集"，否则策略改动被容量瓶颈淹没。
3. **分池在等容量下不是收益项**（15.2→15.0、43.2→44.1，正负 0.9pp 内互有胜负）；它的真价值是**可预测性**（把 :216 那种"open 灌 64 条把点评全挤光"的整类风险结构性消除），不是命中率。
4. **真正的杠杆是容量**：总容量 64→192 把 trace-1 命中率从 15.2% 抬到 **46.9%**（+31.7pp）——是策略改动收益的十倍以上。

## 五、分池与容量建议（完成标准③：含数值依据）

条目体量（`deep()` 递归 `sys.getsizeof`，沙盒读数）：

| 项 | 字节 |
|---|---|
| 键元组 `(lang, pid, sha1hex)` | **247 B** |
| 点评文本（120 字符，接近 DB 中位～均值） | **298 B** |
| 点评文本（470 字符＝DB 实测上界） | **998 B** |
| 开放题结果 dict（5 个 dimensions，含 name/score/comment） | **2126 B** |
| 64 条**全按最坏 open** 计 | **132.9 KB** |
| 64 条全按最坏点评 | 62.4 KB |

⇒ **整只缓存的最坏内存占用约为 0.13 MB**，扩到 192 条约 **0.4 MB**、扩到 512 条约 1 MB。**内存不构成任何约束**——"64" 这个数不是为了省内存而定的（现役注释也没写理由）。

据此给三档容量建议（数值依据即上表＋§四-4）：
- **保守档**：容量 **64 → 192**（代码池 128／open 池 64，≈0.4 MB）。理由：trace-1 命中率 +31.7pp，是四五个方案里唯一"数量级有效"的一项；分池取 2:1 是按 `run:ai_open = 333:70 ≈ 4.8:1` 与 open 条目 **2.1 KB vs 点评 0.3 KB（≈7 倍）** 两个数折中——按题量给 open 太少、按字节给 open 太多。
- **激进档**：**512 条 + TTL**（≈1 MB）。真 LRU 的命中率收益要等工作集可测才有意义，而"改一个字就不命中"（§〇 否证条）意味着**键形不改，扩容收益有上限**：同题不同码永远是不同键。⇒ 若目标是"少烧 LLM 调用"，**键形（如按 `(lang,pid,规范化代码)` 或题面版本号）比容量与策略都更靠前**。
- **不建议**：只把 `move_to_end` 加进写路径（LRU-w）——实测 0 收益、必改 1 条桩，纯负期望。

## 六、案序（🔴 选案交人工；本单一行生产码未改）

1. **案 0（前置，零风险）：订正两处注释口径**——①§〇 否证的"改一个字"收益陈述与全码哈希键形矛盾；②`core/ai_review.py` 头注释若再出现"LRU 上限 64"字样即为 l923-05 已订正过的旧口径（现读已正确）。**只改注释、零行为变更**，可先于任何裁决执行。
2. **案 A（最小动作）：容量 64→192 ＋ 分池 128/64**，**淘汰策略维持 FIFO**。同步面：`:216` 那条"共用一只预算"的桩必须改写为"分池互不挤占"（这是**换断言**，不是放宽：断言强度不降）；`_FEEDBACK_CACHE_MAX` 一分为二 ⇒ `rg -n "_FEEDBACK_CACHE_MAX" tests/` 现值 **4 处**（`:121` 注释、`:122`、`:137`、`:219`）要逐处定夺。依据：§四-3、§五。
3. **案 B（次小）：FIFO→LRU-rw**（读写都刷新）。**前置条件**是先按 §三 把 :120 与 :134 两条桩改成"不经读路径的顺序断言"，并接受"给测试开一个非刷新读接口"这条口径。收益：仅在会话工作集 ≤ 容量时 +2.8pp。
4. **案 C（收益最大、面也最大）：改键形**（规范化代码或带 `prompt_version`/题目版本），让"改一个字"也能复用点评。**牵 `PROMPT_VERSIONS` 与点评正确性**（旧点评配新代码＝内容错配风险）⇒ 属内容质量域，必须人工拍，且要先想清楚"改 3 个空格的代码该不该吃同一份点评"。
5. **案 D（不做）**：只加写路径 `move_to_end`（LRU-w）。理由见 §四-1，实测 0 收益。
6. 与 l924-07（`mtime`→`(mtime_ns,size)` 错题本缓存键）同族但**不同只缓存**：本档只管 `core/ai_review.py` 的 `_feedback_cache`；`core/progress.py:_memoized`（TTL 3 s、写操作 `_clear_memo`）与 `core/loader.py:_cache` 是另两只，**不在本案面内**（登记以免串案）。

## 七、本单没做的 ＋ 待订正清单 ＋ 复算

**没做**：未改 `core/ai_review.py`／`tests/test_ai_review_strategy.py` 任何一行；未跑全量（并行纪律 §四.2）；未真调 LLM（沙盒全是内存假件，零网络）；未放宽任何断言。

**待订正清单（交主班进台账，本单未改他班在册档）**
1. `core/ai_review.py:45`「避免学生『改一个字再跑一次』反复触发 LLM 调用」⇄ 键是全码 sha1 ⇒ 改一个字必不命中，且与同行上方 `:44`「相同代码重复提交」自相矛盾。建议**删 :45 或改写**（只改注释、零行为变更）。复算：`sed -n "44,45p" core/ai_review.py`。
2. `zcode-bridge/done/l923-05.result.md` 与本档 §三 的口径互补：l923-05 只点了 `:134` 一条会红，实测 **`lru-rw` 还会带红 `:120`** ⇒ 该 result 的"改 LRU 的影响面"少列一条（done 档不可回改，请台账加注）。
3. 索引件「git 入库」列整列过期（l924-18 已登记，此处不重复计数）。

**复算配方**
```bash
cd D:/code/learning-system
# 1 锚点与键形
sed -n '44,56p' core/ai_review.py; rg -n "_feedback_cache|_FEEDBACK_CACHE_MAX|popitem|sha1" core/ai_review.py
# 2 三条桩动作序列重放（A_*）＋命中率对拍（B_*／B2_*）＋条目体量（C_*）
PYTHONIOENCODING=utf-8 python tmp/l924-20/cache_sandbox.py
# 3 现值负载（只读，跑完复验无侧车）
PYTHONIOENCODING=utf-8 python -c "import sqlite3;c=sqlite3.connect('file:data/progress.db?mode=ro&immutable=1',uri=True);print(c.execute('select count(*),count(distinct lang||problem_id||code) from attempts').fetchone());print(c.execute('select min(length(ai_feedback)),max(length(ai_feedback)) from attempts').fetchone());c.close()"
# 4 两类题宇宙
rg -n "ai_open" content/*/*/*.yaml | wc -l   # 与 §一 loader 口径并列对（正则轨 vs 运行时轨）
# 5 索引闭合（本档同批自登）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q
```
> 沙盒第 4 条是**正则轨**，严格串读数 66；`rg -o "judge_mode.{0,12}" content/ --no-filename \| sort \| uniq -c` 现读 `judge_mode: ai_open` **66** ＋ `judge_mode: "ai_open"` **4** ＝ 70，与 §一 的运行时轨**逐位对上** ⇒ 差额已归因，不取单个数（纪律档 §十.3）。容量决策用运行时轨（70/333），因为那才是真会进缓存的两类题。
