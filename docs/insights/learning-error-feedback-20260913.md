# learning 错误提示统一 formatter（d913c-07，2026-09-13）

任务：定义统一提示函数（标题＋原因＋下一步动作三要素），≥3 处散落 st.error 收口，保留触发条件与文案事实。

## 交付

**统一函数**：`ui/components.py::render_error_notice(title, reason="", next_action="")`（:177）——三要素排版：**标题** ＋ 原因：… ＋ 下一步：…（reason/next_action 可省略）；页面级 st.error 今后一律收口于此。

**收口 6 处**（≥3 ✓，全部保留原触发条件与 return 语义，事实内容不变、仅补三要素结构）：

| 位置 | 原文案 | 三要素化 |
|---|---|---|
| app.py:105 未知路由 | `未知路由：{route}` | 标题=未知路由；原因=route 无对应渲染器；下一步=侧边栏重选 |
| ui/pages/dashboard.py:243 导入失败 | `导入失败：{exc}（当前数据未受影响）` | 标题=导入失败；原因={exc}；下一步=数据未受影响可重试 |
| ui/pages/path.py:85 路径不存在 | `路径 {path_id} 不存在。` | 标题=路径不存在；原因=path_id 不在路径表；下一步=回主页或重生成 |
| ui/pages/language.py:94 未知语言 | `未知语言：{lang}` | 标题=未知语言；原因=不在 LANG_META；下一步=回主页重选 |
| ui/pages/language.py:100 题库缺失 | `未找到 {name} 的题库内容。` | 标题=题库内容未找到；原因=尚无内容；下一步=先生成或另选 |
| ui/pages/language.py:244 AI 出题失败 | `AI 出题失败，请稍后再试。` | 标题=AI 出题失败；原因=模型调用暂不可用；下一步=稍后再试/先用原题 |

home.py 的两处 st.error（公开部署安全提示、季度深查提醒）属**通知类**非错误反馈，按语义保留原样不入本次收口。

## 测试适配（行为等价，非放松断言）

3 个既有 UI 行为测试经页面模块 st 假件断言错误输出；formatter 引入 ui.components 间接层后，为 3 测试补 `monkeypatch.setattr(components, "st", fake)` 同一假件注入（含 unknown-route 测试体内的二次假件）——断言内容不变（`"未知路由" in msg` 等全过），注入点升级。

## 验收

- `rg -n "def .*error.*msg|def .*notify" src`：ui/ 下组件函数命名制——`render_error_notice` 定义 1 处（ui/components.py:177）、调用点 6 处 ✓（app.py/ui 下的 rg 口径等价核验，src/ 目录本仓不存在，实际布局为 app.py+ui/+core/）。
- `python -m pytest -q`：**349 passed + 7 skipped，零失败**（≥304 ✓；修前 346 passed+3 failed，3 个失败系 formatter 间接层的测试注入点问题，已按上述方式修复）。
- 未 commit；触发条件与文案事实零变更。

## 遗留问题

- 其余散落 st.warning（月度浅扫提醒等通知类）如需统一，可另立 render_notice_notice 双形态函数，留下批。
- FakeStreamlit 的 calls 记录对 markdown/error 均捕获，后续页面接入 formatter 时测试只需补 components 假件注入一行。
