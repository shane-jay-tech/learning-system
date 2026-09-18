# learning 指标数字三处一致性复核（917-35，partial）

**结论：pytest 实测 384 passed / 7 skipped 零失败（本班口径）；plan.md:33 的 376 已过期→订正为 384（保留历史值标注）。README:52 的 399 题/85 知识点/3 路径——generate_metrics 脚本缺盘＋本机内容包不全（load_language 仅加载 183 题），399 官方口径本机不可复现，维持原文不动。判 partial（题量实测受限）。**

## 一、复跑（命令与两数同段）

```
$ python -m pytest tests -q   → 384 passed, 7 skipped（2026-09-18 05:0x，4x 秒）
$ generate_metrics             → 脚本缺盘（172e7e0 提及但未随仓留存）；题量 399 本机
  经 load_language 实测仅 183 题（内容包不全）——399 官方口径无法复核，README 维持原值。
```

## 二、三处对表（文档值/实测值/是否订正）

| 处 | 文档值 | 实测值 | 是否订正 |
|---|---|---|---|
| plan.md:33 用例数 | 376 passed, 7 skipped | 384 passed, 7 skipped | ✅ 已订正（384＋历史值标注） |
| README.md:52 题量 399/85/3 | 399/85/3 | 本机内容包不全不可复现 | ❌ 不订正（维持原文，无法证伪） |
| learn-report-v065 记载 383 | 383（376+7） | 历史时点值 | ❌ 历史记载不改 |

## 三、验收情况

- ✅ pytest 384/7 实测同段；✅ 对表三列齐；✅ plan.md 订正只改数字＋日期标注（历史值保留）；✅ git diff 仅 plan.md；未 push。

## 遗留问题

题量 399 的官方复核需 generate_metrics 脚本归仓或内容包齐全后执行。
