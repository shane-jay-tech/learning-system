# 触发器摘要升格实施判定（l1025-009 · 2026-10-26 · 零执行）

> 判据源：artifacts/l-trigger-upgrade.md（l1023-014 设计稿）。本单=就绪判定＋实施工单；零改码零 DDL 零写库。

## 一、判定：**实施就绪（荐方案 A：attempts 加列）**，无阻塞项

设计稿全部锚点按现码复核**逐项吻合、行号零漂移**：

| 锚 | 设计稿 | 实测 | 判 |
|---|---|---|---|
| judge.py:126 _error_summary | 摘要提取器 | ✓ def 位置同 | 合 |
| [:120] ×4 | :145/:148/:152/:153 | ✓ 四条返回路径逐字同 | 合 |
| judge.py:167/:304 | 反馈链入口／「运行错误：」唯一产地 | ✓ | 合 |
| ai_review.py:246/:352/:118 | review()／_offline_fallback／_trim | ✓ | 合 |
| progress.py:74-82/:200/:267 | CREATE TABLE attempts（ai_feedback :80）＋两条 INSERT | ✓ | 合 |
| corpus_trigger_check.py:20/:26 | PREFIX="运行错误："＋`LIKE ?||'%'` 判定 | ✓ | 合 |
| python_runner.py:64 | _truncate 头尾保留（l1007-02 已落地） | ✓ | 合 |
| progress.db mode=ro | attempts=0、前缀命中 0、无 stderr_full 列 | ✓ | 合 |
| SQLite 版本 | ≥3.35 支持 DROP COLUMN 硬回滚 | 3.45.3 | 合 |

载体断裂疑点（设计稿 §二）维持成立：判定域前缀「运行错误：」现码唯一产地是 UI 侧 diff_hint，落库 ai_feedback 无稳定产径——升格（判定域改锚 stderr_full 实列）是对症修法。

## 二、实施工单（另单执行，建议 1-2 单）

**单 1：库列＋写侧（核心单）**
1. `core/progress.py` `__init__` 的 executescript 段尾追加两语句（try/except OperationalError duplicate-column 容忍，幂等）：
   - `ALTER TABLE attempts ADD COLUMN stderr_full TEXT;`
   - `ALTER TABLE attempts ADD COLUMN stderr_sha256 TEXT;`
2. 写侧传参链：judge 侧 record 调用→`record_attempt_and_status`（l1012-02 原子包）＋legacy `record_attempt`（progress.py:200/:267 两条 INSERT）同步加列。取值口径：`stderr_full = getattr(run_result, "stderr", "") or None`（仅失败行非空）；`stderr_sha256 = hashlib.sha256(stderr.encode()).hexdigest()[:16]`（对齐 code_hash 16 位口径）。
3. **判分零触碰**：stderr_full 只入存储，不进 ok/passed/feedback 任何判定（l1004-02 公共护栏延续）。

**单 2：触发器双轨升格＋测试钉**
4. `scripts/corpus_trigger_check.py`：主判定域改 `passed=0 AND stderr_full IS NOT NULL AND stderr_full != ''`；ai_feedback 前缀域降级为旧行回退兼容（双轨并报）；THRESHOLD=15 不变（案 B 决议不动）。
5. 测试钉三件：①失败行写 stderr_full／成功行 NULL；②触发器新域计数＋旧行 NULL 容忍；③stderr_full 不进 UI 渲染面（防双渲染漂移）。

**验收口径**：存量行 stderr_full 恒 NULL（禁止拿 ai_feedback 猜补）；judge 侧回归全绿（_error_summary/hint_only 行为钉不松）；`pragma table_info(attempts)` 含两新列且旧读数路径零变化；回滚演练＝DROP COLUMN（3.45.3 支持）。

## 三、余量与边界

- 用户态 15 行库（l1007-22 实测面）本机不可达，触发器计数验证用仓内空库造数完成。
- 方案 B（伴生表）留案备查：仅当未来扩 stdout_full／多列诊断面时重启。
