# learning insights 索引（l918-12 建档 2026-09-19；l922-127 于 2026-09-22 04:02 按磁盘实况重建，本文件为当前权威索引）

> **对账口径（唯一判据，改档必重跑并回填下面三行读数）**——命令均在仓库根 `D:/code/learning-system` 执行：
>
> ```bash
> ls docs/insights/*.md | wc -l                                               # A 磁盘 .md 数
> grep -c '^| docs/insights/' docs/insights/learn-insights-index-20260918.md  # B 本表条目数（含本文件）
> comm -23 <(ls docs/insights/*.md | sort) \
>          <(grep -o '^| docs/insights/[^ |]*' docs/insights/learn-insights-index-20260918.md | cut -d' ' -f2 | sort)   # C 未列项（应为空）
> ```
>
> 闭合等式：**A == B，且 C 为空，且 B 去重后条数 == B（无重复）**；B 已含索引自身 1 份，故等价于「磁盘其余档数 == 条目数 − 1」。
>
> - 本次落笔读数（2026-09-22 04:02 建档＝l922-127／04:2x 追加 1 份＝l922-129／04:4x 追加 1 份＝l922-130／04:5x 追加 1 份＝l922-131，后三份同处 HEAD `1831cc7` 的在途批；末次复算时刻 2026-09-22T04:52+08:00）：**A=62、B=62、C=空、重复=0 ⇒ 等式闭合**。
> - 重建前读数（同一组命令）：**A=59、B=37、C=22 行、重复=0 ⇒ 不闭合**，缺的 22 行即 09-19 之后各浪新档。
> - 2026-09-23 追加 1 份＝l923-06（写序缺陷设计稿 `learn-shown-writeorder-design-20260923.md`，登记时未跟踪）：复算 **A=63、B=63、C=空、重复=0 ⇒ 等式闭合**；哨兵 `tests/test_insights_index_closure.py` 同批复跑 3 passed。
> - 2026-09-23 再追加 1 份＝l923-17（F-1 outline 复位静态普查 `learn-focus-f1-outline-static-20260923.md`，登记时未跟踪）：复算 **A=64、B=64、C=空、重复=0 ⇒ 等式闭合**；同批哨兵复跑见 result（3 passed）。
> - 2026-09-23 主班代登 1 份＝l923-24（CALIBER_NOTE 前提取证 `learn-caliber-note-premise-20260923.md`，登记时未跟踪）：复算 **A=65、B=65、C=空、重复=0 ⇒ 等式闭合**；哨兵同批复跑 3 passed。登记人＝主班而非出档班，原因见本仓并行纪律：多路子班同时改本表会互相覆盖，故索引件由主班单点写。
> - 2026-09-23 主班代登 1 份＝l923-28（cpp／sql／r 末档难度上抬设计稿 `learn-tail-difficulty-design-20260923.md`，登记时未跟踪）：复算 **A=67、B=67、C=空、重复=0 ⇒ 等式闭合**；哨兵同批复跑 3 passed。
> - 2026-09-23 主班代登 1 份＝l923-30（事件型普查 `learn-eventtypes-census-20260923.md`）：复算 **A=68、B=68、C=空、重复=0 ⇒ 等式闭合**；哨兵同批复跑 3 passed。同时把 l923-24 那行的 git 状态列由「未跟踪」更正为「已入库」（该档已随 `e8447b7` 入库；此列不参与哨兵断言，只影响人读准确性）。
> - 2026-09-24 出档班自登 1 份＝l924-06（焦点环对比度静态实算 `learn-focusring-contrast-20260924.md`，登记时未跟踪）：复算 **A=71、B=71、C=空、重复=0 ⇒ 等式闭合**；哨兵 `tests/test_insights_index_closure.py` 同批复跑 3 passed。本波 learning 分区仍只一路写位，继续按「同班追加规则」自登而非主班代登。
> - 2026-09-24 出档班自登 1 份＝l924-05（判题结论保留行为改动裁决稿 `learn-judge-result-keep-design-20260924.md`，登记时未跟踪）：复算 **A=70、B=70、C=空、重复=0 ⇒ 等式闭合**；哨兵同批复跑 3 passed。与上一条（l924-04）同班同波，仍是单路写位，故继续自登。
> - 2026-09-24 出档班自登 1 份＝l924-04（`editor_*` 键规范设计稿 `learn-editor-key-spec-20260924.md`，登记时未跟踪）：复算 **A=69、B=69、C=空、重复=0 ⇒ 等式闭合**；哨兵 `tests/test_insights_index_closure.py` 同批复跑 3 passed。本波 learning 分区只有一路子班在跑（索引件非并发写），故按「同班追加规则」由出档班自登而非主班代登。
> - 2026-09-24 出档班自登 1 份＝l924-17（权威索引「我是权威」frontmatter 标记**设计稿** `learn-index-authority-mark-design-20260924.md`，登记时未跟踪；本单零生产码改动，哨兵判据一行未动）：复算 **A=73、B=73、C=空、重复=0 ⇒ 等式闭合**；同批哨兵 `tests/test_insights_index_closure.py` 复跑 3 passed。同批实测新发现：本表 `| 未跟踪 |` 9 行经 `git ls-files` 逐行复验**已全部入库**，该列整体过期（哨兵不读此列，故不拦）。
> - 2026-09-25 出档班自登 1 份＝l924-18（achievements 存量逗号格式一次性迁移**设计稿** `learn-achievements-migration-design-20260924.md`，登记时未跟踪；本单零生产码改动、零写库，盘态实验全在 `tmp/l924-18/` 副本上）：复算 **A=74、B=74、C=空、重复=0 ⇒ 等式闭合**；同批哨兵 `tests/test_insights_index_closure.py` 复跑 3 passed。本波 learning 分区仍只一路（文档位），继续按「同班追加规则」自登。
> - 2026-09-25 出档班自登 1 份＝l924-19（path 文案 ⇄ 磁盘题数过期自述普查 `learn-path-claim-audit-20260924.md`，登记时未跟踪；只读普查，`content/` 与生产码零改动）：复算 **A=75、B=75、C=空、重复=0 ⇒ 等式闭合**；同批哨兵复跑 3 passed。否证卷宗两条口径（"7 文件"实为 6 份 path yaml／"16+ 处"无对应口径，实值 82·129·12 三档）。
> - 2026-09-25 出档班自登 1 份＝l924-20（点评缓存 FIFO→LRU 与分池两案**裁决材料** `learn-review-cache-lru-verdict-20260924.md`，登记时未跟踪；判据全部出自 `tmp/l924-20/` 内存假件，零生产码改动、零 LLM 调用、未放宽断言）：复算 **A=76、B=76、C=空、重复=0 ⇒ 等式闭合**；同批哨兵复跑 3 passed。否证一条在册自述：`core/ai_review.py:45`「改一个字再跑一次」与全码 sha1 键形矛盾（且与 :44 自相矛盾）。
> - 2026-09-25 出档班自登 1 份＝l924-21（`test_count_is_22` 字面量桩处置**裁决材料** `learn-achievements-count-verdict-20260924.md`，登记时未跟踪；`tests/`／`core/`／`README.md`／`plan.md` 零改动，只跑完成标准点名的定向基线）：复算 **A=77、B=77、C=空、重复=0 ⇒ 等式闭合**；同批哨兵复跑 3 passed。否证两条：白名单 `_NON_ID_LITERALS` 实为 **14** 条（在册注释与派单都写 15）／所谓"两侧同步"实测是 **4 处必改＋2 处条件性**。
> - 2026-09-25 出档班自登 1 份＝l924-22（换 widget key ＋ 陈旧键有界回收**裁决稿** `learn-uploader-key-recycle-design-20260924.md`，登记时未跟踪；零生产码改动，盘态实验全在 `tmp/l924-22/` 探针内，不连库不启服务）：复算哨兵 `tests/test_insights_index_closure.py` 同批复跑 3 passed、A==B 且 C 空 ⇒ 等式闭合（本行不写绝对条目数，避免下一份档又把它漂成假数）。否证两条在册自述：① 「陈旧键在 `session_state` 无界增长」——可见键实测有界（脚本外恒 1／脚本内当帧 2），真线性增长的是 Streamlit 内部 `KeyIdMapper` 与 `widget_metadata` 两张表；② 「pop/赋值已实例化控件的 key 会抛 `StreamlitAPIException`」——本机 streamlit 1.58.0 下两种写法均未抛。
> - 2026-09-25 出档班自登 1 份＝l924-23（core/ 函数级零测终扫**台账** `learn-core-final-scan-20260924.md`，登记时未跟踪；同批新增在册测试件 `tests/test_format_local_ts.py`，生产码零改动）：复算哨兵 `tests/test_insights_index_closure.py` 同批 3 passed、A==B 且 C 空 ⇒ 等式闭合（本行同样不写绝对条目数）。否证卷宗两条：① 「唯一漏网 format_local_ts」实为 **4 个零名**（core 2＋runners 2）；② 「15 模块」按盘上是 16 份 .py，而 `rg -c` 只回 14 行（零命中文件被静默省略）。
> - 2026-09-25 出档班自登 1 份＝l924-24（content tags 词表普查＋消费面双轨取证**三案建议稿** `learn-content-tags-census-20260924.md`，登记时未跟踪；只读普查，探针在 gitignore 的 `tmp/l924-24/`，`content/` 与 `core/` 与 `ui/` 零改动、三案一律未选）：复算哨兵 `tests/test_insights_index_closure.py` 同批 3 passed、A==B 且 C 空 ⇒ 等式闭合（本行不写绝对条目数）。否证／订正卷宗三条口径：① 「6 件无 tags」的 6 件全部是 `content/paths/*.yaml`（题以外件型，**补标才是错**），真分母 403 题件覆盖率 100%；② 「唯一值 416／单例 265」现值经三轨对平**成立**（旧口径 343/220 作废）；③ 「mark_r_judge_plain 写侧」不确——它把顶层 `tags:` **行**当插入锚点（`:275/:279/:281/:289`），是词表唯一真实生产依赖，属读位置不读值。
> - 同班追加规则（l922-129 起生效）：**新增 insights 档必须与索引件同单登记**，否则本表读数当场失效；改完请重跑上面三条并回填本节。
> - 作废口径：旧版档头自述「36 份既有＋本文件=37」是 2026-09-19 建档时点快照，**不得再当现值引用**。
> - 盘上另有 2026-09-17 旧索引 `learning-insights-index-20260917.md`（r917-20），按历史快照原则原样保留并已列入本表；**当前权威索引是本文件**。

## 重建记录（l922-127，2026-09-22；只动本索引文件，未触碰任何被索引报告）

- 补登 23 份未列档：20260918 批 4 份（l918-13/17/26/27）、20260919 批 2 份（l920-08 与 `content-id-conflict-04-functions-20260919.md`）、20260920 批 3 份、20260921 批 4 份（l922-03/05/06/07）、20260922 批 9 份（l922-107/108/109/116/117/118/120/126/129）、另 1 份为 09-17 旧索引本身。**无删除条目、无改名、未动任何被索引报告**。
- 旧表「被引用状态」列实测填的是 **git 入库状态**，且 37 行全写「未跟踪」——现 59 份全部入库（`git ls-files docs/insights | wc -l` = 59），该列读数整体过期。本次拆成两列，各自可用上面风格的单条命令复算：
  **git 入库**（`git ls-files` 判定）／**insights 外引用数**（`git grep -l --fixed-strings <文件干名> -- ':(exclude)docs/insights'` 命中文件数）。
- 「主题」列改为**逐档 H1 原文**直取（不再手写摘要），杜绝转录漂移；本文件自身那一行取重建后的新 H1。
- 现值分布（l922-130／l922-131 各追加 1 份后复算）：insights 外被引用 10 份／未被引用 52 份（合计 62）；git 入库 60 份／未跟踪 2 份（`learn-home-notice-migrate-20260922.md`、`learn-readme-tree-20260922.md`，待主班收口提交后应转「已入库」）；未引用 ≠ 缺陷，与 colony 侧同形态，仅作登记不据此改动任何档。

| 文件 | 日期 | 主题（各档 H1 原文） | git 入库 | insights 外引用数 |
|---|---|---|---|---|
| docs/insights/agent-dev-rubric-review-20260905.md | 20260905 | agent_dev 开放题 rubric 评分设计质量评审（只评不改，2026-09-05 夜 1022） | 已入库 | 0 |
| docs/insights/content-id-conflict-04-functions-20260919.md | 20260919 | 跨语言 slug 冲突 04_functions —— 用户拍板维持（2026-09-19） | 已入库 | 0 |
| docs/insights/content-quality-sample-20260905.md | 20260905 | 编程题库抽样质量评审（seed=20260905，psy-C…/learning 100c） | 已入库 | 1 |
| docs/insights/learn-384-7-caliber-20260918.md | 20260918 | learning pytest「384/7」口径澄清留档（2026-09-19 晨间执行班，任务 l918-01，零改动） | 已入库 | 0 |
| docs/insights/learn-achievements-count-verdict-20260924.md | 20260924 | learning `test_count_is_22` 字面量桩处置裁决材料（l924-21，只出稿＋案序 · 零生产码改动） | 未跟踪 | 0 |
| docs/insights/learn-achievements-migration-design-20260924.md | 20260924 | learning achievements 存量逗号格式一次性迁移设计稿（l924-18，只出设计 · 零生产码改动） | 未跟踪 | 0 |
| docs/insights/learn-bank-cadence-20260915.md | 20260915 | verify-question-bank 纳入例行方案（n915-65，只出设计） | 已入库 | 0 |
| docs/insights/learn-caliber-note-premise-20260923.md | 20260923 | CALIBER_NOTE「阅读合并」前提交叉取证＋learning_events 账本重建量化：注记因果前提在全量 git 历史不成立（l923-24，纯只读，三选一待裁决） | 已入库 | 0 |
| docs/insights/learn-compare-inventory-20260916.md | 20260916 | learning 全仓同族比较逻辑清点（n916x-40，_cell_eq 语义校正后横向核验，只读） | 已入库 | 0 |
| docs/insights/learn-content-tags-census-20260924.md | 20260924 | learning content tags 词表普查（l924-24，409 件三轨对平＋416/265 现值＋消费面 rg/AST 双轨 ＋ 三案建议未选案） | 未跟踪 | 0 |
| docs/insights/learn-core-final-scan-20260924.md | 20260924 | learning core/ 函数级零测终扫台账（l924-23，双轨计数表＋终扫命令 ＋ `format_local_ts` 收口） | 未跟踪 | 0 |
| docs/insights/learn-coverage-reconcile-20260917.md | 20260917 | learning 覆盖率三口径对账（916p-a3-014，2026-09-17，只读） | 已入库 | 0 |
| docs/insights/learn-d5d6-review-fix-20260920.md | 20260920 | D5/D6 处置记录：agent_mastery 时数、judge_mode 等价性证明、迁移脚本加固 | 已入库 | 0 |
| docs/insights/learn-dashboard-768-fold-budget-20260922.md | 20260922 | dashboard 首屏 768 纵向预算静态推演（1366×768，l922-117） | 已入库 | 0 |
| docs/insights/learn-dashboard-coverage-20260917.md | 20260917 | dashboard.py 渲染主路径补测（916p-a3-015，2026-09-17，只增测试） | 已入库 | 0 |
| docs/insights/learn-deps-suspects-20260918.md | 20260918 | pywebview / streamlit-ace 疑点依赖只读核报（2026-09-19 晨间执行班，任务 l918-08，零改动） | 已入库 | 0 |
| docs/insights/learn-difficulty-histogram-20260921.md | 20260921 | learning 难度分布第三轮：末档空洞普查与判定（l922-06，2026-09-21） | 已入库 | 1 |
| docs/insights/learn-editor-key-spec-20260924.md | 20260924 | learning `editor_*` 键规范设计稿：全局 UI 键 vs 题态键 vs 变体残键（l924-04，只读，零生产码改动） | 未跟踪 | 0 |
| docs/insights/learn-eventtypes-census-20260923.md | 20260923 | learning 事件型 emit_event 普查：11 类／12 写点、5 类零行、heatmap 读侧不存在（progress.py:538 events_by_date() 生产零调用方）（l923-30，只读零改动） | 已入库 | 0 |
| docs/insights/learn-focus-f1-outline-static-20260923.md | 20260923 | learning F-1 上行风险排查：Streamlit 1.58 自带样式里的 outline 复位普查（l923-17，2026-09-23，只读零源码改动） | 未跟踪 | 0 |
| docs/insights/learn-focus-surface-audit-20260922.md | 20260922 | learning 键盘焦点覆盖面静态审计（unsafe_allow_html 面，l922-118，2026-09-22） | 已入库 | 0 |
| docs/insights/learn-focusring-contrast-20260924.md | 20260924 | learning 焦点环对比度静态实算：`styles.py:209/:216/:225` 三组 rgba(#5B5BD6,.28) 对全部在册浅面色仅 1.45–1.49，WCAG 1.4.11 的 3:1 三组全不达标（α_min=0.70–0.745；streamlit 自带 .5 亦仅 2.06–2.11）；改色三档含复算值＋在册注释引错判据（2.4.7 无门槛）（l924-06，只读零改码，收口 l923-18 R-1） | 未跟踪 | 0 |
| docs/insights/learn-home-notice-migrate-20260922.md | 20260922 | home AI 档位 st.warning → render_notice 统一收口（l922-130 双形态并档） | 未跟踪 | 1 |
| docs/insights/learn-index-authority-mark-design-20260924.md | 20260924 | learning 权威索引「我是权威」标记设计稿：frontmatter role 取代靠文件名日期挑档（l924-17，只出稿、零生产码改动） | 未跟踪 | 0 |
| docs/insights/learn-insights-index-20260918.md | 20260918 | learning insights 索引（l918-12 建档 2026-09-19；l922-127 于 2026-09-22 04:02 按磁盘实况重建，本文件为当前权威索引） | 已入库 | 0 |
| docs/insights/learn-insights-intake-20260917.md | 20260917 | learning docs/insights 未入库报告收口（916p-a3-017，2026-09-17） | 已入库 | 0 |
| docs/insights/learn-judge-edges-20260916.md | 20260916 | learning judge 三函数反例边界补测（l916-02） | 已入库 | 0 |
| docs/insights/learn-judge-mode-census-20260922.md | 20260922 | judge_mode 显式化只读普查：全库 399 题的显式/默认切面（l922-116） | 已入库 | 0 |
| docs/insights/learn-judge-result-keep-design-20260924.md | 20260924 | learning「回访上一题保留判题结论」行为改动裁决稿（l924-05，只读，零生产码改动） | 未跟踪 | 0 |
| docs/insights/learn-lang-cards-layout-20260922.md | 20260922 | learning「各语言通过情况」5 卡断行均衡复核（l922-120，2026-09-22） | 已入库 | 0 |
| docs/insights/learn-metrics-dual-20260918.md | 20260918 | generate_metrics 归仓＋183/399 题量双口径对账（2026-09-19 晨间执行班，任务 l918-07） | 已入库 | 0 |
| docs/insights/learn-mtime-size-key-design-20260924.md | 20260924 | learning 错题本缓存键 mtime 单因子加强为 (mtime_ns,size) 设计稿：撞键场景实测（现状吞新题面／草案取新值，等长改写仍撞＝残留面）、11 行 diff 草案、在册影响实测红名集恰好 2 条（`test_mistakes_lookup_cache.py:219/:240`）、md5 成本 25.1× 故不顺手外扩（l924-07，只出设计零改码，收口 l923-19 登记项） | 未跟踪 | 0 |
| docs/insights/learn-notice-census-20260918.md | 20260918 | learning 散落 st.warning/info/error/success 裸用普查（2026-09-19 日间续班，任务 l918-26，只读零改动） | 已入库 | 0 |
| docs/insights/learn-pages-coverage-20260918.md | 20260918 | ui/pages 各页覆盖率缺口盘点（2026-09-19 晨间执行班，任务 l918-13，只读） | 已入库 | 0 |
| docs/insights/learn-path-claim-audit-20260924.md | 20260924 | learning path 文案 ⇄ 磁盘题数过期自述普查（l924-19，只读 · 零内容改动） | 未跟踪 | 0 |
| docs/insights/learn-path-coverage-fill-20260920.md | 20260920 | learning 补学习路径：42 个未引用 topic 全部进线（D5 落地） | 已入库 | 1 |
| docs/insights/learn-paths-order-consistency-20260922.md | 20260922 | learning path 双顺序通道一致性实测（l922-126，2026-09-22） | 已入库 | 1 |
| docs/insights/learn-paths-prereq-20260919.md | 20260919 | learning 五语言 lessons 与 paths prereqs 引用一致性（l920-08） | 已入库 | 1 |
| docs/insights/learn-plan-baseline-refresh-20260922.md | 20260922 | learning 对外基线口径刷新（l922-107，2026-09-22） | 已入库 | 1 |
| docs/insights/learn-plan-count-drift-20260917.md | 20260917 | learning plan.md 验收数字订正（916p-a3-011，2026-09-17） | 已入库 | 0 |
| docs/insights/learn-progressdb-census-20260918.md | 20260918 | data/progress.db 表结构快照体检（2026-09-19 日间续班，任务 l918-27，只读） | 已入库 | 0 |
| docs/insights/learn-r-plain-downgrade-20260920.md | 20260920 | r 题库判定模式显式化：84 题降级为普通题（D6 落地） | 已入库 | 0 |
| docs/insights/learn-readme-commands-audit-20260922.md | 20260922 | README 验证命令块只读巡检（l922-109，2026-09-22） | 已入库 | 0 |
| docs/insights/learn-readme-numbers-20260922.md | 20260922 | learning README 数字口径复现巡检（l922-108，2026-09-22） | 已入库 | 1 |
| docs/insights/learn-readme-tree-20260922.md | 20260922 | README 目录树 vs 磁盘清单核对（l922-131，2026-09-22） | 未跟踪 | 0 |
| docs/insights/learn-report-v065-reconcile-20260917.md | 20260917 | learning v0.6.5 报告指标对账（916p-a3-012，2026-09-17） | 已入库 | 0 |
| docs/insights/learn-requirements-reconcile-20260917.md | 20260917 | learning requirements.txt 与 freeze 口径核验（916p-a3-018，2026-09-17，只读） | 已入库 | 0 |
| docs/insights/learn-review-cache-lru-verdict-20260924.md | 20260924 | learning 点评缓存 FIFO→LRU 与分池两案裁决材料（l924-20，只出稿＋案序 · 零生产码改动） | 未跟踪 | 0 |
| docs/insights/learn-rubric-r1r3-20260918.md | 20260918 | agent_dev 48 道 rubric 题 R1-R3 规范对账（2026-09-19 晨间执行班，任务 l918-17，只读） | 已入库 | 0 |
| docs/insights/learn-shown-writeorder-design-20260923.md | 20260923 | dashboard 推荐曝光写序缺陷修法设计稿：emit 前 vs emit 后 ＋ 幂等键（l923-06，只出设计零改码） | 未跟踪 | 0 |
| docs/insights/learn-sidebar-218-20260915.md | 20260915 | learning 侧栏 218px 降级验收余项核验（n915-66，只读） | 已入库 | 0 |
| docs/insights/learn-skipped-audit-20260916.md | 20260916 | learning 7 个 skipped 测试核查与分类（l916-01，只读） | 已入库 | 0 |
| docs/insights/learn-sql-roworder-census-20260922.md | 20260922 | learning SQL 多行题行序判读普查（l922-129，2026-09-22，只读零改动） | 已入库 | 1 |
| docs/insights/learn-sql-roworder-design-20260923.md | 20260923 | SQL 排序语义题处置设计稿（l923-23，出口次序改推 C→A→B；expected_rows 为 sql 独占） | 已入库 | 0 |
| docs/insights/learn-tail-difficulty-design-20260923.md | 20260923 | cpp／sql／r 末档（4/5 档）难度上抬补题设计稿：三门 census＋25 格直方对平＋12 条候选 topic，不替三门写题也不猜 expected_output（l923-28，只出设计零改码；learn10 复核并推翻前档 4 条自述） | 未跟踪 | 0 |
| docs/insights/learn-test-baseline-20260921.md | 20260921 | learning 测试资产基线（l922-03，2026-09-21） | 已入库 | 0 |
| docs/insights/learn-tests-baseline-20260915.md | 20260915 | learning 仓 unittest 发现计数基线（n915-77，只读） | 已入库 | 0 |
| docs/insights/learn-thin-thick-topics-20260921.md | 20260921 | learning 薄/厚 topic 比例失衡分析与增题优先级（l922-07，2026-09-21） | 已入库 | 0 |
| docs/insights/learn-topic-dualnum-20260921.md | 20260921 | learning topic 双号冲突对账与影响判定（l922-05，2026-09-21） | 已入库 | 1 |
| docs/insights/learn-uncommitted-inventory-20260917.md | 20260917 | learning 未提交改动盘点与提交就绪度（916p-a3-019，2026-09-17，只读） | 已入库 | 0 |
| docs/insights/learn-untracked-tests-intake-20260917.md | 20260917 | learning 3 个未跟踪测试文件入库收口（916p-a3-016，2026-09-17） | 已入库 | 0 |
| docs/insights/learn-uploader-key-recycle-design-20260924.md | 20260924 | learning 学习数据导入位：换 widget key 让「被拦帧」文件消失 ＋ 陈旧键有界回收 裁决稿（l924-22，只出稿 · 零生产码改动） | 未跟踪 | 0 |
| docs/insights/learn-verify-commands-audit-20260917.md | 20260917 | learning README「验证」节 8 条命令可用性核验（916p-a3-013，2026-09-17） | 已入库 | 0 |
| docs/insights/learning-breakpoint-constant-20260913.md | 20260913 | learning 断点字面量收敛为常量（d913c-10，2026-09-13） | 已入库 | 0 |
| docs/insights/learning-dashboard-coverage-20260917.md | 20260917 | learning dashboard 覆盖率复核＋未覆盖段清单（917-37，只读零改动） | 已入库 | 0 |
| docs/insights/learning-dashboard-density-20260913.md | 20260913 | learning 面板页表格密度与列宽可读性（d913c-11，2026-09-13） | 已入库 | 0 |
| docs/insights/learning-empty-caption-tokens-20260914.md | 20260914 | 学习系统空态 caption 差异化样式 token 落点盘点（d914-36，2026-09-14，只读出稿） | 已入库 | 0 |
| docs/insights/learning-empty-state-20260913.md | 20260913 | learning 空态文案与样式统一（d913c-06，2026-09-13） | 已入库 | 0 |
| docs/insights/learning-ergo-diag-path-1366-20260913.md | 20260913 | learning 诊断/路径/语言/侧栏 1366 适配走查（d913c-01，2026-09-13） | 已入库 | 0 |
| docs/insights/learning-ergo-fix-20260912.md | 20260912 | learning 人体工学走查修复批报告（h912-13，2026-09-13 夜班） | 已入库 | 0 |
| docs/insights/learning-ergonomics-scan-20260911.md | 20260911 | learning 前端人体工学有界只读走查（2026-09-12 夜间执行班，任务 p911r-42，零改码） | 已入库 | 0 |
| docs/insights/learning-error-feedback-20260913.md | 20260913 | learning 错误提示统一 formatter（d913c-07，2026-09-13） | 已入库 | 0 |
| docs/insights/learning-focus-visible-20260913.md | 20260913 | learning 键盘焦点可见性（d913c-02，2026-09-13） | 已入库 | 0 |
| docs/insights/learning-insights-index-20260917.md | 20260917 | learning insights 索引与未引用清单核对（r917-20，p917-20 重投） | 已入库 | 0 |
| docs/insights/learning-line-length-20260913.md | 20260913 | learning 长文本区行宽收敛 ≤80ch（d913c-08，2026-09-13） | 已入库 | 0 |
| docs/insights/learning-metrics-recheck-20260917.md | 20260917 | learning 指标数字三处一致性复核（917-35，partial） | 已入库 | 0 |
| docs/insights/learning-narrow-sidebar-20260913.md | 20260913 | learning 窄窗（<1000px）侧栏关键入口可达性（d913c-12，2026-09-13） | 已入库 | 0 |
| docs/insights/learning-nav-current-item-20260913.md | 20260913 | learning 导航当前项高亮单源化（d913c-09，2026-09-13） | 已入库 | 0 |
| docs/insights/silent-except-batch2-20260913.md | 20260913 | learning 静默 except 续清批次（c-03，2026-09-13） | 已入库 | 0 |
| docs/insights/weekly-card-note-20260913.md | 20260913 | learning 周报卡口径提示落地（a-47/c-04，2026-09-13） | 已入库 | 0 |
