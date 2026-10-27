"""热力图 13 周×7=91 日格 vs SQL 窗口口径钉桩（l922-110）。

背景：网格渲染 13 周共 91 个日格（offset 0..90），旧 SQL 窗口
`datetime('now', '-90 days')` 的边界 = 最老一日格当天的**当前时刻**，
当日 00:00 至此刻之间的作答被系统性漏计。收口选择：窗口改 '-91 days'
对齐 13 周整格，标题/README 同句改「13 周」。本档钉住三件事：
①格数数学（13×7=91）；②源码窗口与格数一致；③口径文案同句防再漂。
"""
import re
from datetime import date, timedelta
from pathlib import Path

import pytest

from core.progress import ProgressDAO

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "ui" / "pages" / "dashboard.py"
README = ROOT / "README.md"


def _heatmap_src() -> str:
    text = DASHBOARD.read_text(encoding="utf-8")
    m = re.search(r"def _render_heatmap.*?(?=\ndef )", text, re.S)
    assert m, "_render_heatmap 函数不存在"
    return m.group(0)


@pytest.fixture
def dao(tmp_path):
    d = ProgressDAO(str(tmp_path / "t.db"))
    yield d
    d.close()


class TestGridWindowAlignment:
    def test_grid_renders_13_weeks_91_cells(self):
        assert 13 * 7 == 91
        src = _heatmap_src()
        assert "range(12, -1, -1)" in src, "网格不再是 13 周，窗口常量若同步变化请一并复核本测试"
        assert "for dow in range(7)" in src

    def test_sql_window_covers_full_oldest_cell(self):
        """窗口必须是 -91 days：-90 days 的边界落在最老日格当天中途，欠计数。

        l1028-05 翻钉：HEATMAP_SQL 已从 _render_heatmap 函数体上提为模块常量
        （dashboard.py:588-592），扫描面从函数体扩到整文件——窗口语义钉不变。"""
        src = DASHBOARD.read_text(encoding="utf-8")
        assert "datetime('now', '-91 days')" in src
        assert "'-90 days'" not in src, "旧窗口残留：热力图最老一格会回到系统性欠计数"

    def test_boundary_math_is_deterministic(self, dao):
        """同基准（UTC，ts 存 CURRENT_TIMESTAMP）下的窗口性质：
        -91 边界恒早于第 90 前的 UTC 日零点 → 最老一日格整日可计数；
        两窗口恒差一天（julianday 差 == 1.0）。"""
        row = dao.conn.execute(
            "SELECT julianday(datetime('now','-90 days')) - julianday(datetime('now','-91 days')),"
            " datetime('now','-91 days') < date('now','-90 days') || ' 00:00:00'"
        ).fetchone()
        assert abs(row[0] - 1.0) < 1e-9, f"两窗口之差应为整一日: {row}"
        assert row[1] == 1, f"-91 边界未早于最老 UTC 日零点: {row}"

    def test_oldest_cell_row_is_counted(self, dao):
        """功能面：最老一格凌晨 00:00:05 的作答必须出现在按日聚合里。"""
        oldest = (date.today() - timedelta(days=90)).isoformat()
        dao.conn.execute(
            "INSERT INTO attempts (lang, problem_id, code, passed, ai_feedback, ts)"
            " VALUES ('python','p_bound','x',1,'',?)",
            (f"{oldest} 00:00:05",),
        )
        dao.conn.commit()
        sql = (
            "SELECT DATE(ts, 'localtime') AS d, COUNT(*) AS n, SUM(passed) AS p "
            "FROM attempts WHERE ts >= datetime('now', '-91 days') "
            "GROUP BY d ORDER BY d"
        )
        rows = {r[0]: r[1] for r in dao.conn.execute(sql).fetchall()}
        assert rows.get(oldest) == 1, f"最老日格未被计入: {rows}"


class TestCaliberSameSentence:
    def test_title_says_13_weeks(self):
        assert "学习热力图（最近 13 周）" in _heatmap_src()
        assert "最近 90 天" not in _heatmap_src()

    def test_readme_same_caliber_as_title(self):
        """README:62 与面板标题同口径，防两处各漂一头（同「caption 同句」钉桩思路）。"""
        readme = README.read_text(encoding="utf-8")
        assert "13 周（91 日格）活动日历" in readme
        assert "90 天活动日历" not in readme
