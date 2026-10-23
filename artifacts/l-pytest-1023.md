# l1023-020 pytest 全量复跑现值（2026-10-23 夜班实测）

- 全量命令：`python -m pytest -q --tb=no`（根目录，pytest.ini testpaths=tests），完整日志 `tmp/l1023-020/full-0228.log`（74 行，含 44 条 FAILED 名单）。
- 树状态锚定：HEAD＝67c3231（本班 l1023-012 双 schema 提交；此后 018/020 仅新增 docs 类 artifact，代码面一致）；工作树干净。

## 一、现值计数

| 口径 | 值 |
|---|---|
| **passed** | **1295** |
| **failed** | **44** |
| skipped | 7（恒 skip：本机无 g++/Rscript，cpp runner 4＋r runner 3，与 plan.md:33 口径一致） |
| xfailed | 2 |
| 收集项合计 | 1348 |
| 墙钟 | 211.99s（README:85「全量约 400s」已失时效——现机实测快约 47%） |

## 二、与锚点口径对比

| 锚点 | 值 | 判定 |
|---|---|---|
| memory「384 passed/7 failed」（2026-09-18 实测） | 现 1295/44 | **严重时效**：套件规模 391→1348 收集项（9-18 后多批加测试）；失败 7→44。锚点未留 7 名名单，逐名「已修复」核销不可行——按 plan.md:33 基线链（1241/8/7 @10/2）判定：旧 7 名在 10/2 基线换代时已不在失败集，构成已换血 |
| plan.md:33「1241/8/7」（10/2 @cf-head） | 现 1295/44/7 | 10-23 期间 failed 8→44，增量全部对位 **l1011 内容批**（见下三分类），无本班新增 |

## 三、失败集画像（44 名三分类，逐名归因——不修，只画像）

### A 类：l1011 内容批数字/分布/契约钉撞新题（37 名）

| 文件 | 名数 | 报错归因（实测原文摘要） |
|---|---|---|
| test_content_census_sql.py | 5 | l1011 sql/01 +3、sql/02 +2、sql/12 +1（fc1a5cf）：题数/直方/setup_sql/expected_rows/hints 分布全数过期 |
| test_content_census_r.py | 5 | l1011 r 批 8 题：84→92 题数钉、难度直方、答案面、judge_mode 契约 |
| test_content_census_python.py | 4 | EXPECTED_PROBLEMS 125 vs 实测 136 等（l1011 python 批） |
| test_content_census_agent_dev.py | 4 | l1011 agent_dev 4 topic 新增（6ccb551/0ed67cc） |
| test_content_census.py | 3 | `total == 408` vs loader 现值 437（README 官方口径钉） |
| test_content_difficulty_pins.py | 3 | `sum == 408` vs 437＋直方＋ge4 名单 |
| test_judge_mode_equivalence.py | 4 | `{run:76, ai_open:16} != {run:70, ai_open:14}`；「84题源文件」→92（r 批改分布） |
| test_mark_r_judge_plain.py | 2 | 「content/r 题目 yaml 总数 = 92」vs 钉 84；70_14 分布门禁 |
| test_readme_version_gate.py | 3 | 「README 未包含题目数 437」（gate 活算值 437 vs README:54 408——l1023-018 R1 同源） |
| test_hr_dataset_determinism.py | 1 | hr 三件数据集引用题面「12 件→13 件」（l1011 python/22_hr_model/05 引 datasets） |
| test_mistakes_redo_lifecycle.py | 1 | hints 长度直方 {3:350, 2:41, 1:28, **0:18**} vs 契约 [1,2,3]——**18 件零 hints**，与 l1023-009（4 件）/011（6 件）候选清单交叉印证 |
| test_paths_difficulty_cliffs.py | 1 | quick_stats 断崖/平台 (0,3) vs 契约 (0,2)——路径引用域难度分布被 l1011 新题改动 |
| test_scripts.py | 1 | test_content_audit_real_repository_is_clean——audit 白名单未收编 l1011 新形态（班前简报已点名） |

### B 类：docs 登记滞后（2 名，2026-10-08/09 档）

- test_insights_index_closure.py ×2：磁盘 199 份 .md vs 索引表 193 条，未登记 6 份（l1010-42/43、learning-a4、learning-deadcode、privacy-recheck、toolchain-install-list）——「现值本身不闭合，先修盘子再谈自检」。

### C 类：班前行为钉过时/登记型红（5 名，非内容批、非本班）

- test_sandbox_limit_boundaries_20260925.py ×2：`assert 333298 == 1000000//3`、`assert 599936 == 1000000`——l1007-02 头尾保留截断（_truncate 改头 60%＋尾 40%）落地后旧字节钉未刷。
- test_parser_boundary_inputs_20260925.py ×1：「本用例登记的是『结论已被切掉』这一实况」——登记型已知偏差红。
- test_l1007_19_lesson_read_pin.py ×1：「warning 单通道现状」——loader 不可读 lesson 的 warning 行为登记型红。
- test_heatmap_window.py ×1：`assert "datetime('now', '-91 days')" in src` 于 `_render_heatmap` 函数体内失败——查询文本已外移/改写，文本钉过时（README:75 的 91 日格口径本身仍由 dashboard.py:590 处查询承载）。

## 四、本班零贡献核验

- 本班唯一代码改动 67c3231（validate_content.py＋新增测试文件）；tests/ 内无任何失败用例 import validate_content（grep 证），A/B/C 三类根因均早于本班或在班前简报已知集内。
- T0 子集对照（tmp/l1023-012/baseline-0216.log vs after-0222.log）：22 failed 失败集**逐名相同**（IDENTICAL-FAILSET）；A 类 22 名在 T0 全量档中即红——非本班造成。
- 本班新增 5 例（test_validate_content_dual_schema.py）全过，计入 1295 passed。
