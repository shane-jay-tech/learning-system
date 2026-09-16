# learning 静默 except 续清批次（c-03，2026-09-13）

## 本批修复 3 处（pass → logger.debug，保留原行为只加日志）

| 位置 | 场景 | 改法 |
|---|---|---|
| core/ai_review.py:271 | 离线提示补充失败（保持主返回） | logger.debug(..., exc_info=True) |
| core/achievements.py:144 | 成就解锁事件上报失败（不影响发放） | logger.debug（补 import logging+模块 logger） |
| ui/pages/language.py:198 | lesson_viewed 事件上报失败 | logger.debug（补 import logging+模块 logger） |

## 分类留档（不动的）

- 已有哨兵：ui/components.py:20（st_ace 导入回退 _HAS_ACE 哨兵）；home.py:167（7cd3d73 已修）；dashboard.py:127/152/316（已有 logger.debug）；judge.py:144/315（已有 warning）；ai_review.py:17（导入降级哨兵 _e）、:486/:513（已有 as e 处理）。
- 全量：349 passed, 7 skipped（与基线一致，零回归）。
