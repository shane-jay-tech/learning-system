# learning plan.md 目标面对照：人体工学／1366 适配／键盘焦点后续——l927-04，2026-09-27

> 执行：波次 19 只读采集子班 `qoder-executor-20260927-1400-learn44`，cwd `D:\code\learning-system`。
> 时戳 `2026-09-27T13:56+08:00`。盘态：HEAD `2665f0a`、`git status --porcelain` **0 行**。
> 性质：**纯只读核对**，完成标准④「零码改动」；未改任何前端／样式／测试／配置。
> 对照的两份源档均为**在途已入库件**（`git show HEAD:<路径>` 与工作树逐字相同，因工作树 clean）。

---

## 〇、目标面口径先立住

`plan.md:4` 固化目标里的可核词条：**1366×768 适配**、**层级/行宽/留白/热区/对比度/键盘焦点/状态辨识**、
覆盖**主页、刷题、路径、诊断、面板及错题本**；`plan.md:31` 验收标准要求「**浏览器实测覆盖所有主要路由**」。
`plan.md:32` 执行结果段自述「已完成…已验证 900×768、1366×768、1920×1080，均无横向溢出」——
**该自述的证据链在盘上找不到任何一条浏览器级实测件**（见 §二 A3／B3），属静态推演冒充实测的形状。

「8 条发现」的落点不在走查档本身，而在修复批报告 `learning-ergo-fix-20260912.md` §一（h912-13，2026-09-13）。本档以该表为骨架逐条 rg／读码复验。

---

## 一、8 条逐条现状表（盘上实测）

| # | 表内原述 file:line | **盘上现位（本班复点）** | 现状 | 回写／钉子 |
|---|---|---|---|---|
| 1 | `home.py:62-75` 首屏折叠（hero／下一步／路径卡先于总览） | `ui/pages/home.py:77-90`，注释 `# h912-13：总览提到 hero/路径卡之前` 原文在世；`section_title("总览")`:78 → `_render_next_action`:89 → `_render_path_cards`:90 | **已修，未回归** | ✅ 断言在世：`test_ergo_h912_13.py::test_home_overview_renders_before_hero_blocks`（源序三比较） |
| 2 | `home.py:67/:80`＋`components.py:105/122` 卡片 HTML 无 `tabindex` 不可聚焦 | `ui/components.py:134 lang_card_html`／`:151 metric_tile`（行号漂 ＋29／＋29）；全仓 `grep -rn tabindex ui/` = **0 命中** | **仍未加固**（走查与批报告一致判「非缺陷」，本班不升判据） | 焦点可见性换了实现路线：`ui/styles.py:207-209`（button／radio／input／textarea／select）、`:214-216`（a／侧栏 a／tab／侧栏 button）、`:224-225`（expander summary）。`learn-focus-surface-audit-20260922.md:58` 已证 37 处自绘 HTML **无任何可交互元素** ⇒ 该项判定成立且被更严口径覆盖 |
| 3 | `dashboard.py:85 st.columns(min(n, 5))` 1366 挤压 | `ui/pages/dashboard.py:151-163`（原行号已漂到注释区），实现被 **l922-120** 换成 `_lang_card_rows` 3＋2 居中分行；中间断点落 `ui/styles.py:5 _BP_MID = 1280` ＋ `:300-303 stHorizontalBlock flex-wrap: wrap` | **已修，且实现换法**（`min(n, 4)` 字面量已消失，别按原断言找） | ✅ 断言随语义**等价改写**（非放宽）：`min(n, 5)` 不得回归 ＋ 机械扫字面量 `st.columns(...)` 槽位 ≤4 ＋ 纯函数 `_lang_card_rows` 排 3+2／末行补等宽空槽／权重和恒 3 ＋ 新增「取模叠卡 `i % len(cols)` 不得回归」。另 d913c-10 把断点数值收敛为常量单源 |
| 4 | `dashboard.py:124` except 静默（推荐展示） | `:204-205 logger.debug("dashboard: 推荐展示数据异常", exc_info=True)` | **已修** | ✅ `test_dashboard_no_silent_except`（正则钉 `except Exception:\s*\n\s*pass` 必须为空 ＋ logger 初始化 ＋ `logger.debug(` ≥3，现值 4） |
| 5 | `dashboard.py:149` except 静默（事件上报） | `:229-230 logger.debug("dashboard: 推荐事件上报异常")` | **已修** | 同上 |
| 6 | `dashboard.py:311` except 静默（跨路径推荐，走查未列、批内补获） | `:417-418` ＋ `:443-446` 两处 `logger.debug` | **已修** | 同上；dashboard 现 5 处 `except Exception`，第 5 处 `:355 except Exception as exc:` → `render_error_notice`（显式错误态，非静默） |
| 7 | `mistakes.py` 移除弱项无二次确认 | 现 `ui/pages/mistakes.py` 操作按钮只有 `:137 复习 →`／`:159 再做 →`／`:198 练习 →`，**无「移除」按钮**；`:147` 文案「重做通过后就能移除」 | **销项维持**（随代码演变自然闭合） | 无需钉子；本班逐行 rg 复点确认，非引用旧结论 |
| 8 | `mistakes.py:113` 上次点评 expander 默认折叠 | `ui/pages/mistakes.py:165 with st.expander("上次代码与点评"):` **仍默认折叠** | **仍开放**（待产品拍板，走查即注明非缺陷） | 无断言。对照面：`path.py` 侧的 expander 展开组合逻辑**已有桩**（`tests/test_path_focus_expand.py`，3 条 `expanded` 断言）⇒ 同类问题在一处有钉子、错题本这处没有 |

**计数小结**：8 条中 已修 5（#1/#3/#4/#5/#6）＋ 自然销项 1（#7）＋ 维持非缺陷 1（#2）＋ 仍开放 1（#8）。**零回归**。

### 1.1 表外新发现（本班核对时撞见，登记不修）

- **走查的第 9 项被 8 条表漏掉**：`learning-ergonomics-scan-20260911.md` home 段第 3 条
  「`home.py:162 except Exception:` 静默吞错」**没进** h912-13 的 8 行表（表＝home 2 ＋ dashboard 4 ＋ mistakes 2）。
  盘上现状：已修 —— `ui/pages/home.py:177-178 except Exception: → logger.debug("home: ai_pulse 时间戳解析失败，按 9999…")`，
  home.py 全文仅此 1 处 except。修它的批次是 **p912-39**，钉子是 `test_ergo_h912_13.py::test_home_days_since_exception_logged`（docstring 自述「p912-39 遗留核销」）。
  ⇒ 「8 条」这个数字与走查档的 9 个编号项**本就对不上**（走查另 2 项判为无缺陷／正面项），后续引用者别再按「8 条＝走查全部发现」理解。
- **`tests/test_ergo_h912_13.py:63-68` 与 `:69-74` 是逐字重复的断言块**（同一 `styles = STYLES.read_text(...)` ＋ 3 条 `_BP_MID`／`_BP_NARROW` 断言写了两遍）。
  恒绿、零增量、误导读者以为有两条不同把守；成因疑为 l922-120 改写断言时的粘贴残留。**本班未删**（判据④零码改动）。

---

## 二、两栏清单

### A. 已修未回写（代码跑了、文档口径没跟上——按档复算会踩空）

| # | 事实 | 证据 |
|---|---|---|
| A1 | 两份人体工学档的**行号全面漂移**且无「行号已漂」标注 | scan：home `162`／fix 表：home `62-75`、dashboard `85/124/149/311`、mistakes `113`、components `105/122` ⇒ 盘上实值 `177-178`、`77-90`、`151-163/204/229/417`、`165`、`134/151` |
| A2 | `min(n, 4)` 这个「修复②的实现」已不存在（被 l922-120 的 3＋2 分行替掉），但 `learning-ergo-fix-20260912.md:21` 仍写「`st.columns(min(n, 5))` → `min(n, 4)`」为终态 | `grep -n "st.columns(min\|min(n," ui/pages/dashboard.py` 只命中注释行 `:151`；断言侧已同步（见 #3），**只有批报告没同步** |
| A3 | 🔴 **「本机无 Playwright」这条阻塞口径已失效，但三档都在用它延后工单**：`learning-ergo-diag-path-1366-20260913.md:35`、`learn-dashboard-768-fold-budget-20260922.md`（缘起段＋「⚠️ 本档未经自动验证」）、`learn-focus-surface-audit-20260922.md:152 F-5`（原文「本机无 Playwright/Selenium，仓内 requirements.txt 无相关依赖」） | 本班现点：`import playwright` OK（`D:\Program\Lib\site-packages\playwright\__init__.py`）；`sync_playwright().chromium.launch()` **成功，版本 151.0.7922.34**；`requirements-freeze.txt:109 playwright==1.62.0`。⇒ **plan.md 验收标准「浏览器实测」的工具前置已就位**，缺的只是写测试的人。附带缺陷：`requirements.txt`（真依赖清单，尾段只有 streamlit-ace／pywebview／pandas／numpy／scipy／sklearn／matplotlib／pytest／pytest-cov）**不含 playwright** ⇒ 按 requirements.txt 重建的环境会缺它，F-5 那半句「requirements.txt 无相关依赖」其实没说错，错在由此推出「本机不能跑」。追加口径：`git log -1 -- requirements.txt` = `57dfb21`（该文件长期未收录 playwright）、`git log -1 -- requirements-freeze.txt` = `0330dfb`（l918-09「刷新至本机现况 62→195 行」）⇒ freeze 档是**本机 pip 快照**而非声明依赖，playwright 的存在属「本机恰好装了」，不属「项目声明要装」——S1 落笔前须先把这点定成人工裁决 |
| A4 | F-1（expander summary 焦点环）已实装，但提出它的档仍标「仍未实装」 | `ui/styles.py:221-225` 有 `[data-testid="stExpander"] summary:focus-visible` ＋ 注释回指 `learn-focus-f1-outline-static` 档；而 `learn-focus-surface-audit-20260922.md:160` 状态行仍是「建议…仍未实装」，`:169` 还写着「请人工或后续单落笔」把回写推给下游 ⇒ 该单已交付、无人回执 |

### B. 仍开放（真缺口，不含已被 A 类掩盖的假缺口）

| # | 项 | 严重度 | 备注 |
|---|---|---|---|
| B1 | #8 错题本 expander 默认折叠 | 低（产品拍板类） | 8 条里唯一从走查活到今天的原判据项；拍板后需配源级断言（可仿 `test_path_focus_expand.py`） |
| B2 | 实机 1366×768／1920×1080 溢出与焦点环重叠**目检** | **中** | A3 解除阻塞后，这是**当前最高收益的人体工学缺口**；`learn-dashboard-768-fold-budget-20260922.md` 自己列了 4 个「必须靠 Playwright 校准的假设点」，至今一个没校准 |
| B3 | `plan.md:32` 自述「已验证 900／1366／1920 均无横向溢出」无实测支撑 | **中** | 现 `tests/` 里 `grep -rln playwright tests/` = **0 命中**；只有 `test_app_flow.py`／`test_app_route_fallback.py` 用 `streamlit.testing`（AppTest 进程内，无像素／无布局引擎）。⇒ 文档结论强于证据 |
| B4 | #2 卡片 `tabindex` 可选加固 | 极低 | 维持走查判定；仅当卡片内将来嵌链接才升级为缺陷 |
| B5 | F-2 热力图 `title` 仅 hover 可达（`dashboard.py:446` 一带） | 信息项 | 上游建议并入「首屏动作出口」人工裁决批，本班不改判 |
| B6 | 走查未覆盖面的残余：**深层 expander 内交互** | 低 | 诊断／路径／语言／侧栏本体已由 d913c-01 补走查（`learning-ergo-diag-path-1366-20260913.md` 矩阵 6 处列布局全 ≤2 列 ✓），深层项原档明写留下一批、至今无批 |
| B7 | `test_ergo_h912_13.py:69-74` 重复断言块 | 低（卫生类） | 见 §1.1；删除即闭合，无行为影响 |

---

## 三、后续切片建议（按 §5 只出建议、一律未实施；粒度对齐源档的「≤40 分钟」刻度）

| 序 | 切片 | 为什么排这个位置 | 最小改动面 | 风险／回滚成本 |
|---|---|---|---|---|
| **S1** | **Playwright 浏览器冒烟档**：1366×768 与 1920×1080 两视口 × 6 条主路由（home／path／diagnostic／language／dashboard／mistakes），首条断言只用 `document.documentElement.scrollWidth <= viewport.width` | B2／B3 同源、A3 刚解除阻塞、`plan.md:31` 验收标准里唯一从未被满足的一条 | 纯新增 `tests/test_browser_smoke_*.py` ＋ `requirements.txt` 补 `playwright>=1.62,<2` | 🔴 两处必须防：① **恒绿形状**——本机有、CI／新检出没有 ⇒ 必须 `pytest.importorskip("playwright")` 并在缺件时**显式 skip 计数**，否则造出「绿但零覆盖」；② 首屏像素断言脆弱，先只钉 scrollWidth 一条，别一上手钉高度 |
| **S2** | **口径回写批**（纯文档，零码）：A1 行号对照表 ＋ A2 终态更正 ＋ **A3 三档的 Playwright 口径改写** ＋ A4 的 F-1 回执 | A3 是**会传染的错**：只要它还写着「本机无 Playwright」，后续任何浏览器单都会被它劝退 | 4 份 .md 各 1–3 行 | 极低；注意 `learn-insights-index-20260918.md` 有真闭合哨兵，**改文档行不新增档**才不动 A==B 等式（本档即按此纪律只新增 1 份并交主班代登） |
| **S3** | #8 expander 展开口拍板 → 落地 ＋ 源级断言 | B1 是 8 条表唯一残项 | 1 行页面参数 ＋ 仿 `test_path_focus_expand.py` 的录制桩 1 例 | 低；**属产品裁决**，执行班不得代拍（本档只列出口） |
| **S4** | 删 `test_ergo_h912_13.py:69-74` 重复块 | B7 卫生项，顺路做 | −6 行 | 零；跑 `-k ergo` 定向复跑即可证 |

> S1 与 S2 的顺序**不能反**：先回写 A3 再排 S1，否则 S1 的卷宗会带着「工具不具备」的错误前提被规划班否掉。

---

## 四、零改动声明（完成标准④）

只读命令集合：`grep`／`sed -n`／`ls`／`git rev-parse`／`git status --porcelain`／`git show`／`python -c "import playwright…"`（含一次 `chromium.launch()`，无网络、无写盘、无 UI 交互）。
未改任何 `ui/`／`core/`／`tests/`／`plan.md`／`README.md`／样式／判分逻辑／资源限制与沙箱参数；未 `add`／`commit`／`stash`／`checkout`／`restore`／`clean`／`push`；未装依赖（playwright 为**既有安装态**，本班只做 import 与 launch 探测）。
唯一净新增文件＝本档。产物**不代登 insights 索引**（本仓有真闭合哨兵 `tests/test_insights_index_closure.py`，索引由主班收班单点写）。
