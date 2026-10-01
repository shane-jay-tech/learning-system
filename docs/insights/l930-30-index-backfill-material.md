# l930-30 insights 索引欠账总汇编（learning 域；只出材料不改索引本体）

## 一、双读数与哨兵现状（命令先于数字）

```
磁盘（不含索引自身）= 148 ｜ 索引引用（learn-insights-index-20260918.md 的 `*.md` 反引号集合）= 24
欠登 = 123 ｜ 红名 = 3（PROTOCOL.md／README.md／plan.md——仓库根文件，非 insights 档）
哨兵：pytest tests/test_insights_index_closure.py → 2 failed, 1 passed（l927-40 在册读数复现）
```

## 二、红名迷惑面说明（I13/I15，供下一班直接引用）

- **红名 3 枚不是欠登**：`PROTOCOL.md`/`README.md`/`plan.md` 是**仓库根**文件——索引文本里引用了它们
  （如工作流指引），哨兵只比路径集合 ⇒ 它们成了「索引里有、磁盘 insights/ 里没有」的假红名。
  处置建议：哨兵改比较「`docs/insights/` 目录限定下的集合」（I13/D 系已给草案），或索引引用时写全相对路径——二选一，交人工。
- **I13 头注停更**：索引头部的收录数回填读数停在 09-25（与磁盘差 30 条且全绿）——哨兵不比头注条目数，
  属「头注是历史陈述」的既定口径（kaoyan 域 k930-85 同判：历史陈述保留、最新陈述追加）。无需修，登记即可。
- **I15 红名成对**：哨兵的有牙自检例起手 `assert 现值闭合` ⇒ 盘子不闭合时自检例也红，
  按红名数估缺陷数会**翻倍**（l927-33 I15 在册）。读数时 2 failed 只代表 1 个缺登事实。

## 三、批量补登行材料（123 行，程序生成：各档首标题行＋档内单号；非手抄）

| 落点 | 标题行 | 单号 |
|---|---|---|
| `agent-dev-rubric-review-20260905.md` | agent_dev 开放题 rubric 评分设计质量评审（只评不改，2026-09-05 夜 1022）  |
| `content-quality-sample-20260905.md` | 编程题库抽样质量评审（seed=20260905，psy-C…/learning 100c）  |
| `l927-01-interrupt.md` | l927-01 — Pyodide 死循环挂起修复：判题超时护栏（75fb 修法一落地） ｜单号：l927-01／l927-05 |
| `l927-02-caret.md` | l927-02 — error_feedback 列定位补齐：Python/R/SQL caret 列纯函数（D-12 修法） ｜单号：l927-02 |
| `l927-03-baseline.md` | learning 测试基线复测（384 基线后漂移）——l927-03，2026-09-27 ｜单号：l927-03／l922-03／n922-10／l922-107 |
| `l927-04-ergonomics-status.md` | learning plan.md 目标面对照：人体工学／1366 适配／键盘焦点后续——l927-04，2026-09-27 ｜单号：l927-04／l922-120／l918-09 |
| `l927-05-judge-security-review.md` | learning 判题安全边界复核（执行安全域年度巡检）——l927-05，2026-09-27 ｜单号：l927-05／l924-27 |
| `l927-06-sampling.md` | 题库格式与 kp 标签一致性抽检（10 条种子抽样） ｜单号：l927-06 |
| `l927-07-dashboard-regression.md` | dashboard.py:85 五列挤压回归复核（B-131 修后） ｜单号：l927-07／l927-04／l922-120／l924-32 |
| `l927-08-crossrepo-boundary.md` | learning English 阅读模块与 kaoyan 侧的分工边界核查 ｜单号：l927-08 |
| `l927-09-copy-audit.md` | l927-09 learning 通知/反馈文案一致性抽检（错别字／术语统一／中英混排） ｜单号：l927-09 |
| `l927-10-deps-health.md` | l927-10 learning 依赖与运行环境健康检查（requirements／node 双面，只读零安装） ｜单号：l927-10／l927-03 |
| `l927-11-fs-constraint-adjudication.md` | l927-11 判题沙箱文件系统零约束（F-1）：越界读写取证复核与三案代价裁决材料 ｜单号：l927-11／l927-10／l927-09／l927-05 |
| `l927-12-note.md` | 12 件未教 API 补课文（V-5 甲案）执行记录 ｜单号：l927-12 |
| `l927-13-note.md` | 回填去重双键化（l927-13）执行记录 ｜单号：l927-13／l927-12 |
| `l927-14-pause-adjudication.md` | l927-14 复习「暂停」态：甲案／乙案裁决材料（只读，零码改动） ｜单号：l927-14 |
| `l927-15-judge-k123.md` | l927-15 — judge.py K-1/K-2/K-3 判据改码（154241 Q-1 验收③最小方案） ｜单号：l927-15 |
| `l927-16-offlinefallback.md` | LLM 挂了也不该只会说「请稍后再试」——离线兜底接上仓内表 ｜单号：l927-16／l927-12 |
| `l927-17-canonical-tag-design.md` | l927-17 `canonical_tag()` 只读别名层设计 ＋ 映射方向裁决材料 ｜单号：l927-17 |
| `l927-18-case-mismatch.md` | l927-18 期望答案大小写／口径不一清单与裁决材料（只读，零写库、零判题改动） ｜单号：l927-18 |
| `l927-19-note.md` | home 页 openai.com/blog 失效链接处置 ＋ 4 道 run 题资源路径核对——l927-19，2026-09-28 ｜单号：l927-19／l927-24／l927-01 |
| `l927-20-similar-design.md` | 相似题互链：形态对比 ＋ loader 接入面 ＋ 数据来源论证 ｜单号：l927-20／l927-18／l922-04 |
| `l927-21-ai-echo-risk.md` | AI 回显期望输出：148 题口径复核 ＋ 离线小样本方案 ＋ 两案 ｜单号：l927-21／l927-18／l922-10／l923-05 |
| `l927-22-handoff.md` | K-2 两枚运行时读数：取证清单 ＋ 静态面汇编 ｜单号：l927-22 |
| `l927-23-note.md` | l927-23 — py -3 降级通道 GBK 编码缺陷修复（l922-01 遗留） ｜单号：l927-23／l922-01／l922-116 |
| `l927-24-crlf.md` | l927-24 — CRLF 三件套统一 LF（l922-04 遗留；.gitattributes ＋ 点名文件规范化 ＋ 复跑） ｜单号：l927-24／l922-04 |
| `l927-25-topicnum-adjudication.md` | 专题号数语义三案裁决材料（l927-25，2026-09-29｜只读，零写数据） ｜单号：l927-25／l922-05 |
| `l927-26-topdiff-list.md` | l927-26 cpp / sql / r 末档难度上抬补题清单（内容侧，只出清单不写题） ｜单号：l927-26／l922-06／l923-28／l923-03 |
| `l927-27-p0-nine.md` | l927-27 — thin-topic P0 补题执行（l922-07 遗留；cpp 两目录净增 5 题，全库 403→408） ｜单号：l927-27／l922-07／l923-03／l922-128 |
| `l927-28-precheck-list.md` | 派单侧「点名文件投产前」检查清单＋落点缺陷族盘点（l927-28，2026-09-29｜零改模板本体） ｜单号：l927-28／l922-08／l922-09／l922-10 |
| `l927-29-note.md` | dashboard 今日推荐点击侧写序翻面：emit 送达成功才跳转——l927-29，2026-09-28 ｜单号：l927-29／l922-101／l922-102／l924-01 |
| `l927-30-except294.md` | dashboard 跨路径区「:294 无异常处理」误判订正（l927-30，只读位·零改动） ｜单号：l927-30／l922-103／l923-07／l924-01 |
| `l927-31-uploader-residue.md` | 导入反馈 uploader 残留交互裁决材料（l927-31，只读位·零码改动） ｜单号：l927-31／l922-105／l923-09 |
| `l927-32-note.md` | README 验证块逐条实测副作用 ＋ 属性标注——l927-32，2026-09-28 ｜单号：l927-32／l922-109／l927-19／l927-29 |
| `l927-33-sentinel-implicit.md` | insights 索引闭合哨兵「权威索引」隐含条件清单与显式化裁决材料（l927-33，只读位·零码改动） ｜单号：l927-33／l923-01／l924-17 |
| `l927-34-metamigrate.md` | meta 逗号串存量迁移「一次性 vs 惰性维持」两案裁决材料（l927-34，只出材料 · 零写库 · 零 git 操作） ｜单号：l927-34／l923-04／l924-18 |
| `l927-35-fifo-lru.md` | FIFO→LRU 升级影响面与测试改写清单·两案裁决材料（l927-35，只出材料 · 不动桩 · 不动生产码 · 零 git） ｜单号：l927-35／l923-05／l924-20／l927-56 |
| `l927-36-funnel-a2a3.md` | A2 残余风险量化／A3 计数口径变更影响／两区写序一致性——l923-06 三条待裁决的汇编材料（l927-36，只读、零写数据） ｜单号：l923-06／l927-36／l923-07／l927-37 |
| `l927-37-writeseq.md` | 跨路径区曝光写序换 A2（emit 先、成功后落本地账）：l927-37，2026-09-28 ｜单号：l927-37／l923-07／l923-06／l927-29 |
| `l927-38-dash-commit-plan.md` | dashboard 三单共改·归位对账材料（l927-38，实况收窄版 · 零 git 操作） ｜单号：l927-38／l923-11／l923-09／l923-10 |
| `l927-39-bound-tighten.md` | paths 松下界收紧单·现值实测：l927-39，2026-09-28 ｜单号：l927-39／l923-12／l924-14／l922-108 |
| `l927-40-lifecycle2.md` | 变式题六族键的第二生命周期终点：独立有界队列 `_variant_lru`——l927-40，2026-09-28 ｜单号：l927-40／l923-15／l924-03／l924-04 |
| `l927-41-variant3cases.md` | A／B／B′ 变式题三选一的终版裁决材料（l927-41，只读 · 不动桩 · 不动生产码 · 零 git） ｜单号：l927-41／l924-04／l924-03／l927-40 |
| `l927-42-display-gate.md` | l927-42 展示门 N／P／E 三案终版裁决材料（不选路、不改判据、不动展示门代码） ｜单号：l927-42／l924-05／l927-26／l927-40 |
| `l927-43-recolor.md` | 焦点环改色落地（档 A＝实色 #4547B9）＋对比度复算＋12 站目检调用指引 ｜单号：l927-43／l924-06／l923-18 |
| `l927-44-atmost-confirm.md` | 「· 至多」口径联动确认单：HEAD 复点＝**不多余**，据此终结 l924-09 遗留 1 的疑点（l927-44，只读 · 不动桩 · ｜单号：l924-09／l927-44／l924-08／l923-20 |
| `l927-45-note.md` | 公开部署分支的 AppTest 双档渲染证据（l927-45） ｜单号：l927-45／l924-10／l927-43／l927-29 |
| `l927-46-note.md` | README 首行版本串补齐·形态取舍与现值实测：l927-46，2026-09-28 ｜单号：l927-46／l924-12／l924-11／l927-47 |
| `l927-47-note.md` | version 一致性 head 行断言加固·标记取法与位移牙：l927-47，2026-09-28 ｜单号：l927-47／l927-46／l924-11／l923-22 |
| `l927-48-fake4.md` | l927-48：FakeStreamlit 四处入参失明面收口（桩侧，生产码零改动） ｜单号：l927-48／l924-02／l924-05 |
| `l927-49-note.md` | l927-49：畸形推荐项 `pid_key` try 外暴露面收口（预检形态） ｜单号：l927-49／l924-01／l923-08／l927-48 |
| `l927-50-retake-true.md` | retake_intent「兼容旧布尔 True」口子两案裁决材料（l927-50，只出材料 · 零生产码改动 · 零 git 操作） ｜单号：l927-50／l923-14 |
| `l927-51-skip7-handoff.md` | 七例恒 skip 的 g++/Rscript 环境缺口：现值复核与日间移交清单（l927-51，零安装 · 零联网 · 零越界写） ｜单号：l927-51／l922-03／l927-52 |
| `l927-52-baseline-refresh.md` | learn 测试基线现值刷新（622 之后的一页现值卡）——l927-52，2026-09-29 ｜单号：l927-52／l922-107／l927-50／l927-51 |
| `l927-53-note.md` | quick_stats s5 过期文案：锚点漂移核验与防回归缺口（l927-53） ｜单号：l927-53／l922-11／l923-13／l923-12 |
| `l927-54-note.md` | 85==85 读解风险注记 ＋ 下游覆盖率类读数清单（l927-54，2026-09-29） ｜单号：l927-54／l922-02／l922-125／l923-03 |
| `l927-55-note.md` | 导出缓存「命中／未命中」两条分支的行为钉桩（l927-55） ｜单号：l927-55／l922-104／l927-53 |
| `l927-56-note.md` | 点评缓存 FIFO 断言面补齐（现状钉桩）＋ LRU 升级衔接清单（l927-56） ｜单号：l927-56／l923-05／l927-35／l924-20 |
| `l927-57-reds-ledger.md` | learning＋kaoyan 在册红归因台账（l927-57，2026-09-29 05:4x） ｜单号：l927-57／k927-120／k921-01／k927-26 |
| `l930-02-writeseq-note.md` | l930-02 今日推荐曝光写序拉齐记录（A2 落地，旧向新看齐） ｜单号：l930-02／l927-37／l924-01 |
| `l930-03-click-note.md` | l930-03 两区点击语义拉齐记录（失败仍跳＝统一契约） ｜单号：l930-03／l927-29／l923-07／l930-02 |
| `l930-10-download-guards-note.md` | l930-10 报告下载按钮看守补齐记录（k927-38 遗留①收口） ｜单号：l930-10／k927-38／l924-02／l927-38 |
| `l930-11-gap-claim-sentinel.md` | l930-11 缺口占位命题防回归桩落地记录（l927-53 note §三 可批形状兑现） ｜单号：l930-11／l927-53／l927-55 |
| `l930-12-fingerprint-note.md` | l930-12 导出缓存指纹升级记录（行数级 → 每表 COUNT＋MAX(时戳) 组合） ｜单号：l930-12／l922-104 |
| `learn-384-7-caliber-20260918.md` | learning pytest「384/7」口径澄清留档（2026-09-19 晨间执行班，任务 l918-01，零改动） ｜单号：l918-01 |
| `learn-bank-cadence-20260915.md` | verify-question-bank 纳入例行方案（n915-65，只出设计） ｜单号：n915-65 |
| `learn-compare-inventory-20260916.md` | learning 全仓同族比较逻辑清点（n916x-40，_cell_eq 语义校正后横向核验，只读）  |
| `learn-coverage-reconcile-20260917.md` | learning 覆盖率三口径对账（916p-a3-014，2026-09-17，只读）  |
| `learn-crlf-portrait-20260924.md` | learning 全仓 CRLF 逐目录×类型透视（l924-30 · 只读增量档） ｜单号：l924-30／n924-32／l924-26 |
| `learn-d5d6-review-fix-20260920.md` | D5/D6 处置记录：agent_mastery 时数、judge_mode 等价性证明、迁移脚本加固 ｜单号：l920-09 |
| `learn-dashboard-768-fold-budget-20260922.md` | dashboard 首屏 768 纵向预算静态推演（1366×768，l922-117） ｜单号：l922-117 |
| `learn-dashboard-coverage-20260917.md` | dashboard.py 渲染主路径补测（916p-a3-015，2026-09-17，只增测试）  |
| `learn-deps-suspects-20260918.md` | pywebview / streamlit-ace 疑点依赖只读核报（2026-09-19 晨间执行班，任务 l918-08，零改动） ｜单号：l918-08 |
| `learn-difficulty-histogram-20260921.md` | learning 难度分布第三轮：末档空洞普查与判定（l922-06，2026-09-21） ｜单号：l922-06／l923-03／l922-05 |
| `learn-focus-surface-audit-20260922.md` | learning 键盘焦点覆盖面静态审计（unsafe_allow_html 面，l922-118，2026-09-22） ｜单号：l922-118 |
| `learn-insights-intake-20260917.md` | learning docs/insights 未入库报告收口（916p-a3-017，2026-09-17） ｜单号：n915-77 |
| `learn-judge-edges-20260916.md` | learning judge 三函数反例边界补测（l916-02） ｜单号：l916-02 |
| `learn-judge-mode-census-20260922.md` | judge_mode 显式化只读普查：全库 399 题的显式/默认切面（l922-116） ｜单号：l922-116 |
| `learn-lang-cards-layout-20260922.md` | learning「各语言通过情况」5 卡断行均衡复核（l922-120，2026-09-22） ｜单号：l922-120／l922-117 |
| `learn-metrics-dual-20260918.md` | generate_metrics 归仓＋183/399 题量双口径对账（2026-09-19 晨间执行班，任务 l918-07） ｜单号：l918-07 |
| `learn-mtime-size-key-design-20260924.md` | 缓存键由 mtime 单因子加强为 (mtime, size)：改法草案 ｜单号：l924-07／l923-19／l924-08 |
| `learn-notice-census-20260918.md` | learning 散落 st.warning/info/error/success 裸用普查（2026-09-19 日间续班，任务 l918 ｜单号：l918-26／l918-19 |
| `learn-pages-coverage-20260918.md` | ui/pages 各页覆盖率缺口盘点（2026-09-19 晨间执行班，任务 l918-13，只读） ｜单号：l918-13 |
| `learn-path-coverage-fill-20260920.md` | learning 补学习路径：42 个未引用 topic 全部进线（D5 落地） ｜单号：l920-08 |
| `learn-paths-order-consistency-20260922.md` | learning path 双顺序通道一致性实测（l922-126，2026-09-22） ｜单号：l922-126／l922-05 |
| `learn-paths-prereq-20260919.md` | learning 五语言 lessons 与 paths prereqs 引用一致性（l920-08） ｜单号：l920-08／l922-02／l927-54／l918-28 |
| `learn-plan-baseline-refresh-20260922.md` | learning 对外基线口径刷新（l922-107，2026-09-22） ｜单号：l922-107／l922-03／l922-04／l922-05 |
| `learn-plan-count-drift-20260917.md` | learning plan.md 验收数字订正（916p-a3-011，2026-09-17） ｜单号：l916-02 |
| `learn-progressdb-census-20260918.md` | data/progress.db 表结构快照体检（2026-09-19 日间续班，任务 l918-27，只读） ｜单号：l918-27／l930-26／l918-02 |
| `learn-r-plain-downgrade-20260920.md` | r 题库判定模式显式化：84 题降级为普通题（D6 落地） ｜单号：l920-02 |
| `learn-readme-commands-audit-20260922.md` | README 验证命令块只读巡检（l922-109，2026-09-22） ｜单号：l922-109 |
| `learn-readme-numbers-20260922.md` | learning README 数字口径复现巡检（l922-108，2026-09-22） ｜单号：l922-108／l922-131 |
| `learn-report-v065-reconcile-20260917.md` | learning v0.6.5 报告指标对账（916p-a3-012，2026-09-17）  |
| `learn-requirements-reconcile-20260917.md` | learning requirements.txt 与 freeze 口径核验（916p-a3-018，2026-09-17，只读）  |
| `learn-rubric-r1r3-20260918.md` | agent_dev 48 道 rubric 题 R1-R3 规范对账（2026-09-19 晨间执行班，任务 l918-17，只读） ｜单号：l918-17 |
| `learn-sidebar-218-20260915.md` | learning 侧栏 218px 降级验收余项核验（n915-66，只读） ｜单号：n915-66 |
| `learn-skipped-audit-20260916.md` | learning 7 个 skipped 测试核查与分类（l916-01，只读） ｜单号：l916-01 |
| `learn-sql-roworder-census-20260922.md` | learning SQL 多行题行序判读普查（l922-129，2026-09-22，只读零改动） ｜单号：l922-129／l922-127／l921-03 |
| `learn-sql-roworder-design-20260923.md` | learning SQL 行序题处置设计稿：出口 A/B/C 可行性对照（l923-23，2026-09-23，零改动） ｜单号：l923-23／l922-129／l923-21／l921-03 |
| `learn-tag-vocab-spec-20260925.md` | 五轴标签规范与三清单（重复 / 大小写 / 未知） ｜单号：l924-24 |
| `learn-test-baseline-20260921.md` | learning 测试资产基线（l922-03，2026-09-21） ｜单号：l922-03／l921-02／l921-03／l921-01 |
| `learn-tests-baseline-20260915.md` | learning 仓 unittest 发现计数基线（n915-77，只读） ｜单号：n915-77／l922-03／n915-66 |
| `learn-thin-thick-topics-20260921.md` | learning 薄/厚 topic 比例失衡分析与增题优先级（l922-07，2026-09-21） ｜单号：l922-07／l922-06／l922-05／l923-03 |
| `learn-topic-dualnum-20260921.md` | learning topic 双号冲突对账与影响判定（l922-05，2026-09-21） ｜单号：l922-05 |
| `learn-uncommitted-inventory-20260917.md` | learning 未提交改动盘点与提交就绪度（916p-a3-019，2026-09-17，只读）  |
| `learn-untracked-tests-intake-20260917.md` | learning 3 个未跟踪测试文件入库收口（916p-a3-016，2026-09-17）  |
| `learn-verify-commands-audit-20260917.md` | learning README「验证」节 8 条命令可用性核验（916p-a3-013，2026-09-17）  |
| `learning-breakpoint-constant-20260913.md` | learning 断点字面量收敛为常量（d913c-10，2026-09-13）  |
| `learning-dashboard-coverage-20260917.md` | learning dashboard 覆盖率复核＋未覆盖段清单（917-37，只读零改动）  |
| `learning-dashboard-density-20260913.md` | learning 面板页表格密度与列宽可读性（d913c-11，2026-09-13）  |
| `learning-empty-caption-tokens-20260914.md` | 学习系统空态 caption 差异化样式 token 落点盘点（d914-36，2026-09-14，只读出稿）  |
| `learning-empty-state-20260913.md` | learning 空态文案与样式统一（d913c-06，2026-09-13）  |
| `learning-ergo-diag-path-1366-20260913.md` | learning 诊断/路径/语言/侧栏 1366 适配走查（d913c-01，2026-09-13）  |
| `learning-ergo-fix-20260912.md` | learning 人体工学走查修复批报告（h912-13，2026-09-13 夜班）  |
| `learning-ergonomics-scan-20260911.md` | learning 前端人体工学有界只读走查（2026-09-12 夜间执行班，任务 p911r-42，零改码）  |
| `learning-error-feedback-20260913.md` | learning 错误提示统一 formatter（d913c-07，2026-09-13）  |
| `learning-focus-visible-20260913.md` | learning 键盘焦点可见性（d913c-02，2026-09-13）  |
| `learning-line-length-20260913.md` | learning 长文本区行宽收敛 ≤80ch（d913c-08，2026-09-13）  |
| `learning-metrics-recheck-20260917.md` | learning 指标数字三处一致性复核（917-35，partial）  |
| `learning-narrow-sidebar-20260913.md` | learning 窄窗（<1000px）侧栏关键入口可达性（d913c-12，2026-09-13）  |
| `learning-nav-current-item-20260913.md` | learning 导航当前项高亮单源化（d913c-09，2026-09-13）  |
| `silent-except-batch2-20260913.md` | learning 静默 except 续清批次（c-03，2026-09-13）  |
| `weekly-card-note-20260913.md` | learning 周报卡口径提示落地（a-47/c-04，2026-09-13）  |

## 四、落地建议（交主班/下一班）

1. **整表追加**：在索引「目录」末尾新增一节（如「其它（未归族，按文件名序）——123 份」），
   把 §三 整表粘入；头部按域内惯例追加一条对账陈述（现取读数＋生成方式声明）。
2. **哨兵双红自消**：补登后 `test_insights_index_closure.py` 应回 3 passed（I15 的成对红同时消）。
3. **可选加固**：哨兵改目录限定比较（消红名假阳性）——判据面改动，另单。
4. 本档零改索引本体（卷宗「只出材料」口径）。
