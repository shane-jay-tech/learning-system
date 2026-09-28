---
id: l927-16
title: `_offline_fallback` 未命中仓外 hub 时回退仓内共用提示表（154242 档 R-1 落地）
task: l927-16（zcode-bridge 波次 40，档位＝代码写位）
shift: qoder-executor-20260928-0145-learn50
written: 2026-09-28T02:02
head_at_write: `83a780e`（开工 porcelain 0 行；主班 01:35 代提交 l927-12 后的 HEAD）
mode: 改 `core/ai_review.py`（+40/−4，只加文案分支与可选 `lang` 入参）＋新增 `tests/test_ai_review_offline_inrepo_fallback.py`；判题面零改动（`core/judge.py`／`*.yaml`／分值／判分口径／学习路径 diff=0）；`data/progress.db` 未连接
status: done——卷宗判据①②③全中
supersedes_or_extends: extends `zcode-bridge/done/20260925-154242-67e5.result.md` §D 表 D ＋「遗留问题」R-1（方案原文）；顺带顶掉该档 R-5 的一条后果（hub 缺失时的静默降级）
---

# LLM 挂了也不该只会说「请稍后再试」——离线兜底接上仓内表

## 〇、一句话

`core/ai_review.py:_offline_fallback`（LLM 全线不可用时的兜底点评）过去只接**仓外**共享 hub
`D:\code\scripts\common\friendly_errors.py` 一张表，同批 6 个高频错误样例上实测**只认得 2 个**；
而**仓内** `core/runners/error_feedback.py` 那张四语言共用、行号已折算的表覆盖 **5/6**，这条路径却没接它。
本次在 hub 未命中／缺失／抛异常时**回退查仓内表**，并把 `lang` 作为可选第三入参接进函数与调用点。

## 一、为什么必须给 `lang`

仓内表的提示条目是**按语言门控**的（`HINTS` 每条带 `langs`）：`IndexError`／`ZeroDivisionError` 只对 `python`/`agent_dev` 生效、
`no such table` 只对 `sql` 生效、`'x' was not declared in this scope` 只对 `cpp` 生效。
`_offline_fallback` 改前签名是 `(passed, stderr)`——**没有 lang**，所以仓内表根本无从命中。
落盘证据（`git show HEAD:core/ai_review.py` 的函数单独加载后调用）：

```
签名：HEAD (passed: bool, stderr: str) -> str  →  工作树 (passed: bool, stderr: str, lang: str = '') -> str
HEAD 版接受第 3 参：否 ⇒ TypeError: _offline_fallback() takes 2 positional arguments but 3 were given
```

⇒ 这确实是**生产码改动**（154242 档 R-1 自己标的「⚠ 属生产码改动，停人工闸后」）。
本单的授权来源＝波次 40 横幅把 l927-16 明确派给代码写位档，且卷宗「做什么」原文就是
「按 R-1 方案实现：ai_review.py:286-297 的 `_offline_fallback` 增加 lang 入参与仓内表回退」。
横幅另 narrow 到「判题面禁碰」——`ai_review` 的**点评文案**不在判题面（`passed`／`ok`／`exit_code`／`error_kind`／分值／题件均未动，diff 可验），
故未撞闸；若 R-1 需要动 `judge.py` 才会停手，本次不需要。

**向后兼容**：`lang` 给缺省 `""`，缺省时仓内表一律不命中 ⇒ 行为逐字等于改前。
既有 5 处测试调用（`tests/test_ai_review_offline.py` 4 处＋`tests/test_core_edges.py:80` 1 处）**一字未改**仍绿。

## 二、改后的判定顺序

```
hub 命中具体模式（title != "出了点问题"）  →  用 hub 文案并**立即返回**（不双写）
  ↳ hub 未命中 / hub 整个缺失（_fe is None，R-5 面）/ hub 抛异常  →  查仓内 hint_only(lang, stderr)，
     命中则拼「先给你一个离线提示——<折算行号><提示>」
  ↳ 两边都不命中                                                  →  只剩通用句（保持安静，不编造提示）
```

标记串沿用既有的「先给你一个离线提示」⇒ `test_offline_fallback_unknown_error_no_noise`（钉"未知名不出额外行"）不破。
`where_phrase` 一起接上，是因为行号折算（preamble 偏移）本就是同一张仓内表的另一半价值。

## 三、判据③：覆盖对照复测（不引用他档数字，当场重算）

新用例 `test_覆盖对照_仓内表命中5例_hub只命中2例` 的现跑读数（`-s` 输出）：

```
NameError      lang=python  hub=未命中    仓内=命中
SyntaxError    lang=python  hub=未命中    仓内=命中
IndexError     lang=python  hub=命中     仓内=命中
no such table  lang=sql     hub=未命中    仓内=命中
ZeroDivision   lang=python  hub=命中     仓内=命中
未知名            lang=python  hub=未命中    仓内=未命中
```
⇒ **仓内 5/6、仓外 2/6**，与 154242 档逐字对上（该档的结论第一次被钉成了断言而不是叙述）。

## 四、改前／改后逐样例读数

对照器把 HEAD 版与工作树版各以独立模块名加载（HEAD 源来自 `git show HEAD:core/ai_review.py`，落 tmp 目录，
**未覆盖工作树文件、无任何 git 写操作**），全日志：
`D:\code\tmp\qoder-executor-20260928-0145-learn50\l92716_beforeafter.log`。

| 样例（lang） | 改前 | 改后（hub 在场） | 改后（hub 缺失 `_fe=None`） |
|---|---|---|---|
| NameError (python) | len 35，只剩通用句 | `第 3 行：「dfn」还没赋值就用——检查拼写，或是否漏了上面的赋值行` | 同左 |
| SyntaxError (python) | len 35，只剩通用句 | `第 2 行：这一行语法不合法——常见于漏冒号 :、括号不配对、中文标点` | 同左 |
| no such table (sql) | len 35，只剩通用句 | `表「users」不存在——检查表名拼写（题目 setup 建了哪些表？）` | 同左 |
| r non-numeric (r) | len 35，只剩通用句 | `R 要的是数值，传进了非数值——先看该列是什么类型` | 同左 |
| cpp not declared (cpp) | len 35，只剩通用句 | `第 7 行第 9 列：「count」未定义——检查拼写与作用域` | 同左 |
| IndexError (python) | hub 给 `**下标越界**…`（len 98） | **逐字不变**（hub 优先，不双写） | `第 1 行：下标越界——序列没有这么长，先看 len()`（原为 len 35 静默） |
| ZeroDivision (python) | hub 给 `**除以了零**…`（len 89） | **逐字不变** | `第 1 行：除数是 0——检查分母来源`（原为 len 35 静默） |
| 未知名（任何 lang） | len 35 安静 | len 35 **仍安静** | len 35 仍安静 |

顺带顶掉的一条（154242 R-5 的后果面）：hub 缺失时改前**一律**静默（下表最后一列的"改前"全是 len 35），
改后 5/6 仍有提示 ⇒ 那条"缺 hub 只 warning 一级、学生侧无感"的降级，在学生可见面上已被补偿
（R-5 的**可观测告警**那半句仍未做，见「遗留」）。

## 五、验收读数

```
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_ai_review_offline_inrepo_fallback.py -q
15 passed in 0.05s      rc=0
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_ai_review_offline.py tests/test_core_edges.py \
    tests/test_error_feedback_rows.py tests/test_ai_review_strategy.py tests/test_ai_followup.py \
    tests/test_ai_generate.py tests/test_backfill_dedup_legacy_events.py -q
87 passed in 6.71s      rc=0
```

卷宗三条判据的落点：

| 判据 | 怎么命中 |
|---|---|
| ① 签名变更的调用方全数同步（rg 调用点清单） | 生产侧 `grep -rn "_offline_fallback(" core/ ui/ scripts/` ⇒ **只有** `core/ai_review.py` 的 1 处定义＋1 处调用（`:274` 已带 lang）。钉成机器断言 `test_全仓无第二处生产调用点`（正则扫 `_offline_fallback\s*\(`，命中集必须恰为 core/ai_review.py 两处，且调用行带 lang 实参）；另有 `test_生产调用点已把lang传下去_源码钉子` 从源码文本再钉一层。测试侧 5 处调用点（`test_ai_review_offline.py:10/16/24/30`＋`test_core_edges.py:80`）靠缺省值兼容，逐字未改、仍绿 |
| ② 4 语言用例绿 | `test_四语言各走仓内表出提示` 参数化 python／sql／r／cpp 各一枚（强制 `_fe=None` 保证走的是新回退支），另验 `agent_dev` 与 `python` 同门控；cpp 另有一枚带列号的 `test_cpp带列号的提示` |
| ③ 覆盖对照（5/6 vs 2/6）复测记录 | `test_覆盖对照_仓内表命中5例_hub只命中2例` 当场重算并断言（读数见 §三），＋ §四 的 HEAD×工作树逐样例并排日志 |

## 六、遗留

1. **R-5 的可观测面没做**：hub 缺失仍只有 `logger.warning` 一级，学生侧靠本单的仓内表补上了，
   但"缺 hub"这件事本身仍无告警出口（154242 R-5 建议的 vendoring 或升级告警＝另一刀，未动）。
2. **R-3／R-4 未碰**：「反馈须带动作」「无空泛表扬」两条仍只有提示词条款、无程序化强制（154242 原档已登记，非本单范围）。
3. **`follow_up` 的兜底没接仓内表**：`core/ai_review.py` 里只有 `review()` 走 `_offline_fallback`；
   追问（`follow_up`）与知识点问答的离线分支不在本单判据内，未动。要不要接＝主班裁。
4. **全量套件未跑**（并发窗，兄弟班在跑）：定向面 87 passed ＋ 本新件 15 passed。
