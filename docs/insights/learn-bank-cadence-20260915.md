# verify-question-bank 纳入例行方案（n915-65，只出设计）

- 任务：n915-65-learn-bank-cadence（created 2026-09-15T23:39:01，软预算 ≤20 分钟）
- 执行：sweep-20260915-2300（GLM-5.3-Flash），2026-09-16 02:5x
- **路径勘误：校验器实位于 `learning-system-demo/tools/verify-question-bank.mjs`**（d914-88 的对象是学习 Demo 仓；learning-system 主仓无 tools/ 目录）。

## 一、复跑输出（原样，先命令后数字）

```
$ node tools/verify-question-bank.mjs   （learning-system-demo 内）
  ok  cpp-hello 结构断言
  ok  cpp-hello 展示档 sampleSolution 在位
PASS 18/18
exit=0
```

（项数口径＝9 题结构断言＋5 道 Python 真跑＋2 道 SQL 真跑＋2 道展示档核对；**零第三方依赖**：node 内置模块＋本机 python，缺失时回退 `py -3`——协约见脚本头注。）

## 二、例行方案三选一（不实施）

| 方案 | 做法 | 需改文件 | 取舍 |
|---|---|---|---|
| 手动清单 | demo 仓 README 加一行「改动 data.js/app.js 后跑 node tools/verify-question-bank.mjs」 | README（1 行） | 最轻；靠人工 |
| 提交钩子 | demo 仓 .git/hooks/pre-commit（本地、不入库）或 husky（引入依赖，违背零依赖协约） | .git/hooks 本地件 | 本地生效但不可迁移；husky 不建议 |
| 文档 SOP | 部署指南（README_部署指南.md）加例行核验节＋PASS 18/18 基线 | 部署指南（1 节） | 与手动清单同源，写给部署者 |

**建议**：手动清单＋部署指南 SOP 双写（两处各 1 行），不加 npm script（保持 demo 零依赖形态）。

## 三、声明

未改 data.js/app.js、未加 npm script；脚本零第三方依赖与 Python 回退分支协约已核（头注原文引用）。

## 遗留问题

无。
