# -*- coding: utf-8 -*-
"""学习面板「导出全部学习数据」的渲染内缓存键覆盖面（l922-104-export-cache-invalidation）。

现场锚点复核（2026-09-22，与任务书一致，0 处漂移）：
  - `ui/pages/dashboard.py:213`  `_exp_key = f"{dao.total_attempts()}_{dao.event_count()}"`
  - `ui/pages/dashboard.py:214`  `if st.session_state.get("_export_cache_key") != _exp_key:`

缺陷：键只含 attempts / learning_events 两个计数，而 `export_all` 导出的是**六张表**。
任何「不改这两计数」的写入，rerun 后仍命中旧键 → 用户立刻点导出拿到的是合并前的旧快照。
本文件用两个不同的注入面把它拆开：
  例 1 旁路写入（脚本/另一进程调 import_json）：只加 problems_status/review_state 行 → 键不变；
  例 3 走 UI 导入按钮的**同键覆盖**（INSERT OR REPLACE）：行数与两计数**完全不变**，
      这种连「扩计数键」都抓不到，只能靠导入成功后主动作废 `_export_cache_key`；
  例 2 反向守护：数据真没变时仍**只序列化一次**（不许用「每次都重导」这种把缓存拆掉的方式糊过去）。

手法：真 `ProgressDAO`（tmp_path 真 sqlite）＋ FakeStreamlit 桩；
把 `core.data_portability.export_json` 换成 spy 数「重序列化了几次」，
并读 `download_button` 的 `data` 实参看导出内容新旧。不连网、不触真实 Streamlit。
复跑：python -m pytest tests/test_export_cache_invalidation.py -q
"""
import json

import ui.components as components
import ui.pages.dashboard as dashboard_page
import core.data_portability as dp
import core.loader as content_loader
from core.data_portability import FORMAT_NAME, import_json
from core.progress import ProgressDAO

from tests.test_dashboard_page_render import DashboardFakeStreamlit

UPLOAD_LABEL = "确认导入"
EXPORT_BTN = "⬇️ 导出全部学习数据 (.json)"
P1 = "python/01_x/01_p"
P2 = "python/01_x/02_p"


def _seed(dao):
    """库里只有 1 道错题 + 1 条事件：导出包的对照基线。"""
    dao.record_attempt_and_status("python", P1, "print(1)", False, "")
    dao.mark_status("python", P1, "wrong")
    dao.emit_event("lesson_viewed", lang="python", topic_id="01_x")
    dao._clear_memo()


def _wire(monkeypatch, dao, buttons=None):
    """渲染整块学习面板，只留「数据导出/导入」区是真件；其余重活全部打桩。"""
    fake = DashboardFakeStreamlit(buttons=buttons or {})
    monkeypatch.setattr(dashboard_page, "st", fake)
    monkeypatch.setattr(components, "st", fake)
    monkeypatch.setattr(dashboard_page, "check_achievements", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_progress_summary", lambda dao: {"earned": 0, "total": 22})
    monkeypatch.setattr(dashboard_page, "get_all_with_state", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "recommend", lambda n=5, dao=None: [])
    monkeypatch.setattr(dashboard_page, "cross_recommend", lambda dao=None, **kw: [])
    monkeypatch.setattr(content_loader, "load_language", lambda lang: [])

    exports = []
    real_export = dp.export_json

    def spy(dao_):
        text = real_export(dao_)
        exports.append(text)
        return text

    monkeypatch.setattr(dp, "export_json", spy)          # dashboard 内是函数级 import，改模块属性即可

    def render(upload=None):
        if upload is None:
            monkeypatch.setattr(fake, "file_uploader", lambda *a, **kw: None, raising=False)
        else:
            monkeypatch.setattr(fake, "file_uploader", lambda *a, **kw: upload, raising=False)
        dashboard_page._render_dashboard_body(dao)
        return fake

    return fake, render, exports


class _Upload:
    def __init__(self, payload: dict):
        self._raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def getvalue(self):
        return self._raw


def _pkg(problems_status=(), review_state=(), meta=()):
    """只带键控表的导出包：attempts / learning_events / rubric_scores 全空 → 旧键两个成分都不动。"""
    return {"format": FORMAT_NAME, "version": 1, "exported_at": "2026-09-20T10:00:00+00:00",
            "data": {"attempts": [], "learning_events": [], "rubric_scores": [],
                     "problems_status": list(problems_status),
                     "review_state": list(review_state), "meta": list(meta)}}


def _status_rows(dao):
    return {k[1]: v for k, v in dao.all_problems_status().items()}


def _by_pid(rows, pid, field):
    return [r[field] for r in rows if r["problem_id"] == pid]


def _exported_text(fake):
    hits = [c[2]["data"] for c in fake.calls
            if c[0] == "download_button" and c[2].get("mime") == "application/json"]
    assert len(hits) == 1, f"学习数据区应当恰有 1 个 JSON 导出按钮，实得 {len(hits)}"
    assert hits[0], "导出按钮的 data 不能是空串"
    return hits[0]


# ---------------------------------------------------------------------------
# 例 1：旁路写入——导入包只带 problems_status / review_state（旧键两计数不变）
# ---------------------------------------------------------------------------

def test_import_touching_only_review_and_status_is_visible_in_next_export(tmp_path, monkeypatch):
    dao = ProgressDAO(str(tmp_path / "k1.db"))
    try:
        _seed(dao)
        fake, render, exports = _wire(monkeypatch, dao)
        render()
        first = json.loads(_exported_text(fake))
        assert first["data"]["review_state"] == []
        assert [r["problem_id"] for r in first["data"]["problems_status"]] == [P1]
        assert len(exports) == 1

        stats = import_json(dao, json.dumps(_pkg(
            problems_status=[{"lang": "python", "problem_id": P2, "status": "solved",
                              "last_attempt_ts": "2026-09-20 10:00:00"}],
            review_state=[{"lang": "python", "problem_id": P2, "interval_days": 4, "ease": 2.3,
                           "review_streak": 2, "next_due_date": "2026-09-26", "last_result": "ok",
                           "updated_ts": "2026-09-20 10:00:00"}])))
        dao._clear_memo()                                 # 与 :241 导入成功后的动作一致
        assert stats["attempts"] == 0 and stats["learning_events"] == 0
        assert (dao.total_attempts(), dao.event_count()) == (1, 1), \
            "前提：旧键的两个成分纹丝不动（否则这例抓不到缺陷）"

        fake.calls.clear()
        render()
        second = json.loads(_exported_text(fake))
        assert _by_pid(second["data"]["review_state"], P2, "interval_days") == [4], \
            "rerun 后仍导出合并前的旧快照：缓存键没覆盖 review_state/problems_status"
        assert _by_pid(second["data"]["problems_status"], P2, "status") == ["solved"]
        assert _status_rows(dao)[P2] == "solved"
        assert len(exports) == 2, "键变了就必须重序列化一次（不是把旧串再塞一遍）"
    finally:
        dao.close()


# ---------------------------------------------------------------------------
# 例 2：反向守护——数据没变仍走缓存；真变了（加了答题）要失效
# ---------------------------------------------------------------------------

def test_unchanged_data_serializes_the_export_only_once(tmp_path, monkeypatch):
    dao = ProgressDAO(str(tmp_path / "k2.db"))
    try:
        _seed(dao)
        fake, render, exports = _wire(monkeypatch, dao)
        render()
        first_key = fake.session_state["_export_cache_key"]
        render()
        render()
        assert len(exports) == 1, "同键连续渲染不得重复序列化（缓存命中路径要保住）"
        assert fake.session_state["_export_cache_key"] == first_key

        fake.calls.clear()
        dao.record_attempt_and_status("python", P2, "print(2)", True, "")   # 真实写入
        dao._clear_memo()
        render()
        assert len(exports) == 2, "答题数变了必须重序列化"
        assert fake.session_state["_export_cache_key"] != first_key
        assert len(json.loads(_exported_text(fake))["data"]["attempts"]) == 2
    finally:
        dao.close()


def test_review_only_write_changes_the_key_even_when_attempts_and_events_stay(tmp_path, monkeypatch):
    """把「键里到底数了哪几张表」钉死：只有 review_state 增长时，键必须跟着变。"""
    dao = ProgressDAO(str(tmp_path / "k2b.db"))
    try:
        _seed(dao)
        fake, render, exports = _wire(monkeypatch, dao)
        render()
        key_before = fake.session_state["_export_cache_key"]
        counts_before = (dao.total_attempts(), dao.event_count())

        dao.update_review_state("python", P1, True)        # 只动复习表，答题/事件计数不变
        dao._clear_memo()
        assert (dao.total_attempts(), dao.event_count()) == counts_before
        fake.calls.clear()
        render()
        assert fake.session_state["_export_cache_key"] != key_before, "复习表变了而键没变＝导出会长期吃旧快照"
        assert len(exports) == 2
    finally:
        dao.close()


# ---------------------------------------------------------------------------
# 例 3：走 UI 导入按钮的**同键覆盖**（行数不变，扩计数键也抓不到 → 必须主动作废）
# ---------------------------------------------------------------------------

def test_ui_import_overwriting_same_rows_without_changing_counts_invalidates_cache(tmp_path, monkeypatch):
    dao = ProgressDAO(str(tmp_path / "k3.db"))
    try:
        _seed(dao)
        dao.update_review_state("python", P1, True)
        dao._clear_memo()
        fake, render, exports = _wire(monkeypatch, dao)
        render()
        before = json.loads(_exported_text(fake))
        assert _by_pid(before["data"]["problems_status"], P1, "status") == ["wrong"]
        interval_before = _by_pid(before["data"]["review_state"], P1, "interval_days")
        assert interval_before and interval_before[0] != 11, "前提：导入前复习间隔不是 11 天"
        rows_before = len(exports)

        # 另一台机器上同一道题已做对：同 (lang, problem_id) 键、行数不变、值被覆盖
        pkg = _pkg(problems_status=[{"lang": "python", "problem_id": P1, "status": "solved",
                                    "last_attempt_ts": "2026-09-21 08:00:00"}],
                   review_state=[{"lang": "python", "problem_id": P1, "interval_days": 11,
                                  "ease": 2.6, "review_streak": 5, "next_due_date": "2026-10-02",
                                  "last_result": "ok", "updated_ts": "2026-09-21 08:00:00"}])
        fake.calls.clear()
        fake.buttons[UPLOAD_LABEL] = True                  # 本次渲染里按了「确认导入」
        render(upload=_Upload(pkg))
        assert fake.rerun_count >= 1, "导入成功后应触发 rerun（现行行为）"
        assert dao.get_status("python", P1) == "solved"    # 库里确实被覆盖了

        fake.buttons[UPLOAD_LABEL] = False                 # 真实 streamlit 按钮态只在被点那次渲染为 True
        fake.calls.clear()
        render()                                           # rerun 之后的那一次：导出必须已是新值
        after = json.loads(_exported_text(fake))
        assert _by_pid(after["data"]["problems_status"], P1, "status") == ["solved"], \
            "同键覆盖不改任何行数：只有导入成功后主动作废 _export_cache_key 才抓得到"
        assert _by_pid(after["data"]["review_state"], P1, "interval_days") == [11]
        assert len(exports) > rows_before
    finally:
        dao.close()


# ---------------------------------------------------------------------------
# l930-12：指纹升级（行数级 → 每表 COUNT＋MAX(时戳) 组合）后的靶点例——
# 「只改值不加行」不再需要走导入路径才被抓（例 3 是导入面变体；本例是最小变体：
# 生产写端 mark_status 同键覆盖，行数与两计数全不变，仅 last_attempt_ts 刷新）。
# ---------------------------------------------------------------------------
def test_value_only_update_bumps_the_combined_fingerprint(tmp_path, monkeypatch):
    dao = ProgressDAO(str(tmp_path / "k4.db"))
    try:
        _seed(dao)
        fake, render, exports = _wire(monkeypatch, dao)
        render()
        key_before = fake.session_state["_export_cache_key"]
        before = json.loads(_exported_text(fake))
        assert _by_pid(before["data"]["problems_status"], P1, "status") == ["wrong"]
        counts_before = (dao.total_attempts(), dao.event_count())
        rows_before = len(exports)

        # 只改值：行数、两计数全不变。⚠ 用直接 SQL 显式刷 last_attempt_ts——
        # mark_status 走 CURRENT_TIMESTAMP（秒级），与本例 seed 同秒执行时 MAX 不变属
        # **精度限制**（组合指纹的已知盲区，见 l930-12 result 登记），不是指纹失效；
        # 显式异值时戳证的是「指纹对值变化本身敏感」这一命题。
        dao.conn.execute(
            "UPDATE problems_status SET status = 'solved', last_attempt_ts = '2026-10-02 12:00:00' "
            "WHERE lang = 'python' AND problem_id = ?", (P1,))
        dao._clear_memo()
        assert (dao.total_attempts(), dao.event_count()) == counts_before
        fake.calls.clear()
        render()
        # 指纹必须变（MAX(last_attempt_ts) 刷新）——旧行数级键在此场景恒等＝本单升级的靶点
        assert fake.session_state["_export_cache_key"] != key_before, \
            "只改值不加行而键不变＝组合指纹未生效"
        # 导出内容跟上新值（不再吃旧快照）
        after = json.loads(_exported_text(fake))
        assert _by_pid(after["data"]["problems_status"], P1, "status") == ["solved"]
        assert len(exports) == rows_before + 1
    finally:
        dao.close()
