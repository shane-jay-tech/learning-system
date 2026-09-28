# -*- coding: utf-8 -*-
"""学习数据导出缓存「命中／未命中两条分支」各自的行为钉桩（l927-55，2026-09-28）。

收的缺口（`zcode-bridge/done/l922-104-export-cache-invalidation.result.md` 遗留问题 1）：
  「任务书假设存在『缓存命中路径原有例』，实测 `tests/` 下对 `_export_cache*` 零引用。
    若规划侧要的是『验我没把缓存改坏』，例 2 已经是那条；若另有所指，请指明文件。」
本单按卷宗点名把**例 2 形态**补齐成两条各自独立成立的路径，钉 `ui/pages/dashboard.py:330-346`：

  未命中（首次导出）：`export_json` 跑一次 → `_export_cache_json` **落盘进 session_state**、
      `_export_cache_key` 等于当场重算的六表指纹、`download_button` 的 `data` 就是这份缓存；
  命中（数据未再变的第二次及以后渲染）：`export_json` **零次新增**、按钮 `data` 逐字复用缓存。

与 `tests/test_export_cache_invalidation.py` 的分工（不重复钉、不互相遮蔽）：
  那件管「键**覆盖面**够不够」（例 1/2b/3：只动某张表时键必须变、导入后必须作废），
  本件管「键命中后**缓存到底有没有被吃**」——用**哨兵探针**把这条分开：
  只断言 `len(exports) == 1` 有一个假绿口子——「每次都重新序列化，恰好产出一样的串」在
  同秒内与「吃缓存」读数相同（`export_all` 带 `exported_at` 秒级时间戳，跨秒才分得开）。
  本件把 session_state 里的缓存串改成哨兵值再渲染：**吃缓存** ⇒ 按钮 data == 哨兵；
  **重生成** ⇒ 按钮 data == 真 JSON、哨兵被覆盖。⇒ 断言不依赖时钟，两条分支可分别证伪。

手法照 `tests/test_export_cache_invalidation.py`：真 `ProgressDAO`（tmp_path 真 sqlite）
＋ `DashboardFakeStreamlit` 桩 ＋ spy `core.data_portability.export_json` 数序列化次数。
不连网、不触真实 Streamlit、不碰 `data/progress.db`、零写生产库。
复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_export_cache_hit_path.py -q
"""
import json

import core.data_portability as dp
import core.loader as content_loader
import ui.components as components
import ui.pages.dashboard as dashboard_page
from core.progress import ProgressDAO

from tests.test_dashboard_page_render import DashboardFakeStreamlit

EXPORT_BTN = "⬇️ 导出全部学习数据 (.json)"
SENTINEL = "__SENTINEL_CACHED_EXPORT__"
P1 = "python/01_x/01_p"
P2 = "python/01_x/02_p"

# 键的构造契约（抄 ui/pages/dashboard.py:330-335 的**取数方式**，顺序也照它）：
# 前两项走 DAO 计数助手，后四项是单表 COUNT(*) 字面量。本件自己重算一遍当对照——
# 若生产侧从键里删掉某张表，这里算出的指纹与 session_state 里的必然不等（例 2b 的牙在本件的镜像）。
_COUNT_SQL = (
    "SELECT COUNT(*) FROM problems_status",
    "SELECT COUNT(*) FROM review_state",
    "SELECT COUNT(*) FROM rubric_scores",
    "SELECT COUNT(*) FROM meta",
)


def expected_key(dao):
    """独立重算的期望键（不用生产码的 `_exp_key`，避免"拿被测对象自证"）。"""
    parts = [dao.total_attempts(), dao.event_count()]
    parts += [int(dao.conn.execute(sql).fetchone()[0]) for sql in _COUNT_SQL]
    return "_".join(str(n) for n in parts)


def _seed(dao):
    """最小库：1 条答题 ＋ 1 条状态 ＋ 1 条事件（复习/评分/meta 三表留空，键形状仍非平凡）。"""
    dao.record_attempt_and_status("python", P1, "print(1)", False, "")
    dao.mark_status("python", P1, "wrong")
    dao.emit_event("lesson_viewed", lang="python", topic_id="01_x")
    dao._clear_memo()


def _wire(monkeypatch, dao):
    """渲染整块学习面板，只留「数据导出」区是真件；其余重活全部打桩。"""
    fake = DashboardFakeStreamlit()
    monkeypatch.setattr(dashboard_page, "st", fake)
    monkeypatch.setattr(components, "st", fake)
    monkeypatch.setattr(dashboard_page, "check_achievements", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_progress_summary", lambda dao: {"earned": 0, "total": 22})
    monkeypatch.setattr(dashboard_page, "get_all_with_state", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "recommend", lambda n=5, dao=None: [])
    monkeypatch.setattr(dashboard_page, "cross_recommend", lambda dao=None, **kw: [])
    monkeypatch.setattr(content_loader, "load_language", lambda lang: [])
    monkeypatch.setattr(fake, "file_uploader", lambda *a, **kw: None, raising=False)

    serialized = []          # 每次真序列化往这里落一条（spy 的牙：数次数 ＋ 留正文）
    real_export = dp.export_json

    def spy(dao_):
        text = real_export(dao_)
        serialized.append(text)
        return text

    monkeypatch.setattr(dp, "export_json", spy)   # dashboard 内是函数级 import，改模块属性即可

    def render():
        dashboard_page._render_dashboard_body(dao)
        return fake

    return fake, render, serialized


def _export_buttons(fake):
    """本次 fake 收到的 JSON 导出按钮 `data` 实参列表（顺序 == 渲染顺序）。"""
    return [c[2]["data"] for c in fake.calls
            if c[0] == "download_button" and c[2].get("mime") == "application/json"]


# ---------------------------------------------------------------------------
# 例 1（未命中／首次导出）：缓存落盘 ＋ 键＝当场六表指纹 ＋ 按钮吃的是这份缓存
# ---------------------------------------------------------------------------

def test_first_export_miss_serializes_once_and_writes_cache_into_session_state(tmp_path, monkeypatch):
    dao = ProgressDAO(str(tmp_path / "hit1.db"))
    try:
        _seed(dao)
        fake, render, serialized = _wire(monkeypatch, dao)

        render()

        assert len(serialized) == 1, "首次渲染没有 `_export_cache_key` ⇒ 必走未命中分支序列化一次"
        cache_json = fake.session_state["_export_cache_json"]
        cache_key = fake.session_state["_export_cache_key"]
        # 缓存内容 == 这次序列化的返回值（不是别处抄来的串），且是能解析的导出包
        assert cache_json == serialized[0], "_export_cache_json 存的必须就是本次 export_json 的结果"
        payload = json.loads(cache_json)
        assert payload["format"] == dp.FORMAT_NAME
        assert [r["problem_id"] for r in payload["data"]["problems_status"]] == [P1]
        # 键 == 独立重算的六表指纹（生产侧从键里删任一张表 ⇒ 本断言当场红）
        assert cache_key == expected_key(dao), \
            f"键形状漂移：盘上 {cache_key!r}，按 dashboard:330-335 契约应为 {expected_key(dao)!r}"
        # 键的组件数 == 导出面表数（导出面新增第 7 张表而键没跟 ⇒ 当场红；绑实取，不写字面量 6）
        assert len(cache_key.split("_")) == len(dp.export_all(dao)["data"]), \
            "缓存键组件数与 export_all 导出表数不等 ⇒ 键没覆盖导出面每一张表"
        # 按钮 data 吃的是缓存（三者同源：session_state / spy 结果 / 按钮实参）
        buttons = _export_buttons(fake)
        assert len(buttons) == 1, f"学习数据区应恰有 1 个 JSON 导出按钮，实得 {len(buttons)}"
        assert buttons[0] == cache_json
    finally:
        dao.close()


# ---------------------------------------------------------------------------
# 例 2（命中／数据未变）：零重算 ＋ 哨兵探针证"吃的是缓存"而不是"恰好重生成同一条串"
# ---------------------------------------------------------------------------

def test_second_export_with_unchanged_data_hits_cache_and_recomputes_nothing(tmp_path, monkeypatch):
    dao = ProgressDAO(str(tmp_path / "hit2.db"))
    try:
        _seed(dao)
        fake, render, serialized = _wire(monkeypatch, dao)

        render()
        first_key = fake.session_state["_export_cache_key"]
        first_json = fake.session_state["_export_cache_json"]
        assert len(serialized) == 1

        render()
        render()
        assert len(serialized) == 1, "同键连续渲染不得再序列化（命中分支的收益面）"
        assert fake.session_state["_export_cache_key"] == first_key
        assert fake.session_state["_export_cache_json"] == first_json

        # 哨兵探针（本件相对 test_export_cache_invalidation 例 2 的增量）：
        # 把缓存串换成明显不是 JSON 的哨兵，再渲染一次。吃缓存 ⇒ 按钮 data == 哨兵；
        # 若有人把缓存拆成"每次都重导"，这里会得到真 JSON ⇒ 当场红，且不依赖跨秒时钟。
        fake.calls.clear()
        fake.session_state["_export_cache_json"] = SENTINEL
        render()
        buttons = _export_buttons(fake)
        assert buttons == [SENTINEL], \
            f"同键渲染没吃缓存（按钮 data={buttons!r}）：命中路径被改成重生成 ⇒ 导出成本回到每帧全库序列化"
        assert len(serialized) == 1, "命中分支里绝不允许调用 export_json"
        assert fake.session_state["_export_cache_json"] == SENTINEL, "命中分支不得回写缓存"
        assert fake.session_state["_export_cache_key"] == first_key
    finally:
        dao.close()


# ---------------------------------------------------------------------------
# 例 3（未命中回来／真写入后）：键跟着变 ＋ 哨兵被真导出整体替换 ⇒ 例 2 的断言不是永绿
# ---------------------------------------------------------------------------

def test_key_change_after_real_write_replaces_sentinel_cache(tmp_path, monkeypatch):
    dao = ProgressDAO(str(tmp_path / "hit3.db"))
    try:
        _seed(dao)
        fake, render, serialized = _wire(monkeypatch, dao)
        render()
        key_before = fake.session_state["_export_cache_key"]
        fake.session_state["_export_cache_json"] = SENTINEL          # 先造命中态（同上例）
        render()
        assert _export_buttons(fake)[-1] == SENTINEL
        assert len(serialized) == 1, "前提：改哨兵后的那次渲染仍命中（否则本例证的不是未命中分支）"

        dao.record_attempt_and_status("python", P2, "print(2)", True, "")   # 真写入：attempts ＋状态各 +1
        dao._clear_memo()
        fake.calls.clear()
        render()

        assert len(serialized) == 2, "键变了必须重序列化一次"
        assert fake.session_state["_export_cache_key"] == expected_key(dao)
        assert fake.session_state["_export_cache_key"] != key_before
        assert fake.session_state["_export_cache_json"] != SENTINEL, \
            "未命中分支没替换缓存 ⇒ 例 2 的『吃缓存』会永远吃到一个假串（哨兵自检失效）"
        assert fake.session_state["_export_cache_json"] == serialized[1]
        buttons = _export_buttons(fake)
        assert len(buttons) == 1 and buttons[0] == serialized[1]
        assert len(json.loads(buttons[0])["data"]["attempts"]) == 2, "重算后的导出必须含新答题"
    finally:
        dao.close()
