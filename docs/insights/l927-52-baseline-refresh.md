# learn 测试基线现值刷新（622 之后的一页现值卡）——l927-52，2026-09-29

> **卷宗**：`zcode-bridge/inbox/l927-52.task.md`（已随收口移入 `done/`）。上游依据＝
> `zcode-bridge/done/l922-107-plan-baseline-refresh.result.md` 遗留问题 1（基线档指针缺口：
> `learn-test-baseline-20260921.md` §六 的 597 已被 622 取代却无后继指针）＋锚点 `plan.md:33`。
> **本班性质**：只读位基线刷新班（shift `qoder-executor-20260929-0500-learn63`），零代码／零测试／零配置改动。
> ⚠️ **本单跑了全量 pytest（合法例外，三处留痕之一：本档）**：卷宗完成标准①「全量命令与计数」与②「与 622／384
> 两个历史口径对齐」的产物**本身就是全量读数**，定向跑无法出这两个数；同刻兄弟班 `psy102`／`quant70`／`kaoyan115`
> 在别的仓，learning 此刻只有本班一路（开工实测 `git status --porcelain` 行数 0、HEAD `31840db`），不存在互踩读数。
> 同路前两枚 l927-50／l927-51 **均未跑全量**（全量在路内只这一枚、只一次）。另留痕于 claim 行与本单 result。

## 一、全量命令与计数（完成标准①：先命令后数字）

```bash
cd /d/code/learning-system
sha256sum data/progress.db | cut -c1-8          # 跑前未单取（如实登记），开工 04:57 的 ls -l 已记 122880 字节／mtime 2026-09-25 20:49
PYTHONIOENCODING=utf-8 python -m pytest -q      # testpaths=tests（pytest.ini），addopts=-ra
sha256sum data/progress.db | cut -c1-8          # 跑后 → cd2dbce4
PYTHONIOENCODING=utf-8 python -m pytest tests --collect-only -q
```

```
2 failed, 1204 passed, 7 skipped, 2 xfailed in 116.55s (0:01:56)      rc=1
1215 tests collected in 1.19s
```

| 项 | 现值（2026-09-29 05:1x @ HEAD `31840db`） | 说明 |
|---|---|---|
| collected | **1215** | 自洽式 1204＋2＋7＋2 ＝ **1215** ✅ |
| passed | **1204**（工作树现读）／**1206**（在册树推算） | 2 条红全部来自本班自己两枚未登索引的产出件（见 §四），主班代登索引行后自动清；**推算值 1206 才是可对外引用的现值** |
| failed | **2**（均属本班产出中间态）／**0**（HEAD 干净树） | 归因逐条见 §四，非回归 |
| skipped | **7** | 与 09-18「384/7」起恒定的同一族（cpp 4＋r 3），行号零漂；现值复核与解除配方见 `docs/insights/l927-51-skip7-handoff.md` |
| xfailed | **2** | `test_sql_roworder_fragile.py::test_多行SQL题行序全部承重`＋`test_paths_order_consistency.py::test_路径内milestone顺序与语言页顺序一致`（两枚 strict 桩现役在世，本班未碰）；比 l927-03 的 3 少 1，因 `ede1b76`（l927-46/47）撤掉 README 版本门禁那枚 xfail 桩 |
| 耗时 | 116.55 s | **不并作性能结论**：本次为零并发单路；l927-03 的 152.82s 是多班并发负载下取的 |
| 生产库 | `data/progress.db` sha256 前 8 位 **`cd2dbce4`**＝与 l927-03 在册值逐字相同；`-wal` 0 字节 | ⇒ 全量跑未写生产库（`b8cc72e`「测试态禁开默认生产库」在册生效） |
| 工作树 | 跑后 `git status --porcelain` ＝ 2 行（本班 l927-50／51 两枚未跟踪产出件），HEAD 未变 | `git add` 0 次 |
| 规模 | `tests/test_*.py` **117** 个文件全部有采集；`^\s*def test_` 函数数 **1089** | 同式回溯：`2665f0a`＝114 件／1046 函数，`a0ee9b9`＝71 件／613 函数 |

## 二、口径对齐表（完成标准②：622／384 及链上各点）

| 口径 | passed | skipped | xfailed | collected | commit | 日期 | 出处 | 现役判定 |
|---|---:|---:|---:|---:|---|---|---|---|
| 376 | 376 | 7 | — | — | — | 09-17 | `learn-insights-intake-20260917.md` 系 | 史 |
| **384**（卷宗点名） | 384 | 7 | 0 | 391 | — | 09-18 | `learn-384-7-caliber-20260918.md`＋`plan.md:33` 旧值（plan-1952 批口径） | 🔴 **已非在册基线**，只是链上第 2 环；卷宗锚点写「plan.md:33（384 基线…）」的括注**盘上已不成立**（:33 现为 622，见 §三-D） |
| 566 | 566 | 7 | 0 | 573 | `0564042` | 09-21 | l922-03（`learn-test-baseline-20260921.md` §一） | 史 |
| 597 | 597 | 7 | 0 | 604 | `1632f91` | 09-22 | n922-10（同档 §六） | 史（§六 无后继指针＝l922-107 遗留 1，本档补建议文本 §五-2） |
| **622**（在册对外口径） | 622 | 7 | 0 | 629 | `a0ee9b9` | 09-22 01:23 | l922-107（`plan.md:33` 现值＋`learn-plan-baseline-refresh-20260922.md`） | ⚠️ 仍是 `plan.md:33` 的在册数字，**但已被 09-27 与今日两次实测越过** |
| 1162 | 1162 | 7 | 3 | 1172 | `2665f0a` | 09-27 | l927-03（`l927-03-baseline.md`，并发时点取数） | 史（最近一次在册复测） |
| **1206 / 1215** | **1206** | 7 | 2 | **1215** | `31840db` | **09-29 05:1x** | **本档（l927-52）** | ✅ **现役现值**，对外请写「1206 passed / 7 skipped / 2 xfailed（1215 collected）@ `31840db`」 |

## 三、差异归因（数字为什么对不上，逐段闭合）

**A. 622 → 1162（＋540 passed）**：本档不复算，直接引 l927-03 §3.2 的分解（`tests/` 文件 71→114、
`def test_` 613→1046、参数化展开＋110、XFAIL 新增 3）。该档是全仓最近一次在册复测，口径与本档同为
`python -m pytest tests -q`，可直接续接。

**B. 1162 → 1206（＋44 passed；collected 1172 → 1215，＋43）**：`2665f0a..31840db` 区间只有 8 枚提交触及 `tests/`，
逐枚取净增 `def test_`（`git show --unified=0 <h> -- tests/` 加／减计数差）：

| commit | 时刻 | 主旨（涉及测试面的部分） | 净增 def |
|---|---|---|---:|
| `4309041` | 09-28 11:25 | l927-13 回填去重双键幂等＋l927-16 越闸回退只留材料 | +9 |
| `22a5325` | 09-28 12:38 | l927-19/29/32 三单收口 | +2 |
| `e9a1606` | 09-28 13:16 | l927-37/40 曝光写序与变体生命周期第二终点 | +9 |
| `472d9e3` | 09-28 14:07 | l927-45 公开部署提示 AppTest 级证据（6 例） | +6 |
| `ede1b76` | 09-28 14:37 | **l927-46/47：README 版本门禁 xfail 桩撤除＋两例翻正更名** | +3 |
| `119c925` | 09-28 15:09 | l927-48 FakeStreamlit 四格入参落 calls＋l927-49 预检收口 | +5 |
| `5ea5995` | 09-28 16:16 | l927-55 导出缓存两分支钉桩（3 例） | +3 |
| `6323fde` | 09-28 16:51 | l927-56 变式题缓存 FIFO 断言面（19→25 例，纯追加 158/0） | +6 |
| **合计** | | | **+43** ＝ collected 1172→1215 的 **+43** ✅ 逐位闭合 |

恒等式核对：`passed ＋44 = def/采集 ＋43 ＋ xfailed→passed 挪位 1`；`collected ＋43 = passed ＋44 ＋ xfailed −1`。
⇒ 本区间**无参数化展开造成的差额**（与 l922-107 在同型区间的结论一致），`def test_` 口径可与采集口径互换。
⚠️ 该 8 枚提交里有 1 枚是**红→绿形状变化**（`ede1b76` 撤 xfail 桩）＝「xfailed 3→2」的全部来源，
**不是**缺陷被修好以外的东西：那枚桩自述「HEAD 长期红，l923-25 遗留」，l927-46 用「补裸版本串」把 README 真修好，
收口后翻正为普通 passed 例（复算：`pytest tests/test_readme_version_gate.py -q` → **5 passed** 无 xfail）。

**C. 为什么 384 不能与 622／现值直接相减**（口径差异四条，任一条都会让差值失真）：
① **passed vs collected 混用**：384 侧的 391 是「384＋7」的采集口径（v0.6.5 注记 commit `a66d604` 即用 391），
622 侧的 629 同理；直接拿 384 与 629 相减＝跨口径。
② **命令形态不同代**：384/566 用裸 `pytest -q`（走 `testpaths`），597/622 用 `pytest tests -q`；本档两条都复核过等价
（`--collect-only` 与全量都按 `testpaths=tests` 收口，现值 `pytest -q` ＝ 1215 采集）。
③ **xfail 集合不同代**：384／566／597／622 四代 xfailed 均为 0，09-27 是 3，今日是 2 ⇒ 同一份代码在三口径下
「passed 数」会差 1–3 例，比较必须先归一（本档对外值 1206 已把 2 xfailed 单列）。
④ **日期≠版本**：`plan.md:33` 与 l922-107 §声明都强调「基线绑 commit 不绑日期」（同日 09-22 基线走过 6 个值），
跨日引用必须带 commit 短号。

**D. 卷宗锚点漂移（按磁盘实况修正并留痕）**：卷宗背景写「`learning-system/plan.md:33`（384 基线为 plan-1952 批口径）」——
盘上 `:33` 现值为 **622 那一行**（384 早已被 l922-107 原地替换，本档 §二 已把 384 另列一行以满足「对比 384」的字面要求）。
同一漂移 l927-03 §四 已否证过一次，本档二次确认 ⇒ 台账若引「plan.md:33＝384」需加注。

## 四、本班工作树那 2 条红的归因（不是回归，别去消）

```
FAILED tests/test_insights_index_closure.py::test_闭合等式_A等于B_且C为空_且无重复
FAILED tests/test_insights_index_closure.py::test_新档漏登记必红_改名必红_有牙自检
E  AssertionError: A != B：磁盘 129 份 .md，索引表 127 条。
   未登记 ['docs/insights/l927-50-retake-true.md', 'docs/insights/l927-51-skip7-handoff.md']／表内多余 []
```

- 成因＝**本班自己（同路 l927-50／l927-51）新落两枚产出档、而 insights 索引件是主班独占写位**（纪律：执行班不代登）。
- 开工基线实测：`pytest tests/test_insights_index_closure.py -q` → **3 passed**、A=B=127；落两档后 → **2 failed, 1 passed**、A=129/B=127。
- 解除＝主班把 §五-3 的三条索引行与三枚产出档**同笔入库**；**未动桩、未放宽判据、未改索引件一字**。
- 因此 §一 的对外现值取 **1206 passed**（＝1204＋这 2 条在干净树上的应有态），并写死「2 failed 属中间态」——
  照 l927-03 §五 的同类先例（「这是等主班代登的正常中间态，不是回归」）。

## 五、建议追加／替换文本（实际追记由主班收班单点做；本单一字未改在册档）

> 卷宗产出只点名本档（`docs/insights/l927-52-baseline-refresh.md`），**未点名**要我直接改 `plan.md` 或基线档 ⇒ 按纪律不越位，只给文本。

1. **`plan.md:33` 的整行替换建议**（原地 1 行，口径链续到今日）：

   ```
   - 全量测试结果：**1206 passed，7 skipped，2 xfailed**（本机未安装 g++／Rscript，7 条恒 skip＝cpp runner 4＋r runner 3，非「7 条 R」；2 条 xfailed 为在册 strict 桩：SQL 行序／paths 顺序，属未修缺陷不是红）。实测命令：python -m pytest -q（testpaths=tests）；另 `--collect-only -q` → 1215 tests collected，1206+7+2=1215 自洽。口径：pytest（非 unittest discover）。**基线绑 commit 不绑日期**：1206/7/2 @ commit `31840db`，2026-09-29 05:1x 复跑、工作树除两枚待登记 insights 档外 clean。口径链：376（9/17）→ 384（9/18）→ 566（9/21 @0564042）→ 597（9/22 @1632f91）→ 622（9/22 @a0ee9b9，l922-107）→ 1162（9/27 @2665f0a，l927-03）→ **1206**（9/29 @31840db，l927-52）；1162→1206 的 +43/+44 逐枚归因见 `docs/insights/l927-52-baseline-refresh.md` §三-B。
   ```

2. **`docs/insights/learn-test-baseline-20260921.md` §六 之后的追加建议**（闭合 l922-107 遗留 1 的指针缺口；纯追加、不改正文一字）：

   ```
   ### §六 之后的后继指针（l927-52，2026-09-29 追加）
   - 本节 597 @ `1632f91` 之后，同日 learn3 复跑为 622 @ `a0ee9b9`（见 `plan.md:33` 与 `learn-plan-baseline-refresh-20260922.md`），
     09-27 复测 1162 @ `2665f0a`（`l927-03-baseline.md`），**现役现值 1206 passed / 7 skipped / 2 xfailed / 1215 collected @ `31840db`（2026-09-29，`l927-52-baseline-refresh.md`）**。
   - 例行取数请看 `l927-52-baseline-refresh.md` §一；本档 §二 主题归类与 §四 缺口清单仍有效（缺口 1「7 例恒 skip」的
     环境侧订正见 `l927-51-skip7-handoff.md`：cpp 侧不是没装编译器，而是 `D:\tools\mingw64\bin` 少 `g++.exe`/`ld.exe` 两个别名文件）。
   ```

3. **索引行建议文本**（三条同笔；learning 索引件由主班单点写，本班未动一字）：

   ```
   | docs/insights/l927-50-retake-true.md | 20260929 | （文本见该档 §六-1） | 待人工（裁决材料选案未拍） | 0 |
   | docs/insights/l927-51-skip7-handoff.md | 20260929 | （文本见该档 §五-1） | 待人工（装机须放行） | 0 |
   | docs/insights/l927-52-baseline-refresh.md | 20260929 | 基线一页现值刷新（本单跑了全量，产物＝全量读数属合法例外）：现值 1206 passed/7 skipped/2 xfailed＝1215 collected @ 31840db，116.55s 零并发，工作树实读 2 failed 全因本班两枚未登索引产出档（中间态非回归）；1162→1206 按 8 枚触及 tests 的提交逐枚净增 def 求和 ＋43 与采集差逐位闭合，另 1 例为 ede1b76 撤 README xfail 桩使 xfailed 3→2 的挪位；口径差异四条归因（passed/collected 混用、命令形态、xfail 不同代、基线绑 commit 不绑日期）；否证卷宗锚点 plan.md:33＝384（盘上现为 622 那行，l927-03 已否证过一次本班二次确认）；plan.md 与基线档 §六 只给建议文本未自改（l927-52，2026-09-29） | 待主班代登索引＋代提交 | 0 |
   ```

## 六、待人工 ＋ 必须同笔入库的件

1. **必须同笔（三枚一批）**：`docs/insights/l927-50-retake-true.md`＋`l927-51-skip7-handoff.md`＋`l927-52-baseline-refresh.md`
   ＋ `docs/insights/learn-insights-index-20260918.md` 的三条索引行。少一条 ⇒ `test_insights_index_closure.py` 红（实测 2 failed）。
   l927-45/46/47 等已入库档的索引行主班此前已代登（现读 B=127 含它们），本次只需追加三行。
2. **待人工①**：是否按 §五-1 改写 `plan.md:33`（在册对外口径落后两代：622 → 1206）。
3. **待人工②**：是否按 §五-2 给 `learn-test-baseline-20260921.md` §六 补后继指针（l922-107 遗留 1 至今未闭）。
4. **待人工③**：台账加注本单否证的卷宗锚点（`plan.md:33` 现为 622 而非 384）。
5. **不做清单（纪律）**：未装 g++/Rscript、未撤 strict-XFAIL 桩、未放宽任何判据、未改生产码／测试码／`plan.md`／索引件、
   未 `git add`／`commit`／`push`、未联网。
6. **探针与留痕**（`tmp/` 已 gitignore，未删未提交）：`D:\code\learning-system\tmp\l927-52\`＝
   `full.txt`（全量输出原文＋`PYTEST_RC=1`）、`collect_per_file.txt`（117 个文件的逐件采集数，供后续班做逐件差值对账）。

## 七、复算配方

```bash
cd D:/code/learning-system
PYTHONIOENCODING=utf-8 python -m pytest -q                                   # 期望 1206 passed/7 skipped/2 xfailed（索引代登后）
PYTHONIOENCODING=utf-8 python -m pytest tests --collect-only -q | tail -1     # 1215 tests collected
sha256sum data/progress.db | cut -c1-8                                       # cd2dbce4（与 l927-03 同值＝跑测未写生产库）
git ls-tree -r --name-only HEAD -- tests/ | grep -c '^tests/test_.*\.py$'     # 117
grep -rhE '^[[:space:]]*def test_' tests/*.py | wc -l                         # 1089；同式取 2665f0a=1046、a0ee9b9=613
for h in 4309041 22a5325 e9a1606 472d9e3 ede1b76 119c925 5ea5995 6323fde; do   # §三-B 逐枚净增
  echo "$h $(( $(git show --unified=0 $h -- tests/ | grep -c '^+.*def test_') - $(git show --unified=0 $h -- tests/ | grep -c '^-.*def test_') ))"; done
PYTHONIOENCODING=utf-8 python -m pytest tests/test_cpp_runner.py tests/test_r_runner.py -rs -q   # 7 skipped 恒定面（解除配方见 l927-51 档）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_readme_version_gate.py -q -rx                  # 5 passed，xfail 桩已撤＝xfailed 3→2 的来源
PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q                  # 代登索引前回 2 failed，代登后 3 passed
```
