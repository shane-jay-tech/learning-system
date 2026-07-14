# Spec 写作：让 Agent 不跑偏的诀窍

## 烂 Spec 等于浪费 Agent

❌ "做一个数据分析工具"
❌ "优化一下这个程序"
❌ "我要个能管理任务的 app"

Agent 拿到这种话只能瞎猜。**90% 的"agent 跑偏"问题不在 agent，在你的 prompt**。

## 好 Spec 的 5 个维度

每写一个新功能或工具，**先把这 5 项写下来**：

| 维度 | 例子 |
|---|---|
| **input** | 一个 Excel 文件，含 3 列：name / score / class |
| **output** | 每班平均分 + 最高分学生名字 |
| **正确示例** | 输入 5 行 → 输出 2 行（A 班 平均 87, 最高 Eve；B 班 平均 73, 最高 Bob） |
| **边界 / 反例** | 空文件 → 报错说"没数据"；列名拼错 → 提示具体哪列；分数为负 → 跳过那行 |
| **约束** | 只用 pandas；不上网；输出到 stdout |

## 一个真实例子：好 Spec 长这样

> **目标**：从 sales.csv 算各产品的月环比
>
> **input**：sales.csv，列 [date(YYYY-MM-DD), product, amount]，10000 行级
>
> **output**：DataFrame 列 [product, month(YYYY-MM), this_month, last_month, growth_pct]
>
> **正确示例**：苹果 2026-04 卖 100，2026-05 卖 130 → growth_pct=30%
>
> **边界**：
> - 当月数据缺失 → growth_pct=NaN（不是 0、不是报错）
> - 上月为 0 → growth_pct=inf（用 numpy.inf，不要除零崩）
> - product 名字为空 → 那行丢弃
>
> **约束**：pandas；输出按 product 然后 month 排序

写完这 30 行 spec，agent 几乎不会跑偏。

## 拆任务：一次只让 agent 做一件事

❌ "做一个完整的 todo app（含 UI / 数据库 / API）"
❌ "重构整个项目"

Agent **一次能吃**的任务大约：
- 1-3 个文件
- 100-300 行新代码
- 1 个清晰目标

把大任务**拆成 5-10 个小步骤**：

1. 先建数据模型（task 表 schema）
2. 写 CRUD 函数（add / list / done / delete）
3. 写最简 UI（只能 add 和 list）
4. 加 done 按钮
5. 加删除按钮
6. 加测试
7. 加导出

每步独立可测——失败了只丢一小段。

## 反例的力量

新手 Spec 只写"正确情况"。**老手 Spec 着重写"反例"**：

> 输入空 csv → ?
> 输入只有标题没数据 → ?
> 输入有 NaN 行 → ?
> 输入超过 100MB → ?
> 输入是损坏的 csv → ?

光是把这些反例写下来，**agent 就会主动加 try/except 和数据校验**。

## 提供"输入样本"

Spec 里**贴一段真实数据**比文字描述强 10 倍：

```
input 示例（前 3 行）：
date,product,amount
2026-01-01,apple,100
2026-01-02,banana,80
```

Agent 看一眼就知道字段名、类型、格式。

## 验收标准

Spec 末尾写 **"验收 = ?"**：

> 验收：
> - python main.py sales.csv 能跑通
> - 输出符合上面 example
> - pytest tests/ 全绿
> - 处理空 csv 不崩（输出"无数据"）

agent 写完会**自检**这些条件。

## 常见错误

1. **缺 output 描述**：agent 自由发挥的点；越具体越好
2. **没说约束**：agent 给你拉来 5 个第三方库
3. **没反例**：用户输入意外数据时崩
4. **没验收**：你不知道何时算"做完了"
5. **太大**：一次让 agent 做 1000 行代码，质量会崩

## 现在做练习

5 道题：用 dict 写出 spec 的 5 维度、判断 spec 是否完整、找出缺失字段、给烂 spec 打分、拆任务。
