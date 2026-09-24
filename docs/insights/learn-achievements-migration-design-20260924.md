# learning achievements 存量逗号格式一次性迁移设计稿（l924-18，只出设计 · 零生产码改动）

> **卷宗**：`zcode-bridge/inbox/l924-18.task.md`（现址 `zcode-bridge/done/`）。上游依据＝`zcode-bridge/done/l923-04.result.md` 遗留问题 1 原话「要不要加一次性迁移（如 `core/migration.py` 启动时归一），属规划决定，未擅自做」——本档做那个"规划决定"的**候选方案与判据**，不替人工做决定。
> **本档性质**：设计稿。未新建 `core/migration.py`、未改 `core/progress.py`、未写生产库；所有盘态实验都在 `tmp/l924-18/` 的**副本**上做（探针 `tmp/l924-18/probe_migration_sandbox.py`，gitignored：`git check-ignore -v tmp/l924-18/probe.py` → `.gitignore:19:/tmp/`）。
> **收口纪律**：§八 的待订正清单**交主班进台账**，本单未改任何他班在册档。

## 一、锚点复核（卷宗每条前提都改成实测，含 2 处否证）

| # | 卷宗前提 | 实测读数 | 现取命令（cwd `D:/code/learning-system`） | 判定 |
|---|---|---|---|---|
| 1 | `core/migration.py` 不存在 | `No such file or directory`；`git log -- core/migration.py` **0 行**（历史上也没存在过） | `ls core/migration.py; git log --oneline -- core/migration.py \| wc -l` | ✅ 成立 |
| 2 | `_get_earned` 在 core 内 4 处读点（卷宗行号 `:60/:156/:162/:172`） | 现读**恰这 4 行**，另有定义与写侧自调共 6 行 | `rg -n "_get_earned" core/achievements.py` | ✅ 成立（但见 §八-3：l923-04 自述行号已漂 −1） |
| 3 | 存量逗号格式还在库里 | `achievements_earned` = `first_solve,multi_lang,no_mistakes,python_first,r_first,solve_10,sql_first`（7 条，`updated_ts` 2026-07-15 03:28:49） | 见 §九配方第 3 条 | ✅ 成立，**迁移对象真实存在** |
| 4 | 🔴 否证：卷宗说「不存在＋四处读点」**漏了现役迁移通道** | `ProgressDAO.__init__` 已调 `self._migrate()`（含 `schema_meta`/`schema_version` 建表逻辑），且已有桩 `tests/test_migration.py`；**"启动归一"在本仓不是新器官，是现役器官** | `rg -n "_migrate\|schema_meta" core/progress.py` ＋ `rg -n "schema_version" tests/test_migration.py` | ⚠ 卷宗只把迁移想象成"新文件"，据此定的产出面偏窄 ⇒ 本案首选挂点改判（§三 案 B） |
| 5 | 🔴 否证：`tests/test_achievements_id_reconcile.py` 注释「本仓 progress.db 实测 journal_mode=delete、无 -wal/-shm 侧车」 | 文件头字节 18/19 = **`2 2`（WAL 持久化）**；同一副本用读写连接查 `PRAGMA journal_mode` → `wal`。`delete` 只是 `mode=ro&immutable=1` 那条**连接**的降级读数，不是盘的事实 | `python -c "import pathlib;print(pathlib.Path('data/progress.db').read_bytes()[18:20])"` | ⚠ 见 §八-4：该注释会诱导后人省掉 `-wal/-shm` 两件 ⇒ 备份口径仍须按三件套 |

其余在册引用面（`_get_earned` 全仓）：`core/achievements.py` 6 行、`tests/test_achievements_branches.py` 29 行、`tests/test_achievements_id_reconcile.py` 8 行 ⇒ **读侧行为全部经 `_get_earned` 单点**，迁移不新增读路径。

## 二、现值（每项绑命令，动手前自己复跑；本机休眠校时与补题都会让它过期）

| 量 | 现值（2026-09-25T00:3x，HEAD `ed63884`） | 现取命令 |
|---|---|---|
| `data/progress.db` sha8 / size / page_count / freelist | `b07f512a` / 114688 B / 28 / 0 | `python -c "import hashlib,pathlib;p=pathlib.Path('data/progress.db');print(hashlib.sha256(p.read_bytes()).hexdigest()[:8],p.stat().st_size)"` |
| `meta` 行数 | **5** | `python -c "import sqlite3;print(sqlite3.connect('file:data/progress.db?mode=ro&immutable=1',uri=True).execute('select count(*) from meta').fetchone())"` |
| `schema_meta` | 1 行 `schema_version='2'`（**仅建表时写一次，`_migrate()` 从不比较它** ⇒ 不是活的版本号） | `rg -n "schema_version" core/progress.py` |
| 成就定义数 `len(ACHIEVEMENTS)` | **22**，id 零逗号、零重复 | `python -c "from core.achievements import ACHIEVEMENTS as A;print(len(A))"` |
| 题库体量 `total_problems` | **403**（python 125／sql 54／cpp 62／r 84／agent_dev 78） | §九配方第 6 条 |
| 松下界护栏 | `tests/test_scripts.py` 内 `assert metrics["total_problems"] >= 399` —— 该桩注释自述「9/5 授权去重时刻意下调的下界护栏」⇒ **实值 403 > 399 属正常，不是待修缺陷**（派单把它说成"会打脸"，此处按卷宗正文与注释自述收窄） | `rg -n "total_problems\] >=" tests/test_scripts.py` |
| `ProgressDAO` 构造点（core/ui/scripts） | **16 处**（ui 页 7、core 5、scripts 4）⇒ 任何"每次构造都跑"的挂点都在 16 条路径上生效 | `rg -n "ProgressDAO\(" core ui scripts \| wc -l` |
| 单次 DAO 构造 / 单次归一判定耗时 | **1.62 ms** / **0.0048 ms**（副本实测，判定成本约为构造的 0.3%） | `python tmp/l924-18/probe_migration_sandbox.py` → `OBS7_cost_ms` |
| 本仓 insights 索引与磁盘 | A=73、B=73、C 空、重复 0；哨兵 3 passed | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q` |
| 生产 .py 扫描面（新建 core 文件会被它扫到） | `core`+`ui` 共 **32** 份（`tests/test_judge_result_per_pid.py` 的 `PROD_SRC`） | `python -c "from pathlib import Path as P;r=P('.');print(len(sorted(list((r/'ui').rglob('*.py'))+list((r/'core').rglob('*.py')))))"` |

## 三、挂点：三案与案序（🔴 选案交人工，本单不代拍）

- **案 B（推荐）：挂进现役 `ProgressDAO._migrate()`**，不新建模块。
  理由：①`_migrate()` 的既有语义就是"存量库形状归一"（现役已在做 `ALTER TABLE ADD COLUMN` 与 `schema_meta` 补建），格式归一与它同族；②零新文件 ⇒ 不动 `PROD_SRC` 扫描面、不动 README 目录树口径；③16 条构造路径全覆盖，含 `scripts/` 三条无 UI 路径；④成本已实测可忽略（0.0048 ms/次）。
  代价：`_migrate()` 从"只改表形状"扩到"改一行数据" ⇒ 它是**唯一会静默写用户数据的构造期代码**，必须由 §五 三条判据钉死，并在 `tests/test_migration.py` 同族补桩（不在本单做）。
- **案 A：新建 `core/migration.py`（卷宗原设想）**，`_migrate()` 末尾 `from core.migration import normalize_achievements_meta; normalize_achievements_meta(self)`。
  与案 B 行为等价，差别只在文件切面：多一个 core 模块、多一处 `PROD_SRC` 扫描件、README/plan 的目录口径要不要跟着提一句需另判。**若人工更看重"数据迁移与建表迁移分家"，选 A；看重"少一个器官"，选 B。**
- **案 C：独立一次性脚本 `scripts/migrate_achievements_meta.py`（dry-run 默认，照 `scripts/backfill_events.py` 的 `--apply` 先例）**，人工执行一次。
  优点：不进入构造期热路径、人可控；缺点：**留脏窗口不受约束**（用户不跑脚本就永远停在旧格式，这正是 l923-04 遗留 1 的原状），且 `scripts/` 新增件要同步 `tests/test_scripts.py` 的扫描面口径。
- 🔴 **三案共同否决项**：不做"扫描全表 / 批量重写多键"的迁移器，不引入 `schema_version` 递增（现值 2 是**出生标记**、代码从不读它，把它升成 3 会让 `tests/test_migration.py::test_schema_version_set` 与 `test_schema_meta_created` 当场红，且属"改计数口径"级动作）。

## 四、迁移判定草案（23 行，≤40 行；与沙盒实跑的代码**逐字同型**）

```python
META_KEY, BACKUP_KEY = "achievements_earned", "achievements_earned_pre_json"

def normalize_achievements_meta(dao, apply=False):
    raw = dao.get_meta(META_KEY, "")
    rep = {"before": raw, "after": raw, "changed": False,
           "empty_dropped": 0, "unknown": [], "skip": None}
    if not isinstance(raw, str) or not raw:
        rep["skip"] = "empty-or-nonstr"
        return rep
    if raw.strip().startswith("["):
        rep["skip"] = "already-json-or-malformed"   # 残缺 JSON 一并留给兼容读，不代改
        return rep
    segs = [s.strip() for s in raw.split(",")]
    ids = sorted({s for s in segs if s})
    rep["empty_dropped"] = len([s for s in segs if not s])
    rep["unknown"] = [i for i in ids if i not in _ACHIEVEMENT_MAP]
    new = json.dumps(ids)                            # 与写侧 _mark_earned 同式，勿加 ensure_ascii
    rep["after"], rep["changed"] = new, new != raw
    if apply and rep["changed"]:
        if dao.get_meta(BACKUP_KEY) is None:
            dao.set_meta(BACKUP_KEY, raw)             # 回滚锚：只写一次，不被后续迁移覆盖
        dao.set_meta(META_KEY, new)
    return rep
```

三条设计约束（都是实测逼出来的，不是审美）：
1. **序列化必须与 `_mark_earned` 同式**。实测：草案输出与 `json.dumps(sorted(_get_earned(dao)))` **字符串逐字相等** ⇒ 迁移后第一次真解锁的 `_mark_earned` 不再改写盘面（否则"幂等"只在自己这套代码内成立，跨写/迁两条路径就假了）。
2. **判据只看值形态、不记"已迁移"标记**。因为 `core/data_portability.py` 的导入路径按 key 整值 `ON CONFLICT DO UPDATE` 覆写 `meta` ⇒ 用户导入一份旧导出件就能把值退回逗号格式；任何"打标记后不再检查"的写法都会被导入路径绕过。值形态判据对回流同样生效（实测见 §五-4）。
3. **不丢信息**：未知 id 原样进数组（在册夹具 `tests/test_core_edges.py` 就写着 `"first_solve,unknown"`，`_LIVE_EARNED_SNAPSHOT` 语义要求未知 id 改名当天即红 ⇒ 迁移无权掩掉它）；空段虽被丢弃，但**原值逐字存在 `BACKUP_KEY`**，可完整回滚。

## 五、幂等判据与回滚法（完成标准①，全部在副本上实跑）

复算：`PYTHONIOENCODING=utf-8 python tmp/l924-18/probe_migration_sandbox.py`（下表读数即其输出标签）。

| # | 判据 | 沙盒实测 | 标签 |
|---|---|---|---|
| 1 | dry-run 零写 | `apply=False` 后 meta 值与 `updated_ts` **逐字不变** | `OBS1_dry_no_write` = true/true/true |
| 2 | 首跑改写 1 行 | 旧串 → 7 元素数组；`empty_dropped=0`、`unknown=[]`；`meta` 行数 **5 → 6**（多的就是回滚锚） | `OBS1_run1` |
| 3 | **二跑零改写（双口径）** | 逻辑口径：`changed=False`、`skip='already-json-or-malformed'`、值与 `updated_ts` **都不动**（ts 不动 ⇒ 连 `UPDATE` 都没发）；文件口径：同一副本 run2 后 **sha8 与 run1 后逐位相同** | `OBS1_run2_idempotent` ＋ `OBS1c_filelevel`（`b07f512a` → dry 不变 → run1 变 → run2 == run1，且无 `-wal/-shm` 残留） |
| 4 | 读侧行为等价（最硬的一条） | 迁移前后 `_get_earned(dao)` **集合逐位相同**；含空段/未知 id 的混排串也相同；回滚后仍相同 | `OBS1_get_earned_equal` / `OBS3` / `OBS6_full_rollback` |
| 5 | 与写侧闭合 | `json.dumps(sorted(_get_earned))` == 迁移落盘值 | `OBS1_mark_earned_roundtrip` |
| 6 | 光构造 DAO 不脏盘 | 副本上 `ProgressDAO(p); close()` 后 sha8/size **不变、无侧车** ⇒ 文件口径可用（案 B 不会自带假红） | `OBS0_dao_init` |

**回滚法（两级，都在副本实测）**：
- 逻辑回滚（首选，两条语句）：
  ```sql
  UPDATE meta SET value=(SELECT value FROM meta WHERE key='achievements_earned_pre_json')
   WHERE key='achievements_earned';
  DELETE FROM meta WHERE key='achievements_earned_pre_json';
  ```
  实测：值逐字 == 原逗号串、备份键消失、`meta` 行数回到 **5**、`_get_earned` 集合不变（`OBS6_full_rollback`）。只跑第一条也能还原值，但会留一行备份键（`OBS4` 实测 rowcount=1、行数仍 6）。
- 物理回滚：`cp -p` 前的**三件套快照**（db＋`-wal`＋`-shm`，本例侧车为空也要按口径走，理由见 §一-5）整件放回。生产库现值 sha8 `b07f512a`/size 114688，写前快照与写后 sha 都记进 result。
- 🔴 不做的事：不删 `attempts`/`learning_events` 任何行、不改 `problems_status`、不跑仓内 backup 脚本（硬编码主库＋会裁剪他人旧备份）。

## 六、与 l923-04 遗留 2（残缺 JSON 杂串分支）的衔接（完成标准②）

遗留 2 原话：`_get_earned` 对「残缺 JSON」退回逗号分支后产出**杂串集合**（`["streak_3"` → `{'["streak_3"'}`）而非报错，属刻意的"不抛异常优先"。迁移与它的三条交界：

1. **草案一律不碰它以 `[` 开头的值**（含合法 JSON 与残缺 JSON），`skip='already-json-or-malformed'`。实测：喂 `["streak_3"` 后盘面逐字不变（`OBS2_draft_skip`）。这是"残缺态"唯一的**可人工修**窗口——`logger.warning` 还在、值仍是人眼可辨的半截串、改一字节即可救。
2. 🔴 **否证一条常见担心**：「迁移会把脏值固化，比现役更早」。实测不成立——现役 `_mark_earned` 走的就是 `_get_earned`，任何一次真解锁都会把杂串写成合法 JSON：沙盒里 `["streak_3"` + 解锁 `streak_7` → 盘上 `["[\"streak_3\"", "streak_7"]`（`OBS2b_mark_earned_freeze`）。⇒ 固化与否**不由本迁移决定**，草案的"不碰"只保证不比现役更激进。
3. **残留风险如实登记，留给裁决**：真库现值不以 `[` 开头 ⇒ 该分支在本机存量库**不触发**；一旦库里出现残缺 JSON，草案与现役行为相同（都不修）。若人工希望"脏值当场暴露"，那属于**改遗留 2 的容错策略本身**（清空＋告警），是另一张单，不在本案面内——本档不放宽任何断言来换数。
4. 案 B 落地时的告警口径：`skip` 分支只 `logger.debug`，**不得在 `_migrate()` 里 raise** ——构造期抛异常会让 16 条路径全崩（现役 `_migrate()` 对 `sqlite3.OperationalError` 都是 `logger.warning` 后继续，同一取向）。

## 七、真做这张单时的在册影响面（本单未做，列给写单与主班）

| 影响 | 现值 | 后果 |
|---|---|---|
| `meta` 行数 5 → 6 | 多一个 `achievements_earned_pre_json` 键 | `docs/insights/learn-progressdb-census-20260918.md` §一快照"meta 5 行"过期（该档另有"首批四成就"描述，见 §八-2）；**无测试钉 meta 行数**（`tests/test_migration.py` 只钉 `schema_version`）⇒ 不会红，属文档面 |
| 导出件多一键 | `core/data_portability.py` 逐表导出 `meta` | 备份键会进 JSON 导出件并被跨机导入 ⇒ 导入了**别人**的旧串。写单须决定是否在导出白名单里排除该键（属"改导出面"，红线相邻 ⇒ 交人工） |
| `tests/test_migration.py` 族 | 现 2 类 / 若干例 | 案 B 须同批补 4 例：dry 零写 / 首跑改 1 行 / 二跑零改写（含 `updated_ts` 不变）/ 残缺 JSON 不动。**定向跑**：`PYTHONIOENCODING=utf-8 python -m pytest tests/test_migration.py tests/test_achievements_branches.py tests/test_achievements_id_reconcile.py tests/test_core_edges.py -q` |
| 案 A 才有的面 | 新建 `core/*.py` 会被 `tests/test_judge_result_per_pid.py` 的 `PROD_SRC`（现 32 份）扫到 | 草案代码不含 `last_judge_result` 字面量 ⇒ 不红，但"新增 core 模块"要不要同步 README 目录树须另判（`learn-readme-tree-20260922.md` 那条线） |
| 全量套件 | **本波未跑**（并行纪律 §四.2：只读位不跑全量）；主班 §十 现值 `915/7/3 rc=0` 系 l924-* 早前批次取，`38ad3bb`→`ed63884` 之间已多次入库 | 引全量数请现取，别抄本档 |

## 八、待订正清单（🔴 交主班进待人工台账，本单未改这些档）

1. `zcode-bridge/done/l923-04.result.md` 的三组行号锚点整体 **−1 漂**：自述 `_mark_earned :246-250`／`_get_earned :224-243`／`_split_legacy :213-221`，现值 `:247-250`／`:223-244`／`:214-220`。复算：`rg -n "^def (_get_earned\|_mark_earned\|_split_legacy)" core/achievements.py`。建议按纪律档 §十.4 改成"只锚唯一文本"。
2. 同档「证据 4」与 `tests/test_achievements_id_reconcile.py:224` 注释把存量串说成"7 条旧逗号格式"——**现值仍成立**（逐字相同，`_LIVE_EARNED_SNAPSHOT` 未过期）；但 `docs/insights/learn-progressdb-census-20260918.md:26` 的「achievements_earned（首批四成就）」**已过期**（现 7 条），且同节「meta | 5」行数是案 B 落地后第一处会漂的数。
3. `tests/test_achievements_branches.py:262` 注释引 `ui/pages/dashboard.py:391` —— 现值 :391 是"跨路径推荐"块，成就读点实际在 `newly = check_achievements(dao)` 一行（现 :452）⇒ **漂 +61 行**（l923-04 结果「证据 3」同错）。复算：`rg -n "check_achievements\(dao\)" ui/pages/dashboard.py`。建议改锚唯一文本。
4. `tests/test_achievements_id_reconcile.py:225` 注释「本仓 progress.db 实测 journal_mode=delete、无 -wal/-shm 侧车」**口径错**：文件头 18/19 = `2 2`（WAL 持久化），`delete` 只是 `mode=ro&immutable=1` 连接的降级读数。危害：后人据此只 `cp -p` 单文件、漏侧车。复算：`python -c "import pathlib;print(pathlib.Path('data/progress.db').read_bytes()[18:20])"`。
5. `docs/insights/learn-insights-index-20260918.md` 的「git 入库」列**整列过期**：表 73 行中标 `未跟踪` 的 **10 行**（l924-17 记的是 9 行，之后又多 1 行登记）经 `git ls-files docs/insights` 复验**全部已入库**（tracked 恰 73 == 表行数）⇒ 该列 73/73 应为「已入库」。复算：`git ls-files docs/insights \| wc -l` 对比 `rg -c "^\| docs/insights/.* \| 未跟踪 \|" docs/insights/learn-insights-index-20260918.md`。（哨兵不读此列 ⇒ 不拦，纯人读准确性；本单只登自己 4 行新档，未回改历史行。）
6. 派单口径「`total_problems >= 399`（实值 403）会打脸」——**收窄**：该下界是 `tests/test_scripts.py` 注释自述的**刻意护栏**（9/5 授权去重时下调），同桩 `paths` 已由 l924-14 钉成 `== 6`。⇒ 属"知情项"而非缺陷，不要顺手收紧成 `>= 403`（改计数口径一律停手，纪律档 §五.4）。

## 九、复算配方（本档读数的取数链，逐条可跑）

```bash
cd D:/code/learning-system
# 1 前提：migration 模块与现役迁移通道
ls core/migration.py; rg -n "_migrate|schema_meta|schema_version" core/progress.py
# 2 读点与序列化同式
rg -n "_get_earned|json.dumps" core/achievements.py
# 3 存量值（只读，跑完复验无侧车）
PYTHONIOENCODING=utf-8 python -c "import sqlite3,glob;con=sqlite3.connect('file:data/progress.db?mode=ro&immutable=1',uri=True);print(con.execute(\"select key,value,updated_ts from meta\").fetchall());con.close();print(glob.glob('data/progress.db*'))"
# 4 盘态
PYTHONIOENCODING=utf-8 python -c "import hashlib,pathlib;print(pathlib.Path('data/progress.db').read_bytes()[18:20],hashlib.sha256(pathlib.Path('data/progress.db').read_bytes()).hexdigest()[:8],pathlib.Path('data/progress.db').stat().st_size)"
# 5 挂点成本与幂等（全部只碰 tmp/l924-18/ 副本）
PYTHONIOENCODING=utf-8 python tmp/l924-18/probe_migration_sandbox.py
# 6 题库体量与成就定义数
PYTHONIOENCODING=utf-8 python -c "from core.loader import load_language;from ui.components import ALL_LANGS;print(sum(sum(len(t.problems) for t in load_language(l)) for l in ALL_LANGS))"
PYTHONIOENCODING=utf-8 python -c "from core.achievements import ACHIEVEMENTS as A;print(len(A))"
# 7 索引闭合（本档同批自登，改完必绿）
PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q
```

> 本单**零生产码改动**：`git status --porcelain` 只应见 `docs/insights/` 下的新增档与索引件改动；`data/progress.db` 前后 sha8 逐位不变（`OBS5_prod` 实测 `b07f512a`→`b07f512a`、size 114688、5 行 meta、无侧车）。
