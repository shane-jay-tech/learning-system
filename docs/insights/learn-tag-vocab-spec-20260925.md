---
id: learn-tag-vocab-spec-20260925
title: 五轴标签规范（语言/难度/知识点/题型/来源）＋重复·大小写·未知三清单与迁移规则
task: 20260925-120546-361f（桥接单，工作类型 docs，风险档 B）
shift: qoder-executor-20260925-1240-learn36
written: 2026-09-25T12:5x
head_at_write: ea18caf
mode: 只读普查＋规范提案（content/ 与 core/ 与 ui/ 与 data/ 零 diff；探针在 gitignore 的 tmp/learn36/）
status: 规范稿——词表基线与迁移规则已钉；**涉及改 content 字面的规则一律标"须人工放行"，本档不动盘**
supersedes_or_extends:  extends `docs/insights/learn-content-tags-census-20260924.md`（l924-24 出词表 census 与消费面；本档出规范与三清单，两者引数口径一致）
---

# 五轴标签规范与三清单（重复 / 大小写 / 未知）

> 卷宗任务：「整理语言、难度、知识点、题型和来源标签的规范。验收：重复标签、大小写差异和未知标签有清单与迁移规则。」
> 本档按「**先证其在世，再定规范**」的顺序写：每一轴先给盘上载体与码内权威，给不出载体的直接记为否证，
> 不为了凑齐"五轴"去发明字段（本批已有兄弟班在同类单上否证过四枚凭空假设）。

## 〇、一句话结论

1. **五轴里三轴在世、两轴须按实况收窄**：
   - 语言 / 难度 / 知识点 ＝ 盘上确有载体（目录名＋`Problem.id` 前缀 / `difficulty` 整型 / `topic` 键）。
   - **题型** 作为字段名不存在（`question_type` 全仓 **0 命中**），实况载体是 **`judge_mode`**，合法集只有 `{run, ai_open}` 两值。
   - **来源** 作为标签字段**不存在**（`content/**/*.yaml` 里含 source/origin/来源 字样的键 **0 处**），
     实况只有两种痕迹：运行时的 `AI_VARIANT::` 题目前缀（真库 `attempts`/`problems_status` 里 **0 行**带它），
     以及 tags 自由词里混着的三个"来源味"标记（`real-data` 12 / `real-task` 8 / `hr` 13）。
2. tags 词表 **416 唯一值 / 898 次出现 / 265 单例**（与 l924-24 同值，HEAD 已前进至 `ea18caf` 而词表未变）：
   - **大小写差异：严格变体 0 组**——卷宗假设的"同一词写成两种大小写"在 tag 值层面是**空集**（可复算，见 §三.2）；
     另有 **11 个**值违反小写词形约定（`IQR`/`ValueError`/`operator()`/`data.frame`…），它们**没有小写孪生值**，属"词形不合群"而非"大小写不一致"。
   - **重复标签：7 组、涉及 15 个值、累计 33 次出现**（把 `_`/`-`/`.`/空格与单复数归一后当场合并，含 `groupby` 10 次那个最大组）。
   - **未知标签：今天无从判起**——全仓**没有任何受控词表**（`tags` 在生产侧唯一读者是 `core/loader.py` 的搬运，l924-24 双轨已证）。
     所以本档把"未知"改写成**可执行判据**：§三.3 给出基线指纹 `bfbf832d88a75f3d`，凡不在重算集合内的值即未知，一条命令可列。
3. 真正的规范化杠杆**不在 tags 里，而在"同一件事被抄了几遍"**：语言词表在全仓有 **7 处手写副本、2 种顺序**；
   `judge_mode` 合法集有 **2 处**独立定义。这两处是本档唯一"改了能同时收干净三轴"的落点。

---

## 一、口径与复算配方（每条读数都可现取）

统一口径（本档所有"题"字都指这个）：

- **题** ＝ `content/**/*.yaml` 中顶层解析为 mapping **且含 `statement` 键**的文件 ⇒ **403**。
- **路径定义件** ＝ 含 `milestones` 键的 `content/paths/*.yaml` ⇒ **6**（它们**本就不是题**，没有 `tags/difficulty/topic` 是设计，不是漏标）。
- `content/**/*.yaml` 合计 **409**，解析失败 **0**，`.yml` 变体 **0**（无第二种扩展名，口径无歧义）。

```bash
# 仓库根 D:/code/learning-system 执行，全程只读、零写盘
PYTHONIOENCODING=utf-8 python - <<'PY'
import io, yaml, hashlib, re
from collections import Counter, defaultdict
from pathlib import Path
rows = []
for p in sorted(Path("content").rglob("*.yaml")):
    rows.append((p, yaml.safe_load(io.open(p, encoding="utf-8").read())))
prob = [(p, d) for p, d in rows if isinstance(d, dict) and "statement" in d]
tags = Counter()
for p, d in prob:
    for x in (d.get("tags") or []): tags[str(x)] += 1
uni = sorted(tags)
print("yaml=%d 题=%d 路径件=%d" % (len(rows), len(prob),
      sum(1 for _, d in rows if isinstance(d, dict) and "milestones" in d)))
print("unique=%d occ=%d singletons=%d 基线sha=%s"
      % (len(uni), sum(tags.values()), sum(1 for v in tags.values() if v == 1),
         hashlib.sha256("\n".join(uni).encode()).hexdigest()[:16]))
def norm(k):                                    # 重复标签判据（§三.1）
    n = re.sub(r"[-_ .]+", "-", k.strip().lower()); n = re.sub(r"-ies$", "-y", n)
    return re.sub(r"([a-z])s$", r"\1", n).replace("-", "")
g = defaultdict(list)
for k in uni: g[norm(k)].append(k)
d = {k: v for k, v in g.items() if len(v) > 1}
print("重复组=%d 涉及值=%d 涉及出现=%d" % (len(d), sum(map(len, d.values())),
      sum(tags[x] for v in d.values() for x in v)))
cc = defaultdict(list)
for k in uni: cc[k.lower()].append(k)          # 严格大小写变体（§三.2 判据 A）
print("严格大小写变体组=%d" % sum(1 for v in cc.values() if len(v) > 1))
print("违反小写词形的值=", [k for k in uni if not re.fullmatch(r"[a-z0-9_\u4e00-\u9fff-]+", k)])
PY
```

**2026-09-25T12:5x @ HEAD `ea18caf` 实测**：`yaml=409 题=403 路径件=6 / unique=416 occ=898 singletons=265 基线sha=bfbf832d88a75f3d / 重复组=7 涉及值=15 涉及出现=33 / 严格大小写变体组=0 / 词形不合群值=11`。

在世性判据（卷宗五轴逐条 `rg` 取证，含否证）：

| 卷宗用词 | `rg -F` 命中文件数（core/ui/scripts/tests ＋ content ＋ docs） | 判定 |
|---|---|---|
| `knowledge_point` / `knowledgePoint` | py **0** ／ yaml **0** | **否证**：知识点不是字段。盘上"知识点"＝ `topic`（`ui/pages/path.py` 的「包含的知识点：」与 `ui/pages/language.py` 的「上一个知识点」都直接渲染 topic）⇒ 本档知识点轴按 `topic` 规范 |
| `question_type` / `questionType` | py **0** ／ yaml **0**；中文「题型」仅 1 份 docs | **否证**：题型不是字段。实况载体 `judge_mode`（yaml 140 处显式）⇒ 题型轴按 `judge_mode` 规范 |
| `source` / `origin` / 来源（作为**键**） | 题 yaml 顶层键 **0 处**（早先 `rg -i source` 的命中全是 `Resource` 假阳性）；content 下无 source/origin 命名文件 | **否证**：来源标签不存在。仅有 `AI_VARIANT::` 前缀（`core/ai_generate.py` 拼 id，`ui/pages/language.py` 判前缀）＋ tags 里的 `real-data/real-task/hr` ⇒ 本档给"来源轴该长什么样"的**建轴提案**，不谎称它已存在 |
| `difficulty` | yaml **403**，类型全 `int` | **在世**，门禁在 `scripts/audit_content.py`（`difficulty < 1 or > 5` 记 error） |
| 语言（`lang`） | `ui/components.py` 的 `LANG_META`/`ALL_LANGS` ＋ `Problem.id` 首段 | **在世**，但词表被抄成 7 份（§二.1） |

---

## 二、五轴规范

### 2.1 语言轴（lang）

| 项 | 规范 |
|---|---|
| 合法值 | `python` / `sql` / `cpp` / `r` / `agent_dev`（**恰 5 值**） |
| 唯一权威 | `ui/components.py` 的 `LANG_META` 键序，`ALL_LANGS = list(LANG_META.keys())` 派生 |
| 载体 | 目录名 `content/<lang>/` ＋ `Problem.id` 首段（`core/loader.py` `_build_problem` 拼 `f"{lang}/{slug}/{problem_slug}"`）＋ DB `attempts.lang` |
| 显示名 | `LANG_META[lang]["name"]`（`Python`/`SQL`/`C++`/`R`/`Agent 开发`）——**显示名不参与寻址**，任何键都不许用 `name` |
| 非语言目录 | `content/paths`（6 份路径件）、`content/datasets`（3 CSV ＋ 1 生成器）——**不得**被当作语言遍历 |

**实测缺口（本档新增，前档未记）**：`core/loader.py:load_language` **不做白名单校验**，任何目录名都照单全收后返回 `[]`：

```console
load_language('datasets') -> topics=0     # 静默空
load_language('paths')    -> topics=0     # 静默空
load_language('nope')     -> topics=0     # 拼错语言 → 与"该语言暂时没题"不可分辨
load_language('Python')   -> topics=27    # 🔴 大写首字母在大小写不敏感的 NTFS 上**照样加载成功**
```

⇒ 语言轴的大小写风险**不在 tags 里，在这里**：`Python` 与 `python` 在 Windows 上落到同一目录，
但会产出 `Problem.id` 首段为 `Python/...` 的另一套题号空间（`progress.db` 按 `problem_id` 记，会写成新行）。
这是本档"大小写差异"一栏**唯一有承重的那条**。

**词表副本实测**（`rg -n '^\s*LANGS\s*='`，排除 `.venv/__pycache__/tmp`）：**7 处手写、2 种顺序**——

- 顺序 `(python, r, cpp, sql, agent_dev)` → `scripts/audit_paths_prereq.py`
- 顺序 `(python, sql, cpp, r, agent_dev)` → `tests/test_content_census.py`、`test_content_difficulty_pins.py`、
  `test_content_ids_unique.py`、`test_content_numeric_consistency.py`、`test_content_thin_topic_p0.py`、`test_topic_dualnum_pins.py`

### 2.2 难度轴（difficulty）

| 项 | 规范 |
|---|---|
| 合法值 | 整数 **1..5**（`scripts/audit_content.py` 的 range 判据为唯一现行门禁） |
| 载体 | yaml `difficulty:` 顶层键；`core/loader.py` 用 `int(raw_diff)` 强转，缺键回落 **1** |
| 现值分布 | `1:75 / 2:180 / 3:131 / 4:16 / 5:1`（题面 403 件，**0 件缺失、0 件越界、类型全 int**） |
| 语言×难度 | 已由 `tests/test_content_difficulty_pins.py:PINNED_HIST` 精确钉桩（含 4/5 档题 id 名单 `PINNED_TOP_TIER`） |

**规范条款**：`difficulty` 只允许字面整数。`"3"`（字符串）会被 `int()` 静默吃掉、`2.5` 会被截成 `2`——
两者今天都不存在于盘上，但**没有桩挡着**，属"新增即失效"的开放面（迁移规则 R-05 补这条）。
新题难度 ≤3 的既有指引（`plan.md` 题库内容规范）继续生效：4/5 档扩宽 `core/progress.py` 的 SRS ease 可达面，属红线域。

### 2.3 知识点轴（topic）

| 项 | 规范 |
|---|---|
| 合法值 | `content/<lang>/` 下的**目录名本身**（形如 `NN_name`，NN 为两位零填充号数；消歧允许 `NNx_` 字母后缀） |
| 唯一权威 | **目录名**。yaml `topic:` 键是**副本**，必须逐字等于目录名 |
| 现有门禁 | `scripts/audit_content_deep.py`（`p.topic != topic.slug` 记 error）⇒ 实测 **403 件全部相等、0 漂移** |
| 显示名 | `_lesson.md` 的首个 H1（`core/loader.py` `_topic_title`），H1 缺失才回落 slug 人话化 |

知识点轴实际有**三个标签承载者**，规范必须把它们分层，否则"重复知识点"无法判：

1. **号数前缀**（`20_`）——只用于排序，`sorted()` 字典序；全仓**无任何代码解析号数**（l922-05 已证）。
2. **slug 全名**（`20_hr_pandas`）——寻址用，全局键是 `lang/slug`。
3. **H1 显示名**——给人看的，可以同名。

实测三张重复账：

| 类别 | 读数 | 是否缺陷 |
|---|---|---|
| H1 显示名跨专题重复 | **0 组**（84 个可取 H1 的 lesson 两两不同） | — |
| 跨语言重名 slug | **1 组**：`04_functions` ∈ {cpp, python} | **不是缺陷，已有人拍板**：`docs/insights/content-id-conflict-04-functions-20260919.md` 结论「维持现状，不改名」，且 `tests/test_content_ids_unique.py` 把"唯一真冲突"钉成契约 |
| 同语言内号数撞号 | **6 组**：python 20/21/22、r 14、agent_dev 07/08（`02b_dataframe` 属字母后缀消歧，**不计入**） | 已由 `tests/test_topic_dualnum_pins.py` 钉桩（组序、字典序==数值序、双号必相邻）；**改号数＝重编号，属日间决策**，见 `docs/insights/learn-topic-dualnum-20260921.md` |

⇒ 知识点轴今天**不缺规范、缺的是"号数 vs 位置"话术**：`ui/pages/language.py` 展示的「第 N 个知识点」是**列表位置**，
不是号数；错位条数 python 7 / r 16 / agent_dev 8（l922-05 实测）。规范条款 R-06：文档与人话一律用 `lang/slug` 指代，禁止裸用「20 号那课」。

### 2.4 题型轴（judge_mode）

| 项 | 规范 |
|---|---|
| 合法值 | `run` / `ai_open`（**恰 2 值**，全小写下划线） |
| 缺省 | 键缺失 ⇒ `core/loader.py` 回落 `"run"`。现值：**263 件依赖缺省、70 件显式 `run`、70 件 `ai_open`** |
| 现值合法性 | 显式值只有 `'ai_open'`/`'run'` 两种拼法；小写归一后**无第三种变体**（盘上零非法值） |
| 合法集定义处 | **2 处独立手写**：`tests/test_content_census_r.py` 的 `VALID_JUDGE_MODES = {"run","ai_open"}`、`scripts/mark_r_judge_plain.py` 的 `VALID_JUDGE_MODES = ("run","ai_open")` |

**"题型"真正想要的是 5 类**（`judge_mode` 单值不足以承载，实测载荷键组合恰为 5 种，无第 6 种）：

| 有效题型 | 判据（载荷键组合） | 件数 |
|---|---|---|
| run/输出比对 | `run` ＋ 仅 `expected_output` | **187** |
| run/多用例 | `run` ＋ `expected_output` ＋ `tests` | **92** |
| run/SQL 行比对 | `run` ＋ `setup_sql` ＋ `expected_rows` | **54** |
| ai_open/评分表 | `ai_open` ＋ 仅 `rubric` | **10** |
| ai_open/评分表＋参考答案 | `ai_open` ＋ `rubric` ＋ `reference_answer` | **60** |

合计 403 ⇒ 与题数逐位对平，**零未归类件、零组合越界**。规范条款：题型轴保持 `judge_mode` 两名制，
**5 类形态由上表推导而非新字段**（若将来要显式化，走 R-09 的建轴流程，不得借 tags 自由词塞）。

### 2.5 来源轴（本档判为"待建"）

盘上事实：无字段、无合法集、无门禁。可用的只有两样：

| 实况载体 | 现值 | 规范性判定 |
|---|---|---|
| `AI_VARIANT::` 题 id 前缀（`core/ai_generate.py` `data["id"] = f"AI_VARIANT::{original.get('id')}"`） | 真库 `attempts` 15 行 / `problems_status` 14 行 / `review_state` 0 行中，带该前缀者 **0 行** ⇒ 变式题只活在 session_state，从不落库 | 这是**唯一**在码内的来源标记。规范条款：判"是否 AI 生成"**只认 id 前缀**，禁止新增第二判据（`ui/pages/language.py:_retire_variant` 已按前缀精确拼键） |
| tags 里的来源味标记 | `real-data` 12 次（跨 python/r/sql 三根）、`real-task` 8（agent_dev）、`hr` 13（python）、`excel` 1 | **越权使用**：tags 是被 l924-24 判为"零读者"的自由词，用它承载来源＝来源轴不可校验。建轴提案见 R-08 |

---

## 三、三张清单（卷宗验收面的逐条落地）

### 3.1 重复标签清单

判据：`norm(k) = lower(k)` 后把 `-`/`_`/`.`/空格统一成 `-`、去分隔符、再做单复数归一（`-ies→-y`、`[^s]s→[^s]`）。
归一后仍合并者即同一标签的多种写法。**7 组、15 值、33 次出现**（@ `ea18caf`）：

| # | 规范名（推荐保留） | 盘上并存写法（频次） | 组内出现合计 | 迁移 |
|---|---|---|---|---|
| D1 | `group-by` | `group-by`(3) \| `group_by`(1) \| **`groupby`(10)** | 14 | R-01 |
| D2 | `error-handling` | `error-handling`(1) \| `error_handling`(1) | 2 | R-01 |
| D3 | `feature-importance` | `feature-importance`(1) \| `feature_importance`(1) | 2 | R-01 |
| D4 | `effect-size` | `effect-size`(1) \| `effectsize`(2) | 3 | R-01 |
| D5 | `if-else` | `if-else`(3) \| `ifelse`(2) | 5 | R-01 |
| D6 | `function` | `function`(3) \| `functions`(1) | 4 | R-02 |
| D7 | `line` | `line`(2) \| `lines`(1) | 3 | R-02 |

> ⚠ 规范名的取舍不是"少数服从多数"：D1 里 `groupby` 以 10 次压倒 `group-by` 的 3+1，
> 但**全仓 tag 的主流词形是连字符**（`cross-validation`/`real-data`/`list-comprehension`…），故推荐名取 `group-by`。
> 这是一条**约定裁决**，不是算出来的结论 ⇒ 放行前不得机械改盘（见 R-01 的闸）。
> 另注：l924-24 §三 凭人工判读列过 `cross_val` vs `cross-validation`、`if-elif-else` vs `if-else` vs `if` 等对，
> 那些是**语义近邻**（本判据不合并：`cross_val` 与 `cross-validation` 归一后仍不同串），
> 属"同义词治理"而非"异形字治理"，本档**不扩判据去凑**，留给 §五 的人工面。

补充账（同一字段内部）：同一文件内重复打同一 tag 的件数 **0**；`tags` 出现非字符串项 **0**；`tags` 被写成标量（非 list）的件 **0**。
⇒ "重复标签"这件事 100% 发生在**跨文件的词形层**，不在单文件的列表层。

### 3.2 大小写差异清单

**判据 A（tag 值层）**：仅大小写不同的孪生值 ⇒ **0 组**（`{k for k in lower-collapse if len>1}` 为空）。
⇒ 卷宗假设的"标签大小写不一致"在 tags 值上**不成立，登记为否证**；本栏改列下面两笔**真会咬人**的：

**判据 B（词形约定层，11 值）**——违反 `^[a-z0-9_一-龥-]+$`，即"该小写而没小写 / 带了标点"：

```
IQR(1)  Surv(1)  ValueError(1)  ZeroDivisionError(1)  data.frame(4)
operator()(1)  operator+(1)  operator<<(1)  operator==(1)  operator[](1)  which.max(1)
```

逐条处置：`IQR`/`Surv`/`ValueError`/`ZeroDivisionError` 是**统计与语言的专有名**，规范上应**保留原拼写**（改成 `iqr` 反而错）；
`operator*` 家族 5 值与 `data.frame`/`which.max` 是**代码符号本身**，规范上属"合法带标点的例外白名单"，
但 `operator==` 家族被拆成 5 个值这件事 l924-24 已点名，收敛应走同义词治理，不走进形归一。
⇒ 规范条款：**tag 默认小写连字符；例外只有两类——专有名与代码符号，二者都必须在登记表里显式登记，未登记的混合大小写值按未知处理（R-03）。**

**判据 C（语言/键层，承重最大）**——见 §2.1 末：`load_language("Python")` 在 NTFS 上真能加载 27 个专题。
这条是本单唯一"大小写会造成实际数据分叉"的位置，规范条款 R-04 处理它。

### 3.3 未知标签清单

**先钉为什么"今天判不出"**（可复算，两轨）：

```console
$ rg -n '\.tags\b|\["tags"\]|get\("tags"' core ui scripts
core\loader.py:186:    raw_tags = data.get("tags") or []      # ← 全仓生产侧唯一一处，且只搬运
$ rg -n 'ALLOWED_TAGS|VALID_TAGS|TAG_VOCAB|KNOWN_TAGS' .      # 受控词表常量
（零命中）
```

⇒ 没有任何权威集合可比对，"未知"无从定义。本档把它变成**可执行判据**：以本 HEAD 的重算集合为登记表基线，
基线指纹 **`bfbf832d88a75f3d`**（416 值按字典序换行拼接的 sha256 前 16 位），凡重算集合里查不到的值即未知。

检测一条命令（零写盘，改盘后可跑）：

```bash
# 未知标签/基线漂移检测（零写盘）。基线 = §一 钉的 bfbf832d88a75f3d（416 值 @ ea18caf）
PYTHONIOENCODING=utf-8 python - <<'PY'
import io, yaml, hashlib
from pathlib import Path
u = sorted({str(x) for p in sorted(Path("content").rglob("*.yaml"))
            for d in [yaml.safe_load(io.open(p, encoding="utf-8").read())]
            if isinstance(d, dict) and "statement" in d
            for x in (d.get("tags") or [])})
fp = hashlib.sha256("\n".join(u).encode()).hexdigest()[:16]
print("值数=%d 基线 bfbf832d88a75f3d 现值 %s %s"
      % (len(u), fp, "未变" if fp == "bfbf832d88a75f3d" else "已变 ⇒ 与基线求差即新增/删除的未知值"))
PY
```

实测输出：`值数=416 基线 bfbf832d88a75f3d 现值 bfbf832d88a75f3d 未变`。

**已在基线内、按规范应判"语义未知"的三笔**（这才是今天能交出的清单）：

| 类别 | 值 | 处数 | 为什么算未知 | 迁移 |
|---|---|---|---|---|
| 跨轴撞词 | `sql` | 4（全在 sql 根） | 值本身是**语言轴**的合法词，出现在 tags 里既不表达技能也不表达形态，语言已由目录名唯一确定 ⇒ 冗余 | R-07 |
| 停用词级 | `and`/`with`/`from`/`get`/`new`/`now`/`what`/`sub`/`log`/`data`/`int`/`bool`/`size`/`line`/`like`/`head` | l924-24 §三 判读列出的 16 值（含 2 次的 `and-or`） | 取自命令行的词，不指任何技能/库/形态 ⇒ 检索面无信息量 | R-07（同义词表须人工签） |
| 未登记混合大小写 | §3.2 判据 B 的 11 值 | 11 | 属"须登记才可豁免词形约定"的白名单，今天没登记 ⇒ 规范生效后即视为未登记项 | R-03 |

⇒ **未知标签清单不是一份"待删名单"，而是一份"待登记名单"**：基线里的 416 值全部**合法但未被承认**，
本档只把其中的**跨轴/停用/词形**三类标出，其余 389 值视为已登记（继承 l924-24 的词频与单例账）。

---

## 四、迁移规则

编号即引用位。**除 R-01/R-02 的"新增题"分支外，全部规则的落盘动作都需人工放行**——本档只出规则不出 diff。

| # | 规则 | 落点 | 连带门禁（改了会红什么） | 放行条件 |
|---|---|---|---|---|
| R-01 | **异形字归一**：同一概念只保留 §3.1 的规范名。存量 15 值 33 处一次性改名；**新增题一律写规范名** | `content/**/*.yaml` 的 `tags:` 列表项 | 🔴 `scripts/mark_r_judge_plain.py` 把**顶层 `tags:` 行当插入锚点**（找不到即 `_fail`）⇒ 只能改列表项字面值，**不得增删 `tags:` 行本身、不得改缩进结构** | 人工确认 §3.1 的 7 个规范名（尤其 D1 取 `group-by` 而非 `groupby`） |
| R-02 | **单复数归一**：`functions→function`、`lines→line`。规则＝tag 指"概念"，用单数 | 同 R-01 | 同 R-01 | 与 R-01 同批放行，同一次提交 |
| R-03 | **词形约定**：新 tag 必须 `^[a-z0-9][a-z0-9-]*$`；专有名/代码符号要豁免，须先在本档白名单登记（现候选＝§3.2 判据 B 的 11 值） | 本档 §3.2 | 无（纯约定） | 白名单一次性登记即可，属文档动作 |
| R-04 | **语言值只认 `ALL_LANGS`**：任何调用 `load_language` 前断言 `lang in ALL_LANGS`；DB `lang` 列写入前同校验。把 7 处手写 `LANGS` 副本改为 `from ui.components import ALL_LANGS`（或抽到 `core` 内避免 ui→core 反向依赖） | `core/loader.py` ＋ 6 个 tests ＋ `scripts/audit_paths_prereq.py` | 🔴 改测试件的 `LANGS` 会动到 5 个在册内容桩；`test_content_census.py` 有 `== 403` 等值断言 | **须人工放行**：收口 7 副本是 src 改动，非 docs 面 |
| R-05 | **难度只允许字面整数 1..5**：补一条 `isinstance(raw_diff, int)` 的桩，禁字符串/浮点经 `int()` 静默归一 | 新桩（或并入 `tests/test_content_difficulty_pins.py`） | 现值 0 件违反 ⇒ 新增桩**当场绿**，不产生新红 | 可直接做（纯增量，不改判分口径） |
| R-06 | **知识点指代只用 `lang/slug`**；`topic:` 键保持等于目录名；号数**不重编** | 文档话术层 | `test_topic_dualnum_pins.py`（6 组双号与次序）＋ `test_content_ids_unique.py`（跨语言唯一冲突 `04_functions`）＋ `audit_content_deep.py` 的 topic≡slug 检查 | 重编号属日间决策（`learn-topic-dualnum-20260921.md` 方案稿），本档不推 |
| R-07 | **冗余/停用 tag 的摘除**：`sql`（4 处）先摘；16 个停用词值待人工签同义词表后再动 | `content/**/*.yaml` | 同 R-01 的插入锚点约束 | 人工签 |
| R-08 | **来源轴建轴提案**：要"来源"就必须新建显式字段（建议题级 `origin: curated\|ai_variant\|real_dataset`），并把 tags 里的 `real-data/real-task/hr/excel` 迁过去；**不新增 tags 值当来源用** | `core/loader.py` 的 `Problem` ＋ 403 件 yaml ＋ `data/progress.db` 无涉 | 🔴 加字段会改 `Problem` 数据类与 `mark_r_judge_plain.py` 的 `ANSWER_KEYS` 键序 ⇒ 属结构改动 | **人工裁决项**（是否要这条轴本身是产品问题，l924-24 的三案之一即"冻结声明"） |
| R-09 | **新轴/新标签的登记程序**：先在本档 §三.3 基线里加值并更新 sha，再落 content；未登记的 tag 值 PR 面视为非法 | 本档 | — | 流程约定，无须放行 |

---

## 五、遗留与人工面（本档不闭合的部分）

1. **"未知标签"的终态要的是受控词表，不是一份 census**：本档给的是"基线指纹 + 检测命令"，属**弱规范**。
   要变强规范必须回答 l924-24 的三案（接线消费 / 二分收敛 / 冻结声明）——**选案是产品裁决，本档不选**。
2. 语义近义治理（`cross_val`/`cross-validation`、`if-elif-else`/`if-else`/`if`、`operator==` 家族拆 5 值）
   超出"异形字"判据，需要人工签同义词表，本档**未做**也未假装做。
3. R-04（收口 7 处语言副本）与 R-08（建来源轴）都是 **src 面改动**，本单工作类型是 docs ⇒ 只出规则未落码。
4. 本档若登记进 `docs/insights/INDEX`（权威索引 `learn-insights-index-20260918.md`），
   需同步加一行才能过 `tests/test_insights_index_closure.py` 的 A==B 哨兵；**本班按多班同改禁例不动索引**，交主班代登。
