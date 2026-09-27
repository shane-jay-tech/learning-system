---
id: l927-06-sampling
title: 题库格式与知识点（topic）标签一致性 10 条种子抽检（seed=20260927）＋去重链后重复形态复查
task: l927-06（zcode-bridge 波次 20，工作类型 docs，风险档 B）
shift: qoder-executor-20260927-1440-learn45
written: 2026-09-27T14:31
head_at_write: c71c6f0
mode: 全程只读（content/ 零 diff；data/progress.db 只用 `mode=ro` URI 探针＋当场试写求 SQLITE_READONLY；探针脚本落 gitignore 区外的 D:/code/tmp/<班名>/，仓内零临时件）
status: 抽样报告——判据①~④全中；样本内 0 例格式/标签缺陷，2 例命中在册重复标签组（均为规范拼法）；不外推整库
supersedes_or_extends: extends `docs/insights/learn-tag-vocab-spec-20260925.md`（五轴规范与词表基线）与 `learn-content-tags-census-20260924.md`；本档是"规范落地后的一次种子抽验"，不新增规范条款
---

# 题库格式与 kp 标签一致性抽检（10 条种子抽样）

> 卷宗完成标准：①五要素齐 ②10 题逐条结论 ③异常清单（如有）④零写库。
> 本档只做**格式与标签一致性**核验，**不核题面数值/统计口径的正确性**（效应量、混淆矩阵、中介效应三题落在红线域「统计数值结论」，见 §六 主动收窄）。

## 〇、一句话结论

1. 抽到的 **10 题全部通过**在册五轴规范（必填字段齐、`topic` 逐字等于目录名、`judge_mode` 合法、载荷键组合归属 5 类形态之一、tags 全在词表基线内）⇒ **样本层零缺陷**。
2. **`options` / 选项结构在本仓 schema 里不存在**——卷宗写的「选项结构」这一项**否证**：`content/**/*.yaml` 顶层键全集里无 `options/choices/answer/a/b/c/d`，「题型」的实况载体是 `judge_mode`（`{run, ai_open}` 两值）。⇒ 本档把该项**收窄为"载荷键组合结构核验"**（题干 5 类形态，见 §三 F5）。
3. **词表基线未漂移**：`learn-tag-vocab-spec-20260925.md` 的指纹 `bfbf832d88a75f3d`／`unique=416 occ=898 singletons=265 重复组=7 严格大小写变体=0` 在 HEAD `c71c6f0` **逐位复现** ⇒ 该档 9-25 至今规范面零变化，本抽样的"未知标签"判据可直接沿用。
4. **9-05 去重链在盘上无残留**：`content/r/14_sem_basics/` 现存 4 件（01~04），被删的 `05_fit_indices.yaml`（题名「解读模型拟合指标」）**全库题名命中 0**，且真库 4 张带 `problem_id` 的表里该题号 **0 行**。
5. 唯一值得交人工的**不是缺陷**而是形态确认：样本里 2 题命中在册重复标签组（D4 `effect-size`／D7 `line`），两题用的都是规范档**推荐保留**的拼法，另一写法（`effectsize` 2 次、`lines` 1 次）在别处并存 ⇒ 属 R-01/R-02 迁移规则的既有账，**本次不新增**。

---

## 一、五要素（抽样口径，逐条可复算）

| 要素 | 内容 |
|---|---|
| **① 总体** | `content/**/*.yaml` 409 件中顶层为 mapping 且含 `statement` 键者 ＝ **403 题**（另 6 件是 `content/paths/*.yaml` 路径定义件，含 `milestones`，**本就不是题**，不入总体）。分语言：python 125 / r 84 / agent_dev 78 / cpp 62 / sql 54 ＝ 403（与 `core/loader.py` 按目录枚举的口径独立对平）。 |
| **② 规则** | 简单随机不放回抽样，**无分层**：`random.Random(20260927).sample(sorted(相对路径), 10)`。排序键＝`content/<lang>/<topic>/<file>.yaml` 的相对路径字典序（Windows 路径统一转正斜杠，故跨机可复现）。 |
| **③ seed** | `20260927`（卷宗指定，未改）。 |
| **④ 样本 ID** | 见 §二表头 10 行（`lang/topic/file` 三段式＝`Problem.id`）。 |
| **⑤ 局限** | **(a) n=10 / 403 ＝ 2.5%**，且是**无分层**抽样：总体 4/5 档题共 17 件（4.2%），本次抽到 1 件（`python/22_hr_model/03_confusion_matrix`，4 档）——**样本难度分布不可当总体分布读**，任何"整库 0 缺陷"结论都不成立。<br>**(b)** cpp/sql 各仅 1 件入样，`setup_sql`+`expected_rows` 形态只被 1 条覆盖（且该条恰为 cpp run 题，未覆盖 SQL 分支）⇒ SQL 载荷判据在样本里**未被检验**。<br>**(c)** tags 受控词表不存在（规范档 §三.3 已判"未知标签今天无从判起"），本档"未知"＝**不在基线 416 值集合内**，只具操作性不具语义性。<br>**(d)** 抽样对象是**题面文件**，非"用户实际做过的题"：真库 `attempts` 仅 15 行／`problems_status` 14 行，样本 10 题的库内足迹**全 0** ⇒ 本抽样不代表真实使用分布（见 §五）。 |

**复现命令**（仓库根 `D:/code/learning-system`，全程只读）：

```bash
# 词表基线＋难度/题型分布（无 core 依赖，只读 yaml）
PYTHONIOENCODING=utf-8 python - <<'PY'
import hashlib, io, re, yaml
from collections import Counter, defaultdict
from pathlib import Path
rows=[(p,yaml.safe_load(io.open(p,encoding="utf-8").read())) for p in sorted(Path("content").rglob("*.yaml"))]
prob=[(p,d) for p,d in rows if isinstance(d,dict) and "statement" in d]
tags=Counter(str(x) for _,d in prob for x in (d.get("tags") or []))
uni=sorted(tags)
print("yaml=%d 题=%d 路径件=%d unique=%d occ=%d singletons=%d 基线sha=%s"%(
  len(rows),len(prob),sum(1 for _,d in rows if isinstance(d,dict) and "milestones" in d),
  len(uni),sum(tags.values()),sum(1 for v in tags.values() if v==1),
  hashlib.sha256("\n".join(uni).encode()).hexdigest()[:16]))
print("difficulty=",dict(sorted(Counter(d.get("difficulty") for _,d in prob).items())))
print("judge_mode=",dict(Counter(str(d.get("judge_mode")) for _,d in prob)))
PY
```

抽样本体（10 条逐字段核验＋全库重复形态直扫）的**最小可复现版**（下面这段与本班跑过的完整版给出**同一 10 个 ID、同一 7/0/0 三读数**；完整版另出 F1~F6 逐题判据 JSON）：

```bash
# 仓库根执行，全程只读、零 DB 句柄（收班后班目录 tmp/<班名>/ 会清空，故把配方留在本档）
PYTHONIOENCODING=utf-8 python - <<'PY'
import random, re, yaml, hashlib, io
from collections import defaultdict
from pathlib import Path
def norm(s): return re.sub(r"\s+"," ",(s or "").strip()).lower()
paths=sorted(str(p.relative_to(Path("."))).replace("\\","/")          # 总体口径＝含 statement 的 yaml
             for p in Path("content").rglob("*.yaml")
             if p.parent.parent.name!="paths"
             and "statement" in (yaml.safe_load(io.open(p,encoding="utf-8").read()) or {}))
pick=random.Random(20260927).sample(paths,10)                          # ← seed 固定，字典序入池
print("总体=",len(paths)); [print("  ",x) for x in pick]
title=defaultdict(list); head=defaultdict(list); full=defaultdict(list) # 重复形态三判据
for rel in paths:
    d=yaml.safe_load(io.open(rel,encoding="utf-8").read())
    pid=rel[len("content/"):-5]; t=norm(d.get("title")); s=norm(d.get("statement"))
    title[t].append(pid); head[s[:60]].append(pid)
    full[hashlib.sha256(s.encode()).hexdigest()[:12]].append(pid)
print("同题名组=",sum(1 for v in title.values() if len(v)>1),
      "题面前60字组=",sum(1 for v in head.values() if len(v)>1),
      "题面全文组=",sum(1 for v in full.values() if len(v)>1))
PY
```

**2026-09-27T14:2x @ HEAD `c71c6f0` 实测**：`总体=403`／10 个 ID 见 §二表／`同题名组=7 题面前60字组=0 题面全文组=0`。
库侧只读探针（§五）另用 `sqlite3.connect(f"file:{DB}?mode=ro", uri=True)` ＋ 当场 `CREATE TABLE` 求 `SQLITE_READONLY`，一条 `python -c` 可复跑。

---

## 二、10 题逐条结论

| # | 样本 ID（=Problem.id） | 题面 sha8 / B | difficulty | judge_mode | tags | 格式 F1~F4 | kp(topic) F5 | 结论 |
|---|---|---|---|---|---|---|---|---|
| 1 | `cpp/10_templates/03_pair` | `4b62db8a` / 1018 | 2 ✓ | 缺省→run ✓ | template, two-params | ✓ `expected_output`+`tests`+`starter_code` | `10_templates`==目录 ✓ | **通过**（run/多用例形态） |
| 2 | `python/21_hr_viz/04_scatter_age_salary` | `89ae92e5` / 1389 | 2 ✓ | ai_open ✓ | matplotlib, scatter, **hr** | ✓ `rubric`+`reference_answer` | `21_hr_viz`==目录 ✓ | **通过**；`hr` 属规范档 §2.5「来源味标记越权使用」既有账（13 次之一） |
| 3 | `python/06_strings/01_to_upper` | `754c9291` / 482 | 1 ✓ | 缺省→run ✓ | upper | ✓ `expected_output`+`tests` | `06_strings`==目录 ✓ | **通过**（run/多用例） |
| 4 | `agent_dev/11_real_tasks/02_write_bug_report` | `5edb8cc4` / 2219 | 2 ✓ | ai_open ✓ | spec, debug, **real-task** | ✓ `rubric`+`reference_answer` | `11_real_tasks`==目录 ✓ | **通过**；`real-task` 同为来源味标记（8 次之一） |
| 5 | `agent_dev/07_data_security/03_anon_vs_pseudo` | `46425fa8` / 2105 | 3 ✓ | ai_open ✓ | security, anonymization, **open**, **ai_judge** | ✓ `rubric`+`reference_answer` | `07_data_security`==目录 ✓ | **通过**；⚠ `open`/`ai_judge` 两枚 tag 把 `judge_mode` 的事**抄进 tags** ⇒ 与规范档 §〇.3「同一件事被抄了几遍」同型，非新缺陷 |
| 6 | `agent_dev/07_write_spec/02_api_spec` | `be1ce322` / 1111 | 2 ✓ | ai_open ✓ | spec, api, **ai_judge** | ✓ `rubric`+`reference_answer` | `07_write_spec`==目录 ✓ | **通过**；同 #5（`ai_judge` 重复承载题型轴） |
| 7 | `python/22_hr_model/03_confusion_matrix` | `edbdc33f` / 1731 | 4 ✓ | ai_open ✓ | sklearn, metrics, **hr** | ✓ `rubric`+`reference_answer` | `22_hr_model`==目录 ✓ | **通过**（格式面）；**内容不核**——4 档＋混淆矩阵/召回率属统计口径，红线域主动收窄 |
| 8 | `python/15_ab_text/02_cohens_d` | `9d2d0ebd` / 680 | 3 ✓ | 缺省→run ✓ | **effect-size**, cohens-d | ✓ `expected_output` | `15_ab_text`==目录 ✓ | **通过**；`effect-size` 命中在册重复组 **D4**（并存 `effectsize`×2），样本用的是**推荐拼法**；**数值不核**（效应量＝红线域） |
| 9 | `python/11_matplotlib/01_line_max` | `953f73bb` / 567 | 1 ✓ | 缺省→run ✓ | plot, **line** | ✓ `expected_output` | `11_matplotlib`==目录 ✓ | **通过**；`line` 命中在册重复组 **D7**（并存 `lines`×1），用推荐拼法 |
| 10 | `r/16_mediation/05_explain_mediation` | `6a4fd63d` / 1803 | 1 ✓ | ai_open ✓ | mediation, interpretation, basics | ✓ `rubric`+`reference_answer`；**无 `starter_code`**——ai_open 允许（`audit_content.py:44` 条件豁免），全库缺该键者恰 4 件均为 ai_open | `16_mediation`==目录 ✓ | **通过**；内容不核（中介效应解释＝医疗/统计口径邻域，只读判格式） |

**逐条汇总**：10/10 通过；必填字段缺失 **0**、空值 **0**、未知顶层键 **0**、`topic≠目录名` **0**、`difficulty` 越界/非整 **0**、`judge_mode` 非法值 **0**、tags/hints 非 list 或含空串 **0**、条件载荷缺失 **0**。

---

## 三、核验规则（把卷宗判据改成可执行判据的过程）

| 判据 | 实现 | 依据 |
|---|---|---|
| F1 字段完整 | `title/topic/difficulty/tags/statement` 五键存在且 `str(v).strip()` 非空 | `core/loader.py` `_build_problem` 的必填面（缺键会回落默认值 ⇒ 回落即"标了个假值"，故按"键在且非空"判） |
| F2 无未知键 | 顶层键 ⊄ 已知 15 键集（`title/topic/difficulty/tags/statement/starter_code/expected_output/expected_rows/setup_sql/tests/hints/judge_mode/rubric/reference_answer`） | 键普查：`grep -rho "^[a-z_]*:" content --include=*.yaml` 命中 16 种，第 16 种是路径件的 `milestones/icon/subtitle/estimated_hours` |
| F3 结构 | `tags`/`hints` 必须是非空 `list[str]` 且元素 strip 非空；`difficulty` 是 `int` 且 1..5 | `core/loader.py` 的 `isinstance` 防御分支＋`scripts/audit_content.py:46` range 判据 |
| F4 条件载荷 | `run`：非 sql ⇒ `expected_output` 或 `tests` 至少一；sql ⇒ `setup_sql` 或 `expected_rows` 至少一。`ai_open` ⇒ `rubric`（`reference_answer` 记为**非硬判据**）。非 ai_open 缺 `starter_code` 记 warning | 与 `scripts/audit_content.py:42-57` 同判据（本档自实现，未调用该脚本，见 §四 F5 否证） |
| **F5「选项结构」否证 → 收窄** | 全库顶层键集合里**没有** `options/choices/answer/a-d` 任何一枚；题型轴实况载体＝`judge_mode`（显式 140 处：`run` 70／`ai_open` 70，另 263 件依赖缺省） | 规范档 §2.4；卷宗「选项结构」按**载荷键组合 5 类形态**核验：本 10 件全部落入 `expected_output(+tests)` / `rubric+reference_answer` 两类，无第 6 种组合 |
| F6 kp 标签一致性 | yaml `topic` 逐字 == 父目录名（`NN_name` 形态） | 规范档 §2.3「唯一权威＝目录名，yaml 是副本」；在册门禁 `scripts/audit_content_deep.py`（实测 403 件 0 漂移）——**本档独立复算 10 件同样 0 漂移** |

> ⚠ 未跑 `scripts/audit_content.py` / `audit_content_deep.py` 本体：`audit_content.py:21` 走 `from core.loader import load_language`、`audit_content_deep.py` 另有 `sqlite3.connect(":memory:")`。
> 二者大概率只读，但**本单判据④是"零写库"**，而本仓在册前科正是"看似只读的入口自开默认库"（§四），
> 故一律自实现纯 `open()` 读，不经任何 `core.*` import。这条取舍如实记为**未复用现成门禁**。

---

## 四、去重链后的重复形态复查（lrdp／commit `5d017f7`，2026-09-05）

锚点复核：卷宗写「历史 lrdp 去重链」，`rg -l lrdp` 在 `learning-system/` 内 **0 命中**——该前缀是**信箱任务号** `20260909-014509-lrdp`（`zcode-bridge/done/20260909-014509-lrdp.result.md`，按 brief §3a 到 `done/` 取到，**内容在世**）。其结论指向真身＝commit `5d017f7`「chore: dedupe fit-indices question, adjust content-count guard 400->399」。

| 项 | 现值 | 命令 |
|---|---|---|
| 被删题 | `content/r/14_sem_basics/05_fit_indices.yaml`（29 行，题名「解读模型拟合指标」） | `git show 5d017f7 --stat` |
| 该目录现存 yaml | 4 件：`01_sem_concept` `02_lavaan_syntax` `03_fit_indices` `04_path_diagram` ⇒ **05 无复活、无重号** | `ls content/r/14_sem_basics/*.yaml` |
| 被删题名在**全库**重现 | 归一化题名命中 **0 件**（既不与 `03_fit_indices` 同题面，也无别处副本） | 抽样脚本 `dup_scan()`：`same_title` 计数里"解读模型拟合指标"=0 |
| `ACCEPTED_TOPICS` 豁免位 | 含 `r/14_sem_basics`（去重致难度分布 >70% 同档，注释自述"预期结果而非质量问题"）——**在册知情项，不是缺陷** | `scripts/audit_content.py:15-17` |
| 计数护栏 | `tests/test_scripts.py` 的 `total_problems >= 399`（注释自述 9/5 刻意下调），实值 403 | `learn-achievements-migration-design-20260924.md:28` 已钉为知情项，**不收紧** |

**全库重复形态直扫**（这是**实测计数**，不是样本外推）：题面全文 sha256 撞车 **0 组**；题面归一前 60 字撞车 **0 组**；题名（归一）撞车 **7 组 / 14 件**——全部为**跨语言同名**，题号 `lang/` 前缀不同 ⇒ `Problem.id` 唯一性不破：

| 同名题 | 两件题号 |
|---|---|
| 判断奇偶 | `python/02_conditionals/01_odd_even` ／ `cpp/02_branch_loop/01_odd_even` |
| 判断质数 | `python/04_functions/04_is_prime` ／ `cpp/04_functions/04_is_prime` |
| 筛选高分学生 | `python/10_pandas_filter_group/01_filter_high` ／ `r/02b_dataframe/02_filter_rows` |
| 定义 student 类 | `python/16_classes_oop/01_simple_class` ／ `cpp/07_pointers_class/03_class_basic` |
| 各部门人数统计 | `python/20_hr_pandas/01_dept_headcount` ／ `sql/04_joins/05_join_groupby` |
| 去掉重复提交的问卷 | `python/24_real_world_data/02_dedup` ／ `r/14_real_world_data/02_dedup` |
| 各部门平均敬业度（清洗后再算） | `python/24_real_world_data/04_dept_avg` ／ `r/14_real_world_data/04_group_avg` |

⇒ 判定：**去重链无残留、无回退**。同名 7 组属"跨语言复用题名"设计（与规范档 §2.3「跨语言重名 slug 1 组＝已拍板维持现状」同族），**不构成缺陷**，也不建议改名（改名＝重编号，日间决策面）。

**在册前科（本单只读取数的直接理由）**：`core/progress.py:13-30` 的 `_guard_default_db_in_tests` 注释自述——波次 15 `learn36` 首版测试传 `dao=None`，`core/judge.py:_record_attempt` 在该分支自开 `data/progress.db`，**往生产库写出 14 行合成数据**（事后按四条 DELETE 定点清除，库 sha8 `46647128`→`cd2dbce4`）。该防线 9-27 才从"人工约定"升成机制（commit `b8cc72e`，A5①），例外出口 `LS_ALLOW_DEFAULT_DB_IN_TESTS=1`。

---

## 五、库侧（只读 `mode=ro`）残留复查

```console
$ python -c "... sqlite3.connect(f'file:{DB}?mode=ro', uri=True) ..."
write_probe          = OperationalError: attempt to write a readonly database   ← 零写主证（非 PRAGMA query_only 弱证）
tables               = attempts, learning_events, meta, problems_status, review_state, rubric_scores, schema_meta, sqlite_sequence
带 problem_id 的表    = attempts 15 行(distinct 14) / problems_status 14 行(14) / review_state 0 / learning_events 81 行(distinct 19)
被删题 05_fit_indices = 4 张表命中 0 行
题号大小写变体组      = 0   ← 规范档点名的承重风险（NTFS 上 `Python/` 与 `python/` 会同目录不同键空间）在真库里**尚未发生**
样本 10 题库内足迹    = attempts 0 / problems_status 0（10/10 全 0）
```

> ⚠ 读数解释：真库当前只有 **15 行 attempts / 14 行 problems_status**——即"被定点清除后几乎空库"的状态（与 §四 前科注释给的 sha8 链一致）。
> 所以「被删题 0 行孤儿」「大小写变体 0 组」两条**只是未发现问题**，不具统计承重；样本足迹全 0 也意味着**无法用库侧反查题面消费面**。
> 库内容数值一律**未做任何判定**（红线：不改数据、不做"该库该有多少行"的结论）。

---

## 六、异常清单（本单发现的、需要动作或需要人看的）

**必须动作的缺陷：0。** 以下为**记档级**观察，全部**未动盘**：

| # | 观察 | 是否新账 | 建议（**待裁，非本单执行**） |
|---|---|---|---|
| A-1 | 卷宗判据「选项结构」在本仓 schema 无对应字段（否证） | 新（本档首记） | 后续同类卷宗把该项写成「载荷键组合 5 类形态」；改派单口径＝主班侧事，本单不动任何档 |
| A-2 | `agent_dev/07_data_security/03`、`07_write_spec/02` 用 tags `open`/`ai_judge` 重复承载 `judge_mode` 已表达的事实 | 半新（规范档 §〇.3「同一件事被抄几遍」的具体实例化） | 归入规范档迁移规则族，**改 content 字面须人工放行**；本单不改 |
| A-3 | 样本 2 题命中在册重复标签组 D4/D7（用推荐拼法） | 否（§3.1 既有账） | 无需动作，R-01/R-02 迁移时一并处理 |
| A-4 | `content/paths/*.yaml` 6 件与题共用 `content/**/*.yaml` glob，任何"题数＝yaml 数"的粗口径都会得 409 | 否（规范档 §一 已钉） | 保持"含 `statement` 键"口径；已在本档复算式里沿用 |
| A-5 | 未复用现成门禁 `scripts/audit_content*.py`（为零写库自实现） | 新 | 若主班认为应复用，需先证 `audit_content_deep.py` 全链不触默认库（其 `sqlite3` 是 `:memory:`，但 import 面未逐层核）——**留给写单** |

**主动收窄（红线域）**：样本 #7（混淆矩阵/召回率）、#8（Cohen's d 效应量）、#10（中介效应解释）三题的**题面数值与统计口径正确性一律未判**——命中「统计数值结论」红线，只核格式与标签。

---

## 七、零写库自证

| 项 | 开工现值 | 收工现值 |
|---|---|---|
| `certutil -hashfile data/progress.db SHA256` 前 8 | `cd2dbce4`（122,880 B） | **`cd2dbce4`**（122,880 B，一字未动） |
| `git status --porcelain \| wc -l`（learning-system） | 0 | 1（**仅本档自身** `?? docs/insights/l927-06-sampling.md`，属卷宗点名的产物） |
| 侧车文件 | `data/progress.db-wal` 0 B、`-shm` mtime `09-27 13:46`（**先于本单开工 14:26**，属第二写手会话遗留，本单未触碰、未删除、未"顺手整理"） | 同前，未变 |
| 代码路径 | 三份探针**不 import** `core.progress` / `core.judge` / `core.dao` / `core.loader`；DB 侧只走 `file:...?mode=ro` URI ＋ 当场试写求 `SQLITE_READONLY`（见 §五 输出） | — |
