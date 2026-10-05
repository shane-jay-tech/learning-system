# loader 诊断信息面材料：LoadDiag 无行列＋递归锚点延迟爆炸＋编码声明失效（l1004-04；1247 D-7/D-8/D-13）

> 产线：执行班 l1004-04（2026-10-06）。**材料型，零码改动**；l927-02 已管 D-12 编辑器列定位纯函数，本单不重复——本单管 **loader 诊断结构** 与**加载期**两案＋一句文档注记。

## §一 现值复核（行号贴出）

| 项 | 现值锚 |
|---|---|
| LoadDiag 字段 | `core/loader.py:57-62`——**仅 `path / error_type / message` 三字段**，无 line/column |
| 截断位 | `:78 message=str(exc)[:200]`（诊断）＋ `:81 logger.warning(...[:200])`（日志）——两处独立截断，message 里第二处位置信息可被切掉（D-7 后半） |
| yaml 入口 | `loader.py:164 yaml.safe_load(f) or {}`（题库）；`core/paths.py`（配置，另一张脸不在本单面） |
| D-8 复演 | `$ python - <<EOF`：`x: &x [1, *x]` → `safe_load` 成功、`data['x'][1] is data['x']=True`、`json.dumps(data)` → `ValueError: Circular reference detected`——**加载期合法、序列化期才炸，爆炸点与坏文件分离** ✓（矿源机制复现） |
| D-8 存量普查 | 全 408 份 yaml id-set DFS 环检测 → **recursive_anchor_files=0**（存量零命中） |
| D-13 现值 | `PREAMBLE` 6 行（`error_feedback.py:30-37`，`PREAMBLE_LINES=len(...)` 派生）⇒ 学生第 1 行被挪到文件第 7 行，Python 编码声明（须在 1-2 行）**必然失效**；runner 写文件本就 `encoding="utf-8"`（python_runner.py:132）＋preamble 里 `reconfigure(encoding='utf-8')`——声明冗余但会误导；题库存量 `# -*- coding -*-` 声明 **0 份**（rg 零命中）⇒ 零现存受害者 |

## §二 两案设计（消费面对照）

### 案 1（D-7）诊断结构化：line/column 字段化＋截断保位

- **修法**：LoadDiag 增 `line: Optional[int] = None`／`column: Optional[int] = None` 两字段（dataclass 尾插带默认值＝向后兼容，既有 3 字段消费面零改动）；`_record_load_error` 里 `mark = getattr(exc, 'problem_mark', None)`（yaml.YAMLError 系自带），命中则填 `mark.line+1 / mark.column+1`。
- **截断保位**：`[:200]` 保留不动（日志口径），但 UI/测试**不再依赖 message 文本里的 "line X, column Y"**——位置改读结构化字段；message 可另做头尾保留（l1004-02 案 2 同族改法，此处不展开）。
- **消费面对照**：
  | 消费点 | 现状 | 改后 |
  |---|---|---|
  | `get_load_diagnostics()`（loader.py:70）→ `tests/test_content_fuzz_pins.py`／`tests/test_parser_boundary_inputs_20260925.py` | 断言 diag 数量/类型 | 字段新增不破既有断言 |
  | 诊断 UI（报告页） | 显示 message 文本（位置被截则丢） | 直接渲染「第 N 行第 M 列」 |
  | l927-02 D-12 列定位 | 编辑器 traceback 列定位（学生代码） | **不同脸**：loader 诊断是题库文件定位，两者共用「行列字段化」理念但无代码交叠 |

### 案 2（D-8）递归锚点加载期检测（锚点环检查）

- **修法**：`_build_problem` 前对 `data` 做 id-set DFS 环检测（本班普查所用同型函数，~10 行），命中环 → `_record_load_error(yaml_path, ValueError("recursive YAML anchor detected"))`＋跳过该文件——把「序列化期爆炸（UI/AI 载荷 json.dumps 处，与坏文件分离）」提前到**加载期诊断位**。
- **成本**：O(节点数)，408 文件 max 2,978B 下总开销毫秒级；不需 yaml constructor 级禁 alias 重载（ heavier 且会误伤合法共享子结构）。
- **诊断计数变化估计**：现库 recursive_anchor_files=0 ⇒ **+0 条**；未来首个递归锚点文件从「UI 随机点位 ValueError」变「loader 诊断 +1，文件跳过」——爆炸点收敛回坏文件本身。

## §三 D-13 注记文案（README/OPERATIONS 一句话）

> **学生代码不享编码声明语义**：判题执行器会在学生代码前注入 6 行引导段，`# -*- coding: -*-` 声明因此不在文件头两行、被 Python 忽略。运行器恒以 UTF-8 读写源码与输出流，学生**无需也不应**依赖编码声明；源码里的非 ASCII 字符直接按 UTF-8 书写即可。

（落点建议：README「学习闭环」沙箱小节或 OPERATIONS 运行器段；零码改动，文档批次带走。）
