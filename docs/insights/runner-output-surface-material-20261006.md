# 执行器输出面三缺陷族材料：stdin 静默截断＋stderr 尾切＋UI 裸 stderr（l1004-02；16e3 D-1＋1247 D-11＋70e3#4）

> 产线：执行班 l1004-02（2026-10-06）。**材料型，零码改动**——判题可见输出属判分邻域，只出材料。
> 与 l927-02（D-12 列定位）互补不重叠：彼单管 traceback 列号折算，本单管**输出面的截断与呈现**。

## §一 三处函数现值（行号贴出，本班复核）

| 函数 | 现值锚 | 现行为 |
|---|---|---|
| `_safe_stdin` | `core/runners/python_runner.py:97-102` | stdin 编码后 `data[:_MAX_STDIN_BYTES]` **静默头切**（1,000,000 字节），rc=0、stdout/stderr 无一字提示 |
| `_truncate` | `core/runners/python_runner.py:64-69` | `data[:limit]` **头切**＋尾部追加「[... 输出过长，已截断（>limit 字节）]」；UTF-8 半字符已防（:68）。调用点：stdout `_truncate(out_b, MAX_STDOUT_BYTES)`、stderr `_truncate(err_b, MAX_STDERR_BYTES)`（:180-181 一带）——**stderr 也被头切**，而 CPython traceback 结论在最后一行 ⇒ 头切吃掉结论（D-11） |
| `_error_summary` | `core/judge.py:118-142` | 「error:」行优先（截 120），否则过滤 Traceback/File 行后取**最后一行**（截 120）；空 stderr 返回「运行失败」——**末行语义**是本族改法的公共约束 |
| UI 裸 stderr | `ui/pages/language.py`（`r.run_result.stderr` → `render_ui_block(r.run_result.stderr)`） | 「错误信息」块逐字渲染 raw stderr（70e3 刻意保留的「可追溯」另一半） |

## §二 三案最小改法（改前后学生所见示例）

### 案 1（D-1）stdin 静默截断 → 截断提示行

- **改法**：`_safe_stdin` 返回 `(data, truncated)` 或在 `run()` 内比较截断前后长度；truncated 时给 **stderr 结果头部**（勿入尾部，护 `_error_summary` 末行语义，见 §三）前置一行提示。
- 改前学生所见（stdin 2 MB 场景）：
  ```
  [程序输出] （空或错误答案）   ← rc=0，「答案错了」，无任何原因
  ```
- 改后：
  ```
  【系统提示】输入超出 1MB 上限，已截断至 1,000,000 字节——程序收到的是不完整输入，请检查输入规模。
  （原 stderr 逐字保留在后）
  ```

### 案 2（D-11）stderr 头切 → 头尾保留

- **改法**：stderr 专用保留比＝**头 60KB＋尾 40KB**（100KB cap 下；尾段保住 traceback 结论行），中段以显式省略标记衔接。stdout 可维持现头切（进度刷屏在头，无「结论在尾」语义）。仅动 `_truncate` 或加 `_truncate_stderr` 变体，判分零触碰。
- 改前学生所见（超长源码行 traceback）：
  ```
  Traceback (most recent call last):
  File "main.py", line 42, in <module> …（海量重复行…）
  [... 输出过长，已截断（>100000 字节）]     ← 结论被切掉
  ```
- 改后：
  ```
  Traceback (most recent call last):
  File "main.py", line 42, in <module> …
  [... 中段省略 N 字节 …]
    NameError: name 'resutl' is defined      ← 尾段完整，结论可见
  ```

### 案 3（70e3#4）UI 裸 stderr ＋ R 中文提示接入点

- **现值维持**：raw stderr 逐字渲染是「可追溯」刻意保留面，**建议不改 UI**——案 1/案 2 的可见行为变更全部发生在 stderr 文本内容内，UI 零改动即受益。
- **R 侧中文提示接入点评估（70e3 预警的验证）**：`_error_summary` 取「最后一个有效行」，**若把中文提示行 append 到 stderr 尾部，`meaningful[-1]` 会改选提示行**，原 summary（真实错误行）被顶掉 ⇒ 接入点必须二选一：
  - ① 提示行走既有 `_row_feedback` 通道（`core/judge.py:145-160`：`error_feedback.hint_only(lang, stderr)` 已经是「追加到 summary 之后」的形态，R 词表加条目即可）——**推荐**，零 raw stderr 污染；
  - ② 若坚持入 stderr，只能前置（同案 1 形态）并在 `_error_summary` 的过滤名单加提示行前缀——改判分邻域，不推荐。
- 改前（R stderr 无中文提示）：
  ```
  错误: object 'df' not found        ← raw 原样；下方 diff 提示＝_error_summary 摘的这一行
  ```
- 改后（走 ① 通道）：
  ```
  第 1 行：object 'df' not found——R 侧常见：变量名拼写或未执行赋值行（hint_only 词表新条目）
  ```

## §三 公共约束（三案共享的设计护栏）

1. **一切提示/标记行不得占据 stderr 末行**——`_error_summary`（judge.py:118）末行语义与 `hint_only` 词表匹配都以现行 stderr 形态为前提；提示行只允许「头部前置」或「中段标记」两种落点。
2. **byte 口径**：提示行计入 100KB/1MB 限额（Windows `\r\n` 的 `\r` 计字节的实况见 16e3 D-5 钉子），提示行长度要短（≤120 字节）防自我挤占。
3. **判分零触碰**：`ok`/`passed`/`exit_code`/`error_kind` 均不动；案 1/2 只改 stderr 内容，案 3 只改 `_row_feedback` 词表——与 16e3「判分口径零改动」同纪律。
