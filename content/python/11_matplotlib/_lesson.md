# matplotlib 画图基础

## 为什么学画图

数据分析的最后一步通常是**告诉别人**：用图比用一堆数字更说服人。matplotlib 是 Python 最经典的画图库，pandas/seaborn 都基于它。

```python
import matplotlib
matplotlib.use("Agg")   # 不弹出窗口（练习平台必须）
import matplotlib.pyplot as plt
```

⚠️ 在没有图形界面的环境（练习沙箱、服务器）必须 `matplotlib.use("Agg")` 在 `pyplot` 之前调用，否则会卡住找显示。

## 三大基础图

### 折线图（line）

```python
x = [1, 2, 3, 4, 5]
y = [3, 5, 4, 7, 6]
plt.plot(x, y)
plt.xlabel("month")
plt.ylabel("sales")
plt.title("Monthly sales")
plt.savefig("line.png")
plt.close()
```

### 柱状图（bar）

```python
plt.bar(["A", "B", "C"], [10, 25, 15])
plt.savefig("bar.png")
plt.close()
```

### 散点图（scatter）

```python
plt.scatter([1,2,3,4], [10,20,15,25])
plt.savefig("scatter.png")
plt.close()
```

## 画完别忘了 close

`plt.close()` 释放图对象。不写，连续画很多张时会累积内存。

## 保存到文件

```python
plt.savefig("output.png", dpi=150, bbox_inches="tight")
```

`dpi` 控制分辨率，`bbox_inches="tight"` 自动裁剪边距。

## 多图（subplot）

```python
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].plot([1,2,3], [4,5,6])
axes[0].set_title("left")
axes[1].bar(["a","b","c"], [3,1,2])
axes[1].set_title("right")
plt.savefig("twin.png")
plt.close()
```

## pandas 的 .plot()

pandas 自带画图（封装 matplotlib），更短：

```python
df["score"].plot(kind="bar")
plt.savefig("scores.png")
```

类型：`line` / `bar` / `barh` / `hist` / `box` / `scatter` / `pie`。

## 在练习平台中怎么"判图"

平台没法看你画得好不好，所以题目会让你**画完后输出一个数值**——比如"画 y 的折线图，**并输出 max**"——判题靠 stdout，但你练的是画图代码。图保存在 `.png` 文件里，沙箱跑完就清掉了。

## 常见错误

1. **没用 Agg 后端**：在沙箱跑 `plt.show()` 会挂死；用 savefig + close
2. **savefig 在 close 之后**：close 后图被释放，存出来是空白
3. **中文乱码**：matplotlib 默认不支持中文；要 `plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]`
4. **subplot 索引乱**：`subplots(2, 3)` 后 `axes` 是 2D 数组，要 `axes[0][1]`

## 现在做练习

5 道题：折线 + 输出 max、柱状 + 输出 sum、散点 + 输出 mean、多线图 + 输出差值、柱状排序 + 输出最大类。
