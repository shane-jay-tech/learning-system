# learning 人体工学走查修复批报告（h912-13，2026-09-13 夜班）

任务：走查报告 8 条发现建表，跳过已覆盖 2 条，可动集修复 ≥3 条＋每条断言。

## 一、8 条状态表

| # | file:line | 一句话 | 状态 |
|---|---|---|---|
| 1 | home.py:62-75 | 首屏折叠：hero/下一步/路径卡先于总览渲染，768 高度首屏不见数据 | **本批已修①** |
| 2 | home.py:67/:80（components.py:105/122） | 卡片 HTML 无 tabindex 不可聚焦 | 走查已判「可接受非缺陷」（卡片无内嵌操作，按钮原生可聚焦）——不动 |
| 3 | dashboard.py:85 | 1366 断点：5 列挤压 | **本批已修②**（任务书称已覆盖，磁盘实证未落，见三） |
| 4 | dashboard.py:124 | except 静默（推荐展示） | **本批已修③**（同上，未落盘） |
| 5 | dashboard.py:149 | except 静默（事件上报） | **本批已修③** |
| 6 | dashboard.py:311 | except 静默（跨路径推荐） | **本批已修③**（走查未列，本批复扫补获） |
| 7 | mistakes.py | 移除弱项无二次确认 | **发现失效**：现行页面已无移除按钮（只有 再做→），随代码演变销项 |
| 8 | mistakes.py:113 | 上次点评 expander 默认折叠 | 属产品拍板（走查已注明非缺陷）——待拍板 |

## 二、修复内容（file:line＋diff 摘要）

- **① 首屏顺序**（ui/pages/home.py:62-75）：`section_title("总览")`+四列 metric_tile 提到 `_render_next_action`/`_render_path_cards` 之前，hero/路径卡后移。文案与数据零改动，仅分区顺序。
- **② 断点**（ui/pages/dashboard.py:86）：`st.columns(min(n, 5))` → `min(n, 4)`；ui/styles.py 在 900px 块前插入 `@media (max-width: 1280px)`（stHorizontalBlock 允许 wrap）——补齐 1024–1280 无中间断点缺口。
- **③ 异常不再静默**（ui/pages/dashboard.py）：新增 `logger = logging.getLogger(__name__)`；三处 `except Exception: pass`（:124/:149/:311）→ `logger.debug("dashboard: <场景>异常", exc_info=True)`——debug 级不污染 UI 但可排障（任务书示例口径：必须记录日志）。

## 三、与任务书「已覆盖 2 条」的出入（磁盘实证）

任务书称 dashboard:85 断点与三处 except 已被第一批覆盖——**磁盘实证未落**（改前 grep：`min(n, 5)` 在位、三处 `except Exception: pass` 在位）。按「磁盘是唯一事实源」纳入本批修复（恰好都是任务优先类：布局/状态辨识）。

## 四、断言与测试（tests/test_ergo_h912_13.py，3 条）

- test_home_overview_renders_before_hero_blocks：总览 < 下一步 < 路径卡（源序断言）
- test_dashboard_column_cap_and_1280_breakpoint：`min(n, 4)` 在位、`min(n, 5)` 不在位、styles 1280 块存在且先于 900 块
- test_dashboard_no_silent_except：正则扫 dashboard 无 `except Exception: pass`、logger 初始化在位、logger.debug ≥3 处

## 五、测试基线与复跑

- 命令（仓内 pytest.ini：testpaths=tests）：`python -m pytest -q`
- 基线：**345 passed, 7 skipped**；改后：**348 passed, 7 skipped**（+3 即本批断言，零回归）。

## 遗留问题

- #8 expander 默认展开与否待产品拍板。
- 走查未覆盖面（诊断页/路径页/语言主页/侧栏本体）留下一批；实机 768 滚动验证留 Playwright 就绪后。
- home 键盘聚焦加固（tabindex+:focus-visible）属可选加固，未做（走查判非缺陷）。
