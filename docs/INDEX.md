# learning-system docs/ 索引（l1023-021 落盘，2026-10-24 实测）

- 口径：**docs/ 层级索引**——根文件逐条登记（文件/主题/入库日期）；`insights/` 域用「域指针＋计数」覆盖（逐条登记单源归内部权威索引，本文件不复制逐条清单——避免出现第二份会漂移的手工登记面）。
- 工具现状：根仓 `rebuild-insights-index.py --root` 泛化（n1011-17 遗留候选）上游 n1023 系**未闭合**、learning-system 仓内无此脚本——本索引为手工汇编；工具落地后可改为重建产物（见维护注记）。

## docs/ 根（3 份，逐条）

| 文件 | 主题 | git 入库日期 |
|---|---|---|
| docs/system-report-v0.6.3.md | 系统报告快照（v0.6.3） | 2026-07-14 |
| docs/system-report-v0.6.4.md | 系统报告快照（v0.6.4） | 2026-09-02 |
| docs/system-report-v0.6.5.md | 系统报告快照（v0.6.5） | 2026-09-02 |

## docs/insights/（199 份，域覆盖）

- **权威逐条索引**：`docs/insights/learn-insights-index-20260918.md`（表结构 `| docs/insights/<file>.md | 日期 | 主题 | git 入库 | 引用数 |`；09-17 旧索引按「历史快照原样保留」原则在册并已列入其表）。
- **闭合哨兵**：`tests/test_insights_index_closure.py`——A（磁盘数）== B（索引表条目数）且 C（差集）空且无重复；零字面量设计，增删档只要同步登记即绿。
- **当前闭合状态：未闭合**（l1023-020 全量跑 B 类点名）——磁盘 199 份 vs 索引表 193 条，**6 份未登记**：l1010-42-brace-balance-wiring-20261009、l1010-43-solved-with-timestamps-adjudication-20261009、learning-a4-20261008、learning-deadcode-20261008、privacy-recheck-20261008、toolchain-install-list-20261008。修复属另单，本索引只记录不代修。
- 入库月度分布（`git log --diff-filter=A` 实测）：2026-09＝137 份／2026-10＝62 份；文件名 8 位日期 token 跨度 20260905→20261009（63 份以任务号命名无日期 token，入库日期以 git 为准）。
- 命名形态：任务号系前缀（l9xx/l10xx 等）65 份／主题命名 134 份。

## 维护注记

- 新增 insights 档：**先登记 `learn-insights-index` 最新版表格**（否则 closure 哨兵当场红）；本文件只需更新本域计数行。
- 新增 docs/ 根文件：在上表逐条登记（文件/主题/入库日期）。
- 泛化工具（--root learning-system）落地后：本文件可改为工具重建产物，逐条登记面仍以内部权威索引为单源。
