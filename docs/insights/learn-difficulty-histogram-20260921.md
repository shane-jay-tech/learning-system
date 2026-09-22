# learning 难度分布第三轮：末档空洞普查与判定（l922-06，2026-09-21）

- 任务：`l922-06-learn-difficulty-round3`（cwd `D:\code\learning-system`，软预算 ≤30 分钟）
- 性质：**只读普查 + 分布下限桩**。未改任何题面、题 id、difficulty 字段、paths yaml、数据库。
  落盘产物只有本档与 `tests/test_content_difficulty_pins.py`（5 例现状桩）。
- 复跑：`PYTHONIOENCODING=utf-8 python -m pytest tests/test_content_difficulty_pins.py tests/test_content_census.py -q`

## 一、五语言难度直方（磁盘实算，2026-09-21 22:0x）

| 语言 | 1 档 | 2 档 | 3 档 | 4 档 | 5 档 | 合计 | 末档 |
|---|---|---|---|---|---|---|---|
| python | 27 | 56 | 31 | 7 | 0 | 121 | 4 |
| sql | 12 | 22 | 19 | 1 | 0 | 54 | 4 |
| cpp | 10 | 31 | 21 | **0** | **0** | 62 | **3** |
| r | 15 | 37 | 31 | 1 | 0 | 84 | 4 |
| agent_dev | 11 | 32 | 27 | 7 | 1 | 78 | 5 |
| **合计** | 75 | 178 | 129 | 16 | 1 | **399** | — |

**锚点复核结论：任务书四条锚点全部成立，零漂移。**
`agent_dev 1×难度5` ✓ ／ `cpp 10/31/21（无 4/5 档）` ✓（三档之和恰等于 cpp 总数 62）／
`r 仅 1×难度4` ✓ ／ `sql 1×难度4` ✓ ／ `test_content_census.py:37 只钉 1-5 越界` ✓。
唯一缺项：任务书没给 python 的 4 档题数，实测为 **7**（本档与快照一并钉上）。

## 二、每语言末档样本题 id（difficulty>=4 全量 17 题，无抽样）

| 语言 | 末档 | 题 id（`p.id` 自带 lang 前缀） |
|---|---|---|
| python | 4 | `python/20_numpy_basics/03_stats_summary`、`python/21_datetime_ts/03_group_by_month`、`python/22_hr_model/03_confusion_matrix`、`python/22_statsmodels/03_significance`、`python/23_sklearn_advanced/02_feature_importance`、`python/23_sklearn_advanced/03_pipeline`、`python/24_real_world_data/04_dept_avg` |
| sql | 4 | `sql/12_people_analytics/04_never_submitted`（全语言唯一） |
| cpp | — | **无**。末档样本退化为 3 档：`cpp/13_move_semantics/02_lvalue_rvalue`、`cpp/13_move_semantics/03_move_count`、`cpp/10_templates/04_sum_template`、`cpp/10_templates/05_specialization`、`cpp/07_pointers_class/04_unique_ptr`、`cpp/11_exceptions/*`、`cpp/12_file_io/*` 各 topic max=3 |
| r | 4 | `r/14_real_world_data/04_group_avg`（全语言唯一） |
| agent_dev | 4 + 5 | 4 档 7 题：`agent_dev/05_modular_config/07_coupling`、`/07_data_security/04_minimization_case`、`/08_read_code/02_find_bug_mutable`、`/11_real_tasks/05_decompose_feature`、`/11_real_tasks/06_emergency_rollback`、`/12_spec_iteration/05_iterative_refinement`、`/13_multi_round/05_full_iteration`；**5 档全库唯一 1 题**：`agent_dev/11_real_tasks/08_end_to_end` |

末档集中度：17 题里 15 题落在 agent_dev + python；**sql 与 r 各只有 1 题摸到 4 档**，cpp 一题没有。

## 三、判定：无 4/5 档是「内容空洞」还是「设计口径」？

**结论：内容空洞（标注口径与语言无关，只有 cpp 整族塌掉；sql/r 是薄而非空洞）。**
四条依据，均可复算：

1. **不存在 per-language 档位上限的设计声明。** 全仓只有两处把 5 档写成契约：
   `core/ai_generate.py:38` 生成题时提示词写「原题难度：{difficulty}**/5**」（五语言共用同一模板），
   `tests/test_content_census.py` 头注与 `test_difficulty_落1到5` 对 `LANGS` 五个元素一视同仁。
   代码里没有任何 `if lang == "cpp"` 的档位豁免。若「cpp 只到 3」是设计，必须先在 `test_content_census.py`
   的 1-5 断言上开口子 —— 现状没有。
2. **cpp 的收官里程碑本身是难题题材，标签却停在 3。** `content/paths/cpp_foundation.yaml`
   标题「C++ 从入门到现代」，末段 `c5 模板、异常与资源管理` 覆盖 `10_templates`…`13_move_semantics`。
   逐 topic 实测 max difficulty：`10_templates` 3、`11_exceptions` 3、`12_file_io` 3、`13_move_semantics` 3；
   其中 `13_move_semantics/04_moved_state`、`05_emplace`、`10_templates/02_class_template` 标的是 **2**。
   移动语义 / 模板特化 / 智能指针在同类语言里对应 python 的 4 档题材（`sklearn pipeline`、`statsmodels significance`）。
   **同一条 1-5 尺子，cpp 收官题被压低了一档** —— 这是标注不一致，不是设计。
3. **空洞的代价落在唯一一个下游行为差异面上。** 难度档全链路只有一个消费点：
   `core/progress.py:378` `if difficulty >= 4: ease = max(1.5, ease - 0.1)`（SRS 难度惩罚，答对也降 ease 以拉长巩固）。
   `core/ai_review.py:162/164/253` 只按 `difficulty <= 2` 分岔 ⇒ 3/4/5 档在点评侧**无差别**，
   所以「没有 4/5 档」在 UI 上看不出来，但在 SRS 上：**cpp 用户的 ease 惩罚分支永久不可达，
   sql / r 用户整条路径只有 1 题能触发**。空洞不是装饰性问题。
4. **反向证据也不成立**：cpp 不是「没有难题可出」——`13_move_semantics/03_move_count`、
   `10_templates/05_specialization` 这类题在 agent_dev 口径下会落在 4。故空洞成因是**逐语言标档时缺横向校准**，
   与前三轮普查的「号数≠位置」「语言梯度不齐」同源。

**分档建议（不在本单动手）**：cpp 收官 4 个 topic（10/11/12/13）里各挑 1-2 题上抬到 4，
优先 `13_move_semantics/02_lvalue_rvalue`、`10_templates/05_specialization`；
sql / r 各补 2-3 题真 4 档（当前 1 题＝单点，一道改标就清零）。
每次上抬都会同时改 `PINNED_HIST` 与 `PINNED_TOP_TIER` 两个快照 —— 这是设计让改动显形，不是桩失效。

## 四、本单钉的桩（`tests/test_content_difficulty_pins.py`，5 例）

| 用例 | 钉什么 | 触发漂移的动作 |
|---|---|---|
| `test_逐语言难度直方_钉死` | 5×5 格题数全表 | 任一档增/删题 |
| `test_合计399与直方自洽` | 快照本身仍等于官方 399 口径 | 只改快照不改题（防空转绿） |
| `test_分布下限_每语言覆盖1到3档` | **下限桩**：1-3 档任一语言任一格不得为 0 | 基层梯度塌陷 |
| `test_末档_ge4_题id名单_钉死` | 17 题逐 id 名单（4 档 16＋5 档 1） | 末档无声清零或灌水 |
| `test_cpp_无4到5档_是现状而非用例失效` | cpp 末档=3 的**现状**，附「须同步改判定档」提示 | 补 cpp 难题时逼回来改本判定 |

> **2026-09-23 l923-03 更新（按本档口径续登记，不改上面 09-21 快照）**：python 行由
> `{1:27, 2:56, 3:31, 4:7, 5:0}`（121 题）变为 `{1:27, 2:58, 3:33, 4:7, 5:0}`（**125 题**），
> 全库 399 → **403**；增量全部落在 1-3 档（`20_numpy_basics`、`21_datetime_ts` 各补难度 2、3 各一题），
> **4/5 档名单 `PINNED_TOP_TIER` 未动**——新题刻意不出 4 档，避免无声扩宽 `core/progress.py`
> 的 SRS ease 惩罚可达面（该面属红线域，须有意才可扩）。
> 另：上表第 2 行的用例名已随口径改名为 `test_合计403与直方自洽`（该族用例名刻意编码当期口径，
> 让「只改断言数字不改名」在 diff 里显形；本档保留 09-21 的原名以维持当时盘态留痕）。

## 五、对前两轮的口径补记（防下一班又数错）

- 本单只读 `core.loader.load_language`，与 `ls content/<lang>/` 两路一致，**不涉及 topic 目录号数**
  （号数≠位置的漂移在 python 组 +3，已由 l922-05 单独立桩，见 `learn-topic-dualnum-20260921.md`）。
- 五语言口径：`test_content_census.py:14` 的 `LANGS` 是 5 个（python/sql/cpp/r/agent_dev），
  `content/` 下另有 `datasets/`、`paths/` 两个非语言目录，不计入直方。
