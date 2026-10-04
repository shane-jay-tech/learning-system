# difficulty 档位语义两处不一致裁决材料（l1002-82，只读零改码）

- 时点：2026-10-05（exec-shift-20261003-manual）
- 矿源：l922-06 遗留——ai_review `<=2` 单分岔 vs SRS `>=4` 惩罚，两口径不一致

## 一、两处现值（完成标准①）

**① core/ai_review.py:187-194 `_build_review_system_prompt`**（AI 评审提示词分岔）：
```python
if difficulty <= 2 and passed:   return _SYSTEM_PROMPT_BEGINNER_PASS   # :189 1-2 档 → 宽容提示词
if difficulty <= 2 and not passed: return _SYSTEM_PROMPT_BEGINNER_FAIL  # :191 1-2 档 → 宽容提示词（未过形态）
return _SYSTEM_PROMPT_STRICT                                            # :193 3-5 档一律 STRICT
```
——3/4/5 三档**无差别**同走 STRICT（「1-2 松 / 3-5 同」）。

**② core/progress.py:409（SRS 复习调度）**：
```python
if passed:
    streak += 1
    interval = min(int(interval * ease), 30)
    if difficulty >= 4:                      # :409 4-5 档答对 → ease 额外 -0.1（难度惩罚）
        ease = max(1.5, ease - 0.1)
```
——SRS 侧 **>=4 惩罚**（4/5 档答对时 ease 因子额外下调，间隔增长放缓）。

**题面档位分布**（content 全语种 408 题）：1 档 75／2 档 183／3 档 133／**4 档 16／5 档 1**——两口径分歧的实际作用面：ai_review 的 3 档（133 题）与 SRS 的 4-5 档（17 题）。

## 二、三案对照（完成标准②，只出对照不下结论）

| 案 | 改动 | 影响面（题量分布视角） |
|---|---|---|
| **A：ai_review 加 3 档分岔**（`<=3` 宽容或 3 档独立提示词） | AI 评审提示词域；3 档 133 题的评审语气/严格度变化（评分规则数值域——**红线只描述不结论**） | 133 题（3 档全量）；4/5 档 17 题不受影响 |
| **B：SRS 去 >=4 惩罚**（删 :409-410 两行） | SRS 调度域；4-5 档 17 题的复习间隔增长曲线变化（ease 不再额外下调） | 17 题（4 档 16＋5 档 1）；3 档 133 题本就不受此惩罚、零变化 |
| **C：维持双轨＋注释**（两处各加口径注释互指） | 零行为变化；两处口径差异文档化（ai_review 评的是「AI 挑错严格度」、SRS 罚的是「高分档记忆衰减预期」——**语义本可不同**，注释把"是有意分层"或"是历史遗留"标出来） | 0 题即时影响；防后人误统一 |

**对照要点**：两处分属不同业务面（AI 反馈语气 vs 记忆调度），「不一致」未必是缺陷——案 C 成本最低且保住语义解释空间；案 A/B 是真实行为变更，涉及评分规则，**须产品/主班拍板**（红线：本材料不下数值结论）。

## 三、零改码声明

全程只读 grep/sed 摘录＋loader 只读统计；core/ 两文件零触碰。
