# learning 权威索引「我是权威」标记设计稿：frontmatter role 取代靠文件名日期挑档（l924-17，只出稿、零生产码改动）

> 状态：**设计稿，未落地**。本单不改 `tests/test_insights_index_closure.py`（生产码），只出稿 + 索引补列。
> 上游：`zcode-bridge/done/l923-01.result.md` 点名"哨兵的『权威索引』判定含一条隐含约定：靠文件名 8 位日期挑档。
> 要根除需给索引档加显式『我是权威』的机器可读标记（如 frontmatter），属另一单"。
> 复跑本档全部读数：`PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q` → 见 §六。

## 一、现状判据（逐字取自磁盘）

`tests/test_insights_index_closure.py` 里权威索引的取法只有三行：

```
def _index_candidates() -> list:
    return sorted(_rel(p) for p in INSIGHTS_DIR.glob("*insights-index*.md"))
def _authoritative_index() -> str:
    return max(candidates, key=lambda rel: (_date_key(rel), rel))   # :66（卷宗锚点 :65，因 l924-15 头注 +2 行而漂移）
```

即：**候选 = 文件名命中 `*insights-index*` 的档；权威 = 文件名里 8 位日期最大者，同日期再按路径字符串取最大**。
档头第 27 行那句「**当前权威索引是本文件**」是**给人读的散文**，机器完全不读。

## 二、这套隐式约定的失效面（全部实跑，不靠推演）

| # | 失效面 | 实测读数 | 后果是红还是假绿 |
|---|---|---|---|
| F1 | 任何新档只要名字含 `insights-index` 且日期更新，就**自动抢走权威**，原作者往往不知情 | `max(['…learn-insights-index-20260918.md', '…learn-insights-index-authority-20260924.md'], key=…)` → 后者胜 | **当场红**：新档表行数 B=0，`A != B` 与「未自登记」双红 ⇒ 属**可用性**故障（夜间无人值守时把整波拦在红名上），不是静默错 |
| F2 | 权威一旦落到旧索引 `learning-insights-index-20260917.md`，B 直接归零 | 该档 `^\| docs/insights/` 行数实测 **0**（它是"未引用清单"体例，不是条目表） | 同 F1：红，且**根因难查**（红名在另一份档上） |
| F3 | 同日期并列时按**路径字符串**取最大，与"哪份是权威"毫无语义关系 | `max(['…learn-insights-index-20260918.md','…zzz-insights-index-20260918.md'], key=…)` → `zzz-…` 胜 | **可真假绿**：若 `zzz-` 那份恰好也带条目表，B 由它算，闭合等式照样成立而**分母已换人** |
| F4 | `_DATE_TOKEN` 用 `search`，取名字里**第一个** 8 位数字 | `_date_key('learn-insights-index-v20260918-reprint-20260930.md')` → `20260918`（不是 20260930）；无 8 位数字 → `''` | 抢权威/丢权威都可能与建档人直觉相反；`''` 那份永远打不过任何带日期的档 |
| F5 | 候选 glob 与"条目表所在档"之间零约束：判据**只认文件名**，不认内容 | 本单产出档名 `learn-index-authority-mark-**index**…`：`fnmatch(名,'*insights-index*.md')` = **False** ⇒ 今天安全；但若哪天把 glob 放宽成 `*index*.md`，本档立即入选 | **最危险的一条**：`_table_entries()` 是**逐行裸扫 `^\| docs/insights/`，不认 markdown 代码围栏** ⇒ 任何在正文里贴"示例索引行"的普通档一旦入选，就把示例当成了真表 |

F5 直接决定了本稿的一条硬约束：**设计稿正文里的示例条目行一律前置一个空格**（`^|` 不再匹配），
即本档自我隔离于"被当成索引"这条路；这条约定要写进 schema（见 §三 `entry_after`）而不是靠人自觉。

## 三、Schema 草案（推荐 A，附 B/C 备选）

### A. YAML frontmatter（推荐）

放在**文件第 1 行起**，`---` 包块：

```
---
insights_index:
  role: authoritative          # 必填：authoritative | historical-snapshot
  as_of: 2026-09-24            # 必填：本标记最后一次人工复核的日期
  scope: docs/insights/*.md    # 必填：与 A 侧口径同（一层、不含子目录）
  entry_after: "| 文件 | 日期 | 主题（各档 H1 原文） | git 入库 | insights 外引用数 |"  # 必填：只在该表头行之后才承认条目行（治 F5）
  entry_prefix: docs/insights/ # 选填，默认 docs/insights/
---
# learning insights 索引（…原 H1 不动…）
```

规则与理由：
- `role` 取值封闭两元；**没写标记 = 未知，不当成 false**（回退见 §四），历史快照档**必须显式**写
  `historical-snapshot`，否则"无标记"与"忘了写标记"不可区分（今日盘上正是这个状态）。
- 解析用**两条正则**，不引 `yaml` 依赖：块必须锚在 `\A---\n`，`role:` 只在块内搜。
  实测冲突面为零：`docs/insights/*.md` 里**首行恰为 `---` 的档 = 0 份**（72 份全部首行是 H1）
  ⇒ 分隔线/setext 用法与 frontmatter 不会撞车。
- `entry_after` 是治 F5 的那味药：有了它，正文里贴示例索引行的普通档即使误入候选，也不会被读出条目表。
  该表头行**今天就在盘上**（锚文本 `^\| 文件 \| 日期` 在权威索引里实测**唯一命中**，且「表头之前出现的条目行数 = 0」）
  ⇒ 加这条规则**当天不改任何判据**，纯为将来兜底。**故意不写行号**：本单自己就往索引里插了 2 行，
  写死"第 36 行"落笔即漂（实测现值 :37）——与 l924-11「拆字面行号快照」同一条教训。
- **代价（必须写进迁移）**：72 份档现值"首行即 H1"是条不变量，加 frontmatter 的两份会破例。
  磁盘实测目前**无任何程序读 insights 的 H1**（`rg "docs/insights" scripts/ core/` 只命中
  `scripts/audit_paths_prereq.py:4` 的一句注释，且是"输出对齐参考"非解析）⇒ 破例只影响人读与
  索引表「主题（各档 H1 原文）」列的**取法**（人工取，需知道跳过 frontmatter）。

### B. 单行 HTML 注释（备选，改动最小）

`<!-- insights-index-role: authoritative -->` 置于第 1 行。零依赖、零 YAML 误判，且 markdown 渲染不显形。
缺点：无 schema、`as_of`/`scope` 无处安放，等于把隐式约定换个写法；不推荐做终态。

### C. Sidecar 文件（备选）

`docs/insights/.index-authority` 里写权威档名。优点：完全不碰 72 份档的首行不变量、且 `.md` 计数 A 不受影响
（glob 只算 `*.md`）。缺点：第二真值源，档名与 sidecar 可各自漂移——正是本稿要根除的病症，否决。

## 四、哨兵改法（唯一生产码改动，未落地；实测本 diff 块新增 25 行 / 删 5 行，含上下文整块 35 行）

设计取舍：**标记优先、无标记回退现值**，并把选路抽成**纯函数**，好让"有牙自检"能喂合成盘态
（照本仓 `_closure_diff` 的既有做法，测试零写盘）。

```diff
 def _date_key(rel_path: str) -> str:
     m = _DATE_TOKEN.search(Path(rel_path).name)
     return m.group(1) if m else ""
 
 
-def _authoritative_index() -> str:
-    """文件名 8 位日期最新的索引档；同日期时按文件名兜底（保证可复算、无并列歧义）。"""
-    candidates = _index_candidates()
-    assert candidates, "docs/insights 下没有任何 *insights-index*.md，闭合等式无从算起"
-    return max(candidates, key=lambda rel: (_date_key(rel), rel))
+# frontmatter 必须锚在文件第 1 行；只认块内的 role，其它键一律不猜
+_FM_BLOCK = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.S)
+_FM_ROLE = re.compile(r"^\s*role:\s*[\"']?([A-Za-z][\w-]*)[\"']?\s*(?:#.*)?$", re.M)
+
+
+def _frontmatter_role(text: str):
+    """档头 frontmatter 的 role；无 frontmatter 或块内无 role 一律返回 None（= 未知，走回退）。"""
+    m = _FM_BLOCK.match(text)
+    r = _FM_ROLE.search(m.group(1)) if m else None
+    return r.group(1) if r else None
+
+
+def _pick_authoritative(roles: dict) -> str:
+    """纯函数：{候选相对路径: role 或 None} -> 权威档。多份自封权威直接红（F3 的根治）。"""
+    marked = sorted(k for k, v in roles.items() if v == "authoritative")
+    assert len(marked) <= 1, f"多份索引档自封 authoritative，闭合分母失去唯一性：{marked}"
+    if marked:
+        return marked[0]
+    assert roles, "docs/insights 下没有任何 *insights-index*.md，闭合等式无从算起"
+    return max(roles, key=lambda rel: (_date_key(rel), rel))   # 回退路：与改前逐字同判据
+
+
+def _authoritative_index() -> str:
+    return _pick_authoritative({rel: _frontmatter_role((REPO_ROOT / rel).read_text(encoding="utf-8"))
+                                for rel in _index_candidates()})
```

可选附稿（**不计入上面 25 行**，约 5 行）：`test_权威选取有牙_多标记必红` ——
`_pick_authoritative({'a.md': None, 'b.md': None})` 必须等于 `_date_key` 最大者（回退路自证）、
`_pick_authoritative({'a.md': 'authoritative', 'b.md': 'authoritative'})` 必须 `AssertionError`（F3 自证）。

## 五、兼容性分析（核心问句：旧索引无标记时行为变不变？）

**不变，且可复算。** 三路盘态各自推演＋实测：

| 盘态 | `roles` 实值 | 走哪条路 | 与改前是否同解 |
|---|---|---|---|
| 今日（两份候选均无 frontmatter，实测 `首行 == "---"` 的档 = 0） | 全 `None` | 回退路 `max(roles, key=(_date_key, rel))` | **逐字同**：`roles` 的键集就是 `_index_candidates()`，`max` 的 key 与原实现同一表达式 ⇒ 现值仍 `learn-insights-index-20260918.md`（§六读数证） |
| 只给 09-18 加 `role: authoritative`（09-17 未加，即"只迁移一半"） | `{09-18: authoritative, 09-17: None}` | 标记路 | 同解（与今天日期路选出的正是同一份）⇒ **迁移过程零红**，可分批提交 |
| 两份都标（09-17 标 `historical-snapshot`） | `{09-18: authoritative, 09-17: historical-snapshot}` | 标记路 | 同解，且此后**改名不再影响权威归属**（F1/F3/F4 一并失效） |
| 反例：有人给 09-17 也写 `authoritative` | 两份都 marked | `assert` 当场红 | 新红——**这是设计意图**：把今天"靠日期暗斗"变成"显式吵架"，红名信息量足够定位 |
| 边界：候选为空（把两份索引都改名/删掉） | `{}` | 回退路前的 `assert roles` 红 | 与改前的 `assert candidates` 同语义、同文案 |

次生影响逐条：
- **A 侧**（`_disk_md_paths`）只看 `*.md` 是否存在，与文件内容无关 ⇒ frontmatter 不改 A。
- **自登记桩**（`test_权威索引在盘且自登记`）与**闭合桩**只读 `_authoritative_index()` 的结果 ⇒ 回退路同解则全绿。
- **有牙桩**（`test_新档漏登记必红_…`）喂的是合成 list，不经过 `_authoritative_index` ⇒ 不受影响。
- 渲染/工具面：GitHub 会把 frontmatter 渲成表格，档头 H1 下移 ⇒ 索引表「主题」列的人工取数需知"跳过 frontmatter"
  （本稿 §三-A 已写；建议同批在档头对账口径里加一句备注）。
- 回退路什么时候删？**先不删**。删它等于把"新索引未标记"从"暗地抢权威"升格为"当场红"，
  属判据收紧，需主班裁（见 §七）。

## 六、本单自证读数（2026-09-24 现取，会漂）

```
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q
3 passed
$ ls docs/insights/*.md | wc -l
73          # 加本档后 A
$ rg -c "^\| docs/insights/" docs/insights/learn-insights-index-20260918.md
73          # 加本档那一行后 B；A == B，C 空，重复 0
```
（改前现值为 A=B=72，与主班纪律档 §九 下传的 72 一致；本单为纯增量 +1，无去重、不改计数口径。）

## 七、落地顺序（交主班裁，本单一步都不做）

1. 生产码：按 §四 给哨兵打"标记优先 + 回退"兼容版（同批跑 §六 两条读数，必须仍 3 passed）。
2. 数据：给 `learn-insights-index-20260918.md` 加 §三-A frontmatter（`role: authoritative`，
   `entry_after` 抄该档表头原文（不写行号，见 §三-A 的自漂教训），实测表头之前零条目行）；给 `learning-insights-index-20260917.md`
   加 `role: historical-snapshot`。两步各自跑哨兵，均应绿（§五 表第 2/3 行）。
3. 复核：跑一次"抢权威演习"——临时把某档改名成 `learn-insights-index-20990101.md` 复跑哨兵，
   **加了标记后必须仍选原权威**（这是本稿的验收判据，也是 F1 的否证证据）；演习在沙盒副本里做，别在真盘上留痕。
4. 观察 ≥1 浪后再议是否删回退路（收紧为"无标记即红"）。删之前，`docs/insights` 里任何新增 `*insights-index*`
   命名的档都得先写标记，这条要进 AGENTS/CLAUDE 的索引维护口径，否则等于没治。

## 八、遗留与未覆盖

- 本稿只治"谁是权威"，不治"条目表内容对不对"（引用数、git 入库两列仍靠人工）。顺手量了一刀这第二族：
  表内 `| 未跟踪 |` 现 **9 行**，逐行 `git ls-files --error-unmatch` 复验 ⇒ **9/9 全部早已入库**
  （列值 100% 过期，含本波 l924-04/05/06 三份）。哨兵只看第一列，**这类漂移它结构性地拦不住**——
  要不要把第四列也纳入判据属**改计数口径**，超出本稿授权，留主班裁。
- `_ENTRY_ROW` 不认代码围栏这条（F5 根因）若不想靠 `entry_anchor` 兜，另一条路是把索引体例从 markdown 表格
  改成 YAML/JSON 清单 + 渲染视图；那是**改体例**，牵动 72 行表和既有对账命令，成本远高于本稿，未推。
