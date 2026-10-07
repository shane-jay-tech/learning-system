# legacy-api-guard 删旧批前置观察窗核（2026-10-08，l1007-07 遗留 1）

> 零改码。guard 上线＝commit 340215b（2026-10-07 06:15，l1006-03 全落批随笔）。

## 一、上线时点与观察窗

| 项 | 读数 |
|---|---|
| guard 上线 | **2026-10-07 06:15**（340215b，l1006-03 批）——**至本档仅 ≈1 天** |
| 主班建议窗 | 1-2 周生产日志零命中即可派删旧批 |
| 窗状态 | **未满**（1 天 < 7 天下限） |

## 二、生产日志命中计数

| 日标 | 存在性 | 命中 |
|---|---|---|
| `data/launcher.log`（RotatingFileHandler 3×1MB） | **不存在** | — |
| `data/streamlit.log` | **不存在** | — |
| `~/.psy_analysis/`（用户数据域） | 无 .log | — |

**命中计数＝0，但证明力受限**：两日志文件双双不存在＝**生产 UI 进程（launcher/streamlit 主路）自 guard 上线后未见运行痕迹**（attempts 15 行含 (stub)×3＝测试/脚本写入，非真用户流）——「零命中」当前是「零运行」的同义语，不能当「生产零调用」证据。

## 三、结论：**观察继续（未满）——删旧批暂不派**

- 观察窗实际起算应从**生产 UI 首次运行日**起（launcher.log/streamlit.log 首次落盘）——当前从未起算。
- 建议到期核：**生产 UI 运行 ≥1 周后**复查 `grep -c "legacy-api-guard" data/launcher.log data/streamlit.log`——零命中即满足主班条件，可派删旧批（record_attempt/mark_status 两 legacy 函数 + guard 块同笔删）。
- 附带发现：launcher/streamlit 日志文件缺失＝**应用自上次部署后未再启动**（或启动方式绕过 launcher 日志 init）——与「10 月零复测提交」（k1006-03）、ai_feedback 零 Traceback（l1007-22）同指向**学习系统生产面使用停滞**，三单互证，晨报可合并点名。

## rg 复现

$ git log -S "legacy-api-guard" --format="%h %ad" --date=iso -- core/progress.py | tail -1 → 340215b 2026-10-07
$ ls data/launcher.log data/streamlit.log → 均不存在
$ grep -c "legacy-api-guard" data/*.log → 无文件可 grep
