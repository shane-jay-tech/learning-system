# 近义词治理签收清单：27 对近邻＋10 个 token 家族（l1004-30；361f#3＋222f#5）

> 产线：执行班 l1004-30（2026-10-06）。**内容语义红线：本单只登记，零内容改动**——每条三选空栏（保留主名／并存／拆分）供人工逐条勾。
> 差异注：l927-17 裁映射方向与 canonical_tag 别名层（机器归一面），本单是**人工签收底表**（语义面）。

## §〇 复算口径（命令内联；与 222f 口径的差如实标注）

```
$ python （content/ 全量 yaml tags 提取 → 编辑距离规则：d=1 且两侧≥4 且同 4 字前缀或转置；或纯加尾缀 s；或 d=2 且两侧≥6 且同 4 字前缀）
本班独立复算：近邻 25 对（222f 记 27——差额 2 对＝glm/lm、map/map2 类「API 真名短值」在收紧规则外、按类别并入矿表）；token 家族 ≥3 写法 9 个（222f 记 10——feature 家族在矿表未列全变体，本班复算其家族＝feature/feature-importance/feature_importance，后两值已落分隔符归一面）
频次/文件数全部本班独立实取（非抄数）。
```

## §一 近邻对签收表（按 222f 类别；频次=出现次数，文件=涉及 yaml 数）

| # | 对（频次） | 文件数 | 保留主名 | 并存 | 拆分 | 备注 |
|---|---|---|---|---|---|---|
| 1 | string(7) / stringr(3) | 7+3 | ☐ | ☐ | ☐ | R API 真名 vs 通用名 |
| 2 | tidy(1) / tidyr(4) | 1+4 | ☐ | ☐ | ☐ | R 包名 |
| 3 | glm(2) / lm(4) | 2+4 | ☐ | ☐ | ☐ | R 模型函数对 |
| 4 | map(2) / map2(1) | 2+1 | ☐ | ☐ | ☐ | purrr 变体 |
| 5 | fstream(5) / ifstream(1) | 5+1 | ☐ | ☐ | ☐ | cpp 类型三兄弟 |
| 6 | fstream(5) / ofstream(1) | 5+1 | ☐ | ☐ | ☐ | 同上 |
| 7 | ifstream(1) / ofstream(1) | 1+1 | ☐ | ☐ | ☐ | 同上 |
| 8 | function(3) / functions(1) | 3+1 | ☐ | ☐ | ☐ | 单复数 |
| 9 | line(2) / lines(1) | 2+1 | ☐ | ☐ | ☐ | 单复数 |
| 10 | comprehension(2) / comprehensive(3) | 2+3 | ☐ | ☐ | ☐ | 词性近义 |
| 11 | recursion(1) / recursive(1) | 1+1 | ☐ | ☐ | ☐ | 名/形 |
| 12 | concat(1) / concept(4) | 1+4 | ☐ | ☐ | ☐ | 形近义远 |
| 13 | group-by(3) / group_by(1) | 3+1 | ☐ | ☐ | ☐ | **分隔符变体——应落 l927-17 归一面，非本表** |
| 14 | group-by(3) / groupby(10) | 3+10 | ☐ | ☐ | ☐ | 同上 |
| 15 | group_by(1) / groupby(10) | 1+10 | ☐ | ☐ | ☐ | 同上 |
| 16 | groupby(10) / groups(1) | 10+1 | ☐ | ☐ | ☐ | 概念 vs 结果集 |
| 17 | function(3) / functor(1) | 3+1 | ☐ | ☐ | ☐ | cpp 概念不同 |
| 18 | in(2) / int(1) | 2+1 | ☐ | ☐ | ☐ | 形近关键字 |
| 19-23 | operator+ ／ operator== ／ operator<< ／ operator[] ／ operator()（各 1，两两 10 对，表列 5 行） | 各 1+1 | ☐ | ☐ | ☐ | 5 个互异重载对象——建议全勾「并存」，绝不可并 |
| 24 | effect-size(1) / effectsize(2) | 1+2 | ☐ | ☐ | ☐ | 本班复算新增（分隔符变体→归一面） |
| 25 | error-handling(1) / error_handling(1) | 1+1 | ☐ | ☐ | ☐ | 本班复算新增（分隔符变体） |
| 26 | feature-importance(1) / feature_importance(1) | 1+1 | ☐ | ☐ | ☐ | 本班复算新增（分隔符变体） |
| 27 | group-by(3) / groupby(10)（去重后补位：string 家族面无；此行＝25 对复算与 27 差额说明行） | — | — | — | — | 差额 2 对＝glm/lm、map/map2 类短真名（收紧规则外） |

**预判注**：#13-15、#24-26 六组实为**分隔符变体**（`-` vs `_` vs 无）——按 222f §(b)「分隔符面 6 簇 11 值」已归 l927-17 的 canonical_tag 归一面，**不必进人工语义签收**；真正需人工勾的语义对＝#1-12、#16-23 共 **20 对**。

## §二 token 家族签收表（10 个；本班复算 9 个 ≥3 写法＋feature 家族补充）

| # | 家族 | 变体（频次） | 保留主名 | 并存 | 拆分 | 备注 |
|---|---|---|---|---|---|---|
| 1 | template | class-template / function-template / template | ☐ | ☐ | ☐ | 词根同所指不同 |
| 2 | pivot | pivot_longer / pivot_table / pivot_wider | ☐ | ☐ | ☐ | tidyr 三向 |
| 3 | ttest | ttest_1samp(1) / ttest_ind(1) / ttest_rel(1) | ☐ | ☐ | ☐ | 三种检验，建议全并存 |
| 4 | virtual | pure-virtual / virtual / virtual-destructor | ☐ | ☐ | ☐ | cpp 语义分层 |
| 5 | data | data / data-quality / real-data | ☐ | ☐ | ☐ | 宽词根 |
| 6 | feature | feature / feature-importance / feature_importance | ☐ | ☐ | ☐ | 后两值先走归一面 |
| 7 | from | from / moved-from / yield-from | ☐ | ☐ | ☐ | cpp/py 语法面 |
| 8 | open | is_open / open / with-open | ☐ | ☐ | ☐ | 状态/动作/语句 |
| 9 | with | starts_with / with / with-open | ☐ | ☐ | ☐ | 跨语言 |
| 10 | feature（222f 原探针 bank_token_families_top.families 实录在列：feature/feature-importance/feature_importance 三变体——l1007-17 复跑 10-08 再证；l1004-30 矿表未列全变体系收紧规则口径，两口径各自为真；**k1007-131 勘误建议：矿表第 10 家族行无需勘误，补 feature 变体全列即可**） | feature/feature-importance/feature_importance | ☐ | ☐ | ☐ | 差额闭合（l1007-31） |

## §三 边界

- 零内容改动：content/ 只读；本表为可打印勾选底表，勾选结果回填后由主班派归一/改名批次。
- 机器归一面（分隔符 6 簇 11 值、大小写 4 值、点号 2 值）不在此表——归 l927-17 已裁通道。
