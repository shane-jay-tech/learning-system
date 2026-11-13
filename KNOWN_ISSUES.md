# KNOWN_ISSUES —— 已知问题登记（首版 · l1114 · 2026-11-14）

> 收录口径：README / plan.md / xfail 桩 / 升级批（l1114）中散落的**已知且未闭合**问题，
> 逐条编号，供后续批次认领。已闭环的历史项列在末节「已闭环」备查。
> 状态标记：`开放`（待处理）／`容忍`（有明确裁决，按现状接受）／`已闭环`。

## 开放 / 容忍问题

### K-1 沙箱未管控面（容忍）——README:67
`local_only` 单人模式下，学生代码执行器已知未管控面：**网络出站、护栏外文件系统写位、
解释器目录内旁路可执行文件**。单人场景按可接受风险对待（裁决材料：
`docs/insights/sandbox-network-identity-path-material-20261006.md` F-2/F-5/F-6、
`docs/insights/l927-11-fs-constraint-adjudication.md` F-1）。
公开部署（`RUNNER_SECURITY_MODE=public`）已拒绝执行学生代码，不受本条影响。

### K-2 多行 SQL 题行序不承重（开放 · 跨层矛盾 · xfail 钉）——tests/test_sql_roworder_fragile.py
7 道无 top-level ORDER BY 的多行题：判分按 `expected_rows` 位置逐行比对，而 sqlite 不保证
无 ORDER BY 查询的行序 ⇒ 题面排序要求实际不承重、判分依赖引擎返回序（l922-129 钉）。
清单与三条出口见 `docs/insights/learn-sql-roworder-census-20260922.md`。
命中集合清空即 XPASS＝哨兵转红，届时删桩并回写普查档。

### K-3 路径里程碑顺序与语言页顺序倒置（开放 · 规划域 · xfail 钉）——tests/test_paths_order_consistency.py
`python_advanced` p4/p5 的 yaml 书写顺序与 loader 字典序真倒置（2 处）。出口二选一：
重排 yaml 或加显式 `order:` 字段（属规划域拍板）。清单见
`docs/insights/learn-paths-order-consistency-20260922.md`。

### K-4 cpp 参考解未经编译对拍（容忍 · 环境缺失）——plan.md「补题规范」注
l927-27 批 cpp 5 题参考解在本机无 g++ 环境下入库，正确性按算术事实与教材口径自证
（出处行在各 yaml 首行注释）。装 g++ 后跑 `tests/test_cpp_runner.py`（现 4 例 skip）即可对拍。

### K-5 g++ / Rscript 本机缺失（容忍 · 环境缺失）
C++ 与 R 的运行器测试各以显式 skip 带原因跳过（g++×4 / Rscript×3，全量 7 skip 的全部来源）。
装机清单见 `docs/insights/toolchain-install-list-20261008.md`。

### K-6 AI 判题依赖仓外脚本（容忍 · 架构裁决）
AI 判题子进程脚本 `llm_call.py` 不在本仓内（默认 `D:/code/scripts/llm_call.py`，可经
`LLM_SCRIPT` 环境变量覆盖；`start.bat` 已显式设置）。克隆本仓到新机器后、配置 `LLM_SCRIPT`
指到可用脚本前，AI 点评/判题不可用（普通运行/判题不受影响）。`.venv` 侧 openai 2.44.0
已由 l1114 批补装，不再依赖根解释器。

### K-7 requirements-freeze.txt 口径失真（容忍 · 历史保留）
`requirements-freeze.txt` 是**根环境** 196 包快照，非本仓项目锁，不可用于复现 .venv。
l1114 起项目锁 = `requirements-lock.txt`（80 包，`.venv` pip freeze 实取）。旧 freeze
保留仅作历史参考，勿再引用。

### K-8 l 域未派增强面 5 项（开放 · 低优先）——artifacts/l-legacy-closeout.md 桶二
多 case tests / 判分增强等功能不失效的纯增强面，维持未派，随扩题批顺带。

## 已闭环（备查）

- **README:72 版本串副本无哨兵**：l1114 挂 `tests/test_content_parity.py`（版本串三副本
  + 437/85/6 计数对账）——plan.md「版本串人肉副本清单」#4 的「无哨兵（人肉自觉）」注销。
- **plan.md 等值点表 #4 现值列漏刷**（仍引 399 世代）：l1114 现值化为 437。
- **.venv 缺 pywebview / openai**：l1114 批补装（pywebview 6.2.1 / openai 2.44.0）并锁入
  `requirements-lock.txt`。
- **10-26 全量 41F**：f0f1eb0 修复批 + l1114 终验补登（insights 索引 l1028 档），全量 0F。
