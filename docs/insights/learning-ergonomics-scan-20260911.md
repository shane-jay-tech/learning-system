# learning 前端人体工学有界只读走查（2026-09-12 夜间执行班，任务 p911r-42，零改码）

> 执行：GLM-5.3-Flash 夜间执行班 sweep-20260911-2300。技术栈实况：**Streamlit**（非 tsx 组件树），页面在 `ui/pages/`（home/dashboard/diagnostic/path/mistakes/language），全局样式 `ui/styles.py`，布局 `app.py:72-75`（layout="wide" + 侧栏展开）。静态只读走查（无浏览器自动化），行号基于当前工作树。

## 一、选样与理由

| 组件 | 选择理由（对应 plan.md 目标词） |
|---|---|
| `ui/pages/home.py`（330 行） | 「首屏清晰」与「任务易达」的主入口；含 hero/下一步/路径卡/总览/语言卡 |
| `ui/pages/dashboard.py`（526 行） | 「面板」最复杂布局（columns 密集、报告导出、AI 脉搏）；最能暴露 1366 断点问题 |
| `ui/pages/mistakes.py`（149 行） | 「错题本」关键闭环页（列表/重做/移除/上次点评） |

## 二、逐组件发现

### home.py
1. `home.py:67-75` 总览 4 列 metric_tile + `:80-88` 语言卡 2 列 + hero/next_action/path_cards——**768 高度下首屏即折叠**：hero+next_action+路径卡占满第一屏，总览与语言卡需滚动。复现：1366×768 打开主页即见。期望：首屏至少露出总览首行；实际：被路径卡推出。修复粒度：≤40 分钟（调整分区顺序/压缩 hero 高度）。
2. `:67` 与 `:80` 的列布局：`st.columns(4)`/`st.columns(2)` 在 1366+侧栏展开下每列 ~250px，metric_tile（`components.py:122`，min-height 84px）可容纳；语言卡 `lang_card_html`（`components.py:105`）为纯展示 HTML——**卡片不可键盘聚焦**（无 tabindex），但其无内嵌操作（操作按钮为独立 st.button，原生可聚焦）→ 判定「可接受，非缺陷」；若未来卡片内加链接需补 tabindex。修复粒度：≤40 分钟（补 CSS :focus-visible 规范）。
3. `home.py:162 except Exception:` 静默吞错——**状态辨识缺失**：加载失败会表现为「空数据」而非错误态。复现：数据文件损坏时首页显示空总览。期望：st.error 显式错误态；实际：静默回退。修复粒度：≤40 分钟。

### dashboard.py
1. `dashboard.py:85` `st.columns(min(n, 5))`——**1366 断点挤压**：5 列在侧栏展开的内容区（~1100px）每列仅 ~210px，卡片文字换行挤压；styles.py:275 的 flex-wrap 只在 ≤900px 生效，1024–1280 区间无中间断点。复现：1366×768 展开侧栏看推荐区。期望：≥5 列时降为 3-4 列或提前 wrap；实际：硬排 5 列。修复粒度：≤40 分钟（styles.py 增 @media (max-width:1280px) 规则 + 列数上限 4）。
2. `dashboard.py:124`、`:149 except Exception:` 静默吞错（同 home.py:162）——推荐/脉搏数据失败无错误态。修复粒度：≤40 分钟（每处补 st.warning/error）。
3. 状态辨识正面：`:74` 空提交 info、`:103` 题库未载 info、`:161/170` spinner——加载/空态辨识良好（已走查项，无缺陷）。

### mistakes.py
1. `mistakes.py:73/101/141` `st.columns([4,1])` 右列操作按钮——1366 下右列 ~180px，按钮文字「重做/移除」可容纳；768 高度无碍。判定：无缺陷。
2. `:113 expander "上次代码与点评"` 默认折叠——上次尝试结果需手动展开（可接受的层级设计；若错题本高频使用可改 expanded=True，属产品拍板非缺陷）。
3. `:134` 空弱项 info ✓；已走查项清单：列表空态（有 info）、操作按钮聚焦（Streamlit 原生）、危险操作（移除）无确认弹层——**发现**：`mistakes.py` 移除弱项无二次确认，误触即丢（复现：点右列移除按钮立即生效）。修复粒度：≤40 分钟（加 confirm checkbox 或 st.popover）。

## 三、不做范围（未覆盖）

诊断页（diagnostic.py）、路径页（path.py）、语言主页（language.py）、app 侧栏本体（`_sidebar`）、深层 expander 内交互——留下一批；浏览器实测（768 实机滚动/热区）无 Playwright，本单仅静态走查，实机项留 Playwright 就绪后（p911r-36 清单）。

## 四、零改动声明

未改任何前端/样式代码；只读 grep/sed/wc；未联网；未 commit/push；`git status --short` 无本单文件变更。
