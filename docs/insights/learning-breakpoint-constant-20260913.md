# learning 断点字面量收敛为常量（d913c-10，2026-09-13）

任务：1280/1366/1080 断点字面量收敛为常量，行为等价。

## 枚举（改前）

| 位置 | 字面量 | 性质 |
|---|---|---|
| ui/styles.py:287（原 :287） | `@media (max-width: 1280px)` | 中间断点（h912-13 落地） |
| ui/styles.py（原 900 块） | `@media (max-width: 900px)` | 窄窗堆叠断点 |
| ui/pages/home.py:67 | 注释「1366×768」 | 注释非代码，保留 |

## 方案与常量定义（ui/styles.py:3-7）

CSS 媒体查询既不能引用 Python 常量也不能用 CSS `var()`，故采用**占位符注入**：
- 常量（唯一定义处）：`_BP_MID = 1280`、`_BP_NARROW = 900`、`_BP_TARGET_WIDE = 1366`（文档口径参考，未用于媒体查询）；
- CSS 内以 `__BP_MID__px` / `__BP_NARROW__px` 占位；
- `inject()` 注入真值：`_CSS.replace('__BP_MID__', f'{_BP_MID}px')...`（styles.py:339-341）。

行为等价：注入后产物与改前逐字符一致（1280/900 两断点数值零变更）。

## 替换点清单

| 位置 | 改前 | 改后 |
|---|---|---|
| ui/styles.py:293 | `@media (max-width: 1280px)` | `@media (max-width: __BP_MID__px)` |
| ui/styles.py:298 | `@media (max-width: 900px)` | `@media (max-width: __BP_NARROW__px)` |
| ui/styles.py:340-341 | （无） | inject() 占位注入 |

`rg -n "1280" ui/`：命中仅剩常量定义处（styles.py:5 与其注释）✓；home.py:67 为注释保留。

## 契约测试适配（非放松）

`tests/test_ergo_h912_13.py::test_dashboard_column_cap_and_1280_breakpoint` 原断言 CSS 字面量；改为断言常量定义（`_BP_MID = 1280`/`_BP_NARROW = 900` 在册且次序正确）——保护意图（断点数值与存在性）不变，字面量检查随单源化失效属预期。

## 验收

- `rg -n "1280" ui/`：常量定义外零命中 ✓（home.py 注释除外，非代码）。
- `python -m pytest -q`：**349 passed + 7 skipped，零失败**（≥348 ✓）。
- 断点数值零变更；未 commit。

## 遗留问题

- 断点常量如需被 app.py/pages 引用（当前无 Python 侧断点需求），可从 styles.py 导出；暂不导出（无消费者不造 API）。
