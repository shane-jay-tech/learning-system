# 手动复习「提前复习」入口甲乙案材料（l1004-24；8c05 遗留2）

> 产线：执行班 l1004-24（2026-10-06）。**材料型**；差异注：l927-14 裁同文件遗留 1（暂停态），本单是遗留 2（入口），不同条。

## §一 现值（入口行号）

- 到期 tab 构造：`ui/pages/mistakes.py:103-117`——`tab_labels.append(f"到期复习 ({overdue_count} · 至多)")`（:105）仅当 `overdue_count` 非空才建 tab；`_render_due_reviews`（:124 起）渲染卡片。
- 复习按钮：`:147` `st.button("复习 →", key=f"review_{r['lang']}_{r['problem_id']}", …)`。
- 取数：`core/progress.py:428-441 get_due_reviews`——谓词 `WHERE next_due_date <= today`（**只读队列，天然不改 review_state**；真正的状态推进只发生在判题侧 `update_review_state` :393）＋伴生真总数 `get_due_reviews_total`（:643）。
- 结论：**「提前复习」的全部缺失面就是一个入口**——数据链路（只读查询＋判题侧推进）已经天然满足 8c05 判据「不把推荐间隔当强制门槛」。

## §二 乙案实现形状（最小 diff）

**入口位**：`mistakes.py:105` 处把到期 tab 从条件建改为**常建**，无到期时 tab 名换语义：

```python
# 现值
if overdue_count:
    tab_labels.append(f"到期复习 ({overdue_count} · 至多)")
# 乙案
tab_labels.append(f"到期复习 ({overdue_count} · 至多)" if overdue_count else "提前复习")
```

`_render_due_reviews` 空态分支：`overdue_count == 0` 时改调 `dao.get_due_reviews(limit, include_future=True)`（新参数）或在 ：129 空态 caption 下补一个「提前复习最近将到期」小列表——两形态任选，推荐**后者**（不动 `get_due_reviews` 谓词主口径，新增只读旁路 `WHERE next_due_date > today ORDER BY next_due_date ASC LIMIT n`，与 l1002-l 系「不动正身」纪律同形）。

**只读队列断言（守卫用例草案）**：

```python
def test_early_review_is_read_only(tmp_path):
    """提前复习入口只读：走新旁路查询后 review_state 行值逐字节不变。"""
    dao = ProgressDAO(db_path=str(tmp_path / "t.db"))
    dao.update_review_state("python", "p1", True, 3)   # next_due 在未来
    before = dao.conn.execute(
        "SELECT * FROM review_state WHERE lang='python' AND problem_id='p1'").fetchall()
    early = dao.get_early_reviews(limit=5)             # 新旁路（含未来到期）
    assert early and early[0]["problem_id"] == "p1"
    after = dao.conn.execute(
        "SELECT * FROM review_state WHERE lang='python' AND problem_id='p1'").fetchall()
    assert before == after, "提前复习查询不得改 review_state"
```

外加一条 UI 源码钉：入口按钮不得调用 `update_review_state`/`record_attempt_and_status`（防未来把「提前」做成「重置间隔」）。

**改动面估计**：progress.py 新旁路查询 ~10 行＋mistakes.py 空态分支 ~8 行＋测试 2 例 ≈ 半个执行单。

## §三 甲案维持理由（供对照）

- 现行「没有到期就看不到复习 tab」并非死路：弱项专练/错题重做两 tab 已覆盖「想主动练」的诉求；提前复习的边际价值＝「赶在到期前巩固即将到期的题」，属锦上添花。
- 甲案零新入口、零评审负担；8c05 判据的实质（**复习到访不受 next_due 强制**）已由「到期即入列＋判题侧推进」满足——判据约束的是「不阻止」，不是「必须提供提前入口」。

## §四 交主班裁

- 若裁「新增 UI 入口需评审」⇒ 甲案维持，乙案挂起；评审要点＝入口语义（提前 ≠ 重置间隔）与空态文案。
- 若放行 ⇒ 乙案按 §二形状走执行单；守卫两例必带（只读断言＋入口不触 update 的源码钉）。
