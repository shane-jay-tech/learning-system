# learning RRunner._version_key 整路径抽数字：盘上普查＋错序用例对照＋收敛设计稿（l924-26，只出稿 · 零生产码改动）

> **卷宗**：`zcode-bridge/inbox/l924-26.task.md`（现址 `zcode-bridge/done/`）。产出面＝本档一份；`core/runners/` 零 diff（自证见 §四）。
> 🔴 **本档是设计稿，一律"建议案、未选案"**：三处需要落码的改动（两 runner 的 `_version_key`、两条在册夹具的期望、可选的 U3 行为变更）全部交人工裁决，执行手不代拍板。
> 取证探针在 gitignore 的 `tmp/l924-26/probe.py`（零写库、零起服务、零网络；`core/` 与 `tests/` 只读）。

## 〇、锚点与前提复核（卷宗每条前提都实测）

| 卷宗前提 | 实测读数 | 命令 | 判定 |
|---|---|---|---|
| `core/runners/r_runner.py:29` 为 `nums = _re.findall(r"\d+", path)` | 该行逐字为 `        nums = _re.findall(r"\d+", path)` | `sed -n '23,30p' core/runners/r_runner.py` | ✅ 行号零漂移 |
| `core/runners/r_runner.py:30` 为 `return tuple(int(n) for n in nums) or (0,)` | 逐字一致 | 同上 | ✅ 零漂移 |
| `core/runners/cpp_runner.py:46` 挂 ⚠️ 自认同款 | `:46` = `    # ⚠️ 排序键沿用 RRunner._version_key（整路径抽数字）⇒ 跨根目录比较时数字可能来自`，`:47` 续「msys64/mingw64 这类架构后缀而非版本号，该局限与 R 侧同源，**未在本单扩大范围修**」 | `sed -n '43,47p' core/runners/cpp_runner.py` | ✅ 成立（cpp 侧由 l923-31 自己留了口子） |
| 排序键只有两处消费者 | `rg -n "_version_key" --glob '!docs/**' .` → `r_runner.py:24/:41`、`cpp_runner.py:46/:57`（注释 1 处）＋ 整路径 findall 全仓仅 `r_runner.py:29`／`cpp_runner.py:61` 两处 | 见左 | ✅ 收敛面就是这两个函数，无第三处 |
| 卷宗示例 `D:\2026\tools\R\R-4.3 → (2026,4,3)` 恒胜 `C:\Program Files\R\R-4.4.1 → (4,4,1)` | 探针 U1 复算：现 key 分别 `(2026, 4, 3)` 与 `(4, 4, 1)`，`(2026,4,3) > (4,4,1)` ⇒ 真错序 | `PYTHONIOENCODING=utf-8 python tmp/l924-26/probe.py` | ✅ 示例成立 |
| 🔴 **否证（本单最重要的一条）**：卷宗要求"盘上四条 fallback_glob 实测 glob 结果留档"，语气预设盘上有 R-* 可比 | **四条 pattern 全为 0 命中**，且全盘浅层扫描无任何 `R-x.y` 目录、`where Rscript` 亦无 ⇒ 本机根本没装 R，**"错序"在本机不可能自然复现**，只剩构造用例（§二的 10 组全部是构造的） | 见 §一 的 4 条命令 | ❌ 前提不成立 ⇒ 完成标准①按实况收窄为"四 pattern 逐条留档命中/空"，不判 failed |
| ⚠ 附带发现（越界，未修）：cpp 侧同样 0 命中，但原因不是"没装" | `D:\tools\mingw64\bin` **在盘**（161 个文件，`install_mingw.ps1:59-60` 解出来的 winlibs gcc-13.2.0），其中有 `gcc.exe`/`c++.exe`/`gcc-ar.exe` 却**没有 `g++.exe`** ⇒ 五条 cpp pattern 全空、`shutil.which('g++')` 亦 None | `ls /d/tools/mingw64/bin \| grep -iE "^g(\+\+\|cc)"` | 只登记进 §五 遗留，不在本单动 |

## 一、盘上实测（完成标准①：四 pattern 逐条留档）

仓库根 `D:/code/learning-system` 执行：

```bash
PYTHONIOENCODING=utf-8 python -c "
import glob
from core.runners.r_runner import RRunner
from core.runners.cpp_runner import CppRunner
for i,pat in enumerate(RRunner.fallback_glob,1): print(i,repr(pat),'->',len(glob.glob(pat)),sorted(glob.glob(pat)))
for i,pat in enumerate(CppRunner.fallback_glob,1): print(i,repr(pat),'->',len(glob.glob(pat)),sorted(glob.glob(pat)))
"
```

| # | RRunner.fallback_glob pattern | 命中 |
|---|---|---|
| 1 | `C:\Program Files\R\R-*\bin\Rscript.exe` | **0** |
| 2 | `C:\Program Files\R\R-*\bin\x64\Rscript.exe` | **0** |
| 3 | `D:\Program Files\R\R-*\bin\Rscript.exe` | **0** |
| 4 | `D:\tools\R\R-*\bin\Rscript.exe` | **0** |

| # | CppRunner.fallback_glob pattern | 命中 |
|---|---|---|
| 1 | `D:\tools\mingw*\bin\g++.exe` | **0**（`D:\tools\mingw64` 存在但缺 `g++.exe`） |
| 2 | `D:\tools\gcc*\bin\g++.exe` | **0**（目录不存在） |
| 3 | `C:\msys64\mingw*\bin\g++.exe` | **0**（`C:\msys64` 不存在） |
| 4 | `C:\mingw*\bin\g++.exe` | **0** |
| 5 | `C:\TDM-GCC-*\bin\g++.exe` | **0** |

补充三条独立佐证（同一命令块可复算）：

| 取证 | 读数 |
|---|---|
| `shutil.which('Rscript')` / `shutil.which('g++')` | 均 `None` ⇒ 走哪条兜底都无从比较 |
| `RRunner()._resolve_rscript()` / `CppRunner()._resolve_compiler()` | 均 `None` ⇒ `run()` 直接落 `error_kind="sandbox"` 提示"未检测到 Rscript" |
| `find /c /d -maxdepth 3 -iname "R-?.*"`（只读、20 s 上限） | 空输出，rc=0；`ls -d /c/Program Files/R` 亦 No such file |
| `%LOCALAPPDATA%\R\win-library` | 不存在 ⇒ `r_runner.py:80-92` 的 R_LIBS_USER 分支本机整段不执行 |

⇒ **结论口径**：本单的错序证据全部是**构造用例 + 纯函数复算**（无副作用、可逐行复算），不是盘上现网事故；现网该缺陷在"装了多个 R/多发行版 mingw"的机器上才会显形。

## 二、错序用例对照表（完成标准②：10 组，两法结论逐组可复算）

复算命令（零副作用）：

```bash
cd /d/code/learning-system && PYTHONIOENCODING=utf-8 python tmp/l924-26/probe.py
```

- **现 key** ＝ 逐字照抄 `r_runner.py:29-30`（＝`cpp_runner.py:61-62`，两份实现同型）。
- **修正 key** ＝ §三 建议案的三层实现（同一探针内已实现，非伪码）。
- "现选/修正选"的 ★ ＝ 按现实现的选法模拟：外层按 `fallback_glob` 序、内层按 glob 返回序遍历，`if best_key is None or key > best_key`（**严格 `>` ⇒ 平手保留先见者**，`r_runner.py:42`）。
- 「期望」列指**版本更新的那条路径**（人工判定，非探针自证）。

| 用例 | 族 | 路径 | 现 key | 修正 key | 现选 | 修正选 | 期望 | 现法 | 修正法 |
|---|---|---|---|---|---|---|---|---|---|
| U1｜跨根目录前缀数字恒胜（卷宗点名） | R | `C:\Program Files\R\R-4.4.1\bin\Rscript.exe` | (4, 4, 1) | (4, 4, 1) | | ★ | 路径A | **错序** | 正 |
| U1 | | `D:\2026\tools\R\R-4.3\bin\Rscript.exe` | (2026, 4, 3) | (4, 3) | ★ | | 路径A | **错序** | 正 |
| U2｜数值序 vs 字典序（现实现的立身之本） | R | `C:\Program Files\R\R-4.10.0\bin\Rscript.exe` | (4, 10, 0) | (4, 10, 0) | ★ | ★ | 路径A | 正 | 正 |
| U2 | | `C:\Program Files\R\R-4.9.0\bin\Rscript.exe` | (4, 9, 0) | (4, 9, 0) | | | 路径A | 正 | 正 |
| U3｜同版本双 arch ⇒ **修正后所选文件会变** | R | `C:\Program Files\R\R-4.4.1\bin\Rscript.exe` | (4, 4, 1) | (4, 4, 1) | | ★ | 平手即可 | 正 | 正 |
| U3 | | `C:\Program Files\R\R-4.4.1\bin\x64\Rscript.exe` | (4, 4, 1, 64) | (4, 4, 1) | ★ | | 平手即可 | 正 | 正 |
| U4｜含空格＋数字的目录段混入 | R | `D:\My Documents 2019\R\R-4.3.0\bin\Rscript.exe` | (2019, 4, 3, 0) | (4, 3, 0) | ★ | | 路径B | **错序** | 正 |
| U4 | | `C:\Program Files\R\R-4.4.1\bin\Rscript.exe` | (4, 4, 1) | (4, 4, 1) | | ★ | 路径B | **错序** | 正 |
| U5｜架构段 `(x86)` 的 86 混入 | R | `C:\Program Files (x86)\R\R-4.3.0\bin\Rscript.exe` | (86, 4, 3, 0) | (4, 3, 0) | ★ | | 路径B | **错序** | 正 |
| U5 | | `C:\Program Files\R\R-4.4.1\bin\Rscript.exe` | (4, 4, 1) | (4, 4, 1) | | ★ | 路径B | **错序** | 正 |
| U6｜在册回归夹具（裸版本号目录，无 `R-` 前缀） | R | `C:\R\4.9\Rscript.exe` | (4, 9) | (4, 9) | | | 路径B | 正 | 正 |
| U6 | | `C:\R\4.10\Rscript.exe` | (4, 10) | (4, 10) | ★ | ★ | 路径B | 正 | 正 |
| U7｜arch 段 64 顶掉 patch 位 | R | `C:\Program Files\R\R-4.4\bin\x64\Rscript.exe` | (4, 4, 64) | (4, 4) | ★ | | 路径B | **错序** | 正 |
| U7 | | `C:\Program Files\R\R-4.4.1\bin\Rscript.exe` | (4, 4, 1) | (4, 4, 1) | | ★ | 路径B | **错序** | 正 |
| U8｜cpp 侧架构后缀污染（`cpp_runner:46` 自认的那条） | CPP | `C:\msys64\mingw64\bin\g++.exe` | (64, 64) | (0,) | ★ | | 路径B | **错序** | 正 |
| U8 | | `D:\tools\mingw13.1.0\bin\g++.exe` | (13, 1, 0) | (13, 1, 0) | | ★ | 路径B | **错序** | 正 |
| U9｜在册 cpp 回归夹具 | CPP | `D:\tools\mingw6.10.0\bin\g++.exe` | (6, 10, 0) | (6, 10, 0) | ★ | ★ | 路径A | 正 | 正 |
| U9 | | `D:\tools\mingw6.4.0\bin\g++.exe` | (6, 4, 0) | (6, 4, 0) | | | 路径A | 正 | 正 |
| U10｜现法平手随 pattern 序漂移 | CPP | `C:\TDM-GCC-64\bin\g++.exe` | (64,) | (0,) | ★ | | 路径B | **错序** | 正 |
| U10 | | `D:\tools\mingw6.4.0\bin\g++.exe` | (6, 4, 0) | (6, 4, 0) | | ★ | 路径B | **错序** | 正 |

读数：**用例 10 组；现行实现错序 6 组（U1/U4/U5/U7/U8/U10）；建议案错序 0 组**。
U2/U6/U9 是"两法都必须保正"的三条——它们正是**在册夹具**（见 §三-4）。
U3 不计错序，但它是**唯一一条修正后会换文件**的用例，单列为行为变更项。

错序的四类根因（对应上表）：① **前缀目录带数字**（U1 `D:\2026`、U4 `My Documents 2019`、U5 `(x86)`）；② **arch 后缀**（U7/U8/U10 的 `x64`／`mingw64`／`TDM-GCC-64`）；③ **元组不等长**使"带杂数字的一方"天然多一位（U7 `(4,4,64)` vs `(4,4,1)`）；④ **平手不确定性**（U10：现法 `(64,)` vs `(6,4,0)` 不等长比较后才平手，胜负交给 pattern 序）。

## 三、收敛设计稿（完成标准③）

### 1. 修正键：三层取值，"版本目录段"优先（建议案，未选）

```python
_SEG    = re.compile(r"[\\/]+")
_DOTTED = re.compile(r"(\d+(?:\.\d+)+)")            # 至少一个点，x.y / x.y.z
_PRODUCT = {                                          # 每族一份，落在各自 runner 里
    "R":   re.compile(r"^R[-_](\d+(?:\.\d+)+)$", re.I),
    "CPP": re.compile(r"^(?:mingw|gcc|tdm-gcc|msys)(?:[-_]?)(\d+(?:\.\d+)+)$", re.I),
}

@staticmethod
def _version_key(path: str) -> tuple:
    segs = [s for s in _SEG.split(path) if s]
    dirs = segs[:-1]                                  # 末段是 exe 文件名，不参与取值
    for s in reversed(dirs):                          # ① 产品前缀的版本目录段
        m = _PRODUCT_R.match(s)                       # cpp 侧换成 _PRODUCT_CPP
        if m:
            return tuple(int(n) for n in m.group(1).split("."))
    for s in reversed(dirs):                          # ② 右起最近的「x.y」形状段（兜未知命名）
        m = _DOTTED.search(s)
        if m:
            return tuple(int(n) for n in m.group(1).split("."))
    return (0,)                                       # ③ 未知档
```

三条设计约束，逐条有出处：
- **"只取目录段、且从右往左"**：版本目录按约定是 exe 的祖父/曾祖，右起第一个命中即它，能躲开 `D:\2026`、`My Documents 2019`、`(x86)` 这类**前缀污染**（U1/U4/U5）；左起扫描会被前缀污染抢到，故不取。
- **"至少一个点"**：这是切断 arch 后缀的关键——`x64`／`mingw64`／`TDM-GCC-64` 都是**无点单数**，一次判据全部出局（U7/U8/U10）。单靠"去掉末段数字"或"截断到 3 位"都不能同时消掉这三类。
- **仓内已有同款先例**：`r_runner.py:87` 选 R_LIBS_USER 时用的就是 `re.match(r"^(\d+)\.(\d+)", os.path.basename(p))` ——**锚定 basename、要求点分**。同文件里一处对、一处错，本设计是把 :29 拉齐到 :87 的既有口径，不引入新风格。

### 2. 两个 runner 的同步点（必须同笔，否则两族口径分叉）

| 文件 | 位置（**只锚唯一文本、不写行号**，避免本单编辑自推行号——纪律档 §十.4） | 改动 |
|---|---|---|
| `core/runners/r_runner.py` | `def _version_key(path: str) -> tuple:` 函数体（锚：`nums = _re.findall(r"\d+", path)`） | 换成 §三-1 的三层实现，产品正则用 `^R[-_]...` |
| `core/runners/r_runner.py` | 同上 docstring（现含"（字典序会把 4.9 排在 4.10 之后）"） | 补一句"只取版本目录段，路径前缀与 arch 后缀不参与" |
| `core/runners/cpp_runner.py` | `def _version_key(path: str) -> tuple:` 函数体（同一 `nums = _re.findall(r"\d+", path)` 字面） | 同一实现，产品正则用 `^(?:mingw\|gcc\|tdm-gcc\|msys)...` |
| `core/runners/cpp_runner.py` | `:43-47` 的 l923-31 ⚠️ 注释块（锚：`未在本单扩大范围修`） | **删掉该 ⚠️ 自认**，否则注释与实现相反；改成"排序键只取版本目录段，`mingw64` 这类无版本目录落未知档" |
| 两处 `for pat in self.fallback_glob:` 循环体 | 锚：`if best_key is None or key > best_key` | 建议同时把内层改为 `for p in sorted(glob.glob(pat))`，让"平手取先见者"成为**声明式**行为而非依赖 OS 返回序（本机实测 `glob.glob` 与 `sorted` 同序，但 CPython 不承诺，见 §一 附注） |

🔴 **可选的第三种同步方案（更省，但改动面不同）**：把 `_version_key` 提成 `core/runners/_version_key.py` 单源、两 runner 各自 `from ... import version_key` ＋传入产品正则。好处是"同款缺陷不会再各自漂移"（本单实测两份实现**逐字相同**，正是复制粘贴的产物）；代价是新增一个模块文件＋两处 import，动到 `core/runners/` 包结构。**案序建议：先就地双改（最小面），抽单源留作下一单**——但选案交人工。

### 3. 行为变更项（唯一一条会换落点的，必须写进验收）

U3：`R-4.4.1` 同时在 `bin\` 与 `bin\x64\` 命中时，**现法选 `bin\x64\Rscript.exe`**（杂数 64 让它多一位而恒胜），**建议案两者平手 ⇒ 按 pattern 序落到 `bin\Rscript.exe`**（pattern[0]）。两者都是合法入口（Windows 下 `bin\Rscript.exe` 是 arch 选择壳），但**这是一次可观察的行为变更**，不能算"零影响修复"。验收时必须显式覆盖，或在人工裁决里明确接受。

### 4. 回归门禁（落码后必跑，逐字给命令）

```bash
cd /d/code/learning-system && PYTHONIOENCODING=utf-8 python -m pytest \
  "tests/test_native_runners_mocked.py::test_cpp_fallback_glob_picks_highest_numeric_version" \
  "tests/test_native_runners_mocked.py::test_rscript_fallback_chooses_highest_numeric_version" \
  "tests/test_native_runners_mocked.py::test_cpp_fallback_paths_take_priority_over_fallback_glob" \
  "tests/test_native_runners_mocked.py::test_r_success_selects_highest_numeric_user_library" -v
```

- 本单（零改动）现值：**4 passed，rc=0**。定向族现值：`tests/test_native_runners_mocked.py tests/test_r_runner.py tests/test_cpp_runner.py tests/test_runner_hardening.py` → **33 passed / 7 skipped**（7 skip 全因本机无 Rscript／g++，`test_r_runner.py:13/19/25`、`test_cpp_runner.py:16/27/34/44`）。
- 🔴 **两条在册夹具是本次设计的硬约束**：`test_native_runners_mocked.py:161` 用 `C:\R\4.9\Rscript.exe`（裸版本号、无 `R-` 前缀），`:50` 用 `D:\tools\mingw6.10.0`（版本紧贴产品名、无分隔符）。⇒ **任何"只认 `R-x.y.z`"的一刀切正则都会让这两例当场红**（都退化成 `(0,)` 后平手取先见者 `4.9`／`mingw6.4.0`）。这就是 §三-1 为什么必须留"层② 右起最近点分段"兜底，也是探针把 U6/U9 单列的原因。
- 若人工反过来选"只认 `R-x.y.z` 严格式"，则连带要改这两条夹具的期望路径——**属改判据，不在本设计稿推荐位**。
- 新增判别建议（落码单顺手补，本单不补）：把 §二的 U1/U5/U7/U8 四条做成参数化夹具，断言 `_version_key` 只看版本目录段。

### 5. 残留局限（不粉饰）

- **`C:\msys64\mingw64\bin\g++.exe` 类目录名里根本没有版本**：建议案把它落到 `(0,)` 未知档。含义＝它**永远排不过**任何带版本的目录（U8 修正后 `mingw64` 输给 `mingw13.1.0`，而真实情况 mingw64 里是 gcc 13.2.0、更新）。只在"两者并存"时才显形；`mingw64` 单独命中仍被选中（本机实况就是这条路径，只是缺 `g++.exe`）。
  彻底的解法只有两条，都**超出"排序键收敛"范围**：① 解析 `g++ --version` 输出（起子进程，动到 runner 启动开销与超时预算 `total_timeout_sec`）；② 加配置/env 覆盖（如 `LS_GXX`／`LS_RSCRIPT`，把选择权交给用户）。⇒ 本档只登记为出口，不建议本波做。
- **层② 仍是启发式**：若 exe 比版本目录**更近**处还有别的点分数字段（假想 `...\R-4.3.1\bin\plugins-2.5\x64\Rscript.exe`），右起会先撞 `plugins-2.5` 而取错。建议案的层①（产品前缀）已覆盖真实 R/mingw 命名，层② 只在层① 未命中时生效，故风险面比现实现小但不为 0；严格式做法见 §三-2 的"抽单源＋按 pattern 通配段位取值"变体。
- **不等长元组比较**仍有一处语义含混：`(4,4)` < `(4,4,1)`（4.4 vs 4.4.1）符合直觉，但 `(4,10)` vs `(4,9,1)` 依赖"次位更大即胜"，属正确；此性质两法相同，本设计未改动。

## 四、零改动自证（完成标准④）

```bash
cd /d/code/learning-system && git diff --stat -- core/runners/ ; git status --porcelain -- core/runners/
```

实测两条命令均**空输出**（`core/runners/` 零 diff）；本单在盘产物只有：
① 本档；② 索引件 `docs/insights/learn-insights-index-20260918.md` 的**1 行表项＋1 行档头追记**；③ gitignore 的 `tmp/l924-26/probe.py`（不入 git，`.gitignore:19:/tmp/` 已 `git check-ignore -v tmp/` 自证）。

## 五、遗留问题（交主班／人工）

1. **选案权**：§三-1 三层键 vs "只认 `R-x.y.z` 严格式"（后者要改 2 条在册夹具）vs "抽 `_version_key` 单源"——三案都只出材料，**未选**。
2. **U3 行为变更**是否接受（`bin\x64\Rscript.exe` → `bin\Rscript.exe`）需人工点头；不点头则需在键里显式区分 arch。
3. **`D:\tools\mingw64\bin` 缺 `g++.exe`**（有 `gcc.exe`／`c++.exe`，161 文件）⇒ 本机 C++ 评测实际走 `error_kind="sandbox"`。可能形态：装歪／被删／被防病毒截断。两条出口：a) 补 `g++.exe`（环境侧，不动仓）；b) runner 接受 `c++.exe` 作为同义驱动（**生产码改动＋判题行为变更**，本单无权）。建议进待人工台账。
4. **R 侧本机无自然样本**：若要在真机上取"盘上实测非空"的证据，需要一台装了多版本 R 的机器（或跑 `D:\tools\install_R.bat`——**装依赖属越界，本单未跑**）。
5. 本档 §一 的 glob 顺序附注只是**本机观察**（NTFS 下 `glob.glob` 与 `sorted` 同序），不构成契约，故 §三-2 建议显式 `sorted()`；该建议本身也是可选项。
