# learning 键盘焦点覆盖面静态审计（unsafe_allow_html 面，l922-118，2026-09-22）

任务：盘点各页 `unsafe_allow_html=True` 自绘 HTML 块是否含可交互元素、是否落在 `ui/styles.py` 的 focus ring 规则之外，输出遗漏清单与结论档。
约束：本单**零源码改动**（只做只读审计＋本档）。

## 一、口径与总数（完成标准 ①）

任务书给定口径：

```
$ grep -rn "unsafe_allow_html=True" ui/ | wc -l
32
```

**N = 32**。按文件分布（`grep -rc` 复核）：

| 文件 | 处数 |
|---|---|
| `ui/pages/dashboard.py` | 10 |
| `ui/pages/language.py` | 9 |
| `ui/components.py` | 7 |
| `ui/pages/home.py` | 5 |
| `ui/styles.py` | 1 |
| **合计** | **32** |

⚠️ **口径盲区（F-3）**：任务书的 `ui/` 范围漏掉了仓库根 `app.py` 的 5 处（:24、:32、:39、:48、:54）。补测：

```
$ grep -rn "unsafe_allow_html" --include=*.py . | grep -v "^./ui/" | grep -v "/tests/"
app.py:29 / app.py:32 / app.py:39 / app.py:48 / app.py:56   （其余命中均在 .venv 内，非本仓码）
```

全仓真实总数＝**37**。5 处 `app.py` 块内容是侧栏品牌卡、三个分组标签（`.sidebar-label`）、侧栏脚注——纯展示 div，**无可交互元素**，不改变本单结论；但下次盘点建议把口径改成 `--include=*.py` 再排除 `.venv`，否则侧栏永远在扫描面外。

## 二、判据：什么叫「落在焦点规则外」

`ui/styles.py` 现行两组规则（锚点复核**未漂移**，行号与任务书一致）：

- `ui/styles.py:207-208` `button:focus-visible, [role="radio"]:focus-visible, input:focus-visible, textarea:focus-visible, [data-baseweb="select"]:focus-within`
- `ui/styles.py:214-215` `a:focus-visible, [data-testid="stSidebar"] a:focus-visible, [role="tab"]:focus-visible, [data-testid="stSidebar"] button:focus-visible`

因此「需要焦点环」的元素集合＝原生可聚焦元素：`a[href] / button / input / textarea / select / summary / [role=tab|radio] / [tabindex] / iframe / audio|video[controls]`，加上带 `onclick` 的任意元素。

全量枚举判据（对 `ui/*.py ui/pages/*.py app.py` 生成 HTML 的字符串做标签级搜索）：

```
$ grep -rn "<a \|<a>\|href=\|onclick\|tabindex\|<button\|<input\|<label\|<select\|<summary\|<details\|role=\|<textarea\|<form" ui/*.py ui/pages/*.py | grep -v "^ui/styles.py"
ui/components.py:99:        f'<div class="hero" role="banner"><h1>{html.escape(title)}</h1>'
```

**唯一命中是 `role="banner"`（landmark，非交互、不可聚焦）。** 另测媒体标签面：

```
$ grep -rn "<img\|<svg\|<iframe\|<canvas\|<progress\|<table" ui/*.py ui/pages/*.py app.py
（无输出）
```

⇒ 结论：**32（37）处 unsafe_allow_html 块里没有任何可交互/可聚焦元素**，全部是 `div / span / b / h1 / p` ＋ 内联 `style`，文案侧统一走 `html.escape()`。
完成标准 ② 的「可交互项 100% 给规则行号」因此是**空集满足**（0 个可交互项），下面逐条分类表把这一空集显式钉住，不以「无」蒙过。

## 三、逐条分类表（完成标准 ②）

分类法：
- **A＝纯静态展示**（无可聚焦元素，焦点规则 N/A，无须覆盖）
- **B＝内容通道**（本块自身静态，但相邻一行 `st.markdown(用户/AI 文本)` 可能渲染出 `a[href]`，该情形由 :214 覆盖）
- **C＝样式注入本体**（不是内容块，不适用）

| # | 位置 | 渲染内容 | 类 | 可聚焦元素 | 覆盖判定 |
|---|---|---|---|---|---|
| 1 | `ui/components.py:98-101` | `hero` 标题块（`role="banner"`） | A | 无 | N/A |
| 2 | `ui/components.py:130` | `.section-title` | A | 无 | N/A |
| 3 | `ui/components.py:142-145` | `verdict pass` | A | 无 | N/A |
| 4 | `ui/components.py:148-151` | `verdict fail` | A | 无 | N/A |
| 5 | `ui/components.py:158` | `io_block`（expected/actual） | A | 无 | N/A |
| 6 | `ui/components.py:165-167` | `ai-feedback` 标签条 | **B** | 潜在 `a[href]`（来自 :169 `st.markdown(text)`） | 已覆盖 :214 |
| 7 | `ui/components.py:174` | `stderr_block`（`html.escape`） | A | 无 | N/A |
| 8 | `ui/pages/dashboard.py:94` | `_streak_html` 连续打卡卡 | A | 无 | N/A |
| 9 | `ui/pages/dashboard.py:96` | `metric_tile` 累计提交 | A | 无 | N/A |
| 10 | `ui/pages/dashboard.py:98` | `metric_tile` 已通过题数 | A | 无 | N/A |
| 11 | `ui/pages/dashboard.py:100` | `metric_tile` 错题待复习 | A | 无 | N/A |
| 12 | `ui/pages/dashboard.py:162-164` | 推荐条目行（icon＋`<span>` 难度） | A | 无 | N/A（跳转由同行 `st.button` 承担，覆盖 :207） |
| 13 | `ui/pages/dashboard.py:302-304` | **最近活动 div 行** | A | 无 | N/A |
| 14 | `ui/pages/dashboard.py:340-342` | 跨路径推荐条目行 | A | 无 | N/A |
| 15 | `ui/pages/dashboard.py:406-408` | 成就徽章卡 | A | 无 | N/A |
| 16 | `ui/pages/dashboard.py:466-468` | 贡献热力图（周列拼装） | **A＋** | 无（但 :446 格子带 `title=` 提示，见 F-2） | N/A |
| 17 | `ui/pages/dashboard.py:566-568` | 开放题能力条 | A | 无 | N/A |
| 18 | `ui/pages/home.py:71` | `metric_tile` 题库总题数 | A | 无 | N/A |
| 19 | `ui/pages/home.py:73` | `metric_tile` 已通过 | A | 无 | N/A |
| 20 | `ui/pages/home.py:75` | `metric_tile` 错题待改 | A | 无 | N/A |
| 21 | `ui/pages/home.py:77` | `metric_tile` 已尝试 | A | 无 | N/A |
| 22 | `ui/pages/home.py:93` | `lang_card_html` 语言卡 | **A＋** | 无（hover 反馈见 F-4） | N/A |
| 23 | `ui/pages/language.py:226-228` | AI 变式题提示条 | A | 无 | N/A |
| 24 | `ui/pages/language.py:369-371` | 「第 x / n 个知识点」进度行 | A | 无 | N/A（左右翻页是 `st.button`，覆盖 :207） |
| 25 | `ui/pages/language.py:390` | 「对话历史」小标题 | A | 无 | N/A |
| 26 | `ui/pages/language.py:395-397` | 追问历史·你（气泡） | A | 无 | N/A |
| 27 | `ui/pages/language.py:401-404` | 追问历史·AI 标签条 | **B** | 潜在 `a[href]`（:406 `st.markdown(msg["text"])`） | 已覆盖 :214 |
| 28 | `ui/pages/language.py:462-464` | 做题中问·你 | A | 无 | N/A |
| 29 | `ui/pages/language.py:467-470` | 做题中问·AI 标签条 | **B** | 潜在 `a[href]` | 已覆盖 :214 |
| 30 | `ui/pages/language.py:516-518` | 知识点随问随答·你 | A | 无 | N/A |
| 31 | `ui/pages/language.py:521-524` | 知识点随问随答·AI 标签条 | **B** | 潜在 `a[href]` | 已覆盖 :214 |
| 32 | `ui/styles.py:341` | `inject()` 注入 CSS 本体 | **C** | — | 不适用 |
| 33-37 | `app.py:29/32/39/48/56` | 侧栏品牌卡＋三个分组标签＋脚注 | A | 无 | N/A（本档追加，超出任务书 grep 口径） |

分类小计：A＝31（ui/ 内，含 #32 之外的全部）、B＝4、C＝1；ui/ 外另 5 处 A。**可交互项＝0。**

**B 类的现实概率评估**：内容通道能否真的长出 `<a>`，取决于题库与 AI 正文是否含链接。实测题库侧：

```
$ grep -ro "](http" content/ data/ | wc -l
0
```

⇒ 当前题库零外链；B 类只在「AI 回包含链接」时生效，而该路径由 `ui/styles.py:214` 的 `a:focus-visible` 兜住，**无须新增规则**。

## 四、补测：原生控件侧的覆盖映射（真正有遗漏的地方在这里）

`unsafe_allow_html` 面干净，不等于焦点面干净。把 `ui/ + app.py` 实际用到的 Streamlit 原生控件枚举出来对表（`grep -oE "st\.(tabs|expander|...)"` 计数）：

| 控件 | 用量 | 命中选择器 | 判定 |
|---|---|---|---|
| `st.button` | 43 | :207 `button:focus-visible` | ✓ |
| `st.text_area` | 5 | :208 `textarea:focus-visible` | ✓ |
| `st.selectbox` | 2 | :208 `[data-baseweb="select"]:focus-within` | ✓ |
| `st.radio` | 2 | :207 `[role="radio"]`＋`input` | ✓ |
| `st.tabs` | 2 | :215 `[role="tab"]` | ✓ |
| `st.file_uploader` | 1 | base-web 内 `button`＋隐藏 `input` | ✓（推演，未经浏览器验证） |
| **`st.expander`** | **12** | **无** | **✗ 遗漏 F-1** |
| `st.progress` / `st.caption` | 3 / 23 | 非聚焦面 | N/A |

`st.expander` 在 Streamlit 1.58 里渲染成 `<details>` ＋ **原生 `<summary>`**，从安装包的构建产物内取证：

```
$ grep -rhoE ".{40}styled\(.{0,3}summary.{60}" .venv/.../static/js/index.*.js
Iy=_(`summary`,{target:`e1wbovuq4`})(({theme:e,isStale:t,expanded:n,isCompact:r})=>({position:`relative`,...
```

同包内 Streamlit 自己判定可聚焦元素的查询串也明确含 `summary`：
`` ...`input:enabled`,`a[href]`,`area[href]`,`summary`,`iframe`,`object`,`embed`,`audio[controls]`,... ``

而本仓 `ui/styles.py:229` 已经在给这个 `summary` 定制尺寸（`[data-testid="stExpander"] summary { min-height: 46px; }`），说明作者知道它是 `summary` ——只是焦点规则那一组没带上它。

## 五、遗漏清单与结论档

**结论档：B（合格，无高危；1 条低危遗漏＋3 条信息项）** —— 不是 A，因为 F-1 确实是可复现的规则缺口；不是 C，因为没有任何「键盘用户看不见焦点」的硬违规（见 F-1 缓解项）。

| 编号 | 严重度 | 事实 | 证据 | 建议出口（本单不实施） |
|---|---|---|---|---|
| **F-1** | 低（一致性缺口，非可访问性违规） | `summary` 未被任何 focus 规则覆盖，12 处 expander 展开头键盘聚焦时拿到的是浏览器默认焦点环，与品牌环（3px `rgba(91,91,214,.28)`＋2px offset）不同源 | `ui/styles.py:207/214` 选择器清单＋`ui/styles.py:229` 反证 summary 存在 | 在 :214 那组末尾追加 `[data-testid="stExpander"] summary:focus-visible`（一行 CSS，属交互性改动，须另开单＋浏览器目检） |
| **F-2** | 信息 | 热力图格子 `title="YYYY-MM-DD: N次提交"` 只有鼠标 hover 能取到，键盘不可达 | `ui/pages/dashboard.py:446` | 若要收口属「等价替代文本」议题（可给每周/每月加可见摘要文案），不是焦点环问题，建议并入首屏动作出口那批人工裁决 |
| **F-3** | 信息 | 任务书 grep 口径 `ui/` 漏 `app.py` 5 处，全仓真数 37 非 32 | 第一节两条命令 | 派单模板把口径改成 `--include=*.py` 排除 `.venv` |
| **F-4** | 信息（轻微可点错觉） | `.lang-card:hover` 改了边框色＋阴影，但该卡无可点语义、也无对应 focus 态；`transition` 也只为 hover 服务 | `ui/styles.py:152-157`、`ui/components.py:105-119` | 二选一：删 hover 效果，或让卡片真能跳转（后者属交互设计变更，需拍板） |
| **F-5** | 口径声明 | 本单全部为**静态推演值**（读源码字符串＋安装包产物），**未经自动验证**：无浏览器环境，未做 Tab 走查、未截屏、未量任何像素 | 本机无 Playwright/Selenium（仓内 `requirements.txt` 无相关依赖，`tests/` 内 `grep focus-visible` 零命中） | 待校准假设点见第七节 |

## 六、对 learning-focus-visible-20260913「框架级元素留拍板」条目的状态更新（完成标准 ③）

原条目（`docs/insights/learning-focus-visible-20260913.md:22`，逐字）：

> Streamlit 顶部 toolbar 与对话框关闭键属框架级元素，主题选择器覆盖不到，如需覆盖须评估 ::part/全局 *:focus-visible 兜底（有样式污染风险，留拍板）。

**更新（2026-09-22，l922-118 只读审计）——状态：留拍板 → 建议「不做全局兜底，改精确选择器增量」，仍未实装。**

依据三条新事实：

1. **兜底风险比原估的低，但污染面是真的**：全仓 `grep -n "outline" ui/styles.py` 只命中 :209 与 :216 两行（都是「加描边」），**没有任何 `outline: none` / `outline: 0` 复位**。⇒ 未被规则命中的可聚焦元素（`summary`、toolbar 关闭键等）**仍保留 UA 默认焦点环**，即"看不见"并非现状，"不统一"才是。这意味着 2.4.7 目前不违规，也就**不支持为它上 `*:focus-visible` 这种高污染兜底**。
2. `::part` 路线走不通：Streamlit 1.58 的侧栏/工具条不是自定义元素封装，`ui/styles.py` 全文与安装包产物侧都没有可用的 part 名；本仓现有覆盖全部靠 `data-testid` 属性选择器达成（:214-:215 就是这条路线），继续沿用即可。
3. 原条目点名的「顶部 toolbar / 对话框关闭键」在本仓**当前无对应渲染面**：`ui/ + app.py` 未使用 `st.dialog`、`st.chat_*` 之外的弹层组件（`grep -c` 侧零命中 dialog），关闭键属"未来引入才需要复议"的开放项。
4. 真正现在就有缺口的是同档没点到的 `summary`（本档 F-1），建议把它作为下一个精确选择器增量的落点，代价＝1 行 CSS，污染面＝0。

⇒ **给主班的收口建议**：把 20260913 那条遗留从「留拍板（要不要全局兜底）」改写为「已否决全局兜底方案，剩余缺口收敛为 `[data-testid="stExpander"] summary:focus-visible` 一处精确增量＋浏览器目检」。本单受「零源码改动」约束未代改那两档，请人工或后续单落笔。

## 七、待浏览器校准的假设点（本档所有结论的边界）

1. 「`summary` 键盘可达」＝依据安装包源码产物推得，**未在真实浏览器里用 Tab 验证过** Streamlit 的 details 封装是否吞掉了 summary 的可聚焦性。
2. 「UA 默认焦点环未被吞」＝依据本仓 CSS 无 `outline:none` 推得；Streamlit 自带 emotion 样式表里是否存在 outline 复位**未逐条排查**（若存在，F-1 的严重度要从「低」升为「违规」）。
3. 「`st.file_uploader` 走 button＋隐藏 input」＝base-web 通用结构推演，未经 DOM 检查。
4. 「B 类内容通道实际不产出 `<a>`」＝只统计了题库静态内容（`](http` 命中 0），**AI 运行时回包不在此口径内**。
5. 锚点：`ui/styles.py:207/:214` 复核**未漂移**；任务书正文「dashboard.py:266 最近活动 div 行」**已漂到 :304**（本档第三节按磁盘实况记）。
6. 本档零像素/视口结论：焦点环粗细（3px）与 offset（2px）在 1366×768 下是否与相邻卡片边框重叠，属目检项，未测。

## 八、验收自证（真实命令＋输出）

```
$ grep -rn "st\.dialog\|st\.chat_message\|st\.chat_input\|st\.popover\|st\.badge" ui/ app.py
（无输出）                              # 支撑第六节第 3 条：本仓无弹层/对话框渲染面

$ grep -rn "outline: *none\|outline:none\|outline: *0" ui/ app.py
（无输出）                              # 支撑第六节第 1 条：无 outline 复位，UA 焦点环仍在

$ grep -n "outline" ui/styles.py
209:  outline: 3px solid rgba(91, 91, 214, .28) !important; outline-offset: 2px;
216:  outline: 3px solid rgba(91, 91, 214, .28) !important; outline-offset: 2px;

$ git status --porcelain
?? docs/insights/learn-focus-surface-audit-20260922.md
```

⇒ 工作树只有本档一个未跟踪文件，`ui/`、`app.py`、`core/` **零改动**（完成标准 ④）；HEAD 仍 `47e4b2d`，本单未 `git add`。
