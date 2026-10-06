# 反馈质量样本面构造方案：expected_* 夹具（l1004-33；67e5 R-2 备用档）

> 产线：执行班 l1004-33（2026-10-06）。**备用档零码**；真 LLM 放行面已由 l1004-26 先行（20/20 真调用读数在档）。

## §一 stub 占比复算（SQL 内联，与 67e5 一致零漂移）

```sql
-- $ python (sqlite3 file:data/progress.db?mode=ro)
SELECT COUNT(*), SUM(CASE WHEN ai_feedback LIKE '%stub%' OR ai_feedback='' THEN 1 ELSE 0 END) FROM attempts;
-- → attempts=15, stub_like=13   （86.7%；有效真文本=2 条，id 14/15，均 python/01_hello_and_vars）
```

13 行 stub＝`(verify stub)` ×8（py/sql 工具链 stub）＋`(stub)` ×5（r stub）；有效 2 条＝同题（hello_world）通过/未通过各一。

## §二 夹具构造方案（n 目标 30）

### 样例来源（三源混采，全部经脱敏+评审）

1. **l1004-26 真调用产物**（现成 20 条：review×10＋grade×10，落点 JSON 已在 `tmp/shift-20261006/l1004-26/latency_results.json`，含 head 全文可回源）——首选，零新增调用量。
2. **测试面确定性样本**（~6 条）：`review()` 对构造 stderr（NameError/SyntaxError/超时/工具链缺失四族，复用 l1004-27 的 8 条矩阵语料）在 stub/离线模式下的 `_offline_fallback` 落点——覆盖「AI 不可用」分支的预期形态。
3. **人工撰写金样例**（~4 条）：每语言至少 1 条「理想反馈」手写样（作 R-3/R-4 校验的阳性对照），标注 `author=human`。

### 脱敏口径

- 样例只含：题面公开文本、学生代码（当前仓内无真实学生个人数据——attempts 代码均为自写演示）、AI 反馈文本；**不含**时间戳/用户名/任何 progress.db 行原样拷贝（id 14/15 的反馈文本提取后与行解耦）。
- 校验：入库前 `rg` 扫样本集无 `\d{4}-\d{2}-\d{2} \d{2}:\d{2}` 完整时戳、无路径 `D:/`、无 `31563`。

### expected_* 键位设计

- **不进生产库**（attempts 表语义是「学习事件账本」，塞夹具=污染历史），落点＝`tests/fixtures/feedback_samples.json`：数组元素 `{sample_id, lang, problem_id, code_hash_mode, passed, source: "real-llm-20261006|offline-fallback|human", feedback, expect: {has_action: true, no_empty_praise: true, rubric_scores optional}}`。
- 断言面：新测试件 `test_feedback_quality_samples.py`——逐样本跑 R-3（动作性标记存在）/R-4（无空泛表扬为唯一内容）程序化校验＋`_post_check` 幂等；n≥30 断言集数。
- 评审步骤：① 探针生成 → ② 人工抽 20% 复核（反馈与题面相关、无幻觉 API 名）→ ③ 主班签样 → ④ 落 fixtures＋测试件。

### 边界

- 零码零写库；真 LLM 放行面＝l1004-26 已行（本方案源 1 直接复用其产物，无新增调用量）。
