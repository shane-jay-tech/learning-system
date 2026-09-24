---
id: learn-content-tags-census-20260924
title: learning content tags 词表普查＋生产消费面取证（只读，三案建议稿）
task: l924-24
shift: qoder-executor-20260925-0220-learn30
written: 2026-09-25T02:4x
head_at_write: e71816d
mode: 只读普查（content/ 与 core/ 与 ui/ 零 diff，探针在 gitignore 的 tmp/l924-24/）
status: 建议稿——三案并列，未选案（选案属人工裁决）
---

# content tags 词表普查与消费面取证（l924-24）

> 本档只做三件事：① 把 tags 词表的**现值与口径**钉住（卷宗旧口径 343/220 已漂，现值 416/265）；
> ② 用 **rg＋AST 双轨**证明「词表在生产侧零读者」这句话到底能说到什么程度（含一条卷宗没说的例外）；
> ③ 给**三案**（接线消费 / 二分收敛 / 冻结声明）**并列利弊与连带面，不选案**。

## 〇、一句话结论

`content/**/*.yaml` 里 **403 件题**共维护 **416 个 tag 值**（累计出现 898 次，其中 **265 个值只出现 1 次＝63.7%**），
而全仓 **150 份 .py 中没有任何一行生产代码读 `Problem.tags` 的值**（loader 只搬运、judge/AI 出题只取别的键）；
唯一的"读者"是 `scripts/mark_r_judge_plain.py` 把顶层 `tags:` **行**当作插入锚点——**它读的是位置，不是词**。
⇒ 现状是「有人在维护词条、没有程序消费词条」，**是否值得继续维护属产品裁决**，本档只出材料。

## 一、口径与复算配方（每条读数都可现取）

### 1.1 主 census（完成标准 ①）

```bash
# 仓库根 D:/code/learning-system 执行；只读，零写盘
PYTHONIOENCODING=utf-8 python - <<'PY'
import io, yaml
from collections import Counter
from pathlib import Path
files = sorted(Path("content").rglob("*.yaml"))
c = Counter(); no_tags = []
for p in files:
    d = yaml.safe_load(io.open(p, encoding="utf-8").read()) or {}
    t = d.get("tags")
    if not t:
        no_tags.append(p);  continue
    for x in (t if isinstance(t, list) else [t]):
        c[str(x)] += 1
print("files=%d unique=%d singletons=%d no_tags=%d occurrences=%d"
      % (len(files), len(c), sum(1 for v in c.values() if v == 1), len(no_tags), sum(c.values())))
PY
```

**2026-09-25T02:3x @ HEAD `e71816d` 读数**：`files=409 unique=416 singletons=265 no_tags=6 occurrences=898`
⇒ 与卷宗"唯一值 416／单例 265／6 件无 tags／409 件"**逐位对平**；卷宗另写的旧口径 **343/220 已过期**，本档起以 416/265 为准。

三轨交叉验文件数（防 `rg -c` 对零命中文件静默省略那类假数）：

| 轨 | 命令 | 读数 |
|---|---|---|
| find | `find content -name '*.yaml' \| wc -l` | **409** |
| rg | `rg --files content -g '*.yaml' \| wc -l` | **409** |
| 磁盘 glob | `Path('content').rglob('*.yaml')` 计数（上面 §1.1） | **409** |
| `.yml` 变体 | `find content -name '*.yml' \| wc -l` | **0**（无第二种扩展名，口径无歧义） |
| 带 `tags:` 行 | `rg -l "^tags:" content -g '*.yaml' \| wc -l` | **403**（与 §1.1 的 409−6 对平） |

### 1.2 「6 件无 tags」不是缺陷，是件型（否证卷宗隐含口径）

```bash
PYTHONIOENCODING=utf-8 python -c "
import io,yaml
from pathlib import Path
for p in sorted(Path('content/paths').glob('*.yaml')):
    print(p.name,'->',list(yaml.safe_load(io.open(p,encoding='utf-8').read())))"
```

6 件全部是 `content/paths/*.yaml`（`agent_mastery / cpp_foundation / people_analytics / python_advanced / quick_stats / r_advanced`），
顶层键为 `title/subtitle/icon/estimated_hours/milestones` —— **学习路径定义件，本就不是题，没有 tags 字段是设计而非漏标**。
⇒ 后续任何"补齐 6 件 tags"的动作都是错的；真正的分母是 **403 件题，覆盖率 100%**（无 tags 为空、无标量 tags：`empty_tags=0 / scalar_tags=0`）。

### 1.3 语言根分布（词表是"每语言私有技能词"）

`content/<lang>/**` 切根，occurrences 分布：`python 278 / agent_dev 209 / r 190 / cpp 117 / sql 104`（合计 898）。
**跨 ≥2 语言根的 tag 只有 59 个（59/416＝14.2%），357 个值绑死单一语言根。**

## 二、词频 top20（与 `Counter.most_common(20)` 一致，完成标准 ③）

| # | tag | 频次 | 语言根数 | 目录数 | 落在哪个根 | 类别（人工判） |
|---|---|---|---|---|---|---|
| 1 | `ai_judge` | 28 | 1 | 8 | agent_dev | 判定标记 |
| 2 | `spec` | 20 | 1 | 4 | agent_dev | 主题（写规格） |
| 3 | `pandas` | 14 | 1 | 3 | python | 库/主题 |
| 4 | `sklearn` | 13 | 1 | 4 | python | 库/主题 |
| 5 | `hr` | 13 | 1 | 3 | python | 数据集域 |
| 6 | `debug` | 12 | 1 | 4 | agent_dev | 主题（读报错） |
| 7 | `open` | 12 | 1 | 4 | agent_dev | 题型标记（开放式，与 ai_judge 同件共现） |
| 8 | `real-data` | 12 | **3** | 3 | python,r,sql | 形态标记 |
| 9 | `iteration` | 11 | 1 | 3 | agent_dev | 主题 |
| 10 | `review` | 10 | 1 | 3 | agent_dev | 主题 |
| 11 | `sum` | 10 | **4** | 10 | cpp,python,r,sql | 技能（跨语言） |
| 12 | `groupby` | 10 | 2 | 5 | python,sql | 技能 |
| 13 | `real-task` | 8 | 1 | 1 | agent_dev | 形态标记 |
| 14 | `string` | 7 | 1 | 3 | cpp | 技能 |
| 15 | `count` | 7 | 3 | 7 | cpp,python,sql | 技能 |
| 16 | `filter` | 7 | 3 | 6 | python,r,sql | 技能 |
| 17 | `regex` | 7 | 2 | 3 | python,r | 技能 |
| 18 | `git` | 6 | 1 | 2 | agent_dev | 主题 |
| 19 | `decompose` | 6 | 1 | 2 | agent_dev | 主题 |
| 20 | `io` | 6 | 3 | 4 | cpp,python,r | 技能 |

复算：`most_common(20)` 即上表前三列；第 4/5 列由 `tmp/l924-24/probe_mix.py` 产出（探针件在 gitignore 的 `tmp/` 下，不入仓）。

**混杂度取证（卷宗"标记类 vs 主题类"的可复算版本）**：人工列一份 57 词的标记类词表
（`ai_judge/open/spec/real-data/real-task/starter/comprehensive/…/prompt-engineering/tool-use/mcp` 全表见 `tmp/l924-24/probe_mix.py:MARKER`），
盘上命中 **57 值 / 累计 207 次（占 898 的 23.1%，其中 32 个是单例）**；其余 **359 值 / 691 次**是技能·库·数据集类。
⇒ **同一个字段里两类语义各占约一到两成与七到八成，且标记类只有 `real-data` 一个真正跨语言**——这正是"词表没有受控词根"的直接读数。

频次分布（`Counter(freq.values())`）：出现 1 次 265 个／2 次 57／3 次 28／4 次 21／5 次 18／6 次 10／7 次 4／8 次 1／10 次 3／11 次 1／12 次 3／13 次 2／14 次 1／20 次 1／28 次 1。

## 三、单例清单（265 个只出现 1 次的值，完成标准 ① 的第二半）

```
IQR, Surv, ValueError, ZeroDivisionError, ab-testing, abstract, advanced, aes, agg, aic, alias, alpha, and,
anonymization, aov, api, append, apply, argmax, arrange, assert, bool, boolalpha, boolean, bootstrap, broom,
bugfix, change-management, check, checkout, chi_square, class-template, coalesce, cohort, color, combinations,
commit, concat, config, constant, constructor, container, correlated-subquery, correlation, counter, coupling,
cross-validation, cross_val, custom-exception, cutree, data, data-quality, date_parsing, decision, decision-tree,
decomposition, delete, dependency, dependency-injection, deref, diagnosis, diagram, distinct, dunder, edge-case,
efa, effect-size, emplace_back, encoding, env, error-handling, error_handling, eta-squared, evaluation, excel,
except, f_oneway, factory, feature, feature-importance, feature_importance, find, fit, from, function-template,
functions, functor, generator, generator-expression, get, getline, ggsave, greater, group_by, groups,
hazard-ratio, hclust, head, headings, http, if-elif-else, ifstream, in-place, index, inner, int, intersection,
is-null, is_open, iter, itertools, julianday, keep, knitr, lag, layers, length, like, limit, linear-regression,
lines, list-comprehension, lme4, lmer, log, logic, logical, logrank, lvalue, magic-method, magic-number,
maintainability, map2, math, matrix, mcp, median, metrics, minimization, mixed-effects, model-comparison,
moderation, month, move-constructor, moved-from, multi-agent, mutate, naming, new, next, now, nrow, nullif,
odds-ratio, ofstream, ols, operator(), operator+, operator<<, operator==, operator[], ostream, out_of_range,
overload, p-value, pearsonr, pii, pipeline, pivot_longer, pivot_table, pivot_wider, pointer, polymorphism,
post-hoc, print, probability, prompt, prompt-engineering, pseudo-r2, pure-virtual, rag, random-forest, range,
readability, recursion, recursive, reduce, reference, reliability, rescue, rewrite, row-number, running-sum,
rvalue, sample, scale, score, secrets, separate, setter, shared_ptr, significance, silhouette, simplification,
size, sorted, specialization, stack-trace, standardscaler, starts_with, statistics, stats, stopwords, str_detect,
stream-extract, stringstream, structure, sub, summarize, super, survdiff, survfit, syntax, t-test, test,
testing, tfidf, three-table, tidy, tidyselect, tool-use, traceback, triage, try-catch, ttest_1samp, ttest_ind,
ttest_rel, tukey, turnover, two-params, union, unique_ptr, use_count, utf-8, value_counts, variables, version,
virtual, virtual-destructor, visualization, what, which.max, with, with-open, word-boundary, wraps, writing,
wss, yaml, yield, yield-from, ymd
```

**单例里的三类噪声（卷宗没点名的新发现，属"词表自身的口径缺陷"，与消费面无关）**：
1. **同义/异形对**：`error-handling` vs `error_handling`、`group_by` vs `groupby`、`group-by`（三种写法共存）、`cross_val` vs `cross-validation`、`feature_importance` vs `feature-importance`、`if-elif-else` vs `if-else` vs `if`、`operator==` 家族被拆成 5 个值。
2. **停用词级噪声**：`and, with, from, get, set, new, now, what, sub, log, data, int, bool, size, line, like, head`——这些是"命令里的词"被当成 tag，不是主题（同族还有出现 2 次的 `and-or`，说明连"布尔运算"这一件事都有两种粒度）。
3. **一次性的元数据**：`yaml, utf-8, mcp, rag, prompt, prompt-engineering, tool-use, multi-agent` 各 1 次，与 top20 的 `ai_judge(28)/open(12)` 同族却零复用 ⇒ **agent_dev 根内的标记没有统一词表**。

## 四、消费面取证（完成标准 ②：双轨＋0 命中输出）

### 4.1 轨 1：rg 属性读

```console
$ rg -n "\.tags\b" --type py .
.\tests\test_content_fuzz_pins.py:79:        assert p.tags == ["single_tag"]  # 不拆字符
```
`app.py`／`ui/`／`core/`／`scripts/` **生产侧零命中**（唯一命中在测试件）。

### 4.2 轨 2：AST（正则口径会漏 `["tags"]`／`tags=` 这类形态，故补第二轨）

```console
$ PYTHONIOENCODING=utf-8 python tmp/l924-24/ast_tags.py
py_files_scanned=150（排除 .git,.venv,__pycache__,logs,node_modules,tmp）
hits=6
core\loader.py                :23    NAME-STORE     ← `tags: list` 字段声明
core\loader.py                :187   NAME-STORE     ← 局部变量（卷宗锚点，行号未漂）
core\loader.py                :208   KWARG tags=    ← 装进 Problem（卷宗锚点，行号未漂）
core\loader.py                :208   NAME-LOAD
tests\test_achievements_branches.py :21 KWARG tags=  ← 测试夹具
tests\test_content_fuzz_pins.py     :79 ATTR-LOAD    ← 测试断言
```
两轨差额＝**0**（rg 轨的 1 条 AST 轨也有；AST 轨多出的都是 loader 自身的定义/搬运与测试夹具，无一在 `app.py/ui/core/scripts` 的读取位）。

### 4.3 透传面（本档补的否证性检查：整字典序列化会不会"间接读到"）

`Problem.to_dict()` 用 `asdict` ⇒ **tags 会跟着进字典**。三个调用点逐个读码：

| 调用点 | 是否读 tags 键 | 证据 |
|---|---|---|
| `core/judge.py:34-47 _to_problem_dict` → `:267` `judge()` | **否**，只喂 `_build_display(lang, pdict, …)`（`core/judge.py:252`） | `rg -n "_to_problem_dict\(" -B2 -A6 core/judge.py` |
| `core/ai_generate.py:35 _build_user_prompt` | **否**，模板只取 `difficulty/title/statement/expected_output` | `rg -n "_build_user_prompt" -A 22 core/ai_generate.py` |
| `ui/pages/language.py:134 / :298` | **否**（134 是把字典交给展示层，298 传给 `generate_variant`） | 同上两命令 |
| `core/ai_review.py:244-250/311/433-445` | **否**（逐个 `problem.get("title"/"statement"/"difficulty"/"rubric"/…)`，**无 `get("tags")`**） | `rg -n "problem\." core/ai_review.py` |

⇒ **"词表零读者"在值层面成立**：即使字典被透传，也没有任何一行的语义消费 tags。

### 4.4 唯一例外：`tags:` 的**行位置**有生产读者

```console
$ rg -n "tags" scripts/mark_r_judge_plain.py
scripts\mark_r_judge_plain.py:125:ANSWER_KEYS = ("title", "topic", "difficulty", "tags", "statement", "starter_code", …
scripts\mark_r_judge_plain.py:275:        if l.startswith("tags:"):
scripts\mark_r_judge_plain.py:279:        _fail("%s 找不到顶层 tags: 行，拒绝猜测插入位置" % path)
scripts\mark_r_judge_plain.py:281:        if lines[idx].rstrip("\r\n").strip() == "tags:":
scripts\mark_r_judge_plain.py:289:            _fail("%s tags 之后是缩进续行（%r），插入位置不明确" % (path, nxt.strip()[:30]))
```
⇒ 该脚本把顶层 `tags:` 当**插入锚点**：6 件 `content/paths/*.yaml`（无 tags 行）在它面前会走 `_fail` 分支，
且**任何"清洗/合并 tags 行"的动作都会改变它的插入位置**——这是词表唯一真实的生产侧依赖，也是案 B 的主要连带面。

## 五、三案（并列，**本档不选案**）

| 案 | 做什么 | 立刻得到的收益 | 代价／连带面 | 风险等级 |
|---|---|---|---|---|
| **A 接线消费**（推荐题曝光） | 在 `core/recommend.py:27-34` 的候选字典里带上 `tags`（现字段：lang/topic_slug/topic_title/problem_id/title/difficulty），让 `recommend()`／`cross_recommend()`（`core/recommend.py:66 / :224`）按"弱项技能词"过滤或加权；`ui/pages/dashboard.py:385 _render_cross_recommend` 展示理由 | 403 件×416 值从死数据变成推荐解释文本（"你 `groupby` 错 3 次"）；词表噪声会**当场影响排序**，逼出真实收敛需求 | 属**行为改动**：要新增/改判据测试、要防"单例噪声词主导曝光"（265 个单例意味着 63.7% 的词永远只有一题，无统计意义）；`tags` 进 prompt 面需复核是否外发给 LLM（现 `_build_user_prompt` 不含，接线后会含） | 中高（改决策行为，需另开单＋人工放行） |
| **B 词表二分收敛** | 把字段拆成 `judge_flags`（判定/形态类，受控小词表：`ai_judge/open/real-data/real-task/starter/comprehensive`）＋ `skills`（主题技能类，去单例、去停用词、合并异形对），403 件题批量迁移 | 消除 §3 三类噪声；"跨语言"只有 59 值的现实被承认，词表规模可缩到可审 | **改 403 件数据文件**（一次纯数据迁移，全库 diff）；🔴 连带 `scripts/mark_r_judge_plain.py:262-289` 的锚点逻辑（它只认 `tags:` 顶格行 ⇒ 改键名会让全部题"找不到锚点"直接 `_fail`，改判据属人工闸）；`tests/test_content_fuzz_pins.py:79` 等断言连带；l923-27/l924-25 的 csv 快照族**不受影响**（数据集与 tags 无关） | 高（大范围数据改动＋撞既有脚本判据） |
| **C 冻结现状并声明** | 不改数据不改行为：① 把本档的现值口径与"零读者"结论写进 `content/README`（或 loader docstring）；② 只补一条**不变量哨兵**——钉"题件 tags 覆盖率 100%／`content/paths` 6 件件型无 tags／字段是 list 非标量"这三条，**不钉 416/265 这类会随出题漂的绝对值** | 零风险、零 diff；把"是否继续维护词表"这个问题从隐性变显性；哨兵能挡住真正的退化（空 tags／标量 tags／给 paths 误加 tags） | 死数据仍是死数据（403 件的维护成本继续付）；哨兵若写成"值集合字面量"就是一枚自漂移桩 ⇒ 必须只钉形状/覆盖率 | 低 |

**共同前提（三案都成立的事实）**：词表当前对生产行为零影响（§4）、但 403 件仍在付维护成本、且 63.7% 的值是单例（§2/§3）。
**选案不属执行手授权**：A 改决策行为、B 动 403 件数据并撞 `mark_r_judge_plain` 判据、C 只是记账 ⇒ 本档交主班进待人工台账。

## 六、锚点复核（卷宗 12 类前提逐条）

| 卷宗前提 | 实测 | 命令 |
|---|---|---|
| `core/loader.py:187` 那条防御赋值 | **成立**，行号未漂，文本逐字相同 | `python -c "…enumerate(loader 行…)"` |
| `core/loader.py:208`「`tags=tags,`」 | **成立**，行号未漂 | 同上 |
| 409 件 / 唯一 416 / 单例 265 / 6 件无 tags | **四条全成立**（§1.1 三轨对平） | §1.1 |
| 旧口径 343/220 已漂 | **成立**（现值 416/265，差 +73/+45） | §1.1 |
| app/ui/core 生产码零读 `.tags` | **成立**，且加 AST 轨后仍成立（§4.2 差额 0） | §4.1/4.2 |
| rg 命中仅 loader 定义／tests／mark_r_judge_plain 写侧 | **部分成立**：`mark_r_judge_plain` 是**读 `tags:` 行位置**（不是写侧的语义读者），另 tests 侧共 2 文件（`test_content_fuzz_pins.py:79`／`test_achievements_branches.py:21`）＋`test_mark_r_judge_txn.py`/`test_mark_r_judge_plain.py` 把 `tags: ["io","starter"]` 当**夹具文本**。已在 §4.4 订正 | §4.4 |
| ai_judge×28 / spec×20 / pandas×14 / sklearn×13 | **四条全成立**（top20 表） | §2 |
| 只读、`content/` 与 `core/` 零 diff | **成立**（改动只有本新档＋索引 2 行，见 result「改动清单」） | `git status --porcelain` |

## 七、遗留问题（未在本档判定）

1. 265 单例是否有一部分本应与"出题形态"绑定（如 C++ 的 `operator<<` 家族被拆成 5 值）——需内容作者确认，不是普查能定的。
2. `recommend()` 若走案 A，弱项权重与 `topic` 权重会共线（`topic_slug` 已进候选字典），需先设计去共线口径。
3. 本档的 `tmp/l924-24/*.py` 两枚探针在 gitignore 的 `tmp/` 下，**不随提交入库**；若后续要复算，`scripts/` 不放探针（纪律：普查类脚本入库需单独立项）。
