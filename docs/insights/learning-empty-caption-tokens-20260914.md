# 学习系统空态 caption 差异化样式 token 落点盘点（d914-36，2026-09-14，只读出稿）

命令：`grep -rn "render_empty_state" ui/ --include=*.py`（统一组件后全部空态走单一入口，检索口径=组件调用点而非散落文案）。

## 一、空态渲染点清单（13 点，file:line + 现状）

| file:line | 文案 | 形态 | 现状样式 |
|---|---|---|---|
| dashboard.py:78 | 还没有任何提交记录 | info | st.info 主题（无专属 token） |
| dashboard.py:252 | 还没有提交记录 | **caption** | st.caption 默认（无专属 token） |
| dashboard.py:341 | 还没有解锁任何成就 | info | 同上（无专属 token） |
| dashboard.py:387 | 还没有提交记录（热力图） | info | 同上 |
| dashboard.py:449 | 还没有推荐数据（漏斗） | **caption** | 同上 |
| dashboard.py:483 | 还没有进入复习循环 | **caption** | 同上 |
| dashboard.py:519 | 还没有开放题评分数据 | **caption** | 同上 |
| language.py:138 | 该专题暂无题目 | info | 同上 |
| path.py:24 | 暂无学习路径定义 | info | 同上 |
| mistakes.py:135 | 暂无可分组的弱项 | info | 同上 |
| home.py:98 | (暂无题目)（行内占位） | caption（直写） | 同上 |
| language.py:239 | (本节暂无讲解)（lesson_box 占位） | 文本参数 | 同上 |

全部空态经 `render_empty_state`（components.py:191）单点渲染——**当前没有任何空态专属 class/token**，info 档依赖 streamlit 默认主题、caption 档依赖浏览器默认，差异化无从谈起。

## 二、token 建议（名字 + 值 + 用点）

新增到 `ui/styles.py :root`（与既有 --muted/--border 同族灰阶）：

| token | 值 | 用在哪 |
|---|---|---|
| `--empty-fg` | `#8A94A6`（比 --muted #667085 浅一档的说明灰） | 空态说明文字（info 与 caption 共用文字色） |
| `--empty-action` | `var(--primary)`（复用既有主色） | 「下一步：」前缀与动作短语色 |
| `--empty-border` | `1px dashed var(--border)` | info 档空态卡片的虚线框（区分于实数据卡片的实线框） |
| `.empty-state`（class，非 var） | `padding: 18px 16px; border-radius: var(--radius-md); color: var(--empty-fg)` | info 档容器 |
| `.empty-state--compact`（修饰） | `padding: 2px 0; font-size: .8rem` | caption 档微空态 |

## 三、影响面（改动点清单，实施时才动）

1. ui/components.py render_empty_state：st.info/st.caption → `<div class="empty-state[ empty-state--compact]">` + st.markdown(unsafe_allow_html)（或 st.container(border=True) 组合）。
2. ui/styles.py：:root 加 3 个 var + 2 条 class 规则。
3. 调用点零改动（组件签名不变）。

## 四、验收自查

空态点 12 ≥3 ✓（含 2 处占位文本非组件路径，已单列）；ui/ diff=0 ✓；仅新增本报告 ✓。
