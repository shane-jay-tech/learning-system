# l1023-004 补题验收·agent_dev 域（l1011 批 4 个补题 topic 现值验收）

- 复扫基线：artifacts/l-census-1023.json（l1023-001，commit 56aaea7）；content/agent_dev/ 现值 82 yaml 与锚点一致。
- 上批补题 topic 定位：l1011-15..18（done/ result 执行摘要），共 4 个 agent_dev topic；l1011-19 为双 08 撞号判定单（零修改），不另列 topic。
- 验收基准：每 topic ≥5 题；difficulty 1-5 分布非退化；测试自洽抽检 2 题/topic。
- 口径修正（留痕）：agent_dev 域全 82 件零 tests 键，全量 judge_mode=ai_open（rubric＋reference_answer 判分），任务书「tests stdin/expected 自洽」按域实况修正为「ai_open 判分键自洽」（rubric≥3＋reference_answer＋hints 在位）。附：topic 级 _lesson.md 在位检查（07_data_security 为 l1011-15 新目录首建，四 topic _lesson.md 全在 ✓）。

## topic 级验收表（三面）

| topic | 题量(≥5) | 难度直方(非退化) | 判分键自洽抽检（2 题/topic） | 判定 |
|---|---|---|---|---|
| 07_data_security | 5 ✓ | {2:1, 3:2, 4:2} ✓ | 01_spot_pii：ai_open＋rubric 4＋reference_answer＋hints 3 ✓；05_prompt_injection_defense：ai_open 但 rubric/reference_answer/hints 全空 ✗ | 局部不合格（点名 05） |
| 08_read_code | 5 ✓ | {2:1, 3:3, 4:1} ✓ | 02_find_bug_mutable：ai_open＋rubric 4＋ref＋hints 3 ✓；05_read_code_flow：全空 ✗ | 局部不合格（点名 05） |
| 08_review_pr | 5 ✓ | {2:2, 3:3} ✓（两档，非单值） | 01_spot_missing_test：ai_open＋rubric 4＋ref＋hints 1 ✓；05_pr_review_checklist：全空 ✗ | 局部不合格（点名 05） |
| 10_debug_logs | 5 ✓ | {1:2, 2:1, 3:2} ✓ | 01_read_traceback：ai_open＋rubric 4＋ref＋hints 1 ✓；05_log_level_strategy：全空 ✗ | 局部不合格（点名 05） |

## 不合格明细（4 件，validator WARN 交叉印证）

以下四件全部为 l1011 新增 05_ 件，形态一致：judge_mode=ai_open 在位，但 rubric/reference_answer/hints 三键全空（validator WARN「答案四键全空；缺 hints」在册）——ai_open 轨缺判分锚，无法评卷：

1. content/agent_dev/07_data_security/05_prompt_injection_defense.yaml
2. content/agent_dev/08_read_code/05_read_code_flow.yaml
3. content/agent_dev/08_review_pr/05_pr_review_checklist.yaml
4. content/agent_dev/10_debug_logs/05_log_level_strategy.yaml

## 域级门禁证据

- `python scripts/validate_content.py --domain agent_dev` → PASS｜文件 82／解析错误 0／字段 ERROR 0／字段 WARN 4／同名组 0（4 个 WARN 与上表不合格件一一对应）。
- 合格面结论：题量、难度分布、_lesson.md 落库三面 4/4 topic 全达标；判分键面 20 件补题文件中 4 件（全为新增 05_ 件）rubric/reference_answer/hints 全空。
- 双 08 目录并存（08_read_code / 08_review_pr）为目录级分立，无文件级撞号（l1011-19 结论维持，本轮 2 组 topic 各 5 件互不重名）。

## 处置建议（留待内容班，本单零改动）

- 四件统一按同 topic 老件 ai_open 轨口径补 rubric（3-4 条）＋reference_answer＋hints（1-3 条）；修复后复跑 `python scripts/validate_content.py --domain agent_dev` 应 WARN 4→0。
