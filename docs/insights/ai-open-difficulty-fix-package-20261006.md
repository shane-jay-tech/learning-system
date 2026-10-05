# 开放题丢 difficulty 修法执行包（l1004-12；99e7 遗留1）

> 产线：执行班 l1004-12（2026-10-06）。**材料型（排期语义变更属判分邻域，落码权留人工）**；差异注：l1002-26 裁的是 difficulty **档位语义阈值**，本单是**入口丢参缺陷**。

## §一 现值（行号贴出，一行修仍适用 ✓）

- 丢参点：`core/judge.py:371`（`_judge_open` 写库分支）——`d.update_review_state(lang, pid, res["passed"])` **三参**，difficulty 走默认。
- 消费点：`core/progress.py:393` `def update_review_state(..., difficulty: int = 3)`；`:409-410` `if difficulty >= 4: ease = max(1.5, ease - 0.1)`——**唯一使用 difficulty 的分支**；d1/d2/d3 在该函数内行为完全一致（无 elif）。
- 对照正身：run 路径 `judge.py:346` `difficulty = int(pdict.get("difficulty") or 3)` → `_record_attempt(..., difficulty)` → 四参。
- **一行修（矿源原文仍适用）**：`_judge_open` 写库分支内补 `difficulty = int(pdict.get("difficulty") or 3)`，`:371` 补成四参。

## §二 ai_open 家族回归面（content/ 全量普查，本班实测）

`judge_mode ∈ {ai_open}` 共 **70 题**：difficulty 分布 d1=7／d2=23／d3=31／**d4=8／d5=1**。
- **行为变化面＝d4+d5 共 9 题**（ease 降档分支从「永不触发」变「按题触发」）；**d1-d3 共 61 题行为零变化**（丢参默认 3 与显式 1/2/3 在 update_review_state 内等价）。
- 家族用例清单（测试侧）：`tests/test_content_census_python.py`（judge_mode 分布钉 run 117/ai_open 8）／`tests/test_content_census_agent_dev.py`（run 30/ai_open 48＋rubric 键集钉）——落码批次须跑；`_judge_open` 直测建议新增 1 例（d4 题答对 ⇒ ease 1.9）。

## §三 副本对照实验（tmp DAO，ease 样例 ≥3 题 ✓）

初态 (interval=3, ease=2.0, streak=0)，连续两次答对：

| difficulty | 修后（FIX 按真值） | 现状（BUG 丢参恒按 3） |
|---|---|---|
| d=3 | pass1 (2.0, 6, 1) → pass2 (2.0, 12) | 同左（**零差异**） |
| d=4 | pass1 (**1.9**, 6, 1) → pass2 (**1.8**, **11**) | pass1 (2.0, 6, 1) → pass2 (2.0, 12) |
| d=5 | pass1 (**1.9**, 6, 1) → pass2 (**1.8**, **11**) | pass1 (2.0, 6, 1) → pass2 (2.0, 12) |

即：难题（d≥4）答对后 ease 每次多降 0.1，第二遍 interval 已差 1 天（11 vs 12）；随通过次数复利，排期差距持续放大——「学生可见排期语义变更」的量化样例。

## §四 执行包（主班放行后照此落）

1. diff＝两行（:371 前补 difficulty 取值行＋改四参调用）；2. 回归＝跑 census 两件＋新增 d4 直测例；3. 影响公告＝9 题（d4=8、d5=1 名单可按 content/ 普查口径重导出）的复习排期自落码日起变紧；存量 review_state 行**不做回填**（下一次通过自然收敛到新曲线），属「历史值不改写」纪律。
