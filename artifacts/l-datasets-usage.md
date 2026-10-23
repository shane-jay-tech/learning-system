# datasets 域使用面调查（l1023-019 · 2026-10-23/24 夜班材料）

> 性质：只读调查材料（artifacts/ 草件），零代码/数据/文档改动。任务书前提「datasets 域 2026-10-23 目录扫描为空/不存在」经盘面核实为**漂移**：content/datasets/ 实存 4 件（generate_hr_data.py ＋ hr_employees.csv ＋ hr_recruitment.csv ＋ hr_survey.csv），下述结论以盘面为准。

## 一、结论：在用域（非僵尸引用）

datasets 是 python hr 族题面的**真数据依赖**，三件 CSV 一件生成器各有明确消费方：

| 资产 | 消费方 | 状态 |
|---|---|---|
| hr_employees.csv | 12 件 python 题面直接 read_csv（20_hr_pandas 4／21_hr_viz 4／22_hr_model 4），经 PythonRunner 只读挂载 | 在用（主消费面） |
| hr_recruitment.csv / hr_survey.csv | 无题面消费；tests md5 硬钉确定性夹具（l1006-05 案B转正登记） | 夹具在用、题面待扩 |
| generate_hr_data.py | 生成器（random.seed(42)）；test_judge_repeat_stability_20260925 点名为全仓唯一 random 源 | 在用（可复现源） |

## 二、引用面全清单（rg 实测）

1. **代码 1 处（活）**：core/runners/python_runner.py:152-161——l930-07 落地：把 content/datasets/ copytree 进判题 tmpdir 并整树只读（_make_tree_readonly），学生代码 read_csv("datasets/…")（题面写作 content/datasets/…，挂载后相对路径可达）。sql/r/cpp runner 零引用。
2. **测试 6 文件**：
   - tests/test_python_runner_datasets_mount.py——挂载三钉（可见可读／整树只读／FILES 4）；
   - tests/test_hr_dataset_determinism.py——hr_recruitment/hr_survey md5 硬钉；
   - tests/test_hr_dataset_columns_snapshot.py——列快照钉；
   - tests/test_paths_reconcile.py:51、tests/test_paths_coverage.py:46——口径注记（datasets/ 无 topic 子目录不参与 lesson/coverage 口径）；
   - tests/test_judge_repeat_stability_20260925.py:7——random.seed(42) 唯一 random 源判重注记。
3. **题面 12 件（活）**：content/python/20_hr_pandas/{01..04}、21_hr_viz/{01..04}、22_hr_model/{01..04}（题面均引用 content/datasets/hr_employees.csv）。
4. **配置**：.coveragerc:7 omit content/datasets/*。
5. **README**：:104（覆盖率 omit 注记）、:115-117（目录说明＋l1006-05 夹具转正登记）。
6. **plan.md：零引用**（任务书预期「plan.md 与 README 的 datasets 引用」——plan.md 实查 0 处，漂移留痕，无文档欠账）。
7. **ui/、app.py**：零引用。

## 三、处置建议（材料，待主班裁决，本单未动手）

1. **README:115 措辞校正**（一行 docs 单）：「SQL / R 练习用的示例数据」与实况不符——实际唯一消费方是 python hr 族题面（PythonRunner 挂载）；建议改「Python hr 族练习用示例数据（PythonRunner 判题时只读挂载）」。
2. **hr_recruitment/hr_survey 题面消费为零**：扩题候选（README 已预登记「hr 族扩题可直接引用」）；若长期无扩题计划，可降级评估去留（夹具钉在，删除成本=两测试+登记注记，非本单范围）。
3. **题面路径形态**：题面用 content/datasets/…、挂载后为 datasets/…，python_runner:152 注记已对译——无欠账，仅备忘。
4. **census 口径**：datasets 域无 yaml 题件，不参与各域 census 钉（validate_content.py 按域计数亦恒 0）——正常，无需钉值。

## 四、证据基线

- 盘面：find content/datasets -type f → 4 件。
- rg datasets 全仓：代码/测试/配置/文档命中面如上；plan.md grep -c datasets → 0。
