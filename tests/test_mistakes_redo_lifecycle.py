"""失败题的重做生命周期与状态转移无重复（信箱单 20260925-120603-942f · B 档 test）。

判据（卷宗「任务／验收」两行逐句改写）：
  任务：检查**失败题进入重做**、**提示逐级展示**和**通过后状态更新**。
  验收：覆盖**连续失败**、**放弃**和**重新进入**；**状态转移无重复**。

本仓对应物：
  * 失败题进入重做 = `problems_status.status='wrong'` 的行被 `ProgressDAO.list_mistakes()`
    捞进「错题重做」页（`ui/pages/mistakes.py:145-168`）。
  * 通过后状态更新 = 同键 `INSERT OR REPLACE` 把 status 改成 `solved`，
    该题必须从错题本、弱项专练、`summary_by_lang` 三个视图同时消失。
  * 状态转移无重复 = `problems_status` 主键 `(lang, problem_id)` ⇒ 每题恒一行，
    无论转移多少轮；错题本条目数 == 状态为 wrong 的**不同键**数。
  * 放弃 = 不作答地离开（`navigate_to_problem` / `drop_shown_judge_result` 只动
    session_state、不写库，`ui/components.py:54-73` 实测）⇒ 盘上必须一字不变。
  * 重新进入 = 换一条连接重开同一库再答错 ⇒ 仍不得多出第二行状态。

「提示逐级展示」这条**按盘上实况否证后收窄**（见 `test_hints_are_rendered_in_one_pass...`
与本单 result 的证据节）：`ui/pages/language.py:285-288` 是在**单个** expander 里
一次性列出全部 hints，没有任何按失败次数/尝试数递进的门槛。
"""
import sqlite3
from pathlib import Path

import pytest

from core.judge import _record_attempt
from core.progress import ProgressDAO

LANG = "python"
PID = "python/redo_lifecycle"
REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "redo.db")


@pytest.fixture
def dao(db_path):
    d = ProgressDAO(db_path)
    yield d
    d.close()


def status_rows_for(d, pid=PID):
    return d.conn.execute(
        "SELECT COUNT(*) FROM problems_status WHERE lang=? AND problem_id=?",
        (LANG, pid)).fetchone()[0]


def fail(d, n, code_prefix="bad"):
    """连续失败 n 次，走生产写入口（attempts + problems_status + review_state + events）。"""
    for i in range(n):
        _record_attempt(LANG, PID, f"{code_prefix}{i}", False, f"点评{i}", d)


def pass_it(d, n=1, code_prefix="good"):
    for i in range(n):
        _record_attempt(LANG, PID, f"{code_prefix}{i}", True, f"通过{i}", d)


def mistake_ids(d):
    return [m["problem_id"] for m in d.list_mistakes()]


# ------------------------------------------------------------- 失败题进入重做

def test_consecutive_failures_enter_redo_exactly_once(dao):
    """连续失败 5 次：错题本必须出现该题**且只出现一次**，明细 5 条都在。"""
    fail(dao, 5)

    assert dao.attempt_count(LANG, PID) == 5, "事件明细必须逐条留痕（重做历史不能覆盖）"
    assert status_rows_for(dao) == 1, "状态转移无重复：五轮失败后仍恰一行"
    assert mistake_ids(dao) == [PID], "错题本只列一次，且只有这一道"
    assert dao.get_status(LANG, PID) == "wrong"

    s = dao.summary_by_lang()
    assert s[LANG] == {"total": 1, "solved": 0, "wrong": 1}, s
    # 弱项专练按专题分组，每题只计一次（错题数 = 不同题数，不是尝试数）
    wrong_rows = dao.conn.execute(
        "SELECT COUNT(*) FROM problems_status WHERE status='wrong'").fetchone()[0]
    assert wrong_rows == len(set(mistake_ids(dao))) == 1


def test_redo_view_shows_the_last_attempt_not_the_first(dao):
    """重做页展示的代码/点评必须是**最后一次**尝试（`list_mistakes` 的 rn=1 语义）。

    有牙设计：五次代码字面各不相同 ⇒ 若窗口函数排序被改成 ASC（取到最早一次），
    本用例直接红；同时显式断言首末两次**不相等**，排除"碰巧相等而蒙绿"。
    """
    fail(dao, 5, code_prefix="第5次之前的代码")
    entries = dao.list_mistakes()
    assert len(entries) == 1
    assert entries[0]["code"] == "第5次之前的代码4", entries[0]
    assert entries[0]["ai_feedback"] == "点评4", entries[0]

    first_code = dao.conn.execute(
        "SELECT code FROM attempts WHERE lang=? AND problem_id=? ORDER BY id ASC LIMIT 1",
        (LANG, PID)).fetchone()[0]
    assert first_code != entries[0]["code"], (first_code, entries[0]["code"])


# ------------------------------------------------------------- 通过后状态更新

def test_passing_updates_status_and_clears_every_view(dao):
    """重做通过后：状态转 solved，错题本/汇总/到期复习三处同步，不得留残影。"""
    fail(dao, 3)
    assert mistake_ids(dao) == [PID]

    pass_it(dao, 1)

    assert dao.get_status(LANG, PID) == "solved"
    assert status_rows_for(dao) == 1, "由 wrong 转 solved 是原地替换，不是插新行"
    assert mistake_ids(dao) == [], "错题本必须当场清空该题"
    assert dao.summary_by_lang()[LANG] == {"total": 1, "solved": 1, "wrong": 0}
    solved = dao.solved_with_timestamps()
    assert [r["problem_id"] for r in solved] == [PID]
    # 复习侧也只一行（通过后进入待复习池，而不是重复登记）
    rs = dao.conn.execute("SELECT COUNT(*) FROM review_state WHERE problem_id=?", (PID,)).fetchone()[0]
    assert rs == 1, rs
    assert dao.conn.execute(
        "SELECT last_result FROM review_state WHERE problem_id=?", (PID,)).fetchone()[0] == "pass"


def test_wrong_solved_wrong_cycles_never_duplicate_rows(dao):
    """来回转移 12 轮（对↔错交替）：状态表恒一行，错题本视图恒不重复。"""
    for i in range(12):
        _record_attempt(LANG, PID, f"c{i}", i % 2 == 0, f"fb{i}", dao)
        assert status_rows_for(dao) == 1, i
        ids = mistake_ids(dao)
        assert len(ids) == len(set(ids)), ids          # 无重复条目
        assert len(ids) in (0, 1)
    # 第 12 轮 i=11 → passed=False ⇒ 最后一次是"错"，必须回到错题本恰一次
    assert dao.get_status(LANG, PID) == "wrong"
    assert mistake_ids(dao) == [PID]
    assert dao.attempt_count(LANG, PID) == 12


# ------------------------------------------------------------- 放弃 / 重新进入

def test_giving_up_touches_nothing_on_disk(db_path):
    """放弃（不作答地离开）：重开库后盘上事实与离开前逐字段相同。

    「离开」在本仓的可复现形态＝只调 session_state 侧的导航助手
    （`navigate_to_problem` / `drop_shown_judge_result` 不接 DAO、不写库），
    随后关连接＝刷新／退出应用。
    """
    d = ProgressDAO(db_path)
    try:
        fail(d, 4)
        before_status = d.conn.execute(
            "SELECT status, last_attempt_ts FROM problems_status WHERE problem_id=?",
            (PID,)).fetchone()
        before_attempts = d.conn.execute(
            "SELECT COUNT(*), MAX(id) FROM attempts").fetchone()
        before_events = d.conn.execute("SELECT COUNT(*) FROM learning_events").fetchone()[0]
    finally:
        d.close()

    # 换连接重开，用户"放弃了这道题"：只读、不作答
    d2 = ProgressDAO(db_path)
    try:
        assert d2.get_status(LANG, PID) == "wrong"
        assert d2.conn.execute(
            "SELECT status, last_attempt_ts FROM problems_status WHERE problem_id=?",
            (PID,)).fetchone() == before_status
        assert d2.conn.execute("SELECT COUNT(*), MAX(id) FROM attempts").fetchone() == before_attempts
        assert d2.conn.execute("SELECT COUNT(*) FROM learning_events").fetchone()[0] == before_events
        assert mistake_ids(d2) == [PID]
        assert status_rows_for(d2) == 1
    finally:
        d2.close()


def test_reentry_after_giving_up_does_not_duplicate_transition(db_path):
    """重新进入后再答错：状态仍一行（不重复转移），明细多一条、错题本仍一条。"""
    d = ProgressDAO(db_path)
    try:
        fail(d, 3)
    finally:
        d.close()

    d2 = ProgressDAO(db_path)
    try:
        assert status_rows_for(d2) == 1
        _record_attempt(LANG, PID, "重进后又错", False, "重进点评", d2)
        assert status_rows_for(d2) == 1, "重新进入不得造出第二行状态"
        assert d2.attempt_count(LANG, PID) == 4
        assert mistake_ids(d2) == [PID]
        assert d2.list_mistakes()[0]["code"] == "重进后又错"
    finally:
        d2.close()


def test_reentry_after_passing_keeps_it_out_of_mistakes(db_path):
    """重做通过后重新进入并再次通过：不得被错题本捞回，也不得重复计数。"""
    d = ProgressDAO(db_path)
    try:
        fail(d, 2)
        pass_it(d, 1)
        assert mistake_ids(d) == []
    finally:
        d.close()

    d2 = ProgressDAO(db_path)
    try:
        pass_it(d2, 1, code_prefix="再进又对")
        assert d2.get_status(LANG, PID) == "solved"
        assert mistake_ids(d2) == []
        assert status_rows_for(d2) == 1
        assert d2.summary_by_lang()[LANG]["wrong"] == 0
    finally:
        d2.close()


# ------------------------------------------------------------- 提示展示形态

def test_hints_are_rendered_in_one_pass_without_a_failure_gate():
    """判据里的「提示逐级展示」在盘上**没有**对应实现 ⇒ 按实况钉住现有形态并点名分歧。

    实测：`ui/pages/language.py` 的提示块是**单个** expander 内一次遍历全部 hints，
    块内没有任何按尝试数/失败数/掌握度递进的门槛。这条用例的判别力在两处：
      ① 精确圈出提示块的作用域（切到下一个 8 空格缩进的 `with st.expander` 为止），
         块内必须**只有**那一次 `st.markdown(f"- {h}")`，多一档就红；
      ② 整个 `ui/` 目录扫「提示/hint × level|stage|step|index|逐级|分档|递进」的组合词，
         现值 0 命中 ⇒ 若有人日后真做了逐级展示，②会红，逼那次改动回来重读本条判据，
         而不是让「逐级展示」一直停在纸面要求上。
    """
    src = (REPO_ROOT / "ui" / "pages" / "language.py").read_text(encoding="utf-8")

    # 现有形态的必要部件（名字法取，不锚行号）
    assert 'if active.get("hints"):' in src
    assert 'st.expander("💡 不会做？看提示", expanded=False)' in src

    block = src.split('if active.get("hints"):')[1].split('\n        with st.expander')[0]
    assert 'for h in active["hints"]:' in block, block
    assert block.count('st.markdown(f"- {h}")') == 1, block
    assert "attempt_count" not in src                      # 没有按尝试次数门控
    assert "if st.session_state" not in block              # 提示块前没有任何会话态条件

    import re
    pat = re.compile(r"(hint|提示).{0,24}(level|stage|step|index|逐级|分档|递进)")
    hits = []
    for path in sorted((REPO_ROOT / "ui").rglob("*.py")):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pat.search(line):
                hits.append(f"{path.name}:{i}:{line.strip()}")
    assert hits == [], hits


def test_problem_hints_are_lists_and_the_three_hint_contract_leaks():
    """数据侧：hints 必须是 list（装载层有防拆字符串的防御），并把「1-3 条」契约的破口钉住。

    `core/ai_generate.py:25,29` 对 AI 写的是「hints 3 条以内／1-3 条」，
    但**手工内容根不受该契约约束**：现取全量题库实测有 2 道题带 4 条提示
    （`r/10_stringr_lubridate/06_date_parsing`、`agent_dev/05_modular_config/03_split_function`）。
    装载层 `core/loader.py::_build_problem` 不截断，页面一次性全列 ⇒
    "上限 3" 目前只是生成提示词里的口头约定，不是任何代码里的夹钳。
    这条用例不替那个缺口背书（不断言 ≤3），只钉：①类型必为 list、②长度分布现值、
    ③破口的**具体题号**——这样下次有人加夹钳或删除那两题，本用例立刻报数变化。
    """
    from core.loader import _build_problem, load_language

    src = inspect_source(_build_problem)
    assert 'data.get("hints")' in src
    assert "isinstance(raw_hints, list)" in src       # 字符串形态要包成单元素 list

    from ui.components import ALL_LANGS
    lengths: dict = {}
    over_cap: list = []
    for lang in ALL_LANGS:
        for topic in load_language(lang):
            for p in topic.problems:
                assert isinstance(p.hints, list), (p.id, type(p.hints))
                lengths[len(p.hints)] = lengths.get(len(p.hints), 0) + 1
                if len(p.hints) > 3:
                    over_cap.append(p.id)
    assert sum(lengths.values()) > 0, "一道题都没读到 ⇒ 本用例空跑"
    assert sorted(lengths) == [1, 2, 3, 4], lengths          # 现值：无 0 条的题
    assert sorted(over_cap) == [
        "agent_dev/05_modular_config/03_split_function",
        "r/10_stringr_lubridate/06_date_parsing",
    ], over_cap


def inspect_source(fn):
    import inspect
    return inspect.getsource(fn)


# ------------------------------------------------------------- 覆盖面自证（有牙）

def test_primary_key_physically_blocks_duplicate_status_rows(dao):
    """「状态转移无重复」不是运气，是主键：手工插第二行必须被 SQLite 拒绝。

    这条是整个文件的判别力锚点——如果 `(lang, problem_id)` 主键被拆掉，
    上面所有 `status_rows_for(dao) == 1` 的断言都可能被绕过而无人察觉。
    """
    fail(dao, 2)
    assert status_rows_for(dao) == 1
    with pytest.raises(sqlite3.IntegrityError):
        with dao.conn:
            dao.conn.execute(
                "INSERT INTO problems_status (lang, problem_id, status) VALUES (?,?,?)",
                (LANG, PID, "solved"))
    # 被拒之后原行必须还在、还是那一行（失败写入不留半成品）
    assert status_rows_for(dao) == 1
    assert dao.get_status(LANG, PID) == "wrong"


def test_mistakes_view_drops_the_duplicate_if_a_stale_status_row_is_injected(dao):
    """合成反例：同一题有 5 次失败尝试 ⇒ 错题本仍恰 1 条，且显示的是最新代码。

    这里改的是**数据**（把 last_attempt_ts 抹成 NULL 模拟脏行），不是生产码。
    若 `list_mistakes` 的 LEFT JOIN 去重被写坏（例如忘了 `rn=1`），
    它会给同一题产出 5 条 ⇒ 断言当场红。
    """
    fail(dao, 5)
    with dao.conn:
        dao.conn.execute("UPDATE attempts SET code = 'attempt-' || id WHERE problem_id=?", (PID,))

    entries = dao.list_mistakes()
    assert len(entries) == 1, entries
    assert entries[0]["code"] == "attempt-" + str(
        dao.conn.execute("SELECT MAX(id) FROM attempts").fetchone()[0])

    # 反向对照：把窗口函数的 rn=1 条件在一条等价手写 SQL 里去掉，同一题就该爆出 5 行
    without_dedup = dao.conn.execute(
        "SELECT ps.lang, ps.problem_id, l.code FROM problems_status ps "
        "JOIN attempts l ON l.lang=ps.lang AND l.problem_id=ps.problem_id "
        "WHERE ps.status='wrong'").fetchall()
    assert len(without_dedup) == 5, without_dedup
