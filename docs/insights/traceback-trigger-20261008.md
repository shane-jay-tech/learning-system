# 语料积累监测与 30 条复测触发器核（2026-10-08，l1007-04 遗留）

> 零改码。l1007-04 挂起条件：「attempts 中含 'Traceback' 的失败行 ≥30 后复跑查询（p50/p90/p99 与首尾密度比）」。

## 一、现值复跑（progress.db attempts）

| 项 | 读数 |
|---|---|
| attempts 总量 | 15（其中 stub 3 行） |
| 失败行（passed=0） | **1** |
| 含 'Traceback' 的行 | **0** |

**触发条件远未满足**（0/30）——30 条复测触发器暂不可触发。

## 二、截断链核（stderr 是否全量入 ai_feedback）

**结论：链路「半通」——stderr 的**摘要**入 feedback，但不是全量**：

- 失败提交链：`_run_test_cases` → 运行错误路径 `diff_hint = "运行错误：" + _row_feedback(lang, case_run)`（judge.py:296）→ `_row_feedback` 内 `base = _error_summary(stderr)`（:167）＝**stderr 摘要单行（截 120 字符）**，非全量 stderr；`review()` 产出的 feedback 组合「思路/代码品质」等评语＋base，最终 `_record_attempt(..., feedback, ...)` 写入 attempts.ai_feedback。
- 实测：现存失败行 ai_feedback 长度 470（评语主体），**无 Traceback 字样**（该行失败原因是输出不一致非运行错误——`输出与期望不一致` 分支根本不含 stderr）。
- l1007-21（本班先行单）刚落的 `_error_summary` 优先取 *Error* 形态行微调**提高了摘要质量**（异常类型行优先），但**量级仍是单行 ≤120 字**。

**先有鸡还是先有蛋的解**：l1004-02 案 2 本体（stderr 全量入 ai_feedback）是积累 30 条 Traceback 行的前提——当前单行摘要形态下，「含 Traceback」的行只有在**摘要恰好选中 Traceback 行**时才出现（l1007-21 前=几乎不可能；l1007-21 后=Python traceback 面仍偏向取末行异常而非 Traceback 头）。

## 三、两案（30 条阈值 vs 降阈 15）

| 案 | 内容 | 建议 |
|---|---|---|
| 案 A：维持 30 条阈值 | 等自然积累——按现失败率（15 attempts/1 失败）且 Traceback 行需运行错误型失败，预计**数十个学习日**才可能达标 | 不荐（观察期过长，样本获取不可控） |
| **案 B：降阈至 15 并扩判定域（荐）** | 触发条件改「`ai_feedback` 含运行错误摘要（'运行错误：' 前缀）的失败行 ≥15」——'运行错误：' 是 stderr 摘要的稳定载体（l1007-21 后摘要质量更高），不依赖 Traceback 字样恰好幸存 | 15 行 ≈ 中期可达（现 0→15 需 15 次运行错误型失败；现有 896 题短答池练习量起后可达）；p50/p90/p99 密度比对 15 行样本已可算粗版 |

**附注**：若主班要「真 Traceback 全量」，正解是 l1004-02 案 2 本体（stderr 全量另列存储），属判卷数据模型变更——非本监测单范围。
