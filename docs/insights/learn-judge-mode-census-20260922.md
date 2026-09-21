# judge_mode 显式化只读普查：全库 399 题的显式/默认切面（l922-116）

- 日期：2026-09-22 ｜ 仓库：D:\code\learning-system ｜ 基线 HEAD：`f4819ef`
- 性质：**只读普查**。content/ 零改动（`git status --porcelain content/` 空输出，见 §六），源码零改动
- 缘起：`learn-r-plain-downgrade-20260920.md`（D6）遗留 2——r 已逐题显式，其余四语言的 run 题仍吃 `core/loader.py` 的隐式默认。
  任务书写「300+ 道」，**现值实测 259 道**（D6 当时是 329，之后 r 的 70 道转为显式；「300+」按磁盘实况收窄，属锚点过期非判错）
- 结论先行：**当前没有任何一题因默认值判错**（§四 三组交叉证据），全库逐题显式的收益只有「可 grep」，
  代价是 259 行内容 diff 与两条字节基线联动；建议改走**三条低成本护栏**（§五 方案 B），不推荐全库显式（方案 A）

## 一、口径：三层分开数，别把「grep 命中」当「解析到的键」

| 层 | 判据 | 本仓实测 |
|---|---|---|
| L1 文本层 | 文件任意列出现 `judge_mode:` | 与 L2 **完全同数**（无嵌套键、无重复行、无缩进误命中） |
| L2 解析层 | `yaml.safe_load` 后**顶层**含 `judge_mode` 键（含显式 null） | 140 件 |
| L3 运行层 | `core.loader.load_language()` 归一化后 `Problem.judge_mode` | 399 题，直方图与 L2＋默认并集逐语言一致 |

L1==L2 是这条普查能直接用 grep 口径复算的前提，三处形态异常计数器**全为 0**：
`nested_only_key`（文本命中多于第 0 列行数）、`duplicate_key_lines`（同文件多行 `judge_mode:`）、`explicit_null_or_empty`（显式写空值）——判据与命令见 §六。

## 二、进线表（先命令后数字，逐语言 显式/总数）

命令：

```
python - <<'PY'   # 逐语言：yaml 件数 / 顶层含 judge_mode 的件数 / 取值直方图 / loader 题数
import glob, os, collections, yaml
from core import loader
for lang in ("python", "sql", "cpp", "r", "agent_dev"):
    files = sorted(glob.glob(os.path.join("content", lang, "*", "*.yaml")))
    hist = collections.Counter(); n = 0
    for fp in files:
        d = yaml.safe_load(open(fp, encoding="utf-8", errors="replace")) or {}
        if "judge_mode" in d:
            n += 1; hist[str(d.get("judge_mode"))] += 1
    loader.invalidate_cache()
    run_hist = collections.Counter(p.judge_mode for t in loader.load_language(lang) for p in t.problems)
    print(lang, f"{n}/{len(files)}", dict(hist), "loader:", dict(run_hist))
PY
```

实测输出（2026-09-22 02:3x，HEAD `f4819ef`，工作树对 content/ 干净）：

| 语言 | 显式件数/题目数 | 显式取值直方图 | 走默认件数 | L3 loader 实际分布 | topic 数 |
|---|---|---|---|---|---|
| python | **8/121** | `ai_open` 8 | 113 | run 113 ／ ai_open 8 | 27 |
| sql | **0/54** | —（无显式件） | 54 | run 54 | 12 |
| cpp | **0/62** | —（无显式件） | 62 | run 62 | 13 |
| r | **84/84** | `run` 70 ＋ `ai_open` 14 | 0 | run 70 ／ ai_open 14 | 18 |
| agent_dev | **48/78** | `ai_open` 48 | 30 | run 30 ／ ai_open 48 | 15 |
| **合计** | **140/399（35.1%）** | run 70 ＋ ai_open 70 | **259** | **run 329 ／ ai_open 70** | 85 |

对账闭合（完成标准 ②）：

```
显式 140 + 默认 259 = 399 = content/<5 语言>/*/*.yaml 件数 = core.loader 加载题数
closed: True   # tmp 普查脚本断言：tot["explicit"] + tot["default"] == tot["yaml"] == tot["loader"]
loader 解析被跳过件数（parse_skipped）= 0，_last_load_errors = 空
```

`content/` 下另有 `paths/`（6 个 yaml，0 处 `judge_mode:`）与 `datasets/`（0 个 yaml）——**不属题库**，不计入 399，也不该被显式化波及。

与既有钉桩互证：五语言 `tests/test_content_census_<lang>.py` 各自 pin 的 judge_mode 直方图（python `{"run":113,"ai_open":8}`、sql `{"run":54}`、cpp `{"run":62}`、r `{"run":70,"ai_open":14}`、agent_dev `{"run":30,"ai_open":48}`）与上表 L3 列**逐值相同**——本普查未引入第二套数字。

## 三、r 显式化前后对照

引用 `docs/insights/learn-r-plain-downgrade-20260920.md`（D6，用户 2026-09-20 拍板「降级为普通题」）§三 的真实复跑输出：

| 面 | D6 改前 | D6 改后（本普查现值） | 变化 |
|---|---|---|---|
| r 显式件数 | 14/84（只有 14 道开放题写了 `judge_mode: ai_open`） | **84/84** | ＋70 行 `judge_mode: run`，逐文件插在 `tags:` 之后 |
| r 走默认件数 | 70 | **0** | 归零 |
| 全库走默认件数 | 329（= 399 − 70 显式 ai_open/r-agent_dev-python 合计） | **259** | −70，全部来自 r |
| 全库判定结果 | — | 与改前**逐字段等价** | 等价性证明在 `tests/test_judge_mode_equivalence.py`（loader／dispatcher／runner／JudgeResult 四层，含阴性对照） |
| 文件级显式契约测试 | 无 | `tests/test_content_census_r.py:107 test_契约_每道题显式judge_mode` | **五语言里只有 r 有这一条** |

D6 的动因（该档 §一 原话）是「**它是什么题只能靠读代码推断**」，不是判错——这一点在本普查里被复算成立：r 的 70 道改前改后 L3 取值都是 run（§二 表 r 行）。

**其余四语言的现状与 D6 之前的 r 完全同型**：259 道 run 题靠 `core/loader.py:216` 的 `str(data.get("judge_mode") or "run")` 落地，
字段定义处 `core/loader.py:31` 亦为 `judge_mode: str = "run"`（两处锚点本单复核**均未漂移**）。

## 四、默认值当前是否改变行为：三组交叉证据，答案是否

1. **`judge.py` 只对 `ai_open` 分支特判**：`core/judge.py:279` `if pdict.get("judge_mode") == "ai_open": return _judge_open(...)`，
   其余一律落 `_run_test_cases`。⇒ 显式写 `run` 与「不写」在判分链路上**走的是同一条路**（D6 的等价性测试已把这条钉成四层证明）。
2. **全库 70 道 `ai_open` 题 100% 已显式**（python 8 ＋ r 14 ＋ agent_dev 48）。⇒ 不存在「该走开放判分却被默认吞成 run」的题。
3. **259 道默认题的答案面全部可机判**（`run_default_no_machine_answer` 计数器五语言均为空），且形态与所属语言自洽：

| 组 | 答案面形态 | 题数 |
|---|---|---|
| 走默认 | `stdout` | 113 |
| 走默认 | `tests+stdout` | 92 |
| 走默认 | `rows+setup_sql`（全在 sql） | 54 |
| 显式 run | `stdout`（全在 r，D6 产物） | 70 |
| 显式 ai_open | `rubric` | 70 |

⇒ 「显式 run」与「默认 run」两组的答案面形态**不同分布**（默认组含 tests/rows，显式 run 组只有 stdout），
这是 r 题库本身形态单一造成的，**不是默认值引入的差异**——它只说明「r 全是 stdout 比对题」这一既成事实。

**真正的残余风险只剩一条，且与「是否全库显式」无关**：取值写错（`AI_open`／`ai—open`／显式 null）会被静默降级成 run，
loader 与 judge 都不校验（`VALID_JUDGE_MODES = ("run", "ai_open")` 目前只在 `scripts/mark_r_judge_plain.py:123` 的批处理门里用）。
现值 0 命中（§一 三计数器均空）。

## 五、口径建议：是否值得全库显式

**不推荐方案 A（全库逐题显式，259 行 diff）**，三条实测依据：

1. 收益只有可 grep／可读性，**判定行为零变化**（§四 证据 1、2）。
2. 内容与字节基线联动成本真实存在：`tests/test_content_census_r.py` 的字节级现状桩、`tests/test_content_crlf.py` 里记录的
   「r/ 现状字节 ＝ pre-D6 备份字节 ＋ 恰一行」证据链（备份在 `data/backups/content-20260920-133722/`，按 manifest sha256 复核）。
   四语言再插 259 行，这类基线要逐条重建；且 python 有 8 个、r 有 16 个（全库共 24 个）**CRLF 题件**，插入行的行尾要与原件自洽，
   否则直接撞 `test_content_crlf.py` 的「文件内行尾自洽」判据。〔注：python 那 8 个 CRLF 件是 13_scipy_stats/14_sklearn_intro/15_ab_text 的统计题，
   **不是** 8 道显式 ai_open 题——数量巧合，普查第一版差点误推成同源，已按文件名逐条否证〕
3. 逐题显式会把「默认值语义」这件事**永久固化成内容债**：以后新增题漏写就是隐式 run，仍要有文件级契约测试兜（见方案 B①），
   等于「插 259 行」＋「写一条测试」两笔都要花，只做前者拿不到后者防的那类错。

**推荐方案 B（三条低成本护栏，只读普查不实施，交日间定夺）**：

- B① 把 r 独有的 `test_契约_每道题显式judge_mode` 反向推广成一条**全库**契约：
  「凡答案面为 `rubric`/`reference_answer` 且无 `expected_output`/`tests`/`expected_rows` 的题，必须显式 `judge_mode: ai_open`」——
  钉的是「新加开放题忘记写」这个唯一真会咬人的场景，一条测试覆盖 399 题，零内容改动。
- B② 在 `core/loader.py:_build_problem` 落一次取值合法性校验（值不在 `("run","ai_open")` 时 `_record_load_error` 并回落默认），
  把 §四 残余风险从「靠脚本自觉」变成「运行时可见」。属 loader 公共面改动，需另行派单评审。
- B③ 若仍要走全库显式：**先**落 `.gitattributes`（`*.yaml text eol=lf` ＋ `git add --renormalize content/`）统一次行尾，
  **再**按语言分批（cpp 62 → sql 54 → python 113 → agent_dev 30，把有 rows/tests 形态的三语先做，r 已完成），
  每批同步重建 §五-2 点名的两条基线。

## 六、content/ 零改动自证与复算命令

```
$ git status --porcelain content/ docs/
(空输出)
$ git diff --stat HEAD -- content/
(空输出)
```

复算（本档所有数字可由此两档重出；两脚本均为临时件，收班时删除，故把判据写在本节）：

- 主普查：`python tmp/l922116_census.py > tmp/l922116_census.json` —— 逐语言 yaml 件数／显式件数／三组形态异常计数器／L3 loader 直方图／`closed` 对账布尔
- 形态附表：`python tmp/l922116_shape.py` —— 显式组与默认组的答案面交叉表（§四 表来源）

判据要点（复现时照此实现，勿简化成一句 grep）：
显式与否按 **yaml 顶层键**判（`"judge_mode" in data`），空值／非字符串／重复行／嵌套命中各自单列计数；
「默认」= 顶层无该键，其运行值由 `loader.py:216` 的 `or "run"` 决定，故 §二 的 L3 列才是判分真值。

## 七、本普查未覆盖处（如实标注）

- 未验证 **`ai_open` 题在 UI 侧的实际判分链路**（`ui/pages/language.py:216/:426` 用 `judge_mode == "ai_open"` 分流），
  该面属 `test_judge.py`／`test_ai_*` 族既有覆盖，本单未重跑；普查只保证「键的显式与否」与「loader 取值」两处口径。
- `judge_mode` 与 **`expected_rows` 语义无关**这一点按 `core/judge.py:_run_test_cases` 的现有分支结构推得，
  未做 sql 54 题的实跑双验证（本机无 g++/Rscript，且 sql 题需授权题库路径，见 `test_sql_authorizer.py`）。
