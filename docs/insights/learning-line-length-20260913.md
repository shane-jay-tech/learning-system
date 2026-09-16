# learning 长文本区行宽收敛 ≤80ch（d913c-08，2026-09-13）

任务：纯段落文本渲染容器加 max-width ≈80ch（设计系统常量表达），不改字号层级。

## 改动（ui/styles.py，纯 CSS 两处）

1. `:root` 新增常量 `--measure: 80ch;`（:22）——阅读测宽设计 token；与既有 hero 副标题 `max-width: 72ch`（:127）同族（正文取 80ch、短引导取 72ch）。
2. 长文本容器收口（:237-239 新增规则）：`.lesson-box, .ai-feedback { max-width: var(--measure); }`——课程讲解正文（lesson_box）与 AI 点评（ai_feedback_block）两类纯段落容器限宽 80ch。
   - `io-box`（代码/stderr 输出）**不设限**：代码行宽受内容支配，强行 80ch 会截断或换行破坏可读性——属「纯段落文本」范围外。

## 验收

- `rg -n "max-width" ui/styles.py`：命中 :42（全局画布 1440px，既有）、:127（hero 72ch，既有）、**:239（本批 --measure）**——落在长文本容器 ✓。
- `python -m pytest -q`：**349 passed + 7 skipped，零失败**（≥304 ✓）。
- 内容文本零变更、字号层级零变更、零新依赖、未 commit。

## 遗留问题

- lesson-box 内嵌代码块继承 80ch 容器宽：如实测感觉代码行过挤，可对 `.lesson-box pre` 单独放宽（`calc(80ch + 8rem)` 类方案），留浏览器实测批决策。
- 1366/窄窗下的实际换行观感归日间浏览器实测批（与 c-06/c-02 目检合并）。
