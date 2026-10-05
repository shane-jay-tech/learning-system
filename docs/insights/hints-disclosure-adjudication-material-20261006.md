# 提示展示口径两出口材料：逐级揭示 vs 一次性展示（l1004-14；942f 遗留1）

> 产线：执行班 l1004-14（2026-10-06）。**材料型**；反向锚由 9/25 班钉下（942f 遗留处置），本班复核仍绿并出两出口裁决材料。

## §一 反向锚现值复核（仍绿 ✓）

- 用例：`tests/test_mistakes_redo_lifecycle.py::test_hints_are_rendered_in_one_pass_without_a_failure_gate`（:220-249）。
- **本班实跑：`1 passed in 0.11s`**。断言逐字（钉「一次性展示」现状＋防逐级暗做）：
  ```python
  assert 'if active.get("hints"):' in src
  assert 'st.expander("💡 不会做？看提示", expanded=False)' in src
  block = src.split('if active.get("hints"):')[1].split('\n        with st.expander')[0]
  assert 'for h in active["hints"]:' in block
  assert block.count('st.markdown(f"- {h}")') == 1      # 块内只有一次遍历，多一档就红
  assert "attempt_count" not in src                     # 没有按尝试次数门控
  assert "if st.session_state" not in block             # 提示块前无会话态条件
  # ② ui/ 全目录扫 (hint|提示)×(level|stage|step|index|逐级|分档|递进) 组合词 == []
  ```
- 实现出口现值：`ui/pages/language.py:333-336`——单个 expander（默认折叠）内 `for h in active["hints"]` 一次列全，无任何门槛。

## §二 两出口对照

| | 出口① 按判据实现逐级展示 | 出口② 修订判据为「一次性展示」 |
|---|---|---|
| 产品规则草案 | 失败次数→提示条数映射：`visible_hints = hints[:min(fail_count + 1, len(hints))]`（第 1 次失败见第 1 条，每多败 1 次多揭 1 条；expander 标题改「已解锁 N/M 条提示」；未失败=0 条） | 判据文案改为：「提示以单个折叠 expander 一次性全部展示（自担是否查看的自控责任）；不做失败次数门控」——并把反向锚用例改名去「分歧」注记，保留防「暗做逐级」的 ② 组合词扫描 |
| 改动面估计 | **UI 一处**（language.py 提示块改切片）＋**状态面**：fail_count 需进 UI 可达位（attempts passed=0 计数已有 DAO 面，加一次查询或随 attempt 事件带出）＋**测试**：反向锚用例整体重写（现断言全数反转，② 扫描保留改期望非空）、redo lifecycle 同件相邻用例回归 ≈3-4 例；est. 1 个执行单 | **零码**：判据文档一处＋反向锚用例 docstring/名称微调（断言体不动，仍钉现状）＋回规划脑（zcode-bridge 侧任务书口径修订，非本仓）；est. 半个维护单 |
| 风险 | 产品语义未经拍板即落＝判据-实现矛盾反向固化；自控型学习者被强制延迟看提示，可能负反馈 | 等于承认「纸面要求与实现长期脱节」以实现为准——需规划脑侧确认无未兑现的产品承诺 |
| 依赖 | attempts 失败计数的口径（**重做通过即除名错题本的现行语义**见 l1004-10 §二——若以「错题本在册」为门槛，与除名语义耦合） | 无 |

## §三 交主班择一

- 若用户/规划脑对「逐级」有真实产品意图（教学设计上「先给最小提示」）→ 出口①，先拍映射规则再派码；
- 若「逐级」只是判据笔误/过度承诺 → 出口②，修订文案＋反向锚转正（本班已备好锚点现状证据）。
- 本班零码；反向锚 ② 组合词扫描在两出口下都保留（防未来无拍板暗做）。
