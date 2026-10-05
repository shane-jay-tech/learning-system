# review_state 导入值域与 ease 上界夹钳裁决材料（l1004-13；99e7 遗留2/3）

> 产线：执行班 l1004-13（2026-10-06）。**材料型**；差异注：l927-50 裁的是 retake_intent 兼容口子，不同字段不相干。

## §一 现值（两处行号）

- **导入无值域**：`core/data_portability.py:128-139`——review_state 逐行 `INSERT OR REPLACE`，`r.get("interval_days", 3)`／`r.get("ease", 2.0)`／`r.get("review_streak", 0)` 只有**缺键默认**，无任何值域检查；`_validate`（:53-67）只查结构（format/version/表存在），不查行内值。
- **写侧无上界**：`core/progress.py:393-414` `update_review_state`——ease 只有**下界**夹钳（`:410 ease = max(1.5, ease - 0.1)`／`:414 max(1.5, ease - 0.2)`），无 `min(ease, 上界)`；interval 有上界（`:408 min(int(interval * ease), 30)`）但乘数 ease 本身失控时恒顶格。

## §二 破坏性用例（ease=1234.5 导入路径 tmp 复现 ✓）

```
$ .venv/Scripts/python.exe （tmp 副本：payload review_state=[{ease:1234.5, interval_days:9999, review_streak:-7}] → import_all）
→ import stats review_state=1（无校验整份收下）
→ after import: (9999, 1234.5, -7)                       ← 脏值三连入库
→ after one pass(update_review_state True): (30, 1234.5)  ← interval=min(int(9999*1234.5),30)=30 顶格
```
后果链：**ease=1234.5 永久停留**（写侧只降不升无上界，通过时 `ease-0.1` 从 1234.5 起步永远远超正常值域）＋ interval 恒顶格 30 天＋负 streak 未拦。「手改或损坏的导出 JSON」一击直达。

## §三 两案对照

| | 案① `_validate` 增列值域检查（拒绝整份导入） | 案② `update_review_state` 加 `min(ease, 上界)` |
|---|---|---|
| 形态 | :67 前对 review_state 逐行断言 `interval ∈ [0,30]、ease ∈ [0,2.95]、streak ≥ 0`（上界取值见下注），违例返回错误串 ⇒ 整份拒绝 | :408 前补 `ease = min(ease, 2.95)`（或 2.0，见下注） |
| 破坏性用例效果 | 上例导入**直接被拒**（用户看到明确错误，可修导出文件） | 导入仍收下脏行，但下一次写库时 ease 被夹回——**interval 9999 与 streak=-7 仍漏**（需再各补一夹钳才完整） |
| 导入成功率影响 | **会拒掉含任何脏行的整份导出**——合法用户一份大导出里一条手改行 ⇒ 全份进不来（99e7 明言的代价） | 导入成功率零影响 |
| 覆盖面 | 只护导入通道；手改活库/其它写入面不设防 | 护**所有**写路径（导入/手改/未来通道），且与既有下界夹钳对称（`max(1.5, …)` 旁补 `min(…, 上界)`） |
| 断言影响 | data_portability 校验测试 +2~3（合法/越界/边界值） | progress 测试 +1~2（上界夹钳/正常值不动） |

**上界取值注**：ease 理论域＝下界 1.5 起、每通过 -0.1 ⇒ 合法稳态上界其实就是初值 2.0；但历史库可能存在 >2.0 行（若曾有其它通道），夹 2.0 会立即改写它们。两档：**严（2.0，与初值一致）** vs **宽（2.95，留三步降档余量）**——建议严档 2.0，落码前先 `SELECT MAX(ease) FROM review_state` 普查存量（本班未查，落码批次前置一步）。

**材料倾向**：**②先行＋①后置**（②补齐三夹钳 ease/interval/streak 后覆盖全通道；①作为导入面 UX 加固可选，其「整份拒绝」语义建议改「跳过脏行＋计数告警」折中案再裁）。

## §四 口径备注：int(interval * ease) 向下截断

`:408` 的 `int()` 是**截断非四舍五入**（如 2.9×3=8.7→8）；与上界夹钳叠加后，ease 恰为整界值时 interval 恒偏小 1 的形态存在。现行测试若已按截断口径断言则保持；夹钳落码批次须在用例里显式钉一个截断样本防未来「顺手改 round」漂移。

## §五 边界

两案均涉用户数据取舍（99e7 明言停手交回），交主班；本档复现全程 tmp 副本（已清理），零生产库触碰。
