# l930-02 今日推荐曝光写序拉齐记录（A2 落地，旧向新看齐）

## 方向依据
l927-37 两区写序不一致（今日推荐 `add→impressions→emit` vs 跨路径 `emit→add→impressions`），
本单方向＝**旧形态向新形态看齐**（今日推荐换成跨路径的 A2：emit 先、成功后落本地账）——
与 l924-01 那次「新向旧看齐」方向相反。依据两条：①A2 是设计稿
`docs/insights/learn-shown-writeorder-design-20260923.md` §三 裁决的终态（失败可重试、
差额自愈），旧形态的「失败条永久丢失且不自愈」是待修缺陷不是要保护的语义；②跨路径区已在
l927-37 先行 A2 并带自愈例，今日推荐向它看齐是向**多数派+终态**收敛。

## 改动
- `ui/pages/dashboard.py`：今日推荐区写序三行换序（emit→add→impressions），rc/rec_id/payload
  前置计算提到 try 外（与跨路径区 :447-456 逐字同型）；日志文案保持原文「推荐展示数据异常」不漂。
- `tests/test_dashboard_event_failures.py` 5 桩同步＋自愈例：
  ①例3 重写为 `test_emit_failure_leaves_no_local_trace_and_self_heals_on_recovery`（旧断言全翻转：
  失败条零残留 2/2/2＋恢复帧重试）；②例4 记账面 5→4；③例5 点击侧改断「失败条零本地账＋空 rid 回退分支」
  （原「本地账在、归因照带」的悬空 rid 形态随旧写序消亡）；④§七例1 ⑤记账面 5→4；
  ⑤例七 expected_local 两支统一 2（原 dashboard=3/cross=2 的不一致陈述随之作废——
  「哪区挪写序哪支红」的哨兵功能由「谁回退谁红」继承）。
- 新增 §八 自愈例 `test_dashboard_impression_failure_self_heals_on_next_frame`（补齐 dashboard 支，
  跨路径支同款在 l927-37 §九 在册）：恢复帧只补报炸掉那一条＋rid＝确定性 rid（归因链自动接上）。

## 验证
全件 27 passed；邻域 test_dashboard_page_render＋test_ui_behavior 全绿。
