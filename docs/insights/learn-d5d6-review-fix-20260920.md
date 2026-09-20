# D5/D6 处置记录：agent_mastery 时数、judge_mode 等价性证明、迁移脚本加固

- 任务：GPT 独立复核判「暂不建议销项」后的三件必修项（+2 条软项）— 2026-09-20
- 上游：D5/D6 落地commit `b68acaf`（l920-09）；复核意见见本轮 parent 会话转达的「GPT 干净版复核」
- 日期：2026-09-20 ｜ 仓库：D:codelearning-system ｜ 起点 HEAD：`b68acaf`
- 性质：内容数据（1 字节）+ 测试 + 工具脚本；**未改题干与答案字段**，judge_mode 相关零内容改动
- 备份：`data/backups/content-20260920-134800-review-fix/`（agent_mastery.yaml + sha256 清单，gitignore 区）
- 门禁：`python -m pytest -q` = **520 passed / 7 skipped / 0 failed**（改动前基线 487/7；新增 33 例）

## 必修 1：agent_mastery 时长失配（PATH-001，CRITICAL）

**问题**：a0..a10 逐个可数 = 4+2+3+3+3+2+2+3+2+2+3 = **29**，而 header `estimated_hours: 22`；
D5 追加 a10 后沿用旧 header，用户按 header 读总时长＝**少报 7 小时（约 24%）**。
旧测试还把该失配写成白名单 `KNOWN_HOURS_MISMATCH = {"agent_mastery": (22, 29)}` 放行。

**修复**：
| 文件 | 改动 |
|---|---|
| `content/paths/agent_mastery.yaml` | `estimated_hours: 22` → `29`（**字节级：仅 1 字节 `2→9`，其余 3962 字节不动**） |
| `tests/test_paths_reconcile.py` | **删除白名单**：全路径强制 `header == sum(里程碑)`；新增「时数为正实数」用例；并断言检查覆盖了全部 path 文件（防循环空了假绿） |

**证据**（备份后回读断言）：
```
$ python %TEMP%assert_hours.py
header = 29 | sum = 29 | milestones = 11
per-milestone: [('a0', 4), ('a1', 2), ('a2', 3), ('a3', 3), ('a4', 3), ('a5', 2), ('a6', 2), ('a7', 3), ('a8', 2), ('a9', 2), ('a10', 3)]
byte-diff count = 1 [(118, '2', '9')]
len(old)=3963 len(new)=3963
PASS: 回读断言 header==合计==29；改动仅 1 字节（'2'→'9'）
```

**变异检验**（把 header 改回 22，看新测试是否真红；随后逐字节还原）：
```
    E  AssertionError: agent_mastery header 时数与里程碑合计不符：header=22 合计=29；逐个=[('a0', 4), ('a1', 2), ...
    FAILED tests/test_paths_reconcile.py::test_全路径_header时数等于里程碑合计_无白名单例外
    1 failed, 3 passed in 0.18s
还原 sha256 一致: True
```

其余路径算术（GPT 已逐个核过，本次复算一致）：cpp_foundation 3+3.5+3.5+5+6=21 ✓、
python_advanced 4.5+4.5+3+6+3=21 ✓、r_advanced 3+4+3+4.5=14.5 ✓、people_analytics 53 ✓。

## 必修 2：judge_mode 显式化的等价性证明（JUDGE-001）

**要求**：70 题从「缺失 judge_mode（吃 loader 隐式默认）」改成「显式 `judge_mode: run`」，
必须证明 loader / dispatcher / runner / 实题双跑结果四层等价，不能靠注释或口头假设。

**新增** `tests/test_judge_mode_equivalence.py`（10 例）：

| 层 | 用例 | 证明方式 |
|---|---|---|
| ① loader | 缺失 vs 显式 run **归一化逐字段全等** | 把真题库 84 题逐个删掉 `judge_mode:` 行复制到临时 content/，与现状题库同为 `load_language("r")` 加载后比较 `Problem` dataclass 与 `to_dict()`；断言 70 道被删、14 道 ai_open 未动 |
| ② dispatcher | 两种写法走**同一条 run 分支** | 注入记录型 runner；断言 runner 收到完全相同的 (code, stdin, expected)，`ai_open` 分支**零调用**；再证「裸 dict（显式/缺失）+ loader 形态（显式/缺失）」四路结果全等 |
| ③ runner | 确定性 runner 全量双跑 + 真 RRunner 实题双跑 | 70 道 run 题 × (正确输出/错误输出) = 140 次 `_run_test_cases` 三元组比对全等；真 RRunner 再对实题双跑（本机无 Rscript → 两边同一条「未检测到 Rscript」；装了 R 则抽 3 题控时） |
| ④ 结果 | JudgeResult 逐字段相等 | passed / ai_feedback / expected_display / actual_display / diff_hint，覆盖「输出正确 / 输出错误 / 空代码」三种输入 |

**非空转保证（阴性对照）**：删掉 **ai_open** 题的 `judge_mode` 后，归一化值必须从 `ai_open` 变 `run`、
判分分支必须从 AI 分支切到 runner（用例断言 `calls == {"ai_open": 1, "run": 1}`）——
否则「等价」就是恒真断言。

```
$ python -m pytest tests/test_judge_mode_equivalence.py -q
..........                                                               [100%]
10 passed in 5.99s
```

## 必修 3：迁移脚本加固（去 assert 依赖 + 端到端 + 字节级差分）

**问题**：`scripts/mark_r_judge_plain.py` 的安全防护用了 `assert`（`python -O` 直接剥离）；
缺「重复执行 / 异常输入 / 只允许插入一行」的字节级证明。

**加固后**（重写该脚本）：
- **零 assert 依赖**：全部校验改为显式 `raise HardeningError` + `main()` 捕获 → 非零退出 + 明确 FAIL 诊断；
- **fail-closed**：任一形态异常（无 tags / 无 expected_output / 空输出 / 坏 yaml / 非法模式值 /
  空或重复 judge_mode 行 / tags 后缩进续行）→ **整批一个字节都不写**；
- 合法值枚举 `run / ai_open`；插入边界校验（锚点顶格、插入后非缩进续行、解析回读只多 judge_mode）；
- **字节级单行差分**：写盘前 `new == old + 恰一行`，写盘后回读比对新字节；原子写（临时文件 + `os.replace`）；
  路径必须落在 `<root>/content/r/` 内；
- 新增 `--root`（对临时基线跑端到端）与 `--expect-distribution run=70,ai_open=14`（精确分布门禁）。

**新旧行为对照**（同一异常输入：坏文件混在合法文件里，`--apply`）：
```
== 异常输入（bad_no_tags 混在合法文件里）==
旧版 no-O                exit=1 写盘文件=['01_missing.yaml', '04_crlf.yaml'] 有Traceback=True
                        末行诊断: ValueError: 找不到顶层 tags: 行，拒绝猜测插入位置
新版 no-O                exit=1 写盘文件=[] 有Traceback=False
                        末行诊断: FAIL：存在 1 个形态异常文件，整批不写盘（fail-closed）
旧版 -O                  exit=1 写盘文件=['01_missing.yaml', '04_crlf.yaml'] 有Traceback=True
新版 -O                  exit=1 写盘文件=[] 有Traceback=False
                        末行诊断: FAIL：存在 1 个形态异常文件，整批不写盘（fail-closed）
```
⇒ 旧脚本会**部分写盘**再崩栈（`-O` 下同样如此），新脚本整批拒绝、零写盘、退出码 1。

**新增** `tests/test_mark_r_judge_plain.py`（18 例）：dry-run 零写盘 / apply 字节级恰插一行 /
重复 apply 零改动 / check 未完成 exit 1 完成后 exit 0 / 分布门禁 / 5 类异常输入 fail-closed /
`-O` 下防护仍生效 / 路径边界拒写 / 两行插入被拒 / 块状 tags 插到块尾 / 真题库 84 行「删掉再插回字节完全相等」/
真题库 `--check --expect-distribution run=70,ai_open=14` 只读门禁。

```
$ python -m pytest tests/test_mark_r_judge_plain.py -q
..................                                                       [100%]
18 passed in 4.19s
```

**测试是否有牙（变异检验）**：把脚本临时换成 git HEAD 旧版跑同一批测试 → `17 failed, 1 passed`（1.84s），
还原后 sha256 一致。

## 字节级基线：D6 的「新文件 == 原文 + 恰一行」复核

用**改动前备份**（`data/backups/content-20260920-133722/`）而非 git blob 做对照
（`core.autocrlf=true`：16 个文件 `i/lf w/crlf`，用 `git show` 对照会被 CRLF 噪声误导）：

```
manifest entries=87  integrity_failures=0
r files=84  identical=14  exactly-one-line-inserted=70  OTHER=0
exit=0
```
⇒ D6 的字节级主张**成立**（70 题 = 原文 + 恰一行 `judge_mode: run`，含 16 个 CRLF 文件行尾原样保留）。

## 软项处置（成本低，已做）

- **F-08 精确数字当不变量** → `tests/test_paths_coverage.py` 重写为性质断言（集合语义）：
  每一条磁盘 topic 至少被一条 path 引用 / path 引用必须存在 / prereq 必须存在且无环；
  删除 85、13 等硬编码，改用 `set(磁盘) == set(引用)`（TEST-003）。
- **F-10 反向封条** → `tests/test_content_census_r.py` 分区为「census 快照 / 可用性契约」，
  并把「任何 R 题出现 expected_rows|tests 即失败」换成 **schema 版本开关 + 业务语义规则**：
  版本 1 = 现状快照（出现机判字段时提示把 `R_SCHEMA_VERSION` 升到 2，而非永久封杀）；
  语义规则永久有效（机判字段必须 `judge_mode: run` + 配 `setup_sql` + 判定面唯一）。

自检证据：
```
A) 版本=2 时： ['1 skipped in 0.06s']
   还原 sha256 一致: True
B) 半成品：有 expected_rows 但没 setup_sql        → 规则拦下：expected_rows 必须配 setup_sql
B) 半成品：机判字段 + judge_mode=ai_open         → 规则拦下：声明机判字段就必须 judge_mode: run
B) 半成品：机判字段 + 同时有 expected_output      → 规则拦下：机判字段不该同时声明 expected_output
B) 合规机判题（版本 2 的合法形态）                 → 规则放行
```

## 门禁与残留

```
$ python -m pytest -q
520 passed, 7 skipped in 49.73s
```
（7 skipped 与基线一致：g++ ×4、Rscript ×3）

**残留 / 未做**：
- 本机无 Rscript、无 g++ ⇒「实题双跑」在真执行层面是「两边同一条未检测到 Rscript 结果」的差分对比，
  等价性的**判分逻辑**层面由确定性 runner 全量覆盖（140 次双跑）；装上 R 后同一用例会自动覆盖真实执行（抽 3 题控时）。
- 未改其他语言 300+ 题同样依赖 loader 隐式默认的现状（另一笔口径，需用户拍板）。
- `tests/test_paths_reconcile.py` 仍保留 quick_stats 跨里程碑重复引用的白名单（同 path 内重复计数致进度虚高），
  属既有内容问题，未在本轮范围内处置。

## 第二轮复核修复：SCRIPT-001..004（2026-09-20，第二轮 GPT 复审 4 条未消解意见）

只改 `scripts/mark_r_judge_plain.py` 与 `tests/test_mark_r_judge_plain.py`（content/ 一个字节未动）。

| 意见 | 处置 |
|---|---|
| **SCRIPT-001**（MAJOR）`--apply` 逐文件写盘，部分写盘后失败不回滚 | 改两阶段：① `prepare_all` 把全部目标生成为 (old,new) 并**全部验证通过**（本阶段零写盘）；② `commit_all` 先 staging（全部新内容落成同目录排他临时文件）再逐个 `os.replace`，任一失败即**回滚已替换文件**；提交后回读不达标（含最终 scan 异常/分布不符）同样整批回滚。回滚失败会点名列出待人工恢复文件。 |
| **SCRIPT-002**（MAJOR）固定临时名 `<file>.tmp<PID>` + `open(tmp,"wb")` 可被预置符号链接抢先 | 弃固定名，改 `tempfile.mkstemp(dir=path.parent, prefix=..., suffix=...)` 的 O_EXCL 独占 fd 写入；写入前/写入后再各校验一次「临时名是普通文件且 st_dev/st_ino == fd 的」；`os.replace` 后再查非符号链接 + 回读比对；目标本身是符号链接一律拒绝。 |
| **SCRIPT-003**（MINOR）scan 只捕 HardeningError，OSError/权限/文件消失不转 FAIL | scan/apply/commit 全程把 `OSError`/`UnicodeError`/`yaml.YAMLError` 统一转 `HardeningError`（`main()` 另有兜底 catch → 非零退出、不崩栈）；提交前用「文件集合 + 逐文件 sha256 快照」复核，发现增删或内容被并发改动即终止且不提交。 |
| **SCRIPT-004**（MINOR）`content/r` 为空时 vacuous pass | 0 个 yaml 一律 FAIL（`--check` 旧输出「PASS：0/0 判定模式全部显式」不再出现）；仅小型 fixture 场景可显式加 `--allow-empty`。 |

**新增测试 10 例**（`tests/test_mark_r_judge_plain.py` 18 → 28）：第二个文件写盘失败（真机只读属性 →
`os.replace` WinError 5）时第一个文件回滚原字节 / 第二个文件被并发篡改 → 整批终止零提交 /
写盘后回读不达标 → 整批回滚 / staging 失败 → 原文件分毫未动 / 固定名抢占（哨兵文件）已失效 /
提交前临时名被换成链接（符号链接，本机无权限时退化为硬链接）→ 拒绝并回滚且外部文件零改动 /
临时文件身份校验契约单测 / scan 遇 OSError（`*.yaml` 是目录）统一 FAIL 零写盘 /
顶层 IO 异常统一 FAIL / 空输入 vacuous pass 与 `--allow-empty` 逃生门。

**变异检验（阴性对照，6 项全部按预期转红）**：

```
M1  注掉 commit_all 的回滚调用        → FAILED test_第二个文件写盘失败…、test_临时文件_提交前被换成链接… (2 failed)
M1b 注掉 _run 的写盘后回读回滚分支     → FAILED test_写盘后回读不达标_整批回滚 (1 failed)
M2  临时文件改回固定名 + open 跟随     → FAILED test_临时文件_固定名抢占攻击已失效、test_staging阶段失败… (2 failed)
M3  注掉空输入守卫                    → FAILED test_空输入_check不再vacuous_pass… (1 failed)
M4  scan 不再把 OSError 转 anomaly     → FAILED test_scan遇到OSError_统一FAIL零写盘 (1 failed)
M5  提交前不复核目标字节               → FAILED test_第二个文件被并发篡改… (1 failed)
每次还原后 sha256 与本轮定稿一致（F774AF93AD480DE2696012BDF09BB44C89F038822F0194965F992B251AF6377B）
```

**真数据规模端到端（在临时根里复制真实 84 题，content/ 零改动）**：

```
① 真实语料 84 个 yaml 复制到临时根
② 摘掉 70 个 judge_mode: run 行；--check exit=1（期望 1）
③ 批量 --apply：exit=0｜已写盘 = 70｜PASS：写盘完成且回读一致
④ 迁移后 84 文件 vs 真实 content/r 逐字节：完全一致 ✓
⑤ 幂等：再 --apply exit=0，已写盘 = 0，字节未变：True
⑥ 真规模回滚：把排序最后的目标文件设为只读再 --apply
   exit=1｜FAIL：提交阶段失败（已回滚 69/69 个已替换文件）…；全部目标已恢复原字节，未留半写状态
   全部文件恢复原字节：True｜*.tmp 残留：无 ✓
```

**门禁**：

```
$ python -m pytest -q
530 passed, 7 skipped in 47.05s          # 基线 520/7 → +10 例（7 skipped 不变：g++ ×4、Rscript ×3）

$ python scripts/mark_r_judge_plain.py --check --expect-distribution run=70,ai_open=14
PASS：84/84 判定模式全部显式              # exit=0
```

**残留 / 未做**：`_run` 的「写盘前 dry-run / check」仍按需重新扫描（未加缓存，84 题开销可忽略）；
POSIX 上「持有 fd 时被 unlink 后换名」只能靠身份校验拦（本机 Windows 连 unlink 打开中的临时文件都会
WinError 32 拒绝，故该路径按契约单测覆盖）；跨文件系统的目录（临时文件与目标不同卷）不受支持
——`mkstemp(dir=path.parent)` 已保证同目录。

