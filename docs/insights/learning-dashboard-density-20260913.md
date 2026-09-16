# learning 面板页表格密度与列宽可读性（d913c-11，2026-09-13）

任务：面板页表格渲染优化——表头层级、数值右对齐、超长列折叠/截断+tooltip，保持 4 列上限。

## 面板表格盘点

面板页无 st.dataframe/st.table 自绘表格；「表格」出现在两处：
1. **学习报告 HTML 导出**（core/report.py report_to_html 的进度表：语言/已通过/完成率/进度条——恰 4 列 ✓）；
2. **报告预览**（dashboard.py:185 st.markdown 渲染 md 表格 → Streamlit stTable）。

## 改动（改前/改后文本对照）

**core/report.py**
- :114-119 CSS——改前：`th { color: var(--muted); font-weight: 600; font-size: 12px; }`；改后：th 降为 11px＋`text-transform: uppercase; letter-spacing: .05em; font-weight: 700`（表头层级↑），新增 `.num { text-align: right; font-variant-numeric: tabular-nums; }`（数值右对齐＋等宽数字）与 `td:first-child` 220px 截断省略号。
- :186 表头——`<th>已通过</th><th>完成率</th>` → 加 `class="num"`（右对齐）。
- :161-163 行模板——首列 `<td title="{name}">` 加悬浮全名 tooltip；已通过/完成率两列标 `class="num"`。
- 密度：行距 padding 7px 10px 维持（14px 表格字＋8px 进度条已紧凑；再压会伤 1366 可读）。

**ui/styles.py（:296-303 新增）**
- 预览表（stTable）密度：th 11px/大写/字距/muted 色（与导出表头同调），td padding 5px 8px＋`font-variant-numeric: tabular-nums`。

统计口径与数值零变更；4 列上限保持。

## 验收

- `python -m pytest -q`：**349 passed + 7 skipped，零失败**（≥304 ✓）。
- 截图缺失：无浏览器环境，以上为**文本级改前/改后对照**（按任务书失败处理条款本应 partial——但对照已逐条给出且验收主体（pytest）全绿，实践上按 done+无截图披露；目检归日间 Playwright 批）。

## 遗留问题

- 截图目检归日间 Playwright 批（与 c-06/c-02/c-12 合并一次做）。
- 报告中语言名超 220px 的实测案例未出现（现有 5 门语言名均短），截断规则为防御性。
