# meta 逗号串存量迁移「一次性 vs 惰性维持」两案裁决材料（l927-34，只出材料 · 零写库 · 零 git 操作）

> **卷宗**：`zcode-bridge/inbox/l927-34.task.md`。上游依据＝`zcode-bridge/done/l923-04.result.md` 遗留问题 1（「写侧不做批量迁移……要不要加一次性迁移（如 `core/migration.py` 启动时归一），属规划决定，未擅自做」）。
> **前案在册**：l924-18 已出过一份**一次性迁移的完整设计稿**（`docs/insights/learn-achievements-migration-design-20260924.md`，含案 A/B/C 挂点、23 行迁移判定草案、幂等判据、两级回滚、影响面清单）。本档不重复其设计细节，只做它欠的那一步：**「一次性迁移」vs「惰性维持」两案对照＋推荐**。判定仍归人工——**本班不下通过判定**。
> **本班性质**：只读位裁决材料班（shift `qoder-executor-20260929-0307-learn60`，2026-09-29 03:1x 全部读数现取）。

## 一、锚点与前提复核（每条都改成命令实测）

| # | 前提 | 现取读数 | 取数命令（cwd `D:/code/learning-system`） | 判定 |
|---|---|---|---|---|
| 1 | 锚点句仍在（l923-04 遗留 1 原话） | `zcode-bridge/done/l923-04.result.md`「遗留问题」第 1 条逐字含「要不要加一次性迁移」 | `head -40 zcode-bridge/done/l923-04.result.md` | ✅ 有效 |
| 2 | 读侧兼容现役 | `_get_earned`（`core/achievements.py:223`）非 `[` 开头走 `_split_legacy`（:214）过滤空段；`_mark_earned`（:247-250）写 `json.dumps(sorted(...))` | `sed -n '205,260p' core/achievements.py` | ✅ 与 l923-04 后一致，未漂移 |
| 3 | **一次性迁移至今未实装** | `core/migration.py` 不存在；`_migrate()`（`core/progress.py:149-166`）只做表形状归一（ALTER＋`schema_meta` 补建），**从不碰 `achievements_earned` 值**；`git log --since=2026-09-24 -- core/progress.py` 无迁移实装入库 | `ls core/migration.py; sed -n '149,166p' core/progress.py` | ✅ 现状＝纯惰性 |
| 4 | 🔴 存量旧串**至今仍在库里，且比 l924-18 时点更"实锤"** | `achievements_earned` = `first_solve,multi_lang,no_mistakes,python_first,r_first,solve_10,sql_first`，`updated_ts` **2026-07-15 03:28:49 未动**；而库文件本体 mtime 2026-09-25 20:49（sha8 `cd2dbce4`/122880）——**期间库其他表有写、唯独这行 meta 没被惰性升级触发**（= 6 周+零新解锁，l923-04 遗留 1 设想的场景已在本机真实发生） | `PYTHONIOENCODING=utf-8 python -c "import sqlite3;con=sqlite3.connect('file:data/progress.db?mode=ro&immutable=1',uri=True);print(con.execute(\"select key,value,updated_ts from meta where key like 'achievements%'\").fetchall());con.close()"` | ✅ 迁移对象真实存在；⚠ 与 l924-18 §二 的 sha8 `b07f512a`/114688 已不同（09-25 20:49 他人写过库，非本班所为，本班只读） |
| 5 | 读侧功能无差异（兼容真的兜住） | 定向四件 **72 passed / 0 failed，1.57s**：`tests/test_achievements_branches.py`（新旧格式/空段/幂等/脏输入 12 例族）＋ `test_achievements_id_reconcile.py`（含 :204 旧串 roundtrip 例、:230 `_LIVE_EARNED_SNAPSHOT` 快照例）＋ `test_migration.py` ＋ `test_core_edges.py`（:29 旧格式夹具） | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_achievements_branches.py tests/test_achievements_id_reconcile.py tests/test_migration.py tests/test_core_edges.py -q` | ✅「读侧兼容已验证」前提成立 |
| 6 | 渲染期消费方仍单点 | `ui/pages/dashboard.py:495` `newly = check_achievements(dao)` 全经 `_get_earned`；全仓 `ProgressDAO(` 命中 **17 行**，其中 `core/progress.py:31` 是 docstring 提及（非构造点）⇒ 真实构造点 **16 处**（core 5／ui 7／scripts 4），与 l924-18 §二 读数**一致未漂** | `git grep -n "ProgressDAO(" -- core ui scripts`（复算时注意减掉 :31 注释行） | ✅ 单点消费成立 |
| 7 | 本班零副作用 | 跑完所有只读取证后 `git status --porcelain` 行数 **0**（写产出档前）；`data/progress.db` 三件 mtime 均早于本班开工时刻（03:07 之后无任何 mtime 变化） | `git status --porcelain | wc -l; ls -l --time-style=full-iso data/progress.db*` | ✅ 零写库坐实 |

## 二、两案矩阵（完成标准①）

| 维度 | 案一：一次性迁移（l924-18 设计稿落地，案 A/B/C 三选一） | 案二：惰性维持现状（不做任何事） |
|---|---|---|
| 收益 | ①旧格式消亡，兼容分支可择期退役（`_split_legacy`＋`_get_earned` 分流段是双格式永续税）；②盘上值与写侧格式一致，人读库/导出件不再见两种格式；③消灭「残缺 JSON 退回逗号分支产杂串」的暴露窗口前移（l924-18 §六：真库现值不以 `[` 开头，该分支现不触发） | ①零改动、零风险、零新测桩；②l923-04/l924-18 兼容面已实测兜住（本档 §一-5：72 passed）；③任何一次新解锁自动升级该用户，**代码语义上不依赖存量** |
| 成本/风险 | ①案 B＝构造期静默写用户数据，在 **16 处构造点**（core 5／ui 7／scripts 4）全路径生效（l924-18 明说它是"唯一会静默写数据的构造期代码"，须 dry 零写/首跑改 1 行/二跑零改/残缺不动 4 例新桩钉死）；②回滚锚键 `achievements_earned_pre_json` 使 meta 5→6 行，且会**进 `core/data_portability.py` 导出件被跨机导入**（改导出白名单＝红线相邻，l924-18 已声明须交人工）；③案 A 另加一个 core 模块、动 `PROD_SRC` 32 份扫描面与 README 目录口径；④案 C 留脏窗口不受约束（等于变相案二＋一个没人保证会跑的脚本） | ①兼容分支成为长期现役代码（但已被 12＋2 例在册桩钉住，非无主死码）；②存量用户若永不解锁，其 meta 永远旧格式——**功能面已验证无差异**，只有"人读库观感"与"双格式认知成本" |
| 实际痛面（现值） | 🔴 **零**：本档 §一-4——本机 6 周+零解锁、旧串躺平，期间 dashboard 反复渲染、`test_core_edges.py` 旧格式夹具、reconcile 快照例全部照常绿；没有出现任何因旧格式导致的红、告警或用户侧损失记录 | 同左：痛面缺失是本案最强事实 |
| 可逆性 | 逻辑回滚两条 SQL（l924-18 §五 实测）＋物理三件套快照；可做但多一道运维面 | 天然可逆（什么都没改） |
| 与红线关系 | 触及生产库写、导出件（数据可携带）面——**本班只出材料，不代拍** | 无 |

## 三、推荐（完成标准②）

**推荐：维持惰性（案二），暂不实装一次性迁移。** 理由按权重：

1. **痛面为零实测**（§一-4/5）：裁决问题「若无实际痛面则推荐维持惰性」的答案是"确无"。l923-04 遗留 1 设想的"长期不再解锁 ⇒ 停在旧格式"已在本机真实发生 6 周+，读侧照常——兼容不是纸面承诺，是 72 passed 的现役事实。
2. **一次性迁移的收益全属"洁癖/收敛"类**（格式统一、兼容分支退役），没有一条是功能正确性或判分口径收益；而成本是构造期静默写数据＋导出件跨机污染面＋4 例新桩——典型的收益/风险倒挂。
3. **前案质量已把路铺好**：真出现痛面（例如有外部工具直读 meta 值、或跨仓消费逗号串）时，l924-18 的案 B 草案可直接启用，无需重设计。本档与之不冲突，只是判"现在不做"。
4. 唯一建议的**非迁移**收尾项（交人工，可与本裁决同批拍）：`docs/insights/learn-progressdb-census-20260918.md:26`「首批四成就」与 meta 行数口径已过期（l924-18 §八-2 已登记），属文档面订正，不需要写库。

**判据（何时应改判"做一次性迁移"）**——出现任一改推荐方向：① 出现直接 SQL 消费 `meta['achievements_earned']` 且假定 JSON 形态的外部件/报表；② 跨机导入路径上旧串造成实际数据错乱；③ `_split_legacy` 兼容族测试被要求退役（退役前必须先迁移）。

## 四、待人工清单（判定留人工，本班不下通过判定）

1. 两案拍板（推荐惰性）；若否，另挂案 A/B/C 选择（l924-18 §三）。
2. 导出件 `achievements_earned_pre_json` 白名单问题（仅案一落地时相关）。
3. 本班产出件 `docs/insights/l927-34-metamigrate.md` **未自登索引**（纪律：索引件主班单点写）⇒ 落盘后 `tests/test_insights_index_closure.py`（开工基线实测 3 passed）预期转红，须由主班登索引后与产出件**同笔入库**。

## 五、复算配方（本档读数取数链）

```bash
cd D:/code/learning-system
# 1 读写侧现状
sed -n '205,260p' core/achievements.py
# 2 现役 _migrate 不碰 meta
sed -n '149,166p' core/progress.py
# 3 存量值＋updated_ts 未动（只读，immutable）
PYTHONIOENCODING=utf-8 python -c "import sqlite3;con=sqlite3.connect('file:data/progress.db?mode=ro&immutable=1',uri=True);print(con.execute(\"select key,value,updated_ts from meta where key like 'achievements%'\").fetchall());con.close()"
# 4 定向四件
PYTHONIOENCODING=utf-8 python -m pytest tests/test_achievements_branches.py tests/test_achievements_id_reconcile.py tests/test_migration.py tests/test_core_edges.py -q
# 5 消费面
git grep -n "ProgressDAO(" -- core ui scripts
git grep -n "check_achievements(dao)" -- ui/pages/dashboard.py
```
