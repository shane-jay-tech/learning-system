# record_attempt 原子包裁决材料（2026-10-08，l1007-08 遗留 1）

> 零改码。矿源 l1007-08：「若主班要求『attempt+SRS 原子包』＝把 update_review_state 并入 record_attempt_and_status 同一 with 块——属行为变更（拆函数语义），由本审计供据另裁；现状自愈路径足以兜底。」

## 一、两函数现值与自愈路径

| 函数 | 位置 | 事务形态 | 写面 |
|---|---|---|---|
| `record_attempt_and_status` | progress.py:187-206 | `with self.conn:` 单事务——attempts INSERT ＋ problems_status INSERT OR REPLACE（**attempt+状态已原子**） | 2 表 |
| `update_review_state` | progress.py:403-445 | 独立 `with self.conn:`（读旧值→夹钳→UPSERT review_state） | 1 表 |
| **调用点** | judge.py:223-224 与 :433-434（两处生产调用，序贯） | **两事务分离**——attempt+status 原子包成功后，update_review_state 才跑 | — |

**「自愈路径」核（矿源「足以兜底」判定复核）**：
1. update_review_state 的行缺失分支（:411-413 `else: interval=3, ease=2.0, streak=0`）＝**幂等自建**——review_state 行缺失时按初值 UPSERT，不依赖先前状态；
2. 两调用点序贯于同一 `try:`（judge.py:220-238/:431-438）——update_review_state 失败被 `except Exception: logger.warning` 吞（不中断主流程），**attempt 已落库为既成事实**；
3. review_state 语义＝「下次复习排期」，缺失行的代价＝该题不进间隔复习队列（下次 update_review_state 任一触发点〔同题再提交〕重建）——**非账本丢失，是排期缺失且可自建**。

## 二、原子包改法（with 合并）影响面

**改法**：`record_attempt_and_status` 增可选参 `update_review: bool = False, difficulty: int = 3`——同一 `with self.conn:` 块内追写 review_state UPSERT（逻辑从 update_review_state 平移）；两调用点改单调用。

| 影响面 | 内容 |
|---|---|
| 行为变更 | 函数签名扩展（默认 False 向后兼容）；「拆函数语义」改变＝单函数两表三写 |
| 事务收益 | attempt 与 review_state 同生共死——消除「attempt 落、review_state 失败（如 disk IO 抖动）」的排期缺失窗 |
| 回归面 | 既有 tests（progress/judge 系）对 record_attempt_and_status 的 stub/断言需随签名审（默认参数向后兼容 ⇒ 影响小）；update_review_state 单测保留（独立调用面仍存在） |
| 风险 | with 嵌套语义（平移代码内含自身 with ⇒ 需拆出「纯 UPSERT 体」函数供两处复用，否则嵌套 with 无害但冗余） |

## 三、翻面用例清单（若裁实施）

1. 正向：record_attempt_and_status(update_review=True) 单调用后 attempts/review_state 两表齐写（现有断言扩展）；
2. review_state 写失败 ⇒ 整包回滚（attempts 也无行——与现状「attempt 已落、review_state 缺」的行为差即本包价值）；
3. update_review=False 默认路径与现状逐位等价（向后兼容钉）；
4. update_review_state 独立调用面回归（仍可用）。

## 四、裁决表

| 选项 | 建议 | 理由 |
|---|---|---|
| 维持现状（两事务＋自愈） | **可维持** | 自愈三重（行缺失自建/异常吞/同题再提交重建）；排期缺失窗代价低；零回归 |
| 原子包（案Ⅱ） | 可选低风险改 | 默认参数向后兼容、回归面小；**收益=消除低概率排期缺失窗**——若主班判「SRS 排期可靠性与 attempt 同级」则值得 |
| 全并（含 emit_event） | 不荐 | emit_event 有去重语义（dedup_code_hash），并入事务改变事件语义面 |

## rg 复现

$ sed -n '187,206p' core/progress.py → 单事务原文
$ sed -n '403,445p' 同文件 → update_review_state（含 :411-413 自建分支）
$ sed -n '223,224p;433,434p' core/judge.py → 两调用点序贯原文
$ sed -n '238,239p' core/judge.py → except 吞异常（自愈第三重）


## 五、行号锚复点（l1007-24，2026-10-08 收编后）

**收编态**：judge.py/progress.py porcelain 净（l1007-21 judge.py 注释与本班面均已入库；k1007-145 批 3 收 workspace/progress 面在途）。l1007-08 原审计三锚**全部漂移**，现值重锚：

| 原锚（l1007-08 时点） | 现值锚 | 锚文本 |
|---|---|---|
| judge.py:217 | **judge.py:222** | `attempt_id = d.record_attempt_and_status(lang, pid, code, passed, feedback)` |
| judge.py:417 | **judge.py:431** | `attempt_id = d.record_attempt_and_status(lang, pid, answer, res["passed"], res["feedback"])` |
| judge.py:419 | **judge.py:434** | `d.update_review_state(lang, pid, res["passed"], difficulty)` |

漂移源＝l1007-21（:144 前插 *Error* 优先查 +7 行）等后续改动推移行号。本档 §一/§二 原引用「:223-224/:433-434」即现值近邻（record 行 :222/:431 未单列），语义不受影响；后续引用一律以本节现值锚为准。
