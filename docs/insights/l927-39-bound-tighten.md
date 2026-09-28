# paths 松下界收紧单·现值实测：l927-39，2026-09-28

> 执行：波次 43 代码写位子班 `qoder-executor-20260928-0300-learn54`，cwd `D:\code\learning-system`。
> 盘态：开班现取 HEAD `22a5325`、`git status --porcelain` 0 行（本单收笔时工作树只多了本档一枚未登记件）。
> 卷宗：`zcode-bridge/inbox/l927-39.task.md`（做什么＝"把两处松下界收紧到现值…现值先实测"）。
> 🔴 结论先说：**卷宗点名的两处都已经在盘上收口了**（分别由 l923-12、l924-14 完成），
> 本单**没有产生任何 diff**——收紧动作无对象可做。按 w40 §0／w41「以磁盘现值为准」如实登记，
> 不为了凑判据①去动没被点名的断言（w42 §B.1 禁"顺手一致"）。

---

## 一、现值实测（收紧动作的前提，全部本班真跑）

```
$ ls content/paths/*.yaml | wc -l
6                                                  # agent_mastery / cpp_foundation / people_analytics
                                                   # / python_advanced / quick_stats / r_advanced
$ PYTHONIOENCODING=utf-8 python -c "from core.paths import load_all_paths; print(len(load_all_paths()))"
6
$ PYTHONIOENCODING=utf-8 python -c "generate_metrics() 逐键打印"
paths= 6  total_problems= 403  total_topics= 85  lessons= 85  tests= 1059
$ grep -n "条学习路径" README.md
52:- 5 种语言并行学，进度独立；403 题、85 知识点、6 条学习路径（…对账见 docs/insights/learn-readme-numbers-20260922.md…）
```

## 二、点名两处的磁盘实况：均已收紧，且比"防回归档"更严（等值）

| 卷宗锚点 | 当时说法 | 磁盘现值（本单实取） | 谁收的口 |
|---|---|---|---|
| `tests/test_paths.py:29` | `assert len(paths) >= 3` 松下界＝README 失真的看守缺口（l922-108 遗留 1） | **`:35` `assert len(paths) == 6` ＋ 带漂移名的失败消息 ＋ 6 行来源注释** | l923-12，commit `1bafa0c`（`git log -S "len(paths) == 6"` 唯一命中） |
| `tests/test_scripts.py:312` | `assert metrics[paths] >= 3` 未收口（l923-12 遗留，同族松下界） | **`:319` `assert metrics["paths"] == 6` ＋ `:312-318` 五行为什么这里钉等值、上面两行留下界的说明** | l924-14，commit `e68ad12`（`git log -S 'metrics["paths"] == 6'` 唯一命中） |

两处行号都**已漂移**（锚点写 :29／:312，现值 :35／:319），漂移原因就是收口时插了注释块。
按 w40 §3「锚点路径查无此件是路径搬家不是缺陷」的同一口径：**判据①「两处收紧 diff」在盘上已闭合，
本单零改动**，不是失败、也不是没做——是对象已不存在。

同族另外两枚（在册，非本单点名）：
- `tests/test_paths_order_consistency.py:68` `assert len(paths) == 6`
- `tests/test_readme_reconcile.py`：README 抽数 ⇄ `load_all_paths()` ⇄ `content/paths/*.yaml` **三方对账**，
  还自带两枚变异自证（改一位 README 数字必红、删掉承载数字的行必红）
  ⇒ l922-108 当年给的"出口二"（加对账测试）也已落地，看守缺口双向都补上了。

## 三、定向读数（判据②，全部 rc=0）

```
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_paths.py tests/test_scripts.py \
    tests/test_readme_reconcile.py tests/test_paths_order_consistency.py \
    tests/test_paths_coverage.py tests/test_paths_reconcile.py \
    tests/test_readme_version_gate.py tests/test_content_census.py -q
52 passed, 2 xfailed in 3.60s                      rc=0
```
两枚 xfail **都是在册既有**、与本单无因果（本单零代码改动）：
`test_paths_order_consistency.py::test_路径内milestone顺序与语言页顺序一致`
（2 处 yaml 顺序 vs loader 字典序真倒置，规划域，档 `learn-paths-order-consistency-20260922.md`）；
`test_readme_version_gate.py::test_真README必须过check_readme`（README 标题版本不含 0.6.5，
l923-25 遗留的 HEAD 长期红）。

## 四、同族**残留**宽界清单＋可批形状（本单没动，交主班裁）

`tests/test_scripts.py::test_system_metrics_cover_repository_shape` 里除 paths 外还有五格松界：

| 现值断言（file:line） | 磁盘实取 | 收紧代价／连坐面 |
|---|---|---|
| `:310 total_problems >= 399` | 403 | 等值钉会**与 `tests/test_content_census.py:27 == 403` 重复**⇒ 每次补题要同批改两枚件（本仓现状：补题单 1 处 → 2 处）；`>=399` 是 2026-09-05 授权去重时刻意下调的护栏（注释在 `:308-309`） |
| `:311 total_topics > 50` | 85 | 全仓**零**等值钉（grep `== 85` 只命中分值断言，不相关）⇒ 这条是真缺口，但收它要顺手决定"知识点口径含不含 `datasets/`"（l922-108 证据节已辨过一次） |
| `:322 lessons > 50` | 85 | 同上，零等值钉；`lessons` 与 `total_topics` 现值相同（85），口径是否同物需先确认再钉 |
| `:323 tests >= 1` | 1059 | **建议不收紧**：这是每开一单都会 +1 的量，钉等值＝天天误红，正是 l924-14 注释里写明的取舍 |
| `:324 lines.core > 0` | >0 | 同上 |

⚠ **与既有在册说法的冲突（点名，不静默覆盖）**：l924-14 在 `:312-318` 写下的口径是
「题库体量类留下界、只有仓库形态类（paths）钉等值」，而本单派单给的档位是「`len==现值` 或
`>=现值-1` 的防回归档」——两者对 `:310/:311/:322` 这三格**方向不一致**。按 w40 §9（卷宗优先）本该收，
按盘上在册理由则不该收；本单两处点名对象已闭合、无需裁决即可交回，剩下的格**留给主班定口径**，
不在执行班授权内自行取舍。

若要收（可批形状，最小改动面）：`:311`／`:322` 改 `== 85`、`:310` 改 `== 403` 并同步
`test_content_census.py:27` 与 `README.md:52` 三处（三者现值已一致），回滚成本＝单行 revert；
`:323`／`:324` 保持下界。

**连坐面＝实测不是预估**（探针 `D:\code\tmp\qoder-executor-20260928-0300-learn54\probe_l927_39.py`：
按原始字节把 `test_scripts.py` 的单行改成等值 → 跑四件定向 → `finally` 逐字节还原，
`还原校验 byte-identical: True`，跑完 `git diff --numstat -- tests/test_scripts.py` 空）：

| 探针 | 命令口径 | 读数 |
|---|---|---|
| 基线（工作树现状） | `pytest tests/test_scripts.py tests/test_content_census.py tests/test_readme_reconcile.py tests/test_paths.py -q` | `rc=0 / 37 passed` |
| P1 `total_problems >= 399` → `== 403` | 同上 | `rc=0 / 37 passed`（连坐 0） |
| P2 `total_topics > 50` → `== 85` | 同上 | `rc=0 / 37 passed`（连坐 0） |
| P3 `lessons > 50` → `== 85` | 同上 | `rc=0 / 37 passed`（连坐 0） |
| P4 `tests >= 1` → `== 1059` | 同上 | `rc=0 / 37 passed`（连坐 0，但**下一单加任何测试就会红**，属"天天误红"那一案） |

⇒ 「收紧后若别的用例依赖宽值会连坐变红」这条在册坑，**在本仓这四件里没有命中**：没有任何用例
依赖这几格的宽值（宽值只被 `generate_metrics` 的现值满足）。真正的代价不在连坐、在**未来每次补题/加测试
都要同步改钉**，其中 `:310` 还会与 `test_content_census.py:27` 形成双份等值钉。

## 五、复算命令

```
cd D:\code\learning-system
PYTHONIOENCODING=utf-8 python -m pytest tests/test_paths.py tests/test_scripts.py \
  tests/test_readme_reconcile.py tests/test_paths_order_consistency.py \
  tests/test_paths_coverage.py tests/test_paths_reconcile.py \
  tests/test_readme_version_gate.py tests/test_content_census.py -q     # → 52 passed, 2 xfailed
PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q   # → 预期红（本档未登记）
git log --oneline -S "len(paths) == 6" -- tests/test_paths.py           # → 1bafa0c（l923-12）
git log --oneline -S 'metrics["paths"] == 6' -- tests/test_scripts.py   # → e68ad12（l924-14）
```
零写库：本单所有读数走 `core.paths` / `generate_metrics` 的只读磁盘计数与 `:memory:`／桩，
`data/progress.db` 未连接。
