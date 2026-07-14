# sklearn 入门：监督学习

## sklearn 是什么

`scikit-learn` 是 Python 机器学习的标准库。在 People Analytics 里你会用它：
- 预测员工离职（分类）
- 预测员工工资（回归）
- 给员工聚类（无监督）

## 一个最简单的例子：线性回归

```python
import numpy as np
from sklearn.linear_model import LinearRegression

# 工资 vs 绩效（5 个员工）
X = np.array([[5000], [8000], [6500], [12000], [9000]])  # 自变量（必须 2D）
y = np.array([70, 88, 75, 95, 82])                        # 因变量

model = LinearRegression()
model.fit(X, y)

print(f"系数: {model.coef_[0]:.4f}")    # 0.0036（每多 1 元工资，绩效涨 0.0036）
print(f"截距: {model.intercept_:.2f}")  # 大约 49
print(f"R²: {model.score(X, y):.4f}")    # 拟合优度
print(f"预测 7000 元工资: {model.predict([[7000]])[0]:.1f}")
```

## sklearn 的标准流程（4 步）

1. `model = SomeAlgorithm(...)` —— 创建模型
2. `model.fit(X, y)` —— 训练
3. `predictions = model.predict(X_new)` —— 预测
4. `model.score(X, y)` —— 评估

90% 的 sklearn 任务都是这 4 步。

## 几个常用算法

```python
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
```

| 任务 | 用什么 |
|---|---|
| 预测连续值（回归） | `LinearRegression`、`Ridge`、`RandomForestRegressor` |
| 预测类别（分类） | `LogisticRegression`、`DecisionTreeClassifier`、`RandomForestClassifier` |
| 聚类（无标签） | `KMeans` |

## 训练 / 测试集划分

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
model.fit(X_train, y_train)
print(model.score(X_test, y_test))
```

不分训练测试集 → "训练集表现好"不能保证"新数据表现好"。

## 特征矩阵 X 必须 2D

```python
# 错：X 是 1D
X = [5000, 8000, 6500]
model.fit(X, y)   # ValueError

# 对：X 必须 2D（每行一个样本，每列一个特征）
X = np.array([[5000], [8000], [6500]])
model.fit(X, y)
```

即使只有 1 个特征也要 2D（reshape 成 `(-1, 1)`）。

## 决策树分类

```python
from sklearn.tree import DecisionTreeClassifier

X = np.array([[25, 5000], [30, 8000], [22, 4500]])  # [age, salary]
y = np.array([0, 1, 0])  # 0=不离职 1=离职

clf = DecisionTreeClassifier(max_depth=3, random_state=42)
clf.fit(X, y)
print(clf.predict([[28, 6000]]))   # [0] 或 [1]
```

`random_state` 是为了复现——同样的 seed 给同样的结果。

## 常见错误

1. **X 不是 2D**：`X = [1,2,3]` 错；要 `[[1],[2],[3]]` 或 `np.array([1,2,3]).reshape(-1, 1)`
2. **训练数据评估**：`model.score(X_train, y_train)` 永远偏高；要用测试集
3. **分类用 LinearRegression**：分类用 LogisticRegression，回归才用 LinearRegression
4. **没归一化连续特征**：年龄(0-100) 和工资(0-100000) 量级差太大，会扭曲许多算法的距离计算

## 现在做练习

5 道题：线性回归系数、R²、预测、决策树训练、KMeans 聚类。
