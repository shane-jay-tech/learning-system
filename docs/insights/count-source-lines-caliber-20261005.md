# count_source_lines 口径重设材料：git ls-files 法 vs _SKIP_DIRS 法（l1002-29，只读零改码）

- 时点：2026-10-05（exec-shift-20261003-manual）
- 矿源：l924-13 遗留——`_SKIP_DIRS` 不含 data/content/logs（现无 .py 无影响，未来落脚本会重演 tmp 污染）

## 一、双口径读数表（完成标准①，命令内联）

| 口径 | 命令/实现 | 总行 | 分项 |
|---|---|---|---|
| **现值·_SKIP_DIRS 法** | `generate_system_report.count_source_lines()`（os.walk 剪 `.venv/__pycache__/node_modules/.git/.pytest_cache/tmp`） | **35,917** | core 4,372／ui 2,985／tests 24,489／scripts 3,858／other 213 |
| **对照·git ls-files 法** | `git ls-files "*.py"` 逐件计行 | **35,642** | 受版 .py **177 件**（其中 data/content/logs 下仅 1 件） |
| **差值** | — | **275 行（0.77%）** | ＝tmp 探针残留 .py（`_SKIP_DIRS` 剪了 tmp 目录但 tmp 之外仍有游离探针）＋未受版新件 |

两口径现值差 275 行——主要成分：① tmp/ 内 `__pycache__` 覆盖不到的散落探针（.py 直接躺在 tmp 子目录外的游离位置，如历史 `*.mts`/一次性脚本）；② 未 `git add` 的新件（untracked .py——本班开工时即有多件）。

## 二、漂移风险对照表（完成标准②）

| 未来场景 | _SKIP_DIRS 法 | git ls-files 法 |
|---|---|---|
| `data/` 落脚本 | **污染计入**（data 不在剪名单）——矿源点名的重演路径 | 天然免疫（data/ 不入受版） |
| `content/`、`logs/` 落脚本 | 同上污染 | 天然免疫 |
| 新建未 add 的临时 .py（任意目录） | **污染计入**（tmp 剪名单之外全收） | 免疫（untracked 不计） |
| git rm 退役旧脚本 | 仍计入（walk 只看磁盘）→ **虚增** | 正确消失 |
| 换机/净 checkout | 随磁盘态漂 | 恒等于受版真值（可复算性最强） |
| 性能 | os.walk 全盘 | git ls-files 一次调用（更快） |

**结论性观察**：git ls-files 法对全部四类历史污染场景免疫，且「测一次随探针涨一次」类不可复算问题从机制上消失；代价是依赖 git 存在（本仓恒有）与「未 commit 的新代码不计」——后者对「代码行数」这种**库存型指标**恰是正确语义。

## 三、推荐案与迁移步骤（完成标准③）

**推荐：口径重设为 git ls-files 法**（一次迁移，永久免疫）。

迁移步骤（另单执行，本单零改码）：
1. `count_source_lines()` 重写：`subprocess git ls-files "*.py"` → 分桶（core/ui/tests/scripts/other 按路径前缀）→ 计行。约 15 行改动。
2. **口径注记**：新报告的源码行数字段标注「git 受版口径 v2（35,642 基准）」；**历史快照（v0.6.3/0.6.4/v0.6.5）读数不回改**（各快照自注当时口径——v0.6.5 已注「git 受版口径」但实现仍是 walk 法，新报告需注明「实现与标注自此对齐」）。
3. `check_report --check` 同链跟随（同一函数出口）；若历史快照跑 --check 会对不上新口径——建议 --check 加 `--caliber walk|git` 开关保留双口径复算能力（或历史快照只人工核对）。
4. 回归：`tests/` 内若有用例钉 count_source_lines 读数需 rg 确认（本单未发现硬编码行数断言）。

## 四、零改码声明

scripts/generate_system_report.py 零触碰；双口径并跑均为只读。
