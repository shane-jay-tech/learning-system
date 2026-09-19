# data/progress.db 表结构快照体检（2026-09-19 日间续班，任务 l918-27，只读）

> 复跑命令：
> ```bash
> python - <<'PY'
> import sqlite3
> con = sqlite3.connect('file:data/progress.db?mode=ro', uri=True)
> for t in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY 1"):
>     print(t[0], con.execute(f"SELECT COUNT(*) FROM '{t[0]}'").fetchone()[0])
> PY
> ```
> mtime 注记：主库 mtime **2026-08-24 12:09:55**（8/24 后未再落主库——数据全在 WAL 伴生件里，-wal/-shm mtime 为本日 10:1x 只读连接触碰所致，同括号复测 unchanged=yes，读操作未写库）。

## 一、基线快照（schema_version=2，7 张业务表＋sqlite_sequence 内部表）

| 表 | 行数 | 索引 | 关键列 |
|---|---|---|---|
| attempts | 15 | idx_attempts_ts / idx_attempts_lang_pid | id, lang, problem_id, code, passed, ai_feedback, ts |
| learning_events | 51 | idx_events_created / idx_events_lang_pid / idx_events_date / idx_events_type | id, event_type, lang, topic_id, problem_id, path_id, milestone_id, payload_json, created_at, local_date |
| meta | 5 | autoindex(key) | key, value, updated_ts |
| problems_status | 14 | idx_status_status_ts + autoindex | lang, problem_id, status, last_attempt_ts |
| review_state | **0** | idx_review_due + autoindex | lang, problem_id, interval_days, ease, review_streak, next_due_date, last_result, updated_ts |
| rubric_scores | **0** | idx_rubric_ts / idx_rubric_lang_pid | id, lang, problem_id, attempt_id, dimension, score, comment, ts, prompt_version, model, dimension_id |
| schema_meta | 1 | autoindex | key, value（schema_version=2） |

meta 现值：ai_pulse_monthly/quarterly=done、all_mistakes_cleared=done、security_notice_seen=done、achievements_earned（首批四成就）。

## 二、观察项（只记不改）

1. **主库 8/24 后未落盘**：attempts/learning_events 的新写入（若有）滞留 WAL——单人本机库风险低，但备份脚本若只拷主库会漏最近数据（供拍板：备份走 `VACUUM INTO` 或 `db.backup()` 而非文件拷贝）；
2. review_state/rubric_scores 双空表＝间隔复习与开放题评分两条链路在本库未启用（功能在、数据未生），非缺陷；
3. 首跑「7 表」与复跑「8 表」差异＝后者未排除 sqlite_internal（sqlite_sequence），口径注记防误判漂移；
4. -wal/-shm 已入 .gitignore（l918-02），status 干净。

## 三、零写库声明

`mode=ro` 连接（SELECT/PRAGMA）；主库 mtime 括号复测不变；-shm/-wal mtime 变化为只读连接的标准触碰（SQLite 打开即建伴生件），无数据变更；未 commit/push。
