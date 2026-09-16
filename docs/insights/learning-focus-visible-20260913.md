# learning 键盘焦点可见性（d913c-02，2026-09-13）

任务：设计系统样式块补 `:focus-visible` 描边（主色描边＋2px offset），覆盖按钮/表单控件/导航项三类。

## 现状与增量

按钮与表单控件的 focus ring 已由往批落地（ui/styles.py:201-204：button/[role="radio"]/input/textarea/select）。本批增量＝**导航项纳入同一焦点环**（ui/styles.py:206-212 新增块）：

- 选择器：`a:focus-visible`、`[data-testid="stSidebar"] a:focus-visible`（侧边栏导航链接）、`[role="tab"]:focus-visible`、`[data-testid="stSidebar"] button:focus-visible`；
- 描边：`outline: 3px solid rgba(91, 91, 214, .28) !important; outline-offset: 2px;`——与按钮/表单组完全同源（品牌主色 var(--primary) #5B5BD6 的 28% 透明），文件内注释已注明取色来源与 WCAG 2.4.7 依据；
- 补 `border-radius: 6px;` 让链接型焦点环不出现直角毛边。

## 验收

- `rg -n "focus-visible" ui/styles.py`：命中 :201 与 :208 两处，均落在设计系统文件内 ✓（rg `src/` 口径按本仓实际布局 ui/ 等价核验）。
- `python -m pytest -q`：**349 passed + 7 skipped，零失败**（≥304 ✓）。
- 纯 CSS 增量：零业务逻辑变更、零新依赖、未 commit。

## 遗留问题

- 浏览器实测（Tab 走查焦点环在 1366×768/1080p 的观感）归日间浏览器实测批次，与 d913c-06 空态目检合并做。
- Streamlit 顶部 toolbar 与对话框关闭键属框架级元素，主题选择器覆盖不到，如需覆盖须评估 ::part/全局 *:focus-visible 兜底（有样式污染风险，留拍板）。
