# learning topic 双号冲突对账与影响判定（l922-05，2026-09-21）

- 任务：l922-05-learn-topic-dualnum（cwd `D:\code\learning-system`，软预算 ≤30 分钟）
- 性质：**只读判定 + 用例加固**。未改任何目录名、题面、题目 id、paths yaml、数据库；
  唯一落盘产物是本档与 `tests/test_topic_dualnum_pins.py`（1 例现状桩）。
- 复跑：`PYTHONIOENCODING=utf-8 python -m pytest tests/test_topic_dualnum_pins.py -q`

## 一、冲突清单（磁盘实测）

`ls content/<lang>/` 与 `core.loader.load_language` 两路一致。**任务书写「5 处」，磁盘实为 6 组 12 个目录**——
它把 agent_dev 的 `07` 与 `08` 两组合并计成了 1 处（其枚举本身已列到 6 组）。

| # | 语言 | 号 | 两个专题（按展示序） | 题数 | paths 引用（path:milestone） |
|---|---|---|---|---|---|
| 1 | python | 20 | `20_hr_pandas` → `20_numpy_basics` | 5 + 3 | `people_analytics:m10` + `python_advanced:p3` |
| 2 | python | 21 | `21_datetime_ts` → `21_hr_viz` | 3 + 5 | `python_advanced:p3` + `people_analytics:m10` |
| 3 | python | 22 | `22_hr_model` → `22_statsmodels` | 4 + 3 | `people_analytics:m10` + `python_advanced:p4` |
| 4 | r | 14 | `14_real_world_data` → `14_sem_basics` | 4 + 4 | `r_advanced:r4` + `people_analytics:m9` |
| 5 | agent_dev | 07 | `07_data_security` → `07_write_spec` | 4 + 5 | `agent_mastery:a10` + `agent_mastery:a3` |
| 6 | agent_dev | 08 | `08_read_code` → `08_review_pr` | 4 + 4 | `agent_mastery:a2` + `agent_mastery:a4` |

**根因（读 paths 引用列即可看出，不是随机撞号）**：每一组的两个专题**分属两条不同学习路径**——
python 三组是 `people_analytics`（HR 数据分析线，`hr` 前缀即 HR，例：`20_hr_pandas/_lesson.md`
标题「HR 数据分析：Pandas 实战」）在 D5 补线时**沿用了 `python_advanced` 已占用的 20/21/22 号段**；
agent_dev 两组同理（`agent_mastery` 的 a3/a4 与 a10 各取了一段号）。
即：号数是**每条路径各自 numbering 的产物**，被当成全语言唯一号使用，才出现双号。

**不计入双号的两条例外（口径先说清，免得下一班又数出 7 组）**：
- `r/02_logic_and_summary` 与 `r/02b_dataframe`：后者是**字母后缀消歧**，号数（数字段）不重复。
  现状桩按 `(数字段, 字母段)` 组合判重，故 02b 不会被误记成 02 的双号。
- `sql` / `cpp` 两语言零双号（12 与 13 个目录，号段 1:1）。

## 二、影响判定：双号**不改变展示顺序**，但改变「号数」的语义

排序通道逐层读码（`core/loader.py`、`core/paths.py`、`ui/pages/language.py`、`ui/pages/path.py`）：

1. **语言页顺序 = 目录名字典序**，且**仅此一种**。`core/loader.py:139`
   `for topic_path in sorted(glob.glob(os.path.join(lang_dir, "*/")))`，`slug = basename(...)`（:140）。
2. **全仓没有任何代码解析号数**：`split('_')` 取号、`int(slug...)`、`lstrip('0')` 三种写法在
   `core/` `ui/` `scripts/` 里**零命中**（本单实测 grep）。⇒ 「字典序 vs 数值序」之争在本库**当前号段下不发生**：
   号数全部 2 位零填充且最大 24，`sorted()` 与按数值排序**逐位相同，零倒置**（现状桩第 ② 条钉住）。
3. **双号组内的次序由 slug 字母序决定**，稳定可复现：`hr_pandas` < `numpy_basics`、`datetime_ts` < `hr_viz`、
   `hr_model` < `statsmodels`、`real_world_data` < `sem_basics`、`data_security` < `write_spec`、`read_code` < `review_pr`。
   注意第 2、3 组恰好「正课在前、hr 插课在后」，第 1 组相反（hr 插课在前）——**号数相同，插入方向不一致**。
4. **用户可见的实际代价 = 「第 N 个知识点」标签与号数错位**。`ui/pages/language.py:370` 显示的是列表**位置**
   （`idx+1 / total`），不是号数：

   | 语言 | 目录数 | `位置+1 != 号数` 的条数 | 最大漂移 | 例 |
   |---|---:|---:|---:|---|
   | python | 27 | **7** | **+3** | 第 27 位是 `24_real_world_data`（号 24） |
   | r | 18 | **16** | +2 | 第 18 位 `16_mediation`（号 16） |
   | agent_dev | 15 | **8** | +2 | 第 15 位 `13_multi_round`（号 13） |
   | sql | 12 | 0 | — | 号段与位置 1:1 |
   | cpp | 13 | 0 | — | 号段与位置 1:1 |

   r 的 16 条里绝大多数由 `02b_dataframe` 的插入引起，双号 `14` 只再加 1 条偏移。
5. **深链与进度不受影响**：`slug == 目录名` 且目录名互异 ⇒ `navigate_to_problem(lang, topic_slug=...)`
   （`ui/pages/language.py:366/376`）与题目 id `python/20_hr_pandas/01_...` 都不歧义；
   `ui/pages/path.py:143-148` 按 **paths yaml 的 topics 列表顺序**渲染，与 loader 的字典序**是两条独立通道**，
   双号不会把 path 页顺序搞乱，但意味着「yaml 里的顺序」与「语言页里的顺序」可以不同（本库当前不矛盾，
   因两条通道都由同一份号数驱动）。

**结论**：双号是**语义/沟通缺陷**（同一号两解、号数不再等于第几课），**不是排序正确性缺陷**。
因此本单不产出「必须重编号」的紧急结论，而是把现状钉住 + 给方案稿留日间。

## 三、重编号方案稿（留日间决策，本单未执行）

改名代价的**真正承重项不是文件内容，而是历史数据**：题目 id 内嵌 slug
（`attempts.problem_id` 实测形如 `python/24_real_world_data/01_missing`），
`data/progress.db` 里 `attempts`/`problems_status`/`review_state`/`rubric_scores`/`learning_events.topic_id`
都以它为主键线索，`test_content_ids_unique.py` 又钉着「目录名与题目 id 前缀一致」。
**本机 dev 库实测**（只读 `mode=ro`）：12 个双号专题里**只有 `r/14_real_world_data` 带历史**
（attempts 4 行 + problems_status 4 行），其余 11 个专题零行；全库仅 attempts 15 / problems_status 14 / review_state 0 / events 51 行。

- 方案 A（**最小改动**，推荐先议）：只动「插班」的那一个，保持正课号数——
  `20_hr_pandas→25_hr_pandas`、`21_hr_viz→26_hr_viz`、`22_hr_model→27_hr_model`（python 尾部续号，
  零历史行，只需同步 `content/paths/*.yaml` 的 topics 引用与本单现状桩）。
- 方案 B（成对连号）：双号组统一改 `20/20b` 式字母后缀（照 r 的 02b 先例），**号数语义保留、位置仍错位**，
  好处是零跨号段挪动，坏处是「第几课」继续与号数脱钩。
- 方案 C（连号顺移）：把 20 之后整段顺移重排。**python 有 7 条、agent_dev 8 条、r 16 条错位一次性归零**，
  代价最大：12 个目录改名 + paths yaml 全量改引用 + `test_content_ids_unique` 的 id 前缀钉桩 +
  真机用户库里已做过题的行需数据迁移（本机 8 行，用户端未知 ⇒ **上线前必须带迁移**）。
- 三案共同前置：`content/paths/*.yaml` 的 `topics:` 引用（方向 A 的悬空钉桩在 `test_paths_reconcile.py:99`，
  改错即红）、`docs/insights/` 与 `_lesson.md` 里的正文互链、以及 `test_topic_dualnum_pins.py` 的 `DUAL_GROUPS` 清单。
- 建议：先定「号数到底承诺什么」（第几课？还是仅分组标签？）。若答「第几课」→ 走 C 并配迁移；
  若答「仅标签」→ 走 B 并把 UI 的「第 N 个知识点」加注「按当前顺序」即可，不必改名。

## 四、声明

本单零题面/零判分/零数据改动；`data/progress.db` 全程 `mode=ro` 只读，未跑任何写脚本，未 push。
现状桩 1 例已入库（`tests/test_topic_dualnum_pins.py`，钉 ①双号清单与组内序 ②字典序==数值序 ③双号相邻）。
