# learning pytest 全量复跑归因档（l1025-006 · 2026-10-26）

> 口径：PYTHONUTF8=1 python -X utf8 -m pytest tests/ -q；全量 1353 项（**41 failed / 1303 passed / 7 skipped / 2 xfailed**）。锚 384/7（2026-09-18，l927 批后）——套件自此扩 ~3.5 倍，锚值为历史读数非现值判据。

## 归因方法

批前基线 A/B：`git checkout 6c01115~1 -- content tests scripts`（l1025 补题批2 五 commit 前）→ 同 19 个失败文件复跑 → `git checkout HEAD -- …` 还原。基线失败 41 例与本班现值 41 例**逐名相同**（comm 双向 diff：新增 0、消失 0）。

## 41 例失败三族归因（全预存）

1. **域钉值/契约落后盘面（27 例）**：census 族 r×5/sql×5/agent_dev×4/全库 test_content_census×3、difficulty_pins×3、judge_mode_equivalence×4（r 域 84 题）、mark_r_judge_plain×2、paths_difficulty_cliffs×1——与 python 域批1 前同病：批1 扩题后域钉未翻。python 域同族 4 例已由本班补题批2 修复转绿（census_python 5/5）。
2. **环境/边界族（7 例）**：sandbox_limit×2、parser_boundary×1、python_runner_datasets_mount×1、hr_dataset_determinism×1、heatmap_window×1、l1007_19×1。
3. **门禁/索引族（7 例）**：readme_version_gate×3、insights_index_closure×2、scripts content_audit×1、mistakes_redo hints 契约×1。

## 偶发注记（非稳定失败）

首轮全量曾现 42 failed：`test_content_crlf::test_content_yaml_无孤立CR且文件内行尾自洽`。三重复核实：单独跑＝过；a-c 段跑＝过；全量复跑＝过。定性为**顺序性偶发**（全量一次出现过、复现 1/2），与本班 8 个 yaml 改动件无关（8 件实测纯 LF 0 CR）。

## 本班净变化（对照批前基线）

- python census 族 **4 红→0 红**（census_python 5/5：题数/直方/答案字段/judge+hints 全钉翻正至实测终值）
- 新增测试 6 例（test_validate_content_semantic）全绿
- 套件计数：批前 1347 项 → 本班 1353 项（+6）

## 余量（后续车道）

- 27 例域钉翻正需逐域实测（同本班 python 法：loader 实测终值→翻钉），建议立「域 census 钉值翻正批」
- 环境/门禁两族 14 例需逐名根因（多数疑为盘面漂移型：datasets 挂载面、README 指纹、insights 索引闭合）
