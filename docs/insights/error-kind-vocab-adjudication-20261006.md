# error_kind 词表统一裁决材料：编译/运行期＋策略拒绝撞名＋退出码上屏（l1004-05；07d4 D-14/D-15＋70e3＋a6b8）

> 产线：执行班 l1004-05（2026-10-06）。**材料型，零码改动（判题可见面，裁决交主班）**。
> 矿源：`done/20260925-120552-07d4`（D-14/D-15）＋`done/20260925-120554-70e3`（策略拒绝撞名）＋`done/20260925-154243-a6b8`（撞名裁决交主班）三遗留合编。

## §一 error_kind 写点/读点全量清单（rg 现值）

### 写点（core/，26 处）

| 文件:行 | 现值 | 语义 |
|---|---|---|
| base.py:34 | `"sandbox"` | 公开部署拒绝（**策略拒绝**） |
| python_runner.py:172 | `"timeout"` | 墙钟超时 |
| python_runner.py:185 | `None if ok else _error_kind_for(stderr)` | r5 B3（9/27 用户裁决）已分 syntax/runtime，非该两值退化 runtime——**D-14 的 python 臂已落地**（矿源锚漂移：07d4 时点尚未修，现值已修，销案留痕） |
| cpp_runner.py:84/:110 | `"sandbox"` | **g++ 未装/编译器启动失败（toolchain 缺失！）** |
| cpp_runner.py:135 | `"compile"` | 编译失败 |
| cpp_runner.py:123/:163 | `"timeout"` | 编译/运行超时 |
| cpp_runner.py:176 | `None if ok else "runtime"` | 运行期 |
| r_runner.py:60 | `"sandbox"` | **Rscript 未装（toolchain 缺失！）** |
| r_runner.py:118 | `"timeout"`；`:131` | `None if ok else "runtime"` |
| sql_runner.py:128/:136/:144 | `"runtime"` | **空输入/多语句/非 SELECT（策略拒绝！）** |
| sql_runner.py:154 | `"sandbox"` | setup_sql 白名单拒绝（**策略拒绝**） |
| sql_runner.py:213 | `None`；`:224 "timeout"`；`:230/:235/:241 "runtime"` | 执行期 |

### 读点

- `classify` 词表（`error_feedback.py:57-66` KINDS）＝`toolchain/policy/timeout/syntax/undefined_name/type/runtime/none`——**分类器自成一套词**，与写点原始标签 `{sandbox, compile, runtime, timeout, None}` 两套并存：`sandbox` 一词同时背「toolchain 缺失」（cpp:84/r:60）与「策略拒绝」（base:34/sql:154）两义＝**a6b8 撞名实锤**；`runtime` 写点在 sql 侧还兼「策略拒绝」（:128/136/144）。
- UI/判分读点：`judge.py:146` 自证不读 error_kind（判分只看 ok）；UI 面经 `_row_feedback`→`classify` 走分类器词表，**写点原始标签不直接上屏**——撞名目前是「台账/测试口径」问题，非学生可见错误。
- 测试断言面：12 文件 46 处 `error_kind`（rg -c：execution_stage_separation 19／native_runners_mocked 6／error_feedback_rows 4／python_runner 4／runner_security 3／sql+cpp+r_runner 各 2／其余 4 文件各 1）。

## §二 两案（各带断言影响数）

### 案 A：统一词表（classify KINDS 平移到写点）

写点改发分类器词：策略拒绝四处 → `"policy"`（base:34、sql:128/136/144/154）、toolchain 缺失三处 → `"toolchain"`（cpp:84/:110、r:60）、`"compile"` → `"syntax"`（cpp:135，与 classify 词表对齐）、timeout/None 不动。
- **断言影响**：写点侧断言 ≈ **15 处**（sql_runner 2＋cpp_runner 2＋r_runner 2＋runner_security 3＋native_runners_mocked 6——与矿源「15 处测试断言」吻合）；`execution_stage_separation`（19 处）断的是 python 侧 syntax/runtime 分离，**不在改造面**零波及；classifier 词表零改动（KINDS 本就是目标词表，无平移成本）。
- **收益**：一词一义；台账/审计可按 KINDS 直查；future error_kind 新档（l1004-01 的 memory_terminated/cpu_time_terminated）有单源落点。
- **风险**：写点标签是事实上的对外契约（若有外部消费按 "sandbox" 字面过滤则破）；需全仓 rg 二次确认无第三消费方（本班已查 UI/判分不读，测试是唯一消费面）。

### 案 B：双面文档化（写点保留原始标签）

零码：在 `error_feedback.py` KINDS 注释块加一张「写点标签 ↔ 分类器词」对照表（sandbox→policy|toolchain 二义、compile→syntax、runtime 写点兼策略拒绝三义），TestCapsSingleSource 同址扩一条**文档钉**（断言注释存在）。
- **断言影响**：**0 处**（新钉 1 条自证注释在位）。
- **收益**：零行为面；撞名风险被文档显式化。
- **代价**：两套词长期并存，后续每张新卡（l1004-01 资源档）都要双写对照。

**材料倾向**：案 A（15 断言一次付清，词表归一）；案 B 为零风险兜底。裁决交主班（a6b8 明言不在执行手授权内）。

## §三 D-15 退出码上屏文案（并入两案任一）

- 现值：`ok=False 且 stderr 空` 时 `_error_kind_for("")`→classify `"none"`→python 侧退化映射 `"runtime"`（python_runner.py:30 守卫）——**「none 对 ok=False」的自相矛盾在 python 臂已被 r5 B3 守卫吃掉**（矿源锚漂移留痕）；但 **exit_code 至今不上屏**（ui/pages/language.py 无 exit_code 渲染，rg 零命中）。
- **文案**（stderr 块头部前置一行，仅 `not ok and stderr` 非空或 exit_code 非 0 时）：
  > `退出码：{exit_code}`（exit_code 为 None 时显示「进程被强制终止」）
- 断言影响：language 页渲染断言 ≤2 处（现有 stderr_block 相关件补一行期望）。
