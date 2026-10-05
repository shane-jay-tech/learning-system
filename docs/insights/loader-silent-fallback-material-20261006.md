# loader 静默回退族材料：空 yaml 幽灵题＋同形异码键＋无体积限额（l1004-03；1247 D-6/D-9/D-10）

> 产线：执行班 l1004-03（2026-10-06）。**材料型，零码改动**；与 l927-06（格式一致性抽检，逐字段粒度）不同层——本单管 loader 的**静默回退语义**。
> 矿源：`zcode-bridge/done/20260925-120550-1247.result.md` 遗留节 D-6/D-9/D-10 逐字（见各节引文）。

## §一 现值复核（行号＋幽灵题普查）

- `load_language`（`core/loader.py:136`）／`_build_problem`（`:191`）；关键锚：**`:164 data = yaml.safe_load(f) or {}`**——空文档 None 被 `or {}` 洗成合法空 mapping，绕过 :166-170 的非 dict 检查，`_build_problem` 用 `str(data.get("title") or problem_slug)`（:213）回退 title＝文件名、`statement or ""`（:216）空题面 ⇒ **D-6 幽灵题通道现值仍在**。
- **幽灵题现存普查（只读扫描，命令与数字内联）**：全 `content/` 408 份 yaml 逐份 `yaml.safe_load` 复演 loader 判据——
  ```
  $ python - <<EOF （safe_load 后判 not data / title falsy / NFKC 键比对）
  total_yaml=408
  empty_doc=0
  title_fallback=0        （其中 statement 同空的=0）
  homoglyph_keys=0        （NFKC 归一后撞预期键名的异码键）
  ```
  **三形态现存数全零**——缺陷是结构性通道（AI 生成题库文件入库时即触发），现库存量健康、未爆发。
- **D-9 体积分布**：`max=2,978B（content/agent_dev/11_real_tasks/08_end_to_end.yaml）`、p95=1,866B、median=749B——现库无大文件；「300KB／2 万键照样吃进」为通道性缺失，现值无受害者。

## §二 三修法与诊断计数连带面

### 案 1（D-6）空文档判错

- **修法**：`:164` 改 `data = yaml.safe_load(f)`，把「None／非 dict」统一交给 :166 的既有非 dict 检查（`TypeError("yaml root is NoneType…")` 进 `_record_load_error`）——空文件从「幽灵题」变「诊断记录＋跳过」，与坏 yaml 同通道。
- **诊断计数变化估计**：现库 empty_doc=0 ⇒ **+0 条**（零连带）；未来首个空文件入库时 +1（当前该形态会 +1 题目、0 诊断）。

### 案 2（D-10）同形异码键 NFKC 告警

- **修法**：`_build_problem` 入口对 `data.keys()` 做 NFKC 归一比对——`unicodedata.normalize('NFKC', k)` 命中预期键名集合（title/topic/statement/…）而原键不等 ⇒ `_record_load_error(yaml_path, Warning(f"homoglyph key {k!r} → {nk!r}"))` 并按归一键取值（或拒绝，二档任选，材料建议**先告警后取归一值**保题目可用）。
- **诊断计数变化估计**：现库 homoglyph=0 ⇒ **+0 条**；对「AI 生成题库文件」（1247 点名的高危源）每命中一个异码键 +1。预期键名集合应与 `_build_problem` 实际消费的 14 键单源（防第三份名单——建议从 Problem 构造参数推导或与 l927-06 的字段清单合一）。

### 案 3（D-9）体积限额提案

- **修法**：读文件前 `os.path.getsize` 预检（建议阈值 **256 KB**，现库 max 2,978B≈87 倍裕量），超限 `_record_load_error`＋跳过；键数限额（建议 2,000 键/文件）可后置——yaml 解析后 `len(data)` 便宜，解析前无法廉价计数，**第一阶段只做字节预检**即可挡住「大文件拖慢整页」主害。
- **诊断计数变化估计**：现库 max 2,978B ⇒ **+0 条**；阈值裕量 87 倍，误伤风险趋零。

## §三 连带面与落地边界

- 三案全部只增 `_record_load_error` 诊断，不动 Problem 结构/判分/缓存签名（`_signature` 若纳入限额状态需评估缓存失效面——**建议限额不做进签名**，诊断在读取时点产生即可）。
- 诊断出口：`_last_load_errors` 的现有消费面（报告/诊断页）零改动即受益——计数自然从 0 基线起步。
- 落地属 loader 行为变更（题库可见面），按任务书材料型另派；落地时建议与案 1 同批（同一行 :164 的连带改动最小）。
