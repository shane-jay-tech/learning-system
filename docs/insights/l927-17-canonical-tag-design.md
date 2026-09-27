# l927-17 `canonical_tag()` 只读别名层设计 ＋ 映射方向裁决材料

- 班次：`qoder-executor-20260927-1820-learn47`（波次 22 只读位），现点 2026-09-27T18:1x（本机 `date`）
- 仓现值：HEAD `bbceef5`、开工 porcelain 0 行
- 锚点：`zcode-bridge/outbox/20260925-154244-222f.result.md` → **实取于 `D:\code\zcode-bridge\done\20260925-154244-222f.result.md`**（18,241 B；路径搬家非缺陷，按 brief §3a）
- 姊妹档（本设计据以对齐，均只读引用）：`D:\code\learning-system\docs\insights\learn-content-tags-census-20260924.md`、`D:\code\learning-system\docs\insights\learn-tag-vocab-spec-20260925.md`
- 判据面：**「折向语言原生 API 名 vs 折向分隔符描述名」是内容口径裁决，本班不签**（§3 写成给人拍的题）。本班未改任何 yaml、未改任何测试基线、未写任何库。
- 生产库：本班**全程未打开**（本单取证只读 `content/**.yaml` ＋ 码面），主库 size＋sha8 见「验收」末条。

---

## 0. 盘上现值复核（锚点逐条复算，含两处订正）

复算命令＝`learn-tag-vocab-spec-20260925.md` §一 那段配方，本班原样重跑（`D:\code\tmp\qoder-executor-20260927-1820-learn47\tag_probe.py`）：

| 锚点读数 | 本班现取 | 判定 |
|---|---|---|
| `content/**/*.yaml` 409、题件 403、路径件 6 | 409／403／6 | ✅ |
| tags 唯一值 416／出现 898／单例 265 | 416／898／265 | ✅ |
| 词表基线指纹 `bfbf832d88a75f3d` | **同值** | ✅ **词表自 09-25 起零漂移**（本单一切设计都还建在同一份词表上） |
| spec 口径重复组 7／涉及值 15／出现 33 | 7／15／33 | ✅ |
| 222f 的 A 级 3 簇 6 值、B 级 5 簇 11 值 | A：`error-handling|error_handling`、`feature-importance|feature_importance`、`group-by|group_by`（3 簇 6 值）；B：加 `effect-size|effectsize`、`if-else|ifelse` ⇒ 5 簇 11 值 | ✅ |
| 「涉及 26 个 yaml 文件、26 个改写点」 | **口径要订正**（§1）：26 是「B 级 5 簇**两侧全部**出现次数＝并集文件数」（每簇每次出现恰好落在不同文件），**不是**任一方向的改写量。真按某个方向折：**改写点 9～17 处／文件 9～17 个** | ⚠️ 订正 |
| 「`tests/test_content_census_*` 系列基线需同批重取」 | **不成立**（§2）：6 件 census 测试里 `rg -n tag` **0 命中**，它们钉的是题数／topic 集合／difficulty 直方图／judge_mode／hints 缺失名单，**没有一条读 tags** | 🔴 否证 |
| 「不可自动合并：27 对近邻」 | 按锚点自述规则字面复算＝**25 对**；锚点表点名的 15 对里有 6 对不被该规则抓到（`glm/lm`、`map/map2`、`fstream/ifstream`、`ifstream/ofstream`、`fstream/ofstream`、`in/int`）⇒ **27 不可复算**，散文计数不稳定（设计结论见 §4 D-4） | ⚠️ 订正 |
| 「10 个同 token 家族」 | 锚点自己只列出 9 个家族名；按「首段同形 ≥3 写法」口径复算＝**5 个**（`data`/`feature`/`if`/`pivot`/`ttest`）；按点名 9 族逐一验在世＝每族 ≥3 在世值 ⇒ 计数同样不稳定 | ⚠️ 订正 |

> 这三处「计数对不上」不是锚点算错这么简单——它正是**别名层必须把保护名单做成数据而不是文档数字**的理由（§4 D-4）。

---

## 1. 26 点影响面对照（逐簇实测，含"两侧"与"单向"两种口径）

B 级 5 簇的文件／出现分布（`tag_files2.py`）：

| 簇（去分隔符同形键） | 现值（各值出现次数） | 出现合计 | 涉及文件 | 取向A 折成 API 真名 → 改写点 | 取向B 折成描述名 → 改写点 | 取向C 各簇多数派 → 改写点 |
|---|---|---|---|---|---|---|
| `groupby` | `groupby`(10) `group-by`(3) `group_by`(1) | 14 | 14 | 4（`group-by`3＋`group_by`1） | 11（`groupby`10＋`group_by`1） | 4 |
| `ifelse` | `if-else`(3) `ifelse`(2) | 5 | 5 | 3（`if-else`，多数派被改成少数派） | 2（`ifelse`） | 2 |
| `effectsize` | `effectsize`(2) `effect-size`(1) | 3 | 3 | 1 | 2 | 1 |
| `errorhandling` | `error-handling`(1) `error_handling`(1) | 2 | 2 | 1 | 1 | 1 |
| `featureimportance` | `feature-importance`(1) `feature_importance`(1) | 2 | 2 | 1 | 1 | 1 |
| **合计** | 11 个现值 | **26** | **26** | **10 处／10 文件** | **17 处／17 文件** | **9 处／9 文件** |

（逐簇明细可现取：`dir_breakdown.py`。要点：**「26」是两侧并集**，任一方向真落地只改 9～17 处；且 `ifelse` 这一簇上"多数派（`if-else` 3 次）"与"语言原生 API 名（`ifelse`，R 的函数真名）"**方向相反** ⇒ C 与 A 在这一簇分叉，这正是 §3 Q2 的难点。）

结构事实（决定改写 mechanics 的难度，全部实测）：
- **1 次出现＝1 个文件**：26 次出现落在 26 个不同文件，**没有任何题件在同一 `tags:` 行里出现两枚簇内值**（同件重复值题件数 **0**）⇒ 原地改写是「一文件一行一处」的最简形状，无跨行合并。
- **块状（多行）`tags:` 写法题件数＝0** ⇒ 全部是 flow 风格单行，改写不涉 YAML 结构变换。
- 反面（原地改写真正的风险）：`scripts/mark_r_judge_plain.py` 把顶层 **`tags:` 行当插入锚点**（`:262 _insert_line_after_tags`、`:275 if l.startswith("tags:")`、`:125 ANSWER_KEYS` 含 `"tags"` 并在 `:396-398` 做"除 judge_mode 外字段不得变化"的 fail-closed 比对）。⇒ 只要改写**保持键名与行形态**（只换值字面），该脚本逻辑不受影响；若把单行改成块状或调换顶层键顺序，就会撞上它的插入位置预检与 `new_data != expect` 比对。这条是"原地改写可行但必须逐字保持格式"的实证边界。

别名层的对照影响面：**改写点 0、yaml 文件 0、census 基线 0**（它只在读侧加一层解释，历史值逐字不动）。

---

## 2. 消费面现状（决定"接入面"这一要素的真实大小）

- `rg -n "\.tags\b|\["tags"\]|get\("tags"\)" core ui scripts tests` ⇒ 生产侧命中 **1 处**：`core/loader.py:186-187`（`_build_problem` 里做「字符串不当 iterable 拆字符」的防御搬运）。测试侧命中 `tests/test_content_fuzz_pins.py:76-79`（钉的就是这条防御）。
- `Problem.tags`（`core/loader.py:23`）在 **core／ui／scripts 里零读者**：报告面 `core/report.py` 与 `core/recommend.py::_topic_weakness` 用的是 `lang/topic_slug` 键；AI 出题面 `core/ai_generate.py:35-43 _build_user_prompt` 只拼 `difficulty/title/statement/expected_output`，**不拼 tags**（本班逐行确认）。
- `Problem.to_dict()`（`asdict`）有 3 个调用点（`ui/pages/language.py:134/:298`、`core/judge.py:39`）⇒ **给 `Problem` 加字段＝改 asdict 键集合**，这是接入面里唯一有隐性连带的一条（`tests/test_achievements_branches.py:21` 手工构造 `Problem(...)` 1 处；`tests/test_judge_mode_equivalence.py:140` 逐题比对 `to_dict()` 相等，两侧同函数产生的新字段不会造成不等）。

⇒ **诚实结论**：别名层今天**没有现役调用方**。它的价值只能在两种形状里选一种：①「备用的读侧解释层」——今天零调用，等第一个按标签聚合的消费方（技能面板／薄弱点标签报告／成就按 tag 计数）出现时直接接；②「治理工具」——先只被 `scripts/` 下的普查脚本用（把 §5 的三清单做成可重跑的读数），生产码零改动。本设计默认走 ②＋为 ①留签名兼容。

---

## 3. 映射方向：给人拍的判断题（本班不选案）

争议点＝`groupby`／`ifelse`／`effectsize` 三簇的规范值取向：**语言原生 API 真名** 还是 **描述性分隔符名**。

| 拍法 | 得到什么 | 后果（可核） | 谁能受影响 | 回滚成本 |
|---|---|---|---|---|
| **取向 A：折向 API 真名**（`groupby`/`ifelse`/`effectsize`） | 单语言侧准确，python/r 用户按真实函数名搜得到 | 改写 10 处；`if-else`(3) 是**多数派**却要被改成少数派 `ifelse`(2) ⇒ 与「按多数派收敛」直觉相反；`group-by`(3)／`group_by`(1) 挤进 `groupby` 后，sql 根下（`content/sql/02_aggregate/03_pass_fail_count.yaml`）的标签变成 pandas 味道 | cpp 根的 `if-else`（`content/cpp/02_branch_loop/02_max_of_three.yaml`）：C++ 里没有叫 `ifelse` 的东西 ⇒ 跨语言可读性受损 | 别名层：删表重跑即可，历史值没动 ⇒ **零回滚成本**。原地改写：26 处字面已入 git 历史，回滚＝一次反向 commit；但 `data/` 之外的 content 有还原点，风险可控 |
| **取向 B：全折分隔符描述名**（`group-by`/`if-else`/`effect-size`） | 跨语言中立，sql/r/cpp/python 同一写法 | `groupby`(10)（最大簇、且是 pandas 真名）要**改写 10 处**；`effectsize`(2)（R 包真名）改 2 处 ⇒ 合计改写量 17 处／17 文件，是取向A（10 处）的 1.7 倍、取向C（9 处）的 1.9 倍 | 语言原生可检索性下降：按 `groupby` 搜 R/SQL 题会落空 | 同上（别名层零成本／原地改一次反向 commit） |
| **取向 C：各簇多数派**（`groupby`/`if-else`/`effectsize`/…） | 改动最少（9 处），"符合直觉" | 规范值集合变得**不成体系**：同一层里既有 API 名又有描述名，`if-else` 与 `effectsize` 并存 ⇒ 下一次再加簇时没有可推的规则，治理成本转给人 | 同 A/B | 同上 |
| **取向 D：不做单一规范值，别名层只给"同形族"归组**（`TAG_FAMILY[原始值] = 族键`，族键用大小写不敏感的去分隔符形态；展示与检索按族、写入按原值） | 不裁"哪个写法更对"，先把"哪些写法是一件事"钉住；三取向都可作为族的**显示名**后续再定 | 需要定义族的展示名规则（否则 UI 上会出现 `groupby` 这种非单词）；**这正是 §4 设计的形状** | 零——历史值不动，无调用方今天不显示任何东西 | 零。族表可增可删，测试钉的是"分组成员"而非"规范写法" ⇒ 方向问题留到真有消费方时再拍，**不阻塞** |

**需要人工回答才能继续的前置问题**：
- Q1：标签的**首要消费者**是谁——语言内检索（选 A）、跨语言面板（选 B）、还是"暂时没有消费者"（选 D）？
- Q2：`if-else`(3) vs `ifelse`(2) 这种**多数派与 API 真名冲突**的簇，按多数派还是按真名？（A 与 C 在这里分叉）
- Q3：`operator+`/`operator==`/`data.frame`/`which.max`/`IQR`/`Surv`/`ValueError`/`ZeroDivisionError`（**11 个违反小写词形的值**，含 2 个带 R 语法的点号值、5 个 C++ 运算符值）**是否永久排除在归一之外**？本设计默认"排除"，需人确认这是策略而非遗漏。
- Q4：`function`/`functions`、`line`/`lines`（单复数）算同一技能标签吗？（spec 的 `norm()` 会把它们并组 ⇒ 重复组 7；222f 把它们归入"需人工看题面"。两者差异全在这一条。）

---

## 4. `canonical_tag()` 别名层设计（四要素）

设计基线＝**同仓已有的成功先例** `core/rubric_dims.py`（`DIMENSION_CANON` 表 + `canonical_dimension() -> (id, 规范名)`，未命中回 `"other"`＋原值；调用方 `core/ai_review.py:477`、`core/progress.py:488/:526` 用函数内延迟 import；测试件 `tests/test_rubric_dims.py` 现 **5 例**）。别名层照此形状，不另发明风格。

### 要素①：映射表位置

- 新建 **`core/content_tags.py`**（模块级常量，与 `rubric_dims.py` 平级）。不放 yaml：词表只有 11＋若干保护对，模块常量可被测试直接 import，而数据文件要额外定义加载与缺失兜底（`mark_r_judge_plain.py` 的教训是内容面改动要走 fail-closed 校验）。
- 三张表，**彼此语义独立**（避免"一个 dict 兼职三件事"）：

```python
# 表 1：显式别名 → 族键（只登记"去分隔符后同形"的 B 级 5 簇 11 值，逐条来自本档 §1 实测）
TAG_ALIASES = {
    "groupby": "groupby", "group-by": "groupby", "group_by": "groupby",
    "if-else": "ifelse", "ifelse": "ifelse",
    "effectsize": "effectsize", "effect-size": "effectsize",
    "error-handling": "errorhandling", "error_handling": "errorhandling",
    "feature-importance": "featureimportance", "feature_importance": "featureimportance",
}
# 表 2：永不参与归一的原值（大小写／点号／运算符承载，§3 Q3）
TAG_OPAQUE = frozenset({"IQR", "Surv", "ValueError", "ZeroDivisionError",
                        "data.frame", "which.max", "operator()", "operator+",
                        "operator<<", "operator==", "operator[]"})
# 表 3：保护名单——近邻对＋同 token 家族，断言"绝不被并"（数据，不是散文计数）
TAG_DO_NOT_MERGE = (("glm", "lm"), ("map", "map2"), ("in", "int"),
                    ("fstream", "ifstream"), ("ifstream", "ofstream"),
                    ("string", "stringr"), ("tidy", "tidyr"),
                    ("comprehension", "comprehensive"), ("recursion", "recursive"),
                    ("concat", "concept"), ("function", "functor"),
                    ("operator+", "operator=="), ("operator()", "operator[]"),
                    ("template", "class-template"), ("pivot_table", "pivot_wider"),
                    ("ttest_ind", "ttest_rel"), ("virtual", "pure-virtual"))
```
- 🔴 表 3 的**来源必须是可重跑脚本**（`near_pairs.py`／`families.py`，见 §6），不要照抄本档或锚点的散文计数——锚点自述规则复算 25 对≠其表内 27 对，且点名 15 对里 6 对不被规则抓到；散文数字会漂，元组列表会被测试钉住。

### 要素②：函数签名（纯函数、零副作用、历史值不改）

```python
def tag_family(tag: str) -> str:
    """原值 → 族键。TAG_OPAQUE 命中或未登记 ⇒ 原样返回（不发明值、不小写化）。"""

def canonical_tag(tag: str) -> tuple[str, bool]:
    """返回 (规范值, 是否发生归一)——对齐 canonical_dimension() 的元组风格。
       规范值 = 该族的展示名；展示名取向未拍时（§3 D）等于族键。"""

def canonical_tags(tags: list) -> list[str]:
    """逐位映射＋**保序去重**（同件内不会出现同簇重复值，实测 0 件；仍保留该语义）。"""

def tag_alias_report(tags: list) -> dict:
    """{"changed": [(原值, 族键)], "opaque": [...], "unknown": [...]}，供普查与人工复核。"""
```
硬约束（都可钉成断言）：**幂等** `canonical_tag(canonical_tag(x)[0])[0] == canonical_tag(x)[0]`；**不改大小写**（非表内值原样返回）；**不去点号**；**未知值永不落到别人的族键上**（返回原值 ⇒ 词表治理与"未知标签"判据仍按 `learn-tag-vocab-spec-20260925.md` §三.3 的指纹口径走，指纹基线现值 `bfbf832d88a75f3d`）。

### 要素③：调用方接入面（分三档，默认只上第 0 档）

| 档 | 接入点 | 改动面 | 风险 |
|---|---|---|---|
| **0（默认，零生产码接入）** | 只被 `scripts/` 普查脚本用：新增/改造一个只读脚本输出「三清单＋指纹」；`core/` 一行不动 | 0 个生产文件；content 0 diff | 无。别名层的正确性由 §4 要素④ 的测试独立钉（不依赖调用方） |
| **1（读侧透出，不动历史）** | `core/loader.py:_build_problem` 之后加 `Problem.canonical_tags: list = field(default_factory=list)`（`core/loader.py:23` 附近），构造时 `tags=raw_tags` 原样保留、另算 `canonical_tags` | 生产码 2 处（dataclass 字段＋构造行）；`to_dict()` 键集合 **+1**（3 个调用点，见 §2）；`scripts/mark_r_judge_plain.py:125 ANSWER_KEYS` 是 **yaml 键**清单、不是 `Problem` 字段清单 ⇒ 不受影响，但要确认无人把它当"字段全集"用 | 中低。需重取 `tests/test_achievements_branches.py:21` 之外无构造点；`test_judge_mode_equivalence.py:140` 两侧同源不受影响 |
| **2（写侧入表闸）** | 未来任何"按标签聚合"的消费方（技能面板／薄弱点报告／成就按 tag 计数）落地时，**只准调 `tag_family()`**，禁止自己写 `lower()/replace()`——把 7 处语言词表副本式重复（`learn-tag-vocab-spec-20260925.md` §二.1）的教训挡在入口 | 每加一个消费方 1 行 import | 低；但这是"别名层是否真的被用起来"的唯一判据，否则它就是死码 |

不建议的形状：**在 loader 里就地把 `tags` 换成规范值**——那等于用代码做原地改写，历史标签消失（锚点"不丢弃历史标签"的判据就破了），且 `to_dict()` 出去的值会变，AI 面与调试面看到的不再是 yaml 原文。

### 要素④：测试（新增 `tests/test_content_tags.py`，形状对齐 `tests/test_rubric_dims.py` 现 5 例）

| # | 例 | 断言（全部可从本档复算） |
|---|---|---|
| T-1 | 表完整性 | `TAG_ALIASES` 的 value 集合＝{`groupby`,`ifelse`,`effectsize`,`errorhandling`,`featureimportance`}；key 集合＝§1 的 11 个现值；且 `set(TAG_ALIASES) ⊆ 盘上 tag 值集合`（防"表里登记了不存在的别名"死条目） |
| T-2 | 归一行为 | 逐值 `tag_family("group_by") == "groupby"` 等 11 条；`canonical_tag` 的 `changed` 标志只在 6 个少数派写法上为 True |
| T-3 | 幂等 | 对全 416 值：`tag_family(tag_family(x)) == tag_family(x)` |
| T-4 | 保护名单 | 对 `TAG_DO_NOT_MERGE` 每一对 `(a,b)`：`tag_family(a) != tag_family(b)`；且 `tag_family` 在 `operator*`／`data.frame`／`which.max`／4 个非小写值上返回**原值逐字相等**（不小写、不去点号） |
| T-5 | 历史不动（构造性哨兵） | ①`content/**/*.yaml` 里出现过的 416 值，经别名层后**仍全部可原样检索到**（`raw == list(problem.tags)` 不丢）；②词表指纹 `sha256("\n".join(sorted(values)))[:16]` 仍等于现值 **`bfbf832d88a75f3d`** ⇒ 一旦有人原地改 yaml 值，这例当场红，"别名层 vs 原地改写"的分界由测试守住而不是靠约定 |
| T-6 | 未知值 | 盘上未登记的任意串（含 `None`、空串、非 list 的 `tags`）不抛异常、返回原值——复用 `core/loader.py:186` 那条"字符串不当 iterable 拆"的既有形状 |

配套（可选，非必须）：`test_content_census_*` **无需**同批重取（本班实测 6 件里零 tag 断言）；但 T-5② 的指纹哨兵若被红，说明有人动了 content ⇒ 那才是真需要重取 census 基线的信号。

---

## 5. 「别名层 vs 原地改写」对比与推荐

| 维度 | 只读别名层（本档 §4） | 原地改 26（实为 9～17）个 yaml |
|---|---|---|
| 判据"不丢弃历史标签" | **由构造保证**（原值就是唯一事实源，别名只在读侧） | 靠 git 历史＋反向 commit，运行期已看不到旧写法 |
| 今天可见的收益 | **零**（无现役消费方，见 §2）——收益全部在未来第一个按标签聚合的面 | 立刻：普查里"同簇多写法"合成一行；`singletons` 265→… 需重算（416→410 是 B 级并表的读数，锚点已给） |
| 影响面 | `core/content_tags.py` 新增 1 件 ＋ `tests/test_content_tags.py` 新增 1 件（档 0 时生产码 0 改动） | content 9～17 文件（取向A 10 处／取向B 17 处／取向C 9 处；锚点的"26"是两侧并集）；`mark_r_judge_plain.py` 的 `tags:` 锚点行必须逐字保持单行形态（§1 反面）；census 基线**不需**重取（本班否证） |
| 方向问题（§3）是否必须先拍 | **不必**（取向 D：先钉族成员，展示名后定） | **必须先拍**（改哪个字面＝选哪个方向），且改完再翻向要二次改 9～17 处（A↔C 只差 `ifelse` 一簇 1 处，A↔B 要重做 13 处） |
| 回滚成本 | 删模块＋删测试，盘上零残留 | content 有 git 还原点 ⇒ 一次反向 commit；但**若这 26 件与在途未提交改动重叠**，回滚会连带别人的行（本仓工作树现点 porcelain 0，但 content 面历史上是编辑热区）⇒ 比别名层重 |
| 出错半径 | 纯函数，红只在自己测试件里 | 词面改动会影响任何未来按原值检索的功能（含 UI 搜索、成就按 tag 计数） |

**推荐（这是"形状取向"，不是放行；方向题一律留给人）**：

1. **先做别名层（档 0）＋ T-5 指纹哨兵，不做原地改写。** 理由三条都可核：方向未拍时别名层不阻塞（§3 D）；改写量与方向耦合（9↔17 处随取向翻动，先改＝先赌）；T-5 把"不许动历史值"从口头纪律变成会红的测试，比"我们约定不改 yaml"强。
2. **档 1（给 `Problem` 加 `canonical_tags`）今天不做**——它只为一个还不存在的消费方服务，却要付 `to_dict()` 键集合变化的隐性代价。等档 2 的真实调用方出现再开，届时字段名与函数签名保持不变即可（本档签名已按此约束写）。
3. 若人工最终裁定"必须统一词面"，**选取向 A 或 C 而不是 B**：B 的改写面 17 处，A 是 10 处、C 是 9 处（＝B 的 1.7～1.9 倍差），且 B 要把最大簇 `groupby`(10) 改掉——这是"为了中立性付最多字面改动"的形状。该判断只涉及改动量与簇内多数派，不涉及哪个名字"更正确"（那属 §3 Q1/Q2）。
4. **保护名单必须重生成**：`near_pairs.py`／`families.py` 两枚探针就是重生成的入口；落地时把它们的输出写进 `TAG_DO_NOT_MERGE`，并让测试断言"名单里每个值都还在世"（否则词表变化后名单会悄悄失效）。

---

## 6. 可复算入口

全部只读，零写盘；探针目录 `D:\code\tmp\qoder-executor-20260927-1820-learn47\`（收班自清）：

- `tag_probe.py`＝词表基线复算（spec §一 配方原样重跑）→ `yaml=409 题=403 路径件=6 / unique=416 occ=898 singletons=265 基线sha=bfbf832d88a75f3d / 重复组=7 涉及值=15 涉及出现=33 / A 级 3 簇 6 值 / B 级 5 簇 11 值`。
- `tag_files2.py`＋`dir_breakdown.py`＝§1 逐簇文件数／出现数／三取向改写点明细（**取向A 10 处 10 文件／取向B 17 处 17 文件／取向C 多数派 9 处 9 文件**；并集 26 文件 26 出现；块状 tags 0 件；同件重复 0 件）。
- `near_pairs.py`＝近邻对复算（**25 对**，并点名锚点 15 对里规则未抓到的 6 对）。
- `families.py`＝同 token 家族（首段口径 **5** 族；锚点点名 9 族逐一在世）＋11 个词形不合群值＋点号／运算符值面＋"B 级规则今天不会误伤点号值（`data.frame` 无同形对手，但 by construction 不安全）"。
- 消费面普查：`rg -n "\.tags\b|\["tags"\]|get\("tags"\)" core ui scripts tests` → `core/loader.py:186` ＋ `tests/test_content_fuzz_pins.py:79` 两处（其余为 `scripts/mark_r_judge_plain.py` 的**行锚点**用途，非值消费）。
- census 测试件零 tag 断言：`rg -n "tag" tests/test_content_census*.py` → **无输出**（例数：4／5／5／5／9／6＝34 例）。
- 生产库（本单未打开，仅作交班自证）：`data/progress.db` **122,880 B ／ sha8 `cd2dbce4`**（18:08 与 18:1x 两点取样一致，与在册基线同值）。

---

## 7. 遗留（不在本设计裁决范围）

1. §3 的 Q1–Q4 未拍 ⇒ 别名层的**展示名**（`canonical_tag()` 第一返回值）暂时只能取族键；拍板后要改的是表 1 的 value 而不是结构。
2. 222f 记录面漂移（同一 `attempt_submitted` 两代 payload 有无 `attempt_id`）**与本单正交**（tags 不落库，`data/progress.db` 七表零 tag 列），仍留在册。
3. `scripts/mark_r_judge_plain.py` 把 `tags:` 行当插入锚点，**块状写法今天 0 件**；若将来有人把 tags 改成块状，该脚本 `:281`/`:289` 的预检路径会从"未 exercised"变成"在用"，届时需要补真实语料侧的测试。本班只登记，未改。
4. 本班未代登 insights 索引（`tests/test_insights_index_closure.py` 真哨兵，写本档前 A=B=95 闭合）；红 3 例属主班的账。
