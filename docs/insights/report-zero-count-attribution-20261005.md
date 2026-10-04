# 周报月报全 0 计数归因材料（l1002-18，只读零写库）

- 时点：2026-10-05（exec-shift-20261003-manual）；复现读法照 l923-24 §十三：`sqlite3.connect('file:data/progress.db?mode=ro&immutable=1', uri=True)`

## 一、现值读数（完成标准①）

| 表 | min | max | 行数 | 按月 |
|---|---|---|---|---|
| attempts.ts | 2026-05-30 13:16:51 | **2026-05-30 15:03:25** | 15 | 2026-05 ×15（**单日单月**） |
| learning_events.local_date | 2026-05-30 | **2026-08-24** | 81 | 2026-05 ×60 ／ 2026-07 ×12 ／ 2026-08 ×9 |

矿源「attempts 停 05-30／events 到 08-24」现值复现成立（attempts 仍是 5/30 单日 15 行，5 月后**零新 attempts**；events 活到 8/24）。

## 二、generate_report 计数源逐字段追（完成标准②）

`core/report.py generate_report`（:19）：
- `total_attempts`（:26）← `d.total_attempts()` ← **attempts 表全量 COUNT**（不分时间）⇒ 报告该字段=15 非 0。
- `period_attempts`（:27,42）← `d.attempts_by_day(days)` ← **attempts 表** `WHERE ts >= datetime('now', '-N days')`（progress.py:298-306，本地日分组）⇒ attempts 最新 5/30、now=10 月 ⇒ **7/30/90 日窗口全 0**。
- `by_lang`/`weak_topics` 等 ← attempts/problem_status 族同理（时间敏感字段全 0/None）。
- **learning_events 在 report.py 零引用**（grep 无命中）——周报/月报的计数源**只有 attempts 一张表**。

## 三、实跑复现（完成标准③）

```
$ python -c "from core.report import generate_report; …"
generate_report(days=7)  → period_attempts = 0
generate_report(days=30) → period_attempts = 0；by_lang = None
（total_attempts = 15：不分时间的总量字段非 0，与「全 0」的体感差异在 period 族字段）
```

## 四、归因与三案对照（完成标准④）

**归因一句话**：报告 period 族计数的唯一供数表 `attempts` 在 5/30 后零新增（5 月后学习行为走的是 events 通道/其它入口），窗口过滤注定 0——**数据面断层**（attempts 通道停用），非报告代码缺陷。

| 案 | 做法 | 影响面 |
|---|---|---|
| **补数据** | 让现学习流回写 attempts（如 english/practice 通道同步落 attempts 行） | 报告即活；需确认 attempts 列语义（lang/problem_id/code/passed）与新流兼容；历史 5/30 后空窗无法补（无源数据） |
| **换源** | report.py 计数改读 learning_events（local_date 活到 8/24） | events 8/24 后也停 ⇒ 只把断层右移；且 events 无 passed/lang 语义对齐问题需逐字段映射，改动面大 |
| **双源合并** | attempts ∪ events 映射后合并计数 | 覆盖最全；两表 schema 语义对齐成本最高，且 8/24 后仍 0（**两表 8/24 后都停**——学习数据面整体断流才是终局事实） |

**诚实注记**：events 在 8/24 后同样零新增——「换源/合并」都救不了 8/24 之后的空窗；**根因是学习行为数据 8/24 后整体断流**（demo 仓使用停滞），不是单表问题。报告逻辑本身健康（有数据即出数）。

## 五、零写入零改码声明

全程 immutable 只读；generate_report 只读跑；无任何数据回填/代码改动。
