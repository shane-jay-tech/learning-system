# learning F-1 上行风险排查：Streamlit 1.58 自带样式里的 outline 复位普查（l923-17，2026-09-23，只读零源码改动）

> 任务：`zcode-bridge/inbox/l923-17.task.md`（已归档 `done/`）。执行班
> `qoder-executor-20260923-0022-learn5`，HEAD `1bafa0c`，被排查对象是
> `.venv/Lib/site-packages/streamlit/`（**streamlit 1.58.0**，`python -c "import streamlit; print(streamlit.__version__)"` 现取）。
>
> 结论一句话：**F-1 维持「低・一致性缺口」，不升为 WCAG 2.4.7 违规**——但这次排查**新登记**
> 了两条原先没被点名的残留（焦点环对比度、`:focus` 与 `:focus-visible` 的条件错位），
> 那两条才是 F-1 真正需要浏览器目检的部分。

## 一、l922-118 留的那个口子，现在结掉了

`zcode-bridge/done/l922-118-focus-surface-audit.result.md` 遗留问题 2 原话：

> **F-1 严重度有一个未排除的上行风险**：Streamlit 自带 emotion 样式表是否含 `outline` 复位
> **未逐条排查**（只查了本仓侧）。若存在复位，F-1 从「一致性缺口」升为「2.4.7 违规」——
> 需要真浏览器才能判，本机无环境。

同口径也抄进了班志 `executor-drain-discipline-20260923.md` §十二 learning 节（焦点面 F-1）。

本单把这条**逐条排查做完**（静态、离线、零源码改动），并把「若存在复位⇒升格」这个条件句
按实测收窄：**复位确实存在，但它带着替代焦点指示器，因此不触发升格**。
原判据「需要真浏览器才能判」**部分成立**：判"有没有指示器"静态就够了（本单已判），
判"指示器够不够显眼"仍要浏览器（见第五节两条残留）。

## 二、口径与覆盖计数（完成标准 ①）

两条通道都跑（卷宗只点了 `css/` 目录，**实测 emotion 运行样式的宿主是 JS chunk，不是那三份 CSS**，
只按卷宗口径跑会得出「无复位」的假结论——这是本单最重要的一条方法论修正）：

| 通道 | 覆盖 | 件数 | 体积 |
|---|---|---|---|
| A 静态 CSS | `.venv/Lib/site-packages/streamlit/static/static/css/*.css` | **3**（全量，一件不漏） | 12,276 + 34,104 + 29,962 B |
| B emotion 源码 | `.venv/.../streamlit/static/static/js/*.js` | **279** | 19,426,608 B |

清单（A 通道全部三件）：`DataFrame.DUkanX9_.css`、`DeckGlJsonChart.s6LXjV0D.css`、`index.7xf2Fe_c.css`。

B 通道 279 件里 `outline:` 属性共 **104 条**，按值分类：

| 类别 | 条数 | 说明 |
|---|---|---|
| **复位**（`none` / `0` / `transparent` / `unset` / `initial`） | **90** | 分属 45 个 emotion 组件归属组 |
| 恢复/描边（含 `solid` / `dashed` / `var(`） | 8 | 多为 `outline: e.$isFocusVisible ? \`solid 2px ${accent}\` : ...` 这类**焦点态描边** |
| 非 CSS 属性（误报，已排除） | 5 | Prism.js 语法表 `outline:{pattern:/<[^>]+>/…}`、deck.gl `outline:{deprecatedFor:`stroked`}`、字符串值 `` outline:`outline` `` |
| 模板插值不可判 | 1 | 值整体由变量拼出 |
| 未分类归入「其它」 | 0 | — |

复算：`PYTHONIOENCODING=utf-8 python tmp/l923-17/scan_outline.py`（本仓 `tmp/` 已 gitignore，`/tmp/` @ `.gitignore:19`；
探针输出全文留在 `tmp/l923-17/scan_outline.txt`，77 行，含 45 组完整归属表）。

## 三、A 通道逐条摘录（完成标准 ②）

**结论：静态 CSS 三件里的 12 条 outline 复位全部落在第三方控件命名空间内，与 `summary` /
`stExpander` / 通用 `*` 无关（三类点名面在复位选择器中出现 0 次）。**

`DataFrame.DUkanX9_.css`（10 条，glide-data-grid `st.dataframe` 内部）：

```
.gdg-r17m35ur                                      { outline:none }
.gdg-s1dgczr6 canvas                               { outline:none }
.gdg-d19meir1 .gdg-clip-region input.gdg-input     { outline:none }
.gdg-d19meir1 .gdg-clip-region textarea.gdg-input  { outline:none }
.gdg-seveqep input                                 { outline:none }
.gdg-seveqep button                                { outline:none }
.gdg-s1wtovjx                                      { outline:none }
.gdg-lw5nakc>button                                { outline:none }
.gdg-lw5nakc .gdg-link-title-editor>input          { outline:none }
.gdg-lw5nakc .gdg-link-title-editor>button         { outline:none }
```

`DeckGlJsonChart.s6LXjV0D.css`（2 条，mapbox-gl 控件）：

```
.mapboxgl-ctrl-group button        { outline:none }
.mapboxgl-ctrl-attrib-button       { outline:none }
```

`index.7xf2Fe_c.css`：**0 条 outline 属性**；且 `summary` / `details` 两个词在该文件里出现
**0 次**（`grep -o 'summary\|details' index.7xf2Fe_c.css | wc -l` ⇒ 0）。

「通用 `*` 复位」专项：三件里 `*` 选择器**只出现 2 次**，都不带 outline
（`.gdg-mnuv029>*{margin:0}`、`.gdg-e1wnlokz *{box-sizing:border-box}`）
⇒ **不存在**「`* { outline: none }` 这种全局抹平」，卷宗点名的第三个可能性排除。

本仓侧对照（`grep -n "outline" ui/styles.py`，现读）：**只命中 2 行，且都是「加描边」不是复位**：

```
ui/styles.py:209:  outline: 3px solid rgba(91, 91, 214, .28) !important; outline-offset: 2px;
ui/styles.py:216:  outline: 3px solid rgba(91, 91, 214, .28) !important; outline-offset: 2px;
```

## 四、B 通道决定性证据：`summary` 确实被复位，但同时被换了指示器

Expander 一族的 emotion 定义（`static/js/index.BfkDCGNp.js`，`@260957` 起是 `details`，
`@261594` 起是 `summary`，同族 target 前缀 `e1wbovuq*`）：

```js
// index.BfkDCGNp.js@261594
_(`summary`, { target: `e1wbovuq4` })(({ theme: e, isStale: t, expanded: n, isCompact: r }) => ({
  position: `relative`, display: `flex`, width: `100%`, minWidth: 0, overflow: `hidden`,
  "&:focus":        { outline: `none` },              ← 复位：存在
  "&:focus-visible":{ boxShadow: e.shadows.focusRing },← 补偿：焦点环换成 box-shadow
  fontSize: `inherit`, alignItems: `center`, cursor: `pointer`, listStyleType: `none`,
  "&::-webkit-details-marker": { display: `none` }, …
```

补偿用的 `focusRing` 定义（`static/js/utils.paqmDQdB.js`，主题派生函数）：

```js
… focusRingWidth: `0.2rem` …
Us = e => { … return { …n,
  focusRing:        `0 0 0 ${r} ${x(e.primary, .5)}`,   ← 0.2rem、主色 50% alpha
  focusRingSubtle:  `0 0 0 ${r} ${x(e.darkenedBgMix25, .5)}`,
  focusRingOutline: `0 0 0 1px ${e.primary}`,
  focusRingMuted:   `0 0 0 ${r} ${x(i, .8)}` } }
```

⇒ 键盘 Tab 走到 `<summary>` 时：`outline` 被抹，但**同一组件**给了一圈
`0 0 0 0.2rem rgba(primary,.5)` 的 box-shadow 环。焦点**看得见**，只是手段不是 `outline`。

其余 44 组复位的分布（完整表在 `tmp/l923-17/scan_outline.txt`）：`div ebngmqm6` 9 处、
`button e1lncrqy1` 3 处、`small egah9gy1` 3 处、`img exttvjz4` 2 处，以及
base-web 系输入件（`NumberInput` / `DateInput` / `DateTimeInput`）若干。
按「同组件 ±1200 字符窗口内是否出现 `&:focus-visible`」粗判，**26 组带补偿 / 19 组窗口内未见**。
⚠️ 那 19 组**不等于**「无焦点指示」：base-web 输入件多以 `:focus` 的 border/boxShadow 变化表达，
窗口启发式会漏。本单只把 `summary` 一族逐条读到底，其余按登记面处理，不据此下结论。

## 五、F-1 严重度判定（完成标准 ③，二选一）

**判定：一致性缺口（维持 l922-118 的「低」），不升为 WCAG 2.4.7 违规。**

依据三条，全部指向上面已摘录的原文行：

1. **2.4.7 Focus Visible（A 级）的判据是「键盘焦点有可见指示」，不规定实现手段。**
   `summary` 在 `:focus-visible` 上拿到 `boxShadow: focusRing` ⇒ 指示器存在 ⇒ 不构成违规。
   l922-118 那句「若存在复位⇒升格」的前提（复位＝抹掉指示器）**不成立**。
2. **本仓那两组品牌焦点环与 emotion 的复位不在同一条件下打架**：
   `ui/styles.py:208-209 / 214-216` 选择器是 `:focus-visible`，emotion 的复位是 `:focus`。
   且本仓声明带 `!important` 而 emotion 的 `outline:none` 不带 ⇒ 真去补那一行 CSS 时
   **本仓声明会赢**，修法可行性不受影响（这是给 F-1 实装单的正面结论）。
3. **UA 默认环确实被拿走了**，但这不等于"看不见"：l922-118 当时靠「本仓无 `outline:none`」
   推「summary 保留 UA 默认环」，**这条推论本单否证**（见下遗留 1）——只是被否证后
   结论仍站得住，因为换成了 streamlit 自己的 focusRing 顶上。

**同时新登记两条此前未点名的残留（这两条才是 F-1 真正需要浏览器的部分）：**

- **R-1 焦点环对比度**：`focusRing = 0 0 0 0.2rem rgba(primary, .5)`。50% alpha 的环在
  深浅背景上是否满足 WCAG **1.4.11 非文本对比 3:1**（以及新增的 **2.4.11 Focus Appearance**
  对最小面积/对比的要求）**静态判不了**——要取运行时主题色与背景色实算。
  注意：这条属「指示器质量」，不改变 2.4.7「指示器有无」的判定。
- **R-2 条件错位窗口**：复位挂 `:focus`、补偿挂 `:focus-visible`。凡是「`:focus` 成立而
  `:focus-visible` 判假」的场景（脚本 `.focus()`、部分嵌入式/iframe 聚焦、个别浏览器启发式），
  summary 会处于「outline 已抹、阴影未加」的双无状态。键盘 Tab 路径**不落进**这个窗口
  （Tab 一定触发 `:focus-visible`），故不影响本次判定；但它是真实存在的一条窄面，
  且**不受本仓控制**（在 streamlit 侧），只能上游提 issue 或本仓用 `!important` 覆盖时一并兜。

## 六、与本仓 12 处 expander 的关系（F-1 实体重述）

F-1 的缺口本体**不在 streamlit 侧**，而在本仓一致性：`ui/styles.py:229`
`[data-testid="stExpander"] summary { min-height: 46px; }` 已经在给这个 `summary` 定制尺寸
（作者知道它是 summary），唯独 :207/:214 两组焦点规则的选择器清单没带上它 ⇒
12 处 `st.expander` 展开头拿到的是 **streamlit 的 0.2rem 半透明阴影环**，
而其余可聚焦元素拿的是**本仓 3px + 2px offset 的品牌描边环**。

⇒ 收口建议不变（l922-118 已给）：`ui/styles.py` 那组末尾追加
`[data-testid="stExpander"] summary:focus-visible` 一行 CSS。**属交互性改动，本单受
「零源码改动」约束未做**，且实装后要连 R-1（对比度）一起在浏览器目检。

## 七、否证与未决（诚实栏）

1. **否证 l922-118 的一条推论**：其「缓解事实」写「全仓无 `outline:none` 复位 ⇒ 未被规则命中的
   可聚焦元素仍保留 UA 默认焦点环」。本仓侧确实无复位，但**streamlit 侧对 `summary` 有复位** ⇒
   summary 拿的不是 UA 默认环。该句作为「看不见焦点并非现状」的**结论仍成立**（有 focusRing 顶上），
   作为「UA 默认环仍在」的**依据不成立**。l922-118 §待校准假设点 2 这条可以按本档结案。
2. **否证卷宗的方法口径**：卷宗写「静态 grep 排查可行」并只指 `static/css/`。
   实测 CSS 三件里 `summary` 一次都没出现（`index.7xf2Fe_c.css` 连 `summary|details` 都是 0 命中），
   **expander 样式全在 JS chunk 的 emotion 对象里**。按卷宗只跑 CSS 会得出
   「无复位 ⇒ 严重度维持」的**过程错误型假结论**（结论碰巧相同，证据链是空的）。
3. **未决：版本适用边界**。本档所有 JS 偏移量与 target 名（`e1wbovuq4` 等）绑
   **streamlit 1.58.0 的本机安装包**。升级后 target 哈希会变，但「summary 带 focus 复位 +
   focus-visible 用 focusRing」这一结构是否保持，需在升级复测时重跑本探针。
4. **未决：本仓是否用了自定义主题**。`focusRing` 的 alpha 恒定 `.5`，但 `e.primary`
   取自运行时主题；本仓 `ui/styles.py` 是注入 CSS 变量（`--primary: #5B5BD6`）而非
   streamlit theme config（本档未去核 `.streamlit/config.toml` 是否有 theme 段——
   不属本单判据，留给 R-1 的浏览器实测一并核）。

## 八、验收自证（完成标准逐条）

| 判据 | 结论 | 复算命令 |
|---|---|---|
| ① 覆盖目录下全部 `*.css`（计数与清单） | **达成** | `ls .venv/Lib/site-packages/streamlit/static/static/css/*.css` ⇒ 3 件，清单见第二节；`find .venv/Lib/site-packages/streamlit/static -name '*.css' \| wc -l` ⇒ **3**（static 树下无第四件） |
| ② 每条复位命中给文件名＋选择器/属性摘录（无命中也明示检索式） | **达成** | 第三节 CSS 12 条逐行；第四节 summary 原文＋focusRing 定义；`tmp/l923-17/scan_outline.txt` 存 45 组全表。检索式：`\boutline\s*:\s*` 取值后按 `none/0/transparent/unset/initial` 判复位 |
| ③ F-1 严重度二选一并给依据 | **达成＝「一致性缺口」** | 第五节三条依据；另登记 R-1/R-2 两条残留 |
| ④ 零源码改动（`git diff` 只含本档） | **达成（本单口径）** | `git status --porcelain`：本单只新增 `docs/insights/learn-focus-f1-outline-static-20260923.md` ＋ 同批改 `learn-insights-index-20260918.md` 两行；`ui/` `core/` `tests/` 无本单改动（工作树里另有 l923-15／l923-16 的在途改动，归属见那两单 result） |

索引闭合：新增本档后 `docs/insights/*.md` 与索引表条目数需同步 ⇒
`PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q`（读数见 result）。
探针：`tmp/l923-17/scan_outline.py`（可重跑）、`tmp/l923-17/scan_outline.txt`（本次全量输出）。
