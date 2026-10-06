# -*- coding: utf-8 -*-
"""学习数据导入的成功反馈不能被 st.rerun 吞掉（l922-105-import-feedback-survive）。

现场锚点复核（2026-09-22，磁盘实况）：任务书写的 `:237 导入完成…` / `:242 st.rerun()` /
`:243-248 失败分支` 现已分别落在 **254 / 262 / 263-268**——位移由同清单前一单
`l922-104`（同文件加缓存作废行，+20 行）造成，非陈旧；语义完全对得上：
success 与 rerun 之间没有任何跨渲染载体，rerun 一发生，那次渲染里的 st.success 就没了，
用户只看到页面闪回上传态、五项统计一个字都不露。

修法是「写入 session_state → 下一次渲染首行一次性回显」，本文件按**修好后**的行为写：
  例 1 rerun 之后仍能看到完整五项统计文案（含数字）；
  例 2 该回显是一次性的（再渲染不重复骚扰），且清空 session_state 即消失；
  例 3 失败分支仍走 `render_error_notice`、标题与 next_action 文案一字不变（任务书③）。
手法：真 ProgressDAO（tmp_path 真 sqlite）＋ FakeStreamlit 桩，不触真实 Streamlit、不联网。
复跑：python -m pytest tests/test_dashboard_import_feedback.py -q
"""
import json

import ui.components as components
import ui.pages.dashboard as dashboard_page
import core.data_portability as dp
import core.loader as content_loader
from core.data_portability import FORMAT_NAME
from core.progress import ProgressDAO

from tests.test_dashboard_page_render import DashboardFakeStreamlit

UPLOAD_LABEL = "确认导入"
OK_HEAD = "导入完成："
NEXT_ACTION = "当前数据未受影响，可修正文件后重试导入"


def _pkg():
    """一份五个表都有内容的包：数字能对得上，才证明文案不是模板残留。"""
    return {"format": FORMAT_NAME, "version": 1, "exported_at": "2026-09-21T08:00:00+00:00",
            "data": {
                "attempts": [
                    {"lang": "python", "problem_id": "python/01_x/01_p", "code": "print(1)",
                     "passed": 1, "ai_feedback": "", "ts": "2026-09-20 09:00:00"},
                    {"lang": "python", "problem_id": "python/01_x/02_p", "code": "print(2)",
                     "passed": 0, "ai_feedback": "", "ts": "2026-09-20 09:30:00"}],
                "learning_events": [
                    {"event_type": "lesson_viewed", "lang": "python", "topic_id": "01_x",
                     "problem_id": None, "path_id": None, "milestone_id": None,
                     "payload_json": "{}", "created_at": "2026-09-20 09:00:00",
                     "local_date": "2026-09-20"}],
                "rubric_scores": [],
                "problems_status": [
                    {"lang": "python", "problem_id": "python/01_x/02_p", "status": "wrong",
                     "last_attempt_ts": "2026-09-20 09:30:00"}],
                "review_state": [
                    {"lang": "python", "problem_id": "python/01_x/01_p", "interval_days": 6,
                     "ease": 2.0, "review_streak": 3, "next_due_date": "2026-09-27",
                     "last_result": "ok", "updated_ts": "2026-09-20 09:00:00"}],
                "meta": [{"key": "migrated_from", "value": "old-laptop",
                          "updated_ts": "2026-09-20 09:00:00"}]}}


class _Upload:
    def __init__(self, raw):
        self._raw = raw if isinstance(raw, bytes) else json.dumps(raw, ensure_ascii=False).encode("utf-8")

    def getvalue(self):
        return self._raw


def _wire(monkeypatch, dao):
    fake = DashboardFakeStreamlit()
    monkeypatch.setattr(dashboard_page, "st", fake)
    monkeypatch.setattr(components, "st", fake)
    monkeypatch.setattr(dashboard_page, "check_achievements", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_progress_summary", lambda dao: {"earned": 0, "total": 22})
    monkeypatch.setattr(dashboard_page, "get_all_with_state", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "recommend", lambda n=5, dao=None: [])
    monkeypatch.setattr(dashboard_page, "cross_recommend", lambda dao=None, **kw: [])
    monkeypatch.setattr(content_loader, "load_language", lambda lang: [])
    notices = []
    monkeypatch.setattr(dashboard_page, "render_error_notice",
                        lambda title, **kw: notices.append((title, kw)))

    def render(upload=None, confirm=False):
        monkeypatch.setattr(fake, "file_uploader", lambda *a, **kw: upload, raising=False)
        fake.buttons[UPLOAD_LABEL] = bool(confirm)
        fake.calls.clear()
        before = fake.rerun_count
        dashboard_page._render_dashboard_body(dao)
        return {"success": [str(c[1][0]) for c in fake.calls if c[0] == "success"],
                "reruns": fake.rerun_count - before}

    return fake, render, notices


def test_success_feedback_survives_the_rerun(tmp_path, monkeypatch):
    """核心例：导入成功触发 rerun 之后，**下一次**渲染仍要看到完整五项统计。

    修之前这里必然拿到空列表——st.success 只存在于被 rerun 丢掉的那一帧。
    """
    dao = ProgressDAO(str(tmp_path / "fb1.db"))
    try:
        fake, render, notices = _wire(monkeypatch, dao)
        first = render()
        assert not any(OK_HEAD in m for m in first["success"]), "没导入就不该冒出成功文案"

        clicked = render(upload=_Upload(_pkg()), confirm=True)
        assert clicked["reruns"] == 1, "现行实现导入成功后仍应 st.rerun()（本单不改这一条）"
        assert not notices, "好文件不该走错误提示"

        after = render()                               # ← rerun 之后用户实际看到的那一帧
        hit = [m for m in after["success"] if OK_HEAD in m]
        assert hit == [f"导入完成：答题 2 条 · 事件 1 条 · 状态 1 题 · 复习 1 题 · 元数据 1 项"], \
            f"rerun 后成功反馈被吞了（实得 {after['success']}）"
        assert dao.get_meta("migrated_from") == "old-laptop", "回显的数字必须对应真实合并结果"
    finally:
        dao.close()


def test_feedback_is_one_shot_and_follows_the_latest_import(tmp_path, monkeypatch):
    """一次性语义：回显只在 rerun 后那一帧出现，再渲染不重复骚扰；连导两次以最后一次为准。"""
    dao = ProgressDAO(str(tmp_path / "fb2.db"))
    try:
        fake, render, notices = _wire(monkeypatch, dao)
        render(upload=_Upload(_pkg()), confirm=True)                     # 被点那次渲染（马上 rerun）
        assert any(OK_HEAD in m for m in render()["success"])
        assert not any(OK_HEAD in m for m in render()["success"]), "反馈应自动消失，不该每帧都刷一遍"

        pkg2 = _pkg()
        pkg2["data"]["attempts"] = pkg2["data"]["attempts"][:1]          # 只导 1 条答题
        render(upload=_Upload(pkg2), confirm=True)
        third = [m for m in render()["success"] if OK_HEAD in m]
        assert third == [f"导入完成：答题 1 条 · 事件 1 条 · 状态 1 题 · 复习 1 题 · 元数据 1 项"], \
            f"第二次导入的回显应反映最后一次统计（实得 {third}）"
    finally:
        dao.close()


def test_failed_import_still_uses_error_notice_with_the_same_words(tmp_path, monkeypatch):
    """失败分支一字不变：标题「导入失败」、next_action 原文、reason 带异常文本，且不写回显。

    用「format 不对」的包制造确定性异常（`_validate` 抛 ValueError），
    免得把断言绑在 stdlib JSONDecodeError 的措辞上。
    """
    dao = ProgressDAO(str(tmp_path / "fb3.db"))
    try:
        fake, render, notices = _wire(monkeypatch, dao)
        bad = render(upload=_Upload({"format": "nope", "version": 1, "data": {}}), confirm=True)
        assert bad["reruns"] == 0, "坏文件不得触发 rerun（现行行为）"
        assert not bad["success"], "坏文件不得冒成功文案"
        assert len(notices) == 1, f"应恰一次 render_error_notice，实得 {notices}"
        title, kw = notices[0]
        assert title == "导入失败"
        assert kw["next_action"] == NEXT_ACTION, "失败分支的 next_action 文案不许被本单顺带改掉"
        assert "不是本系统的导出文件" in kw["reason"], f"reason 应携带异常文本：{kw}"
        assert fake.session_state.get("_import_feedback") is None, "失败的导入不得留下成功回显"
        render()
        assert not any(OK_HEAD in m for m in render()["success"]), "失败的导入不能冒出成功反馈"
    finally:
        dao.close()
