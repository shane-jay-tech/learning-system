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

---

# 附：ai_review R-4 空泛表扬判据未接线裁决材料（l1010-44，2026-10-09）

> 独立主题与本档主文（brace_balance）无耦合，附录于此仅省一份档；引用时请点名 l1010-44。

## 复核读数

- `rg -n "\b_empty_praise_hits\b" core/ ui/ scripts/` → 唯一命中＝定义 core/ai_review.py:302（生产零调用；tests/test_ai_review_strategy.py:429 一例独养，与本档口径同型）。
- `_post_check`（:307-317）注释自称「l930-19：R-3/R-4 强制」，函数体只调 `_feedback_actionable`（R-3）——**R-4 判据建成未接线**，注释超述。

## 两案

### a) 接线进 _post_check（行为变更，留主班裁）

```diff
     if not _feedback_actionable(text):
         text += _CORRECTIVE_TAIL
+    hits = _empty_praise_hits(text)
+    if hits:
+        text += "\n\n（提示：点评中含空泛表扬「" + "」「".join(hits) + "」，请对照具体错误逐条给建议。）"
```

- 翻面风险清单：test_ai_review_strategy.py 的 golden/rubric 断言若含「命中空泛表扬短语的样本经 _post_check 后形状」用例会翻面（l930-19 原批的 R-3 用例不受影响；上线前需跑全量 ai_review 面测试核对）；另 _post_check 是判分文案域，行为变更涉 l930-19 拍板语义（「改写式不拦截」仍守）。
- 收益：R-4 真正生效，空泛表扬获得可执行尾注。

### b) 订正注释为真实语义（推荐，零行为变更）

- :307 注释「l930-19：R-3/R-4 强制」→「l930-19：R-3 强制；R-4 判据 _empty_praise_hits 供测试（未接线，接线属行为变更留裁决）」。
- :302 docstring「（供测试与日志；空 = 合规）」→「（供测试；空 = 合规）」（去「与日志」——日志面零消费）。
- 风险：无（纯文案）；收益：注释与函数体一致，下次审计不再误读。

## 裁决表

| 案 | 收益 | 风险 | 推荐 |
|---|---|---|---|
| a 接线 | R-4 生效 | 行为变更＋golden 翻面风险，判分文案域留主班 | 备选 |
| b 订正注释 | 注释诚实化零风险 | R-4 继续休眠（已登记） | ✅ 推荐 |

## is_degraded_feedback 钉桩（已落地，见 tests/test_is_degraded_feedback_l1010.py）

judge.py:401 生产调用位的首测四例（断线文案真/普通点评假/空串假/None 假）4/4 绿；docstring「多个测试钉住」实指前缀契约（offline_fallback 面），本件补的是函数本体的直接钉桩。
