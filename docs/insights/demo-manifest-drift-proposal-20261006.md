# demo-manifest.json 两处订正提案＋verifier 编码 1 行修法（l1004-20；75ea 遗留3）

> 产线：执行班 l1004-20（2026-10-06）。**材料型零落码**（manifest 刷新与工具码改动均属人工闸）。
> 差异注：l1002-01/02 管 demo 解释器降级与 pyMissing 面，本单管 manifest 键漂移与探针编码口径。

## §一 两键 old/new 对照（逐字）

### 键 1：`storage.key`（键名漂移）

- **manifest 现值**（assets/demo-manifest.json）：`"storage": { "kind": "browser-localStorage", "key": "学习完成进度", "server": null }`
- **实况**（assets/app.js:9）：`const DONE_KEY = "lsdemo_done_v1";`（:11/:16 读写同一常量）
- **订正 new**：`"key": "lsdemo_done_v1"`——「学习完成进度」是 UI 文案化的旧键名，与实际 localStorage 键不符。

### 键 2：`verifier.last_result`（缺复现条件）

- **manifest 现值**：`"verifier": { "tool": "tools/verify-question-bank.mjs", "last_result": "PASS 18/18" }`
- **实况**（本班复跑 `node tools/verify-question-bank.mjs`）：`PASS 18/18（python 解释器：python）`——**结果串自带解释器条件后缀**，manifest 只留了前半；「PASS 18/18」在 python 缺失的机器上不可复现（工具会降级/判不可信），无条件串具误导。
- **订正 new（二选一，建议 B 结构化）**：
  - A 最小：`"last_result": "PASS 18/18（python 解释器：python）"`
  - B 结构化：`"last_result": { "text": "PASS 18/18", "condition": "python 解释器：python", "date": "2026-10-06" }`（后续复跑只改字段，不再手工拼串）

## §二 verify-question-bank.mjs 编码 1 行 env 修法（行号定位）

- 已修面：`tools/verify-question-bank.mjs:70-73` `pyRun()` 已带 `PYTHONIOENCODING: 'utf-8'`（l927-23 落地）。
- **漏画面**：`:48`（`probeInterpreter()` 内的探针执行）——`out = execFileSync(cand, args, { input: '', encoding: 'utf8' });` **无 env 注入**。探针只跑 `print(1)` 输出纯 ASCII，当前不假红；但与 ：73 形成同文件两口径（矿源「gbk→utf8 假红」指的即此类无 env 面）。
- **1 行修法**：`:48` 改 `{ input: '', encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' } }`——与 ：73 同款，防未来探针/print 内容含中文时假红。属改已跟踪生产码 ⇒ 闸后执行；同批建议把两处 env 提为模块级常量 `UTF8_ENV` 防第三处漂移。

## §三 落地边界

两键订正＋编码 1 行均为一次小执行单；manifest 若按 §一键 2-B 结构化，须同步检查是否有消费方解析该串（rg 全仓 `last_result` 仅 manifest 自身，零消费方——订正无连带）。
