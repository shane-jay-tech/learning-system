# 编程题库抽样质量评审（seed=20260905，psy-C…/learning 100c）

- 抽样：seed=20260905，6 轨道分层（python 4 / cpp 4 / agent_dev 3 / r 3 / sql 3 / paths 3），共 20 项；抽样清单与洗牌方式可复现（random.shuffle 后取前 N）。
- 验证手段：python/sql 题用**沙盒执行**参考解（.venv 解释器 / sqlite3 内存库，均在系统临时目录）；cpp/r 无本地工具链，做逻辑复核并标注。
- paths 三个 yaml 为学习路径文档（milestones），非题目，仅结构性检查。

## 一、逐题评语与分级

| # | 轨道 | 题目 | 分级 | 评语 |
|---|---|---|---|---|
| 1 | python/11_matplotlib/01_line_max | 画折线图输出最大值 | 建议 | 沙盒验证输出 7 ✓、matplotlib 可导入 ✓。但判定只核对 stdout「7」，题干要求的 line.png 未纳入判定——题面要求与判定口径不一致 |
| 2 | python/06_strings/03_reverse_str | 反转字符串 | 可不修 | 沙盒验证 olleH ✓；题干示例与 tests 一致 |
| 3 | python/21_hr_viz/02_salary_box | 部门薪资箱线图（ai_open） | 可不修 | rubric 4 条具体可判（boxplot/分组/转角/存图）；依赖 content/datasets/hr_employees.csv，建议在题面标注数据文件路径不变性假设 |
| 4 | python/05_lists/05_mode | 众数（并列取最小） | 建议 | 沙盒验证并列取最小输出 5 ✓；题面已明示并列规则。但 tests 仅 1 组，建议补「无并列」「负数」两组 |
| 5 | cpp/12_file_io/03_sum_words | 写文件再求和 | 可不修 | 40=3+5+7+11+14 算术 ✓；逻辑复核写/读分离符合题意（本地无 g++，未编译验证） |
| 6 | cpp/04_functions/03_factorial_recursion | 阶乘递归 | 建议 | 10!=3628800 ✓（long long 防溢出设计合理）；tests 仅 n=10 一组，建议补 n=0 边界（1!与 0!=1） |
| 7 | cpp/08_inheritance/04_abstract_class | 抽象类纯虚函数 | 可不修 | 3.14159×25=78.5398→78.54 ✓（题面指定 π 精度，判定无歧义） |
| 8 | cpp/11_exceptions/05_multi_catch | 多 catch 顺序 | 建议 | 题面定义输入 1/2/0 三种行为，但 tests 只覆盖输入 1（oob）；2（rt）与 0（无异常）两条路径无判定——覆盖缺口 |
| 9 | agent_dev/03_spec_writing/03_score_spec | spec 评分 | 建议 | 3−2×0.5=2.0 算术 ✓；expected_output「2.0」为小数字符串，若判定为精确匹配，「2」会被误判——建议题面写明输出格式（保留一位小数） |
| 10 | agent_dev/02_debug_read/03_fix_name_error | 改 NameError | 可不修 | scor→score 拼错定位清晰，期望 85 无歧义 |
| 11 | agent_dev/07_data_security/04_minimization_case | 数据最小化场景（ai_open） | 可不修 | rubric 四条覆盖风险识别/最小化/权衡/具体保护，质量高；无标准答案压制，符合开放题定位 |
| 12 | r/02_logic_and_summary/03_count_above | 及格人数 | 可不修 | 7/10 正确（≥60：85,92,78,60,88,95,70=7 人 ✓；48,55,33 不及格） |
| 13 | r/12_clustering/05_silhouette | silhouette 评估 | **必修** | **题干与期望矛盾**：题干写「应约 0.78」而 expected_output=「0.89」；且「对上面 kmeans 的结果」依赖上一题（02_scale_first）的运行状态，独立运行时指代不明。建议：改题干数值与 expected 一致（以实际数据集跑出的值为准）并显式声明前置依赖 |
| 14 | r/12_clustering/02_scale_first | 归一化后聚类 | 可不修（待人工核实） | set.seed(42)+nstart=10 意图确定化，但 kmeans 结果随 R 版本/平台可能漂移；本地无 Rscript 无法沙盒验证——「3 3」期望需在有 R 的环境复核 |
| 15 | sql/11_null_handling/04_count_compare | COUNT(*) vs COUNT(col) | 可不修 | 沙盒验证 (4,3) ✓；NULL 语义考点清晰 |
| 16 | sql/06_window_functions/05_top2_per_class | 每班 TOP 2 | 可不修 | 沙盒验证 ROW_NUMBER 方案输出与 expected_rows 完全一致 ✓；并列分数的边界未定义（若第 2/3 名同分），建议题面补充 tie-break 规则 |
| 17 | sql/04_joins/02_left_join_null | LEFT JOIN 找无部门 | 可不修 | 沙盒验证 David ✓；题面明确"输出 name 列"无歧义 |
| 18-20 | paths/*（agent_mastery/quick_stats/people_analytics） | 学习路径文档 | 可不修 | 非题目（title/subtitle/milestones 结构完整），仅作结构检查；不被判题/抽样逻辑引用即可 |

## 二、分级汇总

- **必修 1**：#13 r/05_silhouette（题干 0.78 vs expected 0.89 矛盾 + 依赖指代不明）。
- **建议 5**：#1 判定与题面要求不一致（png）；#4/#6 tests 用例偏少；#8 三输入路径仅测一；#9 输出格式歧义。
- **可不修 14**（含 #14 待人工核实项）。
- 沙盒执行证据：python 3 题输出与 expected 完全一致、matplotlib 导入正常、sql 3 题参考查询结果与 expected_rows 完全一致（临时目录执行，无仓库写入）。

## 三、与昨夜 audit 5 warnings 交叉印证

本次样本命中 2 个 ACCEPTED 警告专题（cpp/12_file_io、r/14_sem_basics 未入样本但 cpp/12_file_io/03_sum_words 在样本内质量正常）。">70% 同难度"类警告属分布性提示，抽样 20 题内未发现与难度标注矛盾的具体题目——与 audit"均为有意设计"的结论一致。新增发现的 #13 矛盾属 audit 语法层检查覆盖不了的"语义层"问题，建议后续给 audit_content.py 增加"statement 数值 vs expected_output 一致性"启发式检查（能捕获本类错误）。

## 四、纪律声明

- content/ 零改动（仅只读）；沙盒执行全部在系统临时目录；无网络/删文件/死循环类样本被触发（R/cpp 未执行）。
- 报告路径：docs/insights/content-quality-sample-20260905.md（本文件）。
