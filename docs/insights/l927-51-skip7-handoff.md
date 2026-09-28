# 七例恒 skip 的 g++/Rscript 环境缺口：现值复核与日间移交清单（l927-51，零安装 · 零联网 · 零越界写）

> **卷宗**：`zcode-bridge/inbox/l927-51.task.md`（已随收口移入 `done/`）。上游依据＝
> `zcode-bridge/done/l922-03-learn-test-baseline.result.md` 遗留问题 1：「7 例恒 skip 的解除属日间动作
> （装 g++/Rscript 后复跑，期望 573 collected 全 passed）——本单按禁止装依赖只做登记」。
> **本班性质**：只读位登记班（shift `qoder-executor-20260929-0500-learn63`，2026-09-29 05:0x 全部读数现取，
> 仓 HEAD `31840db`、开工时 `git status --porcelain` 行数 0）。**未装任何东西、未联网、未写 cwd 之外的路径。**
> 🔴 **复核结论与锚点有两处实质差别**（都实测）：① 锚点的期望值「573 collected」是 09-21 时点，现值口径归同路 l927-52；
> ② **cpp 侧缺的不是「没装 g++」，而是「已解出的 mingw 发行版里少了两个文件名」**——这一条把日间动作从「下载重装」降级成「补两个别名副本」，见 §三。

## 一、锚点复核（先命令后数字）

| # | 前提 | 现取读数 | 命令（cwd `D:/code/learning-system`） | 判定 |
|---|---|---|---|---|
| 1 | 7 例仍在恒 skip | **`7 skipped in 0.06s`**（零解除） | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_cpp_runner.py tests/test_r_runner.py -rs -q` | ✅ 缺口仍在 |
| 2 | skip 逐条归属与行号 | `test_cpp_runner.py:16/:27/:34/:44`＝g++ not available（4 条）＋ `test_r_runner.py:13/:19/:25`＝Rscript not available（3 条） | 同上（`-rs` 逐条原文，留痕 `tmp/l927-51/skip7.txt`） | ✅ **行号与 l922-03 逐字一致，零漂移** |
| 3 | 门是模块级 `pytestmark`（不是逐例） | `test_cpp_runner.py:11`、`test_r_runner.py:8` 各一只 `pytestmark = pytest.mark.skipif(...)` | `grep -n "pytestmark" tests/test_cpp_runner.py tests/test_r_runner.py` | ✅ 形态未变（连带面见 §三-2） |
| 4 | 判据就是生产解析函数 | cpp 门调 `CppRunner()._resolve_compiler()`、r 门调 `RRunner()._resolve_rscript()`；两函数**先 `shutil.which` 再 `fallback_paths` 再 `fallback_glob`** | `sed -n '1,12p' tests/test_cpp_runner.py`；`sed -n '26,70p' core/runners/cpp_runner.py`；`sed -n '17,46p' core/runners/r_runner.py` | ✅ 复核必须按三层口径查，只查 PATH 会误判 |
| 5 | 生产解析三层全空 | `_resolve_compiler()` → **None**；`_resolve_rscript()` → **None**；`which('g++')`/`which('Rscript')` → None；`fallback_paths` 命中 `[]`；两侧 `fallback_glob` 命中 `[]`；`R_HOME` 未设 | `PYTHONIOENCODING=utf-8 python -c "<见 §七-2>"`（留痕 `tmp/l927-51/env_probe.txt`） | ✅ 七例 skip 的**直接原因坐实** |
| 6 | 🔴 盘上其实有 mingw，且**缺的是文件名不是目录** | `D:\tools\mingw64` 存在＝winlibs `gcc-16.1.0-mingw-w64ucrt-14.0.0-r2`（`version_info.txt` 原文）；`bin` 161 条目 / 82 个 exe，**含 `c++.exe`、`gcc.exe`、`as.exe`、`ld.bfd.exe`，独缺 `g++.exe` 与 `ld.exe`**（`x86_64-w64-mingw32-g++.exe`/`-ld.exe` 同缺）；`libexec/gcc/x86_64-w64-mingw32/16.1.0/cc1plus.exe` 在位 | `PYTHONIOENCODING=utf-8 python -c "<见 §七-3>"` | ✅ 缺口性质＝**别名文件缺位**，不是「编译器不存在」 |
| 7 | 只加 PATH 不补名会怎样（对照实测） | `PATH` 追加 `D:\tools\mingw64\bin` 后真驱动报 `collect2.exe: fatal error: cannot find 'ld'`，rc=1（`as` 这一步已经过了：`as.exe --version` rc=0，Binutils 2.46.0） | `c++.exe --version`／`as.exe --version`／`c++.exe -std=c++17 -O0 -Wall main.cpp -o main.exe`（见 §七-4） | ✅ **第二道 fatal＝ld.exe 名缺位** ⇒ 修复必须两件事一起 |
| 8 | R 侧无任何可模拟物 | 常见安装位全 NOT-EXIST：`C:\Program Files\R`、`D:\Program Files\R`、`D:\tools\R*`、`%LOCALAPPDATA%\Programs\R`、`D:\R`、`C:\R`；glob 搜 `Rscript.exe` 零命中 | `python -c "os.path.isdir(...)"` 逐路径（见 §七-2 同一条命令） | ✅ R 侧＝真缺件，须装机 |
| 9 | 仓内既有安装脚本（只读，**本班未跑**） | `D:\tools\install_R.bat`（421 B）＝`winget install -e --id RProject.R`＋UAC 弹窗；`D:\tools\install_mingw.ps1`（2925 B）＝GitHub API 取 winlibs 最新 release 再下载 zip 解到 `D:\tools` ⇒ **两者都要联网**，正是本单禁止事项，故只登记为日间动作入口 | `head -12 /d/tools/install_R.bat`；`head -18 /d/tools/install_mingw.ps1` | ⚠ 脚本可用但属「下载依赖」面 ⇒ 交人工 |

## 二、七例的成分：真需工具的 5 例 ＋ 被模块级门连带的 2 例

把两枚测试件在 `tmp/` 里复制一份、**删掉模块级 `pytestmark` 行**（原件一字未动）后实跑：

```
$ PYTHONIOENCODING=utf-8 python -m pytest tmp/l927-51/noskip_test_cpp_runner.py tmp/l927-51/noskip_test_r_runner.py -q --no-header -rs
5 failed, 2 passed in 0.13s        # 留痕 tmp/l927-51/noskip-run.log
```

| 用例 | 现值 | 装工具前能否跑？ | 依据 |
|---|---|---|---|
| `test_cpp_runner.py::test_hello_world` | skip | ❌ 需 g++ 真编译 | 走 `CppRunner().run()` |
| `::test_compile_error` | skip | ❌ 需 g++ | 断 `error_kind == "compile"`（无编译器会得到 `sandbox`，实测见 §七-5） |
| `::test_stdin_passed` | skip | ❌ 需 g++ | cin/cout 真跑 |
| `::test_sandbox_when_no_gpp` | skip | ✅ **不需要任何工具**（它自己 monkeypatch `which→None`＋清空 `fallback_paths`/`fallback_glob`，断 sandbox） | noskip 副本实跑 **passed** |
| `test_r_runner.py::test_hello_world` | skip | ❌ 需 Rscript | — |
| `::test_runtime_error` | skip | ❌ 需 Rscript（无 R 时实跑得到 `sandbox`≠`runtime`） | noskip 副本 `AssertionError: assert 'sandbox' == 'runtime'` |
| `::test_sandbox_when_no_rscript` | skip | ✅ **不需要任何工具**（同型 monkeypatch） | noskip 副本实跑 **passed** |

⇒ **恒 skip 的 7 例里只有 5 例真被环境卡住，另外 2 例是模块级 `pytestmark` 的连带牺牲品**（本机 R/g++ 都缺，这两例在本机从未跑过一次）。
两条出口（**都属写单，本班不动桩、不放宽任何判据**）：
① 把两只 sandbox 例移出 `pytestmark` 作用域（挪进类里或用 `skipif` 逐例挂），可在**零安装**下当场回收 2 例真跑面；
② 保持现状，等日间装机后 7 例一起解除。取舍属人工，本档只把代价写清。

## 三、修复配方实测：cpp 侧「补两个文件名」即可，无需下载

在 cwd 内的沙盒 `tmp/l927-51/fakebin/` 放两个**本地副本**（`c++.exe`→`g++.exe`、`ld.bfd.exe`→`ld.exe`，
纯 `shutil.copy2`，零下载、零系统改动、零 PATH 注册），再用插件把「修后态」模拟给真测试件跑：

```
$ PYTHONIOENCODING=utf-8 python tmp/l927-51/cpp_e2e_probe.py            # 留痕 tmp/l927-51/e2e_probe.txt
which(g++) 在 PATH 含 fakebin 时 = ...\fakebin\g++.EXE                   # 解析层会翻正
test_hello_world 断言面：ok = True | error_kind = None | exit = 0 | stdout = 'Hello, World!\r\n'  ⇒ ✅ 会过
test_compile_error 断言面：ok = False | error_kind = compile            ⇒ ✅ 会过

$ PYTHONPATH="D:/code/learning-system/tmp/l927-51" PYTHONIOENCODING=utf-8 python -m pytest -p repair_plugin --no-header -q tests/test_cpp_runner.py
4 passed in 2.40s          # 留痕 tmp/l927-51/repair-run.log —— 真测试件、原文件、修后态读数
（对照未挂插件：4 skipped）
```

⇒ **结论（实测支撑）**：`CppRunner` 的解析顺序是 `which → fallback_paths → fallback_glob`，而
`fallback_paths[0]` 逐字就是 `D:\tools\mingw64\bin\g++.exe` ⇒ 日间只要在该目录里补出 `g++.exe`（`c++.exe` 的副本）
与 `ld.exe`（`ld.bfd.exe` 的副本），**不必改 PATH、不必重启、不必下载**，4 例当场解除。
runner 编译子进程的受限 PATH＝「编译器自己所在目录＋System32」（`cpp_runner.py:93-97`），
两副本落在同一 bin ⇒ `collect2` 找得到 `ld`，这条已用 `-p repair_plugin` 的真件 4 passed 验证。

## 四、日间移交清单（完成标准②：安装项 / 复跑命令 / 期望值）

| # | 项 | 动作 | 复跑命令（cwd `D:/code/learning-system`） | 期望读数 |
|---|---|---|---|---|
| 1 | **cpp 侧最小修复（推荐先做，零联网）** | 在 `D:\tools\mingw64\bin` 内补两个别名文件：`copy c++.exe g++.exe`、`copy ld.bfd.exe ld.exe`（winlibs 正常发布形态即含这两个别名，本机这套少了） | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_cpp_runner.py -rs -q` | **`4 passed`**，`SKIPPED` 行归零；再跑 §一-5 的解析命令应得 `_resolve_compiler() = D:\tools\mingw64\bin\g++.exe` |
| 2 | cpp 侧备选（若怀疑 bin 本体不完整） | 跑仓内既有脚本 `powershell -ExecutionPolicy Bypass -File D:\tools\install_mingw.ps1`（**要联网＋UAC**，会重下 winlibs 到 `D:\tools`） | 同 #1 | 同 #1 |
| 3 | **R 侧修复（只能装，无本地可补物）** | `D:\tools\install_R.bat`（`winget install -e --id RProject.R`，要联网＋UAC）；装完 R 会落 `C:\Program Files\R\R-x.y\bin\Rscript.exe`，正是 `RRunner.fallback_glob[0]` 的通配范围 ⇒ **不必手动配 PATH** | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_r_runner.py -rs -q` | **`3 passed`**，`SKIPPED` 归零；解析命令应得 `_resolve_rscript()` 非 None |
| 4 | 两案都修完的总账 | — | `PYTHONIOENCODING=utf-8 python -m pytest -q`（全量，本机约 130 s 级） | **`skipped` 由现值 7 → 0、`passed` 净 ＋7、`collected` 不变**；锚点里的「573 collected 全 passed」是 09-21 时点数字，**别拿它当期望值**，现值见同路 `docs/insights/l927-52-baseline-refresh.md`（基线档） |
| 5 | 只修 cpp 不修 R 的中间态 | — | 同 #4 | `skipped 7 → 3`、`passed ＋4`（r 侧 3 例仍 skip） |
| 6 | 只回收 sandbox 连带例（零安装出口） | 把 `test_sandbox_when_no_gpp`／`test_sandbox_when_no_rscript` 移出模块级 `pytestmark`（**需改测试件 ⇒ 另派写单，本单未做**） | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_cpp_runner.py tests/test_r_runner.py -rs -q` | `5 skipped, 2 passed`（本档 §二 已用 tmp 副本实跑出这 2 例现在就能绿） |
| 7 | 回滚 | 删掉 #1 的两个副本即可（`del D:\tools\mingw64\bin\g++.exe ld.exe`），解析层回 None、门自动合上 | 同 #1 | 回 `4 skipped` |
| 8 | 修后必查的连表面（**提醒别只数 7**） | 装 R/g++ 后这几处会出现**新的真跑面**，历史读数全部作废需刷新：`tests/test_mark_r_judge_plain.py:592`（pre-D6 备份不在盘上才 skip）、`tests/test_content_census_r.py:170`（R_SCHEMA_VERSION 放宽 skip）、`tests/test_import_dry_run.py:203`（生产库不在盘上才 skip） | 修后跑全量并 `-ra`（`pytest.ini` 的 `addopts=-ra` 已默认带） | 逐条 `SKIPPED` 归属重新登记；本班未跑全量（全量读数归 l927-52） |
| 9 | 本机既有验证脚本（可用，未跑） | `D:\tools\verify_cpp_phase4.py`（10121 B）／`D:\tools\verify_r_phase4.py`（8995 B）／`D:\tools\test_lm.R`（240 B）——修好工具链后可作二次确认 | 日间自行决定 | 不在本单判据内，只登记 |

**移交时须一并说明的三条纪律**：① 本班零安装零联网，上面 #2/#3 都要人工放行；
② 装完请**同时**刷新测试基线档（`learn-test-baseline-20260921.md` §六 的 597／622 口径由 l927-52 处理）；
③ 禁止用「把 skip 断言改成通过」这类放宽——7 例的解除只能来自环境或 §二-6 的挂具挪位。

## 五、必须同笔入库的件 ＋ 待人工

1. **必须同笔**：本产出件 `docs/insights/l927-51-skip7-handoff.md` ＋ `docs/insights/learn-insights-index-20260918.md` 索引行
   （落盘前哨兵实测 `3 passed`／A=B=127；本班三枚产出件依次落盘后 A=128…130、B=127 ⇒ `test_insights_index_closure.py`
   红两格，见 l927-50 result 证据末条）。**索引件本班未动一字**（主班独占件）。建议索引行文本：

   ```
   | docs/insights/l927-51-skip7-handoff.md | 20260929 | 七例恒 skip 现值复核＋日间移交清单（零安装零联网）：7 skipped 行号逐字未漂（cpp :16/:27/:34/:44＋r :13/:19/:25）；🔴 定性订正——cpp 侧不是没装编译器而是 D:\tools\mingw64\bin 少 g++.exe/ld.exe 两个别名文件（winlibs 16.1.0 本体在位，as 可用、collect2 只报 cannot find 'ld'），沙盒补名＋真件挂插件实测 4 passed／对照组 4 skipped ⇒ 最小日间动作可零下载；R 侧盘上无件须 winget 装；另测出 7 例里 2 例系模块级 pytestmark 连带（noskip 副本 5 failed 2 passed），零安装出口属写单未动桩（l927-51，2026-09-29） | 待人工（装机须放行） | 0 |
   ```

2. **待人工①**：cpp 补名（§四-1，零联网）——越界写 `D:\tools` 且属安装面，本班不做。
3. **待人工②**：R 装机（§四-3，联网＋UAC）。
4. **待人工③**：§二 的 2 例连带牺牲品要不要在装机前先解（需动测试件 ⇒ 另派写单）。
5. **待人工④**：台账加注 `l922-03` 遗留 1 的「期望 573 collected 全 passed」——该期望绑 09-21 时点，现役不可当判据（现值归 l927-52）。
6. **本班探针残留**（`tmp/` 已 gitignore，未删未提交，供日间复跑）：`D:\code\learning-system\tmp\l927-51\`＝
   `env_probe.txt`、`cpp_e2e_probe.py`、`e2e_probe.txt`、`repair_plugin.py`、`repair-run.log`、
   `noskip_test_cpp_runner.py`、`noskip_test_r_runner.py`、`noskip-run.log`、`skip7.txt`、`fakebin\{g++.exe,ld.exe}`（两个副本，共约 4.3 MB，日间复跑后可删）。
   ⚠ 探针局限：`repair_plugin` 是**运行时模拟**（把 `which('g++')` 指到真驱动 `c++.exe`＋受限 PATH 追加 ld.exe 副本目录），
   不在 `D:\tools\mingw64\bin` 真落文件；主班复跑同源命令不算独立复算，独立读数请按 §四-1 真补名后跑 §四-1/#3 的命令。

## 六、复算配方（本档读数取数链）

```bash
cd D:/code/learning-system
# 1 现值七例＋逐条归属
PYTHONIOENCODING=utf-8 python -m pytest tests/test_cpp_runner.py tests/test_r_runner.py -rs -q
# 2 生产解析三层口径（skipif 用的就是这两个函数）
PYTHONIOENCODING=utf-8 python -c "
import shutil,glob,os
from core.runners.cpp_runner import CppRunner; from core.runners.r_runner import RRunner
print(CppRunner()._resolve_compiler(), RRunner()._resolve_rscript(), shutil.which('g++'), shutil.which('Rscript'))
print([p for p in CppRunner.fallback_paths if os.path.exists(p)])
print([m for pat in CppRunner.fallback_glob for m in glob.glob(pat)])
print([m for pat in RRunner.fallback_glob for m in glob.glob(pat)])"
# 3 bin 里到底少了什么
PYTHONIOENCODING=utf-8 python -c "
import os; b=r'D:\tools\mingw64\bin'; f=sorted(os.listdir(b))
print(len(f), [x for x in f if '+' in x], [x for x in f if x.startswith('ld')], (r'D:\tools\mingw64\bin\g++.exe' in f))"
# 4 驱动/汇编/链接三段体检
/d/tools/mingw64/bin/c++.exe --version | head -1
/d/tools/mingw64/bin/as.exe --version | head -1
PATH="/d/tools/mingw64/bin:$PATH" /d/tools/mingw64/bin/c++.exe -std=c++17 -O0 -Wall tmp/l927-51/build/main.cpp -o tmp/l927-51/build/main.exe   # 期望 collect2: cannot find 'ld'
# 5 连带面（tmp 副本去 pytestmark 后真跑）
PYTHONIOENCODING=utf-8 python -m pytest tmp/l927-51/noskip_test_cpp_runner.py tmp/l927-51/noskip_test_r_runner.py -q --no-header -rs
# 6 修后态（真测试件＋运行时模拟补名）
PYTHONPATH="D:/code/learning-system/tmp/l927-51" PYTHONIOENCODING=utf-8 python -m pytest -p repair_plugin --no-header -q tests/test_cpp_runner.py
# 7 索引闭合哨兵（本档落盘后预期红两格）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q
```
