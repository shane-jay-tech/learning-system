# r 题库判定模式显式化：84 题降级为普通题（D6 落地）

- 任务：D6（用户 2026-09-20 拍板「按推荐进行」）— 依据 `docs/decisions/2026-09-20-user-decisions-partials.md` 第 15 行
- 上游事实：l920-02 纵向普查（`zcode-bridge/done/l920-02-learn-r-census.result.md`）
  ——`content/r` 84 个 yaml **无一含 `expected_rows` / `tests` 键**（grep 0 命中），
  loader 侧两字段 84 题恒为 None；r 的答案面是 `expected_output 70 + rubric 14`，
  `judge_mode` 实测 run 70 / ai_open 14
- 用户口径：**降级为普通题**（不硬补测试用例）→ 本单**只改标记字段，不动题干与答案**
- 日期：2026-09-20 ｜ 仓库：D:\code\learning-system ｜ 起点 HEAD：`283629b`
- 性质：**内容数据（r 题库 yaml）改动**——改前已备份、改后有字节级与 loader 级双重回读断言
- 复跑命令：`python scripts/mark_r_judge_plain.py`（dry-run）／`--apply`（写盘，幂等）／`--check`（校验，未完成 exit 1）
  ＋ `--root <dir>`（临时基线）／`--expect-distribution run=70,ai_open=14`（精确分布门禁）
- ⚠️ 后续（2026-09-20）：脚本已去掉 assert 安全依赖（改显式校验 + 非零退出 + 原子写），
  并补 dry-run／apply／重复 apply／check 端到端与字节级单行差分测试；判定模式显式化的等价性证明见
  `tests/test_judge_mode_equivalence.py`。见 `docs/insights/learn-d5d6-review-fix-20260920.md`。

## 一、判定口径：r 题库本来就该按普通题走

| 面 | 计数 | 判定方式 |
|---|---|---|
| `expected_output`（普通题） | 70 | `judge_mode: run`——跑 R 脚本，**stdout 与期望逐字比对**（`core/judge.py:_run_test_cases` 的 else 分支） |
| `rubric` + `reference_answer`（开放题） | 14 | `judge_mode: ai_open`——LLM 按 rubric 评分 |

关键事实：`core/judge.py` 只在 `expected_rows is not None` 时才走「按行比对」的机判分支；r 题库 84 题该字段恒为 None，`RRunner` 也不产出 rows ⇒ **r 题目从来就是 stdout 比对的普通题**，不存在「多 DataFrame 机判题」形态。

那为什么要改？因为 70 个题目**没有写 `judge_mode`**，靠 `core/loader.py:216` 的隐式默认（`or "run"`）运行——「它是什么题」只能靠读代码推断。D6 落地＝把这层隐式显式化：**84/84 逐题写明判定模式**，「r 是普通题」从此可被 grep 和测试钉住。

## 二、改了什么

| 文件 | 类型 | 内容 |
|---|---|---|
| `content/r/*/*.yaml`（**70 个**） | 增量 1 行/文件 | 在 `tags:` 块之后插入 `judge_mode: run`（与既有 14 个 `judge_mode: ai_open` 同位同格式）；**题干、expected_output、rubric、reference_answer、hints、starter_code、title、topic、difficulty、tags 一律零改动** |
| `scripts/mark_r_judge_plain.py` | 新增 | 幂等改标脚本：默认 dry-run、`--apply` 写盘、`--check` 校验；内置「只多 judge_mode」的写前回读断言与写后再计划自证 |
| `tests/test_content_census_r.py` | 增量 | 新增源文件级用例：84/84 必须显式 `judge_mode`、源文件不得出现 `expected_rows`/`tests`（D6 口径钉死） |

**没做的**（有意）：不给 r 补 `expected_rows`/`tests`（用户已拍板「不硬补测试用例」）；不改 `RRunner`（无 rows 能力可用，改它属内容建设前置条件）；不动 `judge_mode` 的既有 loader 默认值（其他语言 300+ 题同样靠默认，属另一笔口径）。

## 三、复跑输出（真实命令，原样粘贴）

Dry-run（改前）：

```
$ python scripts/mark_r_judge_plain.py
r 题目 yaml 总数 = 84；已显式 = 14；待补 = 70
  [dry-run] 将补 judge_mode: run → content\r\01_vectors_and_basics\01_hello_world.yaml
  [dry-run] 将补 judge_mode: run → content\r\01_vectors_and_basics\02_vector_sum.yaml
  [dry-run] 将补 judge_mode: run → content\r\02_logic_and_summary\01_mean.yaml
  ...
dry-run 结束（未写盘；加 --apply 落盘）
```

写盘 + 写后自证：

```
$ python scripts/mark_r_judge_plain.py --apply
r 题目 yaml 总数 = 84；已显式 = 14；待补 = 70
已写盘 = 70
回读：已显式 = 84；仍待补 = 0
PASS：写盘完成且回读一致（幂等：再跑 --apply 将零改动）
```

**幂等证明**（紧接着再跑一次 --apply）：

```
$ python scripts/mark_r_judge_plain.py --apply
已写盘 = 0
回读：已显式 = 84；仍待补 = 0
PASS：写盘完成且回读一致（幂等：再跑 --apply 将零改动）
```

校验模式：

```
$ python scripts/mark_r_judge_plain.py --check
r 题目 yaml 总数 = 84
已显式 judge_mode = 84（ai_open 14 / run 70）
待补 judge_mode = 0
PASS：84/84 判定模式全部显式
```

字节级 + loader 级回读断言（对比 `data/backups/content-20260920-133722/manifest-before.txt`）：

```
r 文件 = 84 | 变更 = 70 | 未变更 = 14
逐文件字节级回读不合格 = 0 []
CRLF 文件数（备份时 16）= 16
loader 侧 judge_mode 分布 = {'run': 70, 'ai_open': 14}
loader 侧 expected_rows/tests 非 None 数 = 0 0
答案/题干面计数 = {'expected_output': 70, 'hints': 84, 'statement': 84, 'rubric': 14, 'reference_answer': 14}
```

逐文件断言内容：新文件字节 == 旧文件字节 **+ 恰好一行 `judge_mode: run`**（插入点唯一）、无 BOM、行尾风格不变（改前 16 个 CRLF 文件改后仍是 16）。

## 四、验收情况

| 完成标准 | 状态 | 证据 |
|---|---|---|
| 改前备份 | **达成** | `data/backups/content-20260920-133722/`（87 文件：3 paths + 84 r + `manifest-before.txt` sha256）；改前复核「与备份清单不一致 = 0」 |
| 只改标记字段 | **达成** | 字节级断言：70 个文件均＝原文 + 恰一行；loader 侧答案/题干面计数与改前完全一致（expected_output 70 / rubric 14 / reference_answer 14 / hints 84） |
| 幂等 | **达成** | 第二次 `--apply` → `已写盘 = 0`；`--check` → `待补 = 0` |
| 回读断言 | **达成** | §三两段输出；不合格数 = 0 |
| 相关测试真跑 | **达成** | `python -m pytest tests/test_content_census_r.py tests/test_content_census.py tests/test_judge.py tests/test_judge_pure.py tests/test_judge_rows_characterization.py tests/test_r_runner.py tests/test_native_runners_mocked.py tests/test_content_fuzz_pins.py tests/test_scripts.py -q` → **99 passed / 3 skipped**（3 skip＝本机无 Rscript，环境条件非缺陷） |
| 全量无回归 | **达成** | `python -m pytest -q` → **487 passed / 7 skipped / 0 failed**（基线 481/7，本单 +6 例） |
| 钉桩留痕 | **达成** | `tests/test_content_census_r.py::test_judge_mode源文件级显式_84之84`：缺显式标记 / 出现 expected_rows|tests 即红 |

## 五、遗留问题

1. **r 题目仍无法按 DataFrame 机判**：若产品上确实需要（例如让学生返回一个 data.frame 并逐单元格判分），前置条件是先定义 r 判题器（`RRunner` 目前不产出 rows）——属**内容建设 + 判题逻辑**改动，本单只落实「降级为普通题」这一步。
2. **`judge_mode` 的隐式默认仍在**：python/cpp/sql/agent_dev 共 300+ 道 run 题同样靠 `loader` 默认值，本单只显式化了 r（D6 范围）；是否全库统一显式属独立口径决策。
3. **判题路径未真机跑过**：本机无 Rscript，`test_r_runner.py` 3 例长期 skip ⇒ 「r 题目 stdout 比对」的实际执行未在本机验证（本单零判题代码改动，属既有环境缺口）。
4. 本单改的是 yaml 文本，**不进运行库**（题库靠文件加载）；若有人拿旧副本部署，需一并带上这 70 行标记（不影响判定结果，只影响可读性/可审计性）。
