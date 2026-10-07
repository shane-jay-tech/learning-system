# progress.db 取证口径守约复检（2026-10-08，l1007-20 遗留）

> 零写库（mode=ro）；隐私红线守约——只取计数/结构/sha，未导出任何行内容。

## 三口径现值 vs l1007-20（10-07）基线

| 口径 | 10-07 基线 | 10-08 复检 | 漂移 |
|---|---|---|---|
| 主库 sha8 | cd2dbce4 | **cd2dbce4** | **零漂移** |
| attempts 计数 | 15 | **15** | 0 |
| 表结构（tables 数） | 8 | **8** | 0 |

**漂移判读**：三口径逐项持平＝10-07 至今**无新学习活动**（attempts 停在 15、库字节未动）——与 l1007-25（launcher/streamlit 日志缺失＝生产 UI 未运行）、k1006-03（10 月零复测提交）三单互证：**learning 生产面使用停滞持续**。取证守约维持（本复检同样零行内容导出）。

## rg 复现

$ python -c "hashlib.sha256(open('data/progress.db','rb').read()).hexdigest()[:8]" → cd2dbce4
$ SELECT COUNT(*) FROM attempts → 15；SELECT COUNT(*) FROM sqlite_master WHERE type='table' → 8
