# learning pytest 全量终验归档（l1114 · 2026-11-14）

> 口径：`PYTHONUTF8=1 .venv/Scripts/python.exe -X utf8 -m pytest tests/ -q`（pytest.ini 在仓库根；解释器 = 项目 .venv，Python 3.12.9）。
> 背景：10-26 全量 41F（artifacts/l-pytest-1025.md 三族口径）；10-28 commit f0f1eb0 声称已修但终验未跑。本档即补跑的终验实录。

## 首轮实录（2026-11-14，HEAD = 543129f，工作树干净）

**1353 项：2 failed / 1342 passed / 7 skipped / 2 xfailed，272.37s（0:04:32）**

对照 10-26 的 41F：f0f1eb0 修复批有效——41F → 2F（39 例转绿/翻钉）。失败明细：

| # | 失败 | 族（l1025-006 口径） | 根因 |
|---|---|---|---|
| 1 | test_insights_index_closure::test_闭合等式_A等于B_且C为空_且无重复 | 门禁/索引族 | commit 543129f（l1028-10 SM-2 契约档）入库 docs/insights/l1028-sm2-contract-registration.md 但漏登记权威索引表——磁盘 200 份 vs 表 199 条 |
| 2 | test_insights_index_closure::test_新档漏登记必红_改名必红_有牙自检 | 门禁/索引族 | 同上（例 2 以例 1 的盘态为前置，同根因连带红） |

skip 7 例均为环境缺失显式 skip（带原因）：g++ 不可用 ×4（test_cpp_runner）＋ Rscript 不可用 ×3（test_r_runner）——属 l1025-006「环境/边界族」中允许的 skip 口径，不计 F。xfailed 2 例为既有登记桩（paths_order / sql_roworder），非本批事项。

## 修复（门禁/索引族 · 单点）

docs/insights/learn-insights-index-20260918.md（权威索引）：表尾补登 l1028-sm2-contract-registration.md 一行 ＋ 档头对账读数补一笔（A=200、B=200、C=空、重复=0）。零代码、零 content 改动。修复后单文件复跑：test_insights_index_closure 3 passed。

## 复跑终验

第二轮（索引修复后，同日）：**1353 项：1 failed / 1343 passed / 7 skipped / 2 xfailed**——索引族 2 例转绿；唯一失败 `test_find_port::test_源码锚点与start_bat接线仍与磁盘一致` 系本升级批在复跑窗口内先行落地任务 3 的 start.bat 改动（显式 set LLM_SCRIPT 增 2 行）绊倒该哨兵钉的接线行号 :26，非任务 1 修复不净。处置：按哨兵自述口径「该同步本桩」显式同步 :26→:28（随任务 3 commit）。

第三轮（最终树 0F 终验，任务 2 装 pywebview 后全量复跑）：**见下方追加段。**

## 三族清算（对照 l1025-006 的 41 例）

- 域钉值/契约落后盘面（27 例）：f0f1eb0「域钉翻正批」全数翻钉转绿（census/difficulty_pins/judge_mode/mark_r/cliffs 各族现值 437 世代全绿）。
- 环境/边界族（7 例）：f0f1eb0 修复（含 datasets 面翻钉 4→8）；本轮实测 7F 中零残留，环境缺失者已显式 skip 化（g++/Rscript 共 7 例 skip 带原因）。
- 门禁/索引族（7 例）：6 例已修；唯 insights 索引闭合 2 例因 543129f 新档漏登复红——本轮修复闭环。

---

## 【2026-11-14 第三轮】pywebview 装入后全量 0F（任务 2 复测 ＝ 任务 1 终验收口）

树 = 任务 1 索引修复 ＋ 任务 3 先行落地的 start.bat set LLM_SCRIPT／config.py docstring／test_find_port 桩同步 :26→:28 ＋ .venv 装入 pywebview 6.2.1。
**1353 项：0 failed / 1344 passed / 7 skipped / 2 xfailed，247.76s（0:04:07）**（本轮收集先于 tests/test_content_parity.py 落盘，该 6 例单跑 6 passed，终验见第四轮）。7 skip = g++×4＋Rscript×3 环境缺失显式 skip 带原因。**10-26 起的 41F 至此全量清算：0F 达成。**
