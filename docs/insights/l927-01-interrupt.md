# l927-01 — Pyodide 死循环挂起修复：判题超时护栏（75fb 修法一落地）

- 日期：2026-09-30
- 任务：zcode-bridge/inbox/l927-01.task.md（result: outbox/l927-01.result.md）
- 锚点：done/20260925-120537-75fb.result.md 遗留 1；docs/insights/l927-05-judge-security-review.md G11
- 改码仓：**learning-system-demo**（目标件 `assets/runners.js`，75fb 锚点指认；任务 cwd=learning-system，主仓零改动）

## 修法与一处有据偏离

75fb 建议两案：①Pyodide `setInterruptBuffer`（约 20 行）②迁 Web Worker（约 2h）。本单按①的预算落地，但**中断信号源改为 CPython `sys.settrace` 看门狗**，原因：

- `setInterruptBuffer` 的跨线程置位需要 `SharedArrayBuffer`（主线程被 Pyodide 同步执行阻塞期间，本线程 JS 无法置位缓冲，只有另一线程写 SAB 才可见）；
- 本 demo 部署形态全部无 COOP/COEP 头（README_部署指南：python -m http.server / Netlify 拖拽 / Vercel / GitHub Pages）→ `crossOriginIsolated=false` → SAB 不可用 → 字面落地①在现网不生效；
- `sys.settrace` 看门狗（逐事件查 `time.monotonic()` 墙钟、超限抛 `KeyboardInterrupt`）纯 Python 机制，全环境可用，语义等价（超时→中断→报超时），约 15 行。

## 改动清单（learning-system-demo）

1. `assets/runners.js`：
   - 新增 `pyTimeoutSec()`：阈值取 `window.PY_JUDGE_TIMEOUT_SEC`（>0 数字），默认 **5s**（与主仓 `python_runner.py:104 timeout_sec=5` 对齐）；
   - harness 增补：`__deadline = monotonic() + float(__time_limit)`；`__timeout_guard` 逐事件查墙钟，超限置 `__timed_out=True` 并抛 `KeyboardInterrupt('judge-timeout')`；`sys.settrace(__timeout_guard)` 安装、finally 中 `sys.settrace(None)` 卸载；
   - `runPython` 尾部：读到 `__timed_out` 即返回友好超时文案（`⏱ 运行超时：超过 N 秒被强制中断（程序可能存在死循环或超长计算）`），不回传 Python traceback；非超时路径错误回传行为零变化。
2. `tools/test-interrupt.html`（新增，回归测试件）：5 用例自驱页（死循环中断/正常判题+stdin/运行错/语法错/中断后复用），跑完在页尾输出 `RESULT: ALL PASS n/n`。

## 验收情况（完成标准对照）

- ① 死循环用例被中断的测试绿：✅ 测试页 5/5 PASS（2026-09-30 实测，本地 http.server:8791 + 浏览器实跑）；
  预热后复测：阈值 1s → elapsed=**1.00s** 中断并报超时（时间精度实证，非碰巧快速失败）。
- ② 约 20 行级 diff：✅ runners.js 净增约 22 行（含注释与超时文案）；测试件另计。
- ③ 正常判题回归不破：✅ case2（print+input stdin 回显）、case3（ZeroDivisionError traceback）、case4（SyntaxError traceback）、case5（中断后 runner 复用再跑正常）全绿——75fb 四类形态中①成功②失败③编译错全部保持原行为，④超时从「挂死页面」变为「N 秒报超时」。

## 证据

- `RESULT: ALL PASS 5/5`（tools/test-interrupt.html，浏览器实测 2026-09-30）
- 预热复测 `elapsedSec=1.00, timedOut=true`（evaluate 直测）
- `grep -nE "timeout|interrupt" assets/runners.js` 修复前 0 命中（75fb 记录）→ 修复后 settrace 护栏在位

## 遗留问题

- 用户代码若自行 `sys.settrace` 会覆盖看门狗（护栏失效）——demo 场景学生题不涉及，记录为已知边界。
- 超时阈值默认 5s 未做成界面旋钮（页面 JS 变量可配）；如需题级配额（如 SQL 2s/cpp 10s 分域），另立单。
- `learning-system-demo/INVENTORY.md`、`OPERATIONS.md`、`assets/demo-manifest.json` 为他人 untracked 在途件，本班未触碰；demo 目录无独立 git 仓（改动落根仓工作树，是否入库由主班裁决）。
