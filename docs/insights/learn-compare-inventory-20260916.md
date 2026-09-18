# learning 全仓同族比较逻辑清点（n916x-40，_cell_eq 语义校正后横向核验，只读）

**结论：全仓扫描后，bool↔数值宽松比较语义仅存在于 `core/judge.py:80-95 _cell_eq` 实现自身（参照实现，已被测试覆盖）；生产代码其余比较逻辑零同族命中——无横向扩散风险。清单行数与 rg 命中数一致。**

## 一、扫描命令与命中数（先命令后数字）

```
$ rg -n '== True|is True|in \(True, 1\)|== 1\b' --glob '*.py' .   → 11 行（见下）
$ rg -n '(float|bool)\(.*==|==(float|bool)\(' --glob '*.py' .      → 3 行（均 judge.py 自身）
$ rg -n 'mark\.skip|skipif' （等扩展形态）                          → 未采用（与本语义无关）
```

## 二、清单（file:line｜实际语义｜是否已覆盖）

### ① 参照实现（同族语义本体，3 行）
- core/judge.py:80-95 `_cell_eq`：宽松语义＝bool 按真值（True 与 1 相等，:84/:88）；数值 float(a)==float(b)（:90）；字符串严格含空白（"1 "≠"1"）。**已覆盖**（tests/test_core_edges.py＋docs/insights/learn-judge-edges-20260916.md 校正记录）。
- core/judge.py:99/:112：`_rows_equal`/答案调用点——复用 _cell_eq，无独立语义。**已覆盖**（同上）。

### ② 生产码非同族（1 行）
- ui/pages/home.py:136 `streak == 1`：int==int 严格相等，无 bool 混入。**非同族**（无需覆盖动作）。

### ③ 测试断言（5 行，覆盖工件本身）
- tests/test_core_edges.py:181 `is True`／:228 `== True`／:339 `is True`：断言 judge 返回值布尔形状——即①语义的覆盖证据。
- tests/test_core_edges.py:39/:196/:227/:369-373：数值相等断言（与 bool 宽松无关）。

## 三、建议

1. 新增比较语义一律路由 `_cell_eq`，禁止在业务码内重写 `== True`/`float()` 混合比较（当前零扩散，保持）。
2. `_cell_eq` 的「bool 按真值」反直觉点已在 docstring 校正记录——后续若引入 strict 模式（bool 严格 isinstance 双向），属行为变更另立单。

## 四、验收情况

- ✅ 清单行数与 rg 命中一致（命令与数字同段）；✅ 每行三列（file:line/实际语义/覆盖）；✅ 零改动未 push。

## 遗留问题

无。
