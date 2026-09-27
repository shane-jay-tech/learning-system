---
id: l927-07-dashboard-regression
title: dashboard 五列挤压（B-131 修后）回归复核——:85 现值对照＋定向 UI 测试子集
task: l927-07（zcode-bridge 波次 20，工作类型 docs，风险档 B）
shift: qoder-executor-20260927-1440-learn45
written: 2026-09-27T14:38
head_at_write: c71c6f0
mode: 只读复核（零码改动；跑定向测试子集 5 件 74 例，未跑全量＝并发窗纪律）
status: 结论＝**修复在位、无回归**；附带 3 条待裁观察（1 条测试件粘贴重复、1 条断点语义澄清、1 条未覆盖面）
supersedes_or_extends: 不重复 `docs/insights/l927-04-ergonomics-status.md`（同波兄弟班的人体工学全表面盘点）；本档只做 B-131 首条发现的**回归复核＋子集取证**，两档在 §五 显式划界
---

# dashboard.py:85 五列挤压回归复核（B-131 修后）

> 卷宗完成标准：①:85 现值对照 ②子集测试结果 ③结论 ④零码改动。判据命中 **4/4**。

## 〇、一句话结论

1. **修复在位、无回归**。`ui/pages/dashboard.py:85` 现值已不是 9-11 扫描时的那行代码，而是**修复本体的入口**：
   `def _lang_card_rows(langs, per_row: int = _CARDS_PER_ROW):`（`_CARDS_PER_ROW = 3` @ `:82`）。
2. **"在位"的可复算判据不是行号，是 blob 等值**——工作树版与 HEAD 版**逐字节相同**：
   `git hash-object ui/pages/dashboard.py` ＝ `git rev-parse HEAD:ui/pages/dashboard.py` ＝ `09401c05b45ca452e39b2a3b3947950b53108e08`，
   `git diff --numstat HEAD -- ui/pages/dashboard.py` **空输出**（另两枚承附件 `ui/styles.py` ＝ `2c404fa1…`、`tests/test_ergo_h912_13.py` ＝ `826386c8…` 同样等值）。
3. 定向子集 **74 passed / 0 failed / 2.74s**（5 个文件，未跑全量）。
4. **锚点行号已漂**（属正常搬家的"内容漂移"，不是路径搬家）：卷宗与 `learning-ergonomics-scan-20260911.md:21` 指的 `st.columns(min(n, 5))` 在盘上**只以注释形式残存**于 `:151`（且写的是 `min(n, 4)`），代码行 **0 命中**。
5. **语义澄清（本档新增）**：9-11 扫描把这条缺陷叫「**1366 断点挤压**」，但 1366 这个数**从未成为媒体查询**——`ui/styles.py:7 _BP_TARGET_WIDE = 1366` 注释自述「文档口径，未用于媒体查询」，媒体查询只有 `max-width: __BP_MID__px`(1280) 与 `__BP_NARROW__px`(900) 两档。⇒ **1366 窗口（视口>1280，媒体查询不触发）下的真实承载者是"每行 3 卡"分行本身**，不是断点。见 §四。

---

## 一、判据①：`:85` 现值对照

| 项 | 现值 | 取法 |
|---|---|---|
| 工作树 `:85` | `def _lang_card_rows(langs, per_row: int = _CARDS_PER_ROW):` | `sed -n '83,87p' ui/pages/dashboard.py` |
| HEAD blob `:85` | **同一行，逐字相同** | `git show HEAD:ui/pages/dashboard.py \| sed -n '83,87p'` |
| blob 等值 | `09401c05b45ca452e39b2a3b3947950b53108e08`（两侧同值） | `git hash-object` vs `git rev-parse HEAD:<路径>` |
| numstat | 空（0 行） | `git diff --numstat HEAD -- ui/pages/dashboard.py` |
| 修复入口常量 | `:82 _CARDS_PER_ROW = 3`，`:79-80` 注释点名「上限仍守着 h912-13 修复② 的『每行 ≤4 列』，该意图由 `tests/test_ergo_h912_13.py::test_dashboard_column_cap_and_1280_breakpoint` 机械把守」 | 读文件 |
| 消费点 | `:154`（语言卡 5 门→3+2）、`:469`（成就墙复用同一助手，`per_row=4`） | `grep -n "_lang_card_rows("` |

**历史链**（谁改的、为什么行号漂）：

| commit | 日期 | 干了什么 |
|---|---|---|
| `a56be3d` | 09-13 | h912-13 修复批：`min(n, 5)` → 列数上限 4 ＋ `styles` 加 1280 中间断点 ＋ 三处静默 except 改 logger（345→348 绿）。**这一版把 :85 从 `st.columns(min(n,5))` 换成了 `st.columns(min(n,4))`** |
| `995fff4` | 09-19 | d913c-10：断点数值收敛为常量单源 `_BP_MID/_BP_NARROW`，CSS 走 `__BP_MID__` 占位注入 |
| `0327f1c` | 09-22 | l922-120：真因订正——`min(n,4)` 配 `cols[i % len(cols)]` 取模**并不折行**，第 5 卡被塞回第 1 列纵堆 ⇒ 改 `_lang_card_rows` 3+2 居中；**否决**在册建议「复用 `min(n,4)` 辅助」（该辅助正是成因，且 a56be3d 已否过 5 列等宽≈183px）；ergo 断言按语义**等价改写**（改断言不改实现） |
| `5aa858a` | 09-25 | l924-32：成就墙末行居中复用同一助手 |

⇒ 行号漂移的**每一跳都有账**，不是"锚点失效"。

---

## 二、判据②：定向 UI 测试子集结果

```console
$ cd D:/code/learning-system && certutil -hashfile data/progress.db SHA256 | sed -n '2p' | cut -c1-8
cd2dbce4                                     ← 跑测试**前**现值
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_ergo_h912_13.py tests/test_dashboard.py \
    tests/test_dashboard_page_render.py tests/test_dashboard_achievements_row_centering.py \
    tests/test_ui_behavior.py -q
74 passed in 2.74s
$ echo ${PIPESTATUS[0]}   → 0                 ← 取 rc 不接管道尾（brief §6 坑；显式取 PIPESTATUS[0]）
$ certutil -hashfile data/progress.db SHA256 | sed -n '2p' | cut -c1-8
cd2dbce4                                     ← 跑测试**后**现值（未变）
```

| 定向文件 | 例数 | 与本案的关系 |
|---|---|---|
| `tests/test_ergo_h912_13.py` | 4 | **h912-13 修复批的自有断言**（含 `test_dashboard_column_cap_and_1280_breakpoint`） |
| `tests/test_dashboard.py` | 20 | dashboard 行为面 |
| `tests/test_dashboard_page_render.py` | 15 | 页面渲染链 |
| `tests/test_dashboard_achievements_row_centering.py` | 9 | **复用同一 `_lang_card_rows` 的第二消费点**（AppTest 真 DOM 读回 `Column.weight`，13/14/15 枚三夹具） |
| `tests/test_ui_behavior.py` | 26 | UI 行为基类（`FakeStreamlit`；本档同时是其在册"失明面"的来源，见 §五） |
| 合计 | **74** | 全绿，0 skip / 0 xfail / 0 error |

**未跑全量**（并发窗内 `kaoyan75`／`quant46`／`psy75` 同刻在跑，全量红不可归因）。全量数若要，交主班收班取。

### 断言实际把守的东西（逐条对盘上现值复核，不只看绿）

| 把守点 | 断言 | 盘上现值复核 |
|---|---|---|
| 旧缺陷正面表述 | `"min(n, 5)" not in src` | `grep -c "min(n, 5)"` ＝ **0**（`:151` 注释里写的是 `min(n, 4)`，不冲突） |
| 取模叠卡不得回归 | 代码行（剔 `#` 开头）不含 `i % len(cols)` | 全件仅 `:151` 一行注释命中 ⇒ 代码行 **0 命中** ✓ |
| 每行 ≤4 列（机械扫） | 所有**字面量**入参 `st.columns(...)` 槽位数 ≤4 | 字面量站点 6 处：`:129/:580/:615` = `st.columns(4)`；`:209/:422` = `[3,1]`；`:243/:264` = `[1,1,3]`；`:292` = `[1,2]` ⇒ 全部 ≤4 ✓ |
| 变量入参槽位（扫描盲区） | 直接跑纯函数 `_lang_card_rows`：5 门→3+2、满行不补空槽、末行 `[0.5,1,1,0.5]` 居中、每行权重和恒 3、空表不产行 | `:85` 实现与断言逐条对齐 ✓（该断言是本单"行号漂移后仍把守同一意图"的**主证据**） |
| 中间断点在位 | `"_BP_MID = 1280" in styles` 且 `_BP_MID` 先于 `_BP_NARROW` | `ui/styles.py:5` `_BP_MID = 1280`、`:6` `_BP_NARROW = 900`、`:300/:305` 两条 `@media`、`:347-348` `inject()` 占位替换 ✓ |

---

## 三、判据③：结论

**修复在位，无回归。** 具体口径：

- 「每行 ≤4 列、不许退回 5 列挤压」这一**意图**由三层把守且现值全中：`min(n,5)` 缺席 ＋ 字面量站点机械 ≤4 ＋ `_lang_card_rows` 纯函数权重和恒为 3。
- 「1024–1280 区间无中间断点」这一**伴随缺陷**由 `styles.py:300` 的 `@media (max-width: __BP_MID__px)`（注入 1280）＋ `:302 stHorizontalBlock { flex-wrap: wrap }` 把守，在位。
- **无"改断言放宽"迹象**：`0327f1c` 那次改写是**等价改写**（把"字面量 `min(n,4)` 在位"换成三条更严的等价把守，其中"取模叠卡不得出现"是**新增**防回归），不是删断言。

### 「1366 断点形态」需要按实况收窄（本档唯一的实质订正）

9-11 扫描把缺陷命名成「1366 断点挤压」，但**1366 从未进过媒体查询**：

- `ui/styles.py:7` `_BP_TARGET_WIDE = 1366  # 目标分辨率参考（文档口径，未用于媒体查询）`；
- 媒体查询阈值是 **1280 / 900 /（:326 另有 1000）**，CSS 视口 1366 时 `max-width:1280px` **不触发**；
- 所以"1366×768 展开侧栏、内容区 ~1100px"这个被复现的场景，其缓解**全部来自列数**（3+2 分行 ⇒ 每卡 ≈1100/3 ≈ **366px**；旧 5 列等宽 ≈ **210px**，与扫描档自述的 ~210px 吻合），断点只在窗口本身 ≤1280 时叠加生效。

⇒ 建议后续文档与人话把这条写成「**每行卡数上限（1366 主承载）＋ 1280 中间断点（窄窗叠加）**」两件事，别再叫"1366 断点"，否则下一次回归复核会去找一个不存在的选择器。

---

## 四、判据④：零码改动自证

| 项 | 现值 |
|---|---|
| `git diff --numstat HEAD -- ui/pages/dashboard.py ui/styles.py tests/test_ergo_h912_13.py` | 空输出 |
| 三件 blob vs HEAD | 全部等值（`09401c05…`／`2c404fa1…`／`826386c8…`） |
| `git status --porcelain`（收工） | **2 行**：`?? docs/insights/l927-06-sampling.md`（同班 l927-06 产物）、`?? docs/insights/l927-07-dashboard-regression.md`（本档）——**均为卷宗点名产物，代码/测试/content 零改动** |
| `data/progress.db` sha8 | 跑测试前 `cd2dbce4` ＝ 跑测试后 `cd2dbce4`（子集内 `_render_achievements` 三枚 DAO 消费者已被 `_patch_dom` 全部 monkeypatch，且本仓 A5① 闸门 `core/progress.py:_guard_default_db_in_tests` 在 pytest 态禁开默认库） |
| 未跑 | 全量套件、dev server、浏览器、任何 SQL 写、任何 `git add/commit/…` |

---

## 五、与兄弟班产物的划界（避免同一件事两份账）

| 档 | 覆盖面 | 本档关系 |
|---|---|---|
| `docs/insights/l927-04-ergonomics-status.md`（同波 l927-04） | 人体工学**全表面**现状盘点（8 条发现逐条对账，含本条 :85 一行，其行号「已漂到注释区」的读数与本档一致） | 本档**不重复**其盘点；只补 ①定向子集 74 例的实测数 ②blob 等值这条可复算"在位"判据 ③§三 的 1366 语义订正 ④§六 的重复断言块 |
| `docs/insights/learning-ergonomics-scan-20260911.md:21`（缺陷原始登记） | 提出者 | 其「1366 断点」措辞按本档 §三 收窄；**未回改该档**（在册扫描档属历史证据，改写＝抹掉提出时的认知状态） |
| `zcode-bridge/done/h912-13-learn-ergo-fix.result.md` | 修复批 result | 按 brief §3a 到 `done/` 取到（卷宗写「done/ 检索」，本就在世，非否证）；其自述「345→348 全量」与本档"未跑全量"不冲突——本档只取子集 |

---

## 六、待裁条目（本单一律未动盘）

| # | 观察 | 证据 | 为何不在本单做 |
|---|---|---|---|
| C-1 | **测试件里有一整块 6 行断言被逐字粘贴了两遍**：`tests/test_ergo_h912_13.py:63-68` 与 `:69-74` 完全相同（`styles = STYLES.read_text(...)` ＋ `_BP_MID/_BP_NARROW` 三条断言）；`grep -c "_BP_MID = 1280"` ＝ 4（每块 2 次） | `git blame -L 62,75` ⇒ 下方块＝原物（`a56be3d` 09-13 起、断言体 `995fff4` 09-19），上方块＝`0327f1c`（09-22 l922-120）**插入**而非就地编辑 | 删重复＝改测试件＝**码改动**，判据④要求零码改动；且它是**幂等断言的冗余**，不影响防回归强度（不会漏判、只会多读一次文件）。建议开一张 chore 单收 |
| C-2 | 「1366 断点」话术与实际媒体查询集合不符（见 §三） | `ui/styles.py:5,6,7,300,305,326,347-348` | 改哪份档由主班定：`learning-ergonomics-scan-20260911.md` 是历史证据不宜回改；`plan.md`/规范类文档若要订正话术属写侧决定 |
| C-3 | **未覆盖面**：AppTest 读回的是 `Column.weight`（Python 侧权重），**不模拟 CSS 视口/媒体查询**，所以"1366 真机上不挤压"这件事在测试链上**不可证**；本单亦未起 dev server／未截图（红线：不起服务、不联网） | `tests/test_dashboard_achievements_row_centering.py` 自述「两轨互证，都不起 dev server、不截图」 | 真机 1366 验证＝日间人工/Playwright 档（且 learning 侧 Playwright 在册属联网域），不在只读子班范围 |
| C-4 | `_CARDS_PER_ROW = 3` 只覆盖「各语言通过情况」（5 门固定），成就墙另用 `cols_per_row=4`；两处的"每行 ≤4"由不同机制把守（前者纯函数断言、后者 AppTest 权重断言） | `ui/pages/dashboard.py:154`／`:469`、`tests/test_dashboard_achievements_row_centering.py` | 仅记档：若将来加第 6 门语言，`:154` 会排成 3+3（每卡仍 1/3 行宽），**无需改动即不破**，但 `test_ergo_h912_13.py` 里 5 门的夹具不会自动覆盖到 6 门 |
