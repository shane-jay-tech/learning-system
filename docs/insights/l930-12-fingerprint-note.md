# l930-12 导出缓存指纹升级记录（行数级 → 每表 COUNT＋MAX(时戳) 组合）

## 选型理由
两案对照：**组合指纹（已采）**＝单点改 `_exp_key` 一处，六表行数＋时戳 MAX 全入键；
**DAO 侧统一作废（备选，未采）**＝所有写端（含 import_json/未来写端）都要记得动作废键，
漏一处即复现 l922-104——把正确性押在 N 个调用点的纪律上。组合指纹把正确性押在
「写端刷新时戳列」这一既有事实上（mark_status/update_review_state/emit 全走
CURRENT_TIMESTAMP/ISO 现取），改动面最小、无需信任传播。

## 改动
- `ui/pages/dashboard.py` `_exp_key`：12 组件＝六表各（COUNT＋COALESCE(MAX(时戳列),'')），
  表序＝export_all 导出序（attempts/problems_status/review_state/rubric_scores/learning_events/meta；
  时戳列分别为 ts/last_attempt_ts/updated_ts/ts/created_at/updated_ts）。
- `tests/test_export_cache_hit_path.py`：镜像 expected_key 同步逐表交错 12 组件；
  组件数守卫改 `== 2×导出面表数`（原「==表数」语义被升级继承，删任一 COUNT 或 MAX 组都红）。
- `tests/test_export_cache_invalidation.py` 新增变体例
  `test_value_only_update_bumps_the_combined_fingerprint`：只改值不加行（直接 SQL 同键覆盖
  status＋显式异值 last_attempt_ts）⇒ 键必变＋导出跟上新值。

## 已知盲区（如实登记）
1. **秒级精度限制**：生产写端走 CURRENT_TIMESTAMP（秒级）——同秒内的「只改值」写入
   MAX 不变、指纹不翻（变体例首版即撞上）。属精度限制非失效；彻底解＝写端改毫秒/微秒时戳（另单）。
2. **绕时戳列的直改**：绕过生产写端直接 UPDATE 且不刷时戳列的写入仍不可见——与改前同一
   信任前提（「走生产写端」），彻底解仍是 DAO 统一作废备选案。

## 验证
三件合跑 8 passed：hit-path 3（含 2×N 守卫与镜像逐位）＋invalidation 5（例1/例2/例3
既有面全绿＋例3同键覆盖面绿＋新变体例绿）。
