---
id: l927-21
title: AI 回显期望输出风险面——"148 题"口径静态复核 ＋ 离线小样本验证方案（N=5）＋ 两案裁决材料
task: l927-21（zcode-bridge 波次 24，工作类型 docs，风险档 B）
shift: qoder-executor-20260927-1850-learn48
written: 2026-09-27T18:5x
head_at_write: 4d11b51（开工 porcelain 0 行；收工时工作树仅本班新增档）
mode: 全程只读＋零调用——**未发任何 LLM 请求、未联网、未起服务、未跑 pytest、未开生产库**；148 题口径只做静态复核（读 prompt 组装与系统提示原文），未构造真请求
status: 静态复核＋方案设计——判据①②③④全中；**不改判分口径、不改题面、不改 prompt 文本**（禁令补齐属生产码改动＝人工闸）
supersedes_or_extends: extends `zcode-bridge/done/20260925-154241-2218.result.md`（K-4 静态证据与本方案的直接上游）与 `docs/insights/l927-18-case-mismatch.md`（同机制的判题侧读数）；本档补的是"要坐实需要什么实验"这一层，并**否证其 148 的口径边界**
---

# AI 回显期望输出：148 题口径复核 ＋ 离线小样本方案 ＋ 两案

> 卷宗完成标准：①148 题口径复核 ②验证方案五要素 ③两案推荐 ④零码改动。
> 上游一句话（154241 K-4）：prompt **逐字含期望输出**（`core/ai_review.py:256`），而 STRICT 档系统提示**无"不得透露答案"条款** ⇒ 风险面 148 道；"回显率"未实测（点真 LLM＝发外部请求，卷宗禁止）。

## 〇、一句话结论

1. **148 这个数复现了，但它不是"回显暴露面"**：难度分布 `{1:75, 2:180, 3:131, 4:16, 5:1}` ⇒ `difficulty≥3` 恰 **148 道**（与上游同值，上游的 `1:81/总 409` 是把 6 个 `content/paths/*.yaml`（无 `difficulty`、非题件）也计了进去；按 `core/loader` 的 403 题件口径是 `1:75`，**148 不变**）。
2. 🔴 **148 里只有 108 道真的走到那条含答案的 prompt**：另外 **40 道是 `judge_mode=ai_open`**，`core/judge.py:300-301` 在进 `review()` **之前就早退**到 `_judge_open → grade_open_answer`，用的是**另一条 prompt**（送 `rubric`＋`reference_answer`，`core/ai_review.py:442-448`，链是**质量档 gpt 优先**）。
3. 🔴 **同时 148 又低估了暴露面**：`expected` 的注入（`:246`＋`:256`）在**三档系统提示下完全同源**——`_build_review_system_prompt:185-191` 只按"难度≤2 且是否通过"换语气，**不换送不送答案**。全仓走 `review()` 且 expected 非空的是 **333 道**（=279 串面＋54 行面，与 l927-18 对平）⇒ STRICT **108** ＋ BEGINNER **225**；三档里只有 `BEGINNER_FAIL` 一档带半句禁令（`:176`「不直接给完整答案」），`STRICT` 与 `BEGINNER_PASS` **零禁令**。⇒ 风险面应按**路径**划（review 333／open 60），不按难度档划。
4. 🔴 **可做小样本验证的池只有 36 道（不是 148）**：108 道 STRICT-run 里 **72 道的期望值本来就写在题面里**（AI 复述它不构成新泄漏、也无法归因给 `expected` 注入），可归因池 **36 道**（30 串面＋6 行面；再要求期望值 ≥4 字符 ⇒ **33 道**）。**5 枚样本必须从这个池里抽**，否则实验结论是假的。
5. **两案推荐（给人拍）**：推荐 **"先补禁令（案甲）＋ 阶段 0 零调用留痕同批做"**，把"要不要花 N=5 真调用"留给案甲落地后另拍——理由与反向条件见 §4（🔴 反向条件很硬：若人工认定"AI 复述期望输出＝对答案的教学价值"，案甲就是在改产品行为，那时必须先验证）。

---

## 一、① 148 题口径的逐层复核（本机现取，命令见 §5）

| 层 | 读数 | 与上游/在册对照 | 判定 |
|---|---|---|---|
| 题件总数（`content/**/*.yaml` 顶层含 `statement`） | **403** | `tests/test_content_census.py:27` 钉 403 | ✔ |
| `difficulty≥3`（＝"走 STRICT 档"） | **148**（131+16+1） | 上游 154241 同值 | ✔ **148 复现** |
| ↳ 其中 `judge_mode=ai_open` | **40** | 上游未拆（其 70 ai_open 是全难度） | 🔴 **这 40 道不经过 `review()`** ⇒ 不在"逐字含期望输出"的那条 prompt 上 |
| ↳ 剩余 STRICT-run | **108**（串面 88＋行面 20；**期望值为空 0 道**） | — | 这一层才是 K-4 说的"prompt 含答案" |
| ↳↳ 其中"期望值 ⊂ 题面原文"（混淆，不可归因） | **72**（≤3 字符短串 28 道／≥6 字符 37 道） | — | 混淆面上界 72；短串那 28 道需人工逐看才能排除 |
| ↳↳↳ **可归因池**（回显实验的抽样框） | **36**（串面 30＋行面 6）；期望值 ≥4 字符者 **33** | 新读数（前档未量过） | 🔴 **小样本只能从这里抽** |
| BEGINNER 档（难度≤2）走 `review()` 且 expected 非空 | **225**（其可归因 42） | — | ⇒ "无禁令"不是 STRICT 独有，`BEGINNER_PASS`（`:154-166`）同样零禁令 ⇒ 总暴露面 **333**，STRICT 占 108 |
| 开放题评分面（`ai_open` 且有 `reference_answer`） | **60**（另有 10 道 ai_open 无参考答案） | 上游 LEAK-4 人群 60 ✔ | 另一条注入位（`:445-447`），链是 `_QUALITY_CHAIN`（**gpt 优先＝中转计费**） |

题面/判分侧的同机制在册事实（**引而不修**）：`core/judge.py:259` 归一化后**精确串比** ＋ `content/agent_dev/06_frontier/05_cot.yaml:9`、`content/agent_dev/01_git_basics/05_revert.yaml:9` 的"也接受 X" ⇒ 照题面答会被判错；出处 `docs/insights/l927-18-case-mismatch.md` §2-A，两案修复方向均未拍板。**本档不重复提修法、不改判分口径、不改题面。**

---

## 二、禁令缺失的逐字证据（静态读码，零请求）

| 事实 | 位置 | 原文/读数 |
|---|---|---|
| 答案进 prompt（三档共用） | `core/ai_review.py:246`＋`:256` | `expected = problem.get("expected_output") or problem.get("expected_rows") or ""` → `f"期望输出：{_trim(str(expected), 800)}\n"` |
| **注入位全集只有两处** | `grep -n "期望输出\|参考答案\|题目要求" core/ai_review.py` | ⇒ `:255/:256`（review 路径）与 `:447`（开放题路径）；🔴 **`follow_up()`（`:300-352`）不直接送 `expected`**，但它把**上一轮 review 正文**（`initial_review`，`:345`）回送模型 ⇒ 一旦首轮回显，追问轮会**二阶携带**且 `FOLLOW_UP_SYSTEM`（`:119-129`）同样零禁令；`ask_lesson()` 只送 `lesson_md`，无答案面 |

| 行面题送的是 **Python repr** 而非表格 | `:246`（`expected_rows` 是 list）＋`:256` 的 `str(expected)` | AI 看到的是 `[["Engineering", "2.0"], …]` 形状 ⇒ 回显判据要按 `str(list)` 比，不能按展示形状比 |
| STRICT 档硬性要求 5 条，**无一条**关于答案/回显 | `:146-151` | 「不说空话」「即使通过也要给 1 条改进」「不贴超过 3 行代码」「不用英文缩写」「总长 200-300 字」 |
| 全模块禁令唯一命中处 | `:176`（`BEGINNER_FAIL`） | 「【怎么改】给一个明确的修改方向（**不直接给完整答案**）」——只覆盖"未通过＋难度≤2"一档，且禁的是"完整答案"不是"复述期望输出" |
| 后处理不查回显 | `:276-284 _post_check` | 只在 `difficulty≤2 且 passed` 时数" harsh markers"补一句安慰话；**没有任何"输出含期望值则改写"的分支** |
| 反馈缓存是**进程内 FIFO 64 条** | `:55-68`（`_feedback_cache`/`_FEEDBACK_CACHE_MAX=64`，淘汰语义系 l922-10/l923-05 订正） | 键 `(lang, pid, sha1(code))` ⇒ **同一份合成码复跑不重新发请求**（复跑取证的隐形陷阱，方案 §3-E2 要处理）；也说明"留痕"不在库里，进程退出即无 |
| prompt 版本无 bump 痕迹 | `:26-33 PROMPT_VERSIONS` | 三档 code_review 全 `v2.0`（`open_scoring` 已是 `v2.1` ⇒ 存在"改文案就 bump 版本"的在册惯例可沿用） |
| 改 prompt 会不会让测试红 | `tests/test_ai_review_strategy.py:12-45` | 该桩是把 `_build_review_system_prompt(...)` 的返回与 `_SYSTEM_PROMPT_*` **同一对象自比对** ⇒ **改文字不会红**（这是"案甲成本极低"的实测依据，不是推测）；`tests/test_core_edges.py:66-75` 用 `monkeypatch` 替掉 `_call/_call_chain`，为**假调用桩**提供仓内现成先例 |
| 零联网也能证"答案在送入内容里" | `core/config.py:5-7` | `get_llm_script_path()` 读环境变量 **`LLM_SCRIPT`** ⇒ 把它指到一个本地 shim，即可在**不发任何外部请求**的前提下捕获真实组装好的 prompt 全文（阶段 0 的落点） |

---

## 三、② 离线小样本验证方案（五要素；两阶段）

🔴 **本方案是本档的产物，本班一步未执行**（零调用、零联网、零费用、零写库）。阶段 1 需主班/人工放行才成立。

### 阶段 0｜零成本、零调用的"暴露机制"取证（建议先做，不需授权面）
`LLM_SCRIPT` 指向班名目录下的 shim（打印 argv 里的 `--prompt`/`--system` 到文件后 `exit 1`）⇒ `review()` 拿到空返回、落 `_offline_fallback`（**不改判分**，判分在 `judge()` 里且答案面另有展示闸），但**送入内容已逐字留痕**。
产出＝"期望输出确实在 prompt 里、且系统提示里无禁令"的**可提交文本证据**；它回答不了"模型会不会回显"，只把 §2 的读码结论升级为"运行时实证"。护栏：直调 `ai_review.review()`，**不经 `judge()`** ⇒ 零 DAO、零 `attempts`/`learning_events` 写入（在册前科：`core/judge.py:199` 与 `:342` 的 `d = dao or ProgressDAO()` 在 `dao=None` 时自开生产库 `data/progress.db`）。

### 阶段 1｜N=5 真调用（须人工放行）——五要素

| 要素 | 口径 |
|---|---|
| **E1 样本框与选择规则** | 池＝§一 的**可归因 STRICT-run 36 道**（叠加"期望值 ≥4 字符"⇒ 33 道，避免 1–3 字符期望值的回显判定假阳/假阴）。分层：**4 语言全覆盖**（池内语言＝cpp/python/r/sql）＋**串面/行面都要有**（行面 6 道里抽 1）。候选（按期望值升序，本班实测前 12）：`r/06_mixed_apa/01_lmer_fixef`、`r/11_survival/02_survfit_median`、`python/21_datetime_ts/02_tenure_days`、`r/06_mixed_apa/03_cohens_d`、`python/15_ab_text/02_cohens_d`、`python/20_hr_pandas/04_training_vs_performance`、`sql/06_window_functions/03_running_sum`、`sql/06_window_functions/04_lag`、`cpp/13_move_semantics/02_lvalue_rvalue`、`python/13_scipy_stats/06_anova_one_way`。🔴 **默认不含 `ai_open` 样本**（它走 `_QUALITY_CHAIN`＝gpt 优先＝中转计费，且判分口径不同）；要测开放面请单开一批并明确计费腿。 |
| **E2 执行路径与护栏** | 入口＝`core.ai_review.review(lang, pdict, code, run_result, passed=True)`，`pdict` 由 `core.loader.find_problem` 取 `Problem.to_dict()`；`run_result` 用 `SimpleNamespace(stdout=…, stderr="")`。🔴 **不经 `judge()`／不传 `dao=None`**（理由同上）；🔴 **`code` 一律用合成码**（照 `tests/test_core_edges.py` 的 `"print(1)\n"` 风格），**严禁从 `attempts.code` 取真实历史作答**（隐私面，且会把一次审计变成搬学生代码出仓）；🔴 **绕开反馈缓存**：每枚样本的代码尾注释带样本号（键含 `sha1(code)` ⇒ 天然不撞），或批次开头清空 `_feedback_cache`；失败重试上限 1 次；`_call` 侧只走现成 `subprocess`（`:519-544`），**不改任何链/超时常量**。 |
| **E3 排程与预算** | 谷时窗执行（在册口径：闲时/夜间跑批量，`AGENTS.md` 记「谷时输出价只有峰时的 2/9」「周日无峰时」；工作日 14–18 峰时一律不排）。时间上界＝`_CHAIN_BUDGET_SEC 45.0 × 5 ＋ 重试 ≤ 1 枚` ⇒ **最坏 ~4.5 分钟**，单次 `TIMEOUT_SEC 30`。调用数硬上限 **5（＋重试 ≤5）**，写进脚本常量而不是靠记性。 |
| **E4 费用预估** | 量级由 §5 实测的 prompt 体积算：`system 683 字符` ＋ `user 117–356 字符`（5 枚候选的静态值）＋合成代码与 stdout ≈ **每枚 1.0–1.6 KB 字符**，输出被 STRICT 档钉在 **200–300 字**。按 DeepSeek 官方 flash 谷时档（约为 pro 的 1/3；pro 谷时 ≈ 输入 3／输出 6 ¥/M，见 `AGENTS.md` 成本实账）⇒ **5 枚合计个位数 ×10⁻³ ¥ 量级，即"几分钱以内"**；即便全链退到 gpt 中转（fallback 腿）也只是同量级 × 若干倍。🔴 这是**为排程决策用的量级公式，不是资金/账单结论**：真账以 `D:\code\zcode-bridge\data\cost_log.jsonl` 与中转余额为准，跑完由主班复核。（统计口径同理：N=5 只能证"存在性"，**不可外推回显率**——5/0 与 0/5 都不构成率的结论。） |
| **E5 留痕格式** | 目录：`docs/insights/l927-21-echo-probe-<YYYYMMDD>/`（人工放行后才建；⚠ 一旦落 `docs/insights/` 会被索引闭合哨兵计入，建议落 `docs/decisions/` 或该目录只放一份档并由主班代登索引）。逐枚文件：`sample_<n>_<id转义>.prompt.txt`（shim 或 `_call` 前的原文）、`.system.txt`、`.feedback.txt`（模型原话）；汇总 `run.jsonl` 一行一枚，字段固定：`{ts_local, ts_utc, head, sample_id, kind(串面|行面), expected_len, expected_sha8, confounded: false, model_role, responding_model, prompt_chars, system_chars, feedback_chars, echo_hit, echo_span, echo_rule_version}`（🔴 **不落 `expected` 明文**，只落 sha8＋长度，留痕件本身不该再复制一遍答案）。🔴 **id 一律用 loader 全 id 形状 `lang/topic/slug`**——不要照抄 `tests/fixtures/rubric_golden/golden_set.yaml` 的 `problem_id`（该 20 条 fixture 的 `agent_07_01` 之类在 loader 口径下**0/20 可解**，本班实测）。 |
| 判定口径（随 E5 一起冻结） | `echo_hit`＝feedback 正文含 `expected` 的**逐字连续子串**，命中长度 ≥ `max(4, ceil(0.5 × len(expected.strip())))`；行面题改比 `str(expected_rows)` 的 repr 片段或 ≥2 个单元格原样串；数值型短串额外要求上下文含"期望/输出/应该/正确"词面或直接引用格式，否则记 `echo_hit: ambiguous`（**口径必须先写死再看结果**，防事后解释）。判定脚本零 LLM、纯字符串，可对 `run.jsonl` 独立复算。 |
| 结果解释矩阵 | 0/5 命中 ⇒ "机制在、行为未见"（仍不推翻案甲，因禁令是单调降暴露）；1/5 ⇒ 弱信号，扩样本到 15 再判；≥2/5 ⇒ 支持立刻补禁令并在 `_post_check` 加"含期望值则改写"的机器闸（`:276` 是现成挂点）。🔴 三档全部只给"下一步该谁拍"，本班不改 `_post_check`。 |

---

## 四、③ 两案推荐（写成给人拍的判断题）

| | 案甲｜**先补禁令**（零成本，先动手） | 案乙｜**先验证**（N=5 真调用，后动手） |
|---|---|---|
| 动作 | 把 `:176` 那句提为三档共用硬要求（写进 `_SYSTEM_PROMPT_STRICT`／`BEGINNER_PASS`），可选配 `_post_check:276` 的机器闸 | 按 §三 阶段 1 跑 5 枚，先看回显存在不存在 |
| 成本 | 文案 ~1 行；**实测不会让测试红**（`test_ai_review_strategy.py:12-45` 是自比对）；需 bump `PROMPT_VERSIONS.code_review_*`（v2.0→v2.1，仓内惯例） | 极小费用（E4 量级）＋一次授权流程＋留痕归档；**真正贵的是"要不要放行外部请求"这条决策** |
| 可逆性 | 高（一处文案，git 可回；但 `attempts` 里的旧点评不回翻——现状点评也不入库文本，只有 `learning_events`/`attempts.feedback` 摘要面） | 不涉及回滚 |
| 未知 | 不知道禁令**有没有效**（提示层承诺，无实测支撑）；且 STRICT 档有「总长 200-300 字／4 段」硬预算，加一条要求可能挤压正文质量 | 5 枚的**统计外推力≈0**（只能证存在性）；样本框只有 36 道可归因，其余 72 道"本来就公开"这一事实不会因验证而变 |
| 风险 | 🔴 若人工认定"AI 复述期望输出＝教学价值（帮学生对答案）"，案甲就是**改产品行为**，且是把 §2 那条"三档同源送答案"的现状悄悄改掉 | 案乙不改任何东西，但会留下"已授权发外部请求"的先例与凭据使用面（凭据内容本班不碰、不读、不打印） |
| **本班推荐** | ✅ **案甲＋阶段 0 同批做**（禁令单调降低暴露面、可逆、零运行时依赖；阶段 0 零调用即可把"答案确实在送入内容里"从读码升级为运行时留痕） | ⏸ 暂缓到案甲落地后再拍："还要不要花真调用去量回显率"——因为**验不验都不改变"该不该防"的结论**，机制已在代码层坐实 |

🔴 **裁决轴只有一条，交给人工**：**"AI 把期望输出复述给学生"在本仓是缺陷还是产品功能？** 判"缺陷" ⇒ 直接走案甲，验证可省。判"功能" ⇒ 必须先案乙（否则禁令会把一个功能禁掉）。本班按卷宗要求**不选边**，且两案都不动判分口径与题面。

---

## 五、④ 零改动自证 ＋ 复算入口

- **git 面**：本班新增件仅 `docs/insights/l927-20-similar-design.md`／`l927-21-ai-echo-risk.md`（本档）／`l927-22-handoff.md`；`core/`、`content/`、`tests/`、`ui/`、`scripts/` **零 diff**；未 add/commit/checkout/restore/stash/clean。
- **零调用/零联网主证**：本班**唯一**触碰 LLM 面的动作是 `from core import ai_review` 读常量（`_SYSTEM_PROMPT_STRICT` 长度、`PROMPT_VERSIONS`、两条 chain 常量）；**未调用** `review/_call/_call_chain/grade_open_answer`，未设 `LLM_SCRIPT`，未执行 `D:/code/scripts/llm_call.py`（仅 `os.path.exists` → True）。
- **生产库**：`data/progress.db` **未打开**；开工 18:32:42 与收工取值均为 **122,880 B ／ sha8 `cd2dbce4`**（在册基线同值，mtime 恒 `2026-09-25 20:49:09`）。
- **探针**（班名目录，全部只读脚本；本档点名它们当复算入口 ⇒ 有意保留不清）：
  `D:\code\tmp\qoder-executor-20260927-1850-learn48\`＝`probe_similar.py`＋`similar_out.json`（l927-20）、`probe_face.py`＋`face_out.json`、`probe_face2.py`、`probe_samples.py`（本档）。
  ```
  $ cd D:/code/learning-system && PYTHONIOENCODING=utf-8 python .../probe_face.py      # rc=0：difficulty 分布 / 148 / 40 ai_open / 108 / 60 open 面 / 候选 id 与 prompt 字符数
  $ cd D:/code/learning-system && PYTHONIOENCODING=utf-8 python .../probe_face2.py     # rc=0：108 = 串面 88 + 行面 20；混淆 72（短串 28 / ≥6 字符 37）；可归因 36（≥4 字符 33）；BEGINNER 可归因 42
  $ cd D:/code/learning-system && PYTHONIOENCODING=utf-8 python -c "from core import ai_review as a; print(len(a._SYSTEM_PROMPT_STRICT), len(a._SYSTEM_PROMPT_BEGINNER_PASS), a.PROMPT_VERSIONS['code_review_strict'])"   # 683 / … / v2.0
  $ cd D:/code/learning-system && grep -n "期望输出" core/ai_review.py                  # 256（唯一注入处）
  $ cd D:/code/learning-system && grep -n "不直接给完整答案" core/ai_review.py          # 176（全模块唯一禁令命中）
  ```
- **未跑 pytest**：零码改动、判据不需测试数；并发窗禁跑全量（同刻 `colony41`／`quant49`／`psy77`／`kaoyan78` 在别仓）。§2 那句"改 prompt 不会让测试红"是**读码结论**（自比对），落地时请由执行班取实际 rc。
- **insights 索引**：未代登（真哨兵 `tests/test_insights_index_closure.py`；写本档前磁盘 98＝收录 98）。

---

## 六、遗留与登记

1. 🔴 **"148" 这个在册读数今后应带边界使用**：它是"走 STRICT 档的题数"，不是"prompt 含答案的题数"（108），也不是"可归因池"（36）。上游 154241 的表述（"风险面 148 题"）在**档位归属**上成立、在**暴露机制**上偏大且在 BEGINNER 侧偏小——本档已按层给出四个数并各附口径，未改任何在册档。
2. **阶段 0 的 shim 未实现**（本班零码改动，包括 `tmp/` 外的任何脚本都不落仓）：放行时若要做，最小形状＝一个 20 行的 `argparse` 脚本打印并落盘 `--prompt/--system` 后 `sys.exit(1)`，放班名目录，**不放仓内**。
3. **`_post_check` 机器闸的副作用未评估**：它现在只在 `difficulty≤2 且 passed` 时动作（`:278`），要加"含期望值则改写"会第一次让"未通过＋高难度"路径也进后处理 ⇒ 属行为变更，需与案甲一起拍，本档只登记这一处形状差异。
4. **开放题面（60 道）的回显口径与本案不同**：那条 prompt 送的是 `reference_answer`（本就设计成"给学生看的答案"，UI 揭示面在 `ui/pages/language.py:376-378` 折叠＋"写完再看"，见 154241 揭示面读数）⇒ **本方案的样本框刻意排除它**；若人工认为"参考答案被复述"也要查，需要单开一单并先定"参考答案的揭示承诺"。
5. **72 道"期望值 ⊂ 题面"的混淆面里，28 道只因期望值 ≤3 字符**（子串巧合），本班未逐道人工排除；若要把可归因池从 36 上修到最多 64，需要人工读这 28 道（脚本已给 id 前 8 枚）。
6. 本档交班后 `tests/test_insights_index_closure.py` 会红（missing＝本班三档）＝主班的账，本班未消。
