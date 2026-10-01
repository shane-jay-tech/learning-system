# l930-03 两区点击语义拉齐记录（失败仍跳＝统一契约）

## 方向依据
l927-29 遗留的两区不一致（今日推荐 reported 门控「失败不跳」vs 跨路径「失败仍跳」），
本单方向＝**旧向新看齐**（今日推荐拆掉 reported 门控，与跨路径 :490-497 逐字同型）。
依据：跳转是用户已明示的意图，事件库故障不该把「去做 →」变死键——跨路径区自 l923-07
起运行该形态零死键事故；且 l930-02 的 A2 写序落地后，曝光侧失败已可自愈重试，
点击侧不再需要叠加「失败不跳」的第二重门控（原门控防的「漏斗只掉不补」已被 A2 治理）。

## 改动
- `ui/pages/dashboard.py`：今日推荐点击路径删 `reported` 旗标与 `if reported:` 门控
  （navigate 移出条件，与跨路径同型）；原 l927-29 裁决注释整段替换为 l930-03 翻面说明。
- 桩同步（l927-29 时代的「失败不跳」三钉全翻面，逐枚记录三代史）：
  - `test_click_event_failure_now_stops_navigation` → 改名 `..._still_navigates_and_logs`
    （rerun 0→2＋路由三键恢复断言）；
  - `test_click_emit_failure_leaves_navigate_never_called` → 改名
    `..._still_navigates_with_full_route`（nav_calls []→恰 1 次完整三元组；spy 只记录不转发，
    路由面由 §五/§六 转发桩钉）；
  - `test_l927_29_second_click_failure_drops_only_its_own_navigation` → 改名
    `test_second_click_failure_drops_only_its_own_click_report`（改钉点击上报连带半径归零：
    两卡都跳、selection 落第 2 张、坏条不送达不吞）。
- §五/§六 三枚跨路径点名桩：断言（rerun_count==2）不变，docstring 补 l930-03 语义迁移注记
  （「跨路径特有残存形态」升格「两区统一契约」）。

## 验证
全件 27 passed。
