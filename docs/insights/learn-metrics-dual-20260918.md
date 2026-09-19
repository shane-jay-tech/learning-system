# generate_metrics 归仓＋183/399 题量双口径对账（2026-09-19 晨间执行班，任务 l918-07）

> 复跑命令：`python scripts/generate_metrics.py`（输出 dict 含 total_problems）。

## 一、脚本归仓

- 新增 `scripts/generate_metrics.py`：转调 `scripts/generate_system_report.py` 的 `generate_metrics()`（单一真源，不复制计数逻辑），以 JSON 输出 dict（total_problems/total_topics/paths/paths_detail/by_lang）。172e7e0 提及的命令出口就此补回仓库。

## 二、双口径对账表（2026-09-19 实测）

| 口径 | 总题数 | 知识点 | 路径 |
|---|---|---|---|
| 脚本静态枚举（generate_metrics） | **399** | **85** | **3** |
| core.loader.load_language 运行时加载（5 语言求和） | **399** | —（按题计） | — |
| README.md:52 官方口径 | 399 | 85 | 3 |

**双口径双双=399/85/3，README 数字正式可复现 ✅。**

by_lang 明细（两口径逐语言一致）：python 121／r 84／agent_dev 78／cpp 62／sql 54。

## 三、183 的归因更新（订正 9/17 报告的推断）

- 9/17 `learning-metrics-recheck` 记「load_language 仅 183 题，内容包不全」——9/19 实测 loader 已加载满额 399：**「内容包不全」状态已被 9/17→9/19 之间的内容补齐消解**（历史测量在当点成立，现值已演进）；
- 因此 README 数字维持原文的处置**歪打正着地正确**——但它现在是「已验证」而非「无法证伪」；plan.md:33 的 384/7 pytest 口径独立成立、不受影响。

## 四、结论

1. 399/85/3 三数双口径对平，README:52 无需任何订正（与 9/17 报告「不订正」结论同向，但理由升级为「已验证」）；
2. generate_metrics 出口已归仓，后续题量复核单命令可跑；
3. 本单零数据写库、未改 README/loader/报告历史件。

## 零改动声明

新增 1 脚本＋本报告；只读遍历 content/；未改 loader/README；未 commit/push。
