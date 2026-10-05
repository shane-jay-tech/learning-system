# LLM 断线写库口径分叉材料：run 照写 vs 开放题不写＋脏 JSON 仍写（l1004-08；0f02 D2＋a6b8#6）

> 产线：执行班 l1004-08（2026-10-06）。**材料型，零码改动（判分红线域）**。

## §一 两处分支现值（逐字贴出）

**run 题臂（断线照写）**——`core/judge.py:343-347`：
```python
    passed, run_result, diff_hint = _run_test_cases(runner, lang, code, pdict)
    expected_display, actual_display = _build_display(lang, pdict, run_result, passed)
    feedback = review(lang, pdict, code, run_result, passed)
    difficulty = int(pdict.get("difficulty") or 3)
    _record_attempt(lang, pdict.get("id") or "", code, passed, feedback, dao, difficulty)
```
`review` 断线时内部降级为兜底文案，`_record_attempt` **不看 llm_ok 无条件写**——run 题计分依据的是 `_run_test_cases`（本地跑测），LLM 只产 feedback，故「照写」在 run 题有结构性理由（D2 原文「同一场断线事故，一处计一次成绩」即指此处与开放题相反）。

**开放题臂（断线不写）**——`core/judge.py:359-370`：
```python
def _judge_open(lang: str, pdict: dict, answer: str, dao=None) -> JudgeResult:
    """开放题：交 LLM 按 rubric 评分。LLM 不可用时不记录 attempt（不把基础设施故障算成用户失败）。"""
    res = grade_open_answer(lang, pdict, answer)
    ...
    if res.get("llm_ok") and not str(pdict.get("id") or "").startswith("AI_VARIANT::"):
```
`llm_ok=False` ⇒ 整块跳过（attempt/status/events 全不写）。开放题计分**依赖** LLM，断线＝无法判 ⇒ 不写有 docstring 自洽理由（「不把基础设施故障算成用户失败」）。

**脏 JSON 臂（a6b8 E，llm_ok=True 但 score=None/维度空仍写）**——`core/judge.py:371-379`：
```python
            attempt_id = d.record_attempt_and_status(lang, pid, answer, res["passed"], res["feedback"])
            ...
            dimensions = res.get("dimensions") or []
            if dimensions and attempt_id:      # 维度空 ⇒ rubric_scores 自然跳过（半防护）
            d.emit_event("ai_open_scored", ..., payload={"score": res.get("score"), "passed": res["passed"]})
            # score=None 照发事件；attempt 行照写
```
影响面＝以 `ai_open_scored.score` 为口径的统计（score=None 行）与 rubric 维度缺失面（attempt 有行、rubric_scores 无行 ⇒ 两表行数不对齐）。

## §二 统一三案与 attempts 计数口径变化

| 案 | 形态 | attempts 计数口径变化 | 评价 |
|---|---|---|---|
| **A 都写＋标记** | 开放题断线也写 attempt（passed=False＋feedback=「AI 暂不可用」）＋新增可观测标记 | 断线期开放题从「0 行」变「每提交 1 行且全 fail」⇒ **attempts 计数上升、通过率被稀释**；且把基础设施故障算成用户失败（违背 :359 自陈原则）——**不推荐** | 与 run 题对齐但方向错 |
| **B 都不写** | run 题断线也不写＝须先定义「run 题断线」（LLM 断但本地跑测可用——把可用判分也停掉） | 断线期 run 题 attempts 从「照写」变「0 行」⇒ **计分缺口**，学生白做 | 违背 run 题结构性理由，**不推荐** |
| **C 分档（现状＋补标记，材料倾向）** | 承认两题计分依赖不同（run=本地跑测、开放=LLM）是**本质分叉而非缺陷**；统一的是**可观测口径**：两臂都发 `llm_degraded` 标记 | attempts 计数**零变化**；变化只在标记/事件面 | D2 的「分叉」实为「计分依赖不同」的合理推论；值得修的是 a6b8 E 的可观测缺口 |

**C 案落地形状**：① run 臂 `review` 内部已知 llm_ok，把降级态透传 `_record_attempt`（feedback 文案已有，补结构化标记）；② 开放题断线分支发 `d.emit_event("ai_open_degraded", lang, pid)`（不写 attempt）——断线事故可在事件层对账，两臂口径统一为「可见但不混入计分」。

## §三 脏 JSON 最小可观测方案（并入 C 案）

- **推荐事件字段（不加列）**：`ai_open_scored` payload 补 `"degraded": true / "score": null` 显式位；`_judge_open` 写 attempt 前判 `res.get("score") is None or not dimensions` ⇒ 额外发一条 `ai_open_dirty_payload`（或同事件 degraded 位）。统计面过滤改按 payload 键，**attempts/rubric_scores 零 schema 改动**。
- 备选标记列（attempts 加 `llm_degraded` 列）：查询方便但要走迁移＋历史行回填口径，材料不建议先行。
- 断言影响估计：judge 事件断言 +2~3 处（脏 JSON 样本夹具沿用 a6b8 E 的否证样本）。

## §四 边界

- 三案均涉计分/统计口径（判分红线），全部交主班；本档只锁「现值逐字」与「C 案＝本质分叉＋可观测补齐」的裁决建议。
