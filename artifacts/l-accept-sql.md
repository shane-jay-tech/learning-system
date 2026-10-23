# l1023-006 补题验收·sql 域（l1011 批 3 个补题 topic 现值验收）

- 复扫基线：artifacts/l-census-1023.json（l1023-001，commit 56aaea7）；content/sql/ 现值 60 yaml 与锚点一致。
- 上批补题 topic 定位：l1011-12/13/14（done/ result 为日班 rebuilt 回填，原班 claims 2026-10-09 shift-20261009-0048「sql/01 补3、sql/02 补2、sql/12 补1，fc1a5cf」）→ 磁盘映射 01_select_where / 02_aggregate / 12_people_analytics（l1023-001 已按目录名修正锚点 topic 名）。
- 验收基准：每 topic ≥5 题；difficulty 1-5 分布非退化；测试自洽抽检 2 题/topic。
- 口径修正（留痕）：sql 域全 60 件零 tests 键，判分键为 setup_sql＋expected_rows（judge._rows_equal **行序敏感**）；「tests stdin/expected 自洽」按域实况修正为「expected_rows 可执行自洽」——抽检用 oracle 查询经 SQLRunner（:memory: sqlite，零写库、不碰 ProgressDAO）真跑对拍。

## topic 级验收表（三面）

| topic | 题量(≥5) | 难度直方(非退化) | expected_rows 自洽抽检（2 题/topic，oracle 真跑） | 判定 |
|---|---|---|---|---|
| 01_select_where | 5 ✓ | {1:2, 2:3} ✓ | 01_select_all：oracle `SELECT id,name,score … ORDER BY id` → 5 行逐格相等 ✓；05_order_limit：`ORDER BY score DESC LIMIT 3` → 相等 ✓ | 合格（03/04/05 缺 hints，WARN 级） |
| 02_aggregate | 5 ✓ | {1:2, 2:1, 3:2} ✓ | 01_average_score：`ROUND(AVG(score),1)` → [[81.8]] 相等 ✓；05_having_avg：`HAVING AVG>100 ORDER BY avg DESC` → [['eng',110.0]] 相等 ✓ | 合格（04/05 缺 hints，WARN 级） |
| 12_people_analytics | 5 ✓ | {2:1, 3:3, 4:1} ✓ | 01_avg_by_dept：join+ROUND2 → [['Engineering',2.33],['HR',3.5],['Sales',4.5]] 相等 ✓；05_turnover_by_dept：**按题面降序 oracle → [['sales',100.0],['eng',50.0],['hr',0.0]] ≠ expected_rows [['sales',100.0],['hr',0.0],['eng',50.0]] ✗** | 不合格（点名 05，见下） |

## 不合格明细

1. **content/sql/12_people_analytics/05_turnover_by_dept.yaml — 题面与判分键矛盾（判分不可通过）**：题面要求「按离职率降序」，正确答案行序应为 sales(100.0)→eng(50.0)→hr(0.0)；而 expected_rows 钉死为 sales→hr→eng（恰为 department 逆字母序）。judge._rows_equal 按位置逐格比对（core/judge.py:105），行序敏感——按题面写的正确查询必 MISMATCH，仅 `ORDER BY department DESC` 能过、但这与题面语义矛盾。**该题按题面不可解**。（该件同时缺 hints，validator WARN 在册。）
2. hints 缺失 6 件（WARN 级，非判分键）：01_select_where/03、04、05；02_aggregate/04、05；12_people_analytics/05——与 l1011 补题件集合重合。

## 域级门禁证据

- `python scripts/validate_content.py --domain sql` → PASS｜文件 60／解析错误 0／字段 ERROR 0／字段 WARN 6／同名组 0（6 WARN 全部「缺 hints」，与 l1011 补题件重合）。
- oracle 真跑：6 题中 5 题 match=True（01_select_all / 05_order_limit / 01_average_score / 05_having_avg / 01_avg_by_dept），1 题 match=False（05_turnover_by_dept，缺陷实锤）。执行环境 SQLRunner 内存 sqlite＋authorizer 白名单，零落盘零写库。

## 处置建议（留待内容班，本单零改动）

- 05_turnover_by_dept：将 expected_rows 改为 [['sales',100.0],['eng',50.0],['hr',0.0]]（与题面降序一致）或改题面为「按部门名降序」二选一；改后需同步复跑 oracle 对拍。
- 6 件缺 hints：按同 topic 老件口径补 hints 1-3 条；修复后复跑 `python scripts/validate_content.py --domain sql` 应 WARN 6→0。
