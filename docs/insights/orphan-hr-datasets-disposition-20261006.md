# 两枚孤儿数据集处置预案：hr_recruitment.csv／hr_survey.csv（l1004-31；5d75 遗留3）

> 产线：执行班 l1004-31（2026-10-06）。**备用档：删除属人工闸，本单零改动**。

## §一 复核：5d75「0 引用」结论需收窄（矿漂如实留痕）

- 两文件现值：`content/datasets/hr_recruitment.csv`（13,570 B）、`hr_survey.csv`（16,660 B），mtime 2026-06-08。
- **题面/生产码引用＝0 实锤**：`rg -rln "hr_recruitment|hr_survey" content --glob "*.yaml"` → **0 文件**（对照主件 hr_employees＝**22 个题面 yaml** 在用）。
- **但「0 引用」不成立的面有两处**（5d75 未记）：
  1. `tests/test_hr_dataset_determinism.py`（l923-27 确定性钉桩）：两文件 **md5＋字节数逐字节硬断言**（rg 计 8 处命中）——测试把三件（含主件）作为再生成确定性夹具，删任一件该测试直接红；
  2. `content/datasets/generate_hr_data.py`：生成器自身写出两件（OUT_DIR 同目录）。
- 净结论：**「题面孤儿」为真，「资产孤儿」为假**——它们是确定性测试的夹具资产＋生成器的固有产物。

## §二 处置两案

### 案 A 删除（须三件套连带）

删两 csv ⇒ 连带：① test_hr_dataset_determinism.py 删两文件的 md5 断言行与 docstring 提及（8 处命中面收缩到 hr_employees）；② generate_hr_data.py 删两个生成函数/写出段（否则脚本再跑会重新长出文件，删了白删）；③ 重跑 determinism 测试＋audit。**连带面＝1 测试件＋1 生成器脚本＋重跑验证**；风险＝低（无题面/生产码消费）但「测试覆盖减少」（确定性回归网从三件缩到一件）。

### 案 B 转正为教材/测试资产（现状即案 B）

保持现状，把身份从「孤儿」改册为「determinism 夹具＋未来题面储备」：① 在 test_hr_dataset_determinism.py docstring 已自陈定位（l923-27），补一行 INVENTORY/README 数据集段登记「hr_recruitment/hr_survey＝夹具资产，题面未消费」；② 未来 hr 族扩题（20_hr_pandas/21_hr_viz 已有 22 题在用主件）可直接引用，免再生成。**连带面＝1 行文档登记；零风险**。

**材料倾向**：案 B（转正登记）。理由：删除净收益仅 -30KB 仓库体积，代价是削确定性回归网；两文件由 seed(42) 生成器可复现，「占位无主」的原始顾虑已被测试钉桩消解。

## §三 引用再核清单（任何处置前重跑）

```
$ rg -rln "hr_recruitment|hr_survey" content --glob "*.yaml"          # 题面（现值 0）
$ rg -rn "hr_recruitment|hr_survey" tests/ core/ scripts/ ui/ app.py  # 生产/测试面（现值 2 件 10 处）
$ rg -n "hr_recruitment|hr_survey" content/datasets/generate_hr_data.py  # 生成器（现值写出 2 处）
$ python -m pytest tests/test_hr_dataset_determinism.py -q            # 处置后必跑
```
