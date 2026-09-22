# 前端人体工学改造计划

## 固化目标（200 字）

将现有Streamlit 前端升级为克制、舒适的学习工作台，服务初学者。保留紫色，减少渐变、阴影与表情符号，统一导航、卡片、按钮、表单和反馈。适配 1366×768、1080p和窄窗；优化层级、行宽、留白、热区、对比度、键盘焦点和状态辨识，降低学习疲劳。覆盖主页、刷题、路径、诊断、面板及错题本，不改业务与数据语义。以首屏清晰、任务易达、文字易读、交互稳定、测试通过和浏览器实测无溢出错位为验收标准。

## 执行边界

- 保留 Streamlit 技术栈、现有路由、课程数据与业务流程。
- 在当前未提交修改上增量工作，不回退用户已有变更。
- 桌面优先；窄窗口保持关键内容与操作可见。
- 不引入新的网络依赖、图片资产或重量级前端框架。

## 执行步骤

1. 审计全局样式、复用组件、导航与七个页面的信息层级。
2. 建立统一的色彩、字号、间距、圆角、阴影、焦点和响应式规范。
3. 改造侧栏、首页、学习路径、诊断、刷题、面板和错题本。
4. 补充或更新界面行为测试，运行相关测试与全量回归。
5. 启动本地应用，在浏览器中按桌面与窄窗口逐页巡检并修正。

## 验收标准

- 主要页面无横向溢出、遮挡、错位和难以点击的关键控件。
- 正文行宽、字号、行高、色彩对比与间距适合长时间阅读。
- 主操作、次操作、状态与导航当前项层级明确，键盘焦点清晰。
- 自动化测试通过，浏览器实测覆盖所有主要路由。

## 执行结果

- 已完成全局设计系统、侧栏、首页、刷题、路径、诊断、面板与错题本改造。
- 已验证 900×768、1366×768、1920×1080，均无横向溢出或页面异常。
- 全量测试结果：**622 passed，7 skipped**（本机未安装 g++ / Rscript；7 条恒 skip 经复核为 cpp runner 4 + r runner 3，非「7 条 R」）。实测命令：python -m pytest tests -q；口径：pytest（非 unittest discover）。**基线绑 commit 不绑日期**：622/7（629 collected，622+7=629 自洽）@ commit `a0ee9b9`，2026-09-22 01:23 复跑、工作树 clean。口径链：376（9/17）→ 384（9/18）→ 566（9/21 @0564042，l922-03）→ 597（9/22 @1632f91，n922-10）→ **622**（9/22 @a0ee9b9，l922-107）；566→622 的 +56 逐文件归因见 `docs/insights/learn-plan-baseline-refresh-20260922.md`。

## 题库内容规范（l923-02 钉，2026-09-23 @ HEAD `1eebffb`）

> 本节是「补题」这一类改动的**唯一授权口径落点**。上游卡点：`l922-07` 遗留 2 要求「把『每 topic 5 题』写进 README.md 或 plan.md，同时决定 399→408 的对外口径改法」，而 `l922-128` 因该规范**未钉**只能整单 partial（执行班无权代定对外口径）。此后补题单照本节同步等值点即可，不必再等规划班拍板。
> 本节只钉内容口径，**不改判分口径、不改题面**；`core/judge.py` 与 `core/progress.py` 属红线域，任何补题都不得顺带动它们。

- **每 topic 目标题数＝5**（补题补到 5 即止，不是「补到 6 消除薄」）。推导与依据见 `docs/insights/learn-thin-thick-topics-20260921.md:73`（「补题目标位应钉在 5（回到众数）」）。落笔时磁盘实取：**85 topic / 399 题**，每 topic 题数直方 `{2:4, 3:8, 4:10, 5:55, 6:6, 8:2}` ⇒ 众数恰为 5；薄于 5 的 22 个是补题对象，厚于 5 的 8 个属**合理厚**（综合实战/多路径复用），不削。
- **下限哨兵另计，不与上面的「目标 5」混为一谈**：真正的门禁在 `tests/test_content_thin_topic_p0.py` —— `:58 MIN_QUESTIONS_PER_TOPIC = 2`（防「新建目录只放一题占位」）、`:62 NON_THIN_RATIO_FLOOR = 0.72`（比例式，绑磁盘实取）、`:67 MILESTONE_Q_PER_HOUR_FLOOR = 1.6`（里程碑题/时下界）。⇒ 「5」是**内容指引**，「>= 2 / 比例下界」才是**会红的东西**；补到 5 只会让三条判据更宽松，不会撞线。
- **新专题目录的语言级精确桩**：`tests/test_content_census_python.py:18-19` 钉 python 的 topic 数与题数（现值 27/121）。**只在已有 topic 目录内补题不撞它**；新建 topic 目录必须同批改该文件的 `EXPECTED_TOPICS / EXPECTED_SLUGS`。

### 补题时必须同批同步的等值点（任务书口径的 4 处）

| # | 落点 | 现值 | 复算命令（仓库根执行） |
|---|---|---|---|
| 1 | `tests/test_content_difficulty_pins.py:29` 的 `PINNED_HIST` | python 行 `{1:27, 2:56, 3:31, 4:7, 5:0}`（合计 121） | `python -m pytest tests/test_content_difficulty_pins.py -q` |
| 2 | `tests/test_content_difficulty_pins.py:80` | `assert sum(per_lang.values()) == 399` | `python -c "import pathlib;print([ (i,l.strip()) for i,l in enumerate(pathlib.Path('tests/test_content_difficulty_pins.py').read_text(encoding='utf-8').splitlines(),1) if '== 399' in l ])"` |
| 3 | `tests/test_content_census.py:27` | `assert total == 399` | 同上换文件名（命中 `!= 399（README 官方口径，变更须有意）`） |
| 4 | `README.md:52` 对外口径 | 「399 题、85 知识点、6 条学习路径」 | `python -c "import pathlib;print(pathlib.Path('README.md').read_text(encoding='utf-8').splitlines()[51])"` |

四处**必须同一批**改，缺任一处即全量红（1/2/3 直接判红；4 经 `scripts/generate_system_report.py:214` 的 README 数字核对间接判红）。
另注：`tests/test_scripts.py:310` 是 `assert metrics["total_problems"] >= 399` 的**下界护栏**，纯增量补题**不需改它**（它挡的是净减）；`tests/test_paths.py:29` 的 `len(paths) >= 3` 同为下界，与补题无关，且收紧它属改测试语义、待人工。

### 读码实测的追加同步面（任务书 4 处之外，本班 2026-09-23 补全）

补 **python** 题除上表外还会同时变红，改动者须一并处理（否则违反「全量零新增红」）：

- `tests/test_content_thin_topic_p0.py:50-55` 的 `P0_SNAPSHOT` —— 四个 P0 目录的**难度多重集**快照，含 `python/20_numpy_basics: [2, 3, 4]`、`python/21_datetime_ts: [2, 3, 4]`。该例的失败信息本身就写着「请同批改 PINNED_HIST ＋ 两处 `== 399` 等值断言 ＋ README:52，并把本快照与 `docs/insights/learn-thin-thick-topics-20260921.md` 的落点表一起刷新」⇒ 落点表（同一 insight 档 §四）是**第 5 处**文档口径。
- `tests/test_content_census_python.py:19,20,71,80` —— `EXPECTED_PROBLEMS 121`、`EXPECTED_DIFF {1:27,2:56,3:31,4:7}`、答案字段计数 `{expected_output:113, tests:46, rubric:8, reference_answer:8}`、`judge_mode {run:113, ai_open:8}` 四组精确桩。
- **新题难度建议 ≤3**：`difficulty >= 4` 会扩宽 `core/progress.py` 的 SRS ease 惩罚可达面并连带要求改 `PINNED_TOP_TIER`（`tests/test_content_difficulty_pins.py:38-58`）。SRS/判题属红线域，补题不得顺手扩。

### 399 → 403 预留（本夜 l923-03 的落地口径）

`python/20_numpy_basics` 与 `python/21_datetime_ts` 各 3→5、**净增 4 题**（难度取 2/3 档）⇒ 官方对外口径由 **399 → 403**，python 侧 121 → 125。届时上表 4 处与追加面 2 处**同批**改为 403/125。cpp 侧两目录（`l922-07` §四 P0 第一行，再 +5 题 → 408）**本机无 g++ 判不了参考答案**，留日间班，留日间时口径停在 403 不冲突——本规范按「每补一批、口径走一次」更新，不预支未落地的数字。

