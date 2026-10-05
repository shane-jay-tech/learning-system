# 重复提交计分裁决材料：judge 幂等键缺失＋recommendation_completed 重复＋payload 两形态（l1004-07；0f02 D1/D3＋222f#3）

> 产线：执行班 l1004-07（2026-10-06）。**材料型，零码改动（判分统计红线域）**；l930-31 已裁实事件 attempt_id 面，本档只裁 `problem_passed/failed` 的 **payload 面**与幂等键方案。

## §一 哨兵现值复核（口径未变 ✓）

- 哨兵件：`tests/test_repeat_submit_settlement_20260925.py`——`test_n_settle_five_times_in_append_tables_but_once_in_status`＋`test_n_pushes_srs_forward_every_click`（rg 全仓唯此一处该主题）。
- **本班实跑：`.venv/Scripts/python.exe -m pytest tests/test_repeat_submit_settlement_20260925.py -q` → `9 passed in 3.45s`**——哨兵全绿＝0f02 所述行为未变：append 层（attempts/learning_events）五次点击五次落行、status 层一次、`review_state.review_streak` 推到 5、间隔按 ease 复利、到期日后推（:119 注释原文「改一个字再点五次等价于答对五次」）。
- D3 面现值：`core/judge.py:163-184 _check_recommendation_completed`——judge 每次判**对**都补一条 `recommendation_completed`（查最近一条 shown 带 attribution 原样回放），无去重 ⇒ 1 shown : N completed 形态仍在（0f02 实测 1:3）。

## §二 submission key 三案与统计口径影响

**SRS 数值影响示例基准**（哨兵口径，同题连点 5 次全对，difficulty=3、初始 interval=1d/ease=2.5 形态）：streak=5；interval 走 1→3→7→…复利 5 步；next_due 后推 5 次。

| 案 | 形态 | streak/间隔数值影响 | 口径影响面 |
|---|---|---|---|
| **① 前端禁点** | 提交按钮 submit 中 disabled＋防抖（UI 层） | **零变化**——后端语义不动，只挡「手抖双击」；刷新页面/双端并发仍可重复 | 最小；不加键、不改表；统计仍按「每次提交都算」 |
| **② 后端幂等键** | judge 入 `submission_key = hash(lang+pid+code+stdin)`，`record_attempt_and_status` 前查 attempts 近 N 分钟同键拒绝（或 attempts 加列＋唯一索引） | 同题同码 5 击＝1 次结算：streak=1、interval 1 步、next_due 后推 1 次——**SRS 曲线整体变平**（历史 streak/interval 数值不可比，需在台账标注切换日） | 生产行为变更＋统计数值口径变更（0f02 明言人工闸后）；attempt_submitted 等事件同键联动去重才彻底 |
| **③ 事件层去重** | emit_event 前按 `(event_type, lang, pid, date, code_hash)` 查当日同键跳过；attempts/review_state 不动 | **零变化**（SRS 层照旧 5 次推进）——只把 learning_events 的 1:N 收敛成 1:1，报表口径变干净 | 报表面口径变更（周报/热力图数字回落）；判分/SRS 不动＝风险最低的「数字洁癖」方案 |

**材料倾向**：①先落（零口径面，挡主害「手抖」）；③次之（报表口径需主班拍板切换日）；②收益最大但动 SRS 曲线，须与 l1004-01 资源档同批走人工闸。

## §三 payload 两形态（problem_passed/failed 面，222f#3）

- 发射点 A：`core/judge.py:205-206` `d.emit_event(event_type, lang=lang, problem_id=pid)`——**payload 为 NULL**。
- 发射点 B：`scripts/backfill_events.py:91` `(event_type, json.dumps({"attempt_id": _id}))`——**payload 带 attempt_id**。
- 同型先例：attempt_submitted 也两形态（judge 侧 `{"passed": bool}` 无 attempt_id，backfill 侧带）——backfill 的去重键（:49-51 精确键/退化键两档）已兼容老形态。
- **并入裁决**：建议发射点 A 补 `payload={"attempt_id": attempts rowid}`（record_attempt_and_status 的返回/lastrowid 透传）——与 backfill 形态归一，222f#3 的消费歧义消除；断言影响 ≈ judge 侧事件 payload 断言 2-3 处。**属事件遥测面，不动判分**，可执行单带走（但仍建议与②/③裁决同批以避免两次口径公告）。

## §四 边界

- 本单零码；三案均涉生产行为或统计口径（判分统计红线），全部交主班；哨兵件（9 例）是任何落地方案的回归底线。
