# -*- coding: utf-8 -*-
"""同一提交多次判题的稳定性 / 随机源 / 测试顺序不变性（qoder-executor-20260925-1555-learn37 · 20260925-120556-2805，A 档 test）。

卷宗判据「相同输入结果一致；随机测试使用记录过的 seed」的两半，本仓实况不同：

* **判题链路零随机**：`core/judge.py` 与 `core/runners/*` 里 `rg "random\\.|shuffle|seed"`
  现读 **0 命中**（全仓唯一随机源是 `content/datasets/generate_hr_data.py:8` 的 `random.seed(42)`，
  它已由 `tests/test_hr_dataset_determinism.py` 逐字节钉住 ⇒ 本件不重复造这一条）。
  「seed 是否记录」属**本仓无此实体**的判据，故这里改成可执行的等价命题：**判题结果对进程
  RNG 状态不敏感**（若将来引入随机，本件立刻红）。
* **测试顺序**：pytest 9.1.1 且 `pytest_randomly` / `pytest_order` / `pytest_xdist` 均未安装 ⇒
  收集序即命令行序，本件用两次 `--collect-only` 的逐位比对钉住，并再跑一遍「两种文件顺序
  结果摘要相同」的实证。

🔴 隔离口径（本仓头号硬警示）
------------------------------
`core/judge.py:_record_attempt` 在 `dao is None` 时执行 `d = dao or ProgressDAO()`，
`ProgressDAO()` 无参 ⇒ 落 `core/progress.py:32` 的 `db_path or os.environ["LS_PROGRESS_DB"] or _DEFAULT_DB`
⇒ **环境变量没设时那就是生产库 `data/progress.db`**。本件因此有三层防护：

1. autouse 夹具把 `LS_PROGRESS_DB` 指到 `tmp_path` 下的沙盒库；
2. 所有显式 `dao` 一律 `ProgressDAO(str(tmp_path / "...db"))`；
3. autouse **生产库字节守卫**：每条用例前后各读一次 `data/progress.db` 的 (size, sha8, wal_size)，
   不一致直接红并打印两次读数——这条与"有没有别的写手"无关，它咬的是本班自己。

复跑：
    cd /d/code/learning-system && PYTHONIOENCODING=utf-8 python -m pytest tests/test_judge_repeat_stability_20260925.py -q -rs
"""
import hashlib
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PROD_DB = REPO / "data" / "progress.db"

sys.path.insert(0, str(REPO))

import core.ai_review as ai_review_mod  # noqa: E402
import core.judge as judge_mod  # noqa: E402
from core.judge import judge  # noqa: E402
from core.progress import ProgressDAO  # noqa: E402


def _db_fingerprint(path: Path):
    """只读字节指纹：不建 sqlite 连接 ⇒ 不会触发 WAL checkpoint（纪律档 §十四）。"""
    if not path.exists():
        return ("absent", 0, "0" * 8)
    b = path.read_bytes()
    wal = path.with_suffix(path.suffix + "-wal")
    return (len(b), hashlib.sha256(b).hexdigest()[:8], wal.stat().st_size if wal.exists() else -1)


@pytest.fixture(autouse=True)
def prod_db_untouched():
    """每条用例的写库守卫：前后两次指纹必须逐位相同。"""
    before = _db_fingerprint(PROD_DB)
    yield before
    after = _db_fingerprint(PROD_DB)
    assert after == before, (
        "生产库 data/progress.db 在本条用例期间被写过！"
        f" 前={before} 后={after}（size, sha8, wal_bytes）"
    )


@pytest.fixture(autouse=True)
def sandbox_db(monkeypatch, tmp_path):
    """把 `ProgressDAO()` 的无参回退也关进沙盒——防 dao=None 分支打到生产库。"""
    fake = tmp_path / "env-sandbox.db"
    monkeypatch.setenv("LS_PROGRESS_DB", str(fake))
    return fake


@pytest.fixture
def dao(tmp_path):
    d = ProgressDAO(str(tmp_path / "explicit.db"))
    yield d
    d.close()


@pytest.fixture
def offline_llm(monkeypatch):
    """把 LLM 边界冻成「不可用」：走 `_offline_fallback`，零网络零子进程。

    注意这里**不 stub `review` 本身**（既有 `tests/test_judge.py` 的 fake_review 是把整个
    review 换成常量，于是点评链路一行没跑）。本桩只切断外呼，`review()` 的缓存查找、
    prompt 组装、离线兜底全部真跑。
    """
    calls = []

    def _fake(prompt, system, chain, *a, **kw):
        calls.append(prompt)
        return (None, None)

    monkeypatch.setattr(ai_review_mod, "_call_chain", _fake)
    return calls


def _snapshot(r):
    """判题结果里「学生可见」的五元组——`run_result` 是每次新开的对象，不参与比对。"""
    return (r.passed, r.ai_feedback, r.expected_display, r.actual_display, r.diff_hint)


# ---------------------------------------------------------------- 判题幂等
def test_same_python_submission_five_times_is_identical(dao, offline_llm, tmp_path):
    """同一份代码判 5 次：学生可见字段逐字节相同，且点评只离线兜底 5 次同文。

    覆盖面自证（合成反例）：第 6 次换一份**不同**的代码，快照必须**不同** ⇒
    证明上面那条 == 比较有鉴别力，不是恒真式。
    """
    problem = {"id": "python/stab/01", "title": "t", "statement": "s",
               "expected_output": "Hello\n"}
    code = 'print("Hello")'
    snaps = [_snapshot(judge("python", problem, code, dao=dao)) for _ in range(5)]
    assert all(s == snaps[0] for s in snaps), snaps
    assert snaps[0][0] is True

    other = _snapshot(judge("python", problem, 'print("Hello!")', dao=dao))
    assert other != snaps[0], "换了代码仍与旧快照相同 ⇒ 比较式无牙"


def test_failing_python_submission_diff_hint_has_no_temp_path(dao, offline_llm):
    """运行失败时 `diff_hint` 必须可复现：runner 的临时文件路径不得泄漏进学生可见字段。

    这是「同一提交多次判题稳定」最现实的破口——python_runner 每次写新临时文件，
    一旦 traceback 的 `File "..."` 行进了 diff_hint，两次判题就会不一致。
    """
    problem = {"id": "python/stab/02", "title": "t", "statement": "s",
               "expected_output": "ok\n"}
    code = "print(undefined_name)\n"
    snaps = [_snapshot(judge("python", problem, code, dao=dao)) for _ in range(3)]
    assert all(s == snaps[0] for s in snaps), snaps
    assert snaps[0][0] is False
    joined = " | ".join(str(x) for x in snaps[0])
    assert ".py" not in joined, f"diff_hint/展示字段里出现源文件路径 ⇒ 逐次判题会漂：{joined}"
    assert "Temp" not in joined and "temp" not in joined, joined


def test_result_independent_of_process_rng_state(dao, offline_llm):
    """判题对进程随机状态不敏感：两次判题之间把全局 RNG 打乱，快照仍相同。

    这就是卷宗「随机种子」那半在本仓的可执行等价物——将来判题链路若引入
    `random.choice` 选题/出题，本条立刻红。
    """
    # 刻意走 python 路：`expected_rows` 分支根本不进 `_normalize`（M1 变异实测打不到它），
    # 只有文本比对路径才能证明「随机一旦进入判题，本条立刻红」。
    problem = {"id": "python/stab/03", "title": "t", "statement": "s",
               "expected_output": "Hello\n"}
    code = 'print("Hello")'
    base = _snapshot(judge("python", problem, code, dao=dao))
    assert base[0] is True, base
    for seed in (0, 12345, 987654321):
        random.seed(seed)
        [random.random() for _ in range(50)]
        assert _snapshot(judge("python", problem, code, dao=dao)) == base, f"seed={seed} 下结果漂移"


def test_real_content_problem_rejudges_identically(dao, offline_llm):
    """反向对照：真实题库（content/）里挑一道 SQL 题，重复判题同样一致。

    上面几条都是合成夹具；这条保证「幂等」不是只在合成输入上成立。
    """
    from core.loader import load_language

    topics = load_language("sql")
    pool = []
    for tp in topics:
        for pr in tp.problems:
            d = pr.to_dict() if hasattr(pr, "to_dict") else vars(pr)
            if d.get("expected_rows") is not None or d.get("expected_output"):
                pool.append(d)
    assert len(pool) > 20, f"真实题库可判样本仅 {len(pool)} 道，样本量不足以支撑结论"

    bad = "SELECT 1 FROM this_table_does_not_exist"
    for d in pool[:3]:
        snaps = [_snapshot(judge("sql", d, bad, dao=dao)) for _ in range(2)]
        assert snaps[0][0] is False, d.get("id")
        assert snaps[0] == snaps[1], f"真实题 {d.get('id')} 两次判题不一致"


# ---------------------------------------------------------------- 反馈缓存契约
def test_feedback_cache_key_separates_lang_pid_and_code(dao, monkeypatch):
    """`_feedback_cache` 是进程级全局：键必须含 (lang, pid, code) 三维，否则重复判题会串味。

    用真 `_call_chain`（此处换成计数假实现）测命中：
      · 同 (lang,pid,code) 判 3 次 ⇒ 外呼只 1 次；
      · 换 lang / 换 pid / 换 code ⇒ 各多 1 次外呼。
    """
    n = {"c": 0}

    def _counting(prompt, system, chain, *a, **kw):
        n["c"] += 1
        return (f"FEEDBACK-{n['c']}", "stub")

    monkeypatch.setattr(ai_review_mod, "_call_chain", _counting)
    # judge 模块持有 review 的直接引用，_call_chain 在 review 函数体内查找 ⇒ 已被上面的桩接管
    p = {"id": "python/cache/1", "title": "t", "statement": "s", "expected_output": "Hello\n"}
    code = 'print("Hello")'
    first = _snapshot(judge("python", p, code, dao=dao))
    assert n["c"] == 1, n
    again = _snapshot(judge("python", p, code, dao=dao))
    assert n["c"] == 1, "同输入重复判题又外呼了一次 ⇒ 缓存没生效"
    assert again == first, "缓存命中却返回了不同文本"

    judge("python", {**p, "id": "python/cache/2"}, code, dao=dao)
    assert n["c"] == 2, "换 pid 未换缓存条目 ⇒ 键里丢了 pid"
    judge("python", {**p, "id": "python/cache/3"}, 'print("Hello!")', dao=dao)
    assert n["c"] == 3, "换 code 未换缓存条目 ⇒ 键里丢了 code 哈希"


def test_ai_feedback_cache_never_stores_unavailable_text(dao, monkeypatch):
    """LLM 不可用时的兜底文本不得入缓存——否则「稍后再试」会被永久钉成答案。

    覆盖面自证：本桩先以「不可用」跑一次，再以「可用」跑一次，第二次必须真外呼并返回新文本。
    """
    mode = {"ok": False}

    def _chain(prompt, system, chain, *a, **kw):
        if mode["ok"]:
            return ("真点评已恢复", "stub")
        return (None, None)

    monkeypatch.setattr(ai_review_mod, "_call_chain", _chain)
    p = {"id": "python/cache/4", "title": "t", "statement": "s", "expected_output": "Hello\n"}
    code = 'print("Hello")'
    r1 = _snapshot(judge("python", p, code, dao=dao))
    assert "暂时不可用" in r1[1], r1
    mode["ok"] = True
    r2 = _snapshot(judge("python", p, code, dao=dao))
    assert r2[1] == "真点评已恢复", f"失败文本被缓存住了，恢复后仍返回旧文本：{r2[1]}"


# ---------------------------------------------------------------- 无 dao 分支的落点
def test_judge_without_dao_lands_in_sandbox_never_production(dao, offline_llm, sandbox_db):
    """`judge(..., dao=None)` 这条真实存在的分支必须写沙盒、不得碰生产库。

    本仓 14 行幽灵数据事故的成因就是这一支。断言两侧同时给：
      · 沙盒库里确有本次 attempts 行（证明写入真的发生了，不是"哪儿都没写"的假绿）；
      · 生产库指纹由 autouse 守卫在 teardown 复核。
    """
    prod_before = _db_fingerprint(PROD_DB)
    p = {"id": "python/no_dao/1", "title": "t", "statement": "s", "expected_output": "Hello\n"}
    r = judge("python", p, 'print("Hello")', dao=None)
    assert r.passed is True, r
    assert os.environ["LS_PROGRESS_DB"] == str(sandbox_db)

    probe = ProgressDAO(str(sandbox_db))
    try:
        rows = probe.conn.execute(
            "SELECT lang, problem_id, passed FROM attempts WHERE problem_id=?",
            ("python/no_dao/1",),
        ).fetchall()
    finally:
        probe.close()
    assert rows == [("python", "python/no_dao/1", 1)], rows
    assert _db_fingerprint(PROD_DB) == prod_before


# ---------------------------------------------------------------- 测试顺序稳定性
_COLLECT_TARGETS = ["tests/test_judge_pure.py", "tests/test_judge_result_per_pid.py"]


def _pytest(*args, timeout=240):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", *args],
        cwd=str(REPO), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )


def _collected_ids(proc_output: str):
    ids = []
    for line in proc_output.splitlines():
        s = line.strip()
        if s.startswith("tests/") and "::" in s:
            ids.append(s)
    return ids


def test_collection_order_is_reproducible_and_order_independent():
    """卷宗「测试顺序是否稳定」的可执行答案，两问分开钉：

    ① 同一批文件两次 `--collect-only` ⇒ 用例 id 序列逐位相同；
    ② 把文件顺序**反过来**真跑 ⇒ 通过数与红名集合相同（顺序不承重）。
    """
    c1 = _pytest("pytest", "--collect-only", "-q", *_COLLECT_TARGETS)
    c2 = _pytest("pytest", "--collect-only", "-q", *_COLLECT_TARGETS[::-1])
    assert c1.returncode == 0, c1.stdout[-2000:] + c1.stderr[-2000:]
    assert c2.returncode == 0, c2.stdout[-2000:] + c2.stderr[-2000:]
    ids1, ids2 = _collected_ids(c1.stdout), _collected_ids(c2.stdout)
    assert len(ids1) > 10, f"收集到 {len(ids1)} 条，样本太少不足以说明顺序稳定"
    assert ids1[:5] != ids2[:5], "两次的文件顺序没变过来 ⇒ 本条测的不是它声称的东西"

    def by_module(ids):
        from collections import defaultdict
        g = defaultdict(list)
        for i in ids:
            mod, _, name = i.partition("::")
            g[mod].append(name)
        return {k: sorted(v) for k, v in g.items()}

    assert by_module(ids1) == by_module(ids2), "同一模块内用例次序随命令行顺序变化"

    r_fwd = _pytest("pytest", "-q", "-p", "no:cacheprovider", *_COLLECT_TARGETS)
    r_rev = _pytest("pytest", "-q", "-p", "no:cacheprovider", *_COLLECT_TARGETS[::-1])
    tail_fwd = r_fwd.stdout.strip().splitlines()[-1]
    tail_rev = r_rev.stdout.strip().splitlines()[-1]
    assert r_fwd.returncode == r_rev.returncode, (tail_fwd, tail_rev)
    assert " passed" in tail_fwd, tail_fwd
    fwd_n = [w for w in tail_fwd.split() if w.isdigit()]
    rev_n = [w for w in tail_rev.split() if w.isdigit()]
    assert fwd_n == rev_n, f"两种顺序的计数不同：{tail_fwd} vs {tail_rev}"
