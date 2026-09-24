# learning core/ 函数级零测终扫台账（l924-23，2026-09-25）

> 用途：**后续新增 core 模块照本档 §九 的命令复扫即可**，不必重开盘点。
> 本档是「名级」台账，**不是覆盖率报告**（口径边界见 §二末）。
> 所有读数现取于 2026-09-25T01:3x+08:00、learning HEAD `8da2dd9`、`tests/` 99 份 .py／17,208 行——
> **它们是当时读数、不是断言对象**，下一浪新增用例就会漂，故本档任何数都配一条可复跑命令。

## 一、三条结论

1. `core/` 与 `core/runners/` 在 tests/ 的**名级**覆盖接近满格，但不是「唯一漏网」：
   实测 **4 个函数名在 tests/ 全文零命中**（`format_local_ts`、`solved_with_timestamps`、
   `check_security`、`fmt_row`），本单只补了其中**有真实 UI 消费点的那一个**（`format_local_ts`），
   其余 3 个见 §八。
2. 卷宗「core/ 15 模块」与「`rg -c 'def [a-z]' core/*.py`」不同源：**盘上 16 份 `core/*.py`**
   ＝ 15 个真模块 ＋ `__init__.py`；而 `rg -c` **只输出 14 行**（`rg` 对零命中文件静默省略，
   `__init__.py` 与 `version.py` 都不报）。⇒ 用 rg 输出行数当「模块数」会少 2。
3. 两轨差额可逐行归因（§五），**没有归不上的差额**：rg 轨比 AST 轨少 53（128−75）全是
   `_私有`／`dunder`／嵌套 def，rg 轨的假阳 1 处（`diagnostic.py` 的题干字符串）。

## 二、口径（三件）

- **轨 A（卷宗点名的正则口径）**：`rg -c 'def [a-z]' <file>`，逐行计数，**含重复名**、
  含字符串/注释里的巧合命中、**不含** `def _私有` 与 `def __dunder__`。
- **轨 B（AST 口径）**：`ast.walk` 收 `FunctionDef` ＋ `AsyncFunctionDef`，含类方法与嵌套闭包，
  再按名字切「小写且非 dunder」子集与轨 A 对齐。
- **覆盖判定**：函数名以 `\b<name>\b` 在 `tests/**/*.py` **全文**（含注释与 docstring）检索，
  命中即记「有名」。**方向性必读**：
  - 「有名」是**上限口径**——名字可能只出现在某条例述/注释里，并不代表行为被测（本仓 §廿六 类教训）；
  - 「零名」是**确证**——它一定没被按名引用，但**仍可能被间接行为覆盖**（走调用方的公开行为）。
    ⇒ 本表只能用来**找候选缺口**，不能用来宣布「X% 覆盖」，也不能反过来宣布「某函数没被测」。

## 三、core/*.py 计数表（16 行，含 `__init__.py` 与 rg 零命中件）

| 文件 | rg `-c 'def [a-z]'` | 唯一名 | AST 全部 def | AST 小写非 dunder 唯一名 | tests/ 有名 | 零命中名 |
|---|---|---|---|---|---|---|
| `core/__init__.py` | 0 | 0 | 0 | 0 | 0 | — |
| `core/achievements.py` | 5 | 5 | 9 | 5 | 5 | — |
| `core/ai_generate.py` | 1 | 1 | 5 | 1 | 1 | — |
| `core/ai_review.py` | 4 | 4 | 17 | 4 | 4 | — |
| `core/config.py` | 3 | 3 | 3 | 3 | 3 | — |
| `core/data_portability.py` | 5 | 5 | 7 | 5 | 5 | — |
| `core/diagnostic.py` | 4 | 4 | 3 | 3 | 4 | —（rg 假阳 1，见 §五） |
| `core/judge.py` | 1 | 1 | 13 | 1 | 1 | — |
| `core/loader.py` | 5 | 5 | 9 | 5 | 5 | — |
| `core/paths.py` | 3 | 3 | 3 | 3 | 3 | — |
| `core/progress.py` | 35 | 35 | 43 | 35 | 33 | `format_local_ts`、`solved_with_timestamps` |
| `core/recommend.py` | 3 | 3 | 9 | 3 | 3 | — |
| `core/report.py` | 3 | 3 | 4 | 3 | 3 | — |
| `core/rubric_dims.py` | 2 | 2 | 2 | 2 | 2 | — |
| `core/utils.py` | 1 | 1 | 1 | 1 | 1 | — |
| `core/version.py` | 0 | 0 | 0 | 0 | 0 | — |

**小计**：rg 合计 **75** 行／唯一名 **75**（无同名重复）／AST 合计 **128**／零命中名 **2**。

## 四、core/runners/*.py 计数表（6 行）

| 文件 | rg `-c 'def [a-z]'` | 唯一名 | AST 全部 def | AST 小写非 dunder 唯一名 | tests/ 有名 | 零命中名 |
|---|---|---|---|---|---|---|
| `core/runners/__init__.py` | 0 | 0 | 0 | 0 | 0 | — |
| `core/runners/base.py` | 2 | 2 | 2 | 2 | 1 | `check_security` |
| `core/runners/cpp_runner.py` | 1 | 1 | 4 | 1 | 1 | — |
| `core/runners/python_runner.py` | 1 | 1 | 6 | 1 | 1 | — |
| `core/runners/r_runner.py` | 1 | 1 | 3 | 1 | 1 | — |
| `core/runners/sql_runner.py` | 2 | 2 | 8 | 2 | 1 | `fmt_row` |

**小计**：rg 合计 **7**／AST 合计 **23**／零命中名 **2**。
「runners 5 件」这条前提成立（6 份 .py ＝ 5 件真模块 ＋ `__init__.py`）。

## 五、两轨差额逐行归因

- **rg 比 AST 少 53（128−75，core 侧）／少 16（23−7，runners 侧）**：差的全是轨 A 字符类
  故意不看的三类——`def _私有`、`def __dunder__`、类内方法嵌套。抽样验证：
  `core/judge.py` rg=1 而 AST=13 ⇒ 该模块是「1 个公开函数 ＋ 一堆类方法/私有」的形状，
  **不是漏计**。⇒ 这条差是**口径差**，不是数据错。
- **rg 比 AST 多 1（`core/diagnostic.py` 唯一一处反向差）**：
  `$ rg -n 'def [a-z]' core/diagnostic.py` → `:44` 是一**道题干字符串**
  （题干文本含 "Python 函数 `def add(a, b): return a + b`"），AST 轨正确不认它。
  ⇒ 轨 A 的假阳在本仓实测**恰好 1 处**，且是题面文案而非代码；这就是本台账坚持双轨并报差额的原因。
- **未做第三轨（剥注释复扫）**：AST 轨已经覆盖这个需求（`ast.parse` 天然不看注释），故不必另做。

## 六、卷宗前提的复核结果（含否证）

| 卷宗前提 | 实测 |
|---|---|
| `core/progress.py:13` 是 `def format_local_ts(...)` | **未漂移** ✓ `grep -n "def format_local_ts" core/progress.py` |
| `core/progress.py:16` 是「直接用 UTC 原文展示会差 8 小时…」 | **未漂移** ✓（同一 docstring 的正文行） |
| `ui/pages/mistakes.py:148` 是消费点 | **行号漂 ＋8**：现落 `:156`；另一消费点 `ui/pages/dashboard.py:370` 现落 `:380`。文本逐字仍在 ⇒ 前提成立、行号不可引 |
| 「core/ 15 模块＋runners 5 件在 tests/ 名级**全覆盖**，**唯一漏网**是 format_local_ts」 | 🔴 **否证**：名级零命中实为 **4 个**（core 2 ＋ runners 2）。且「15 模块」要按「16 份 .py − `__init__.py`」换算，直接 `rg -c` 只回 14 行 |
| 「`rg` 全仓仅 `core/progress.py:13` 定义 ＋ 两 UI 消费点」（指 format_local_ts） | **成立** ✓ `rg -n "format_local_ts" --glob '!tmp/**' .` → 定义 1 ＋ mistakes 的 import/用点 ＋ dashboard 的 import/用点 |

## 七、本次收口：`format_local_ts` 钉桩

新增 `tests/test_format_local_ts.py`：**6 个测试函数／8 条用例**（`test_utc到本地换算与平台口径一致`
按 3 个时刻参数化）。计数现取：`rg -c "^def test_" tests/test_format_local_ts.py` → 6。

四条卷宗点名的行为都在，另加两条（格式契约、判别力自适应例）：

| 用例 | 钉的行为 |
|---|---|
| `test_空值与假值都渲染成空串` | `''`／`None` → `''`，且不得被兜成 `"None"` |
| `test_解析失败逐字原样返回` | 5 种失败形态（含带时区尾巴、缺秒、前导空格）逐字退回 |
| `test_小数秒形与整秒形同值` | `split('.')[0]` 截断口径（3 种小数位长度） |
| `test_utc到本地换算与平台口径一致` | 期望由**显式 UTC datetime 对象** `.astimezone()` 构造，不走被测实现链路 |
| `test_本机偏移非零时换算不是空操作` | 偏移≠0 的机器上断言「展示值 ≠ UTC 原文到分钟」；偏移=0 时退化为等值断言（**不造假红**） |
| `test_输出格式不含秒也不含时区尾巴` | 16 字符 `YYYY-MM-DD HH:MM`，可再 `strptime` |

不 flaky 与判别力的两条自证（本单实跑）：

```
$ for tz in UTC EST+5 JST-9 IST-5:30 Kiritimati-14 GMT0BST; do TZ=$tz python -m pytest tests/test_format_local_ts.py -q; done
（六态各 8 passed）
$ TZ=JST-9 PYTHONIOENCODING=utf-8 python tmp/l924-23/mutate_check.py
本机偏移：9:00:00；测试函数 6 个
M0 原件（对照）  被杀例 0/6: []
M1 不做换算      被杀例 3/6: [utc到本地换算与平台口径一致, 本机偏移非零时换算不是空操作, 解析失败逐字原样返回]
M2 不截小数秒    被杀例 1/6: [小数秒形与整秒形同值]
M3 空值兜成字符串 被杀例 4/6: [utc到本地换算…, 小数秒形…, 空值与假值…, 输出格式…]
```

⚠️ 写这组用例时踩到并已消掉的两个**永绿陷阱**（下传）：
① 输出格式本来就没有秒，若判别力例写成 `out != raw`（raw 带秒）→ **恒真**，必须与 `raw[:16]` 比；
② 偏移=0 的机器上「等于原文」才是对的，写成 `!=` 会在 UTC 执行机上**假红**——两态分支都要写。

## 八、余 3 个零名（本单未做，附实况供派单）

| 名 | 位置 | 生产消费点（实测，`rg -n <名> --glob '!tests/**' --glob '!tmp/**' .`） | 建议 |
|---|---|---|---|
| `solved_with_timestamps` | `core/progress.py` | 🔴 **零调用方**（全仓仅定义那一行）⇒ 死码候选 | 别急着补桩：先派「死码裁决」单（同族在册做法），**补测会把死码钉活** |
| `check_security` | `core/runners/base.py` | **4 处调用**（cpp/python/r/sql runner 各 1）⇒ 大概率被 `run()` 行为间接覆盖 | 若要补，按「危险代码被拦」的行为例补，别按名补 |
| `fmt_row` | `core/runners/sql_runner.py` | 2 处调用（同文件内部渲染） ⇒ 同上，属渲染细节 | 低收益，可与 sql_runner 渲染例合并 |

## 九、终扫命令（照单复扫，新增模块后重跑即得新表）

```bash
# 轨 A（卷宗口径；注意 rg 对零命中文件不输出 ⇒ 行数 ≠ 模块数）
rg -c 'def [a-z]' core/*.py core/runners/*.py
ls core/*.py | wc -l            # 现值 16（含 __init__.py）
ls core/runners/*.py | wc -l    # 现值 6（含 __init__.py）
# 双轨 ＋ 名级覆盖：一次性打出 §三/§四 两张表（含差额与零命中名）
PYTHONIOENCODING=utf-8 python tmp/l924-23/scan_core_census.py
# 单个名字的「有没有被 tests/ 提及」
rg -n "\b<函数名>\b" tests/
# 新桩本体（跨时区自证见 §七）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_format_local_ts.py -q
```

> ⚠️ `tmp/l924-23/scan_core_census.py` 在 gitignored 的 `tmp/` 下，**不随本档入库**；
> 主班若要把它转成在册件（`scripts/` 或 `tests/`），需另开一单——本单授权面不含 `scripts/`。

## 十、遗留问题

1. §八 三个零名各自的处置（尤其 `solved_with_timestamps` 的死码裁决）**未做**，不在本单范围。
2. 「有名」→「被测」的**行为级**判定未做（要把 AST 切出的函数与打桩点比对），本台账只是名级下限/上限清单。
3. `format_local_ts` 的一处**现状缺陷未修**（本单不动生产码）：入参为非字符串真值（如 int）时，
   `ts_str.split` 抛 `AttributeError`，而 `except (ValueError, TypeError)` 接不住 ⇒ 会崩渲染。
   实际路径上库里 ts 列都是串，故**未钉成断言**（钉了就是把崩溃钉成契约），在此登记待裁决。
4. 未跑全量套件（卷宗完成标准未点名；并行不跑全量是默认约束）。新增 1 份测试件对全量的影响：
   **+8 例**（该件自身收集数），无红。
