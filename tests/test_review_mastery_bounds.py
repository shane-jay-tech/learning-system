"""掌握度（间隔复习状态）的边界与跳变（信箱单 20260925-120601-99e7 · B 档 test）。

判据（卷宗「任务／验收」两行逐句改写）：
  任务：**用固定事件序列**验证**掌握度变化、最小值和上限**。
  验收：**无负数／溢出／跳变**；**参数来源可追溯且不凭空调整**。

「掌握度」在本仓的真实载体是 `review_state`（core/progress.py 的 SM-2 变体：
`interval_days` / `ease` / `review_streak` / `next_due_date`），推进入口是
`ProgressDAO.update_review_state`，生产调用方是 `core/judge.py`。
题面 `difficulty` 来自 `core/loader.py`（yaml 原文），不属本单算法面。

三条不变量按判据拆开钉：
  * **最小值／上限**：`interval_days ∈ [1, 30]`、`ease ∈ [1.5, 2.0]`、`streak ≥ 0`
  * **无负数／溢出**：`next_due_date` 永远是可解析 ISO 日期且 = today + interval_days（≥ today）
  * **无跳变**：单次答对的涨幅不超过 `interval × ease`（且被上限截断），
    失败一律回到下限 1（这是设计内的重置，不是跳变）
  * **参数来源可追溯**：代码里的兜底值 `3 / 2.0 / 0` 必须与建表 DDL 的
    `DEFAULT` 逐列相等（两处不同源就会漂移），且 30 / 1.5 两个夹钳常数
    在轨迹读数里可反查。

覆盖面自证（纪律要求断言有牙）：
  * `test_bounds_helper_flags_synthetic_out_of_range_rows` —— 直接塞越界行，
    校验器必须逐项报红；
  * `test_seeded_overflow_is_brought_back_by_the_clamp` —— 把库里预置成
    `interval_days=10000 / ease=99.0`，答对一次必须被压回 ≤30（夹钳真有 bites）；
  * 反向对照 —— 同一校验器在真实算法轨迹上全绿。
本文件**不为了自证而修改生产码**（纪律 §十三.7）。
"""
from datetime import date, timedelta

import pytest

from core.progress import ProgressDAO

LANG = "python"
PID = "python/mastery_probe"

# 固定事件序列：(passed, difficulty)。全程确定、无随机、无时钟依赖。
# 覆盖：连续答对（爬到上限 30）→ 失败重置 → 难题（difficulty>=4 才降 ease）
#       → 连续失败（ease 触到 1.5 下限）→ 再爬。
FIXED_SEQUENCE = [
    (True, 3), (True, 3), (True, 3), (True, 3), (True, 3), (True, 3),   # interval 冲上限
    (True, 5), (True, 5),                                               # 难题：ease -0.1
    (False, 5),                                                          # 失败：重置 + ease -0.2
    (True, 5), (True, 5), (True, 5), (True, 5), (True, 5), (True, 5),    # 再爬到 30 并停住
    (False, 1), (False, 1), (False, 1), (False, 1), (False, 1),          # 连续失败：ease 触底
    (True, 1), (True, 1), (True, 1),                                     # 低难题不降 ease
]

MIN_INTERVAL = 1
MAX_INTERVAL = 30
MIN_EASE = 1.5
INIT_EASE = 2.0


@pytest.fixture
def dao(tmp_path):
    d = ProgressDAO(str(tmp_path / "mastery.db"))
    yield d
    d.close()


def read_state(d):
    row = d.conn.execute(
        "SELECT interval_days, ease, review_streak, next_due_date, last_result "
        "FROM review_state WHERE lang=? AND problem_id=?", (LANG, PID)
    ).fetchone()
    assert row is not None, "固定序列首步就该建 review_state 行"
    return {"interval_days": row[0], "ease": row[1], "review_streak": row[2],
            "next_due_date": row[3], "last_result": row[4]}


def violations(s):
    """返回该状态违反不变量的清单（空 = 合格）。越界项按名字报，便于反查。"""
    bad = []
    iv, ez, sk = s["interval_days"], s["ease"], s["review_streak"]
    if not isinstance(iv, int) or isinstance(iv, bool):
        bad.append(f"interval_days 不是整数：{iv!r}")
    if iv < MIN_INTERVAL:
        bad.append(f"interval_days 低于下限 {MIN_INTERVAL}：{iv}")
    if iv > MAX_INTERVAL:
        bad.append(f"interval_days 越上限 {MAX_INTERVAL}：{iv}")
    if ez < MIN_EASE:
        bad.append(f"ease 低于下限 {MIN_EASE}：{ez!r}")
    if ez > INIT_EASE:
        bad.append(f"ease 越初始上界 {INIT_EASE}：{ez!r}")
    if sk < 0:
        bad.append(f"review_streak 为负：{sk}")
    if s["last_result"] not in ("pass", "fail"):
        bad.append(f"last_result 非法：{s['last_result']!r}")
    try:
        due = date.fromisoformat(s["next_due_date"])
    except (TypeError, ValueError):
        bad.append(f"next_due_date 不可解析：{s['next_due_date']!r}")
    else:
        if due < date.today():
            bad.append(f"next_due_date 落在过去（负天数）：{due}")
        if (due - date.today()).days > MAX_INTERVAL:
            bad.append(f"next_due_date 距今天数越上限：{(due - date.today()).days}")
    return bad


def assert_in_bounds(s):
    v = violations(s)
    assert v == [], v


# ------------------------------------------------------------------ 固定序列主用例

def test_fixed_sequence_keeps_mastery_within_bounds(dao):
    """固定事件序列全程推进 ⇒ 每一步都落在声明的区间内，无负数／溢出。"""
    trajectory = []
    for passed, difficulty in FIXED_SEQUENCE:
        dao.update_review_state(LANG, PID, passed, difficulty)
        s = read_state(dao)
        assert_in_bounds(s)
        trajectory.append((passed, difficulty, s["interval_days"], s["ease"], s["review_streak"]))

    # 序列真的走完了（防止 FIXED_SEQUENCE 被清空后整套退化成空跑）
    assert len(trajectory) == len(FIXED_SEQUENCE) == 23

    # 上界真的被触达：连续答对必须爬到 30 并停住，否则"上限"这条判据是空断言
    intervals = [t[2] for t in trajectory]
    assert max(intervals) == MAX_INTERVAL, intervals
    # 下界也真的被触达：连续失败必须把 ease 压到 1.5 并且不再往下
    eases = [t[3] for t in trajectory]
    assert min(eases) == pytest.approx(MIN_EASE), eases
    # 失败重置确实把 interval 打回下限 1
    assert min(intervals) == MIN_INTERVAL, intervals


def test_no_upward_jump_beyond_ease_factor(dao):
    """「无跳变」：答对一次的涨幅不得超过 `上一值 × ease`（上限截断后取小）。
    l1006-01/l1004-25 乙案：前进下界 max(interval+1, ...) 托底后，判据同步为
    「涨幅 ≤ 乘积帽 与 线性 +1 托底 的较大者」——低 ease 起步段允许 +1 前进。"""
    prev = None
    for passed, difficulty in FIXED_SEQUENCE:
        before = read_state(dao) if prev is not None else None
        dao.update_review_state(LANG, PID, passed, difficulty)
        s = read_state(dao)
        if before is not None and passed:
            ease_before = before["ease"]
            ceiling = min(int(before["interval_days"] * ease_before), MAX_INTERVAL)
            floor_fwd = before["interval_days"] + 1          # 乙案前进下界
            assert s["interval_days"] <= max(ceiling, floor_fwd), (
                before, s, ceiling)
            # 答对绝不该让 interval 变负或归零
            assert s["interval_days"] >= MIN_INTERVAL
        if before is not None and not passed:
            # 失败是设计内重置：interval 必等于下限、streak 必归零
            assert s["interval_days"] == MIN_INTERVAL, (before, s)
            assert s["review_streak"] == 0, (before, s)
        prev = s


def test_streak_counts_up_and_resets_exactly(dao):
    """streak 每次答对 +1、失败归零（掌握度的"变化"必须是可数的一格一格）。"""
    streak = 0
    for passed, difficulty in FIXED_SEQUENCE:
        streak = streak + 1 if passed else 0
        dao.update_review_state(LANG, PID, passed, difficulty)
        assert read_state(dao)["review_streak"] == streak
    assert streak > 0


def test_parameters_traceable_to_ddl_defaults(dao):
    """「参数来源可追溯」：代码兜底值必须与建表 DDL 的 DEFAULT 逐列相等。

    `update_review_state` 无行时用 `3 / 2.0 / 0`（core/progress.py 的 else 分支），
    而 DDL 也声明了 DEFAULT —— 两处若各改一处，新库与老库的掌握度轨迹就会分叉。
    这里读 `PRAGMA table_info` 的 dflt_value 与代码常量对撞，不靠注释自觉。
    """
    defaults = {
        r[1]: r[4] for r in dao.conn.execute("PRAGMA table_info(review_state)").fetchall()
    }
    # 代码侧兜底值（写死在 progress.py 的 else 分支；名字法取，不锚行号）
    import inspect
    src = inspect.getsource(ProgressDAO._upsert_review_state_locked)  # l1012-02 体迁锚随翻
    assert "interval, ease, streak = 3, 2.0, 0" in src, src

    assert defaults["interval_days"] == "3"
    assert defaults["ease"] == "2.0"
    assert defaults["review_streak"] == "0"

    # 上限／下限常数也必须能从源码里逐字反查（不是"读现值等于现值"）
    assert "min(max(interval + 1, int(interval * ease)), 30)" in src   # 乙案前进下界同笔溯源
    assert "max(1.5, ease - 0.1)" in src
    assert "max(1.5, ease - 0.2)" in src
    assert "interval = 1" in src


def test_difficulty_gate_is_4_and_only_hard_items_lower_ease(dao):
    """「不凭空调整」：只有 difficulty>=4 的答对才降 ease；低难题答对时 ease 必须一格不动。

    这条把「门槛值 4」和「步长 0.1」两个参数从**行为**侧钉住（不是读源码字面量）：
    若有人把 `difficulty >= 4` 改成 `>= 3`，或把 0.1 改成 0.05，本用例会红。
    """
    for difficulty in (1, 2, 3):
        pid = f"python/ease_gate_{difficulty}"
        dao.update_review_state(LANG, pid, True, difficulty)
        ease = dao.conn.execute(
            "SELECT ease FROM review_state WHERE problem_id=?", (pid,)).fetchone()[0]
        assert ease == pytest.approx(INIT_EASE), (difficulty, ease)

    hard = "python/ease_gate_4"
    dao.update_review_state(LANG, hard, True, 4)
    ease = dao.conn.execute(
        "SELECT ease FROM review_state WHERE problem_id=?", (hard,)).fetchone()[0]
    assert ease == pytest.approx(INIT_EASE - 0.1), ease

    # 同一个难题再答对一次：继续按 0.1 递减，不能一次掉两档
    dao.update_review_state(LANG, hard, True, 4)
    ease2 = dao.conn.execute(
        "SELECT ease FROM review_state WHERE problem_id=?", (hard,)).fetchone()[0]
    assert ease2 == pytest.approx(INIT_EASE - 0.2), (ease, ease2)


# ------------------------------------------------------------------ 覆盖面自证（有牙）

def test_bounds_helper_flags_synthetic_out_of_range_rows():
    """合成反例：越界行必须被 violations() 逐项报出 ⇒ 主断言不是恒真式。"""
    synthetic = [
        ({"interval_days": -4, "ease": 2.0, "review_streak": 0,
          "next_due_date": date.today().isoformat(), "last_result": "pass"},
         "interval_days 低于下限"),
        ({"interval_days": 31, "ease": 2.0, "review_streak": 0,
          "next_due_date": date.today().isoformat(), "last_result": "pass"},
         "越上限"),
        ({"interval_days": 5, "ease": 1.4, "review_streak": 0,
          "next_due_date": date.today().isoformat(), "last_result": "fail"},
         "ease 低于下限"),
        ({"interval_days": 5, "ease": 9.9, "review_streak": 0,
          "next_due_date": date.today().isoformat(), "last_result": "pass"},
         "ease 越初始上界"),
        ({"interval_days": 5, "ease": 2.0, "review_streak": -2,
          "next_due_date": date.today().isoformat(), "last_result": "pass"},
         "review_streak 为负"),
        ({"interval_days": 5, "ease": 2.0, "review_streak": 1,
          "next_due_date": (date.today() - timedelta(days=7)).isoformat(),
          "last_result": "pass"},
         "落在过去"),
        ({"interval_days": 5, "ease": 2.0, "review_streak": 1,
          "next_due_date": "not-a-date", "last_result": "weird"},
         "不可解析"),
    ]
    for state, expected_fragment in synthetic:
        vs = violations(state)
        assert vs, state
        assert any(expected_fragment in v for v in vs), (expected_fragment, vs)


def test_seeded_overflow_is_brought_back_by_the_clamp(dao):
    """预置越界的库行（模拟导入/手工改库），答对一次必须被夹钳压回 ≤30。

    这条专打「溢出」方向：把上限那行 `min(..., 30)` 删掉的话本用例会红
    （30 × 99.0 = 2970 会被写进库），所以它证明上限夹钳真的在起作用。
    """
    with dao.conn:
        dao.conn.execute(
            "INSERT INTO review_state (lang, problem_id, interval_days, ease, review_streak, "
            "next_due_date, last_result) VALUES (?,?,?,?,?,?,?)",
            (LANG, PID, 10000, 99.0, 3, date.today().isoformat(), "pass"))
    assert dao.conn.execute(
        "SELECT interval_days FROM review_state WHERE problem_id=?", (PID,)).fetchone()[0] == 10000

    dao.update_review_state(LANG, PID, True, 5)
    s = read_state(dao)
    assert s["interval_days"] <= MAX_INTERVAL, s
    assert s["next_due_date"] >= date.today().isoformat(), s


def test_bounds_survive_reopen(dao, tmp_path):
    """落盘后换连接重开：区间不变（掌握度不是进程内状态）。"""
    for passed, difficulty in FIXED_SEQUENCE[:8]:
        dao.update_review_state(LANG, PID, passed, difficulty)
    before = read_state(dao)
    dao.close()

    d2 = ProgressDAO(str(tmp_path / "mastery.db"))
    try:
        assert read_state(d2) == before
        assert_in_bounds(read_state(d2))
    finally:
        d2.close()
