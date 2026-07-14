# R Markdown / Quarto：动态文档

## R Markdown 是什么

R Markdown（.Rmd）让你**把代码、文字、图表、公式**写在同一个文档里——一键渲染成 PDF / HTML / Word。论文写作的标准流程。

```r
library(rmarkdown)
```

文件结构：

````markdown
---
title: "员工流失分析"
author: "我"
date: "2026-05-29"
output: html_document
---

# 第一章 概述

普通文字。

```{r}
# 这是 R 代码块（chunk）
df <- read.csv("data.csv")
mean(df$score)
```

代码下方会自动出现运行结果。

```{r my-plot, fig.width=6, fig.height=4}
hist(df$score)
```

图也直接嵌入。
````

## 三个核心元素

1. **YAML 头部**（顶部 `---` 之间）：标题/作者/输出格式
2. **Markdown 文本**：普通文字、标题、列表
3. **代码块（chunk）**：` ```{r} ... ``` `

## chunk 选项

```` ```{r my-chunk, echo=FALSE, message=FALSE, fig.width=8} ````

| 选项 | 作用 |
|---|---|
| `echo=TRUE/FALSE` | 是否显示代码 |
| `eval=TRUE/FALSE` | 是否运行 |
| `include=FALSE` | 跑但完全不显示 |
| `message=FALSE` | 隐藏 message |
| `warning=FALSE` | 隐藏 warning |
| `fig.width / fig.height` | 图大小（英寸）|
| `cache=TRUE` | 缓存 chunk（耗时计算用）|

## 内联代码

```markdown
平均分是 `r mean(df$score)`，最高分 `r max(df$score)`。
```

文字里嵌 R 表达式 → 渲染时变成数值。

## 输出格式

```yaml
output: html_document       # 网页
output: pdf_document        # PDF（需 LaTeX）
output: word_document       # docx
output: github_document     # GitHub README 风
output: ioslides_presentation  # 幻灯片
```

## Quarto：R Markdown 的"下一代"

```bash
quarto render report.qmd
```

`.qmd` 文件 + `quarto` 命令——比 R Markdown 更现代，支持 R + Python + Julia 混用。论文写作正在从 Rmd 迁到 qmd。

## tinytex：装 LaTeX 用于 PDF

```r
install.packages("tinytex")
tinytex::install_tinytex()
```

之后 `output: pdf_document` 就能用——不需要单独装 MiKTeX/MacTeX。

## kableExtra：表格美化

```r
library(kableExtra)
df %>% kable() %>% kable_styling()
```

把数据框变成漂亮的 HTML/PDF 表格——论文里常用。

## bookdown：写整本书

```r
library(bookdown)
```

支持交叉引用、章节、参考文献——研究生学位论文经常用。

## 常见错误

1. **chunk 里 setwd**：不要！R Markdown 默认 chunk 工作目录是 .Rmd 所在
2. **路径用绝对**：会让协作者跑不通；用相对路径
3. **Plot 不显示**：忘了 print 一些 ggplot 在某些版本要 `print(p)` 显式
4. **PDF 渲染挂了**：tinytex 没装；或者中文字体没设

## 现在做练习

5 道题（注意：本平台沙箱不直接渲染 .Rmd，但题目让你**用 R 函数操作 Rmd 概念**）：write 一个 Rmd 文件、读它、统计 chunk 数、用 knitr::knit_expand、自动生成报告。
