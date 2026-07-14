# 用 SQL 做人力分析

前面的 SQL 练习是单表小数据。真实的 People Analytics 往往是**多张表**：一张存员工基本信息，一张存调查结果，你得把它们**连起来（JOIN）**再分析。

这一章用两张表：
- **employees**：`emp_id, name, department, hire_date`（员工花名册）
- **surveys**：`emp_id, engagement, submit_date`（敬业度调查，1-5 分）

注意一个真实的坑：**不是每个员工都交了问卷**。有人在花名册里、却不在调查表里——这正是数据分析里天天遇到的"数据缺口"，得用 `LEFT JOIN` 才能把这些人揪出来。

这一章练的就是分析师的日常：
- `JOIN` —— 把员工和他的调查连起来
- `GROUP BY` + `AVG` / `COUNT` —— 按部门聚合
- `HAVING` —— 对聚合结果再筛选（"哪些部门平均分≥4"）
- `LEFT JOIN ... IS NULL` —— 找出"没交问卷"的人（数据质量检查）
- `ROUND(x, 2)` —— 平均分保留 2 位小数，报表才好看
