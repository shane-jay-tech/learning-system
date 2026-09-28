# 派单侧「点名文件投产前」检查清单＋落点缺陷族盘点（l927-28，2026-09-29｜零改模板本体）

- 任务：l927-28（cwd `D:\code\learning-system`，软预算 ≤25 分钟）
- 性质：**清单只作为新档落 `docs/insights/`**（规划素材库）。
  `docs/night-plans/PROTOCOL.md`、`scripts/night_brain.py`（含 `PREFLIGHT_PROBE` / `render_task_file` / `validate_task`）、
  `zcode-bridge/prompts/*.md`、`zcode-bridge/scripts/anchor_health.py`／`inflight_probe.py`
  **一律未改**——那属规划班写权域；本档 §四 只给「建议追加行」文本，逐字可粘，粘贴与否由规划班定。
- 上游：l922-08 §执行摘要＋§遗留问题 1、l922-09 §执行摘要＋§遗留问题 1、l922-10 §执行摘要＋§遗留问题 1、
  l922-104 §证据 1＋§遗留问题 1。
- 全部读数为 2026-09-29 现取；命令原文随每条读数内联，主班可原样复跑。

## 一、缺陷族盘点：卷宗说「4 例」，磁盘实况是 **4＋2＋1**

任务书点名的 4 例（l922-08／09／10＋104）**全部现读复核成立**，但按磁盘实取，同族件不止 4 枚，
且 4 枚内部其实是**两种不同的失效形态**。下面把形态拆开——清单要防的是形态，不是枚数。

### 1.1 形态 α：把「已存在的 tracked 文件」写成「产出新文件」（照字面 Write 即清库）

| 单号（引节号） | 卷宗点名的产出件 | 当年 result 申报的开工前状态 | 2026-09-29 磁盘现值 |
|---|---|---|---|
| l922-08 §执行摘要 :20-24／§遗留 :106 | `tests/test_recommend_review_state.py` | 已存在且 tracked，**119 行／5 条既有用例** | **274 行／14 例**（`git ls-files` 命中） |
| l922-09 §执行摘要 :25-27／§遗留 :109-111 | `tests/test_achievements_branches.py` | 已存在且 tracked，**104 行**（d914-68 T6 三条分支补测） | **279 行／12 例** |
| l922-10 §执行摘要 :12／§遗留 :106 | `tests/test_ai_review_strategy.py` | 已存在且 tracked，**7 例且主题不同族**（`_build_review_system_prompt` 策略选择） | **414 行／25 例** |
| 🔴 **n922-10 §执行摘要 :12／§验收 :102（卷宗未计入）** | `docs/insights/learn-test-baseline-20260921.md` | 已存在且 tracked，**是另一枚单 l922-03 的交付物**（commit `0564042`） | **158 行**，§一~§五 完整保留＋§六 追加仍在（最近提交 `0dac1f7`） |

- 四枚当年都按「同文件追加」自救成功，diff 删除数为 0（l922-08 `+155/-0`、l922-10 `+177/-0`、n922-10 `+74/-0`）。
- 🔴 **爆炸半径在长**：同一批件今天的既有内容量约为当年的 **2.3 倍**（119→274、104→279、7 例→25 例）。
  ⇒ 今天再投同样形状的单、再被子班照字面 Write，清掉的行数比 09-21 那次多一倍——**这单不是历史包袱，是现役风险**。
- n922-10 那枚还多一层：**踩的是「别的单的交付物」**，不是自己族的前手件。⇒ 清单必须查**归属**（§三 步 3），
  只查「存不存在」不够。
- l922-10 §遗留 1 建议的改名候选 `tests/test_ai_review_cache.py` **现仍不存在** ⇒ 该出口今天依旧可用（`ls` 实测 MISSING）。

### 1.2 形态 β：任务书把「盘上不存在的东西」写成「原有／已存在」（虚构锚点）

| 单号（引节号） | 卷宗断言 | 磁盘实况（当年） | 2026-09-29 现值 |
|---|---|---|---|
| l922-104 §证据 1／§遗留 1 | 完成标准③「缓存命中路径**原有**例」 | `grep -rn "_export_cache" tests/` **0 命中**＝不存在该例 | 该格已由 **l927-55** 补上 `tests/test_export_cache_hit_path.py`（commit `5ea5995`）；生产侧同文件行号已从 `:213/:214` 漂到 **`:336/:338`** |
| 🔴 l922-103 §遗留 1（卷宗未计入） | 把 `dashboard :294` 当成「有 except、缺测试」 | 该处**无异常处理**，唯一 except 在点击路径 `:321` | 已由 `b575e0d`（l923-07）＋`38ad3bb`（l924-01）修掉；**l927-30 实测并登记「前提已不成立」** |
| ✅ l922-101 :21（阴性对照，非缺陷） | 产出 `tests/test_dashboard_event_failures.py` | 开工前 `ls` 确认**不存在**，按新建执行 | 现存在 **1144 行／25 例**（l922-103 之后走追加，未再被整写） |

⇒ **对卷宗口径的一处收窄**：「本批已知 4 例」这句不成立——磁盘现值是同族 **6 例真实缺陷**
（α 型 4 枚：l922-08／09／10／n922-10 ＋ β 型 2 枚：l922-104／l922-103）**另加 1 例阴性对照**（l922-101）。
l922-104 虽被卷宗算进「4 例」，但它根本不是 α 型；而 α 型里被漏掉的 n922-10 恰是后果最重的一枚（覆盖他单交付物）。
按实况登记，不判卷宗 failed。

## 二、防再发的真正缺口：**模板里接了线，现役投递路径没走那根管**（实测）

这条是本单最值钱的发现，先于清单本身：

```
$ rg -l "前置探针" zcode-bridge/inbox/*.task.md | wc -l      → 0   （inbox 任务书共 164 份）
$ rg -l "前置探针" zcode-bridge/done/*.task.md | wc -l       → 0   （done 归档共 3427 份）
$ rg -l "前置探针" zcode-bridge/pending/ --glob "*.task.md"  → 0   （待放行 72 份）
$ rg -l "inflight_probe.py --task-file" D:/code             → 仅命中脚本本体 zcode-bridge/scripts/inflight_probe.py
```

而 `scripts/night_brain.py` 里**确实有**这套件：`PREFLIGHT_PROBE` 常量（:575，注释写明「k922-40 三条硬规则之二；2026-09-22」，
「固定追加在任务书正文尾部，让每一份投递都自带动单前先跑 porcelain 探针」）在 `render_task_file()`（:585→:596 `{PREFLIGHT_PROBE}`）插值，
调用点在 :1759。`docs/insights/pipe-executor-3rules-qoder-draft-20260922.md:34` 也已写「投递侧已接线」。

**但盘上 0/3427＋0/164＋0/72 份任务书带这一段。** 反证「09-22 之后没人用过该函数」也不成立：
inbox 里有 `created: 2026-09-28T01:20:30` 的 l927 批。再取一条磁盘证据说明原因——
现役任务书骨架里那句 `## 背景与锚点（执行时先复核锚点仍有效；有漂移则按磁盘实况修正并留痕）`
在**任何 .py 生成器里都查不到**（`rg -l "<该串>" --type py` 只命中 2 枚测试件的引用注释：
`learning-system/tests/test_content_difficulty_pins.py`、`test_hr_dataset_determinism.py`），
而 `scripts/llm_call.py:300-321` 自己那份写盘骨架（`## 任务 / ## 完成标准 / ## 禁止事项`，`max_minutes: 30` 写死）
与盘上件（`max_minutes: 25`、多出「## 产出」「## 软预算」两节）**也对不上**。

⇒ 实况结论（只述形不裁决）：**现役批次的任务书由规划班手写落盘，`render_task_file` 与 `llm_call` 两条渲染路径都没经过**。
所以「往模板常量里补一行」这类修法**对现役批次零效果**——防再发必须落在
①规划班自身的出稿提示词／检查动作，或 ②投产闸（`approve`）侧的机械校验。§四 的建议追加行就是按这两处给的。

## 三、派单侧检查清单（**8 步，α／β 两型都覆盖**；每步：命令原文 → 判读 → 命中处置）

> 命名口径：本节「点名文件」＝任务书「## 产出」段与「## 完成标准」段里出现的一切路径；
> 「投产前」＝`night_brain.py approve` 放行移入 `inbox/` 之前（PROTOCOL §投产前人工放行那条闸）。

**步 1｜存在性（α 型主闸）**——两条判据并用，单用任一条都有盲区（全部实测）：

```
rg --files <相对点名路径>        # 在目标仓库根下跑；含「已落盘但未入库」的新档
git ls-files <相对点名路径>      # 含「已跟踪但被 .gitignore 覆盖」的件
ls -1 <目录>                     # ignore 域兜底
```
| 判据 | 能捞到什么 | 捞不到什么（实测反例） |
|---|---|---|
| `rg --files` | 未入库新档：本班刚产的 `docs/insights/l927-25-topicnum-adjudication.md` → 命中 1，同路径 `git ls-files` **查无** | 被 ignore 的目录内文件：`rg --files data` → **0**，而 `ls data/*.db` → 1 |
| `git ls-files` | 「已跟踪＋被 ignore」叠加态：learning-system `git ls-files data` → **1**（`data/progress.db`，`.gitignore:7 data/*.db` 挡不住已跟踪件） | 未入库新档（上一行反例即它漏的） |

⇒ **旧档口径要订正**：l922-08 §遗留 1 与 l922-09 §遗留 1 建议的是「投递前跑 `git ls-files` 查重」。
本会话工作树里有大批**未入库交付物**（brief §C 点名 kaoyan 15 单约 150 枚零 commit），
`git ls-files` 对这一整类**全瞎**；`rg --files` 才捞得住。两条一起跑。

**步 2｜主题匹配（β 型前置／l922-10 那类的真因）**——存在只说明不能 Write，不说明该怎么处置：

```
rg -n "^\"\"\"|^def test_|^class " <点名文件> | head -20
```
读首段 docstring 与用例名。既有用例与本单主题**同族** ⇒ 走「同文件追加」；**异族** ⇒ 换名
（l922-10 实况：点名件里是 `_build_review_system_prompt` 策略选择 7 例，本单主题是缓存层，异族）。

**步 3｜归属核对（n922-10 那类的真因）**：

```
git log --oneline -3 -- <点名文件>
git log -1 --format=%s <点名文件> | rg -o "[a-z]+9[0-9]{2}-[0-9]+"
```
命中**别的单号** ⇒ 该件是别单交付物，本单不许整写；处置只有「追加」或「换名」两条，且 result 要点名被占用的单号。

**步 4｜把冲突处置写回任务书「## 产出」字段（不是写进备注）**——三选一的措辞：
- `产出：在 <file> 内追加用例（该件开工前已存在且 tracked，<N> 行／<M> 例，属 <单号> 交付物；禁止整写）`
- `产出：<新名>（原点名 <file> 已被 <单号> 占用且主题异族；<新名> 现不存在，实测 rg --files 0 命中）`
- `撤单／改判：<断言的既有内容> 盘上不存在（rg -n <符号> tests/ → 0 命中），本单前提不成立`

**步 5｜β 型主闸：完成标准里「原有例／既有 X」逐条点名**：

```
rg -n "<完成标准点名的符号或用例名>" tests/      # 0 命中＝该条断言虚构
```
l922-104 那枚就是这么发现的（当年 `grep -rn "_export_cache" --include=*.py .` 只命中 `ui/pages/dashboard.py` 4 行、tests 0 命中）。

**步 6｜行号锚点双验（防行号漂移，本会话已踩两次）**：

```
sed -n '<NN>p' <path>            # 逐字对原文，不只看文件存在
```
本档已实测三处漂移：`ui/pages/language.py:370→:471`（l922-05 引）、`ui/pages/dashboard.py:213/:214→:336/:338`（l922-104 引）。
⇒ 存在性过了不等于锚点有效；`anchor_health.py --all` 现值报「行号锚点 有效 11／漂移 0／漂移率 0.0%」，
但那是它自己的解析口径，**别把工具绿当免检**（本会话实测：同一次 `--all` 对 10 枚 l927 在库单报「产出存≥1」，
而我按「## 产出」段独立解析的结果是 **10/10 点名文件均不存在**——两口径不吻合，派单前以直接实测为准）。

**步 7｜查本单是否已被前手消解**（防投「已修完」的旧单，l927-30 型）：

```
git log --oneline -S"<缺陷关键串>" -- <受影响文件>
rg -n "<卷宗说要改的字样>" <文件>          # 0 命中＝已消解
```
l927-30 实测「要订正的误判已在盘上被 `b575e0d`／`38ad3bb` 修掉」；l927-53 同样实测「要订正的字样已由 `1bafa0c` 删除」。
⇒ 命中即撤单或改判，别让它占一个执行班轮次。

**步 8｜产出落 `docs/insights/` 时加一条索引闭合提醒**：
本仓 `tests/test_insights_index_closure.py` 判 A（磁盘 .md 数）== B（索引表 `^| docs/insights/` 条目数）。
现值 **A=B=132**；新档落盘即 A=133 ⇒ **该桩必 2 红**，属预期中间态。
⇒ 任务书「## 产出」若点名 insights 档，应在同段加一句「索引由主班单点代登，执行班禁自登」——
本会话已两路（l927-52／l927-57）因此踩红，写明即免踩。

## 四、建议追加行文本（**本单一行未落**，逐字供规划班取用）

1. **`docs/night-plans/PROTOCOL.md`**（§投产前人工放行 那条之后，纯新增一行）：
   > `- **放行闸前置检查（l927-28 建议追加）**：`approve` 移件入 inbox 前，对每份任务书「## 产出／## 完成标准」点名的路径跑
   > `rg --files <path>` ＋ `git ls-files <path>` 双判据；任一命中即要求把「产出」字段改写为「同文件追加／换名／撤单」三选一措辞，
   > 并附 `git log --oneline -3 -- <path>` 的归属读数。判据口径见 `docs/insights/l927-28-precheck-list.md` §三。`
2. **`scripts/night_brain.py:validate_task()`**（`for marker in BODY_REQUIRED` 那段之后，机械可判、零主观）：
   > ```python
   > # 建议追加（l927-28）：产出名占用闸——α 型落点缺陷的机械拦法
   > for p in _named_outputs(body):            # 取「## 产出」「## 完成标准」两段里的 *.md/*.py/*.yaml 路径串
   >     if (Path(cwd) / p).exists():
   >         problems.append(f"产出名已被占用: {p}（须改写为同文件追加/换名/撤单，见 l927-28 §三 步 4）")
   > ```
   > 说明：`validate_task` 现值已查 id／cwd 存在性／`max_minutes` 越界／正文长度／`完成标准`＋`禁止` 两段／`anchors` 非空，
   > **唯独不查产出路径是否已存在**——这一格是空的，补在这里比补在提示词里硬。
3. **`scripts/night_brain.py:PREFLIGHT_PROBE`**（常量内补一句；⚠ 单补此行对现役批次无效，见 §二）：
   > `「MISSING＝磁盘不存在；CLEAN 不等于可新建——CLEAN 也可能是『已被他单 tracked 占用』，须再跑 rg --files 归步 1。」`
4. **`zcode-bridge/scripts/inflight_probe.py`**（新增第 4 态，或至少在结论行补一列）：
   > 现状实测——对 l922-08 那枚的事故对象 `tests/test_recommend_review_state.py`，探针给 **`CLEAN` → verdict CLEAR → rc=0**；
   > 对本班刚落的未入库档 `docs/insights/l927-25-topicnum-adjudication.md` 给 **`DIRTY ??` → rc=1**。
   > ⇒ 探针按设计只判「在途编辑」，**把最危险的「已存在且干净的他单既有件」归入 CLEAN 放行**。
   > 建议：`--paths` 之外加 `--expect-missing`（声明「本单产出＝新建」的路径集），其中任一存在即 rc=1。
5. **`zcode-bridge/scripts/anchor_health.py`**：产出锚点现按「尚未产出属正常」计（`--all` 汇总行口径：存在 168／缺失 165）。
   > 建议：把「**产出锚点已存在**」从正常项拆出单列告警，并在 `--check` 里可选纳入（默认关，避免现役批一次全红）。
6. **执行班提示词**（`zcode-bridge/prompts/executor.md` ／ `docs/qoder/2026-09-18-executor-automation-prompt.md`）：
   > `开工前对点名产出跑 §三 步 1-3；命中即改「同文件追加」，收口用 git diff --numstat 证明删除行为 0（本会话 4 枚 α 型全靠这招未降 status）。`

## 五、声明（判据③）

- 本单**未改任务模板本体**：`scripts/night_brain.py`（`PREFLIGHT_PROBE`／`render_task_file`／`validate_task`／:1759 写盘点）、
  `docs/night-plans/PROTOCOL.md`、`zcode-bridge/prompts/*.md`、`scripts/llm_call.py`、
  `zcode-bridge/scripts/anchor_health.py`／`inflight_probe.py` 全部只读跑命令，零编辑。
- 未改任何生产码与在册判据；未撤 `test_sql_roworder_fragile.py`／`test_paths_order_consistency.py` 两枚 strict-XFAIL 桩；
  未跑全量套件；零 git 写；未自登 learning 索引件。
- 信箱侧只动本单自己的：`claims.log` 两行（走 `claims_writer.py`）、`inbox/l927-28.task.md` → `done/`、`outbox/l927-28.result.md`。
- §一 表格里的「当年状态」引自各单 done/ result 的**节号＋行号**（已现读，非凭记忆）；「磁盘现值」全部本会话现取，命令内联。
