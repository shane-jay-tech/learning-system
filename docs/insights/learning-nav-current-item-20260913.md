# learning 导航当前项高亮单源化（d913c-09，2026-09-13）

任务：枚举所有「当前项高亮」实现点，收敛到一个判定函数。

## 高亮判定点：N=7 → 1

**改前（7 处散落，全在 app.py _sidebar）**：每项各自写 `type="primary" if route == X else "secondary"` 三元式——主页(:33)、学习路径(:37，含 {paths, path_detail} 别名)、诊断(:41)、语言项(:48-51，复合条件 route=="language" and selected_lang==lang)、面板(:56)、错题本(:60)。

**改后（判定单源）**：
- 判定函数 1：`ui/components.py::nav_is_active(current_route, routes, extra_condition=True)`（:184）——routes 支持单路由/别名集合，extra_condition 承载语言项附加条件；
- 渲染函数 1：`ui/components.py::nav_button(label, key, active, on_activate)`（:193）——primary/secondary 三元式唯一居所，docstring 明令勿在外再写；
- app.py 七个导航项全部改为数据化调用（app.py:33-55），零散三元式清零。

## 附带发现

- `ui/styles.py:180 .problem-card.active`：CSS 有定义但全仓无 Python 端输出 active 类——死样式（卡片实际用 solved/wrong 两态）。保留未删（样式清理留设计系统批）。

## 验收

- `python -m pytest -q`：**349 passed + 7 skipped，零失败**（≥304 ✓）。
- 路由与页面内容零变更（on_activate 行为与原内联块逐字等价：set route→rerun / navigate_to_problem）；未 commit。

## 遗留问题

- `.problem-card.active` 死样式清理留设计系统批（含 decided-by-product 的样式梳理）。
- 页面内其它按钮（如返回列表）非导航项，未纳入 nav_button。
