# learning path 双顺序通道一致性实测（l922-126，2026-09-22）

## 结论一句话
两条独立顺序通道**确有真矛盾**（推翻 l922-05 遗留 #2 「当前不矛盾」的乐观判定）：
`python_advanced` 的 **p4 / p5** 两个里程碑内，`milestones[].topics` 的 yaml 手写序与语言页
（`core/loader.py:139` 目录名字典序）**相对次序倒置**，全库实测 **2 处**。属规划域决策
（重排 yaml 或给专题加显式 `order:` 字段），执行班不改生产码、只把矛盾清单落本档交规划。

## 两条通道（读码定位，均取自生产函数、未另造判据）
- 语言页顺序：`core/loader.py:139` `sorted(glob.glob("content/<lang>/*/"))` → slug 的**目录名字典序**。
- 路径页顺序：`ui/pages/path.py:143` `get_milestone_topics_flat(milestone)` → `milestones[].topics`
  的**手写列表序**（按语言分组后逐条渲染成跳转按钮）。
- 判据：对每个 `(path, milestone, lang)`，把该 milestone 内同语言的 slug 取其在 loader 序里的下标，
  下标序列若非单调递增即判为倒置。悬空引用不在本单职责（`tests/test_paths_reconcile.py` 已钉 0 悬空）。

## 矛盾清单（条数 == 2，与测试 `xfail(strict=True)` 主断言一一对应）

| # | path / milestone | 语言 | yaml 列表序（路径页看到的顺序） | loader 字典序位置 | loader 实际序 |
|---|---|---|---|---|---|
| 1 | `python_advanced` / **p4「统计建模与机器学习」** | python | `13_scipy_stats → 22_statsmodels → 14_sklearn_intro → 23_sklearn_advanced` | `[12, 24, 13, 25]` | `13 → 14 → 22 → 23` |
| 2 | `python_advanced` / **p5「真实数据与实验分析」** | python | `24_real_world_data → 15_ab_text` | `[26, 14]` | `15 → 24` |

- 第 1 条：`22_statsmodels` 被排在 `14_sklearn_intro` 之前（路径页），但语言页字典序里 `14` 在 `22` 前 → 一处倒置（`24 → 13`）。
- 第 2 条：`24_real_world_data` 被排在 `15_ab_text` 之前（路径页），语言页里 `15` 远在 `24` 前 → 整段倒置（`26 → 14`）。

其余 4 条 path（`agent_mastery` / `cpp_foundation` / `people_analytics` / `quick_stats`）41 个
`(path, milestone, lang)` 三元组逐语言相对序**与 loader 一致**，无新增矛盾。

## 根因（与 l922-05 同源，非随机撞号）
专题号数 `NN_` 是**每条路径各自编的教学号**，被 `load_language` 当成**全语言唯一字典序键**用。
p4/p5 的作者按「先 scipy 再 statsmodels、先 sklearn_intro 再 sklearn_advanced」「先真实数据再 AB 实验」
的教学意图手写了跨号段的顺序（13→22→14→23），而目录名字典序只会给 13→14→22→23。
两条通道各表各的意图：yaml 承载「教学推进序」，loader 只承载「浏览列表序」——这正是 l922-05
insight §三留的「号数到底承诺第几课还是仅作分组标签」未决口径的具体咬人实例。

## 出口（交规划，三选一；本单不擅动）
1. **重排 yaml**：把 p4/p5 的 `topics` 列表按语言页字典序改齐 → 两通道归一。代价：牺牲路径作者的教学推进序，
   且 `p4` 的 `13→22→14→23` 本就是刻意交错，改齐会丢失意图。
2. **给专题加显式 `order:` 字段**（l922-05 方案 C 的方向）：`load_language` 改为按 `order:` 排，
   语言页与路径页共用同一显式序 → 彻底摆脱「靠目录名编码顺序」。代价：动 loader 排序＝全库展示序变更，
   须评估「第 N 个知识点」标号与既有一切按位置取数的假设。
3. **接受两通道并存、只把差异写进 UI 文案**：路径页标注「按推荐学习顺序」，语言页标注「按目录顺序」，
   不再要求二者相等（则应把本测试从 xfail 改成断言「差异清单 == 本档清单」的现状桩，同 KNOWN_DUP_TOPICS 范式）。

## 落钉方式（现状，零生产码改动）
`tests/test_paths_order_consistency.py`：
- `test_覆盖全部path` 绿钉 6 条 path 全覆盖（集合漂移即红）；
- `test_路径内milestone顺序与语言页顺序一致` 主断言 `assert not divergences` 现状 2 处真红 →
  以 `@pytest.mark.xfail(strict=True)` 记录为「已知未消解的跨层矛盾」，不污染全量绿基线；
  **一旦规划按出口 1/2 把顺序改齐，divergences 变 0 → 断言转绿 → strict xfail 当场报 XPASS＝红**，
  逼着回来删这个标记（＝修好即提醒，符合本仓「钉桩转红＝提醒」范式）。
- 取数命令（复现本档）：`python -c "import glob; from core.paths import load_all_paths; ..."` 见测试 docstring；
  本档清单条数 = `_collect_divergences()` 返回长度 = 实测 2。
