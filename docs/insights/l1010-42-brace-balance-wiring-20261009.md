# _brace_balance_error 未接线裁决材料（l1010-42，2026-10-09）

## 复核读数

- `rg -n "\b_brace_balance_error\b" scripts/ tests/` → 生产侧唯一命中＝定义行 `scripts/audit_content_deep.py:96`；tests/test_scripts.py:294-303 四用例独养（复跑与 k1010 时点一致）。
- deep_audit 主循环 starter 检查分支（:151-159）只有两支：`sql → _sql_setup_error`、`python/agent_dev → _python_syntax_error`；**无第三分支**——cpp/r 题的 starter_code 平衡检查从未接入。
- 全库现值跑数：cpp **13** 题 / r **18** 题（load_language 实载），用 _brace_balance_error 全量试跑：**不平衡命中 0**（现库干净，接线当日零新增报错）。

## a 案：接线（推荐）

deep_audit 主循环 python 分支后追加（+4 行级，逐字预估）：

```python
                # cpp/r：大/圆括号平衡（无 ast 可用，字符规则面）
                if lang in ("cpp", "r") and p.starter_code.strip():
                    err = _brace_balance_error(p.starter_code, lang)
                    if err:
                        errors.append(f"[{pid}] {err}")
```

- 收益：检查建成不跑＝假审计的形态解除；cpp/r 后续新增题的 starter 平衡进审计门。
- 风险：极低——现值命中 0，接线当日 audit 输出零变化；未来真不平衡时 errors 面 +1 类是预期行为。
- 波及：scripts/test_scripts.py 四用例无需改（函数行为未变，只是多了调用方）。

## b 案：不接线

- tests/test_scripts.py 四用例改判「纯字符规则单测」，_brace_balance_error docstring 注明「未接入 audit 主循环，仅供测试/手工核查」。
- 风险：cpp starter 平衡永无自动门，后续导入题不平衡要靠人眼；「建成未接线」状态固化为已知债务。

## 裁决表

| 案 | 收益 | 风险 | 推荐 |
|---|---|---|---|
| a 接线 | 审计门覆盖 cpp/r 全部 31 题；现值零翻红 | 未来不平衡题会开始报错（=功能生效非风险） | ✅ 推荐：检查建成不跑等于假审计 |
| b 不接线 | 零代码改动 | 假审计固化；后续题质量无人拦 | 备选 |

——默认零码改（本档只出材料，接线实施另单走授权）。
