# A/B 测试 + 文本基础

## 这一节学什么

People Analytics 进阶常用的两大工具：

1. **A/B 测试**：比较两种方案（新旧界面、新旧政策）哪个更好
2. **文本基础**：处理调查问卷的开放性回答、招聘 JD 提取关键词

## A/B 测试核心：比例检验

新版界面 vs 旧版界面，转化率分别是 6/100 vs 5/100。这 1% 的差异**显著**吗？

```python
from scipy.stats import chi2_contingency
import numpy as np

# 列联表：[转化, 未转化]
table = np.array([
    [6, 94],    # A 组（旧）
    [12, 88],   # B 组（新）
])
chi2, p, dof, expected = chi2_contingency(table)
print(f"p={p:.4f}")
```

p < 0.05 → 差异显著。

## 用 statsmodels 做更专业的比例检验

```python
from statsmodels.stats.proportion import proportions_ztest

count = np.array([6, 12])     # 转化次数
nobs = np.array([100, 100])   # 各组样本量
z, p = proportions_ztest(count, nobs)
```

但 statsmodels 在本平台不一定装；用 scipy.stats 也够用。

## 效应量（effect size）

只看 p 值容易陷入"显著但效应小"的陷阱。一个简单的效应量是 **Cohen's d**：

```python
import numpy as np

def cohens_d(a, b):
    pooled_sd = np.sqrt((np.var(a, ddof=1) + np.var(b, ddof=1)) / 2)
    return (np.mean(a) - np.mean(b)) / pooled_sd

a = [85, 92, 78, 88, 95]
b = [72, 68, 75, 82, 70]
print(f"d = {cohens_d(a, b):.3f}")
# 经验：|d|≈0.2 小、0.5 中、0.8 大
```

## 文本基础：分词 + 计数

最简单的中文/英文分词（按空白切）：

```python
text = "the quick brown fox jumps over the lazy dog the fox"
words = text.lower().split()
from collections import Counter
counts = Counter(words)
print(counts.most_common(3))
# [('the', 3), ('fox', 2), ('quick', 1)]
```

`Counter` 是字典的子类，专门数频次，自带 `most_common(N)`。

## 移除常见停用词

英文文本里 the / a / is 等"停用词"通常要去掉：

```python
stopwords = {"the", "a", "is", "and", "or", "of", "in", "to"}
filtered = [w for w in words if w not in stopwords]
```

## TF-IDF（词频 - 逆文档频率）

衡量一个词在文档里的"特色程度"：

```python
from sklearn.feature_extraction.text import TfidfVectorizer

docs = [
    "I love python programming",
    "Python is great for data analysis",
    "Java and python are different",
]
vec = TfidfVectorizer()
X = vec.fit_transform(docs)
print(vec.get_feature_names_out())   # 词典
print(X.toarray())                   # 每行一个文档的向量
```

文档里独特的词（"java"）TF-IDF 高；常见的（"python"）TF-IDF 低。

## 常见错误

1. **A/B 样本量不够**：100 vs 100 检测不出 1% 差异；样本量计算用 `power_analysis`
2. **多次"偷看 p 值"**：实验跑一半看一次、跑完看一次——p 值会被这种行为扭曲
3. **`split()` 中文分不动**：中文要用 jieba（`pip install jieba`）
4. **TfidfVectorizer 没去停用词**：`TfidfVectorizer(stop_words="english")` 自动去英文停用词

## 现在做练习

5 道题：A/B 卡方检验、Cohen's d、词频前 3、去停用词、TF-IDF 维度。
