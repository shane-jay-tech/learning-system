# dashboard.py 渲染主路径补测（916p-a3-015，2026-09-17，只增测试）

## 验证（命令与数字同段）

```
$ python -m pytest tests/test_dashboard_page_render.py -q
8 passed in 1.22s                                   ← ≥6 达标
$ python -m pytest tests/test_ui_behavior.py tests/test_dashboard_page_render.py -q --cov=ui.pages.dashboard --cov-report=term
ui\pages\dashboard.py     345    124    106     25    59%   ← 基线 9% → 59%（≥25% 达标）
$ python -m pytest tests -q
384 passed, 7 skipped in 29.22s                     ← passed ≥382、skipped 7、failed 0 ✓
```

## 用例 ↔ dashboard.py 行段对照（8 条）

| # | 用例 | 覆盖行段 |
|---|---|---|
| 1 | test_render_dashboard_full_flow | :44-53 入口＋:54-108 主渲染体＋:156-176 子调用链（ProgressDAO 打桩＋recommend/cross_recommend/achievements 域打桩） |
| 2 | test_render_dashboard_body_smoke | :54-265 _render_dashboard_body 主体（summary/total/recent/attempts_by_day 图表与最近活动） |
| 3 | test_render_cross_recommend | :273-325 跨路径推荐（展示＋recommendation_shown 事件，经 components.st 录制） |
| 4 | test_render_achievements | :326-376 成就三态（领域函数打桩：check_achievements/get_progress_summary/get_all_with_state/get_achievement） |
| 5 | test_render_heatmap | :377-436 热力图 |
| 6 | test_render_recommendation_funnel | :437-477 推荐漏斗（shown/clicked/completed＋百分比） |
| 7 | test_render_review_health | :478-513 复习健康度（total_pool/total_due/平均间隔） |
| 8 | test_render_rubric_trends | :514-536 能力维度趋势（含最薄弱维度 caption） |

## 脚手架注记

- FakeStreamlit 直接复用 tests/test_ui_behavior.py 的类，子类 `DashboardFakeStreamlit` 仅扩展 EXTRA 组件名（bar_chart/plotly_chart/file_uploader 等 dashboard 用到而基类未录制的键），既有文件零改动。
- DAO 用 MagicMock 兜底未知方法（热力图/健康度等深层方法返回值由显式配置提供）。
- 实测发现的额外数据面契约（已按现状配桩）：recent_attempts 行需含 `problem_id` 与 `ts`；lang_attempt_counts 值为 {"attempts": n} 嵌套。

## 未覆盖行段（59% → 剩余）

109-155（双图表分支）、176-205（周期对比）、230-250（导入/导出分支）、311-323（弱项深挖）、345-366/402-409/468-475/509-511（各子渲染器空态深分支）——多为错误/空态深分支，留后续单。

## 验收对照

- ✅ 新文件 8 用例 ≥6 全绿（同段）。
- ✅ dashboard.py 覆盖率 59% ≥25%（同段；基线 9%）。
- ✅ 全量 384 passed ≥382、skipped 7、failed 0（同段）。
- ✅ 用例↔行段对照表如上。
- ✅ ui/pages/dashboard.py 与其它源码零改动；零新增依赖；不 push。
