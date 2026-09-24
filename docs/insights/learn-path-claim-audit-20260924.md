# learning path 文案 ⇄ 磁盘题数过期自述普查（l924-19，只读 · 零内容改动）

> **卷宗**：`zcode-bridge/inbox/l924-19.task.md`（现址 `zcode-bridge/done/`）。上游依据＝`zcode-bridge/done/l923-13.result.md` 收尾自述「若想系统性清一遍『文案说没有、磁盘已有』的过期自述……需要一条『path 文案 ⇄ 题数』的可判定命题，属新单；本单未扩」。
> **本单性质**：只读普查＋可判定命题草案。**未改任何 content/、core/、ui/、tests/ 文件**（完成标准③）。
> 探针（gitignored，`git check-ignore -v tmp/l924-19/probe.py` → `.gitignore:19:/tmp/`）：`tmp/l924-19/census_path_claims.py`、`tmp/l924-19/propositions.py`、`tmp/l924-19/out.json`。

## 一、卷宗前提逐条实测（含 2 处否证）

| # | 卷宗前提 | 现取读数 | 命令（cwd `D:/code/learning-system`） | 判定 |
|---|---|---|---|---|
| 1 | `people_analytics.yaml:16` 的 `graduation_project: "写一个简单的薪资计算器：输入基本工资和绩效系数，输出税后月薪"` | **逐字命中、行号零漂移**（m1） | `sed -n '16p' content/paths/people_analytics.yaml` | ✅ |
| 2 | 🔴 「rg 实测 **7 文件**」 | `content/paths/*.yaml` 实为 **6 份**；`rg -l graduation_project` 全仓 **8 份**（6 份 yaml ＋ `core/paths.py` ＋ `ui/pages/path.py`）。两头都不是 7 | `ls content/paths/*.yaml \| wc -l`；`rg -l graduation_project .` | ❌ 否证（见 §七-1） |
| 3 | 🔴 「**16+ 处** graduation_project/description 陈述句」 | 该两字段**共 82 行**（各 41 行，41 个里程碑全有值）；含 path/milestone 标题则 **129 行**。而**值本体含数字**的只有 **12 行 / 14 个数字出现**。「16+」与任一口径都不吻合 | `rg -c "(description\|graduation_project):" content/paths/*.yaml`；`python tmp/l924-19/census_path_claims.py` | ❌ 否证（口径不明，已给三个可复算读数） |
| 4 | l923-13 已删的两处「（待题目新增后解锁）」没有回流 | `rg -n "待题目新增后解锁" content/paths/` → **rc=1 零命中**；GAP 式（`还没有\|暂无\|待解锁\|待补充\|待题目\|尚未`）普查 → **0 处** | 见 §九配方第 4 条 | ✅ 且**卷宗设想的"系统性存量"现值为 0**（⇒ 本单的真产出是防回归命题，不是一批订正） |

## 二、现值（每项绑命令；HEAD `ed63884`，2026-09-25T00:4x）

| 量 | 现值 | 现取命令 |
|---|---|---|
| path 文件 / 里程碑数 | 6 份；**41** 个里程碑（agent_mastery 11／cpp 5／people_analytics 11／python_advanced 5／quick_stats 5／r_advanced 4） | `python tmp/l924-19/census_path_claims.py` → `milestone_total` |
| 承诺字段 | `description` 41、`graduation_project` 41（41/41 **无一空缺**）、含 title 共 129 行 | §九配方第 5 条 |
| 值含数字 / 数字出现 | **12 行 / 14 个**（其中指向磁盘量的只 **1** 处） | `python tmp/l924-19/propositions.py` → `P1 数字条数` |
| GAP 式空缺承诺 | **0** | 同上 → `P2 空缺承诺命中` |
| 里程碑引用专题题数（双轨） | 磁盘 glob 与 `core.loader` 运行时**逐专题相等，差额 0 条** | `python tmp/l924-19/census.py` → `topic_track_delta`（实跑 `[]`） |
| 引用专题为 0 题/缺失 | **0**（41 个里程碑引用的专题全部有题） | 同上 → `zero_or_missing_topics` |
| 专题被引覆盖 | 全 path 引用去重 **85** 个专题 == 磁盘 `content/<lang>/<topic>/` 目录数 **85**（`ls -d content/*/*/ \| wc -l`）⇒ `learn-path-coverage-fill-20260920.md` 那条"42 个未引用全部进线"**仍成立** | 两条命令并列 |
| 每 path 题数合计（含跨路复用） | agent_mastery 98／cpp 62／people_analytics 152／python_advanced 66／quick_stats 20／r_advanced 45 | §九配方第 6 条 |
| 工时自洽 | 6/6 path 顶层 `estimated_hours` − Σ 里程碑 = **0**（29/21/53/21/10/14.5） | `propositions.py` 同型脚本 → `hours_check` |
| 术语锚定（P6 见 §四） | 文案里 **66** 个 ASCII 术语；三档锚点口径下未命中数 **8 → 4 → 2**（① 被引专题 `*.yaml` ② 再加 `_lesson.md` ③ 升到"整条 path 全部专题"）⇒ **口径本身就能把"缺陷"数改 4 倍**，命题必须点名口径 | §九配方第 7 条（三口径并列跑） |

## 三、过期自述清单（完成标准①：逐条带 yaml 行号＋题数实值）

**A 类＝文案承诺与磁盘内容不符（真货，1 条）**

| # | 落点 | 文案原句 | 磁盘实值 | 判据 | 定性 |
|---|---|---|---|---|---|
| A-1 | `content/paths/agent_mastery.yaml:26`（里程碑 **a1**「Git 救命技能」的 `graduation_project`；:21 的 `description` 同族「agent 写坏代码时如何回滚」） | 「模拟一次 agent 写坏代码后**用 git revert 恢复**」 | a1 只引 `agent_dev/01_git_basics`，**5 题**（磁盘 glob 与 loader 双轨同值）；该专题（含 `_lesson.md`）`rg -c -i "revert"` **零命中**，唯一含 `revert` 的地方是**文件名** `05_revert.yaml`；全仓正文里的 `revert` 只有 **2 处**，都在 `agent_dev/11_real_tasks/06_emergency_rollback.yaml:34/:52`——那是 **a7**（:77-81）引的专题 | 双重毛病：①**里程碑级错位**（a1 承诺、a7 才教）；②**命令语义混用**（`05_revert.yaml:1/:7/:10` 考的是 `git checkout .`／`git restore .`＝丢弃**未提交**改动，而 `git revert` 撤销的是**已提交**历史） | 🔴 **内容正确性域**（GOAL.md §二红线 4）⇒ 本单**只出报告不改字**。三条出口（a1 文案改口径 / 把毕业项目挪到 a7 / 在 `01_git_basics` 补一道真 `git revert` 题）都需人工拍，补题那条还会牵题数等值断言族（§五） |
| A-2 | `content/paths/agent_mastery.yaml:36`（a2 gp「读一段 agent 写的 **100 行代码**，找出 3 个潜在问题」） | 同左 | a2 引 `agent_dev/02_debug_read`＋`08_read_code`，合计 **9 题** | 14 个数字里**唯一**在题面找不到锚点的（`anchor_hit=False`）；属"操作描述"而非磁盘量 | ⚠ **待人工核**（低危：不必改文案，但命题白名单要显式收它，否则每次跑都报） |
| A-3 | `content/paths/people_analytics.yaml:27`（m2 gp「解析一份 **CSV** 格式的员工名册，统计各部门人数」） | 同左 | m2 引 `python/05_lists`／`06_strings`／`07_dicts_sets` 三专题共 **15 题**；三专题（`*.yaml` **＋ `_lesson.md`** 全扫）`rg -c -i "csv"` **零命中**（rc=1）；同 path 的 CSV 素材出现在**更晚**的 m7（`sql/…/\_lesson.md`）与 m10（12 件题面） | 与 A-1 同族＝**里程碑级错位**（本里程碑承诺了后面才教的素材），**不是** path 级缺失（path 级口径下 CSV 不再未命中） | ⚠ **低危，待人工**：出口是把这句话挪到 m10／或接受"里程碑文案可预告后续素材"这条口径并把它写进命题白名单。🔴 本单不改文案 |

**B 类＝卷宗设想的"文案说没有、磁盘已有"（现值 0 条）**：GAP 式命中 **0**（§一-4）。l923-13 那两处即该族全部存量，删后无第三处、无回流。
**C 类＝数字疑似但非磁盘量（假阳，必须被命题挡掉）**：12 行里 11 行属此类（`30 行以内`／`3 条反馈`／`5 个子任务`／`3 段报错`／`2 轮迭代`／`v1`/`v2`／`前 3 个高频字符`／`Milestone 3`／`ggplot2` 的 `2`×2／`9 题问卷`）。其中 `9 题问卷` 虽是"磁盘量词"形状，但**有题面源**：`content/r/15_cfa/03_cfa_interpret.yaml:7` 逐字写「一份 9 题工作敬业度量表 (UWES-9)」⇒ 若拿它去对拍该里程碑磁盘题数（**4**）就是**假红**（s5，`quick_stats.yaml:51`）。
**D 类＝序数跨引（成立）**：`people_analytics.yaml:94` m7「用 R 复现 Milestone 3 的流失率分析」⇒ 第 3 个里程碑 `m3` 存在，其 gp 逐字含「员工**流失率**」⇒ **P3 通过**；但本仓里程碑**没有序号字段**，`Milestone 3` 靠**列表位次**解释（`core.paths.load_all_paths()` 按 yaml 顺序）⇒ 有人在 m1–m3 之间插一个里程碑，这句话就会**静默指错**，这是 P3 要钉的真风险。

## 四、可判定命题（完成标准②：可机执行，正则＋双轨）

```python
# 每条都是"红/绿"或"进待人工清单"，永不自愈、永不改文案
F = re.compile(r'^\s*(description|graduation_project):\s*["\']?(.*?)["\']?\s*$')        # 字段行
NUM   = re.compile(r"(\d+)\s*(道题|题|个专题|个知识点|章节)")     # P1a 数字=磁盘量
GAP   = re.compile(r"还没有|暂无|待解锁|待补充|待题目|尚未")     # P2  空缺承诺
MSREF = re.compile(r"Milestone\s*(\d+)")                        # P3  序数跨引
def per_topic(lang_slug):                                        # 双轨：缺一轨即红
    disk    = len(glob(f"content/{lang}/{slug}/*.yaml"))         # 轨 1 磁盘
    runtime = len(load_language(lang)[slug].problems)            # 轨 2 运行时 loader
    assert disk == runtime, (lang_slug, disk, runtime)           # 不等 ⇒ 红（loader 漏读/多读）
    return disk
for yml in glob("content/paths/*.yaml"):
    ms = yaml.safe_load(yml)["milestones"]
    for i, m in enumerate(ms, 1):
        n = sum(per_topic(t) for t in m["topics"])               # 该里程碑磁盘题数
        for line_no, (fld, val) in fields(yml, F):               # 只测值本体，禁测带行号前缀的整行
            assert not (GAP.search(val) and n > 0), f"{yml}:{line_no} 空缺承诺 vs 实有 {n} 题"   # P2
            for d, unit in NUM.findall(val):                     # P1a 数字型磁盘量
                if anchor_in_topic_bodies(val, d, unit): continue        # 题面有源（如 UWES-9）⇒ 绿
                assert int(d) == n, f"{yml}:{line_no} 文案 {d} {unit} vs 磁盘 {n}"              # 否则红
            for k in MSREF.findall(val):                         # P3 序数跨引
                assert k <= len(ms) and keyword_shared(ms[k-1], val), f"{yml}:{line_no} Milestone {k} 指错"
    assert yml_top_hours == sum(m["estimated_hours"] for m in ms)                # P4 工时自洽
    assert all(per_topic(t) > 0 for m in ms for t in m["topics"])                # P5 被引专题非空
```

命题有效性实测（🔴 三条都是拿读数逼出来的，不是设计偏好）：
1. **P1 必须先过"量词＋题面有源"两道闸**。裸数字在题面里的命中率 **13/14 = 92.9%** ⇒ 用裸数字当锚点≈永绿（假绿）；改成"数字＋行/题/个/条/轮/道/章"量词构造后只剩 **8/14** ⇒ 另 6 处是 `v1`/`ggplot2`/`Milestone 3` 这类**非量词数字**，必须显式排除而不是靠正则碰运气。
2. **P1a 与磁盘题数对拍要带"题面源"豁免**，否则 `quick_stats.yaml:51` 的「9 题问卷」会被判成"文案 9 vs 磁盘 4"假红（实为 `03_cfa_interpret.yaml:7` 的 UWES-9 量表）。
3. **术语锚定（P6）只能 warn、不能 assert，而且必须点名口径**。实测三档未命中数：**8 → 4 → 2**（口径见 §二末行）。逐条归因（不取单个数，纪律档 §十.3）：`revert`＝A-1 真缺陷（path 级才"消账"，因为它在 a7 的素材里）；`CSV`＝A-3 里程碑级错位；`agent`／`Python`／`People`／`Analytics`＝场景词与 path 标题词（纳入 `_lesson.md` 即命中）；`Milestone`＝跨引词自身；`A-B`＝**词形假阳**（题面与 slug 写的是 `A/B`、`python/15_ab_text`，连字符版永不命中）。⇒ 只报"未命中 8"会把 5 条噪声当真缺陷上交。

**落地案序（交主班/人工，本单不写测试）**：
- 案 **乙**（推荐先做）：把 P2/P4/P5 三条钉进新桩 `tests/test_path_claims.py`——**现值全绿、零待订正**，属"零成本防回归"，且 P5 与 `tests/test_paths_coverage.py`（专题被引覆盖）不重叠（那条管"专题有没有进线"，本条管"进线的专题有没有题"）。
- 案 **甲**（价值最高但要人先清 A-1）：P1/P3 钉成断言前，A-1/A-2 两条必须先由人工定性（改文案 or 补题 or 进白名单）。**在 A-1 未处置前直接钉 P1 会让全量当场 1 红**——这是"先加断言后清账"的反向顺序，不做。
- 案 **丙**（不推荐）：把 41 个里程碑的 82 句文案全部人工改写为"无数字无承诺"式 ⇒ 面太大、且牺牲文案可读性，收益不如哨兵。

## 五、不重复建设声明（在册已覆盖的面，本档不另起一轨）

| 在册件 | 已钉的事 | 与本档关系 |
|---|---|---|
| `tests/test_paths_coverage.py`、`learn-path-coverage-fill-20260920.md` | 磁盘 85 专题全部被 path 引用 | 本档 §二"覆盖 85==85"是对它的**现状复验**，不新钉 |
| `tests/test_paths_prereq.py`、`learn-paths-prereq-20260919.md` | lessons 与 prereqs 引用一致性 | 与 P3（序数跨引）不同轴：那条查 `prereqs` 字段，P3 查**文案里的自然语言序号** |
| `tests/test_paths_order_consistency.py` | 语言页与 path 页两条顺序通道一致 | P3 的红正是"位次被插队改变"，两档互为上下游，落地时**同族同批**跑 |
| `tests/test_readme_reconcile.py`、`test_scripts.py`（`paths == 6`） | README 口径与 paths 计数 | 卷宗"7 文件"若被写单当真，会先把 `paths == 6` 那条改坏 ⇒ 已在 §一-2 钉死为 6 |
| `learn-paths-prereq`／`learn-tail-difficulty-design` | 题数与难度口径 | 本档不动题数口径（纪律档 §五.4：改计数一律停手） |

## 六、本单没做的（如实）

- **没跑全量套件**（并行纪律 §四.2 只读位；主班 §十 现值 `915/7/3 rc=0` 系早前批次，`38ad3bb`→`ed63884` 已多次入库 ⇒ 要全量数请现取）。
- 没改 `content/paths/agent_mastery.yaml:26` 那句失准文案（内容正确性域，GOAL.md 要求关键内容修复先由两个不同模型独立核验 ⇒ 本单只出报告）。
- 没新增 `tests/test_path_claims.py`（卷宗产出面只点名 `docs/insights/*.md`；写测试属后段写单，本档 §四 已给可执行判据）。

## 七、待订正清单（🔴 交主班进台账，本单未改这些档）

1. 派单/卷宗前提「rg 实测 **7 文件**」⇒ 实为 **6 份 path yaml**（`content/paths/*.yaml`）／**8 份**含 `graduation_project` 的文件（加 `core/paths.py`、`ui/pages/path.py`）。台账记两条读数，防止下一次又被抄成 7。
2. 同卷宗「**16+ 处**陈述句」⇒ 无对应口径，实值三个候选：82（两字段行）／129（含标题）／12（值含数字的行）。
3. `content/paths/agent_mastery.yaml:21/:26`（a1）文案「用 git revert 恢复」⇄ `agent_dev/01_git_basics` 5 题零 `revert` 正文（`05_revert.yaml` 实考 `git checkout .`）⇒ 🔴 **内容正确性待人工**，两条出口：改文案 / 补一道 `git revert` 题（补题会牵 `total_problems` 等值断言族，见 `learn-tail-difficulty-design-20260923.md` §四的联动清单 ⇒ 不属本单面）。
4. 在册文档 `docs/insights/learn-paths-order-consistency-20260922.md` 与 `learn-paths-prereq-20260919.md` 都没钉"文案里的自然语言序号 ⇄ 里程碑位次"这层（§五）⇒ 属新增面而非订正，登记供主班决定要不要排写单。

## 八、红线自查

未碰鉴权/凭据/密钥；未改任何统计数值结论（题数、通过率的**在册值**一律只读取证）；未做经济平衡/医疗内容；未写库（本单零 sqlite 连接）；未改 content/ 与生产码 ⇒ **完成标准③**：`git status --porcelain` 只应见 `docs/insights/` 下本批新档与索引件（本单 2 项）。

## 九、复算配方

```bash
cd D:/code/learning-system
# 1 结构与字段计数
ls content/paths/*.yaml | wc -l            # 6
rg -c "(description|graduation_project):" content/paths/*.yaml
# 2 普查主表（里程碑/引用专题双轨题数/命中句）
PYTHONIOENCODING=utf-8 python tmp/l924-19/census_path_claims.py > tmp/l924-19/out.json
# 3 命题实跑（P1 数字/P2 空缺/P3 序数）
PYTHONIOENCODING=utf-8 python tmp/l924-19/propositions.py
# 4 空缺承诺回流检查（期望 rc=1 零命中）
rg -n "待题目新增后解锁|还没有|暂无|待解锁|待补充|尚未" content/paths/; echo rc=$?
# 5 值本体含数字的行（禁把 rg -n 的行号前缀算进去：先剥前缀再测）
python -c "import re,glob,pathlib;F=re.compile(r'^\s*(description|graduation_project):\s*[\"\x27]?(.*?)[\"\x27]?\s*\$');print(sum(1 for f in glob.glob('content/paths/*.yaml') for l in pathlib.Path(f).read_text(encoding='utf-8').splitlines() if (m:=F.match(l)) and re.search(r'\d',m.group(2))))"
# 6 每 path 题数合计
python tmp/l924-19/census_path_claims.py   # 见 out.json 的 paths[].ms[].disk/runtime
# 7 术语锚定（warn-only；三口径同跑，读数即 §二 末行与 §四-3）
PYTHONIOENCODING=utf-8 python - <<'PY'
import re, yaml, pathlib
T = re.compile(r'[A-Za-z][A-Za-z0-9_.-]{1,15}')
def files(topic, scope):                      # 口径 1: 只 *.yaml；口径 2: 加 _lesson.md
    d = pathlib.Path('content').joinpath(*topic.split('/'))
    for p in sorted(d.glob('*.yaml')):
        yield p
    if scope >= 2 and (d / '_lesson.md').is_file():
        yield d / '_lesson.md'
for scope in (1, 2):
    miss, tot = [], 0
    for f in sorted(pathlib.Path('content/paths').glob('*.yaml')):
        for m in yaml.safe_load(f.read_text(encoding='utf-8'))['milestones']:
            body = ' '.join(p.read_text(encoding='utf-8') for t in (m.get('topics') or [])
                            for p in files(t, scope)).lower()
            txt = ' '.join([(m.get('description') or ''), (m.get('graduation_project') or '')])
            for tok in sorted(set(T.findall(txt))):
                tot += 1
                if tok.lower() not in body:
                    miss.append((f.name, m['id'], tok))
    print('口径', scope, '术语', tot, '未命中', len(miss), miss)
# 口径 3：锚点升到"整条 path 的全部专题"
for f in sorted(pathlib.Path('content/paths').glob('*.yaml')):
    ms = yaml.safe_load(f.read_text(encoding='utf-8'))['milestones']
    body = ' '.join(p.read_text(encoding='utf-8') for m in ms for t in (m.get('topics') or [])
                    for p in files(t, 2)).lower()
    txt = ' '.join(' '.join([(m.get('description') or ''), (m.get('graduation_project') or '')]) for m in ms)
    print('path 级', f.name, [t for t in sorted(set(T.findall(txt))) if t.lower() not in body])
PY
# 8 索引闭合（本档同批自登）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q
```

> 探针脚本第 7 条为一次性形态（可读性优先）；落地成测试时应照 §四 的双轨函数取数，不要复用这里的内联推导。
