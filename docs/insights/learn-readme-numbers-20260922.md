# learning README 数字口径复现巡检（l922-108，2026-09-22）

- 任务：`l922-108-readme-numbers`（cwd `D:\code\learning-system`，软预算 ≤20 分钟）
- 性质：**只改 README.md 一行 + 新增本档**；生产码、题库内容、测试实现零改动。
- 复现时点：HEAD `898a4ad`，工作树 clean，2026-09-22 01:2x。数字绑 commit 不绑日期。

## 一、结论：四项相符、一项失真（已订正）

| README 位置 | 声称值 | 磁盘/运行时实测 | 判定 |
|---|---:|---:|---|
| `:52` 语言数 | 5 | 5（`agent_dev` `cpp` `python` `r` `sql`） | **相符** |
| `:52` 题数 | 399 | 399（`content/*/*/*.yaml` 计数；分语言合计亦 399） | **相符** |
| `:52` 知识点 | 85 | 85（含题专题目录 85 ＝ 语言下专题目录 85，零题目录 0） | **相符** |
| `:52` 学习路径 | **3** | **6**（`content/paths/*.yaml` 6 个；`load_all_paths()` 返回 6 条） | **失真 → 已改为 6** |
| `:61` 徽章 | 22 | 22（`grep -c "Achievement("` 与 `len(ACHIEVEMENTS)` 同为 22） | **相符** |
| `:62` 热力图窗口 | 90 天 | 90（`ui/pages/dashboard.py:414` 文案、`:418` SQL `-90 days`） | **相符** |

## 二、逐数字的可复跑命令（先命令后读数）

```
$ ls content/paths/*.yaml | wc -l
6

$ PYTHONIOENCODING=utf-8 python -c "import glob; print(len(glob.glob('content/*/*/*.yaml')))"
399

$ PYTHONIOENCODING=utf-8 python -c "
import glob, os
probs = glob.glob('content/*/*/*.yaml')
print('题数', len(probs), '知识点(含题专题目录)', len({os.path.dirname(p) for p in probs}))
"
题数 399 知识点(含题专题目录) 85

$ grep -c "Achievement(" core/achievements.py
22
$ PYTHONIOENCODING=utf-8 python -c "from core.achievements import ACHIEVEMENTS; print(len(ACHIEVEMENTS))"
22

$ PYTHONIOENCODING=utf-8 python -c "from core.paths import load_all_paths; ps=load_all_paths(); print(len(ps))"
6
```

分语言题数（同一 glob 按目录归并）：`python 121 ＋ agent_dev 78 ＋ r 84 ＋ cpp 62 ＋ sql 54 = 399` ✅
`content/` 一级目录实为 7 个：上述 5 语言 ＋ `paths/`（路径定义）＋ `datasets/`（共享数据资产，**不产生**专题目录也不含 `*/*/*.yaml` 题件，故不影响 85/399 两个计数）。

## 三、路径为什么是 6 而不是 3

```
$ git log -S "3 条学习路径" --oneline --date=format:%Y-%m-%d -- README.md
b14a136 2026-07-14 chore: establish local baseline      # 该行建仓时至今未再动过
$ git ls-tree --name-only b14a136 content/paths/ | wc -l
3                                                       # 当时确实只有 3 条
$ git log --diff-filter=A --name-only --pretty=format:"%h %ad" --date=format:%Y-%m-%d -- content/paths/
b68acaf 2026-09-20   cpp_foundation.yaml / python_advanced.yaml / r_advanced.yaml
b14a136 2026-07-14   agent_mastery.yaml / people_analytics.yaml / quick_stats.yaml
```
即「3 条」在 09-20 之前是**正确口径**，`b68acaf` 一次加 3 条后 README 没跟上，失真起点 2026-09-20。

现 6 条路径（`load_all_paths()` 实况，无过滤全量加载）：

| id | 标题 | 里程碑 | 预估时数 |
|---|---|---:|---:|
| `agent_mastery` | Agent 指挥主线 | 11 | 29 |
| `cpp_foundation` | C++ 从入门到现代 | 5 | 21 |
| `people_analytics` | People Analytics 主线 | 11 | 53 |
| `python_advanced` | Python 进阶级 | 5 | 21 |
| `quick_stats` | 统计速成线 | 5 | 10 |
| `r_advanced` | R 统计进阶线 | 4 | 14.5 |

`core/paths.py:76` 的 `for fname in sorted(os.listdir(_PATHS_DIR)):` **无白名单/无 enabled 开关**（任务书锚点逐字命中，未漂移）——磁盘上有几个 `*.yaml` 前端就有几条路径，README 的「N 条学习路径」等价于 `ls content/paths/*.yaml | wc -l`。

## 四、为什么这个失真没人拦（结构性原因，本单未修）

- 题数 399 有守卫：`tests/test_content_census.py:27` `assert total == 399, "题库总量漂移：…（README 官方口径，变更须有意）"`，`tests/test_content_difficulty_pins.py:80` 亦钉 399。
- 路径数**没有等价的精确守卫**：`tests/test_paths.py:29` 只写 `assert len(paths) >= 3`（松下界）。加到 6 条不触红，README 的「3」因此无人看守。
- 徽章 22 同样无钉：`core/achievements.py` 增删 `Achievement(...)` 不会让 README 侧变红（本单实测数值仍一致，未构成缺陷）。

出口（**交主班裁决，本单按「不做顺手改动」未动**）：把 `tests/test_paths.py:29` 收紧为 `== 6` 并在 README 改动时同步；或反向给 README 数字加一条对账测试（读 README 正则抽数 vs 磁盘计数）。后者与 l922-131（README 目录树巡检）同族，建议并单。

## 五、声明

- 本单零生产码、零测试实现、零题库内容改动；未触碰红线域（判分逻辑、统计结论、经济数值）。
- 改动面：`README.md:52` 一行原地替换，其余 91 行零改动；新增本档。
- 观察但**未改**（不在本单点名范围）：`README.md:87` 目录行写 `content/ python / cpp / r / sql / agent_dev 题库与知识点`，未提 `datasets/`；`:90` 写 `docs/ 系统报告`，而 `docs/insights/` 已有 50+ 篇分析档——属 l922-131 的目录树巡检面。
