# dashboard 三单共改·归位对账材料（l927-38，实况收窄版 · 零 git 操作）

> **卷宗**：`zcode-bridge/inbox/l927-38.task.md`（本班收口时已移 `done/`）。上游锚点＝`zcode-bridge/done/l923-11.result.md`「主班提交口径需拍板：ui/pages/dashboard.py 现由 l923-09/l923-10/l923-11 三单共同改动（累计 55 16）。按单分笔提…」。
> 🔴 **锚点已被前人闭合**：主班已于 **2026-09-23 09:57:17** 以单笔 `84d76ed`（"l923-08..11 四单合并入账"）完成入库，`55 16` 在途态在本班开工时点（09-29，porcelain 仅本班两件产出档）**已不存在 6 天**。卷宗"分笔提交清单"的判据对象消失 ⇒ 按实况把本单收窄为**归位对账材料**（不判 failed、不制造改动、不补做已消失的在途态）。**判定留人工，本班不下通过判定。**
> **本班**：`qoder-executor-20260929-0307-learn60`，只读位，读数 09-29 03:2x 现取（HEAD `6323fde`）。

## 一、在途现状（完成标准①，答案：无在途）

| 项 | 现取读数 | 命令（cwd `D:/code/learning-system`） |
|---|---|---|
| 工作树 | porcelain 只有本班自己的 `?? docs/insights/l927-34…`/`…35…` 两行，**dashboard 域 0 行** | `git status --porcelain` |
| 闭合件 | `84d76ed fix(learning): l923-08..11 四单合并入账（dashboard.py 被三单共改，累计 +55/-16）` | `git log --oneline -- ui/pages/dashboard.py` |
| 闭合件 numstat（六文件） | `core/report.py 2/1`、`tests/test_dashboard_event_failures.py 158/0`、`tests/test_dashboard_report_persistence.py 71/28`、`tests/test_import_dedup.py 177/0`、`tests/test_report_markdown_contract.py 35/8`、`ui/pages/dashboard.py 55/16` | `git show --numstat 84d76ed` |
| 闭合后追加面 | `84d76ed..HEAD` 又有 **5 笔**动过 dashboard.py（38ad3bb／5aa858a／22a5325／e9a1606／119c925）——分笔窗口物理关闭，任何"按单拆 hunk"已不可行也无必要 | `git log --oneline --format='%h' 84d76ed..HEAD -- ui/pages/dashboard.py | wc -l` |

## 二、归位对账（替代"分笔清单"的实况清单，完成标准②）

**账目恒等式复算闭合**：三单在 dashboard.py 的自报净额相加恰等于合并入账 numstat——
l923-09 `+32/−12` ＋ l923-10 `+5/−2` ＋ l923-11 `+18/−2` ＝ **55/16** ✅（自报数取各 result 档「改动清单」，入账数取 `git show --numstat 84d76ed` 首行读数）。逐单归属核对：

| 单 | 交付物 | HEAD 归位证据 | 读数 |
|---|---|---|---|
| l923-08 | `tests/test_dashboard_event_failures.py` 纯追加 | `git ls-files` 在册；定向 4 件合跑 **48 passed**（含 09/10/11 测试件） | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_dashboard_report_persistence.py tests/test_dashboard_event_failures.py tests/test_report_markdown_contract.py tests/test_import_dedup.py -q` |
| l923-09 | 导入防重（dashboard +32/−12）＋新档 177 行 | `git show --stat` 含 `test_import_dedup.py 177/0`；`git ls-files` 在册 | 同上 |
| l923-10 | caption 单源 `core.report.CALIBER_NOTE`（dashboard +5/−2）＋contract 件 35/8 | 同上在册；合跑绿 | 同上 |
| l923-11 | `_report_file_tag`（dashboard +18/−2）＋persistence 件 71/28＋`core/report.py` 注释 2/1 | `grep -n "_report_file_tag" ui/pages/dashboard.py` ⇒ def 在 **:66**（与该单自述一致未漂），消费点在 **`:301`**（该单自述 :256-260——**已漂 +45**，漂移全部来自 84d76ed 之后那 5 笔追加，属正常演化非丢失） | `sed -n '60,80p;295,310p' ui/pages/dashboard.py` |
| 基线面 | dashboard 域 6 件合跑 **68 passed / rc=0**（本单材料所依附的入库态在 HEAD 仍是绿的） | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_dashboard.py tests/test_dashboard_report_persistence.py tests/test_dashboard_event_failures.py tests/test_report_markdown_contract.py tests/test_import_dedup.py -q` |

**提交口径对账**：l923-11 卷宗给主班的两选项（按单分笔 vs 合并一笔注单号），主班实际选了**合并一笔**，且 commit body 逐单注记四段（08/09/10/11 各自改动与变异自证）＋附"同文件跨单不可拆"理由＋独立复跑全量 `731 passed/7 skipped/2 xfailed rc=0`（基线 722 净 +9）——与 l923-11 result 档自述「未 commit、未 add（交主班按精确路径代提交）」闭环。**无悬挂件、无部分入库**（六文件一次入账，`git ls-files` 全在册）。

## 三、本班未做与不该做的

- 未执行任何 git 写操作（add/commit/stash/checkout/restore 全零）；`git status --porcelain` 仅本班产出档。
- 未制造改动去"复活"已消失的在途态；未回改 l923-11／84d76ed 任何在册档。
- 84d76ed commit body 自留的两条在册遗留**仍是活的**（归位对账不等于裁决）：① 按钮文案/mime/help 全仓零覆盖（看守缺口，M-4 变异全绿）；② uploader「二次点击文件要不要消失」待裁决。二者归属 l923-* 域，是否另开单交人工/主班，本单一律不裁。

## 四、待人工清单

1. 签收本对账：确认 l927-38 以"锚点已被前人闭合（84d76ed）⇒ 收窄为归位对账"的方式闭合，无需补做分笔操作说明。
2. 84d76ed body 自留的两条在册遗留（文案覆盖缺口／uploader 裁决）去向。
3. 产出件 `docs/insights/l927-38-dash-commit-plan.md` **未自登索引** ⇒ `tests/test_insights_index_closure.py`（开工基线 3 passed）预期红，与 l927-34/35 两件产出同批由主班登索引后同笔入库。

## 五、复算配方

```bash
cd D:/code/learning-system
git status --porcelain
git log --oneline -- ui/pages/dashboard.py
git show --numstat 84d76ed | head -20
git log --oneline --format='%h' 84d76ed..HEAD -- ui/pages/dashboard.py | wc -l   # 5
grep -n "_report_file_tag" ui/pages/dashboard.py                                  # :66 / :301
PYTHONIOENCODING=utf-8 python -m pytest tests/test_dashboard.py tests/test_dashboard_report_persistence.py \
  tests/test_dashboard_event_failures.py tests/test_report_markdown_contract.py tests/test_import_dedup.py -q
```
