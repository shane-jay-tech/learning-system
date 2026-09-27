# learning 测试基线复测（384 基线后漂移）——l927-03，2026-09-27

> 执行：信箱波次 19 只读采集子班 `qoder-executor-20260927-1400-learn44`，cwd `D:\code\learning-system`。
> 时戳 `2026-09-27T13:50+08:00`（本机 `date` 校时会双向跳，落笔前复取）。
> 起点盘态：HEAD `2665f0a`、`git status --porcelain` 行数 **0**（与派单横幅 13:4x 现值一致，本班自行复跑核对）。

> ⚠️ **caveat（负载红解读口径，与 result／claims 三处同文）**：本单按卷宗完成标准①要求**跑全量 pytest**，
> 属波次 19 共通指示 §5「并发不跑全量」的**合法例外**；同刻有兄弟班 `kaoyan74`／`colony38`／`quant45`／
> `psy74`／`train42` 在各自域并发跑测。**因此本档任何"红／慢"读数都可能是并发负载所致、不可单独归因给本仓**；
> 本班实测结果为零红（见下），但耗时 152.82s 这一项在并发下不作性能结论。

---

## 一、全量命令与计数（磁盘现取）

命令（仓库根执行，口径与 `plan.md:33` 一致）：

```bash
cd /d/code/learning-system
sha256sum data/progress.db | cut -c1-8     # 跑前 → cd2dbce4
PYTHONIOENCODING=utf-8 python -m pytest tests -q -p no:cacheprovider
sha256sum data/progress.db | cut -c1-8     # 跑后 → cd2dbce4
```

| 项 | 现值（2026-09-27 @ `2665f0a`） |
|---|---|
| passed | **1162** |
| failed | **0** |
| errors | **0** |
| skipped | **7** |
| xfailed | **3** |
| 合计 collected | **1172**（1162+7+3 自洽） |
| 耗时 | 152.82 s（0:02:32） |
| 输出尾行原文 | `1162 passed, 7 skipped, 3 xfailed in 152.82s (0:02:32)` |

**7 条 skip 构成复算**（定向复跑 `-rs`，`9 passed, 7 skipped in 0.09s`，rc=0）：
`tests/test_cpp_runner.py` 4 条（`:13` 整件 `pytestmark = skipif(not _gpp_available())`）＋
`tests/test_r_runner.py` 3 条（`:10` 整件 `skipif(not _r_available())`）。
⇒ 与基线自述「cpp runner 4 + r runner 3，非『7 条 R』」**逐位相符**；本机 `which g++` 仍 `NO_GPP`（未装）。

**生产库前科复核**（该仓有测试自开默认库写生产数据的在册前科，故跑前跑后逐位比）：

| 时点 | `data/progress.db` sha256 前 8 位 | 字节数 | mtime |
|---|---|---|---|
| 全量跑前 | `cd2dbce4` | 122880 | 2026-09-25 20:49 |
| 全量跑后 | `cd2dbce4` | 122880 | 2026-09-25 20:49 |
| skip 定向复跑后 | `cd2dbce4` | 122880 | 2026-09-25 20:49 |

⇒ **逐位不变**，主证成立。侧车 `-wal` 恒 0 字节；`-shm` 只有 mtime 被推进（32768 字节不变），属 SQLite 打开库时的正常侧车触碰，非数据写入。
`git status --porcelain` 跑后仍为 **0 行**、HEAD 仍 `2665f0a`。

---

## 二、漂移表（对 384 基线 ＋ 对盘上真基线双列）

卷宗点名「384 passed 基线 2026-09-17」，但 `plan.md:33` **盘上现值早已不是 384**（见 §四否证）。
下表把口径链全列出来，避免只跟一个作废数字比：

| 口径点 | passed | skipped | 其它 | collected | commit | 日期 | 出处 |
|---|---|---|---|---|---|---|---|
| 376 | 376 | — | — | — | — | 09-17 | `plan.md:33` 口径链自述 |
| **384（卷宗点名）** | 384 | 7 | — | — | — | 09-18 | 卷宗锚点＋`learn-384-7-caliber-20260918.md` |
| 566 | 566 | — | — | — | `0564042` | 09-21 | `plan.md:33`，l922-03 |
| 597 | 597 | — | — | — | `1632f91` | 09-22 | `plan.md:33`，n922-10 |
| **622（盘上在册基线）** | 622 | 7 | 0 xfail | 629 | `a0ee9b9` | 09-22 | `plan.md:33`，l922-107 |
| **本班现值** | **1162** | **7** | **3 xfail** | **1172** | `2665f0a` | 09-27 | 本档 §一 |
| 漂移 vs 384 | **+778** | 0 | +3 | — | — | — | — |
| 漂移 vs 622（有效对比） | **+540** | **0（构成逐位相符）** | **+3** | **+543** | — | — | — |

**failed 漂移：0 → 0 ⇒ 零新增红。** 这是本单唯一需要「逐个归因」的槽位，实测为空集。

---

## 三、归因

### 3.1 新增失败（完成标准③要求的对象）：**空集**

`grep -cE "^FAILED|^ERROR"` on 全量输出 = **0**。无在途红、无环境红、无真回归可归因。

### 3.2 +540 增长的构成（红为 0，故增长才是需要解释的量）

| 归因 | 实测数 | 命令 |
|---|---|---|
| `tests/` 测试件数 71 → **114**（净新增 **43**，删除 0） | +43 件 | `git ls-tree -r --name-only <c> -- tests/ \| grep -c '^tests/test_.*\.py$'`；`git diff --name-status a0ee9b9 2665f0a -- tests/` |
| `def test_` 函数数 613 → **1046**（+433） | +433 | `grep -rhE "^[[:space:]]*def test_" tests/*.py \| wc -l`；同式在 `git grep` 上取 `a0ee9b9` |
| ├ 其中 43 份新件自带 | +413 | 逐件 `grep -c` 求和 |
| └ 18 份在改件净贡献 | +20 | 差额 |
| 参数化展开（collected 比函数数多出的部分） | +110 | 现值树内 `@pytest.mark.parametrize` 45 处——**此行为推断而非逐件复算**，本班未做 per-file collect-only |
| **3 枚 XFAIL 桩（= 在册未修缺陷，非新增红）** | +3 xfail | 三份文件全部 `a0ee9b9..2665f0a` 区间内新增（`git diff --name-status` 均为 `A`） |

3 枚 xfail 逐条（现值原文摘自全量输出尾段）：

1. `tests/test_paths_order_consistency.py::test_路径内milestone顺序与语言页顺序一致`
   —— 2 处 yaml 顺序 vs loader 字典序真倒置（python_advanced p4/p5），属规划域；清单见 `learn-paths-order-consistency-20260922.md`。
2. `tests/test_readme_version_gate.py::test_真README必须过check_readme`
   —— README 标题版本不含 0.6.5，桩内自述「**HEAD 长期红**，l923-25 遗留」。
3. `tests/test_sql_roworder_fragile.py::test_多行SQL题行序全部承重`
   —— 判分按 `expected_rows` 位置逐行比对 vs sqlite 无 top-level ORDER BY 不保证行序；
   桩内明写「命中集合清空即 XPASS＝本例转红，届时请删桩并回写普查档，勿放宽断言」。

⇒ **「failed=0」不等于「缺陷=0」**：三条真缺陷被 XFAIL 桩合法罩住。收班读漂移表时请把这三条与 +540 一起看。

### 3.3 「绿但零覆盖」形态提示（本仓现存实例）

`test_cpp_runner.py`／`test_r_runner.py` 是**整件 `pytestmark` skip**（各 16/13 行文件级标记），
非逐例 skip ⇒ 本机 C++ 与 R 两门 runner **全链路零执行**。这 7 条 skip 自 09-18 的「384/7」口径起就恒定存在，
**不是**漂移，但也不能因为"和基线一致"就当成覆盖到了。`learn-skipped-audit-20260916.md` 是在册的上一份复核。

---

## 四、锚点否证（按磁盘实况收窄，不判 failed）

| 卷宗锚点 | 盘上实况 | 处置 |
|---|---|---|
| `learning-system/plan.md:33`（注「plan-1952 批订正：384 passed 基线 2026-09-17」） | **行号在世、内容已被后续批次覆写**：`plan.md:33` 现记「**622 passed，7 skipped** …… 622/7 @ commit `a0ee9b9`，2026-09-22 01:23 复跑」，并自带口径链 376→384→566→597→622。384 只是链上第 2 环，**已非在册基线** | 有效对比对象改为 622 @ `a0ee9b9`；384 另列一行以满足"对比 384"的字面要求 |
| 锚点里的日期「2026-09-17」 | 384 口径在盘上是 **09-18**（`learn-384-7-caliber-20260918.md`），09-17 是 376 | 差一天，本档两个日期都保留标注 |
| `docs/insights/learning-metrics-recheck` 系 | 在世：`learning-metrics-recheck-20260917.md`（1 份，非"系"）；`learn-metrics-dual-20260918.md` 同域 | 引到即用 |
| brief §3a「`outbox/<id>.result.md` 全批命中 0 枚」 | 本单卷宗未点名 outbox 锚点，故不受该缺陷影响；对照件走 `done/` 与 `docs/insights/` | 无冲突 |

---

## 五、零改动声明（完成标准④）

- **零代码／零测试／零配置改动**：全程只 `pytest` 只读执行＋`git`/`grep`/`sha256sum` 取证；
  未 `add`、未 `commit`、未 `stash`、未 `checkout`、未 `restore`、未 `clean`、未 `push`、未联网、未装依赖。
- 唯一净新增文件＝本档本身（`docs/insights/l927-03-baseline.md`），属卷宗点名的产出位。
- 工作树：跑前后 `git status --porcelain` 均 0 行 → 本档落盘后为 1 行（未跟踪的本产出）。
- **本档不代登 insights 索引**：`docs/insights/learn-insights-index-20260918.md` 由主班收班统一代登
  （本仓有真闭合哨兵 `tests/test_insights_index_closure.py`，判据 A==B 且未列项为空；
  本班一份新档未登记 ⇒ 哨兵会在下次全量转红，**这是等主班代登的正常中间态，不是回归**）。
- 临时件全部落在 `D:\code\tmp\qoder-executor-20260927-1400-learn44\`（`pytest_full.txt`／`added.txt`／`newtests.txt`），
  仓根与 `tests/` 零临时件；本班自行清理。
