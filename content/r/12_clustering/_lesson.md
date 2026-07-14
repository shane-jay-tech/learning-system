# 聚类（kmeans / hclust）

## 聚类做什么

PA 场景：
- 把员工分成几类（高绩效高潜、稳定型、新人）
- 把客户分群（活跃用户、休眠用户）
- 探索性分析：数据里有没有自然的"组"

聚类是**无监督**——你**不告诉算法**该怎么分，让它自己找。

## kmeans：最常用

```r
df <- data.frame(
  age = c(22, 25, 23, 40, 42, 45),
  salary = c(4000, 4500, 4200, 12000, 13000, 12500)
)

set.seed(42)
km <- kmeans(df, centers = 2, nstart = 10)
km$cluster        # 每个样本所在的簇编号
km$centers        # 每个簇的中心
```

参数：
- `centers`：分成几簇（你指定）
- `nstart`：尝试几个初始种子（推荐 ≥10）

## scale：归一化是关键

```r
df_scaled <- scale(df)             # 每列变成均值 0、方差 1
km <- kmeans(df_scaled, centers = 2)
```

⚠️ kmeans 用欧氏距离——量纲差大时（年龄 0-100 vs 工资 0-100000）一定要先 `scale`，否则结果只反映工资。

## 选 k：肘部法则

```r
wss <- sapply(1:10, function(k) {
  kmeans(df_scaled, centers = k, nstart = 10)$tot.withinss
})
plot(1:10, wss, type = "b")
```

WSS（簇内方差）随 k 增加而下降。找"肘部"——再加 k 收益变小的拐点。

## hclust：层次聚类

```r
d <- dist(df_scaled)               # 距离矩阵
hc <- hclust(d, method = "ward.D2")  # 层次聚类
plot(hc)                            # 画树状图
clusters <- cutree(hc, k = 2)       # 切成 2 簇
```

层次聚类**给一棵完整的树**，可以选任何 k 切。`method = "ward.D2"` 是 PA 论文最常用的方法。

## kmeans vs hclust

| 算法 | 优势 | 劣势 |
|---|---|---|
| `kmeans` | 快、好理解 | 必须先指定 k；容易陷局部最优 |
| `hclust` | 不用指定 k；可视化树状图 | O(n²) 慢，10000+ 点不可用 |

## 评估聚类质量：silhouette

```r
library(cluster)
sil <- silhouette(km$cluster, dist(df_scaled))
mean(sil[, 3])     # 平均 silhouette；越接近 1 越好
```

silhouette 范围 [-1, 1]：
- 1：完美聚类
- 0：边界模糊
- -1：分错了

## 常见错误

1. **没 scale**：量纲不一致时聚类只反映最大尺度的列
2. **k 拍脑袋定**：用肘部法则或 silhouette 系统选
3. **kmeans 没 set.seed**：每次结果略有不同（centers 随机初始化）
4. **类别变量丢进 kmeans**：kmeans 只能处理数值；类别要先 dummy 编码

## 现在做练习

5 道题：kmeans 基础、scale 后聚类、cluster 大小、hclust 切树、silhouette 评估。
