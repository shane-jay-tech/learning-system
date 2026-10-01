# -*- coding: utf-8 -*-
"""导入成功后「确认导入」二次点击不得把只追加表翻倍（l923-09）。

现场锚点（l930-18 现取订正，原 :289-290/:292 指针随头部扩展漂移，现值 :377/:381）：
  - `ui/pages/dashboard.py:377` `uploaded = st.file_uploader("选择之前导出的 .json 文件", …,
    key="data_import_uploader")`
  - `:381` `if st.button("确认导入", type="primary", key="data_import_confirm")`
  - 上游事实来源 `tests/test_data_portability.py:46-59`（l922 系列的 by-design 断言
    `dao.total_attempts() == before * 2`）⇒ **append 表在 `import_all` 层面刻意不去重**，
    本单不动那一层（改它＝改判分/统计口径的邻域，且会把那条在册断言弄红）。

缺陷机制（l922-105 遗留问题原文）：streamlit 的 `file_uploader` 控件态由 key 持久化，
导入成功后那个文件**仍在原处**，回显那一帧里 expander 还展开着、按钮还能再按一次
⇒ 同一份字节被 `import_json` 合并第二遍，attempts / learning_events / rubric_scores 翻倍。

修法（本单实装）：成功分支写 `session_state["_import_consumed_fp"] = sha256(字节)`，
同一次会话里同指纹的第二次确认**只提示不写库**（`components.render_notice` 出一句 warning）。
任务书首选的「清 uploader 键」没照做，原因写在生产码注释里（l930-18 已按 l927-31 实测
口径改写）：**赋值**会抛（守卫只挂 `__setitem__`）；pop 不抛但前端可能仍回送文件；
换 key 的陈旧 user-key 短驻留约 2 帧后被 stale-widget 回收（≈2 个、非无界）。
结论绑 streamlit 1.58.0，换版本需重跑 probe 两件。

手法沿用同族档：真 `ProgressDAO`（tmp_path 真 sqlite）＋ FakeStreamlit 桩，
`file_uploader` 与按钮态由 `_wire.render()` 逐帧注入。不连真实 Streamlit、不联网。
⚠️ 本文件的 warning 断言依赖 `components.st` 与 `dashboard_page.st` **同时**被 patch
   （`render_notice` 住在 ui.components，只 patch 页面侧就一条都录不到＝绿灯零覆盖）。
复跑：python -m pytest tests/test_import_dedup.py -q
"""
import json

import core.data_portability as dp
from core.progress import ProgressDAO

from tests.test_dashboard_import_feedback import (
    OK_HEAD, UPLOAD_LABEL, _pkg, _Upload, _wire,
)

SKIP_MARK = "已跳过重复导入"
APPEND_TABLES = ("attempts", "learning_events", "rubric_scores")


def _rows(dao, table):
    return dao.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _append_counts(dao):
    return {t: _rows(dao, t) for t in APPEND_TABLES}


def _pkg_with_rubric():
    """三张只追加表**各带行**的包：rubric_scores 在 l922-105 的夹具里是空的，
    本单的核心风险面正是它也会翻倍，所以自带一份三表齐全的包（不改别人的夹具）。"""
    pkg = _pkg()
    pkg["data"]["rubric_scores"] = [
        {"lang": "python", "problem_id": "python/01_x/01_p", "attempt_id": 1,
         "dimension": "清晰度", "score": 80, "comment": "", "prompt_version": "v1",
         "model": "m", "ts": "2026-09-20 09:00:00"},
        {"lang": "python", "problem_id": "python/01_x/02_p", "attempt_id": 2,
         "dimension": "完整性", "score": 61, "comment": "", "prompt_version": "v1",
         "model": "m", "ts": "2026-09-20 09:30:00"},
    ]
    return pkg


def _warnings(fake):
    return [str(c[1][0]) for c in fake.calls if c[0] == "warning"]


def test_second_confirm_on_the_same_file_appends_nothing(tmp_path, monkeypatch):
    """核心例（完成标准 ①）：同一份文件连点两次「确认导入」，第二次三张只追加表**行数一字不动**。

    第一下：attempts 2 / learning_events 1 / rubric_scores 2 真的写进去；
    第二下（uploader 里那个文件还在、按钮还能按）：库内数字必须与第一后完全相同，
    且这一帧出现「已跳过重复导入」的 warning、不再冒成功文案、不触发 rerun。
    """
    dao = ProgressDAO(str(tmp_path / "dedup1.db"))
    try:
        fake, render, notices = _wire(monkeypatch, dao)
        upload = _Upload(_pkg_with_rubric())

        render()                                        # 先跑一帧空白页
        first = render(upload=upload, confirm=True)
        assert first["reruns"] == 1, "第一次确认应当照常导入＋rerun（现行行为不变）"
        after_first = _append_counts(dao)
        assert after_first == {"attempts": 2, "learning_events": 1, "rubric_scores": 2}, \
            f"前提：第一次导入要真的把三张 append 表各写进行，否则本例是空断言（实得 {after_first}）"
        assert not notices and _warnings(fake) == []

        echo = render()                                 # rerun 后那一帧：成功回显
        assert [m for m in echo["success"] if OK_HEAD in m]
        assert _warnings(fake) == [], "正常回显帧不该冒跳过提示"

        second = render(upload=upload, confirm=True)     # ← 用户第二次点同一个文件
        assert _append_counts(dao) == after_first, \
            f"第二次确认把只追加表翻倍了：{after_first} → {_append_counts(dao)}"
        hits = [w for w in _warnings(fake) if SKIP_MARK in w]
        assert len(hits) == 1, f"应恰一条跳过提示，实得 {_warnings(fake)}"
        assert not [m for m in second["success"] if OK_HEAD in m], "被拦下那帧不得再报导入完成"
        assert second["reruns"] == 0, "跳过分支不该 rerun（提示要当场看得见）"
        assert not notices, "跳过不是失败，别走 render_error_notice"
    finally:
        dao.close()


def test_guard_is_per_content_not_a_one_shot_lock(tmp_path, monkeypatch):
    """防重按**内容指纹**：拦下同字节后，换一份内容不同的文件仍须照常导入（防误伤）。

    顺带钉「键控表仍按 l922-105 语义合并」：第二份包只带 1 条答题，attempts 从 2 → 3
    （append 表逐条追加），而 problems_status/review_state 是同键覆盖 ⇒ 行数不涨。
    """
    dao = ProgressDAO(str(tmp_path / "dedup2.db"))
    try:
        fake, render, notices = _wire(monkeypatch, dao)
        upload = _Upload(_pkg_with_rubric())
        render(upload=upload, confirm=True)
        render()
        render(upload=upload, confirm=True)
        assert SKIP_MARK in "".join(_warnings(fake)), "先确认真的进入过拦截路径"
        before = _append_counts(dao)

        pkg2 = _pkg_with_rubric()
        pkg2["data"]["attempts"] = pkg2["data"]["attempts"][:1]
        pkg2["data"]["rubric_scores"] = pkg2["data"]["rubric_scores"][:1]
        render(upload=_Upload(pkg2), confirm=True)      # 新内容 ⇒ 必须放行
        after = _append_counts(dao)
        assert after["attempts"] == before["attempts"] + 1
        assert after["rubric_scores"] == before["rubric_scores"] + 1
        assert after["learning_events"] == before["learning_events"] + 1
        render()                                         # 成功回显按 l922-105 走 rerun 后那一帧
        assert [m for m in _success(fake) if OK_HEAD in m] == [
            f"导入完成：答题 1 条 · 事件 1 条 · 状态 1 题 · 复习 1 题 · 元数据 1 项"], \
            "放行那帧的成功回显文案口径不得被本单改动"
        assert dao.get_status("python", "python/01_x/02_p") == "wrong", "键控表仍是覆盖语义"
    finally:
        dao.close()


def _success(fake):
    return [str(c[1][0]) for c in fake.calls if c[0] == "success"]


def test_failed_import_leaves_no_fingerprint_so_retry_still_works(tmp_path, monkeypatch):
    """指纹只在**成功**后写入：坏文件连按两次仍各报一次错（不得被误判成「已导入过」），
    修好之后同一份好文件仍要能导进去。"""
    dao = ProgressDAO(str(tmp_path / "dedup3.db"))
    try:
        fake, render, notices = _wire(monkeypatch, dao)
        bad = _Upload({"format": "nope", "version": 1, "data": {}})
        first_bad = render(upload=bad, confirm=True)
        assert first_bad["reruns"] == 0 and len(notices) == 1
        assert _warnings(fake) == [], "坏文件不该冒「已跳过重复导入」"
        assert fake.session_state.get("_import_consumed_fp") is None

        render(upload=bad, confirm=True)
        assert len(notices) == 2, "同一条坏字节第二次仍应真报错，而不是被防重门吞掉"
        assert fake.session_state.get("_import_consumed_fp") is None
        assert _append_counts(dao) == {"attempts": 0, "learning_events": 0, "rubric_scores": 0}

        render(upload=_Upload(_pkg_with_rubric()), confirm=True)
        assert _append_counts(dao) == {"attempts": 2, "learning_events": 1, "rubric_scores": 2}, \
            "失败留下的记录不得让后续正常导入失效"
    finally:
        dao.close()


def test_library_level_append_semantics_untouched(tmp_path):
    """反向守护：本单只加 UI 防重，`import_json` 本身**仍然**会把 append 表翻倍
    ——`tests/test_data_portability.py:46` 的 by-design 断言依赖这一条，不能被"顺手修好"。"""
    dao = ProgressDAO(str(tmp_path / "dedup4.db"))
    try:
        text = json.dumps(_pkg_with_rubric(), ensure_ascii=False)
        dp.import_json(dao, text)
        first = _append_counts(dao)
        dp.import_json(dao, text)                        # 同一份字节，库层面照单全收
        assert first == {"attempts": 2, "learning_events": 1, "rubric_scores": 2}
        assert _append_counts(dao) == {"attempts": 4, "learning_events": 2, "rubric_scores": 4}, \
            "去重发生在 UI 层；导入 API 语义一变，l922 在册断言就会红"
    finally:
        dao.close()
