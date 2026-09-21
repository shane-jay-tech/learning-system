# learning 对外基线口径刷新（l922-107，2026-09-22）

- 任务：`l922-107-plan-baseline-refresh`（cwd `D:\code\learning-system`，软预算 ≤20 分钟）
- 性质：**只改 plan.md 一行 + 新增本档**；源码、测试实现、既有基线档 `learn-test-baseline-20260921.md` 零改动。
- 动因：`plan.md:33` 是对外口径面，却仍停在 09-18 的 **384 passed**；仓内已有两档更新的实测（09-21 的 566、09-22 的 597）都没回写 plan.md，形成「基线档往前跑、对外口径留在原地」的漂移。

## 一、实跑（先命令后数字）

```
$ PYTHONIOENCODING=utf-8 python -m pytest tests -q
622 passed, 7 skipped in 50.68s                              rc=0
$ PYTHONIOENCODING=utf-8 python -m pytest tests --collect-only -q
629 tests collected in 1.19s                                 # 622 + 7 = 629 自洽 ✅
```

取数快照（基线绑 commit 不绑日期，同一小时内本仓已被走过 597→605→610→614→617→622）：

| 项 | 值 |
|---|---|
| HEAD（跑前 / 跑后） | `a0ee9b9` / `a0ee9b9`（全程未变） |
| `git status --porcelain`（跑前 / 跑后） | 空 / 空（无并行班插提交） |
| 全量跑窗口 | 2026-09-22 01:23:03 → 01:23:55 |
| 采集跑窗口 | 2026-09-22 01:23:55 → 01:23:57 |
| 采集文件数 | 71（`--collect-only -q` 按 `::` 前缀去重） |

## 二、与 566 的差值：+56 逐文件归因

口径：`git log --format=%h %s 0564042..HEAD -- tests/`（0564042 即 l922-03 落 566 的那个提交）＋逐提交 `git diff --unified=0 <h>^ <h> -- tests/` 净增 `def test_`；每文件「现采集」取本单 `--collect-only -q` 实况。

| commit | 单 | 净增 | 落点文件 |
|---|---|---:|---|
| `7451474` | l922-04 | +1 | `test_content_crlf.py`（新） |
| `304ddc7` | l922-05 | +1 | `test_topic_dualnum_pins.py`（新） |
| `5e266ae` | l922-06 | +5 | `test_content_difficulty_pins.py`（新） |
| `5b6bd03` | l922-08 | +9 | `test_recommend_review_state.py`（存量内部） |
| `fee9dc6` | l922-09 | +4 | `test_achievements_branches.py`（存量内部） |
| `1632f91` | l922-10 | +11 | `test_ai_review_strategy.py`（存量内部） |
| `298a38c` | l922-101 | +8 | `test_dashboard_event_failures.py`（新） |
| `8e87e67` | l922-102 | +2 | `test_dashboard_event_failures.py`（同文件追加） |
| `f6c3160` | l922-103 | +3 | `test_dashboard_event_failures.py`（同文件追加） |
| `19f8e9c` | l922-104 | +4 | `test_export_cache_invalidation.py`（新） |
| `6abc4c6` | l922-105 | +3 | `test_dashboard_import_feedback.py`（新） |
| `a0ee9b9` | l922-106 | +5 | `test_report_markdown_contract.py`（同文件追加） |
| **合计** | 12 提交 | **+56** | 566 + 56 = **622** ✅ |

**两种来源别混计**（`--diff-filter=A` 只给得出前者，照它归因会漏掉一半）：

- 新增文件贡献 **27**：`test_dashboard_event_failures`(13) ＋ `test_content_difficulty_pins`(5) ＋ `test_export_cache_invalidation`(4) ＋ `test_dashboard_import_feedback`(3) ＋ `test_content_crlf`(1) ＋ `test_topic_dualnum_pins`(1)。
- 存量文件内部增长贡献 **29**：`test_ai_review_strategy`(11) ＋ `test_recommend_review_state`(9) ＋ `test_report_markdown_contract`(5) ＋ `test_achievements_branches`(4)。
- 逐文件净增与本单采集数**逐行相等**（如 event_failures 净增 13 = 现采集 13），说明这 56 例里**没有 parametrize 展开**，`def test_` 口径与采集口径在本区间可互换；将来若出现展开，本表口径须改用逐文件 `--collect-only -q` 差值。

采集侧同界：573（566 档）+ 56 = **629** ✅；skip 恒 7，故 passed 侧与采集侧同增。

## 三、597 → 622（本浪 25 例，给只读旧档的班用）

`a54f958`（n922-10 记 597）到 `a0ee9b9` 共 6 个提交：l922-101 +8、l922-102 +2、l922-103 +3、l922-104 +4、l922-105 +3、l922-106 +5 = **+25**，597 + 25 = 622 ✅。
注意 l922-101/102/103 **三单写进了同一个** `tests/test_dashboard_event_failures.py`（同文件追加），所以「新增文件数」远小于「新增用例数」——按 `--diff-filter=A` 数文件会把这 13 例算成 1 个新件的贡献。

## 四、7 条 skip 归属复核（与基线档 §一/§六 逐行相同）

```
$ PYTHONIOENCODING=utf-8 python -m pytest tests/test_cpp_runner.py tests/test_r_runner.py -q -rs
SKIPPED [1] tests\test_cpp_runner.py:16: g++ not available; skipping C++ runner tests
SKIPPED [1] tests\test_cpp_runner.py:27: g++ not available; skipping C++ runner tests
SKIPPED [1] tests\test_cpp_runner.py:34: g++ not available; skipping C++ runner tests
SKIPPED [1] tests\test_cpp_runner.py:44: g++ not available; skipping C++ runner tests
SKIPPED [1] tests\test_r_runner.py:13: Rscript not available; skipping R runner tests
SKIPPED [1] tests\test_r_runner.py:19: Rscript not available; skipping R runner tests
SKIPPED [1] tests\test_r_runner.py:25: Rscript not available; skipping R runner tests
7 skipped in 0.05s
```
cpp 4 + r 3 = 7，行号与 09-21／09-22 两档完全一致 → 基线档 §四.1「cpp/r runner 真跑面本机 0 验证」**仍开放**（本单按禁止事项不装依赖）。

## 五、口径链与改后 plan.md

| 时点 | 数字 | 档 |
|---|---|---|
| 09-17 | 376 passed | plan.md 原行内注记 |
| 09-18 | 384 passed / 7 skipped | `learn-384-7-caliber-20260918.md`（口径澄清档） |
| 09-21 | 566 / 7 / 573 collected | `learn-test-baseline-20260921.md` §一（@`0564042`） |
| 09-22 00:3x | 597 / 7 / 604 | 同档 §六（@`1632f91`，n922-10） |
| **09-22 01:23** | **622 / 7 / 629** | 本档（@`a0ee9b9`，l922-107）→ 已回写 `plan.md:33` |

plan.md 第 33 行为**原地替换**（`git diff --numstat` 显示 +1/-1），其余行零改动；对外引用请写「622 passed / 7 skipped @ `a0ee9b9`」，**不要只写日期**——同日基线已走过 6 个值。

## 六、声明与遗留

- 本单零源码、零测试实现改动；未碰红线域（判分、题库内容、统计结论）；未 push 之外仅本地提交。
- 基线是活的：本档数字对 `a0ee9b9` 负责。下一班若发现 plan.md 与本档不符，先比 commit 再判漂移。
- 未回改 `learn-test-baseline-20260921.md`（基线档不回改的规矩），其 §六 现值 597 已被本档取代，但本单**没有**权限在那份档里加 superseded 指针（不在任务书产出清单内）→ 交主班决定是否补一行。
- 仓内其它引用 384/566/597 的口径面（README、docs/decisions、v0.6.5 注记等）本单未逐一排查，属 l922-108／l922-131 等巡检班的范围。
