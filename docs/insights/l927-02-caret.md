# l927-02 — error_feedback 列定位补齐：Python/R/SQL caret 列纯函数（D-12 修法）

- 日期：2026-09-30
- 任务：zcode-bridge/inbox/l927-02.task.md（result: outbox/l927-02.result.md）
- 锚点：done/20260925-120550-1247.result.md D-12（「error_feedback 抽 caret 列是纯函数改动、不碰判分，但会新增可见输出面 ⇒ 交主班裁」——本单即该裁的执行单）

## 修法

`core/runners/error_feedback.py:locate_column` 原先非 cpp 恒 `None`；现按语言分治：

- **python/agent_dev**：新私有纯函数 `_py_caret_column`——锚定**最后一个 main.py 帧**（不是最后一个 caret 块：3.11+ 每帧都带 caret，库帧会排在学生帧之后），在该帧段内找首个 caret 标记行（`^^^^` 与 `~~~^~~~` 形态都认），`列 = caret 下标 − 3`（CPython 打印源码行带 4 空格前缀）。**列号口径＝去缩进显示行**：CPython 3.12 打印前会把源码行去缩进（本机 3.12.9 实采证实：4 空格缩进行与 Tab 行打印结果逐字相同），学生行首有缩进时编辑器绝对列还要加缩进宽——stderr 里无从得知，docstring 如实写明，绝不瞎补。
- **r**：R ≥ 4.3 解析错报文自带 `行:列:`（如 `Error: main.R:2:7: unexpected symbol`），只在含 "Error" 的行上找，防学生自己打印的时间戳（`12:30: …`）被当坐标；运行期错误不带位置 ⇒ None。本机无 Rscript，形态按合成报文钉（沿 1247 L-9 先例，工具链在位窗复测）。
- **sql**：SQLite 报文**不带任何位置信息**（真跑 SQLRunner 坏表名实证）⇒ 恒 None，登记为**实测契约**而非缺口。
- **cpp**：原逻辑逐字未动。

输出面变化自动流经既有 `where_phrase`（"第 N 行"→"第 N 行第 M 列："），`feedback`/判分链路零触碰；`locate_column` 抽不到时一切照旧（宁缺勿错）。

## 改动清单

- `core/runners/error_feedback.py`（+62/−11）：新 `_PY_FRAME_RE`/`_PY_CARET_LINE_RE`/`_R_LINE_COL_RE` 三个正则、`_py_caret_column` 纯函数、`locate_column` 三语言分治＋docstring。
- `tests/test_error_feedback_columns_20260930.py`（新增 15 例）：几何真值全部来自本机 CPython 3.12.9 实采（探针件 tmp/l927-02/），含库帧插队反例、无 caret 反例、时间戳防误判、SQL None 契约（真 runner）、cpp 两形态回归、判分零改动自证。
- `tests/test_parser_boundary_inputs_20260925.py`：`test_column_is_never_located_for_python`（钉 D-12 **缺陷**实况）翻转为 `test_column_now_located_for_python_d12_fixed`（钉**修复**），cpp 对照原样保留。
- `tests/test_error_feedback_rows.py`：行号钉 `"第 5 行："` → `"第 5 行"`（列号追加后"第 5 行第 7 列："不再含"第 5 行："子串），行折算断言强度不变。

## 验收情况

- ① 三语言列定位用例绿：✅ 新件 15 例＋既有三件全绿，`125 passed / 0 failed`（2026-09-30 实测，含消费方 test_ai_review_strategy/test_execution_stage_separation）。
- ② 判分逻辑零改动自证：✅ `git diff --stat` 仅 error_feedback.py＋2 个测试件；`core/judge.py` 零触碰；`test_判题结论面逐字未变`（rows 件）通过——passed/ok/error_kind/exit_code 取值面一字未动。
- ③ cpp 侧行为不回归：✅ cpp 定位代码逐字未动＋rows 件 `test_cpp_行列定位_两种报文形态` 与新件 cpp 两例全绿。

## 证据

- `PYTHONIOENCODING=utf-8 python -m pytest tests/test_error_feedback_columns_20260930.py tests/test_error_feedback_rows.py tests/test_parser_boundary_inputs_20260925.py tests/test_ai_review_strategy.py tests/test_execution_stage_separation_20260925.py -q` → **125 passed**
- 实采真值：`print(nope)` caret idx 10 → 列 7；`print(` idx 9 → 列 6；函数内 `1/0` `~^~` idx 11 → 列 8；库帧插队 → None
- `git diff --stat`：core/runners/error_feedback.py + tests 两件，judge.py 不在列

## 遗留问题

- 列号口径是"去缩进显示行"（CPython 3.12 自身显示语义如此）；学生行首缩进的绝对列 stderr 里不可得，如需绝对列须改 runner 传文件行原文——超出本单"纯函数"授权面，如需另立单。
- R 合成钉未经真工具链验证（本机无 Rscript）；R 工具链在位窗请主班排复测（同 1247 L-9）。
- tmp/l927-02/ 探针件（实采 stderr 四份）留盘备查，gitignored 不入册。
