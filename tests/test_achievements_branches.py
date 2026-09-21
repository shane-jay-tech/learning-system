# -*- coding: utf-8 -*-
"""achievements 三条未覆盖分支补测（d914-68 T6）：半程成就 / 路径成就 / 事件上报失败。

桩法照抄 _tmp/night-feed/probe_achievements.py（已验证可触发分支），但改用
monkeypatch.patch 模块属性（check_achievements 是函数内 import，patch 目标必须是
core.loader.load_language / core.paths.load_all_paths）。DAO 一律 :memory:。
断言一律用 in / not in newly，不断言精确相等（streak 等环境成就可能共存）。
"""
import logging

import pytest

from core.achievements import check_achievements
from core.loader import Problem, Topic
from core.progress import ProgressDAO


def _fake_load(lang, content_dir=None):
    fake_topic = Topic(slug="01_x", title="X", lesson_md="# X", problems=[
        Problem(id="python/01_x/p1", title="t", topic="x", difficulty=1, tags=[],
                statement="s", starter_code="c", expected_output="o")])
    return [fake_topic]


def _fake_paths():
    """三条假路径：
    - agent_mastery / people_analytics：各 1 个可全通里程碑 → 覆盖 path_agent_done
      与 path_pa_done 两条 append 分支；
    - pa_probe：milestone 指向不存在的 topic（python/99_z）→ 覆盖「topics 不可解析
      → all_done=False + continue」防御分支（:126-127）。"""
    def make_path(pid, topics):
        return type("P", (), {"id": pid, "milestones": [
            type("M", (), {"id": "a0", "topics": topics})()]})()
    return [
        make_path("agent_mastery", ["python/01_x"]),
        make_path("pa_probe", ["python/99_z"]),
        make_path("people_analytics", ["python/01_x"]),
    ]


@pytest.fixture()
def stubbed_env(monkeypatch):
    monkeypatch.setattr("core.loader.load_language", _fake_load)
    monkeypatch.setattr("core.paths.load_all_paths", _fake_paths)


def _seed_three_langs(dao: ProgressDAO):
    """python / sql / agent_dev 各过 1 题 → 触发三个 *_half 与 multi_lang 前提。"""
    dao.record_attempt_and_status("python", "p1", "x=1", True, "ok")
    dao.record_attempt_and_status("sql", "s1", "SELECT 1", True, "ok")
    dao.record_attempt_and_status("agent_dev", "a1", "step 1", True, "ok")


def test_case_a_half_achievements_fire(stubbed_env):
    dao = ProgressDAO(":memory:")
    _seed_three_langs(dao)
    dao.milestone_progress = lambda items: {"pct": 1.0}
    newly = check_achievements(dao)
    assert "python_half" in newly
    assert "sql_half" in newly
    assert "agent_half" in newly


def test_case_b_path_achievements_threshold(stubbed_env):
    dao = ProgressDAO(":memory:")
    _seed_three_langs(dao)
    dao.milestone_progress = lambda items: {"pct": 1.0}
    newly = check_achievements(dao)
    assert "path_agent_done" in newly
    assert "path_first_milestone" in newly

    # 阈值边界：pct < 1.0 时两者都不得出现
    dao2 = ProgressDAO(":memory:")
    dao2.record_attempt_and_status("python", "p1", "x=1", True, "ok")
    dao2.milestone_progress = lambda items: {"pct": 0.5}
    newly2 = check_achievements(dao2)
    assert "path_agent_done" not in newly2
    assert "path_first_milestone" not in newly2


def test_case_c_idempotent_second_call_empty(stubbed_env):
    dao = ProgressDAO(":memory:")
    _seed_three_langs(dao)
    dao.milestone_progress = lambda items: {"pct": 1.0}
    first = check_achievements(dao)
    assert first, "首次应有成就入账"
    second = check_achievements(dao)
    assert second == [], "第二次调用不应重复发放"


def test_case_d_emit_event_failure_does_not_crash(stubbed_env, caplog):
    dao = ProgressDAO(":memory:")
    _seed_three_langs(dao)
    dao.milestone_progress = lambda items: {"pct": 1.0}

    def raiser(*args, **kwargs):
        raise RuntimeError("telemetry down")

    dao.emit_event = raiser
    with caplog.at_level(logging.DEBUG):
        newly = check_achievements(dao)
    assert newly, "事件上报失败不影响成就发放"
    assert any("解锁事件上报失败" in r.message for r in caplog.records
               if r.levelno == logging.DEBUG)


# ---------------------------------------------------------------------------
# l922-09：_get_earned / _mark_earned 这一对私有函数的直钉补测（4 例）。
# 开工前实测：`grep -rn "_get_earned\|_mark_earned" tests/` 0 命中 —— 上面的 case_a/b/d
# 全走 check_achievements 顶层，从未单独打过这对存取函数。
# 存储契约（core/achievements.py:213-223）：meta["achievements_earned"] = ",".join(sorted(ids))，
# 读侧 raw.split(",") ⇒ 逗号是唯一分隔符，幂等全靠"先读成 set 再 add 再排序回写"。
# 落点说明：任务书把产出写成"新建本文件"，但它开工前已存在且被 git 跟踪（104 行 d914-68 的分支补测），
# 故按同文件加例处理，不覆盖写。
# ---------------------------------------------------------------------------


def _meta_raw(dao):
    return dao.get_meta("achievements_earned", "")


def test_get_earned_空库返回空set():
    """两种"空"都要落到 set()：① meta 行根本不存在（get_meta 给 default ""）；
    ② meta 行存在但值为空串。只钉一条，另一条被改成返回 {""} 也不会红。"""
    from core.achievements import _get_earned
    dao = ProgressDAO(":memory:")
    try:
        assert _get_earned(dao) == set()
        assert isinstance(_get_earned(dao), set)
        dao.set_meta("achievements_earned", "")
        assert _get_earned(dao) == set(), "空串被 split 成 [''] 了"
    finally:
        dao.close()


def test_mark_earned_幂等():
    """同一 aid 连标三次：集合不涨、存储串逐字节不变（sorted 回写必须与上一次相同）。"""
    from core.achievements import _mark_earned, _get_earned
    dao = ProgressDAO(":memory:")
    try:
        _mark_earned(dao, "streak_3")
        first = _meta_raw(dao)
        for _ in range(2):
            _mark_earned(dao, "streak_3")
        assert _get_earned(dao) == {"streak_3"}
        assert _meta_raw(dao) == first, (_meta_raw(dao), first)
    finally:
        dao.close()


def test_mark_earned_后立即可读():
    """标完立刻读得到；多成就按 sorted 落串（读侧不依赖顺序，写侧顺序决定 diff 稳定性）。"""
    from core.achievements import _mark_earned, _get_earned
    dao = ProgressDAO(":memory:")
    try:
        for aid in ("streak_30", "cpp_first", "streak_3"):   # 故意乱序写入
            _mark_earned(dao, aid)
            assert aid in _get_earned(dao), (aid, _get_earned(dao))
        earned = _get_earned(dao)
        assert earned == {"streak_30", "cpp_first", "streak_3"}
        assert _meta_raw(dao) == ",".join(sorted(earned)) == "cpp_first,streak_3,streak_30"
    finally:
        dao.close()


def test_逗号是编码分隔符_成就目录必须无逗号id():
    """含逗号的 id 会静默裂成两个成就 ⇒ 把"22 个 id 全部不含逗号"这个前提钉住，
    并用内存桩直接演示违反前提的后果，证明第一条断言不是凑数。"""
    from core.achievements import ACHIEVEMENTS, _mark_earned, _get_earned
    bad = [a.id for a in ACHIEVEMENTS if "," in a.id]
    assert bad == [], f"成就 id 含逗号，CSV 编码会被撕裂：{bad}"
    assert len({a.id for a in ACHIEVEMENTS}) == len(ACHIEVEMENTS), "成就 id 有重复"
    dao = ProgressDAO(":memory:")
    try:
        _mark_earned(dao, "a,b")     # 反例
        assert _get_earned(dao) == {"a", "b"}, "含逗号 id 的裂解行为已变，须同步改本注释"
    finally:
        dao.close()
