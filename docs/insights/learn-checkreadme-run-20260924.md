# learning `check_readme` 出口实跑对账：rc／四检点现值／组合矩阵（l924-28，只出稿 · 零生产码改动）

> **卷宗**：`zcode-bridge/inbox/l924-28.task.md`（现址 `zcode-bridge/done/`）。产出面＝本档一份；`README.md` 与 `scripts/` 零 diff（自证见 §八）。
> 取数时刻 2026-09-25T04:2x+08:00、learning HEAD `cc7e4d5`、工作树 `git status --porcelain` = 0 行。
> 🔴 **本档是 l924-12 的 xfail 前提底数，不是修复方案**：任何"该改 README 首行还是该改判据"的取舍一律**建议稿、未选案**，交人工拍板。
> 探针在 gitignore 的 `tmp/qoder-executor-20260925-0420-learn32/`（`git check-ignore -v` → `.gitignore:19:/tmp/`）：`probe_writes.py`（AST 轨落盘面扫描）、`probe_shortcircuit.py`（短路次序实测，合成件只写在 tmp）。

## 〇、锚点与前提复核（卷宗每条前提都实测）

| 卷宗前提 | 实测 | 命令 | 判定 |
|---|---|---|---|
| `scripts/generate_system_report.py:247` 为 `elif args.check_readme:` | 逐字一致（行号 247） | `$ rg -n "elif args\.check_readme:" scripts/generate_system_report.py` | ✅ 零漂移 |
| `:249` 为 `sys.exit(0 if ok else 1)` | 一致，但**同型串在 :246 也有一份**（rg 实测 2 命中） | `$ rg -n "sys\.exit\(0 if ok else 1\)" scripts/generate_system_report.py` → `246:`／`249:` | ✅ 锚点成立，⚠ 不唯一，注释/改码勿只写行号 |
| `:242-246` 是「--check 与 --check-readme 同给时的 `and ok` 短路次序」 | 一致：`:243 ok = check_report(...)` 先跑、`:245 ok = check_readme(...) and ok` 后算 | `$ rg -n "if args\.check:|ok = check_report|ok = check_readme" scripts/generate_system_report.py` | ✅ 见 §六实测 |
| 四检点＝标题版本／题目数／知识点数／路线图 v 串 | 与 `check_readme` `:210/:213/:216/:219` 四条 `errors.append` 一一对上 | `Read` `scripts/generate_system_report.py:203-229` | ✅ |
| 版本单源 | `core/version.py:1 VERSION = "0.6.5"`、`:2 RELEASE_DATE = "2026-08-15"` | `$ rg -n "VERSION\|RELEASE_DATE" core/version.py` | ✅ |

## 一、跑前先验落盘面：本出口**可安全实跑**，无需 copy2 保护

判据来自"它用哪些落盘 API"，双轨对到位：

| 轨道 | 命令 | 读数 |
|---|---|---|
| 正则轨 | `$ rg -n "write_text\|open\([^)]*[\"']w\|mkdir\|to_csv\|sqlite3\|shutil\|dump\(" scripts/generate_system_report.py` | **0 命中**（rc=1 无匹配） |
| AST 轨（可达模块图） | `$ python tmp/qoder-executor-20260925-0420-learn32/probe_writes.py` | 入口 `scripts/generate_system_report.py` 命中 3 条：`L102 run()`＋`L184 replace()` ×2；`core/loader.py` 命中 2 条全是 `replace()`；`core/version.py` **0 命中** |

两轨差额解释（不许只报一个数）：

- `L184`／`loader.py:L84/L111` 的 `replace()` 是 **`str.replace`**，被我的 `WRITE_FUNCS` 名单（含 `Path.replace`）误收 ⇒ **假阳 5 条**，真实写点 0。正则轨把 `replace` 排除了，所以读 0 —— 两轨在"零真实写盘"上闭合。
- `L102 subprocess.run` 是**唯一非只读支路**，且只在 `count_tests(strict=True)`（即 `--strict`）里执行，跑的是 `pytest --collect-only` ⇒ 副作用只到 `.pytest_cache/`、`__pycache__/`（`.gitignore:10`、`:1` 均已忽略，实测跑完 `git status --porcelain` 仍 0 行）。
- `check_readme` 本体 `Path(readme_path).read_text(...)`（`:205`）＝只读；`core/loader.py` 无 `FileHandler`／`basicConfig`（`rg -n "FileHandler|basicConfig" core scripts` 全仓 0 命中）⇒ 导入期不写日志文件。

⇒ **README.md 不会被这个出口重写**，本单无需 `copy2` 指过去；直接对真档实跑，跑前跑后各取一次 sha256 自证（§八）。

## 二、实跑输出全文（主判据命令）

```
$ PYTHONIOENCODING=utf-8 python scripts/generate_system_report.py --check-readme README.md
FAIL: README 检查不通过:
  - README 标题版本不含 0.6.5（当前：# 编程 + Agent 开发学习平台）
```

- **rc = 1**、stdout 118 B、**红项数 = 1**、成因 = 检点①（标题版本）。
- 与完成标准 ①「rc 与红项数一致」自洽：`rc=1` 且 `errors` 列表长度 1（`:222 if errors:` 判 False）。
- 与 l924-12 在册桩一致：`tests/test_readme_version_gate.py` 定向复跑 **`5 passed, 1 xfailed in 1.00s`**（xfail＝`test_真README必须过check_readme`），同批闭合哨兵 `tests/test_insights_index_closure.py` 3 passed（合计 6 例收集）。
  `$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_readme_version_gate.py tests/test_insights_index_closure.py -q`

## 三、四检点现值表（每点附 README 现值行摘录）

| # | 检点（源码位） | 判据实现 | metrics 现值 | README 现值行摘录 | 判定 |
|---|---|---|---|---|---|
| ① | 标题版本 `:210` | `version not in first_line`（**裸子串，无整词边界**） | `0.6.5`（`core/version.py:1`） | `README.md:1  # 编程 + Agent 开发学习平台` | 🔴 **FAIL**（唯一红） |
| ② | 题目数 `:213` | `_contains_number`＝`(?<!\d)403(?!\d)` 整词 | `total_problems=403` | `README.md:52  - 5 种语言并行学，进度独立；403 题、85 知识点、6 条学习路径…` | ✅ PASS（全档含 `403` 仅 1 行：`rg -c "403" README.md` = 1） |
| ③ | 知识点数 `:216` | 同整词口径 | `total_topics=85` | `README.md:52`（同上"85 知识点"） | ✅ PASS。⚠ 全档含 `85` 的有 2 行，另一行 `README.md:48 http://localhost:8511（与心理系统 8501 错开）` 被整词边界正确挡掉 ⇒ 该检点在真档上**只有 1 个合法命中点**，删 :52 即红 |
| ④ | 路线图 v 串 `:219` | `f"v{version}" not in text`（**全档子串，且不整词**） | `v0.6.5` | `README.md:3 …当前版本 v0.6.5。`／`:59 ## 当前能力亮点（v0.6.5）` | ✅ PASS，但**名实不符**：README **根本没有路线图小节**（`rg -c "^#{1,3} " README.md` = 10 个标题，逐条看完无"路线图/Roadmap"；`rg -in "roadmap\|路线图\|里程碑" README.md` 仅 :56 一句功能描述）。该检点实为"全文任何位置出现 v0.6.5"，且 `v0.6.5` 是 `v0.6.50`/`v0.6.51` 的子串 ⇒ 版本号换代时会**假 PASS** |

检点②③与 `check_report` 的前两条（`:171/:174`）是**同一条判据的两次实现**；`check_report` 另查 5 个 `by_lang` 题数与 6 条路径里程碑数，`check_readme` **一概不查**——两函数覆盖面不对称，实测见 §四组合 7。

## 四、组合矩阵（`--check` / `--check-readme` / `--json` 三开关，8 组合实测）

每条都是 `$ PYTHONIOENCODING=utf-8 python scripts/generate_system_report.py <args>`，`rc` 用 `; rc=$?` 现取（不接管道，避免读到 `tail` 的 rc）。

| # | args | rc | stdout | 结论 |
|---|---|---|---|---|
| 1 | （无开关） | 0 | 449 B，`=== 学习平台系统指标 (v0.6.5, 2026-08-15) ===` ＋全量指标 | `else: print_metrics` 支路 |
| 2 | `--json` | 0 | 1424 B JSON | `elif args.json` 支路 |
| 3 | `--check docs/system-report-v0.6.5.md` | 0 | 35 B `PASS: 报告数字与实测一致` | 在册报告档当前**与实测对平**（l923-25 的修数没过期） |
| 4 | `--check-readme README.md` | 1 | 118 B，1 条 FAIL | 主判据（§二） |
| 5 | `--check docs/system-report-v0.6.5.md --check-readme README.md` | 1 | 153 B：**先** report 的 `PASS`、**后** README 的 `FAIL` | `:242` 支路优先于 `:247`；`and ok` 的 rc＝两者之与 ⇒ **README 一条红就足以让组合命令 rc=1** |
| 6 | `--json --check-readme README.md` | 1 | 118 B，与组合 4 **逐字相同**（`diff` 无输出） | 🔴 `--json` 被 `elif` 链吞掉：给了 `--check-readme` 就**永不输出 JSON**，机器读方拿不到指标（不是 rc=0 的空 JSON，是完全没有） |
| 7 | `--check README.md`（拿 README 当 report） | 1 | 940 B，**11 条 FAIL**：5 条 `by_lang` 题数＋6 条路径里程碑（**没有**题目总数/知识点数两条） | 印证 §三末：②③两检点与 report 前两条同源，故在 README 上过；细粒度项 README 全缺 |
| 8 | `--check docs/no-such-report.md` | 1 | 993 B **裸 traceback**，`FileNotFoundError: [Errno 2] ... 'docs\\no-such-report.md'`（`:168 read_text` 未兜异常） | ⚠ 路径写错与"数字不符"**同为 rc=1** ⇒ 任何只看 rc 的钉法（含 pytest 里 shell out）会把拼错路径当成"红得像现状"，判据必须钉 stdout 文案 |

组合 5 的 stdout 顺序是"report 在前、README 在后"，而表达式写成 `check_readme(...) and ok` ⇒ 打印次序与操作数次序相反，成因见 §六。

## 五、`--strict` 对指标的影响：只动 `tests` 一个数，且**在本机默认编码下静默失效**

| 形态 | 命令 | `tests` 读数 | rc | stderr |
|---|---|---|---|---|
| 默认（无 `--strict`） | `$ … --json` | **865**（`^\s*def test_` 正则计数，`:115`） | 0 | 空 |
| `--strict`（本机默认 GBK） | `$ PYTHONIOENCODING=utf-8 … --strict --json` | **865**（与默认**一模一样**） | 0 | **10 行**：`Exception in thread Thread-1 (_readerthread)` … `UnicodeDecodeError: 'gbk' codec can't decode byte 0xbb in position 2076` |
| `--strict`（UTF-8 模式） | `$ PYTHONUTF8=1 PYTHONIOENCODING=utf-8 … --strict --json` | **947**（pytest `--collect-only` 真收集数，`:106`） | 0 | 空 |

- 机制：`count_tests` 用 `subprocess.run(..., text=True)`（`:102-105`），解码走**父进程 locale**（本机 `cp936/GBK`）；`PYTHONIOENCODING=utf-8` 只管 stdio 文本层、**改不了 `locale.getpreferredencoding()`**，只有 `PYTHONUTF8=1`/`-X utf8` 能改。子进程输出含中文 ⇒ 读线程抛异常 ⇒ `proc.stdout=None` ⇒ 被 `:108 except Exception: pass` **整块吞掉** ⇒ 回落到正则口径。
  `$ python -c "import locale;print(locale.getpreferredencoding(False))"` → `cp936`
- 影响面（对 l924-12 的关键结论）：**`--strict` 从不改变 rc**——`metrics["tests"]` 既不进 `check_report` 也不进 `check_readme`（§三、§四组合 5/7 的 FAIL 清单里都没有"测试用例"一项）。实测 `$ … --strict --check-readme README.md` 的 stdout 与不带 `--strict` **逐字相同**（`diff` 除 stderr 噪声外 0 行差异），rc 同为 1。⇒ xfail 桩**不必**碰 `--strict`；但要防"把 :10 行的 GBK traceback 当失败信号"。
- 865 vs 947 的 82 例差额＝parametrize 展开等口径差，本单不裁决（在册全量数属他单，见 §九）。

## 六、`:242-246` 短路次序实测：现写法保诊断，改法会吞诊断

`$ PYTHONIOENCODING=utf-8 python tmp/qoder-executor-20260925-0420-learn32/probe_shortcircuit.py`（合成必红 report 只写在 tmp，README 只读）

| 写法 | rc | stdout 长度 | 是否含 README 的 FAIL 行 |
|---|---|---|---|
| 现：`ok = check_report(...)` 后 `ok = check_readme(...) and ok`（`:243/:245`） | 1 | 553 B | ✅ 含 |
| 假想对调：`ok = ok and check_readme(...)` | 1 | 485 B | 🔴 **不含**（68 B 诊断被短路吞掉） |

⇒ `and` 交换律不改 rc，但**会把 README 的成因清单弄没**。l924-12 若为"理顺次序"而对调操作数，等于给长期红装一个"只显示 report 那半截"的盲门；现写法（把有副作用的调用放左边）是要保持的行为，不是笔误。

## 七、交付给 l924-12 的 xfail 前提底数（建议稿，未选案）

1. **底数**：真 README 上 `check_readme` 有且只有 **1 条红**（标题版本），另三条检点在真档上**本来就是绿的**——与 `tests/test_readme_version_gate.py::test_现状红的成因恰为标题版本一条` 的"成因数==1"断言同值，本档是它的**命令行侧独立复算**（一个走 in-process、一个走子进程 rc）。
2. **钉法风险清单**（本档新查出的三条，都属"以后会假绿/假红"的形态，处置取舍交人工）：
   - 检点④ **全文子串**＋无版本边界 ⇒ README 路线图小节不存在也能过；将来升 `v0.6.6` 时若只改 :59 标题、:3 忘了改，它仍判绿（:59 一处即足够）。
   - 检点①④ 都**不吃整词**（与②③的 `_contains_number` 不对称），`v0.6.50` 一类串会造成假 PASS。
   - 组合命令 rc **恒被 README 的红牵着**（§四组合 5），且 `--json` 与 `--check-readme` **互斥**（组合 6）⇒ 若 xfail 桩想同时钉"报告数字"与"README 版本"，必须拆成两次子进程调用，不能指望一次跑出两份结论。
   - 路径拼错＝`FileNotFoundError` 裸 traceback＋rc=1（组合 8）⇒ 判据要钉文案不钉 rc。
3. 本档**不改** `README.md`、不改 `scripts/generate_system_report.py`、不改 `tests/test_readme_version_gate.py`；§七 2 的四条若采纳，需另单出稿并同步 `plan.md:53` 的"四处同一批改"清单。

## 八、零 diff 自证（完成标准 ④）

| 时点 | `git status --porcelain \| wc -l` | `README.md` SHA256 |
|---|---|---|
| 实跑前 | 0 | `f750a2f8f87bf8fab0aa8878c5419a9accb07bcd75b09a340ee7f9af922c7f60` |
| §四 全部 8 组合跑完 | 0 | 同上（逐位一致） |
| §六 探针跑完（本档落盘前） | 0 | 同上 |

`$ certutil -hashfile README.md SHA256 \| sed -n 2p`、`$ git status --porcelain`
⇒ `README.md`、`scripts/`、`docs/`（除本档）零改动；新增内容只在 gitignore 的 `tmp/qoder-executor-20260925-0420-learn32/`。

## 九、复算配方（一条不落，逐字可跑）

```bash
# 主判据（rc 用 ; rc=$? 现取，别接管道）
cd /d/code/learning-system
PYTHONIOENCODING=utf-8 python scripts/generate_system_report.py --check-readme README.md   # 期望 rc=1、1 条 FAIL
# 组合矩阵
PYTHONIOENCODING=utf-8 python scripts/generate_system_report.py --check docs/system-report-v0.6.5.md            # rc=0
PYTHONIOENCODING=utf-8 python scripts/generate_system_report.py --check docs/system-report-v0.6.5.md --check-readme README.md   # rc=1，先 PASS 后 FAIL
PYTHONIOENCODING=utf-8 python scripts/generate_system_report.py --json --check-readme README.md                  # rc=1，stdout 与上一条主判据逐字相同
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python scripts/generate_system_report.py --strict --json | rg '"tests"'      # 947；去掉 PYTHONUTF8=1 则回落 865 且 stderr 10 行 GBK traceback
# 定向面（禁跑全量：本波 learning 只出稿，全量数属其它单）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_readme_version_gate.py tests/test_insights_index_closure.py -q  # 5 passed, 1 xfailed
```

> ⚠ 本档所有读数都是 **2026-09-25T04:2x+08:00 @ HEAD `cc7e4d5` 的现值，不是断言对象**；题量/知识点数/用例数会随后续补题与新增用例漂移，引用前请按 §九 现取。
