# -*- coding: utf-8 -*-
"""冷启动关键流程链：选题 → 编辑 → 运行 → 判题 → 反馈 → 进度保存，以及测试数据可重置
（qoder-executor-20260925-1555-learn37 · 20260925-120607-9d3d）。

⚠ 档位分歧（点名）：本单**卷宗正文写「风险档：B」，派单横幅写 A**。按纪律档 §九 与横幅自身
「以卷宗正文为准、冲突时从严」的口径，本班**按 A 档执行**：只加测试 + 登记缺陷，零生产行为改动。

七环节在本仓的实况（逐条实测，见 result「证据」节）：

| 卷宗环节 | 实况 | 本件处置 |
|---|---|---|
| 登录 | **本仓无此实体**（单人桌面应用；`attempts` 等 8 张表无 user/login 列，UI 无登录入口） | 写成**探针**钉住"不存在"，将来真加了登录会红 ⇒ 判据届时才有对象 |
| 选题 | `core.recommend.recommend(n, dao)` 空库可直接推 | 冷启动可推 + 字段契约 |
| 编辑 | 题目 `starter_code` 是编辑器初值来源；widget 层由既有 `tests/test_app_flow.py`（AppTest 真跑 `app.py`）覆盖 | 本件钉数据层初值契约，不重复造 AppTest |
| 运行 | `core.runners.*` 四语言，本件走 python / sql 两条真实路径 | 全链真跑（无 stub） |
| 判题 | `core.judge.judge` | 全链真跑 |
| 反馈（**错误定位**） | python 折算 runner 引导行 ⇒ 报「第 3 行」而非引导段行号；sql 报「第 N 行第 M 列」 | 两条定位各钉一例（卷宗「错误定位」判据的正面回答） |
| 进度保存 | `attempts` / `problems_status` / `review_state` / `learning_events` 四表 | 逐表点名 + 重开连接复读 |

🔴 隔离（与同批 `-2805` / `-0f02` 两件同一套三层防护）：
autouse 把 `LS_PROGRESS_DB` 指到 `tmp_path` 沙盒（防 `core/judge.py:199` 的 `dao or ProgressDAO()` 打到生产库）
+ 显式 `ProgressDAO(str(tmp_path / ...))` + 每条用例前后复点 `data/progress.db` 字节指纹。
「测试数据可重置」= 每条用例天然拿全新库，本件**不删任何数据行**（真删属人工闸）。

复跑：
    cd /d/code/learning-system && PYTHONIOENCODING=utf-8 python -m pytest tests/test_cold_start_key_flows_20260925.py -q -rs
"""
import hashlib
import sqlite3
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PROD_DB = REPO / "data" / "progress.db"

import core.ai_review as ai_review_mod  # noqa: E402
from core.judge import judge  # noqa: E402
from core.progress import ProgressDAO  # noqa: E402


def _db_fingerprint(path: Path):
    if not path.exists():
        return ("absent", 0, "0" * 8)
    b = path.read_bytes()
    wal = path.with_suffix(path.suffix + "-wal")
    return (len(b), hashlib.sha256(b).hexdigest()[:8], wal.stat().st_size if wal.exists() else -1)


@pytest.fixture(autouse=True)
def prod_db_untouched():
    before = _db_fingerprint(PROD_DB)
    yield before
    after = _db_fingerprint(PROD_DB)
    assert after == before, f"生产库被本班用例写过！前={before} 后={after}"


@pytest.fixture(autouse=True)
def sandbox_env(monkeypatch, tmp_path):
    monkeypatch.setenv("LS_PROGRESS_DB", str(tmp_path / "env-sandbox.db"))


@pytest.fixture
def cold_db(tmp_path):
    """冷启动库：全新文件、零行。"""
    d = ProgressDAO(str(tmp_path / "cold.db"))
    yield d
    d.close()


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    """断线态跑全链：反馈落到离线兜底，链路仍可判定 ⇒ 关键流程不依赖网络。"""
    monkeypatch.setattr(ai_review_mod, "_call_chain", lambda *a, **kw: ("", None))


def _rows(dao, table):
    return dao.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


# -------------------------------------------------------- 冷启动 + 「登录」探针
def test_cold_start_db_is_empty_and_repo_has_no_login_entity(cold_db):
    """冷启动定义钉死：六张数据表全零行；同时否证「登录」——库里没有任何身份列。

    实测校正：新建库里 `schema_meta` **不是**零行——`ProgressDAO.__init__` 会写
    `('schema_version','2')`（core/progress.py:133-138），那是建表记账不是业务数据，
    故把它单独钉成读数（版本号漂了本条会红＝迁移哨兵）。
    若将来引入登录/多用户，`user`/`login` 列或新表会出现 ⇒ 身份列探针转红，判据才重新有对象。
    """
    tables = {r[0] for r in cold_db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    data_tables = {"attempts", "problems_status", "review_state",
                   "learning_events", "meta", "rubric_scores"}
    assert data_tables <= tables, f"缺表：{data_tables - tables}"

    for t in sorted(data_tables):
        assert _rows(cold_db, t) == 0, f"冷启动库 {t} 有残留行"

    bookkeeping = cold_db.conn.execute("SELECT key, value FROM schema_meta").fetchall()
    assert bookkeeping == [("schema_version", "2")], \
        f"建表记账变化（迁移版本漂了？原口径 [('schema_version','2')]）：{bookkeeping}"

    id_cols = set()
    for t in tables:
        if t.startswith("sqlite_"):
            continue
        for r in cold_db.conn.execute(f"PRAGMA table_info({t})").fetchall():
            id_cols.add(r[1].lower())
    assert not {x for x in id_cols if "user" in x or "login" in x or "account" in x}, \
        f"库里出现身份列 {sorted(id_cols)}——「登录」判据已有对象，需改判据"


# -------------------------------------------------------- 选题（冷启动可推）
def test_recommend_on_cold_db_returns_wellformed_items(cold_db):
    """环节①选题：空库也能推出题，且每条带可解释的 reason_code。"""
    from core.recommend import recommend

    rec = recommend(5, dao=cold_db)
    assert len(rec) == 5, f"冷启动推荐只拿到 {len(rec)} 条"
    for item in rec:
        assert item["problem_id"] and item["lang"], item
        assert item["reason"] and item["reason_code"], f"推荐项缺归因：{item}"
    assert recommend(5, dao=cold_db) == rec, "冷启动两次推荐结果不同 ⇒ 选题层引入了不稳定输入"


def test_topic_selection_moves_after_progress_is_saved(cold_db):
    """选题必须响应进度：把榜首那道题记为已通过之后，它不再占据推荐位。

    覆盖面自证：先钉「判前它确实在榜」（否则"不在榜"是恒真）。
    这里刻意走 DAO 结算层而非 `judge`——真实榜首题的期望输出未必能靠一行 `print` 命中，
    判分未通过反而会把它送进「错题复习」推荐位，那样测的就不是选题响应进度了。
    """
    from core.recommend import recommend

    rec = recommend(5, dao=cold_db)
    target = rec[0]["problem_id"]
    assert recommend(5, dao=cold_db)[0]["problem_id"] == target, "冷启动推荐本身不稳定，后面的断言没有意义"
    assert target in {r["problem_id"] for r in rec}

    cold_db.record_attempt_and_status("python", target, "x", True, "ok")
    cold_db.update_review_state("python", target, True)
    after = {r["problem_id"] for r in recommend(5, dao=cold_db)}
    assert target not in after, f"已通过的 {target} 仍占推荐位（未响应进度）"
    assert after, "记完进度后推荐直接空了——那是另一个缺陷，不是本条要读的结论"


# -------------------------------------------------------- 编辑 → 运行 → 判题 → 反馈 → 保存
def test_full_chain_on_real_content_problem_persists_every_layer(cold_db):
    """环节②③④⑤⑥串跑：真实题库取题 → starter_code 作编辑初值 → 运行 → 判题 → 反馈 → 四表落库。

    全程零 stub（`_call_chain` 只被冻成"断线"，仍真跑 review 与离线兜底）。
    """
    from core.loader import find_problem, load_language

    # 取一道真实 python 题（有 starter_code 与 expected_output）
    picked = None
    for tp in load_language("python"):
        for pr in tp.problems:
            d = pr.to_dict() if hasattr(pr, "to_dict") else vars(pr)
            if d.get("expected_output") and (d.get("starter_code") or "").strip():
                picked = d
                break
        if picked:
            break
    assert picked is not None, "真实题库里没有带 starter_code 的 python 题，本判据无对象"
    pid = picked["id"]
    assert find_problem("python", pid) is not None, f"{pid} 取不回原题，选题↔编辑接缝断了"

    starter = picked["starter_code"]
    run_res = None
    from core.judge import _RUNNERS
    run_res = _RUNNERS["python"].run(starter, stdin="", expected={"expected_output": ""})
    assert run_res is not None and hasattr(run_res, "ok") and hasattr(run_res, "stdout"), \
        "环节③运行：RunResult 契约字段缺失"

    r = judge("python", picked, starter, dao=cold_db)
    assert r.diff_hint or r.actual_display is not None

    assert _rows(cold_db, "attempts") == 1, "环节⑥进度保存：attempts 没落"
    assert cold_db.get_status("python", pid) in ("solved", "wrong")
    assert _rows(cold_db, "review_state") == 1, "环节⑥：review_state 没落"
    assert _rows(cold_db, "learning_events") >= 2, "环节⑥：learning_events 没落"
    assert r.ai_feedback, "环节⑤反馈：空串"
    assert "暂时不可用" in r.ai_feedback, f"断线态应落离线兜底：{r.ai_feedback}"


# -------------------------------------------------------- 反馈：错误定位两条路
def test_python_runtime_error_is_located_at_student_line_not_runner_preamble(cold_db):
    """环节⑤错误定位：python 的行号必须折算掉 runner 注入的引导段。

    学生代码第 3 行出错 ⇒ 反馈里必须写「第 3 行」。若折算失效会报成引导段之后的偏移行号
    （如「第 12 行」），学生会在编辑器里找不到那一行——这正是本判据要防的。
    """
    from core.runners import error_feedback as ef

    code = "a = 1\nb = 2\nprint(a / c)\n"
    p = {"id": "python/locate/1", "title": "t", "statement": "s", "expected_output": "3\n"}
    r = judge("python", p, code, dao=cold_db)
    assert r.passed is False
    assert ef.PREAMBLE_LINES > 0, "引导段行数为 0 ⇒ 折算逻辑无对象，本条测不到东西"
    assert "第 3 行" in r.diff_hint, f"行号没折算回学生编辑器行号（引导段占 {ef.PREAMBLE_LINES} 行）：{r.diff_hint}"
    assert "NameError" in r.diff_hint, r.diff_hint
    assert ef.PREAMBLE_LINES + 3 not in [int(x) for x in _nums(r.diff_hint)], \
        f"反馈里仍带未折算的绝对行号：{r.diff_hint}"


def test_sql_wrong_answer_is_located_at_row_and_column(cold_db):
    """环节⑤错误定位（SQL 路）：报「第 N 行第 M 列」并给出实际/期望值。"""
    p = {"id": "sql/locate/1", "title": "t", "statement": "s",
         "setup_sql": "CREATE TABLE t(a INTEGER, b INTEGER); "
                      "INSERT INTO t VALUES (1,10),(2,20);",
         "expected_rows": [[1, 99], [2, 20]]}
    r = judge("sql", p, "SELECT a, b FROM t ORDER BY a", dao=cold_db)
    assert r.passed is False
    assert "第 1 行第 2 列" in r.diff_hint, r.diff_hint
    assert "99" in r.diff_hint and "10" in r.diff_hint, f"定位里没带实际/期望值：{r.diff_hint}"

    ok = judge("sql", {**p, "id": "sql/locate/2", "expected_rows": [[1, 10], [2, 20]]},
               "SELECT a, b FROM t ORDER BY a", dao=cold_db)
    assert ok.passed is True, f"反向对照失败（同一条 SQL 对正确期望也应通过）：{ok.diff_hint}"
    assert ok.diff_hint == "", ok.diff_hint


def _nums(s):
    import re
    return re.findall(r"\d+", s)


# -------------------------------------------------------- 边界：空提交不结算
def test_empty_submission_is_rejected_without_settling(cold_db):
    """空白代码不得写 attempts（否则学生点一下就掉一次正确率）。"""
    p = {"id": "python/empty/1", "title": "t", "statement": "s", "expected_output": "x\n"}
    r = judge("python", p, "   \n", dao=cold_db)
    assert r.passed is False and r.diff_hint == "代码为空", r
    assert _rows(cold_db, "attempts") == 0, "空提交被计了一次作答"
    assert cold_db.get_status("python", p["id"]) == "unseen"
    assert _rows(cold_db, "learning_events") == 0

    judge("python", {**p, "id": "python/empty/2"}, 'print("x")', dao=cold_db)
    assert _rows(cold_db, "attempts") == 1, "对照失败：写库通路本身不通"


# -------------------------------------------------------- 进度保存可复读 + 数据可重置
def test_saved_progress_is_readable_from_a_fresh_connection(cold_db, tmp_path):
    """环节⑥进度保存的验收口径：换一条连接（模拟重启）后读数一致。"""
    p = {"id": "python/persist/1", "title": "t", "statement": "s", "expected_output": "Hello\n"}
    judge("python", p, 'print("Hello")', dao=cold_db)
    before = (cold_db.get_status("python", p["id"]), _rows(cold_db, "attempts"))
    assert before == ("solved", 1), before

    other = ProgressDAO(str(tmp_path / "cold.db"))
    try:
        assert other.get_status("python", p["id"]) == "solved"
        assert _rows(other, "attempts") == 1
        assert _rows(other, "review_state") == 1
    finally:
        other.close()


def test_two_sandboxes_are_isolated_and_resettable(cold_db, tmp_path):
    """「测试数据可重置」的可执行断言：两个沙盒库互不串写，重开即是冷启动。

    这条同时是本仓头号事故的哨兵——若某处回退到默认库（生产库），两侧会同时看到数据。
    """
    b_path = str(tmp_path / "second.db")
    b = ProgressDAO(b_path)
    try:
        judge("python", {"id": "python/iso/A", "title": "t", "statement": "s",
                         "expected_output": "Hello\n"}, 'print("Hello")', dao=cold_db)
        assert _rows(b, "attempts") == 0, "两个沙盒串了 ⇒ 有代码路径绕过显式 dao"
        judge("python", {"id": "python/iso/B", "title": "t", "statement": "s",
                         "expected_output": "Hello\n"}, 'print("Hello")', dao=b)
        assert {r[0] for r in cold_db.conn.execute("SELECT problem_id FROM attempts")} == {"python/iso/A"}
        assert {r[0] for r in b.conn.execute("SELECT problem_id FROM attempts")} == {"python/iso/B"}
    finally:
        b.close()

    # 重置＝换新文件：立刻回到零行冷启动
    fresh = ProgressDAO(str(tmp_path / "third.db"))
    try:
        assert _rows(fresh, "attempts") == 0 and _rows(fresh, "learning_events") == 0
        assert fresh.db_path != cold_db.db_path
        assert fresh.db_path != str(PROD_DB)
    finally:
        fresh.close()
    assert _rows(cold_db, "attempts") == 1, "新库的建立改动了旧库 ⇒ 隔离不成立"


def test_progress_db_arg_never_falls_back_to_production(tmp_path):
    """`ProgressDAO()` 无参时的落点由 `LS_PROGRESS_DB` 决定；显式路径优先。

    覆盖面自证：无参构造必须落在 autouse 沙盒（不是 data/progress.db），
    且显式传入的路径胜出。
    """
    import os
    env_target = os.environ["LS_PROGRESS_DB"]
    assert env_target.endswith("env-sandbox.db"), env_target
    assert PROD_DB.name not in env_target

    implicit = ProgressDAO()
    try:
        assert implicit.db_path == env_target, implicit.db_path
    finally:
        implicit.close()
    explicit = ProgressDAO(str(tmp_path / "explicit-win.db"))
    try:
        assert explicit.db_path == str(tmp_path / "explicit-win.db")
    finally:
        explicit.close()
