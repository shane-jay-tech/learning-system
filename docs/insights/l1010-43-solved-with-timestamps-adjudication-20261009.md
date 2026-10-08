# ProgressDAO.solved_with_timestamps docstring 失真处置材料（l1010-43，2026-10-09）

## 复核读数

- `rg -n "\bsolved_with_timestamps\b" . -g '!tmp/**' -g '!__pycache__' -g '!*.md'` → 全仓两命中：定义 core/progress.py:366＋tests/test_mistakes_redo_lifecycle.py:118（测试消费）。**生产调用零**。
- 间隔复习真实数据源＝review_state 表：core/recommend.py:61 `_due_reviews_from_state` → `dao.due_review_ids()`（interval_days/ease/next_due_date 间隔算法驱动）；本方法读 problems_status.status='solved' 快照＋last_attempt_ts——**不同表不同口径**，「供间隔复习使用」的消费方不存在，docstring 失真实锤。

## 三案

### a) 删方法＋随删测试用例

```diff
-    def solved_with_timestamps(self) -> List[Dict]:
-        """返回所有 solved 状态的题目及其最后尝试时间，供间隔复习使用。"""
-        rows = self.conn.execute(
-            "SELECT lang, problem_id, last_attempt_ts FROM problems_status WHERE status='solved'"
-        ).fetchall()
-        return [{"lang": r[0], "problem_id": r[1], "last_attempt_ts": r[2]} for r in rows]
```
＋tests/test_mistakes_redo_lifecycle.py:118 用例随删。
风险：若 mistakes 重做链未来需要 solved 时戳面则重写；当前测试覆盖少一例。

### b) 改 docstring 为真实语义（推荐）

```diff
-        """返回所有 solved 状态的题目及其最后尝试时间，供间隔复习使用。"""
+        """返回 solved 状态快照视图（lang/problem_id/最后尝试时间）。
+        注意：间隔复习的真实数据源是 review_state 表（见 recommend._due_reviews_from_state），
+        本方法仅供测试与排障查询，未被生产路径调用。"""
```
理由：方法本身行为正确、有测试在养（删之需随删用例，覆盖净损）；谎言只在 docstring 一行——改一行即消除误导，成本最低。

### c) 注明预留

docstring 改为「为 mistakes 重做链预留（未接线）」。仅当主班确认该链未来需要 solved 时戳面才成立；当前无此需求在册，预留是空头支票——劣于 b。

## 裁决表

| 案 | 收益 | 风险 | 推荐 |
|---|---|---|---|
| a 删 | 死码面 −10 行 | 测试覆盖−1；未来重做链需重写 | 备选 |
| b 改 docstring | 语义诚实化一行，测试保留 | 无 | ✅ 推荐 |
| c 预留注记 | 语义诚实＋留口 | 空头预留无需求背书 | 劣于 b |

——默认零码改；b 案 docstring 一行改写若主班授权可顺手落。
