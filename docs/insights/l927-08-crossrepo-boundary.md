---
id: l927-08-crossrepo-boundary
title: learning ↔ kaoyan 英语功能分工边界核查（跨仓契约，只读扫描）
task: l927-08（zcode-bridge 波次 20，工作类型 docs，风险档 B）
shift: qoder-executor-20260927-1440-learn45
written: 2026-09-27T14:47
head_at_write: learning-system c71c6f0 ／ kaoyan-system 4f6d1fd
mode: 两仓**全程只读**（grep/find/sed -n/git log/git status 与 `find -newermt` 现取；kaoyan 侧零写、零测试执行、零 npm/tsx）
status: 结论＝**英语功能面分工清晰（learning 侧该面不存在）**；**通用学习机制面两仓各建一套**＝重复建设候选，属跨仓裁决域 ⇒ 只出待裁条目不动盘
supersedes_or_extends: 承接 `docs/decisions/2026-06-17-review-cross-system-learning.md`（四系统定位表）与 `docs/decisions/2026-09-09-impl-english-review-expansion.md`（英语四阶段全部落 kaoyan）；为 E08 的**语义补充件**（E08 自身声明不证跨仓语义等价）
---

# learning English 阅读模块与 kaoyan 侧的分工边界核查

> 卷宗完成标准：①扫描命令与输出 ②重叠清单 ③结论 ④零码改动。判据命中 **4/4**。

## 〇、一句话结论

1. **卷宗前提「learning English 阅读模块」不成立**——learning-system 里英语面**从建仓起就不存在**：
   `find learning-system -ipath "*english*"` ＝ **0 个文件**；`git log --all --pretty=format: --name-only | sort -u | grep -i english` ＝ **0 条历史路径**（不是"被删了"，是从未有）。
   盘上 13 行 `english/英语` 命中（7 个文件，**全在 content 课面，代码侧 0**）**全是巧合命中**：R tidyr 课把 `english` 当**列名**（`content/r/08_tidyr/{01,02,04,05}.yaml` ＋ `_lesson.md`）、Python NLP 课 `stop_words="english"`（`content/python/15_ab_text/_lesson.md:107`）、以及"语法接近自然英语"这类散文（`content/python/01_hello_and_vars/_lesson.md:5`）。
2. 英语阅读功能**整体在 kaoyan-system**：`src/{app/api/english,app/english,modules/english,components/study/english}` 共 **44 个 TS/TSX 文件 / 8,139 行**，测试面 `tests/*(english|reading|vocab)*` **40 个文件**。卷宗锚点「k43a/k44a 在 kaoyan 侧合并」**在世且属实**（两份 result 在 `zcode-bridge/done/`，均 status done）。
3. **两仓互不引用**：全仓 explicit 路径引用 learning→kaoyan **0 条**、kaoyan→learning **1 条且是注释里的"文风引用"**（`kaoyan-system/tests/corpus-index-invariant.test.ts:193` 提到"同 learning-system 的比例式判据风格"，**不是路径依赖**）。历史 E08 扫描同样给出 learning↔kaoyan 互引断链 **0**。
4. ⇒ **就"英语阅读"这个功能面：分工清晰，零重复建设。**
5. ⇒ **但把问题从"功能名"挪到"机制"就有真账**：两仓各有一整套间隔重复／错题本／AI 判分／AI 出题——最尖锐的一处是 **SM-2 参数在两份 schema 里各写一遍且默认值不同**（kaoyan `srs_cards.ease_factor REAL DEFAULT 2.5` ＋ `interval_days REAL DEFAULT 1` vs learning `review_state.ease REAL DEFAULT 2.0` ＋ `interval_days INTEGER DEFAULT 3`）。**这是"重复建设"结论的真实落点，且它不属于英语面**；合并或分工属跨仓裁决 ⇒ 见 §五 待裁条目，本单不动盘。

---

## 一、判据①：扫描命令与命中（逐条可复跑）

### 1.1 为什么没跑 `focus_audit.py cross-repo`（E08），以及"等价"做到了什么程度

卷宗写「跑 focus_audit cross-repo（**或等价 rg**）」。本单走等价 rg，两条理由都落在档上：

| 理由 | 证据 |
|---|---|
| E08 **写盘**，且写位属信箱产物域 | `zcode-bridge/scripts/focus_audit.py:41-48` `finish()` 以 `out_path.open("w")` 写 `E08.jsonl` ＋ `E08.run.jsonl`；`docs/night-plans/FOCUS-MAP.md:220` 登记的产出契约就是 `$out/E08.jsonl`。brief §1 把 `zcode-bridge/scripts/*.py` 与其产物列为主班独占 |
| E08 **答不了本题** | `focus_audit.py:222-223` 自述「只扫『明确路径引用』的存在性，断链才出 finding；**本轮不做语义等价证明**」；`FOCUS-MAP.md:226` 同句重申 ⇒ 本单的"重复建设/分工清晰"是**语义**判断，E08 按其自身定义不产出该结论 |

⇒ 折中：**读**上一次 E08 历史产物做对照（只读 `zcode-bridge/tmp/focus/20260917-2300/E08.*`），并自己跑等价的"显式路径引用存在性"检查（§1.4）。历史件读数：`files_scanned 3117 / refs_ok 1930 / refs_broken 1062`，但 `skipped` 含 **`file cap 500 at kaoyan-system`** ⇒ 该件对 kaoyan 覆盖**不全**，本单的 rg 全仓扫描反而更完整（下述排除集）。

### 1.2 learning 侧英语面普查（结果：0）

```bash
cd D:/code
# ① 现存路径：0 个
find learning-system -ipath "*english*" -not -path "*/.venv/*" -not -path "*/.git/*" | wc -l        → 0
# ② 历史路径：0 条（从未有过，非"已删除"）
cd learning-system && git log --all --pretty=format: --name-only | sort -u | grep -i "english\|英语" → 空
git log --all --diff-filter=D --name-only | grep -i english                                          → 空
# ③ 文本命中（-i english|英语，范围＝content core ui scripts tests app.py README.md plan.md，排除 docs/）
#    ＝ 13 行 / 7 个文件，且 7 枚全在 content 课面（core/ui/scripts/tests/app.py **0 命中**）：
#    content/r/08_tidyr/{01_pivot_longer,02_pivot_wider,04_long_groupby,05_starts_with}.yaml ＋ r/08_tidyr/_lesson.md → 列名
#    content/python/15_ab_text/_lesson.md:107                                              → stop_words="english"
#    content/python/01_hello_and_vars/_lesson.md:5                                         → 「语法接近自然英语」
# ④ 页面面：ui/pages/ 只有 dashboard/diagnostic/home/language/mistakes/path —— 无英语页
# ⑤ 定位档：plan.md 全文无「英语」；唯一"阅读"命中是 :25「适合长时间阅读」（排版口径）
```

**learning-system 的语言轴恰 5 值**：`python / sql / cpp / r / agent_dev`（`ui/components.py:LANG_META` 为唯一权威，见 `learn-tag-vocab-spec-20260925.md` §2.1）⇒ 要加"英语"得先动语言轴，而语言轴**不是题库侧可自便的**（有 7 处手写副本在册）。

### 1.3 kaoyan 侧英语面普查（结果：44 文件 / 8,139 行）

```bash
cd D:/code/kaoyan-system
find src -ipath "*english*" -type f \( -name "*.ts" -o -name "*.tsx" \) | wc -l        → 44
find src -ipath "*english*" -type f \( -name "*.ts" -o -name "*.tsx" \) -exec cat {} + | wc -l → 8139
ls tests | grep -icE "english|reading|vocab"                                            → 40
grep -rli "english" src --include=*.ts --include=*.tsx | wc -l                          → 91   （引用面，非实体面）
```

实体面骨架（`find src -ipath "*english*"` 摘录）：

| 层 | 代表件 |
|---|---|
| 路由/页面 | `src/app/english/page.tsx`、`src/app/api/english/route.ts` |
| 组件（10 枚） | `ReadingPractice.tsx`、`EnglishIntensiveReading.tsx`、`EnglishRereadQueue.tsx`、`EnglishRecitation.tsx`、`SectionPractice.tsx`、`SentenceTypingDrill.tsx`、`VocabReview.tsx`、`WritingPractice.tsx`、`types.ts` |
| application | `english-handlers.ts`(88,601 B)、`passage-translation-service.ts`、`reading-attempt-summary.ts`、`reread-queue.ts`、`vocab-{frequency,progress,review-evidence,schedule,syllabus}.ts`、`rating-corrections.ts` |
| domain | `english1-policy.ts`、`reading-routine-task.ts`(在 planning)、`vocab-dictation.ts`、`async-feedback.ts`、`exam-explanation-quality.ts` |

### 1.4 跨仓引用双向检查（E08 等价，只读）

```bash
cd D:/code
grep -rn "learning-system" kaoyan-system/src kaoyan-system/tests kaoyan-system/docs kaoyan-system/package.json
  → 1 命中：kaoyan-system/tests/corpus-index-invariant.test.ts:193（注释，指"判据风格"，非路径依赖）
grep -rn "kaoyan" learning-system/{core,ui,scripts,tests,plan.md,README.md}
  → 0 命中（docs/insights 内的命中全是信箱/兄弟班点名与班名，非代码耦合）
# 历史 E08 件交叉验证（只读）
python - <<'PY'   # 解析 zcode-bridge/tmp/focus/20260917-2300/E08.jsonl
learning<->kaoyan 互引断链：0      含 english 的断链：10（全在根仓 docs//zcode-bridge/ 与 kaoyan 脚本名，无一指 learning）
PY
```

### 1.5 定位档（谁该有什么，档上原话）

| 档 | 关键句 | 用法 |
|---|---|---|
| `docs/decisions/2026-06-17-review-cross-system-learning.md` | learning-system 定位＝「**编程学习判题**」，最强项＝多语言沙箱执行器/LLM fallback 链/SQLite 进度/YAML 题库分离/推荐引擎 | 边界**权威源**：learning 的能力面从来是"判题管道"，不是"学科内容" |
| `docs/decisions/2026-06-14-impl-learning-platform-demo.md:85-95` | 重定位＝「面向非计算机背景 HR 的能力升级平台，两条能力线」；语言轴＝Python/SQL/R/C++/Agent | 同上（无英语学科位） |
| `docs/decisions/2026-09-09-impl-english-review-expansion.md` | 英语四阶段（TTS 听写/完形/新题型/背诵）落地文件**全部是 `src/.../english/*`** | 英语演进的**唯一去向**＝kaoyan |
| `zcode-bridge/done/20260909-120705-k43a.result.md`、`...120706-k44a.result.md` | 「英语阅读间隔复读」合并进「每日英语阅读」单任务；kaoyan 侧 `planner.ts`/`reading-routine-task.ts`/`english-handlers.ts`/`ReadingPractice.tsx`；k44a 独立验收**发现并修一处真回归**（`797fa6e`） | 卷宗锚点**在世**；合并后的形状是 kaoyan 单任务 `english-<date>-99` |

---

## 二、判据②：重叠清单

### 2.1 英语功能面：**空集**

| 潜在重叠项 | learning 现值 | kaoyan 现值 | 判定 |
|---|---|---|---|
| 英语题库/篇章 | 0 件（语言轴 5 值里无 english） | `src/modules/english/**` 44 文件 | **无重叠** |
| 阅读练习 UI | 无页面 | `ReadingPractice.tsx` 等 10 组件 | **无重叠** |
| 词汇/SRS 词表 | 无 | `vocab-{schedule,syllabus,frequency,progress,review-evidence}.ts` | **无重叠** |
| 题型（完形/新题型/默写/听写） | 无 | 四阶段全部落 kaoyan（09-09 决策档） | **无重叠** |
| 跨仓引用 | 0 | 1 条注释（非依赖） | **无耦合** |

### 2.2 通用学习机制面：**同名不同栈，各一套**（本单唯一有重量的发现）

| 机制 | learning-system（Python/Streamlit/SQLite） | kaoyan-system（TS/Next.js/SQLite） | 参数是否一致 |
|---|---|---|---|
| **间隔重复（SM-2 家族）** | `core/progress.py:91-101` 表 `review_state(lang, problem_id, interval_days INTEGER DEFAULT 3, ease REAL DEFAULT 2.0, review_streak, next_due_date, last_result)`；更新式 `:388 update_review_state` → `interval = min(interval*ease, 30)`，失败 `ease -= 0.1 / -0.2`、`interval = 1` | `src/infrastructure/db/migrations/schema.ts:427-449` 表 `srs_cards(... ease_factor REAL DEFAULT 2.5, interval_days REAL DEFAULT 1, next_review_date, review_count, correct_streak, card_type, source_question_id …)`；调度 `english/application/vocab-schedule.ts`、`review/domain/due-date-balance.ts`（只平移落点不改间隔）、`learning/domain/{srs-channels,wrong-question-srs-intake}.ts` | ❌ **ease 2.0 vs 2.5、首间隔 3 vs 1、列型 INTEGER vs REAL、键名 `ease` vs `ease_factor`、`next_due_date` vs `next_review_date` 全不同** |
| 错题本 | `core/progress.py:227 list_mistakes`、`ui/pages/mistakes.py`(201 行) | `learning/application/wrong-questions*.ts`、`wrong-question-srs-{intake,pause}.ts`、`learning/domain/wrong-item-remediation.ts` | ❌ 两套模型（按 `problem_id` 状态位 vs 按 `knowledge_point_id` 卡片） |
| AI 判分/评分表 | `core/judge.py`(358)、`core/ai_review.py`(546)、`core/rubric_dims.py`(40)、表 `rubric_scores` | `english/application/rating-corrections.ts`、`english/domain/exam-explanation-quality.ts`、`modules/assessment/**` | ❌ 两套（rubric 维度 vs 评分修正回路） |
| AI 出题/变式 | `core/ai_generate.py`(106)，题 id 前缀 `AI_VARIANT::`（**从不落库**，规范档 §2.5 已证） | `learning/domain/ai-generated-practice.ts`、`ai-jobs*.ts`（走任务队列） | ❌ 两套，且落库语义相反（learning 不落库／kaoyan 有 job 表） |
| 学习事件 | 表 `attempts`/`learning_events`（`learn-eventtypes-census-20260923.md` 在册 10 写点） | `learning/application/observation-events.ts`、`record-{learning,objective}-attempt.ts` | ❌ 两套 schema |

体量对照（只作"哪侧承重"的读数，不作优劣判断）：learning 上述机制 6 件 **1,927 行**；kaoyan 仅英语路径就已 **8,139 行**、机制面另在 `modules/{learning,review,assessment,content}` 四模块。

---

## 三、判据③：结论

1. **就卷宗问的那件事（英语阅读功能）——分工清晰，不是重复建设。** 依据：learning 侧该面**实体为 0、历史为 0、页面为 0、语言轴无位**；kaoyan 侧 44 文件成建制且有决策档与两封 result 链；双向无路径耦合。
2. **"重复建设"这个标签在跨仓上成立，但落点不是英语**：间隔重复／错题／AI 判分／AI 出题这四项**通用机制在两仓各有一套不兼容实现**（§2.2 参数表）。
   要不要收敛，取决于一个**本单无权回答**的问题：这两套是"同一产品的两份实现"还是"两个不同用户场景的各自实现"。档上现有答案是后者——`2026-06-17` 评审定的口径是 **adopt-not-centralize（借鉴而不集中）**，且明确 learning 的强项是"判题管道"、可被别人借，**不是**要合并成一个服务。
   ⇒ 因此本单结论写成：**「英语功能面分工清晰；机制面重复是**已知设计选择**，但 SM-2 参数分叉无档可查」**——参数分叉那一条是**新事实**，值得入册（§五 X-2）。
3. **卷宗前提需订正**：把这张单再发给任何班时，"learning English 阅读模块"应改为"kaoyan English 阅读模块（learning 侧无对应物，本题实为『learning 有没有悄悄长出一份英语面』的排除性核查）"。核查结果＝**没有**。

---

## 四、判据④：零码改动／零写入 kaoyan 自证

| 项 | 现值 |
|---|---|
| learning-system `git status --porcelain`（收工） | **3 行**：`?? docs/insights/l927-06-sampling.md`／`l927-07-dashboard-regression.md`／`l927-08-crossrepo-boundary.md` ＝ 本班三张点名产物，代码零改动 |
| kaoyan-system 是否被本单写过 | **否**。命令集只有 `find / grep / sed -n / ls / wc / git status / git rev-parse / git log`；无 `npm`、无 `tsx`、无重定向写入、无编辑器写 |
| kaoyan 时间窗反证 | `find . -type f -newermt "2026-09-27 14:39" -not -path "./node_modules/*" -not -path "./.git/*" -not -path "./.next/*"` ＝ **空输出**（本单认领时刻 14:39，扫描期间 kaoyan 全仓无任何文件 mtime 变动，含兄弟班 `kaoyan75` 亦未落笔） |
| kaoyan 现点读数（仅记录，不判） | `git status --porcelain` **35 行**、HEAD `4f6d1fd`（⚠ brief §5 表写 `ab2358b`／32 行，均已前进＝兄弟班在途，本单未触碰） |
| learning `data/progress.db` | 本单**完全未打开**该库（无 DAO、无 sqlite3 连接），sha8 沿用同班 l927-06 的 `cd2dbce4` 现值 |
| 未跑 | `focus_audit.py cross-repo`（理由见 §1.1）、任何一仓测试、任何 SQL、任何 git 写操作 |

---

## 五、边界建议＝待裁条目（本单一律不自定、不动盘）

| # | 条目 | 现状证据 | 要裁什么 | 最小改动面（若放行） | 回滚成本 |
|---|---|---|---|---|---|
| X-1 | 派单/登记口径：删掉「learning English 阅读模块」这一不存在的前提 | 本档 §1.2 四条命令全 0 | 主班在派单表/BACKLOG 里把该描述改成「kaoyan 英语阅读面（learning 无对应物）」 | 纯文档一行 | 零 |
| X-2 | **SM-2 参数分叉是否入册为在册事实**（ease 2.0 vs 2.5、首间隔 3 vs 1、REAL/INTEGER、键名两套） | §2.2 表；`core/progress.py:91-101,388-409` vs `schema.ts:427-449` | 裁"两仓两算法是设计选择、需登记为契约"还是"需收敛到一套" | 若只登记：根仓 `docs/decisions/` 加一节（写侧）；若要收敛：跨栈改调度＝**大改，另开写单**且触红线（学习数据） | 登记＝零；收敛＝高（涉及 `srs_cards` 历史行与 `review_state` 语义） |
| X-3 | 是否给 learning **钉一句范围声明**（"本仓不含英语/学科内容，学科内容一律落 kaoyan"）写进 `learning-system/plan.md` 或 README | 现无该声明（`plan.md` 全文无"英语"） | 裁要不要写、写哪份 | 文档 2 行 | 零 |
| X-4 | 若将来真要 learning 承载"非编程学科题"，**语言轴是硬门**（7 处手写副本、无受控词表门禁、`load_language` 不做白名单校验且 NTFS 大小写不敏感可长出 `English/` 影子题号空间） | `learn-tag-vocab-spec-20260925.md` §2.1 实测缺口（含 `load_language('Python') -> topics=27`） | 裁"先补白名单校验再谈扩学科"还是"学科一律不进 learning" | 白名单校验属代码改动（另开单，触 loader） | 中 |
| X-5 | E08 覆盖缺口：`file cap 500 at kaoyan-system`（历史 run 自述 skipped） | `zcode-bridge/tmp/focus/20260917-2300/E08.run.json` | 裁是否放宽上限；这是**信箱层脚本**改动＝主班域，本单不动 | 改 `focus-sources.json:limits.max_records`／`focus_audit.py` 上限（人工闸） | 低 |

> 上表五条**没有一条在本单被执行**。X-2 是唯一"新事实"，其余四条是"知情项/口径项"。
