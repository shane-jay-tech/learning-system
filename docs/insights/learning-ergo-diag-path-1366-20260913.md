# learning 诊断/路径/语言/侧栏 1366 适配走查（d913c-01，2026-09-13）

任务：按 a56be3d 既有改法（列数上限 4＋1280 断点）收敛诊断/路径/语言/侧栏中列数 >4 或宽度溢出 1366 的处。

## 走查矩阵（目标四页全量列布局点）

| 位置 | 布局 | 列数 | 1366 判定 |
|---|---|---|---|
| ui/pages/diagnostic.py:52 | st.columns(2) | 2 | ✓ |
| ui/pages/path.py:62 | st.columns([4, 1]) | 2 | ✓ |
| ui/pages/language.py:155 | st.columns([1, 5]) | 2 | ✓ |
| ui/pages/language.py:162 | st.columns([3, 2], gap=medium) | 2 | ✓ |
| ui/pages/language.py:214 | st.columns([38, 62], gap=medium) | 2 | ✓ |
| ui/pages/language.py:242 | st.columns(2) | 2 | ✓ |
| ui/pages/language.py:277 | st.columns([2, 1, 2]) | 3 | ✓ |
| ui/pages/language.py:334 | st.columns(2) | 2 | ✓ |
| ui/pages/language.py:361 | st.columns([1, 2, 1]) | 3 | ✓ |
| ui/pages/language.py:414/:480/:534 | st.columns([1, 1, 3]) | 3 | ✓ |

## 结论：零改动需要（收敛已在往批达成）

- **列数上限**：四页最大列数 = 3 ≤ a56be3d 上限 4；全仓 `st.columns(4)` 4 处均在非目标页且 = 4 上限合规。
- **宽度溢出**：四页零固定像素宽（`width=<n>` 0 命中）；`use_container_width=False` 仅 2 处（home.py:110、path.py:94 的「打开错题本/返回列表」紧凑按钮），属有意的短按钮形态，1366 下无溢出。
- **断点**：1280px 中间断点与窄窗规则已在 ui/styles.py（a56be3d/h912-13 落地），本次无需追加。
- 溢出面的大头（代码编辑器 io_block、长代码块）已由往批的 stderr_block/io_box 样式处理。

## 验收

- `python -m pytest -q`：**349 passed + 7 skipped，零失败**（≥304 基线 ✓，未下降）。
- 生产码零 diff（走查未发现违规点，无「改前/改后」对可列——逐处现状已列矩阵）。
- 未 commit；零新依赖。

## 遗留问题

- 实机 1366 目检（与 768 窄窗）仍需 Playwright/真人过一遍，归日间浏览器实测批次（0913-0620-06 同款遗留，条目 8 expander 展开口亦仍待产品拍板）。
- 若后续语言页新增 >4 列布局，建议直接复用 a56be3d 的 min(n, 4) 辅助而非散写。
