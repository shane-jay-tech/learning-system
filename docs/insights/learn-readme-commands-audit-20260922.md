# README 验证命令块只读巡检（l922-109，2026-09-22）

- 巡检人：qoder-executor-20260922-0000-learn4（zcode-bridge 执行班）
- 巡检对象：`README.md:69-78` 验证块（powershell 代码块，8 条命令）
- 基线：HEAD `0dac1f7`，工作树 clean；**本档为唯一新增件，README 与 scripts/ 零改动**
- 方法：源码级逐脚本读 argparse/入口/写盘路径；仅对 argparse 在册的 4 条脚本实跑 `--help` 取证（源码证其 safe），backup/prune/起进程类一律未真跑。

## 一、锚点复核（任务书 vs 磁盘）

| 任务书锚点 | 磁盘实况 | 判定 |
|---|---|---|
| `README.md:74` audit_content | :74 即「python scripts/audit_content.py # 题库内容审计」 | 未漂移 |
| `README.md:76` prune_old_data | :76 即「python scripts/prune_old_data.py # 过期数据清理」 | 未漂移 |
| 验证块 :69-78 共 8 条 | :69 开栏、:70-77 八条命令、:78 闭栏 | 未漂移 |
| 完成标准① `ls scripts/*.py \| wc -l` → 17 | **实测 16** | **任务书预期数过期**（在册核对改用 16，见下）；README 提及 8 条仍全部在册 |

`scripts/` 实测 16 个 .py（`create_shortcut.ps1` 不计）：audit_content / audit_content_deep / audit_paths_prereq / backfill_events / backup_data / bench_imports / bench_pages / find_port / generate_metrics / generate_system_report / health_check / mark_r_judge_plain / perf_baseline / prof_pages / prune_old_data / smoke_boot。README 8 条 = pytest（根目录命令）+ 其中 7 个脚本，**全部在册**。

## 二、分类表（8 条命令 × 入口 / 参数 / 写盘 / 可否夜跑）

| # | 命令 | 入口（文件:行） | 参数面 | 写盘 | 夜跑判定 |
|---|---|---|---|---|---|
| 1 | `pytest` | pytest 工具本身（pytest.ini `testpaths=tests`） | 块内无 | `.pytest_cache/`、`__pycache__/`（测试件产物，非业务数据）；app_test 夹具走 `LS_PROGRESS_DB` 临时库不碰真实库 | **可夜跑**（只读巡检级） |
| 2 | `health_check.py` | `main()` :31，guard :100 | **无**（无 argparse，任何参数被无视） | 无（纯 stdout；仅 Path 存在性/which/import 探测） | **可夜跑** |
| 3 | `smoke_boot.py` | **模块顶层即执行**：`subprocess.Popen` :10，无 main | **无**（无 argparse） | 起 streamlit 子进程 + 绑 127.0.0.1:8599 + 轮询最长 ~30s | **禁夜跑**（起进程） |
| 4 | `perf_baseline.py` | `main()` :56，guard :143 | `--quick` `--json` `--markdown`（:58-60 **手工判 sys.argv**，非 argparse） | `ProgressDAO()` :107 → `core/progress.py` __init__ `os.makedirs`+`sqlite3.connect`+建表（库不存在时**建库**）；其余操作只读查询 | **禁夜跑**（触库 + 默认 5 采样耗时） |
| 5 | `audit_content.py` | `main()` :90，argparse :91-92 | `--strict` | 无（只读 content/ 与 paths yaml） | **可夜跑** |
| 6 | `backup_data.py` | `main()` :93，argparse :94-97 | `--list` `--restore ZIP` `--keep N` | **默认模式写**：WAL checkpoint（写库）+ 写 `data/backups/progress-*.zip` + **轮换删除最旧 zip**（`prune_backups` :80 unlink）；`--list` 只读；`--restore` 覆盖库 | **禁夜跑**（写+删数据文件） |
| 7 | `prune_old_data.py` | `main()` :86，argparse :87-92 | `--days` `--keep-per-problem` `--apply` `--json` | **默认干跑只 SELECT**（但 `ProgressDAO()` :40 init 触库建目录/文件）；`--apply` DELETE + checkpoint + **VACUUM 全库重写** | **禁夜跑**（语义即清理，--apply 重写；干跑虽不删但触库） |
| 8 | `generate_system_report.py` | `main()` :232，argparse :233-237 | `--check FILE` `--check-readme FILE` `--json` `--strict` | 默认只读扫 repo；`--strict` :102 起 `pytest --collect-only` 子进程（可写 .pytest_cache） | **可夜跑**（默认形态） |

汇总：**只读可夜跑 = pytest / health_check / audit_content / generate_system_report（默认形态）**；**写数据或起进程必须日间 = backup_data / prune_old_data / smoke_boot / perf_baseline**。

## 三、`python scripts/xxx.py --help` 可否无副作用执行（逐条判定）

| 脚本 | 判定 | 依据 |
|---|---|---|
| audit_content.py | ✅ 可，实测 rc=0 打印 usage | argparse（:91）parse_args 在 audit() 之前退出 |
| backup_data.py | ✅ 可，实测 rc=0 | argparse（:94），--help 不触 create/restore |
| prune_old_data.py | ✅ 可，实测 rc=0 | argparse（:87），--help 不触 DAO |
| generate_system_report.py | ✅ 可，实测 rc=0 | argparse（:233），--help 先于 generate_metrics |
| health_check.py | ⚠️ 可执行、**无副作用但不出 help**：--help 被无视，直接跑完整检查（纯读，可容忍） | 无 argparse（grep 实测 0 处） |
| perf_baseline.py | ❌ 禁：--help 被无视，**直接开全量基准**（含 DAO init 建库副作用） | 手工 argv 判旗标 :58-60 |
| smoke_boot.py | ❌ 禁：--help 被无视，**直接起 streamlit 进程** | 顶层 Popen :10，无任何参数解析 |

## 四、遗留观察（本单只登记不修）

1. README 验证块**未标注各命令的写盘/夜跑属性**，夜桥若照块执行会误跑 backup/prune——建议后续单把「可夜跑 4 条 / 日间 4 条」并入 README 注释（本单纪律禁改 README 语义，未动）。
2. health_check / smoke_boot / perf_baseline 三脚本无 argparse，与其余 5 个风格不一致；给 perf/smoke_boot 补 argparse 可让 --help 语义统一。
3. 任务书「预期 17 个脚本」与磁盘 16 的差异属规划侧口径过期，交主班转告规划。
