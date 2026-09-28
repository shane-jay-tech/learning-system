# insights 索引闭合哨兵「权威索引」隐含条件清单与显式化裁决材料（l927-33，只读位·零码改动）

- 任务：`zcode-bridge/done/l927-33.task.md`（班 `qoder-executor-20260928-0210-learn52`，2026-09-28）
- 盘面：`D:\code\learning-system` @ HEAD `4309041`（开工现取，porcelain=0）
- 上游：`zcode-bridge/done/l923-01.result.md` 遗留问题 2（哨兵的「权威索引」判定含一条隐含约定）
- 纪律：只读位 ⇒ **`tests/test_insights_index_closure.py` 一行未动**，断言只出草案（§三）

## 一、与 l924-17 的分工（别把本单当重复建设）

l923-01 点名的只有**挑档那一条**。l924-17（`learn-index-authority-mark-design-20260924.md`）已就那一条
出了 frontmatter 标记设计稿并实测了 F1-F5 五个失效面。本单复核：

```
$ grep -n "authority\|frontmatter\|我是权威" tests/test_insights_index_closure.py
（零命中，rc=1）
```
⇒ **设计稿至今未落地**，权威索引判定仍是 `tests/test_insights_index_closure.py:62-66` 的
`max(candidates, key=lambda rel: (_date_key(rel), rel))`；
而 l924-17 自己在索引表里那行（`:76`）第 4 列仍写「未跟踪」（实际早已入库）。

本单的增量＝把**整条判定链**（候选集 → 挑档 → B 取数 → A 取数 → 闭合等式 → 自检例）的隐含条件一次列全，
l924-17 已列的 F1/F3/F4/F5 直接引用不重算（只复核在现值仍成立），F6 起为本单新增。

## 二、隐含条件清单（15 条；「触发后果」区分当场红／假绿，这决定优先级）

| # | 隐含条件（当前无人钉，靠巧合成立） | 现值读数 | 触发后果 | 出处 |
|---|---|---|---|---|
| I1 | 候选集＝文件名命中 `*insights-index*.md` 的档；**只认文件名不认内容** | 盘上候选恰 2 份 | 任一新档含该子串即抢权威 ⇒ 当场红（B=0） | l924-17 F1/F5 |
| I2 | 权威＝文件名里**第一个** 8 位数字最大者（`_DATE_TOKEN.search`，非 findall/max） | `learn-insights-index-v20260918-reprint-20260930.md` → `20260918` | 抢／丢权威与建档人直觉相反 | l924-17 F4（本单复算仍成立） |
| I3 | 同日期并列 ⇒ 按**路径字符串**取最大，与语义无关 | `max(['…20260918…','…zzz-…20260918…'])` → `zzz-` 胜 | 🔴 **可真假绿**：分母换人而等式仍闭合 | l924-17 F3 |
| I4 | 文件名**无 8 位日期**者 `_date_key` 返回 `''`，永远打不过任何带日期的档 | `l927-33-sentinel-implicit.md` → `''` | 静默不入选＝**假绿**（新索引写了也不算权威，且没人报错） | 本单新增 |
| I5 | 权威索引必须**自登记**在自己的表内（B 含索引自身 1 份） | `test_权威索引在盘且自登记` 已钉 | 已显式（唯一被钉住的一条） | 哨兵 `:87-92` |
| I6 | A 的口径＝`INSIGHTS_DIR.glob("*.md")` **只一层、大小写敏感、不含子目录** | A=107（含本班 3 份未登记档，本档自身计入） | 有人把 insights 归档进子目录 ⇒ 该项从 A 消失，若表里还留着它 ⇒ extra 红 | 本单新增 |
| I7 | 表行必须**顶格**：模式是 `^\|` ＋紧跟路径，缩进两格就不入 B | 探针：`   \| docs/insights/indented-b.md` → **未命中** | 项数少算 ⇒ A>B、missing 红（可诊断，不是假绿） | 本单新增 |
| I8 | 表行**不认 markdown 代码围栏**：正文里贴的"示例索引行"会被当真表 | 探针：围栏内 `\| docs/insights/fenced-c.md` → **命中** | 🔴 与 I1 合起来是**假绿配方**：一份含示例行的普通档一旦成为权威，B 由示例行算 | l924-17 F5 后半（本单复算） |
| I9 | 第一列必须逐字等于 `docs/insights/<名>.md`：`./` 前缀、`docs/Insights/` 混大小写都不入 B；含空格的文件名只截到空格前 | 探针：`./docs/…` 未命中、`docs/Insights/…` 未命中、`space f.md` 截成 `docs/insights/space` | 双红（missing＋extra），可诊断 | 本单新增 |
| I10 | **档与索引必须同批**才闭合：哨兵无宽限、无 allowlist、无"在途档"概念 | 本班新增 2 档 ⇒ 当场 2 failed | 每次代提交拆两笔（出档一笔／补索引一笔）就有一段**必然红**的中间态；夜间无人值守时按红名拦波 | 本单新增（＝横幅说的"预期红"） |
| I11 | 权威索引必须登记**全部**磁盘 md，**含历史快照索引本身**（09-17 那份也在表里） | 候选 2 份，09-17 那份表行 0 条 | 若权威落到 09-17 ⇒ B=0 双红且根因在另一档 | l924-17 F2 |
| I12 | 索引档头那句「本文件为当前权威索引」是**给人读的散文**，机器零读取 | `learn-insights-index-20260918.md:1` | 人读与机器判定可以相反（I3 触发时即如此） | l924-17 §一 |
| I13 | 索引头承诺的「对账三条＋改档必重跑并回填读数」**本身无哨兵**：头里读数停更不会红 | 头最后一条回填＝`:28` 行 2026-09-25 的 **A=77、B=77**；磁盘实取 **A=107** | 🔴 **已经漂了 30 条而全绿**——这是清单里唯一一条**现值即命中**的失效面 | 本单新增 |
| I14 | 表第 4 列（git 入库状态）、第 5 列（引用数）不参与判定 | 现值该列大量「未跟踪」（l924-17 `:24` 已自述"该列整体过期"） | 只误导人读，不拦机器 | 本单新增 |
| I15 | 有牙自检例 `test_新档漏登记必红…` 起手就 `assert 现值闭合` ⇒ 盘子不闭合时**自检例自己也红** | 本班实测 **2 failed, 1 passed**（两条红都源于同一缺登） | 红名成对出现 ⇒ 按红名数估缺陷数会翻倍 | 本单新增（哨兵 `:119`） |

## 三、显式断言草案（可批形状；`tests/` 属生产码，本班零改动）

按「先堵假绿、再堵可用性红」排序，每条给出落点与最小形状（示意，非最终代码）：

```python
# D1（堵 I1/I12/I3，＝l924-17 主案）：权威由档内机器可读标记声明，文件名日期只作交叉校验
_AUTHORITY = re.compile(r"^<!--\s*insights-index-authority:\s*(\d{8})\s*-->", re.M)
def _authoritative_index():
    marked = [rel for rel in _index_candidates()
              if _AUTHORITY.search((REPO_ROOT / rel).read_text(encoding="utf-8"))]
    assert len(marked) == 1, f"『我是权威』标记必须恰 1 份，实得 {marked}"      # 0 份或多份都当场红
    return marked[0]

# D2（堵 I1/I8/I11）：候选即表——入选的每份档必须有可解析的条目行，且权威档的表非空
def test_候选必须是表不是散文():
    for rel in _index_candidates():
        assert _table_entries(rel) or rel != _authoritative_index(), f"{rel} 命中候选 glob 却零条目行"

# D3（堵 I2/I4）：文件名日期必须存在且唯一，杜绝 search 取首个与 '' 静默垫底
def test_权威档文件名带且只带一个8位日期():
    toks = _DATE_TOKEN.findall(Path(_authoritative_index()).name)
    assert len(toks) == 1, f"文件名日期歧义 {toks}"

# D4（堵 I3）：同日并列直接判失败，不走字典序兜底
def test_无并列同日候选():
    dates = [_date_key(c) for c in _index_candidates()]
    assert len(dates) == len(set(dates)), f"同日候选 {dates}，权威归属当前靠文件名字典序"

# D5（堵 I7/I9）：表行形状规范绑磁盘实取，而不是"大家写对了"
def test_表第一列逐字等于磁盘相对路径():
    disk = set(_disk_md_paths())
    bad = [e for e in _table_entries(_authoritative_index()) if e not in disk and "/" in e and " " not in e]
    assert bad == [], f"表内路径写法与 as_posix 口径不符：{bad}"

# D6（堵 I8）：_table_entries 跳过 ``` 围栏（实现面＋一例断言：围栏内示例行不进 B）

# D7（堵 I13）：索引头最后一条回填读数 == 磁盘实取，让"改档必回填"这条纪律本身可被机器拦
def test_索引头回填读数不陈旧():
    last = int(re.findall(r"A=(\d+)", head_text)[-1])
    assert last == len(_disk_md_paths()), f"头里停在 A={last}，磁盘实取 {len(_disk_md_paths())}"

# D8（堵 I15 的读数迷惑）：自检例把"现值不闭合"与"哨兵无牙"分开报——起手 assert 改成带 id 的 skip/分组
```

## 四、两案与代价

### 甲：显式化（＝落 D1-D7，推荐分批）

- **批 1（最小切口，纯拦假绿）**：D1＋D2＋D4。改动面＝哨兵件约 +25 行，
  外加**一次性**给现权威档 `learn-insights-index-20260918.md` 顶部加一行标记注释（`docs/` 文本，1 行）。
  直接消灭清单里三条最危险的：I3（同日字典序真假绿）、I8×I1（示例行假绿）、I11（权威落到散文体旧索引）。
- **批 2（可用性面）**：D3＋D5。I2/I4/I7/I9 全部从"可诊断红"升级为"当场点名"。
- **批 3（纪律自证）**：D7＋D8＋D6。⚠️ **D7 落地当天必红**：头里回填停在 A=77（`:28`，2026-09-25），
  磁盘实取 A=107 ⇒ 要么先把头注补齐 30 条，要么 D7 以「警告不拦」起步。这条要主班拍，不是执行班能定的。
- 代价：①写档纪律变化（新索引档必须带标记；多标记＝当场红）；
  ②`tests/test_insights_index_closure.py` 属生产码 ⇒ **需写位班次**，本波只读位不落；
  ③D1 落地后 l924-17 设计稿可关闭（其 §六 复跑读数要同步）。

### 乙：维持隐含＋文档

- 改动面：把 §二 清单抄进哨兵档头（现档头已写 I5/I11 相关两句）＋在索引头加硬约定
  「新建索引档必须：① 名字含 `insights-index` ②带**唯一** 8 位日期 ③正文第一行写「本文件为当前权威索引」④表自登记」。
- 优点：零测试码改动，零写位需求。
- 缺点：②③④全是**人读散文**（I12），机器照旧靠文件名日期＋字典序挑档；
  I3／I8 两条假绿路径**一条都没堵**；I13 已经实证"靠纪律回填的读数会漂 30 条而全绿"，
  所以"再加一条散文约定"的预期收益有反例可查。

### 推荐：**甲，且按批 1 先走**

任务书要求的推荐方向是显式化，本单复核后仍站得住，但要收窄成「批 1 三例」而不是 D1-D7 一把梭：
1. 批 1 只碰哨兵件＋1 行档内注释，回滚成本＝`git revert` 一笔，无数据面；
2. 它拦的是清单里唯二能**假绿**的 I3/I8，其余（I1/I2/I4/I7/I9/I11）触发时本来就红，属可用性问题，可排在批 2/3；
3. 批 3 的 D7 一落地就红，需要人工先决定「补头注」还是「警告不拦」——把它和批 1 捆在一起会让批 1 也背上人工闸。

若判甲，**必须同批**处理的两件：①l924-17 设计稿的在册状态更新（它的 §一 判据现值仍写着 `:66`，
本单复核 `:62-66`，未漂）；②索引表第 4 列「未跟踪」的陈旧标记（I14）——否则显式化之后仍是"机器绿、人读红"。

## 五、本班撞到的预期红（点名，非缺陷）

```
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q
rc=1 · 2 failed, 1 passed in 0.08s
FAILED …::test_闭合等式_A等于B_且C为空_且无重复
FAILED …::test_新档漏登记必红_改名必红_有牙自检
E   At index 0 diff: ['docs/insights/l927-30-except294.md', 'docs/insights/l927-31-uploader-residue.md',
                      'docs/insights/l927-33-sentinel-implicit.md'] != []
$ 同批实取：A=107、B=104、重复=0、C=上面 3 条
```
⇒ 正是 I10＋I15 的组合：出档班只出档、索引由主班单点写（索引头 `:20` 的并行纪律），
中间态必红且**红名成对**（3 档未登记也只报 2 个红名，不是 3 个）。
本班按横幅纪律**不自己改索引**。

## 六、本单不动的东西

- `tests/test_insights_index_closure.py`、`docs/insights/learn-insights-index-20260918.md`、
  `docs/insights/learn-index-authority-mark-design-20260924.md`：零改动。
- `data/progress.db`：不连不写（本单全部读数来自 `docs/insights` 只读文本与正则探针，无 DAO）。
