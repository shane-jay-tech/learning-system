# scikit-learn 进阶

基础 sklearn 会 `fit/predict`，进阶要学：交叉验证（防止过拟合）、特征重要性（解释模型）、Pipeline（标准化工作流）。

## 交叉验证

不要只看一次 train/test 分割的结果——用 K 折交叉验证取平均更可靠：

```python
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier

scores = cross_val_score(DecisionTreeClassifier(), X, y, cv=5)
print(f"平均准确率: {scores.mean():.3f} ± {scores.std():.3f}")
```

## 特征重要性

树模型（随机森林、GBDT）天然能输出特征重要性：

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

for name, imp in zip(feature_names, model.feature_importances_):
    print(f"{name}: {imp:.3f}")
```

## Pipeline

把预处理和建模串成一条流水线，避免数据泄漏：

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("model", LogisticRegression()),
])
pipe.fit(X_train, y_train)
print(pipe.score(X_test, y_test))
```

## 何时用进阶技巧？

- **交叉验证**：只要你在评估模型好不好
- **特征重要性**：需要向业务解释"哪些因素最影响结果"
- **Pipeline**：生产环境、或特征需要标准化/编码时
