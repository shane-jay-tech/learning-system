"""复习状态机四类规则：转移矩阵 + "推荐间隔不是门禁" 的钉桩。

班：qoder-executor-20260925-2030-learn39 · 单号 20260925-154240-8c05（风险档 B，工作类型 research）

卷宗验收：「每种状态转移有表格与测试；不把推荐间隔当作用户强制门槛。」
表格在本文件 docstring 与 result「验收情况」两处；本文件只补**既有测试没覆盖的三面**
（数值边界已由 tests/test_review_mastery_bounds.py 钉住，此处不重复建设）：
  A. 完整转移矩阵（可达 interval/ease/streak 集合，逐格由**生产函数**跑出来）
  B. 「推荐间隔不是门禁」——练习入口与推荐引擎都不以到期日阻断作答（正向＋反向双证）
  C. 「暂停」「手动复习」在本仓**不是实体**——把否证钉成断言，将来若有人加这两态，本文件先红

🔴 全部用例的库都是 `:memory:`（`ProgressDAO.__init__` 无参会退回默认生产库，故绝不无参构造）。
"""
import itertools
import os
import re

import pytest

from core.progress import ProgressDAO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INIT = (3, 2.0, 0)          # 无行时的起点，core/progress.py:368-370
MIN_INTERVAL = 1
MAX_INTERVAL = 30
MIN_EASE = 1.5


def _dao():
    return ProgressDAO(":memory:")


def _put(dao, interval, ease, streak):
    if (interval, ease, streak) != INIT:
        dao.conn.execute(
            "INSERT INTO review_state (lang, problem_id, interval_days, ease, review_streak, "
            "next_due_date, last_result) VALUES (?,?,?,?,?,?,?)",
            ("python", "p", interval, ease, streak, "2026-01-01", "pass"))
        dao.conn.commit()


def _step(state, passed, difficulty):
    """用**生产函数**跑一格转移（不抄公式——抄公式就是自证循环）。"""
    dao = _dao()
    _put(dao, *state)
    dao.update_review_state("python", "p", passed, difficulty)
    row = dao.conn.execute(
        "SELECT interval_days, ease, review_streak, last_result, next_due_date "
        "FROM review_state").fetchone()
    dao.close()
    return {"interval": row[0], "ease": round(row[1], 6), "streak": row[2],
            "last_result": row[3], "due": row[4]}


# 状态格：真实可达的 (interval, ease, streak) 组合，覆盖初始/中段/封顶/降级后
GRID = [INIT, (6, 2.0, 1), (12, 2.0, 2), (24, 2.0, 3), (30, 2.0, 4), (30, 1.5, 9),
        (1, 1.5, 0), (1, 2.0, 0), (2, 1.8, 1), (10, 1.6, 3), (16, 1.8, 4)]
DIFFS = [1, 3, 4, 5]


# ==========================================================================
# A. 转移矩阵
# ==========================================================================
def test_转移矩阵_失败一律降到1天并清零streak():
    dao_cases = [(g, d) for g, d in itertools.product(GRID, DIFFS)]
    bad = []
    for (st, diff) in dao_cases:
        r = _step(st, False, diff)
        if not (r["interval"] == MIN_INTERVAL and r["streak"] == 0
                and r["last_result"] == "fail"):
            bad.append((st, diff, r))
    assert bad == [], f"失败降级规则不唯一：{bad[:4]}"


def test_转移矩阵_失败后ease降幅0_2且不低于下限():
    for st in GRID:
        r = _step(st, False, 3)
        expect = round(max(MIN_EASE, st[1] - 0.2), 6)
        assert r["ease"] == pytest.approx(expect), (st, r["ease"], expect)
    assert _step((1.5, 1.5, 0), False, 3)["ease"] == pytest.approx(MIN_EASE), "ease 下界未生效"


def test_转移矩阵_通过时ease仅在难度不小于4时降0_1():
    for st in GRID:
        for diff in DIFFS:
            r = _step(st, True, diff)
            expect = round(max(MIN_EASE, st[1] - (0.1 if diff >= 4 else 0.0)), 6)
            assert r["ease"] == pytest.approx(expect), (st, diff, r["ease"], expect)
    lo = [(_step(st, True, 3)["ease"], st[1]) for st in GRID]
    assert all(a == pytest.approx(b) for a, b in lo), "diff<4 竟改动 ease —— 与判分口径无关的隐性漂移"


def test_转移矩阵_通过后间隔按interval乘ease增长且封顶30():
    for st in GRID:
        r = _step(st, True, 3)
        # l1006-01/l1004-25 乙案：前进下界 max(interval+1, ...) 先并，再整体封顶——两式都保留
        assert r["interval"] == min(max(st[0] + 1, int(st[0] * st[1])), MAX_INTERVAL), (st, r)
        assert r["interval"] >= MIN_INTERVAL
        assert r["streak"] == st[2] + 1
        assert r["last_result"] == "pass"


def test_转移矩阵_连通过序列单调不减并停在封顶():
    cur, seq = INIT, []
    for _ in range(12):
        r = _step(cur, True, 3)
        seq.append(r["interval"])
        cur = (r["interval"], r["ease"], r["streak"])
    assert seq == [6, 12, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30], seq
    assert all(b >= a for a, b in zip(seq, seq[1:])), "连续通过竟缩短间隔"


def test_转移矩阵_可达集合与next_due_date口径():
    seen_iv, seen_ez = set(), set()
    for st, passed, diff in itertools.product(GRID, [True, False], DIFFS):
        r = _step(st, passed, diff)
        seen_iv.add(r["interval"])
        seen_ez.add(round(r["ease"], 3))
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["due"]), f"next_due_date 非 ISO 日：{r['due']}"
    assert seen_iv == {1, 2, 3, 6, 12, 16, 24, 28, 30}, sorted(seen_iv)
    # 28 来自 (16, 1.8, 4) 这一格：int(16*1.8)=28，说明 30 的帽只在乘积越过 30 时才咬住
    assert 28 in seen_iv and 30 in seen_iv
    assert min(seen_ez) == MIN_EASE and max(seen_ez) == 2.0, sorted(seen_ez)


def test_转移矩阵_低间隔配低ease时前进下界托底线性起步():
    """l1006-01/l1004-25 乙案（用户 2026-10-06 拍板）：通过必前进——(1, 1.5, 0) 通过后
    原本 int(1*1.5)=1 原地踏步，现由 max(interval+1, ...) 下界托底转线性（本例语义反转，
    改名前为「乘积取整会原地踏步」，该行为已被乙案替代）。"""
    r = _step((1, 1.5, 0), True, 3)
    assert r["interval"] == 2, f"前进下界应托到 2，实得 {r}"
    assert r["streak"] == 1
    r2 = _step((2, 1.8, 1), True, 3)
    assert r2["interval"] == 3, r2          # max(2+1, int(3.6))=max(3,3)=3，两式恰等


def test_转移矩阵_有牙_若去掉封顶则矩阵会在24之后失守():
    """合成反例：本例证明"封顶 30"这条断言真能区分有无 min(...,30)。
    若有人把封顶调大，上一例会先红；这里再补一刀：无帽参考序列必须与生产序列不同值。"""
    cur, capped = INIT, []
    for _ in range(6):
        r = _step(cur, True, 3)
        capped.append(r["interval"])
        cur = (r["interval"], r["ease"], r["streak"])
    cur2, uncapped = INIT, []
    for _ in range(6):
        nv = int(cur2[0] * cur2[1])          # 同公式，但去掉 min(..., 30)
        cur2 = (nv, cur2[1], cur2[2] + 1)
        uncapped.append(nv)
    assert capped != uncapped, f"夹具无判别力：有无封顶同值 {capped}"
    assert capped[3:] == [30] * 3 and uncapped[3:] == [48, 96, 192], (capped, uncapped)


def test_转移矩阵_乙案低ease起步序列线性转几何():
    """l1006-01/l1004-25 乙案配方序列：ease=1.5 初值 1 连续通过 ⇒ 2,3,4,6,9,13,19,28
    （低速段线性 +1 托底，ease 复利接管后回归几何；封顶语义不变）。"""
    cur, seq = (1, 1.5, 0), []
    for _ in range(8):
        r = _step(cur, True, 3)
        seq.append(r["interval"])
        cur = (r["interval"], r["ease"], r["streak"])
    assert seq == [2, 3, 4, 6, 9, 13, 19, 28], seq
    r9 = _step(cur, True, 3)
    assert r9["interval"] == 30, r9          # min(max(29, 42), 30)=30，封顶保持

# ==========================================================================
# B. 推荐间隔不是用户强制门槛
# ==========================================================================
def test_练习入口完全不读复习状态故到期日无法阻断作答():
    src = open(os.path.join(ROOT, "ui", "pages", "language.py"), encoding="utf-8").read()
    for token in ("review_state", "next_due_date", "get_due_reviews", "due_review_ids"):
        assert token not in src, f"练习页开始引用 {token} ⇒ 推荐间隔正在变成门禁"


def test_推荐引擎把到期题作为一个受限来源而非门禁():
    src = open(os.path.join(ROOT, "core", "recommend.py"), encoding="utf-8").read()
    m = re.search(r'_fill\(review,[^)]*\)', src)
    assert m, "推荐引擎里到期复习来源的接线已变 ⇒ 本例前提需复核"
    assert "review_due" in src
    limit = re.search(r"_fill\(review,.*?,\s*(\d+)\)", src)
    assert limit and int(limit.group(1)) >= 1, f"review 来源配额解析失败：{m.group(0)}"
    assert int(limit.group(1)) < 10, "review 配额异常放大 ⇒ 挤压新题面"
    # 未到期题仍应能被推荐出来（explore 来源不受 review 约束）
    assert "explore" in src, "探索新题来源消失 ⇒ 到期队列变成了唯一入口"


def test_未到期与无复习态的题目照样可以作答并写入进度():
    """行为面正向证：一道从未有过 review_state、且 next_due 被刻意设到未来的题，
    经生产写入器作答后必须照常记账（没有任何"还没到期"的拒绝路径）。"""
    dao = _dao()
    dao.update_review_state("python", "p_future", True, 3)
    future = dao.conn.execute(
        "SELECT next_due_date FROM review_state WHERE problem_id='p_future'").fetchone()[0]
    assert future > "2020-01-01"
    dao.update_review_state("python", "p_future", True, 3)     # 未到期再答一次
    row = dao.conn.execute(
        "SELECT interval_days, review_streak FROM review_state WHERE problem_id='p_future'").fetchone()
    assert row == (12, 2), f"未到期作答被间隔规则拒绝或未记账：{row}"
    dao.record_attempt_and_status("python", "p_nostate", "x", True, "")
    assert dao.get_status("python", "p_nostate") == "solved"
    assert dao.conn.execute("SELECT COUNT(*) FROM review_state WHERE problem_id='p_nostate'"
                            ).fetchone()[0] == 0, "写入器竟自动建了复习态行"
    dao.close()


def test_到期查询只做筛选不设拒绝分支():
    src = open(os.path.join(ROOT, "core", "progress.py"), encoding="utf-8").read()
    body = src.split("def get_due_reviews")[1][:900]
    assert "next_due_date <= ?" in body, "到期查询表达式已变 ⇒ 复核门禁面"
    for word in ("raise", "return None", "not due", "未到期"):
        assert word not in body, f"get_due_reviews 出现拒绝路径 {word!r} ⇒ 间隔正在变门槛"


# ==========================================================================
# C. 「暂停」「手动复习」不是实体（否证钉桩）
# ==========================================================================
def test_暂停态在本仓不存在将来加了要先红():
    hits = []
    for base in ("core", "ui"):
        for dp, _dn, fns in os.walk(os.path.join(ROOT, base)):
            for fn in fns:
                if fn.endswith(".py"):
                    t = open(os.path.join(dp, fn), encoding="utf-8").read()
                    if re.search(r"暂停|paused|suspend|\barchive[_d]?\b", t):
                        hits.append(os.path.relpath(os.path.join(dp, fn), ROOT))
    assert hits == [], f"「暂停」已在世，本单需按实况重做：{hits}"


def test_复习态取值域只有pass与fail没有第三态():
    """注意取值域要**按函数体切**：整份文件里还有 `"solved" if passed else "wrong"`
    这一对属于 problems_status，混进来会得出两个三元组（本班第一版就混了）。"""
    src = open(os.path.join(ROOT, "core", "progress.py"), encoding="utf-8").read()
    body = src.split("def _upsert_review_state_locked")[1].split("def ")[0]  # l1012-02 体迁锚随翻
    vals = set(re.findall(r'"([a-z]+)" if passed else "([a-z]+)"', body))
    assert vals == {("pass", "fail")}, f"last_result 取值域变了：{vals}"
    assert re.search(r"last_result", body), "update_review_state 不再写 last_result"
    # 全仓第三态自查：review_state.last_result 的读者只认 pass/fail
    readers = []
    for dp, _dn, fns in os.walk(os.path.join(ROOT, "core")):
        for fn in fns:
            if fn.endswith(".py"):
                t = open(os.path.join(dp, fn), encoding="utf-8").read()
                for m in re.finditer(r'last_result\s*(?:==|!=)\s*"([a-z]+)"', t):
                    readers.append(m.group(1))
    assert set(readers) <= {"pass", "fail"}, f"出现第三态读者：{set(readers)}"


def test_手动复习在本仓不是命名实体其最近邻是到期复习页的跳转按钮():
    src = open(os.path.join(ROOT, "ui", "pages", "mistakes.py"), encoding="utf-8").read()
    assert "手动复习" not in src and "提前复习" not in src, "手动复习已成实体，前提变了"
    assert "到期复习" in src, "错题本页连到期复习tab都没了 ⇒ 本例的最近邻指认失效"
    assert re.search(r'st\.button\("复习 →"', src), "复习按钮文案/形态已变 ⇒ 复核门禁面"
    # 最近邻是"跳转"，不是"绕开间隔"：按钮只 set 状态后导航，不改 review_state
    seg = src.split('st.button("复习 →"')
    assert len(seg) == 2, "复习按钮不止一处，本例需逐处核"
    tail = seg[1][:400]
    assert "update_review_state" not in tail, "复习按钮直接改写了复习态 ⇒ 手动通道正在绕过间隔规则"
