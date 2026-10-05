# 旧双 API 收口裁决＋status=wrong 零行取证（l1004-10；7b25#2＋942f#4＋222f#4）

> 产线：执行班 l1004-10（2026-10-06）。**材料型，零码改动**；与 l1002-13（dao 死形参）不同物。

## §一 两旧 API 现值与调用面（rg 清单）

- `record_attempt`＝`core/progress.py:207-214`（只写 attempts）；`mark_status`＝`:216-222`（只写 problems_status）；单事务正身＝`record_attempt_and_status :187-204`（注释自陈「兼容旧 API（test_progress 等）」:206）。
- **生产调用面（core/ui/scripts）＝0 处**：`rg "\.record_attempt\(|\.mark_status\(" core/ ui/ scripts/ -g "*.py"`（排除 record_attempt_and_status）零命中——judge 走 `_record_attempt`→`record_attempt_and_status`（judge.py:182）。desync 风险面**只在测试**。
- 测试调用面（矿源 7b25 称 test_progress 4 用例，**现值已漂**）：`rg -c` ＝ test_progress.py **16 处**；另有 test_app_flow.py（mark_status 'wrong'）、test_core_edges.py（mark_status 'solved'×2）、test_dashboard.py（record_attempt×3+）等跨文件使用。

## §二 status=wrong 零行跨面取证

**写点清单**（能产出 status='wrong' 的全部路径）：① `record_attempt_and_status:191` `status = "solved" if passed else "wrong"`；② `mark_status:217-220`（调用方任意传 'wrong'——test_app_flow 一例）。

**三面计数（活库 mode=ro，本班实测）**：
```sql
-- $ python (sqlite3 file:data/progress.db?mode=ro)
SELECT COUNT(*) FROM problems_status WHERE status='wrong';        -- → 0
SELECT status, COUNT(*) FROM problems_status GROUP BY 1;          -- → [('solved', 14)]
SELECT COUNT(*) FROM attempts WHERE passed=0;                     -- → 1 （attempts 总 15）
SELECT COUNT(*) FROM learning_events WHERE event_type LIKE '%wrong%' OR event_type LIKE '%mistake%';
                                                                  -- → 0
```

**222f#4 两问判定**：错题本唯一数据源＝`list_mistakes:235-246` `WHERE ps.status='wrong'`（JOIN attempts 取最新作答）。attempts 有 1 行 `passed=0` 但 problems_status 无 wrong 行——机制＝`record_attempt_and_status` 对 problems_status 用 **INSERT OR REPLACE**：重做通过后 wrong 被覆盖成 solved，**该题同时从错题本除名**。⇒ 判定＝「**重做通过后被覆盖成 solved**」为真且是现行设计语义（不是数据丢失）；「错题本另有口径」为假（错题本与 status 同源，无第二口径）。「错过的题通过后是否该留在错题本」属产品裁决，材料提请主班注意：现行为＝通过即除名，与「错题本应长期追踪薄弱点」的常见预期相悖。

## §三 收口三案

| 案 | 形态 | 影响 |
|---|---|---|
| **① 删旧 API** | 删 :206-222，测试全迁 `record_attempt_and_status` | 生产零影响（0 调用）；测试改造＝test_progress 16 处＋app_flow/core_edges/dashboard 约 7 处（**23 处级**）——有意测「单表写入」语义的用例（core_edges 单独 mark_status）需改语义或删除 |
| **② 内部化** | 改名 `_record_attempt`/`_mark_status`＋docstring 标「仅测试兼容」 | 断言影响＝同①（改名后测试仍要跟改）——与①成本相近、收益更低，**不推荐单选** |
| **③ 守卫告警** | 两旧 API 首行 `logger.warning("deprecated legacy API ...")`（或 DeprecationWarning） | 零破坏零测试改动；渐进观察一轮后执行①——**推荐为①的前置步** |

**材料倾向**：③→① 两步走（先告警一周期，pytest 输出可见全部触点，再删）；②不单选。收口后 7b25 的 desync 通道（单表写入）从 API 面消失，仅剩 `update_review_state` 独立写（judge 侧与 record 同事务性另案）。

## §四 边界

收口属重构决策（7b25 明言），材料交主班；wrong 除名语义若需改（重做通过仍留错题本）属产品口径变更，与本案可分离拍板。
