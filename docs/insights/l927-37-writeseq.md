# 跨路径区曝光写序换 A2（emit 先、成功后落本地账）：l927-37，2026-09-28

> 执行：波次 43 代码写位子班 `qoder-executor-20260928-0300-learn54`，cwd `D:\code\learning-system`。
> 盘态：开班现取 HEAD `22a5325`、`git status --porcelain` **0 行**（与横幅一致）。
> 卷宗：`zcode-bridge/inbox/l927-37.task.md`（做什么＝"按档内预置断言（例B④／例C）换序：
> add 成功后再记 impressions、emit 前置条件齐备，两断言翻绿"）。
> 上游档：`done/l923-07.result.md`（遗留问题 1 点名这两格靶子）、
> `done/l923-06` 设计稿 `docs/insights/learn-shown-writeorder-design-20260923.md`（A2 案的出处）、
> 兄弟单 `outbox/l927-29.result.md`＋`docs/insights/l927-29-note.md`（同族写序面，本单没碰它翻过的点击侧）。

---

## 一、改了哪些行、为什么（生产码一块，20 增 8 删）

`ui/pages/dashboard.py` `_render_cross_recommend` 的曝光记账循环（现值 `:409-441`）：

| 现值行号 | 内容 |
|---|---|
| `:430-432` | `rec_id = _make_rec_id(...)` ＋ `payload = {...}` **提到 try 外**＝卷宗说的「emit 前置条件齐备」 |
| `:433 try` → `:434-435` | `dao.emit_event("recommendation_shown", …, payload=payload)` —— **先送达** |
| `:436` | `st.session_state[cross_shown_key].add(pid_key)` —— **emit 成功了才记 shown** |
| `:437-439` | `impressions_key[(lang, pid, "cross_path")] = {…}` —— **add 成功后再记 impressions** |
| `:440 except` → `:441` | `logger.debug("dashboard: 跨路径推荐展示异常", exc_info=True)`，per-item try 粒度不动（l923-07 的形态） |

为什么：旧写序把两件本地账写在送达**之前** ⇒ 失败那条已进 `_cross_rec_shown_ids`，下一帧被
`if pid_key not in …` 门控整条跳过 ⇒ 该条曝光**永久丢失且不自愈**，本地口径与 `learning_events`
从此恒差 1（`l922-101` 实测、`l923-06` 设计稿 §二）。换序后失败那条不进本地账 ⇒ 恢复帧重试同一条，
rid 由 `_make_rec_id`（同日＋同 surface＋同 reason＋同 lang＋pid 尾＋同 rank）确定性生成 ⇒ 补报带的是
**同一个 rid**，归因链事后闭合（设计稿 §七 推荐理由 2，也是它判 A2 优于 B 案的那一格）。

**没动的面**（逐条点名，避免被当成"顺手一致"）：
- 今日推荐区曝光写序 `:191-205` 一字未动（卷宗只点名跨路径区，w42 §B.1 禁越界）⇒ 见 §三 代价 2；
- 两区**点击侧**（`:226-242` 今日推荐＝l927-29 的送达门控、`:449-462` 跨路径＝失败仍跳）一字未动；
- `core/judge.py`／题件 `*.yaml`／分值判分：**禁碰域，本单零接触**；
- `core/progress.py` 的漏斗口径、`learning_events` schema：**未动**（A3 属改计数口径＝停手项）；
- `data/progress.db`：**全程未连接**，所有断言跑在 `DashboardFakeStreamlit` ＋ MagicMock DAO 桩上，零真库零写盘。

## 二、翻面与新增的用例（逐条，明细同见测试文件末尾「🔴 l927-37 改桩记录」）

| 节 | 例 | 变化 |
|---|---|---|
| §五 例 B | `test_cross_shown_event_failure_is_contained_per_item` 的第 ④ 组 | 判据②靶子一。`CROSS_SHOWN_KEY==全 3 条`＋`len(IMPR)==3`＋`len(sent)==2（悬空账）` → `CROSS_SHOWN_KEY==items[1:]`＋`len(IMPR)==2`＋新增 `len(IMPR)==len(sent)`。① 不外窜／② 尝试数／③ 日志／卡片全渲四格**逐字照旧** |
| §五 例 C | `test_cross_shown_event_failure_no_longer_takes_down_the_sections_below` 末段 | 判据②靶子二。`payload["recommendation_id"]` 为真值（悬空 rid）→ `== ""` ＋ `rank == 0` ＋ 新增两条「失败那条不进本地账」。整页后半段那五个区块标题与 `download_button`／`file_uploader`（本例本体）**一字未动** |
| §七 例 2 | `test_both_surfaces_share_the_same_per_item_containment_shape` | **连坐面，如实登记**：两区共用的 `len(shown)==3`／`len(IMPR)==3` 两行改成逐表面钉值（dashboard 支 3/3 旧写序、cross_path 支 2/2 新写序）；另四面（尝试数／送达 problem_id／卡片／日志）仍合比。没放宽成 `<=3` 之类的恒真形态 |
| §九 新增 例 1 | `test_l927_37_failed_cross_exposure_is_retried_next_frame_with_same_rec_id` | 设计稿 §七 批次② 点名的"钉好"例（这条线以前只有钉坏）：故障帧没送达的第 2 条，恢复帧补报且 rid 与故障帧**尝试时**逐字相同 |
| §九 新增 例 2 | `test_l927_37_impressions_are_written_only_after_shown_add_succeeded` | 钉住换序的**第三格**（add 与 impressions 谁先谁后）。前四处翻面都钉不住这一格：M2 变异（两者对调）只有本例红 |
| §一／§二／§三／§四／§六／§八 | —— | **一字未动**。§六 例 3/例 4 靠「预填 shown 集合」构造空 rid 场景，换序后仍绿（它们 docstring 预言的"一起转红"没兑现，见 §三 代价 4） |

## 三、判分口径与代价影响（本单**不动**任何分值/判分码，只登记写序的后果面）

1. **A2 的已知残余风险落地了**：故障帧最多 1 条 **空 rid / rank=0** 的 `recommendation_clicked` 进事件库
   （设计稿 §八 待裁决 1 点名的就是这条）。与旧写序的差别：旧形态是**悬空 rid**（库里永不出现，漏斗对账
   看着完整、实则断裂），新形态是**肉眼可辨的空串**（下一帧补报同一个 rid 可闭合）。本单把它写成
   「该红就红」（例 C 末段），没有加 `st.warning`、没改文案、没动 except 粒度。
2. **两区曝光写序自此不一致**（🔴 本单最大的开放面，请主班裁）：跨路径 `:430-441` ＝ emit 先、
   成功后记账；今日推荐 `:191-205` ＝ add→impressions→emit（失败那条永久丢失，仍由 §二 例 3、§七 例 1 钉着）。
   设计稿 §六 与 l923-07 遗留 1 都要求「两区同批」才不留形态漂移，但卷宗只点名跨路径区，
   同批改要连 §一/§二/§三 那 5 例一起改桩（超出授权）。⚠ **拉齐方向别照抄 l924-01**：那单在 except 粒度上
   是把今日推荐"照跨路径那一案"改（新形态向旧形态看齐），本单方向相反——要拉齐该把今日推荐区换成 A2，
   不是把本单回退。这条与 l927-29 留下的**点击侧**不一致是两格，两案可并案裁。
3. **故障期事件库行数会变多**（验收漏斗时别误判成"曝光涨了"）：稳态（零故障）两案逐位相同，
   设计稿 §四 表 1/表 2 口径——现状故障帧送达 2／本地 3，A2 故障帧送达 4／本地 4，两帧后 A2 永久丢失 0。
   本区每 episode 的差额上限＝「故障帧数 × ≤3 条」（跨路径区 `cross_recommend(n=3)`）。
4. **§六 例 3/例 4 的预言未兑现**：两例 docstring 写「A2 一旦落地就会变成常态路径 ⇒ 这两例该一起转红」。
   实测它们仍绿，因为它们用**预填 shown 集合**造空 rid 场景，不经失败注入路径；真正的"常态空 rid"路径
   由 §五 例 C 末段与 §九 钉。属当年推演偏差，本单**不改它们的断言**，只在此点名。
5. 重试语义（与 l927-29 遗留 4 同型）：本区换序后失败那条会在下一帧**重试上报同一条 rid**，
   若故障持续多帧会落多条同 rid 行（漏斗是裸行数计数、不按 rid 去重＝A3 域）。本单不动口径。

## 四、判别力实验（新桩确有牙，临时件 `D:\code\tmp\qoder-executor-20260928-0300-learn54\mutate_l927_37.py`）

按原始字节改坏 `ui/pages/dashboard.py` 的跨路径块 → 跑 `tests/test_dashboard_event_failures.py` →
`finally` 逐字节还原（`还原校验 byte-identical: True`，跑完 `git diff --numstat` 只剩本班正式的 `20 8`）。

| 变异 | 含义 | 结果 | 转红的例 |
|---|---|---|---|
| 基线 | 本单实现（emit→add→impressions） | `25 passed` rc=0 | — |
| M1 | 旧写序 `add→impressions→emit` | `5 failed, 20 passed` | 例 B ④、例 C 末段、§七 例 2[cross_path]、§九 例 1、§九 例 2 |
| M2 | `emit→impressions→add`（两格对调） | `1 failed, 24 passed` | **只有 §九 例 2** ⇒ 那一格由新例独立钉住 |
| M3 | emit 挪到 try 外（回到 l923-07 前的裸奔） | `4 failed, 21 passed` | 例 B、例 C、§七 例 2[cross_path]、§九 例 1 |
| M4 | 漏记 impressions | `6 failed, 19 passed` | 上述 ＋ §六 例 1/例 2 ＋ §五 例 A（归因链面） |
| M5 | `add→emit→impressions` | `5 failed, 20 passed` | 与 M1 同集 ⇒ "emit 先"这格有牙 |

## 五、复算命令与读数（cwd `D:\code\learning-system`，均需 `PYTHONIOENCODING=utf-8`）

```
$ git rev-parse --short HEAD && git status --porcelain | wc -l
22a5325 / 0                                   # 开班基线
$ python -m pytest tests/test_dashboard_event_failures.py tests/test_dashboard_page_render.py \
    tests/test_ergo_h912_13.py -q             # 只换生产码、改桩之前
3 failed, 39 passed                           # 红恰为 例B／例C／§七例2[cross_path]，一枚不多一枚不少
$ python -m pytest tests/test_dashboard_event_failures.py -q                  # 改桩＋新增后
25 passed                                     # HEAD 基线是 23 例，本单 +2
$ python -m pytest tests/test_dashboard_event_failures.py tests/test_dashboard_page_render.py \
    tests/test_dashboard.py tests/test_cross_recommend.py tests/test_ergo_h912_13.py \
    tests/test_ui_behavior.py tests/test_dashboard_import_feedback.py -q
99 passed                                     # 判据③正常路径不回归（未跑全量，并发归因不了）
$ python -m pytest tests/test_insights_index_closure.py -q
预期红（本班新增本档未登记），读数见 zcode-bridge/outbox/l927-37.result.md「证据」
```
