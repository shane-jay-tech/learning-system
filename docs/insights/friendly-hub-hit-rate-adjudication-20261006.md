# 离线解释枢纽命中率 1/8 处置材料：加中文词表 vs 承认 diff_hint 已够（l1004-27；a6b8 遗留5）

> 产线：执行班 l1004-27（2026-10-06）。**材料型**；与 l927-16（仓内回退表 error_feedback）关系见 §三。

## §一 命中率现值复跑（8 条样本矩阵内联，与 a6b8 否证② 一致）

```
$ python （sys.path 插 D:\code；friendly_explain 对 8 条真实 stderr 形态）
py-1 ZeroDivisionError: division by zero        → hit  「除以了零」
py-2 NameError: name 'undef_x' is not defined   → miss
py-3 SyntaxError: '(' was never closed          → miss
py-4 ModuleNotFoundError: No module named …     → miss
py-5 IndentationError: unexpected indent        → miss
sql-1 near "FRM": syntax error                  → miss
cpp-1 未检测到 g++…                              → miss
r-1  代码运行超时（超过 5 秒）…                    → miss
命中率 1/8
```

**机理复核**：枢纽 `_GENERAL_PATTERNS`（friendly_errors.py:33-57，11 条）是**运维域英文词表**（file/encoding/permission/timeout/connection/JSON/numeric/keyerror/zero/memory/index）；本仓 stderr＝Python 异常原文＋**中文话术**（「代码运行超时（超过 5 秒）」不被 `timed?\s?out|timeout` 命中；「未检测到 g++」不在任何模式）——两个词表世界几乎不相交，唯一交集是 `division by zero`（Python 异常原文恰好是英文）。

## §二 两案对照

### 案 A：给枢纽加中文/判题专属词表（extra_patterns 通道）

- **改动量**：枢纽自带**免触全局的注入通道**（friendly_errors.py:79-87 `extra_patterns` checked first，docstring 明言「the leak-free way to customize」）⇒ ai_review 侧 `_offline_fallback` 调用处传 5-6 条判题域模式即可，**根仓文件零改动**：
  ```
  (r"name '?\w+'? is not defined|未赋值", "名字找不到", …),
  (r"syntaxerror|near \"|syntax error|解析", "语法错误", …),
  (r"modulenotfounderror|no module", "缺模块", …),
  (r"超时|死循环", "运行超时", …),
  (r"未检测到 (g\+\+|rscript)", "缺编译/运行环境", …),
  (r"indentationerror|缩进", "缩进不对", …),
  ```
- **估计改动量**：ai_review.py 一处调用点 ~10 行词表＋测试 2-3 例（复用 8 条样本矩阵做断言）。维护代价＝与 error_feedback.HINTS 两词表并行的第三份口径（_offline_fallback 的提示与 diff_hint 会重复/措辞漂移）。
- 收益：AI 断线时的离线兜底从「通用话」升「判题域指引」。

### 案 B：承认 diff_hint 面已够，离线兜底降级为纯告知

- **论据**：`error_feedback.HINTS → diff_hint` 已经给中文、带行号、走判题主路径（`_row_feedback`，p50 0.053ms 恒在）；离线兜底只在 **AI 断线**这一罕见分支出现，且其正文已有「判题本身不受影响」＋离线提示补充段——把「先给你一个离线提示」补充段删去/降频，用户在断线场景仍保有 diff_hint 的完整指引。
- **改动量**：ai_review.py `_offline_fallback`（:321-333）删/短-circuit 友好解释分支 ~3 行＋测试调整（若有断言兜底含提示的用例）。
- 收益：消灭第三词表的维护面；断线文案更短。
- 风险：`_offline_fallback(passed=False, stderr)` 在 follow_up 等其它调用点的 stderr 形态（非判题 diff_hint 覆盖面，如 AI 网络错误）会失去唯一指引——**需先普查 `_offline_fallback` 全部调用点的 stderr 来源**（本班未展开，落地前必查）。

## §三 与 l927-16（仓内回退表）关系标注

- l927-16 的回退表＝`error_feedback.HINTS`（四语言中文提示，**判题主路径常驻**）；案 A 的词表＝**AI 断线兜底分支**专用。两案都不动 HINTS。
- 若案 A：新词表只挂 `_offline_fallback` 的 extra_patterns，**不得**与 HINTS 合流（职责不同：HINTS 面向学生错误教育，兜底词表面向「AI 不在时给一句可行动建议」）。
- 若案 B：等价于裁定「HINTS/diff_hint 已是唯一解释面」，与 l927-16 无冲突、反而收拢。

## §四 交主班

材料倾向**案 B**（命中率低的根因＝两词表世界不相交，而非词表「不够长」；补 5-6 条只是把 1/8 抬到 ~7/8，代价是永久的双词表维护；而 diff_hint 面已实测覆盖同一批错误且恒在）。案 A 仅当主班认为断线兜底是高频体验面时才值得。
