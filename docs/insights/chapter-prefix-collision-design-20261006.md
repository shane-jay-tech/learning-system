# 章节序号碰撞 7 组＋audit_content 数字前缀唯一性诊断项设计（l1004-23；bb29 B-1 乙案）

> 产线：执行班 l1004-23（2026-10-06）。**材料＋设计稿；写 scripts 属放行后另派**。
> 差异注：l927-25 裁的是专题号语义（l922-05 方案 C），本单只做**碰撞检测**不改号（改号牵 topic 403 处＋attempts 14 个历史 pid＝数据面人工闸，bb29 已裁）。

## §一 7 组碰撞现值（只读复扫，命令内联，与 bb29 记录一致零漂移）

```
$ python （glob content/*/*/ 正则 ^(\d+) 取前缀，按 (lang, prefix) 分组计重）
碰撞组数: 7
  agent_dev 前缀 07: ['07_data_security', '07_write_spec']
  agent_dev 前缀 08: ['08_read_code', '08_review_pr']
  python 前缀 20: ['20_hr_pandas', '20_numpy_basics']
  python 前缀 21: ['21_datetime_ts', '21_hr_viz']
  python 前缀 22: ['22_hr_model', '22_statsmodels']
  r 前缀 02: ['02_logic_and_summary', '02b_dataframe']     ← 02b 形态：字母后缀非纯数字序
  r 前缀 14: ['14_real_world_data', '14_sem_basics']
```

（附注：`02_logic_and_summary` 与 `02b_dataframe` 的碰撞形态与其余六组不同——02b 是**字母分支号**；诊断项若只取 `^(\d+)` 会把两者算碰撞，属设计取舍：建议**算**（报警文案里注明形态），将来改号时 02b 可改 03 一并收敛。）

## §二 audit_content.py 新检查项设计（零改盘承诺）

**挂点**：`scripts/audit_content.py::audit()`（现 :34-88 逐 lang/topics 循环之后、paths 循环之前），作为独立 warnings 源——**只 append warnings，不动任何文件**（零改盘承诺与既有检查项同纪律）。

**检测函数伪码**：

```python
def check_topic_prefix_uniqueness(warnings: list) -> None:
    """B-1（bb29 乙案）：同 lang 数字前缀唯一性诊断。只报警、不改盘。"""
    import re
    from collections import defaultdict
    seen = defaultdict(list)
    for lang in LANGS:                                   # 复用 audit() 既有 langs 常量
        for topic_dir in (ROOT / "content" / lang).iterdir():
            m = re.match(r"^(\d+)", topic_dir.name)
            if topic_dir.is_dir() and m:
                seen[(lang, m.group(1))].append(topic_dir.name)
    for (lang, prefix), slugs in sorted(seen.items()):
        if len(slugs) > 1:
            branch = "（含字母分支号形态）" if any(re.match(r"^\d+[a-z]", s) for s in slugs) else ""
            warnings.append(
                f"[{lang}] 章节序号前缀 {prefix} 被多个专题使用{branch}: "
                + "、".join(slugs)
                + " ——排序/展示序未定义；改号属数据面人工闸（bb29），本检查只登记"
            )
```

**报警文案样例（3 条，按上伪码对现库实跑预期输出）**：

```
[python] 章节序号前缀 20 被多个专题使用: 20_hr_pandas、20_numpy_basics ——排序/展示序未定义；改号属数据面人工闸（bb29），本检查只登记
[python] 章节序号前缀 22 被多个专题使用: 22_hr_model、22_statsmodels ——排序/展示序未定义；改号属数据面人工闸（bb29），本检查只登记
[r] 章节序号前缀 02 被多个专题使用（含字母分支号形态）: 02_logic_and_summary、02b_dataframe ——排序/展示序未定义；改号属数据面人工闸（bb29），本检查只登记
```

**接入点与回归面**：`audit()` 内一行调用；`tests/` 若有 audit 全量断言（warning 计数型）需 +7 容忍或加 accepted 名单——落地批次先 `python scripts/audit_content.py` 取 warning 基数再定断言口径；`--strict` 语义下 7 条 warning 会转红，建议与 ACCEPTED_TOPICS 同款登记为「已知接受」或按 warning 通道保留（不进 strict 面，与「Topic has no problems」同档）。

## §三 边界

- 本稿零改盘：未触碰 scripts/ 与 content/；7 组清单为只读扫描产物。
- 改号收敛（含 02b→03）属数据面人工闸（bb29 原判），本设计只为把碰撞变成**机器可见**。
