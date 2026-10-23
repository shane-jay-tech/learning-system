# l1023-014 触发器摘要截断升格材料（stderr 全量列入 attempts·DDL 草案——零执行）

- 上游锚点复核：l1012-01 遗留#1 原文在档（「触发器现以摘要前缀代理，语料密度比对精度受摘要 120 字符截断约束——升格属另单」）；l1004-02 案 2 本体复核发现**已由 l1007-02 落地**——python_runner.py:64 `_truncate` 已改头 60%＋尾 40% 头尾保留（原「头切」描述漂移，按磁盘实况修正留痕）。即：**头尾保留形态的 stderr 全量在 `run_result.stderr` 已可得，缺的只是库内承接列**。
- 本单为材料单：零改码、零执行 DDL、零写库（progress.db 仅 mode=ro 读证）。

## 一、摘要代理点定位（file:line＋截断证据）

| # | 位置 | 角色 |
|---|---|---|
| 1 | core/judge.py:126 `_error_summary`（l1004-02 时为 :118-142，行号漂移已按现值修正） | stderr→单行摘要提取器；**[:120] 截断 4 处＝:145、:148、:152、:153**（*Error* 行优先／error: 行优先／末行兜底三径全部截 120） |
| 2 | core/judge.py:167 `_row_feedback` | `base = detail if detail is not None else _error_summary(stderr)`——摘要进反馈链的入口 |
| 3 | core/judge.py:304 `diff_hint = f"运行错误：{_row_feedback(lang, case_run)}"` | **「运行错误：」前缀唯一产地——但 diff_hint 是 JudgeResult UI 侧字段，不落库** |
| 4 | core/ai_review.py:246 `review()` | 落库 ai_feedback 的实际来源＝LLM 回复或 `_offline_fallback`（:352，「AI 点评暂时不可用…」开头）；prompt 内 stderr 另受 `_trim(stderr, 800)` 二级约束 |
| 5 | core/progress.py:74-82 `CREATE TABLE attempts` | ai_feedback TEXT 单列（:80），无 stderr 全量列 |
| 6 | core/progress.py:200 / :267 | 两条 INSERT 写入点（record_attempt_and_status 原子包 l1012-02／legacy record_attempt） |
| 7 | scripts/corpus_trigger_check.py:17,:20,:26 | 触发器：THRESHOLD=15；`PREFIX="运行错误："`；`ai_feedback LIKE '运行错误：%'` 判定域（l1012-01） |

**截断证据（现码原文）**：judge.py:145 `return l[:120]`、:148 `return l[:120]`、:152 `return meaningful[-1][:120]`、:153 `return lines[-1][:120]`——四条返回路径无一保留全量；单行摘要进库后，多行 traceback 的其余行（重编结果集所需语料）永久丢失。

## 二、新发现：判定域载体断裂疑点（只读观察，不改码）

- 触发器判定域键在 attempts.ai_feedback 前缀「运行错误：」（corpus_trigger_check.py:20,26），但该前缀现码唯一产地是 judge.py:304 的 **diff_hint（UI 字段）**；落库 ai_feedback 走 review()（LLM 文本或「AI 点评暂时不可用…」兜底），**现码无任何路径稳定产出该前缀**（ai_review.py 全文零命中，system prompt 无此前缀约定，tests 仅直接 seed 库行不经写侧）。
- 即：触发器现值 0/15 除语料未积累外，还存在**判定域载体可能永远计不到数**的结构性疑点——l1007-22 §二「经 _row_feedback 进 diff_hint/feedback 写入 attempts.ai_feedback」的 feedback 半句与现码不符（diff_hint 半句成立）。此疑点进一步支持升格方向：判定域改锚 stderr_full 实列，不再代理 ai_feedback 前缀。
- 佐证读数：data/progress.db（mode=ro）attempts 总数 0、前缀命中 0（仓内库为空库；l1007-22 实测的 15 行库在用户态，本单不可达——按只读纪律留痕不追）。

## 三、DDL 草案（**零执行**，落地属另单）

### 方案 A（荐）：attempts 加列（ALTER 扩展，零重建）

```sql
-- 迁移 001（建议入 core/progress.py 的 executescript 初始化段＋try/except 重复列容忍）
ALTER TABLE attempts ADD COLUMN stderr_full TEXT;      -- runner 头尾保留策略处理后的 stderr 原文；passed=1 或无 stderr 时存 NULL
ALTER TABLE attempts ADD COLUMN stderr_sha256 TEXT;    -- 16 位截断 hex（对齐 code_hash 口径）：完整性校验＋密度比对去重辅助
```

- 理由：SQLite `ALTER TABLE ADD COLUMN` 为元数据操作，零表重建零锁表风险；与 l1012-02 原子包（record_attempt_and_status）同事务写入即可，多一列不多一次往返。
- 代价：attempts 行宽增加，但 stderr_full 仅失败行非空（现库失败率低），可接受。

### 方案 B（备）：独立伴生表（attempts 保持瘦）

```sql
CREATE TABLE IF NOT EXISTS attempt_stderr (
  attempt_id INTEGER PRIMARY KEY REFERENCES attempts(id) ON DELETE CASCADE,
  stderr_full TEXT NOT NULL,
  stderr_bytes INTEGER NOT NULL,
  captured_ts TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_attempt_stderr_nonempty ON attempt_stderr(attempt_id);
```

- 适用面：若未来 stderr_full 要扩到 stdout_full／多列诊断面，伴生表可独立膨胀；当前单列需求下方案 A 更省一笔 JOIN。

### 共同迁移考虑（写进另单验收口径）

1. **存量行不可回填**：历史 attempts 无 stderr 全量（只在当次进程内存里存在过）——stderr_full 恒 NULL；新列语义必须「NULL＝无全量数据（旧行）」，密度比对仅对新行生效，禁止拿 ai_feedback 摘要猜补。
2. **写侧改动面**：judge.py `_record_attempt`→`record_attempt_and_status` 传参链加 stderr_full（来源 `getattr(run_result, "stderr", "") or None`，失败行才非空）；`core/progress.py` 两条 INSERT 语句与参数同步；**判分零触碰**（stderr_full 只入存储，不进 ok/passed/feedback 任何判定——l1004-02 公共护栏延续）。
3. **触发器同步升格**：corpus_trigger_check.py 判定域改双轨——`passed=0 AND stderr_full IS NOT NULL AND stderr_full != ''`（新域）为主，ai_feedback 前缀域降级为旧行回退兼容；阈值 15 不变（案 B 决议不动）。
4. **回滚**：方案 A 两列可留库休眠（可空列无读取方即零行为影响）；SQLite ≥3.35 亦支持 `ALTER TABLE ... DROP COLUMN` 硬回滚。
5. **测试钉建议（另单）**：① record 路径失败行写 stderr_full／成功行 NULL；② 触发器新域计数＋旧行 NULL 容忍；③ stderr_full 与 UI stderr_block 渲染面分离（列不进 UI，避免双渲染漂移）。
6. **与 l1004-02 案 2 的关系更正**：案 2（头尾保留）已落地（python_runner.py:64-72，l1007-02），本 DDL 是其「另列入 attempts」的库内承接半；落地批次须带 judge 侧回归（_error_summary/hint_only 行为钉，l1004-02 遗留#1 同口径）。
