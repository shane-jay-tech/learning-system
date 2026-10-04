# RRunner DataFrame rows 产出通道设计稿（k1002 批外 l1002-05，判题域——**需第二模型独立复核后才能实施**）

- 时点：2026-10-05（exec-shift-20261003-manual）；**零生产码改动**
- 矿源：l920-09／l920-02（r 题 DataFrame 机判＝内容建设＋判题逻辑前置；题库现无 r 多 DataFrame 题）

## 一、现值（完成标准"现值"）

`core/runners/r_runner.py`：`RRunner.run()` 只产出 stdout/stderr 文本（ok = returncode==0），**无 rows 通道**——`expected.expected_rows` 对 r 题不被消费（judge.py:20 RUNNERS 表分派后，rows 判据 `_rows_equal`/`_first_diff_cell`（judge.py:97-118）目前**唯一生产者是 SQLRunner**）。与 SQLRunner rows 语义差异：SQL 侧由 sql.js 结构化执行返回 `columns/rows` 二维数组，天然免解析；R 侧是子进程 stdout 文本，**rows 必须先定义序列化协议再解析**——这是三路径分歧的根源。

## 二、三路径设计（完成标准"三路径"）

### 路径 1：`dim()` + 逐行 cat 自定义协议（base R 零依赖）

```r
# runner 侧 harness 追加（用户码执行后）：
if (exists("result") && is.data.frame(result)) {
  cat("\n__ROWS_BEGIN__\n")
  write.table(result, sep="\x1f", row.names=FALSE, quote=FALSE, na="__NA__")
  cat("__ROWS_END__\n")
}
```
- runner 解析：取 BEGIN/END 之间按 `\x1f`（unit separator，规避内容含逗号/竖线冲突）切列。
- **判分语义**：解析为 `rows: list[list[str]]` 后**直接复用** `_rows_equal`/`_first_diff_cell`（零判据新增）。
- 影响面：浮点字面漂移（R `0.5` vs expected `0.50`）——`_cell_eq` 已有 float 分支兜底（str→float 等价比较），但需在题面规范固定 `options(digits=…)` 或 runner harness 注入 `options(digits=15)`。
- 风险：`\x1f` 在 Windows 控制台编码链可能被转换——建议 base64 兜底开关。

### 路径 2：named list → JSON（jsonlite 依赖）

```r
cat("__JSON_BEGIN__"); jsonlite::toJSON(result, dataframe = "values"); cat("__JSON_END__")
```
- 语义最干净（类型保真：数值/逻辑/NA→null），但**引入 jsonlite 依赖**——本机 R 环境不可控（学习者机器），`R_LIBS_USER` 探测已在 runner（:75-95）但依赖缺失即判题崩。需 fallback 到路径 1。
- 判分语义：JSON 解析出的 rows 数值型可直接进 `_cell_eq` float 分支 ✓。

### 路径 3：逐行 cat 表格式（print 形态）

`print(result)` 原样文本 + expected 用正则/列位置比对。
- **不推荐**：print 输出受宽度/行名/截断（`max.print`）影响，跨 R 版本/终端不稳，判分语义会退化成文本模糊匹配——与逐字 rows 口径冲突。

**推荐**：路径 1（零依赖）为主、路径 2 为可选增强（检测到 jsonlite 时自动升级类型保真）。

## 三、与 expected_rows 口径的对齐方案

- expected_rows 形态沿用 SQL 题（`[[row1c1, row1c2], [row2…]]`），`_cell_eq` 数值等价（"0.5"≡0.5）直接生效。
- **列名不判**（SQL 侧同口径：只判 rows 值）——如需列名判分另加 `expected_columns`（新判据，超本稿）。
- NA/缺失：R 侧协议 `__NA__` → 解析端映射 `None`，`_cell_eq` None 分支持 ✓。
- 行序：严格按 _rows_equal 顺序判（如需无序判分另加 sort 前处理，超本稿）。

## 四、验证缺口与有 R 环境机器的验证清单（完成标准③）

**本机缺口**：无 Rscript（7 例 R 测试 skip）——本稿三路径**全部未实测**，仅为静态设计。
**有 R 环境机器验证清单**：
1. `Rscript -e 'cat("\x1f")'`——unit separator 经 Windows 管道是否原样存活（路径 1 前提）。
2. `write.table` 对含 NA/中文/引号/超宽数值列的输出形态（na 参数、quote=FALSE 边界）。
3. harness 追加段对用户码 `result` 未定义/非 data.frame 时的静默降级（不输出协议块 → rows=None → 走纯 stdout 判）。
4. `options(digits=15)` 注入后浮点字面与 expected 的 `_cell_eq` 通过率样例（0.1+0.2 类）。
5. timeout护栏（settrace 是 Python 侧；R 侧超时=进程级 kill，harness 内死循环仍由 runner timeout_sec=5 兜底——实测确认）。

## 五、实施前置条件（非本稿范围）

- 内容建设：r DataFrame 题面（题库现无）——内容作者定义题集后才有机判对象。
- **判题逻辑升级＝硬触发第二评审**：本稿须经 GPT/第二模型独立复核（尤其 §二判分语义与 §四边界）后才能进实施单。
- 实施面：r_runner.py（harness＋解析）＋judge.py（r 题接 expected_rows 分支）＋题库 schema（r 题 expected_rows 字段启用）。
