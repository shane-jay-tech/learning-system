# HR 预测建模

用 scikit-learn 构建离职预测模型，是 People Analytics 从"描述过去"升级到"预测未来"的关键一步。

## 为什么重要

如果能提前识别高离职风险员工，HR 可以主动干预（加薪、换岗、谈话），比事后分析有价值得多。

## 核心步骤

1. **准备数据**：特征（年龄、工龄、薪资、绩效、加班时长）+ 标签（是否离职）
2. **拆分数据集**：`train_test_split(X, y, test_size=0.2)`
3. **训练模型**：`LogisticRegression().fit(X_train, y_train)`
4. **评估效果**：准确率、混淆矩阵、AUC

## 最小示例

```python
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
model = LogisticRegression()
model.fit(X_train, y_train)
print(f"准确率: {model.score(X_test, y_test):.2%}")
```

## 关键概念

- **特征重要性**：`model.coef_` 看哪些因素权重最大
- **混淆矩阵**：真正例、假正例、漏报率
- **交叉验证**：`cross_val_score` 防止过拟合，结果更可信
- **过拟合**：训练集完美、测试集很差 = 模型记住了噪音

## 常见错误

- 特征没标准化（`StandardScaler`），某些特征因量纲大而主导模型
- 样本不平衡（离职的人远少于在职的）未处理
- 直接看准确率，忽略了类别不均匀下的陷阱
