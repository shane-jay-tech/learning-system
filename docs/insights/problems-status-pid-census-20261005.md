# problems_status pid 形态全量普查报告（l1002-82，只读 immutable）

- 时点：2026-10-05（exec-shift-20261003-manual）；读法 `sqlite3.connect('file:data/progress.db?mode=ro&immutable=1', uri=True)`

## 一、三桶计数与对账（完成标准①）

| 桶 | problems_status | attempts 唯一 pid |
|---|---|---|
| 三段式（`<lang>/<slug>/<stem>`） | **14** | 14 |
| AI_VARIANT:: 变式 | 0 | 0 |
| 其它 | 0 | 0 |
| **合计** | **14**（对账 ✓） | 14 |

矿源「DB 侧历史行未穷举」的悬置**闭合**：全量穷举后**零非三段式行**——l923-19 探针「真实题库 0 例」的结论从抽样升级为全量。

## 二、「其它」桶逐行（完成标准②）

**空**——无来源猜测需求。两表 pid 形态 100% 三段式，与 core/loader `_build_problem` 单源一致。

## 三、mistakes 退化路径关联（完成标准③）

`ui/pages/mistakes.py _problem_yaml_stamp`（原 _problem_yaml_mtime）的退化分支（`len(parts) != 3 or parts[0] != lang` ⇒ None）在现库**触发面为 0**——正常路径全部走正常缓存键；该退化分支仅对「历史脏数据/别的写入口」防御性存在，现库无需触发。

## 四、零写入声明

全程 immutable 只读；未做任何清洗（数据面人工闸后）。
