# learning 侧栏 218px 降级验收余项核验（n915-66，只读）

- 任务：n915-66-learn-sidebar-218-verify（created 2026-09-15T23:39:01，cwd learning-system，软预算 ≤25 分钟）
- 执行：sweep-20260915-2300（GLM-5.3-Flash），2026-09-16 03:0x
- **结论：已落地部分在册且全量绿；「验收余项」实质已消化。**

## 一、已落地 / 验收余项两栏

**已落地（在册证据）**：
- `ui/styles.py:321`——`section[data-testid="stSidebar"] { width: 218px; min-width: 218px; }`（d913c-12 侧栏 218px 降级主体，7 导航入口零删除）。
- 全量回归 **368 passed / 7 skipped**（≥ d913c-12 自述 349 基线；差 19＝后续批次新增测试）。

**验收余项**：
- 浏览器目检（1280px 宽度下的实际渲染）——夜里无法起浏览器目检，属日间动作；验收命令＝日间起 server 后 `streamlit run app.py` 于 1280px 视宽目检侧栏宽度与 7 导航完整。
- 断点带语义测试（若存在）——`rg -n "218" tests` 无独立断言文件；现有 UI 行为测试（test_ui_behavior.py）随全量绿。

## 二、复跑命令与 passed 数（同段）

```
cd D:/code/learning-system && python -m pytest tests -q
→ 368 passed, 7 skipped in 35.87s（全量，含 UI 行为测试）
rg -n "218" src → ui/styles.py:321（唯一命中=降级规则本体）
```

## 三、声明

未改 UI 代码（源码零改动）；不 push。

## 遗留问题

浏览器目检余项留日间（命令已给）；代码与测试侧无遗留。
