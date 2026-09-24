# learning `test_count_is_22` 字面量桩处置裁决材料（l924-21，只出稿＋案序 · 零生产码改动）

> **卷宗**：`zcode-bridge/inbox/l924-21.task.md`（现址 `zcode-bridge/done/`）。上游依据＝`zcode-bridge/done/l923-26.result.md`
> 「`test_achievements.py:30 test_count_is_22` 与本桩取向冲突，交主班裁决：它把 `len(ACHIEVEMENTS) == 22` 钉成字面量，
> 所以**加一个成就即便两侧同步改齐，那条例仍会红**……删它属摘用例、改它属改判据」。
> 🔴 **本单只出裁决材料与案序，选案交人工**；未改 `tests/`、`core/`、`README.md` 任何一行。

## 〇、锚点复核（逐条实测，含 1 处否证）

| 卷宗前提 | 实测 | 命令 | 判定 |
|---|---|---|---|
| `tests/test_achievements.py:30` 是 `def test_count_is_22(self):` | `:30 def`、`:31 assert len(ACHIEVEMENTS) == 22` | `rg -n "def test_count_is_22\|len(ACHIEVEMENTS) == 22" tests/test_achievements.py` | ✅ 零漂移 |
| `:26 test_all_have_unique_ids`、`:33 test_all_have_category` | `:26`、`:33` 逐字命中 | 同上换名 | ✅ 零漂移 |
| 「与 l923-26 白名单桩（**15 条**登记面）相互作用」 | 🔴 白名单 `_NON_ID_LITERALS` 现值 **14 条**（AST 数 `frozenset` 元素），同文件 `:52` 的注释也写着"（15 条，逐项标身份）" | `python -c "import ast,pathlib;src=pathlib.Path('tests/test_achievements_id_reconcile.py').read_text(encoding='utf-8');m=[n for n in ast.parse(src).body if isinstance(n,ast.Assign) and getattr(n.targets[0],'id','')=='_NON_ID_LITERALS'][0];print(len(m.value.args[0].elts))"` | ❌ 否证 ⇒ 进 §六-1 待订正 |
| 「加一个成就……那条例仍会红」 | ✅ 成立，但**"两侧同步改齐"低估了同步面**：实测是 **4 处必改 ＋ 2 处条件性**（§二） | §二逐条命令 | ⚠ 口径修正 |
| （新发现）这条字面量桩**已被另一条在册桩当设计依据引用** | `tests/test_readme_reconcile.py:12-14` 的 docstring 原文：「『徽章 22 同样无钉』→ 现役已有 `tests/test_achievements.py::test_count_is_22` 钉 `len(ACHIEVEMENTS) == 22`……**两条都是代码侧等值**」 | `sed -n '9,16p' tests/test_readme_reconcile.py` | 🔴 删例会抽掉 l923-12 书面推理的一根柱子（案甲的连带成本，见 §三-甲） |

## 一、现值复算（完成标准②，全部内联命令）

| 量 | 现值（HEAD `ed63884`） | 现取命令（cwd `D:/code/learning-system`） |
|---|---|---|
| `len(ACHIEVEMENTS)` | **22** | `PYTHONIOENCODING=utf-8 python -c "from core.achievements import ACHIEVEMENTS as A;print(len(A))"` |
| category 分布 | `streak 4 / special 7 / language 8 / path 3`（合计 22） | 同上换 `Counter(a.category for a in A)` |
| 定义面 ⇄ 解锁面 ⇄ 白名单 | reconcile 族定向 **30 passed**；白名单 14 条 | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_achievements_id_reconcile.py -q` |
| README 对外口径 | `README.md:61`「**成就系统**：22 枚徽章，涵盖打卡、语言、路径与特殊成就。」 | `sed -n '61p' README.md` |
| README 侧门禁 | `test_readme_reconcile.py:43` `("徽章数", _BADGE_PAT, lambda: len(ACHIEVEMENTS))` ⇒ **抽数 ⇄ 实值动态对账**，且 `_claimed` 要求正则**恰好命中 1 次**（改写到别处/删句＝门禁空转即红） | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_readme_reconcile.py -q` → 5 passed |
| 现状基线（完成标准③） | `tests/test_achievements.py -q` → **21 passed，rc=0** | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_achievements.py -q` |
| 本仓"钉死 vs 下界"取向先例 | `tests/test_scripts.py` 里 `paths` 已由 l924-14 从 `>= 3` **收紧为 `== 6`**，而同桩 `total_problems >= 399` 注释自述"**刻意保留下界**" | `rg -n "total_problems\] >=|paths.*== 6|l924-14" tests/test_scripts.py` |

⇒ **本桩的定性正卡在两条先例中间**：成就表既像"仓库形态快照"（受结构约束：8 条 language 成就对 5 种语言、3 条 path 成就对 6 条主线），又像"会增长的体量"。这个判断**属规划域**，见 §五。

## 二、加一个成就的真实同步面（实测，逐条带行号）

必改 4 处：
1. `core/achievements.py:21-49` 定义面 `ACHIEVEMENTS` 追加一条（`rg -n "^ACHIEVEMENTS" core/achievements.py`）。
2. `core/achievements.py:58-151` 解锁面加对应字面量 ⇒ 否则 `test_achievements_id_reconcile.py` 的
   「定义面每个 id 都在 `check_achievements` 字面量里」当场红（`:125` 那条断言）。
3. **`tests/test_achievements.py:31` 的 `== 22`** ⇒ 🔴 **纯字面量、不看任何外部实值，必红**（这就是本案要裁决的那道"人工税"）。
4. `README.md:61` 的「22 枚徽章」⇒ 不改则 `test_readme_reconcile.py:43` 红（它拿 `len(ACHIEVEMENTS)` 现值对账）。

条件性 2 处：
5. 新增 `category` 值 ⇒ `tests/test_achievements.py:34-36` 的 `valid_cats` 白名单要加。
6. 新增**非 id 字面量**（新事件名/新 dict 键/新文案）⇒ `_NON_ID_LITERALS` 要登记（现 14 条），由
   `test_白名单不得吞掉真成就id_且每项都仍在源码里()`（`:132`）双向把守。

⇒ 三案争的**只是第 3 处**：第 1、2、4、5、6 处都有动态桩兜着（改了实值就会提醒），**只有第 3 处是"常量表自身的形状哨兵"**。

## 三、三案对比（完成标准：各成节）

### 案甲：删掉 `test_count_is_22`
- **改动面（实测）**：`tests/test_achievements.py` 净删 3 行（:30-31＋空行），**外加**必须回改
  `tests/test_readme_reconcile.py:12-14` 的 docstring（它把本桩写成"代码侧已有等值钉"的依据）——
  不改就是**注释与盘态不符**（本仓同类问题已被 l924-15/16 两单专门收口）。
- **风险（实测推论）**：删后"成就表被整体缩水"只剩 README 侧动态对账兜底 ⇒
  **同时删成就＋改 README 数字 ⇒ 全绿**（`test_all_have_unique_ids`/`test_all_have_category`/reconcile 两侧同步都成立）。
  即：第 3 处是**唯一不依赖外部文本的自洽哨兵**，删掉它就没有任何桩能区分"22 条被有意改成 11 条"与"README 跟着改了"。
- **收益**：加成就少改 1 处（省一次红名往返）。
- **纪律冲突**：l923-26 原话「删它属**摘用例**」⇒ 超出执行手授权，只能交人工。

### 案乙：改区间断言（推荐形态为**下界** `>= 22`，不是双端区间）
- **改动面**：`tests/test_achievements.py:31` 一行（`== 22` → `>= 22`）；同步面 4 处**不变**（README 侧仍钉等值口径）。
- **风险**：①与本仓最新取向**相反**——l924-14 刚把 `test_scripts.py` 的 `paths >= 3` **收紧**为 `== 6`，理由是"钉死才拦得住整目录改名/丢失"；
  ②下界只挡净减，**挡不住"加了却不更 README"**（那条仍由 `test_readme_reconcile` 管，所以不致命）；
  ③下界本身要随成就增长人工上调，否则退化成永绿（`>= 22` 在 22 条时与 `== 22` 等强，加到 23 条后就永久失去上界）。
- **收益**：加成就不再红 ⇒ 但也**不再有提醒**去回看常量表（这正是字面量桩的作用）。
- **纪律冲突**：l923-26 原话「改它属**改判据**」⇒ 同样只能交人工。

### 案丙：保留字面量 ＋ 把"加成就须同批改"写进 plan.md
- **改动面（最小）**：`tests/` 零改动；`plan.md` 追加一节（先例：plan.md 的 §「补题口径」正是"补题类改动的**唯一授权口径落点**"，
  而 `l922-128` 曾因该规范**未钉**整单 partial）。建议措辞含 §二 的 4＋2 处清单与 `test_count_is_22` 的红是**预期行为**（不是回归）。
- **风险**：文档约定无自动哨兵 ⇒ 靠"红名即提醒"（本桩自己就是哨兵，红了自然会去看）；另需防"后人把这条红当回归去改坏" ⇒ 措辞要点名。
- **收益**：零判据改动、零用例损失；把 l923-26 悬着的"交主班裁决"变成一句可读的授权口径。

### 三案共同否决项（🔴 不要顺手做的）
- 不改 `test_achievements_id_reconcile.py`（它 `:22` 已明说"**不锁 22 字面量**，个数一律现取"）——两桩取向**本就互补**：
  一个管"名字对不对得上"，一个管"个数变没变"。**卷宗说的"取向冲突"实测不成立**（见 §四）。
- 不为了"少一处字面量"把 22 挪进 `core/version.py` 或 config ⇒ 那会把断言变成自我循环（常量对常量），**哨兵当场失效**。

## 四、与白名单桩的相互作用（卷宗点名项，实测结论）

- 白名单 `_NON_ID_LITERALS`（现 **14** 条）只作用在**解锁面的字面量集合**上：`unknown = lits - _NON_ID_LITERALS`（`:84`），
  它**完全不读** `len(ACHIEVEMENTS)` ⇒ 与 `test_count_is_22` 无共享变量、无先后依赖。
- 唯一交集是"加一个成就"这个**动作**同时触到两者（§二 第 2 步与第 6 步）：若新成就的实现顺手引入了新事件名/dict 键，
  白名单会要求登记（刻意的噪声，`:53-55` 注释自述），**这条红与计数红相互独立**、各自只提醒一件事。
- 🔴 因此 l923-26 的"与本桩取向冲突"应**降级表述**为："两桩对『个数』的取向不同（一个现取、一个钉死），但互不遮蔽、互不解锁"——
  不构成必须删/改其一的理由。这条改法交主班在台账里对 l923-26 加注（done 档不回改）。
- 三道"防白名单吞真 id"的自证桩（`:132` 等）现值全绿（reconcile 族 30 passed）⇒ 本案**不需要**动它来换取任何好处。

## 五、案序（🔴 选案交人工；执行手建议）

1. **案丙**（建议首选）：零判据改动、保住唯一自洽哨兵、成本＝plan.md 一节。
2. **案乙**（次选）：仅当下界语义被人工认可（须同时接受"它挡不住增长后的漂移"）。
3. **案甲**（**不建议**）：省一次红名往返，代价是失去常量表自身的形状哨兵，且连带要回改另一条在册桩的 docstring。
4. 若人工选丙，请一并处置 §六-1 那条"15 条 vs 14 条"注释漂移（同一族、同一次提交最省）。

## 六、待订正清单（交主班进台账，本单未改他班在册档）

1. 🔴 `tests/test_achievements_id_reconcile.py:52` 注释「不是成就 id 的字符串常量（**15 条**，逐项标身份）」⇄ AST 实数 **14 条**；
   本派单正文的"白名单桩（15 条登记面）"抄的正是这个过期读数。复算命令见 §〇 第 3 行。建议改为"条数不写死、由 `:132` 自证桩把守"（照纪律档 §十.4：注释别写会被判据排除的字面串/会被自己推走的数）。
2. `zcode-bridge/done/l923-26.result.md` 的"与本桩取向冲突"表述应降级为"对个数的取向不同但互不遮蔽"（§四）；
   同档"两侧同步改齐仍会红"应改成"**四处必改＋两处条件性**"（§二）。done 档不回改 ⇒ 请台账加注。
3. 索引件「git 入库」列整列过期（l924-18 已登记，本单不重复计数）。

## 七、本单没做的 ＋ 复算配方

**没做**：未跑全量套件（并行纪律 §四.2 只读位；只按完成标准③跑了 `tests/test_achievements.py` 定向基线 21 passed）；
未改 `tests/`/`core/`/`README.md`/`plan.md` 任一行；未新增用例（卷宗产出面只点名 `docs/insights/*.md`）。

```bash
cd D:/code/learning-system
# 1 现值计数与分布（完成标准②）
PYTHONIOENCODING=utf-8 python -c "from core.achievements import ACHIEVEMENTS as A;from collections import Counter;print(len(A),dict(Counter(a.category for a in A)))"
# 2 四处同步面锚点
rg -n "^ACHIEVEMENTS|^def check_achievements" core/achievements.py
rg -n "def test_count_is_22|len\(ACHIEVEMENTS\) == 22|valid_cats" tests/test_achievements.py
sed -n '61p' README.md; rg -n "徽章数|_BADGE_PAT" tests/test_readme_reconcile.py
# 3 白名单条数（AST 轨）＋注释口径（正则轨）并列对
python -c "import ast,pathlib;src=pathlib.Path('tests/test_achievements_id_reconcile.py').read_text(encoding='utf-8');m=[n for n in ast.parse(src).body if isinstance(n,ast.Assign) and getattr(n.targets[0],'id','')=='_NON_ID_LITERALS'][0];print('AST 轨',len(m.value.args[0].elts))"
rg -n "条，逐项标身份" tests/test_achievements_id_reconcile.py
# 4 定向基线（完成标准③；单跑 21 passed，三族合跑现值 56 passed rc=0）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_achievements.py tests/test_achievements_id_reconcile.py tests/test_readme_reconcile.py -q
# 5 闭合哨兵（完成标准④，本档同批自登）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q
```
