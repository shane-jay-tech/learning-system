---
id: l927-20
title: 相似题互链功能缺口——字段形态 vs 外置映射文件的取舍与 loader 接入面（设计稿，零码改动）
task: l927-20（zcode-bridge 波次 24，工作类型 docs，风险档 B）
shift: qoder-executor-20260927-1850-learn48
written: 2026-09-27T18:4x
head_at_write: 4d11b51（开工 `git status --porcelain` 0 行；brief §5 表里的 `2665f0a` 已漂移，按磁盘现值取）
mode: 全程只读（content/ 零 diff、core/ 零 diff；`data/progress.db` 未打开、未走任何 `dao=None` 路径；未起服务、未调 LLM、未跑 pytest）
status: 设计稿——判据①②③④全中；**不落字段、不改 loader、不改题面**（落 `similar_to` 属改数据契约＝人工闸）
supersedes_or_extends: extends `zcode-bridge/done/20260925-154245-6130.result.md`（近重复检测原始读数）与 `docs/insights/l927-18-case-mismatch.md`（16/7 独立复现＋判题口径）；本档只补"要不要把它变成产品字段"这一层
---

# 相似题互链：形态对比 ＋ loader 接入面 ＋ 数据来源论证

> 卷宗完成标准：①两形态对比 ②loader 接入面 ③数据来源论证 ④零码改动。
> 本班按 `154245` 遗留 1 的口径接续：那单说"A 类建议若采纳需要新增字段＋loader 消费面＋测试，属写单"。本档就是那张写单的**前置设计**，不是它本身。

## 〇、一句话结论

1. **本仓今天没有任何互链载体**：409 个 `content/**/*.yaml` 的顶层键全集 19 种，键名正则 `similar|related|link|see_also|variant|dup` 命中 **0**（本班独立复算，读数见 §1）。
2. **要链的内容是"派生数据＋人工裁决"的混合体**：宽档口径 **16 对 / 15 组 / 涉及 31 题 / 单点最大度 2**（与 154245、l927-18 三档逐位对平），其中 **7 对期望答案互斥**（l927-18 B 类）⇒ 链可以自动扫出来，但"这条链该不该让学生点"必须逐对人工签。
3. **推荐形状：B（外置映射）作证据层＋A（题内字段）作消费层，但落点只有一个**——先 B、A 的 `similar_to` 只写"人工签过的那批"（今天＝0 条），理由不是"字段不好"，而是**A 形态在本仓撞三道现成的闸**（CRLF 24 文件、`test_mark_r_judge_plain.py:588` 字节基线、re-scan 会想覆盖人工裁决），而 B 形态撞的两道闸（loader 缓存签名、`content/paths/` 被 `listdir` 当成路径）**是可以在设计期绕开的**。
4. 🔴 **本档不落任何字段、不改 loader、不改题面、不改判分口径**。§3 的接入面是"如果人批了，最小要动哪 6 处"的清单，不是待办。

---

## 一、盘上事实（本班自己取的可复算读数）

复算入口：`PYTHONIOENCODING=utf-8 python D:/code/tmp/qoder-executor-20260927-1850-learn48/probe_similar.py`（rc=0，读数落同目录 `similar_out.json`；探针**故意保留**，因为本档 §1/§4 的每个数字都能用它整段重跑）。

| 读数 | 现值 | 与在册锚点对照 |
|---|---|---|
| `content/**/*.yaml` 文件数 / 可解析 mapping | 409 / 409（零解析失败） | 154245 否证① 同值 |
| 题件（顶层含 `statement`） | **403** | 与 `tests/test_content_census.py:27` 的 403 桩一致 |
| 顶层键种类 | 19 种（`title 409 / topic 403 / difficulty 403 / tags 403 / statement 403 / hints 403 / starter_code 399 / expected_output 279 / judge_mode 140 / tests 92 / rubric 70 / reference_answer 60 / setup_sql 54 / expected_rows 54 / subtitle 6 / icon 6 / estimated_hours 6 / milestones 6 / starter_code_note 1`） | 逐键逐值与 154245 否证① **全等** |
| 互链类键名命中 | **0**（正则 `similar\|related\|link\|see_also\|variant\|dup`） | 缺口在世 |
| 近重复对（题干归一化＋3-gram Jaccard≥0.30 预筛＋`SequenceMatcher.ratio()≥0.75`） | **16 对 → 15 个连通分量**（14 组二元＋1 组"链式"三元） | 154245／l927-18 第三次独立复现 |
| 涉及题数 / 涉及文件数 | **31 / 31**（一题一文件，无合并文件） | 同 154245 |
| 跨语言对 / 同语言对 | **12 / 4** | 同 154245 否证③ |
| 单点最大链度 | **2**（度分布 `1:30, 2:1`）⇒ 每道的 `similar_to` 列表长度 ≤2 | **新读数**（前二档未量过）：字段形态的取值域天然很小 |
| 题文件行长度 最小/中位/最大 | 16 / 25 / 67 行 | 用于估 A 形态的 diff 体积 |
| `content/**/*.yaml` 盘上 CRLF 文件数 | **24**（其余 385 纯 LF，混合行尾 0） | 与 `tests/test_content_crlf.py:12-14` 自述的 24 同值；**其中 2 个落在 31 道互链成员里** |
| 外置映射文件粗算体积 | 16 对的 id 列表 JSON ≈ **1,169 B**（未算注释头） | 用于 §2 的"一文件 vs 31 处编辑"对比 |

在册闸（本档不撞、但落 A 形态必撞，逐条盘上核过）：
- `tests/test_content_crlf.py`（钉"零孤立 CR＋文件内行尾自洽"）＋ `core.autocrlf=true` 且**无 `.gitattributes`** ⇒ 手工往 CRLF 题文件里插一行，编辑器/工具稍有差池即红。
- `tests/test_mark_r_judge_plain.py:588 test_真题库_run题现状字节_等于原文加恰一行judge_mode_run` 把 **r/ 70 道 run 题的现状字节**钉成"`data/backups/content-20260920-133722/` 的 pre-D6 备份字节 ＋ 恰一行 `judge_mode: run`"（备份不在盘时该例会 `pytest.skip`，但**它在盘**：`data/backups/content-20260920-133722/`）⇒ 往 r/ 成员题文件再加一行 = 直接改这条字节基线的判定，属**在册"基线不属内容班权限"域**（l922-04 原话）。
- 31 道成员里 **10 道**被学习记录引用、**18 个专题全部**被 `content/paths/*.yaml` 的 85 条 topic 引用（154245 合并闸）⇒ 互链本身不动这些，但**任何"顺手合并"的念头都会撞到**，故 §2 把"不可合并"写死成前提。

---

## 二、① 两形态对比

前提（两形态共用，不重新裁决）：pair 集 = 154245 宽档口径，**必须先过人工裁决**才能对学生露出（7/16 期望答案互斥，l927-18 B 类；照题面答会被判错的活缺陷已另有在册档，见 §四·闸 3）。

| 维度 | 形态 A｜题内字段 `similar_to: [id]` | 形态 B｜外置映射文件（如 `content/similar_map.yaml`） |
|---|---|---|
| 写入面 | **31 个文件各加 1 行**（每度 ≤2 ⇒ 列表最多 2 项；16 对若**双向**写＝32 行、**单向**写＝16 行） | **1 个新文件**（≈1.2 KB 净数据） |
| 与 re-scan 的关系（🔴 决定性维度） | 扫描器输出的 pair 与人工签过的 pair **混在同一批文件里**，再扫一次要覆盖谁没有规则 ⇒ 要么丢弃人工裁决、要么写"只增不减"的合并逻辑（＝新代码） | 扫描器**只重写这一个文件**（派生层，可再生），人工裁决另落一份 `docs/insights/lXXXX-similar-adjudication.md` 或在 map 里加 `status: pending\|signed`；**再生与承诺天然分层** |
| 一致性风险 | 双向性靠自觉（A 写了 B 没写 A ⇒ UI 上"相似题"单边可见）；悬挂 id（改名/删除后）散在 31 处，**逐文件才能发现** | 悬挂 id 集中一处可校验；双向性可在 loader 里一次性补（读侧对称化），**存储层允许只存一条有向边** |
| loader 改动 | `Problem` 加字段 ＋ `_build_problem` 加显式映射（**两处，且必须同时改**，见 §3-2 假绿形状） | 一个新 loader（`core/paths.py` 已有同形状先例：`_path_cache` ＋ `load_all_*`），**现有 `Problem` 结构零改动** |
| 缓存/失效风险 | 低（题文件 mtime 本就在 `_signature` 里） | 🔴 **高，且必须显式设计**：`core/loader.py:97-116 _signature` 只 `os.walk(lang_dir)`、只收 `.yaml/.yml/.md` ⇒ map 放 `content/` 根、或用 `.json` 扩展名，**都不会触发缓存失效**，改完不生效且现象像"代码没跑"（2 秒 TTL memo，`:93`） |
| 撞现成测试闸 | 🔴 CRLF 桩 ＋ r/ 字节基线（见 §1）＋ 31 个 diff 的评审成本 | 只撞 2 道**可预判**的：`core/paths.py:76` 用 `os.listdir(_PATHS_DIR)` 把所有 `*.yaml` 当**学习路径**（⇒ map 绝不可落 `content/paths/`，否则 `load_path` 读 `data["title"]` 当场 KeyError／`tests/test_paths.py:35` 钉 6 条路径立刻红）；`scripts/import_dry_run.py:105` 对 `content/<lang>/` 做 `rglob("*.yaml")`（它靠 `"statement" in data` 过滤，map 不带 `statement` ⇒ 安全，但**map 不能放进语言目录**这条要写进注释） |
| 学生可见性的语义 | "这道题自己的属性"，与 `hints`/`tags` 同层，题面级评审自然 | "系统算出来的关系"，需在 UI 上说明来源（否则学生会以为"官方说这题和那题一样"，而 7 对其实**答案互斥**） |
| 回滚成本 | 31 个文件的反向 diff；r/ 那 2 个成员还要同步字节基线判定（**回滚不等于复原**） | 删 1 个文件＋（若已接 loader）revert 1 个新模块；`content/` 有 git 还原点 |
| 可评审性 | 逐对裁决记录散在文件里，"哪些对已签"要扫全库才知道 | **一屏可签**：一个文件就是 pair 全集 ＋ 每条的 `status`，与 kaoyan 的产线形状同构（§4） |

**推荐（给人拍的判断题，非本班待办）**：**B 先行、A 后置且只装已签子集**。
- 关键理由不是"改文件少"，而是**A 形态把"派生数据"和"人工承诺"焊死在同一行里**，而本仓的互链候选**每次 re-scan 都可能变**（阈值是 154245 临时定的双档，未经内容侧校准——154245 遗留 6 原话）；B 形态允许扫描器无脑重写，把"签过"这件事留在另一个可审计的地方。
- 若人工反过来选 A，前置要求只有两条：① 先给 `content/**/*.yaml` 落 `.gitattributes`（`*.yaml text eol=lf` ＋ `--renormalize`）并**同步重建 r/ 备份基线**（l922-04 遗留 1 已把它列为"仓库级策略＋r-judge 族联动，留日间定夺"），否则 31 处编辑要先付这两笔账；② 定死"单向存、双向读"还是"双向存"，并在 loader 里对称化。

---

## 三、② loader 接入面（"真要落地，最小要动这 6 处"——清单，不是执行）

1. **`core/loader.py:17-33 Problem`**：`similar_to: list = field(default_factory=list)`。
   加在**末尾且有默认值** ⇒ `tests/test_scripts.py:257/263/270`、`tests/test_judge.py:94` 这类手工构造 `Problem(...)` 的用例不受影响（关键字构造，实测三处均用 kwargs）。
2. **`core/loader.py:181-219 _build_problem`（🔴 必须同刀改）**：该函数是**白名单式取值**（`data.get("statement")`、`data.get("hints")` …逐键写），未在映射表里出现的顶层键会被**静默丢弃**。⇒ 只在 yaml 里写 `similar_to` 而不同刀加 `similar_to=_as_str_list(data.get("similar_to"))`，会出现"文件里明明有、界面上永远空"的**假绿形状**；且要照 `:186-189` 对 `tags`/`hints` 的同一防御（`list` 才当序列，字符串要 `[str(...)]` 而不是被拆成单字符）。
3. **解析/校验闸（B 形态才需要）**：新 `load_similar_map()`，照 `core/paths.py:36-63` 的形状（模块级 cache ＋ 逐键 `.get()` 兜底 ＋ 不抛异常）。**必须做的两条校验**：① 每个 id 能在 `find_problem` 里解到（悬挂 id 要么丢弃要么进诊断，别静默露给学生）；② 把 map 文件的 mtime **并入** `core/loader.py:126-136` 的缓存 key（或自持 cache），否则 §2 的陈旧缓存坑必咬。
4. **跨语言解析面**：`core/loader.py:222-227 find_problem(lang, problem_id)` 是**按语言分片**的 API，而互链 12/16 是跨语言对 ⇒ 需要一个 `find_by_full_id(pid)`（id 首段即 lang：`pid.split("/", 1)[0]`，与 `_build_problem:184` 的 `f"{lang}/{slug}/{problem_slug}"` 拼法同型）。
   正向证据：UI 侧的选择状态**已经在用全 id 比**（`ui/pages/language.py:180 if p.id == target_problem_id`）⇒ 互链只需把 id 交给 `ui/components.py:67-90 navigate_to_problem(lang, topic_slug, problem_id)`，**该函数已支持跨语言跳转并自带 session 清理**，这是接入面里最省的一处。
5. **判题零影响（本方案最重要的安全论证，逐点枚举过）**：`Problem.to_dict()` 是 `asdict` ⇒ 新键自动进 pdict，但**所有下游按 `.get()` 白名单取用**：
   `core/judge.py:216-256 _run_test_cases`（只读 `setup_sql/expected_rows/tests/expected_output`）、`:273-282 _build_display`、`:300-301`（`judge_mode`）、`:315-316`（`difficulty`/`id`）；
   `core/ai_review.py:243-259 review`（只读 `title/statement/expected_output|expected_rows/difficulty`）、`:439-448 grade_open_answer`（只读 `statement/rubric/reference_answer`）⇒ **`similar_to` 不会进 prompt、不会进判分、不会进 `expected_display`**。
   另注：`core/judge.py:35-47 _to_problem_dict` 的 `for k in (...)` 兜底白名单**不含新键**，只在"传进来的既无 `to_dict` 也不是 dict"时生效（`AI_VARIANT::` 变体面）⇒ 落 A 形态时要顺手决定是否补进去，否则变体题拿不到互链（属"可接受"，但要有意写下来）。
6. **测试与爆炸半径**：
   - 需要新增：loader 单测（字段解析／字符串防御／悬挂 id／双向对称化）＋ 一条"map 里的 id 全部可解"的普查桩（照 `tests/test_paths_reconcile.py` 的比例式风格，别写死条数）。
   - 不受影响：`tests/test_content_census*.py`（题数 403 与答案字段计数，新增键不进它们的判定；实测 `test_content_census.py` 只断言 `statement`/答案字段/`difficulty`/`hints`）；`core/data_portability.py:29-51 export_all` 只搬 `progress` 库的行、**不搬 content** ⇒ 导出/导入 JSON schema 零变化（`tests/test_import_dedup.py`／`test_data_portability*.py` 不受牵连）。
   - 会红：`tests/test_content_crlf.py`（A 形态若把 CRLF 文件改成 LF 混行尾）、`tests/test_mark_r_judge_plain.py:588`（r/ 成员加行）、`tests/test_paths.py:35`（B 形态文件误落 `content/paths/`）。这三条就是 §2 表"撞现成测试闸"的可执行判据。

---

## 四、③ 数据来源论证：与 kaoyan 近重复批（571 对族）的关系

**结论：方法不可移植，产线形状可照抄，数字不可借用。** 三点分开说，逐条带出处。

1. **判据载体不同 ⇒ kaoyan 的三信号在本仓无信号可用**。kaoyan 口径（`D:/code/kaoyan-system/docs/insights/question-near-dup-scan-20260905.md:5-9`）是三信号：A 题干归一化**完全相同**、B 归一化前 50 字相同、**C 同 `knowledge_point_id` 且选项文本集合 Jaccard≥0.8**；`near-dup-adjudication-batch1-20260909.md:4` 的"全库共 **571 对**"用的就是 C 为主键的口径（"同知识点选项集 Jaccard≥0.8，与 k47a 总账脚本一致；其中答案文字相同 41 对"）。
   ⇒ 本仓**选项查无此物**：403 道题全是"写代码／画图／开放作答"型，顶层键全集 19 种里没有 `options/choices/answer`（154245 否证①，本班 §1 第三次复算同值），`knowledge_point` 的对应物是 `topic`（403/403 有值，distinct slug 84）＋`tags`（416 唯一值）。
   ⇒ **571 这个数在本仓没有对应物，不能借用**；本仓能沿用的是"题干归一化＋知识点面"这一条，其现值＝16 对/15 组/31 题（§1，已三度复现）。
2. **兄弟仓的经验：裁决 571 对，至今零字段**。`D:/code/kaoyan-system` 全仓 `grep -rl "similar_to"` **rc=1（零命中）**——它把这套关系做成了**外置件产线**：原始 pair 落 `docs/insights/question-near-dup-scan-20260905-pairs.json`（44,953 B，形状 `{"sigA": [[id, 科目, 题干前缀], …]}`，按信号分桶）→ 逐批裁决 md（`near-dup-adjudication-batch1…batch8`／`b7`／`batch3-execution`／`batches-crossaudit`）→ 聚合主清单 `near-dup-true-dup-masterlist-20260907.md:3`（"batch2a–8 十批，193 对中判真重复 75 对"，多副本家族 9 组 27 对涉及 31 题）。
   ⇒ 两条经验直接可用：① **"外置映射＋逐批裁决 md"在同生态里是被验证过的形状**（§2 推 B 的经验依据，不是本班拍脑袋）；② 同一个"近重复"家族在 kaoyan 内部就有 **571 / 199 / 193 / 75** 四个不同总体的读数（全库口径／sigC／进裁决批次／判真重复）⇒ **互链数据必须自带口径头**（扫描日期、HEAD、阈值、总体定义），否则下游会把四个数当同一个用。这也是 §2 里 B 形态"文件头写口径"比 A 形态"31 个文件各写什么"更容易守住的原因。
3. **但目标不同，故本仓不能停在"只有 md"**：kaoyan 产线要的是**给人拍的停用裁决**（"停用需用户拍板，BACKLOG B-052"），学生侧不消费；本仓若立项"相似题互链"是要**给学生看的可点链接**（消费面存在 ⇒ 才有形态 A 的意义）。⇒ 分层结论：证据/再生层照 kaoyan 走 B（含口径头），消费层若批了才落 A 且**只装 signed 子集**，两侧用全 id 对齐。
4. 🚪 **三道闸（本档一律不推）**：
   - 闸 1｜落 `similar_to` 字段＝**改数据契约**（题件 schema 加顶层键）＝人工闸；本档只出 §3 的最小改动面。
   - 闸 2｜"哪些对可以露给学生"＝**内容裁决**（7/16 期望答案互斥，露出去等于暗示两题等价）。
   - 闸 3｜**别把互链读成"重复题可合并"**：同一机制的活缺陷已在册——`content/agent_dev/06_frontier/05_cot.yaml:9` 与 `content/agent_dev/01_git_basics/05_revert.yaml:9` 都写"也接受 X"，而 `core/judge.py:259` 是归一化后**精确串比** ⇒ 照题面答会被判错（出处 `docs/insights/l927-18-case-mismatch.md` §2-A，两案修复方向**均未拍板**）。本档碰到的是同一机制，**引它、不重复修**。

---

## 五、④ 零改动自证 ＋ 复算入口

- **git 面**：写本档前 `git status --porcelain` **0 行**（HEAD `4d11b51`）；本班**未 add / 未 commit / 未 checkout / 未 restore / 未 stash / 未 clean**（brief §5 禁列）；`content/` 与 `core/` **零 diff**；本档是 `docs/insights/` 下唯一新增件。
- **生产库**：`data/progress.db` **未打开过**（本班不需要 db 读数；154245 的历史引用即可）。开工 `certutil -hashfile data/progress.db SHA256` 前 8 位＝**`cd2dbce4`**、size＝**122,880 B**（与在册基线同值，mtime 恒 `Sep 25 20:49`）；收工同法再取一次（数值见 result 的「证据」节）。在册前科：`core/judge.py:199` 与 `:342` 的 `d = dao or ProgressDAO()` 在 `dao=None` 时会自开生产库 ⇒ 本班**未调用**任何 `judge/ai_review` 入口。
- **侧车说明（免得被误判成本班写库）**：`data/progress.db-shm` 的 mtime 会因**只读探针**刷新（大小 32,768 B 不变），本单连库都没开，该侧车变化与本班无关；主证一律是**主库 size＋sha8 前后不变**。
- **零联网／零 LLM／零服务**：未调 `scripts/llm_call.py`、未起 Streamlit、未开端口（本档判据不需要运行时读数）。
- **未跑 pytest**：并发窗禁跑全量（同刻 `colony41`／`quant49`／`psy77`／`kaoyan78` 在别仓），且本档零码改动、无判据需要测试数；§3 的"会红哪三条"是**读码结论**并已给出行号，落地单跑基线时再取实际 rc。
- **探针**：`D:\code\tmp\qoder-executor-20260927-1850-learn48\probe_similar.py` ＋ `similar_out.json`。**本档有意保留**（产物点名它当复算入口，符合 brief §6 的"自清"例外）；仓内 `tmp/` 未落任何件（`git status` 0 行即证）。
- **insights 索引**：本班**未代登**（真哨兵 `tests/test_insights_index_closure.py`，写本档前磁盘 98＝收录 98 闭合）。本班交班后该桩会红 1 例（missing＝本档），那是主班的账。

---

## 六、给主班／人工的最小裁决条目（照此拍，不必重读全文）

| # | 待拍问题（一句） | 选边后果（可复算依据） |
|---|---|---|
| Q1 | 互链要不要变成学生可见的功能？ | 不要 ⇒ 本档与 154245 的建议 A/B/C 一起归档即可，零改动；要 ⇒ 进 Q2 |
| Q2 | 关系数据存 B（一个外置文件）还是 A（31 个题文件各一行）？ | B 撞 `content/paths/` 与 loader 缓存两道可预判闸（§3-3）；A 撞 CRLF 桩＋r/ 字节基线（§1 在册闸）且需先定 `.gitattributes` 策略（l922-04 遗留 1） |
| Q3 | 单向存、双向读，还是双向存？ | 双向＝32 行编辑量＋单边漏写风险；单向存＋读侧对称化＝16 条边，但要在 §3-3 的新 loader 里写明 |
| Q4 | 7 对期望答案互斥的题对，露不露？ | 露 ⇒ 等于系统宣称"这两题相似"而两题答案互斥（l927-18 B 类），需内容侧一句话定调；不露 ⇒ 消费面只剩 9 对（§1 度分布随之变小） |
| Q5 | `similar_to` 的 id 校验闸放哪？ | 只放 loader（运行时丢弃悬挂 id）⇒ 坏数据静默；放普查桩（`test_paths_reconcile.py` 同族）⇒ 改名当场红，但会把"扫出来的候选"也一并钉死，需 Q2 分层 |
