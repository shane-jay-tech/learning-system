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
> - 2026-09-25 出档班自登 1 份＝l924-26（RRunner／CppRunner `_version_key` 整路径抽数字**收敛设计稿** `learn-runnner-versionkey-20260924.md`，登记时未跟踪；只读出稿，探针在 gitignore 的 `tmp/l924-26/`，`core/runners/` 零 diff、`tests/` 零改动，三案一律未选）：复算哨兵 `tests/test_insights_index_closure.py` 同批 3 passed、A==B 且 C 空且重复 0 ⇒ 等式闭合（本行不写绝对条目数，照 l924-24 起口径）。否证卷宗一条前提：「盘上四条 fallback_glob 实测」预设盘上有 R-* 可比，实测**四条 pattern 全 0 命中**（全盘无 R 安装、`which Rscript` 亦 None）⇒ 本单的错序证据全部是**构造用例＋纯函数复算**（10 组，现法错序 6／修正法 0），非现网事故。附带发现（越界未修，见该档 §五-3）：`D:\tools\mingw64\bin` 在盘但**缺 `g++.exe`**（有 `gcc.exe`／`c++.exe`），故 cpp 侧五条 pattern 同样全空。
> - 2026-09-25 出档班自登 1 份＝l924-27（smoke_boot 硬编码 8599 ⇄ find_port 端口族统一**两案建议稿** `learn-smokeboot-port-design-20260924.md`，登记时未跟踪；只出稿，`scripts/`／`start.bat`／`launcher.pyw` 零 diff，探针在 gitignore 的 `tmp/l924-27/`，三案一律未选）：复算哨兵 `tests/test_insights_index_closure.py` 同批 3 passed、A==B 且 C 空且重复 0 ⇒ 等式闭合（本行不写绝对条目数，照 l924-24 起口径）。定向面现值 `tests/test_find_port.py` 8 passed／`tests/test_scripts.py` 22 passed rc=0，未跑全量。🔴 否证卷宗三条前提：① 「撞口→150 次超时→误报启动失败」不成立——Windows 下 uvicorn `config.py:583` 的 `SO_REUSEADDR` 令撞口 bind **照样成功**，探针实跑双监听、health 由**外来服务**应答 200 ⇒ 症状是**假绿**不是误报红（一次性子进程＋45 s 超时，被测件是 3 行 tiny_app 非 app.py，跑完复验端口释放）；② 该脚本全文**不含**"启动失败"字样（`rg` 空），属 `launcher.pyw:280/:287/:333/:388` 的措辞；③ 8599 ∉ 主服务端口段（`find_port` 8511-8530、launcher 8511+20）⇒ "start.bat 起主服务后 smoke_boot 撞口"的因果链不成立，真撞口对象是别的东西。另新发现第 3／4 处缺陷：`smoke_boot.py` 无 `sys.exit` ⇒ **rc 恒 0**，且子进程 `stdout=DEVNULL` 把唯一诊断丢掉。
> - 2026-09-25 出档班自登 1 份＝l924-28（`check_readme` 出口实跑对账·l924-12 xfail 前提底数 `learn-checkreadme-run-20260924.md`，登记时未跟踪；只读出稿，探针在 gitignore 的 `tmp/qoder-executor-20260925-0420-learn32/`，`README.md` 跑前跑后 SHA256 逐位不变、`scripts/` 零 diff）：复算哨兵 `tests/test_insights_index_closure.py` 同批 3 passed、A==B 且 C 空且重复 0 ⇒ 等式闭合（本行不写绝对条目数，照 l924-24 起口径）。定向面现值 `tests/test_readme_version_gate.py`＋哨兵合跑 5 passed／1 xfailed rc=0，未跑全量。实跑底数：`--check-readme README.md` **rc=1、红项恰 1 条**（标题版本），与 l924-12 的"成因数==1"桩在命令行侧独立对上。新查四条（卷宗未预设）：① 检点④号称查"路线图"，实为**全文子串且不整词**，而 README **根本没有路线图小节**（10 个标题逐条看完，"路线图/roadmap" 0 命中），靠 :3／:59 蒙过 ⇒ 将来只改一处版本号仍判绿；② `--strict` 在本机 GBK 下**静默失效**（子进程读线程 `UnicodeDecodeError` 被 `except Exception: pass` 吞 ⇒ `tests` 回落 865，与不带 `--strict` 同值；加 `PYTHONUTF8=1` 才读到真收集数 947），且 `metrics["tests"]` 既不进 `check_report` 也不进 `check_readme` ⇒ **`--strict` 从不改变 rc**；③ `--json` 与 `--check-readme` 同给时被 `elif` 链**整支吞掉**（stdout 与单跑 `--check-readme` 逐字相同），机器读方拿不到指标；④ `--check` 路径拼错是**裸 traceback＋rc=1**，与"数字不符"同码 ⇒ 钉判据须钉文案不钉 rc。另实测 `:245` 短路次序：现写法保诊断，若对调成 `ok and check_readme(...)` 则 report 判红时 README 的 FAIL 清单被吞（stdout 少 68 B）——**现写法不是笔误**，l924-12 别顺手"理顺"。本档一律建议稿、未选案。
> - 2026-09-25 同班续登 1 份＝l924-29（`ai_open_scored` 零行事件处置**三案裁决材料** `learn-aiopenscored-disposition-20260924.md`，登记时未跟踪；只读出稿，`core/judge.py` 零 diff、`git diff --stat -- core/judge.py` 无输出，探针 `tmp/qoder-executor-20260925-0420-learn32/probe_events.py` 全程 `mode=ro`＋`query_only=ON`，可比快照按纪律档 §十二 改用 `sqlite3` 的 `backup()` 单文件并**开两次比对**（12/12 字段一致），未跑仓内 backup/prune 脚本、零 DELETE/checkpoint）：复算哨兵 `tests/test_insights_index_closure.py` 同批 3 passed、A==B 且 C 空且重复 0 ⇒ 等式闭合（本行不写绝对条目数）。四检结论：① 存量 0 行**复算成立且跨时点稳定**（两份历史备份 0815／0904 同为 0、`prune_old_data` 无任何 .bat/.ps1 排程 ⇒ 零行＝未触发，非被清）；② 🔴 **否证卷宗案 B 的落点名**——`ai_judged` 全仓零命中（`rg -c "ai_judged"` rc=1），该族字段在盘上不存在，B 案必须先选真实落点（attempts 新列＝触 schema 迁移＋`data_portability:46` 导出列清单，故本档把 B 拆成 B1/B2/B3 并只推荐 B2）；③ 🔴 **否证 census D-5 的"LLM 用量唯一审计流水"**：缓存命中（`ai_review.py:435`）也写事件、`llm_ok=False` 的真调用**反而不留痕**，且 G2 门为假时 attempt/review_state/rubric/event **四表全不写** ⇒ "静默无痕"比卷宗写的更强，**连分母都拿不到**；④ 案 B/C 的"写而不读"不精确：`event_count()` 总数口径被 `dashboard.py:300` 显示＋`:213` 导出缓存键＋`backfill_events.py:36/92` 幂等基线**间接**消费。判据按实况收窄：卷宗建议的"近 30 日 attempts 开放题占比"**当下不可算**（`attempts` 近 30 日 0 行、全库最后一条事件 `created_at=2026-08-24` 距今 32 天 ⇒ 0/0；且 `attempts` 无 `judge_mode` 列，开放题身份只能靠 70 道开放题 id 白名单反推，而门为假时 attempt 不写 ⇒ 右删失样本，用它下线是循环论证）⇒ 本档改成"先造分母（A′ 失败侧计数）、再看阈值"的两段式判据表。**推荐 A′、C 的判据延后自动生效，一律未选案交人工**。顺带纠正 census 一处行号漂移：`if dimensions and attempt_id` 实在 `:326`（census 写 `:324`）。⚠ 本班自己踩到纪律 §十一.5 的 `rg -rn` replace 坑（一次普查 prune 排程时把命中词替换成 "n" 打出假象，已用 `rg -n` 重跑并复核），下班级别提醒：**`-r` 后面必须跟替换串，别把 `-r` 当 reverse**。
 > - 2026-09-28 主班代登 2 份＝l927-46／l927-47（README 首行版本串 ＋ test_version_consistency 提取器加固，两档登记时未跟踪）：复算 **A=117、B=117、C=空、重复=0 ⇒ 等式闭合**；哨兵 tests/test_insights_index_closure.py 同批复跑见班志。索引件由主班单点写。
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
| docs/insights/learn-aiopenscored-disposition-20260924.md | 20260924 | learning `ai_open_scored` 零行事件处置三案：门控链路图＋消费面/存量现值＋推荐案判据（l924-29，只出稿 · 零生产码改动） | 未跟踪 | 0 |
| docs/insights/learn-bank-cadence-20260915.md | 20260915 | verify-question-bank 纳入例行方案（n915-65，只出设计） | 已入库 | 0 |
| docs/insights/learn-caliber-note-premise-20260923.md | 20260923 | CALIBER_NOTE「阅读合并」前提交叉取证＋learning_events 账本重建量化：注记因果前提在全量 git 历史不成立（l923-24，纯只读，三选一待裁决） | 已入库 | 0 |
| docs/insights/learn-checkreadme-run-20260924.md | 20260924 | learning `check_readme` 出口实跑对账：rc／四检点现值／组合矩阵（l924-28，只出稿 · 零生产码改动） | 未跟踪 | 0 |
| docs/insights/learn-compare-inventory-20260916.md | 20260916 | learning 全仓同族比较逻辑清点（n916x-40，_cell_eq 语义校正后横向核验，只读） | 已入库 | 0 |
| docs/insights/learn-content-tags-census-20260924.md | 20260924 | learning content tags 词表普查（l924-24，409 件三轨对平＋416/265 现值＋消费面 rg/AST 双轨 ＋ 三案建议未选案） | 未跟踪 | 0 |
| docs/insights/learn-core-final-scan-20260924.md | 20260924 | learning core/ 函数级零测终扫台账（l924-23，双轨计数表＋终扫命令 ＋ `format_local_ts` 收口） | 未跟踪 | 0 |
| docs/insights/learn-coverage-reconcile-20260917.md | 20260917 | learning 覆盖率三口径对账（916p-a3-014，2026-09-17，只读） | 已入库 | 0 |
| docs/insights/learn-crlf-portrait-20260924.md | 20260924 | learning CRLF 逐目录×类型透视＋四类风险分类＋`core/achievements.py` 逐行实测＋≤3 批迁移建议（l924-30，只读 · n924-32 的增量档） | 未跟踪 | 0 |
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
| docs/insights/learn-runnner-versionkey-20260924.md | 20260924 | learning RRunner._version_key 整路径抽数字：盘上普查＋错序用例对照＋收敛设计稿（l924-26，只出稿 · 零生产码改动） | 未跟踪 | 0 |
| docs/insights/learn-shown-writeorder-design-20260923.md | 20260923 | dashboard 推荐曝光写序缺陷修法设计稿：emit 前 vs emit 后 ＋ 幂等键（l923-06，只出设计零改码） | 未跟踪 | 0 |
| docs/insights/learn-sidebar-218-20260915.md | 20260915 | learning 侧栏 218px 降级验收余项核验（n915-66，只读） | 已入库 | 0 |
| docs/insights/learn-skipped-audit-20260916.md | 20260916 | learning 7 个 skipped 测试核查与分类（l916-01，只读） | 已入库 | 0 |
| docs/insights/learn-smokeboot-port-design-20260924.md | 20260924 | learning smoke_boot 硬编码 8599 与 find_port 端口族统一：撞口复现＋两案对照＋推荐案验收口径（l924-27，只出稿 · 零生产码改动） | 未跟踪 | 0 |
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
| docs/insights/learn-tag-vocab-spec-20260925.md | 20260925 | 五轴标签规范与三清单（重复 / 大小写 / 未知）（120546-361f，2026-09-25） | 已入库 | 0 |
| docs/insights/l927-03-baseline.md | 20260927 | learning 测试基线复测：全量现值与 384→622→1162 漂移表（l927-03，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-04-ergonomics-status.md | 20260927 | plan.md 目标面对照＋浏览器实测前置否证（playwright 在环境、tests 零用）（l927-04，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-05-judge-security-review.md | 20260927 | 判题安全边界现状与 G1–G11 缺口清单（只读巡检）（l927-05，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-06-sampling.md | 20260927 | seed=20260927 抽 10 题核验＋全库重复直扫（l927-06，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-07-dashboard-regression.md | 20260927 | dashboard 1366 断点修复在位核对（blob 等值自证）＋定向 UI 子集（l927-07，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-08-crossrepo-boundary.md | 20260927 | learning×kaoyan 英语功能面跨仓对账：本仓 0 命中、该模块从未存在（l927-08，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-09-copy-audit.md | 20260927 | 全量反馈文案普查（101 条，A62/B3/C36）与 14 条问题清单（零文案改动）（l927-09，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-10-deps-health.md | 20260927 | 依赖钉死面对账：freeze 钉错对象（195/195 系统等、仅 50/195 等 .venv）＋两解释器各缺一包（l927-10，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-11-fs-constraint-adjudication.md | 20260927 | F-1 越界读写复核（写句柄被接受、主库三点取样不变）＋三案代价矩阵（l927-11，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-12-note.md | 20260928 | V-5「12 件未教 API」甲案落地：9 名在各自 lang 课文由 0 命中变 ≥1、10 份课文纯增 22 行、零题面／判分／DB；份数按「章内对应」而非语言级最小口径（l927-12，2026-09-28） | 已入库 | 0 |
| docs/insights/l927-13-note.md | 20260928 | 回填去重双键幂等修复（精确 attempt_id 键＋老行计数额度）：改前红 6→12 行、改后连跑三轮零新增，判据③全跑临时库（l927-13，2026-09-28） | 已入库 | 0 |
| docs/insights/l927-14-pause-adjudication.md | 20260927 | 暂停甲案等价性否证（生产面无 `review_state` 写入口、错题通道不看日期）＋两案代价（l927-14，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-16-offlinefallback.md | 20260928 | R-1 `_offline_fallback` 仓内表回退的裁决材料：覆盖 5/6 vs 2/6 当场重算、签名需加 lang——上游 154242 标「属生产码改动停人工闸后」⇒ 实现面已回退、只留材料（l927-16，2026-09-28） | 待人工择案 | 0 |
| docs/insights/l927-17-canonical-tag-design.md | 20260927 | canonical_tag() 别名层设计四要素＋26 点（实为并集）影响面对照（l927-17，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-18-case-mismatch.md | 20260927 | 期望答案大小写／同义异形对账；🔴 A 类＝题面写"也接受"而 `judge.py:259` 精确串比（l927-18，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-19-note.md | 20260928 | home 页两处失效链接按 /news/ 处置（403 归因继承 5d75，本单禁联网故非一手）；4 道 run 题用真 PythonRunner 实测⇒缺陷由「缺答案键」收窄为**只缺挂载**，三条修法全越题件红线故只出形状（l927-19，2026-09-28） | 待人工择案 | 0 |
| docs/insights/l927-20-similar-design.md | 20260927 | 相似题互链两形态十二维对比＋loader 接入面 6 点（推荐 B 作证据层，未落字段）（l927-20，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-21-ai-echo-risk.md | 20260927 | AI 回显风险可归因池由 148 收窄到 36 道；两案判断题（补禁令 vs 零调用阶段 0）（l927-21，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-22-handoff.md | 20260927 | 日间人工窗取证交接：两读数方法-命令-判据-安全注意；回环性全押 config.toml 一行（l927-22，2026-09-27） | 已入库 | 0 |
| docs/insights/l927-29-note.md | 20260928 | 点击侧写序翻面（emit 送达成功才 navigate）＋新 2 例＋l922-101/102 那 3 例按裁决翻面；4 组变异实测 M1 回旧形态恰红那 3 例、M3 过度修正红另 3 例。⚠ 交回一条不一致：今日推荐失败不跳、跨路径 :447-458 失败仍跳，且 l924-01 当年拉齐方向相反 ⇒ 别默认（l927-29，2026-09-28） | 待人工择案 | 0 |
| docs/insights/l927-30-except294.md | 20260928 | 任务书前提已被 `b575e0d`／`38ad3bb` 关单（改前红判据 4→5 逐定位）；新出裁决项＝`ui/pages/path.py:207/:216` 两枚裸 emit，甲案属 UI 生产码需写位班（l927-30，2026-09-28） | 待人工择案 | 0 |
| docs/insights/l927-31-uploader-residue.md | 20260928 | streamlit 1.58.0 AppTest 否证 `dashboard.py:332-335` 两半句：pop 不抛（守卫只挂 `__setitem__`）／陈旧键会留但有界（6→7→8→8）；推荐乙先落一行 caption，甲须三件同批（l927-31，2026-09-28） | 待人工择案 | 0 |
| docs/insights/l927-32-note.md | 20260928 | README 验证块 8 条命令逐条实测副作用后加行尾标注（只读／写盘／需日间）；主班复核：剥注释后的 36 条命令本体与顺序同 HEAD 完全一致⇒判据②成立；smoke_boot 那格未一手实测（禁起服务），依据＝源码＋netstat 8599 零行（l927-32，2026-09-28） | 已入库 | 0 |
| docs/insights/l927-33-sentinel-implicit.md | 20260928 | 闭合哨兵隐含条件清单：15 条靠巧合（I5 已在册显式）＋D1-D8 断言草案；🔴 I13 实测索引头回填读数停在 09-25 的值而磁盘条目已漂 30 条**且全绿**；l924-17 设计稿复核至今未落地（l927-33，2026-09-28） | 待人工择案 | 0 |
| docs/insights/l927-37-writeseq.md | 20260928 | 跨路径区曝光写序换 A2（emit→add→impressions），例B④＋例C 两靶子翻绿；5 组变异有牙（M2「add/impressions 对调」只由新增 §九例2 抓到）。⚠ 本班明写未照 l923-06/07 的「两区同批」做（卷宗只点名跨路径区）⇒ 两区曝光写序自此不一致，与 l927-29 的点击侧不一致是两格（l927-37，2026-09-28） | 待人工择案 | 0 |
| docs/insights/l927-39-bound-tighten.md | 20260928 | 判据①无对象：两处松下界早由 l923-12（test_paths.py:35）／l924-14（test_scripts.py:319）收成 ==6，行号亦漂移 ⇒ 零 diff；残留宽界五格＋4 组连坐探针（实测连坐 0）写成可批形状交裁（l927-39，2026-09-28） | 待人工择案 | 0 |
| docs/insights/l927-40-lifecycle2.md | 20260928 | 第二终点＝档内「出口一」独立有界队列 _variant_lru（cap 沿用 _LRU_CAP，溢出走现成 _retire_variant），新增 7 例含离开路径与代价钉子；退回原题侧 15 例一字未动仍绿（l927-40，2026-09-28） | 已入库 | 0 |
| docs/insights/l927-43-recolor.md | 20260928 | 按推荐档 A 落 #4547B9（三处逐字替换、3px/offset 未动）＋同笔订正 :211 注释版本；在册浅色六面复算 min 6.41:1、复算器改前 rc=1／改后 rc=0、反向自证旧值 1.49<3。⚠ 判据③只到亮态：本仓无暗态载体（无 html.dark／prefers-color-scheme／theme.base 未设）⇒ 未造空壳断言；12 站目检＝待人工，零目检结论（l927-43，2026-09-28） | 待人工目检 | 0 |
| docs/insights/l927-45-note.md | 20260928 | 公开部署提示补 AppTest 级证据：真环境变量→真 is_public_deploy→真 st.error 四档渲染（公开/默认/PUBLIC_DEPLOY=1/值≠1），6 例、五刀内存变异零漏抓（M3 证该分支改前渲染层零证据）；生产码零改动。另否证 l923-18 那份 12 站行号 11/12 已漂（现取 dashboard 4／language 6／mistakes 1／path 1＝12，旧档正文「language 5」自相矛盾）（l927-45，2026-09-28） | 已入库 | 0 |
| docs/insights/l927-46-note.md | 20260928 | README 首行补裸版本串（V2 形状）：--check-readme rc=1→0、test_version_consistency 10 passed。⚠ 否证在册说法一处在册预述——l924-12「首行补串不会误红 version 一致性桩」按其建议的 `# … v{VERSION}` 形状补会当场红（:73 双写==2 判据，实测 [1, 3, 59]）；同批连带收口 tests/test_readme_version_gate.py 三条（删 xfail 桩＋两例翻正更名），不收口则全量 3 红（l927-46，2026-09-28） | 已入库 | 0 |
| docs/insights/l927-47-note.md | 20260928 | test_version_consistency 的 splitlines()[2] 改按「# 」标记取（新提取器 C ＋3 例，10→13 passed）；「改前必红」用 git show HEAD: 的旧断言本体在位移副本上真跑红，三刀变异 M1 红 3/4、M2/M3 红 4/4；生产码与题件零接触（l927-47，2026-09-28） | 已入库 | 0 |
| docs/insights/l927-48-fake4.md | 20260928 | FakeStreamlit 四处失明面收口：button/expander/tabs/columns 落 calls 记 (name,args,kwargs)、返回值逐项不变；单件 26→30 passed，fake 域 25 枚消费件 298 passed。有牙证据＝HEAD 类体同条件探针 n_calls 0／names_recorded 空 对比工作树 4／四格齐。⚠ container／spinner 同型格不在卷宗点名面，本单按 4 格收口并把该边界钉成断言；六枚带私有录制版的消费件撤除属裁决面未碰（l927-48，2026-09-28） | 已入库 | 0 |
| docs/insights/l927-49-note.md | 20260928 | dashboard 今日推荐区 pid_key 在 try 外裸取（KeyError 会带走整页后半段）收口为预检形态：21+/1−，记账与渲染两循环同吃 checked；⚠ 卷宗首选的「挪进 try」单独收不住判据②——渲染循环 LANG_META[it.lang] 同格裸奔（实跑证实），故走许可的预检支。新增 §十 1 例 50+/0−（既有 25 例一字未动），改前 RAISED KeyError 对比改后 NO_RAISE、4 卡 4 发（l927-49，2026-09-28） | 已入库 | 0 |
