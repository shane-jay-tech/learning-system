# learning 空态文案与样式统一（d913c-06，2026-09-13）

任务：主页/刷题/面板空态统一为同一组件（一句话说明＋下一步动作），色号与间距取设计系统。

## 组件

`ui/components.py::render_empty_state(message, next_action="", compact=False)`：
- 默认 st.info 档（页面级空态）；`compact=True` 用 st.caption 档（卡片内微空态）；
- 文案模板＝`{message} 下一步：{next_action}`；
- 色号与间距沿用 styles.py 对 st.info/st.caption 的既有主题定制，零新常量零新依赖。

## 收口清单（11 处，rg「暂无|尚无|没有数据」命中点逐条）

| 位置 | 原文案 | 现调用 | 档位 |
|---|---|---|---|
| ui/pages/path.py:23 | warning「暂无学习路径定义。」 | render_empty_state(暂无学习路径定义, 做完题目或导入内容后自动出现) | info |
| ui/pages/home.py:98 | caption「(暂无题目)」 | render_empty_state(该专题还没有题目, 换专题或 AI 出题, compact) | caption |
| ui/pages/home.py:109 | info「暂无错题。」 | render_empty_state(还没有错题记录, 做题后自动收进错题本) | info |
| ui/pages/mistakes.py:134 | info「没有可分组的弱项。」 | render_empty_state(暂无可分组的弱项, 多积累几道错题后自动分组) | info |
| ui/pages/language.py:138 | warning「该专题暂无题目。」 | render_empty_state(该专题暂无题目, 换专题或 AI 出题) | info |
| ui/pages/dashboard.py:78 | info 提交记录 | render_empty_state(还没有任何提交记录, 先做几道题…) | info |
| ui/pages/dashboard.py:252 | caption 提交记录 | render_empty_state(…, 做完第一道题后开始统计, compact) | caption |
| ui/pages/dashboard.py:341 | info 成就 | render_empty_state(还没有解锁任何成就, 开始做题获得第一枚徽章) | info |
| ui/pages/dashboard.py:387 | info 热力图 | render_empty_state(还没有提交记录, 开始做题后展示热力图) | info |
| ui/pages/dashboard.py:449 | caption 推荐漏斗 | render_empty_state(…, 做几天题后展示漏斗, compact) | caption |
| ui/pages/dashboard.py:483 | caption 间隔复习 | render_empty_state(…, 做对题后自动加入, compact) | caption |
| ui/pages/dashboard.py:519 | caption 开放题评分 | render_empty_state(…, 做几道开放题后展示趋势, compact) | caption |

不在收口范围：ui/pages/language.py:106（render_error_notice 错误提示，非空态）、:239（lesson_box 内联占位符，属内容渲染）、dashboard 数据齐全分支。

## 测试适配

3 个测试补 components 假件注入（mistakes/path/language 空态经统一组件渲染）；2 处断言 warning→info（空态从警示档并入信息档＝本任务统一组件的预期行为，断言仍核「暂无题目/暂无学习路径」事实内容）。

## 验收

- `python -m pytest -q`：**349 passed + 7 skipped，零失败**（≥304 ✓）。
- rg「暂无|尚无」ui/ 命中点全部经 render_empty_state 或 render_error_notice（上表），业务分支逻辑零变更。

## 遗留问题

- 本地目检（每改一处）受无头环境限制未逐处截图，浏览器实测归日间（与 plan.md 浏览器实测验收合并做）。
- caption 档微空态如需图标/留白差异化，等设计系统出空态专属 token 再迭代。
