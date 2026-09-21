# -*- coding: utf-8 -*-
"""report_to_markdown 段落契约钉桩（l920-07）。

锚点 l920-07：src/core/report.py:204 report_to_markdown(report) —— 现测只测「## 存在 / 通过 二字」
的宽口径，本文件把段落标题行集合、空数据段行为、数值格式化口径全部钉死（照现状翻桩，零生产码改动）。

⚠ 本文件同时钉住两处现状（复跑即知，非本单改动）：
  A. 任务锚点写「空数据段省略」——实测**不省略**：weak_topics 为空时渲染占位行
     「- 暂无明显薄弱项，继续保持！」，标题始终保留（见 test_空数据段_不省略而是占位行）。
  B. report_to_markdown 的目标区**内联复制**了 _build_goals 的五个分支（report.py:245-258），
     未调用 _build_goals——两条渲染路径存在漂移风险，本文件用一致性用例把它钉住
     （见 test_目标区与_build_goals_逐字一致）。
"""
from core.report import _build_goals, report_to_markdown

EXPECTED_SECTIONS = [
    "## 总览",
    "## 各语言进度",
    "## 薄弱知识点（需重点练习）",
    "## 下一步建议（3 个可执行目标）",
]


def _report(**kw):
    base = {
        "period_days": 7,
        "generated_date": "2026-09-19",
        "streak": 0,
        "total_attempts": 0,
        "period_attempts": 0,
        "period_passed": 0,
        "grand_solved": 0,
        "grand_wrong": 0,
        "weak_topics": [],
        "lang_progress": {
            "python": {"name": "Python", "icon": "🐍", "total": 121, "solved": 0, "pct": 0},
        },
        "mistakes_count": 0,
        "due_reviews": 0,
    }
    base.update(kw)
    return base


def test_段标题行集合精确():
    md = report_to_markdown(_report())
    got = [l for l in md.split("\n") if l.startswith("## ")]
    assert got == EXPECTED_SECTIONS, f"markdown 段标题集合/顺序漂移：{got}"
    assert md.splitlines()[0] == "# 📚 编程学习报告", "H1 标题行漂移"
    assert md.splitlines()[2] == "> 生成日期：2026-09-19 | 统计周期：最近 7 天", "元信息行漂移"


def test_空数据段_不省略而是占位行():
    """任务锚点预期「空数据段省略」；实测为占位行＋标题保留。照现状钉桩。"""
    md = report_to_markdown(_report())
    assert "## 薄弱知识点（需重点练习）" in md, "空弱项时段标题不该消失"
    assert "- 暂无明显薄弱项，继续保持！" in md, "空弱项占位行漂移"
    # 目标区：streak==0 → 恒有 1 条，不该出现空目标区
    assert "1. 恢复每日打卡——哪怕只做 1 道题也比断连好" in md
    assert "\n\n\n" not in md, "出现连续空行（段落契约破裂）"


def test_数值格式化口径():
    md = report_to_markdown(_report(
        streak=3, period_attempts=17, period_passed=11, grand_solved=42, grand_wrong=4,
        weak_topics=[("python/19_regex", 3.14159), ("sql/04_joins", 2.5)],
        due_reviews=6,
    ))
    # 整数不带小数、带单位后缀
    assert "| 🔥 连续打卡 | 3 天 |" in md, "打卡行格式漂移"
    assert "| 📝 本周期提交 | 17 次 |" in md, "本周期提交行格式漂移"
    assert "| ✅ 本周期通过 | 11 次 |" in md, "本周期通过行格式漂移"
    assert "| 📊 累计通过题数 | 42 |" in md, "累计通过行格式漂移"
    assert "| ❌ 待改错题 | 4 |" in md, "待改错行格式漂移"
    # 弱项分固定两位小数（round-half-even）
    assert "- **python/19_regex**（弱项分 3.14）" in md, "弱项分未按 .2f 格式化"
    assert "- **sql/04_joins**（弱项分 2.50）" in md, "弱项分未补零到两位"
    # 目标区编号从 1 起
    assert "1. 清理 4 道错题——错题是最高效的学习材料" in md


def test_语言表行数与百分比口径():
    report = _report(lang_progress={
        "python": {"name": "Python", "icon": "🐍", "total": 121, "solved": 12, "pct": 9.9},
        "sql": {"name": "SQL", "icon": "🗄️", "total": 54, "solved": 54, "pct": 100.0},
    })
    md = report_to_markdown(report)
    body = md.split("## 各语言进度")[1].split("## 薄弱知识点")[0]
    rows = [l for l in body.split("\n") if l.startswith("| ") and "---" not in l]
    # 表头 + 2 数据行
    assert len(rows) == 3, f"语言表行数漂移（应表头+2数据行）：{rows}"
    assert "| 🐍 Python | 12 | 121 | 9.9% |" in md, "语言行格式漂移（pct 直接拼 %，不 round）"
    assert "| 🗄️ SQL | 54 | 54 | 100.0% |" in md, "100% 行的 pct 口径漂移"
    # 表头列名固定
    assert "| 语言 | 已通过 | 总题数 | 完成率 |" in md, "语言表头漂移"


def test_目标区与_build_goals_逐字一致():
    """B 项：markdown 目标区内联复制了 _build_goals。此处**不**改生产码，
    只用同一 report 对拍——一旦两处分支漂移立即变红，逼作者收敛成单一实现。"""
    for kw in (
        {},
        {"grand_wrong": 12, "weak_topics": [("python/19_regex", 3.75)], "streak": 21,
         "due_reviews": 8},
        {"streak": 6, "due_reviews": 2},
        {"streak": 0, "due_reviews": 1, "grand_wrong": 1},
    ):
        report = _report(**kw)
        expected = [f"{i}. {g}" for i, g in enumerate(_build_goals(report), 1)]
        md = report_to_markdown(report)
        body = md.split("## 下一步建议（3 个可执行目标）")[1]
        got = [l for l in body.split("\n")
               if l[:2] in ("1.", "2.", "3.") and l[0].isdigit()]
        assert got == expected, f"内联目标分支与 _build_goals 漂移\nreport={kw}\nmd={got}\nexpected={expected}"


def test_尾部签名固定():
    md = report_to_markdown(_report())
    tail = md.split("\n")[-3:]
    assert tail[-3:] == ["", "---", "*由编程学习平台自动生成*"], f"尾部签名漂移：{tail}"


# ---------------------------------------------------------------------------
# l922-106：口径注记随导出件走（以下为本单追加段，上方 l920-07 原文零改动）
# 修前的红：report_to_markdown / report_to_html 产物里根本没有「口径」二字，
#           注记只活在面板 caption（ui/pages/dashboard.py:189）——下载即丢。
# ---------------------------------------------------------------------------

def test_口径注记进markdown产物头部():
    """导出件头部必须带口径注记，且位置固定在元信息行之后、总览段之前。"""
    from core.report import CALIBER_NOTE
    md = report_to_markdown(_report())
    lines = md.split("\n")
    assert "口径" in md, "markdown 导出件不含口径注记（跨期对比失真风险随文件带走）"
    assert CALIBER_NOTE.startswith("口径提示："), f"注记文案不以『口径提示：』起头：{CALIBER_NOTE}"
    assert lines[4] == f"> {CALIBER_NOTE}", f"口径注记位置/格式漂移（应为元信息行之后的引用行）：{lines[3:6]}"
    # 位置契约：注记在「## 总览」之前
    assert md.index(CALIBER_NOTE) < md.index("## 总览"), "口径注记跑到了总览段之后"
    # 头部三行（l920-07 契约）不得因新增注记而漂移
    assert lines[0] == "# 📚 编程学习报告"
    assert lines[2] == "> 生成日期：2026-09-19 | 统计周期：最近 7 天"


def test_口径注记进html产物头部():
    """HTML（打印/PDF 出口）同样要带注记。"""
    from core.report import CALIBER_NOTE, report_to_html
    html = report_to_html(_report())
    assert CALIBER_NOTE in html, "html 导出件不含口径注记"
    assert html.index(CALIBER_NOTE) < html.index("<h2>总览</h2>"), "html 口径注记跑到了总览段之后"


def test_两条导出路径注记同一常量():
    """md 与 html 共用 CALIBER_NOTE 常量——内联两份文案必然各自漂移（同 _build_goals 的教训）。"""
    from core.report import CALIBER_NOTE, report_to_html
    md = report_to_markdown(_report())
    html = report_to_html(_report())
    assert md.count(CALIBER_NOTE) == 1, "markdown 注记重复渲染"
    assert html.count(CALIBER_NOTE) == 1, "html 注记重复渲染"


def test_注记只随导出件不随report字典():
    """注记是渲染层职责：generate_report 的字典键集合不受本单影响（防有人改成往数据里塞字段）。"""
    md = report_to_markdown(_report())
    assert "口径提示" in md
    for forbidden in ("\n\n\n",):
        assert forbidden not in md, "新增注记引入了连续空行（段落契约破裂）"


def test_面板caption与导出注记同句():
    """面板 caption（完成标准③要求保留不删）与导出注记必须同句，否则两处口径会各自漂移。"""
    import pathlib
    import re
    from core.report import CALIBER_NOTE
    src = pathlib.Path(__file__).resolve().parents[1] / "ui" / "pages" / "dashboard.py"
    text = src.read_text(encoding="utf-8")
    hit = re.search(r'st\.caption\("([^"]*口径[^"]*)"\)', text)
    assert hit is not None, "面板 caption 口径提示被删（本单完成标准③要求保留）"
    assert hit.group(1) == CALIBER_NOTE, (
        f"面板 caption 与导出注记不同句\ncaption={hit.group(1)}\nCALIBER_NOTE={CALIBER_NOTE}")
