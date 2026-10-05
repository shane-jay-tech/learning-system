# 跨设备合并事件顺序裁决材料：import_all 旧事件冒充新事件（l1004-09；7b25 遗留1）

> 产线：执行班 l1004-09（2026-10-06）。**材料型，生产码零改动；复现在 tmp 副本，零生产库触碰**。

## §一 import_all 现值（排序/覆盖依据）

`core/data_portability.py:93-127`：
- append 层（attempts/learning_events/rubric_scores）：`:103-116` 直接插入，无序问题。
- 键控表（problems_status/review_state）：`:119-127` **`INSERT OR REPLACE` 无条件覆盖**——`problems_status` 明明有 `last_attempt_ts` 列（schema 见 core/progress.py:83-89，主键 (lang, problem_id)），但 :123-126 的 REPLACE **不比较 last_attempt_ts**，导入行必胜。净效果＝「最后写入者赢」且写序＝执行序（导入在后），与 ts 无关——7b25 所述「按 rowid 序而非 ts 序决定最后事件」的机制实锤。

## §二 E4 复现（tmp 副本，可复制）

```bash
mkdir -p tmp/l1004-09 && .venv/Scripts/python.exe - <<'EOF'
import os, sys; sys.path.insert(0, os.getcwd())
tmpdb = os.path.abspath('tmp/l1004-09/repro.db')
if os.path.exists(tmpdb): os.remove(tmpdb)
from core.progress import ProgressDAO
from core.data_portability import import_all, FORMAT_NAME
dao = ProgressDAO(db_path=tmpdb)
with dao.conn:
    dao.conn.execute("INSERT INTO problems_status(lang, problem_id, status, last_attempt_ts) VALUES ('python','demo/p1','solved','2026-10-05T10:00:00')")
payload = {"format": FORMAT_NAME, "version": 1, "data": {
    "attempts": [], "learning_events": [], "rubric_scores": [],
    "problems_status": [{"lang": "python", "problem_id": "demo/p1", "status": "solved", "last_attempt_ts": "2026-09-01T08:00:00"}],
    "review_state": [], "meta": [], }}
stats = import_all(dao, payload)
row = dao.conn.execute("SELECT status, last_attempt_ts FROM problems_status WHERE problem_id='demo/p1'").fetchone()
print(row)  # → ('solved', '2026-09-01T08:00:00')
dao.close()
EOF
```
本班实跑读数：`import stats problems_status = 1`；`after import: ('solved', '2026-09-01T08:00:00')`；**VERDICT old-overrides-new = True**——本地 10-05 新结果被导入方 09-01 旧作答覆盖，矿源指控复现为真。

## §三 两修法对照（迁移风险×回滚面）

| | 案① problems_status 按 last_attempt_ts 比较后再覆盖 | 案② 合并前按业务键 ts 归并 attempts 重排 |
|---|---|---|
| 形态 | :123 改 `INSERT INTO … ON CONFLICT(lang,problem_id) DO UPDATE SET … WHERE excluded.last_attempt_ts > problems_status.last_attempt_ts`（SQL 一处） | 导入前置步骤：把 payload 与本地 attempts 按 `(lang, problem_id, ts)` 归并排序后重建键控表（Python 侧，或临时表＋JOIN） |
| 覆盖语义 | 新 ts 赢；ts 相同（跨设备同秒）维持「导入方赢」需再定 tie-break（建议再比 status 枚举或 payload checksum） | 全量重排＝语义最正，但重排后「本地现行值」可能被改写（非仅导入键） |
| 迁移风险 | 低：单点改动；`last_attempt_ts` 可空（schema :87）——**NULL 行需定规**（建议 NULL 视作最旧，被任何有 ts 行覆盖） | 中：批量重写键控表＋append 层插入序＝rowid 语义变化，下游「最近 N 条」类查询结果序改变 |
| 波及面 | 仅 problems_status；review_state 同型病（:128-133 同为 REPLACE）建议同批同改（其业务 ts 列为 last_reviewed_at/见 schema 实列） | attempts/learning_events/rubric_scores 全 append 层＋两键控表 |
| 回滚面 | 极小：revert 单 commit 即回 REPLACE 语义；已合并数据无需修复（下次导入自然纠正） | 大：重排不可逆（rowid 已变），回滚需从备份整库恢复 |
| 断言影响估计 | data_portability 测试 +2~3（新旧两向＋NULL 规）；既有 import 断言若断「导入后值＝导入值」需改 1~2 处 | data_portability 全件回归＋顺序敏感断言全套重写（估 5~8 处） |

**材料倾向**：案①（单点＋可回滚＋NULL 规可文档化）；案②的「全量归并」收益主要在 append 层展示序，可后置为独立展示层排序（查询时 ORDER BY ts），不必动存储序。

## §四 边界

两案均属用户数据取舍（7b25 明言超出执行手授权），全部交主班；本档复现零生产库触碰（tmp/l1004-09/repro.db 为一次性副本，可留档复跑）。
