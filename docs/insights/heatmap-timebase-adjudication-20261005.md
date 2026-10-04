# 热力图 GROUP BY localtime 与窗口 UTC 时基统一裁决材料（l1002-10，只读零改码）

- 时点：2026-10-05（exec-shift-20261003-manual）
- 现值 SQL（l1002-09 同源化后的 `HEATMAP_SQL`，dashboard.py 与 test_heatmap.py 同源）：
  `SELECT DATE(ts, 'localtime') AS d, COUNT(*) AS n, SUM(passed) AS p FROM attempts WHERE ts >= datetime('now', '-91 days') GROUP BY d ORDER BY d`
  ——**SELECT/GROUP 用 localtime（本地日界），窗口 WHERE 用 UTC now**：即矿源点名的混用。

## 一、错格窗口量化（完成标准①）

**前置事实（attempts.ts 写入形态）**：`record_attempt` 走 SQLite 默认（表定义 ts DEFAULT datetime('now')＝**UTC**）；生产库 progress.db 现值 15 行、UTC 小时分布 13×8/14×5/15×2（=本地 21–23 时），**UTC 日≠本地日的行＝0**——现库无一行落在错格带。

**错格带推演**（用户本地 UTC+8）：
- 本地 **0:00–7:59** 作答（=UTC 前日 16:00–23:59）→ `DATE(ts,'localtime')` 归**作答当日**本地格（正确）；但窗口边界 `ts >= datetime('now','-91 days')` 是 **UTC 日界截断**——窗口首日的本地凌晨行（UTC 时间属 91 天前那天 16:00 后）**早于** UTC 边界被排除 ⇒ **少算**，偏移量最多 8 小时（矿源「错一格」的实态：窗口首日格缺失，非错格错列）。
- 本地 8:00 后作答：UTC 与本地同日，无任何偏移。
- **受影响行现值：0**（上表）；影响仅在「未来出现本地 0–8 点作答 × 恰逢窗口首日」的交集，属潜伏口径毛刺非现行数据错误。

## 二、两案对照（完成标准②）

**案 A：统一 localtime**（窗口补 'localtime'，一行 diff）
```diff
- "FROM attempts WHERE ts >= datetime('now', '-91 days') "
+ "FROM attempts WHERE ts >= datetime('now', 'localtime', '-91 days') "
```
- 索引/性能：窗口函数化后仍是对 ts 的范围比较（'now' 常量+修饰在解析期定值），`idx`（若有 ts 索引）扫描形态不变，性能无差。
- **既有测试影响（必须同批修）**：test_heatmap 的 manual timestamps 用例插入的是**本地形态字面串**（`f"{yesterday} 10:00:00"`）——`'localtime'` 修饰会把无时区字面**当 UTC 再 +8**，`DATE` 归 tomorrow ⇒ `len(rows)==2` 断言转红。同批修法：夹具字面改 UTC 形态（`f"{yesterday} 02:00:00"` 类）或经 `datetime.utcnow()` 生成——夹具与生产写入形态（UTC）对齐本就是应有之义（现夹具形态与生产不一致属既有暗分叉）。
- 收益：格子归属与窗口边界同用本地日界，错格窗口归零；用户日历直觉一致。

**案 B：统一 UTC**（GROUP 改 `DATE(ts)`）
```diff
- "SELECT DATE(ts, 'localtime') AS d, …"
+ "SELECT DATE(ts) AS d, …"
```
- 零测试影响（窗口/GROUP 同为 UTC）。
- 代价：本地凌晨作答归**前一 UTC 日格**，与用户本地日历直觉冲突（GitHub 风格热力图惯例是本地日界）；不推荐。

**建议**：案 A＋test 夹具 UTC 化同批（两行级改动）；或维持现状（现库 0 行受影响，急迫度低——若近期无凌晨使用习惯，可留观察至首条错格行出现再动）。

## 三、零改码声明

本单零码改动（含 l1002-09 刚同源化的 HEATMAP_SQL 未再触碰——两案 diff 均为草案）。
