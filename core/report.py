"""学习报告生成——周报/月报导出，本机可用，不依赖用户系统。"""
from datetime import date, timedelta
from typing import Dict, List, Optional

from core.loader import load_language
from core.progress import ProgressDAO
from core.recommend import all_problems, _topic_weakness
from ui.components import ALL_LANGS, LANG_META


def generate_report(dao: Optional[ProgressDAO] = None, days: int = 7) -> Dict:
    """生成最近 N 天的学习报告。"""
    own = dao is None
    d = dao or ProgressDAO()
    try:
        summary = d.summary_by_lang()
        streak = d.daily_streak()
        total_attempts = d.total_attempts()
        daily = d.attempts_by_day(days=days)
        recent = d.recent_attempts(limit=50)
        mistakes = d.list_mistakes()
        status = d.all_problems_status()
        items = all_problems()
        weakness = _topic_weakness(items, status)
        due_reviews = len(d.get_due_reviews(limit=100))
    finally:
        if own:
            d.close()

    grand_solved = sum(s.get("solved", 0) for s in summary.values())
    grand_wrong = sum(s.get("wrong", 0) for s in summary.values())

    # 最近 N 天统计
    period_attempts = sum(r["attempts"] for r in daily)
    period_passed = sum(r["passed"] for r in daily)

    # 薄弱知识点 top 5
    weak_topics = sorted(weakness.items(), key=lambda x: -x[1])[:5]

    # 各语言进度
    lang_progress = {}
    for lang in ALL_LANGS:
        total = sum(len(t.problems) for t in load_language(lang))
        solved = summary.get(lang, {}).get("solved", 0)
        lang_progress[lang] = {
            "name": LANG_META[lang]["name"],
            "icon": LANG_META[lang]["icon"],
            "total": total,
            "solved": solved,
            "pct": round(solved / total * 100, 1) if total else 0,
        }

    return {
        "period_days": days,
        "generated_date": date.today().isoformat(),
        "streak": streak,
        "total_attempts": total_attempts,
        "period_attempts": period_attempts,
        "period_passed": period_passed,
        "grand_solved": grand_solved,
        "grand_wrong": grand_wrong,
        "weak_topics": weak_topics,
        "lang_progress": lang_progress,
        "mistakes_count": len(mistakes),
        "due_reviews": due_reviews,
    }


def _build_goals(report: Dict) -> List[str]:
    """下一步建议（3 个可执行目标）——markdown 与 HTML 共用同一份逻辑。"""
    goals = []
    if report["grand_wrong"] > 0:
        goals.append(f"清理 {report['grand_wrong']} 道错题——错题是最高效的学习材料")
    if report["weak_topics"]:
        top_weak = report["weak_topics"][0][0]
        goals.append(f"重点攻克 **{top_weak}** 知识点（做 3-5 道相关题）")
    if report["streak"] == 0:
        goals.append("恢复每日打卡——哪怕只做 1 道题也比断连好")
    elif report["streak"] < 7:
        goals.append(f"保持打卡到 7 天连续（当前 {report['streak']} 天）")
    else:
        goals.append(f"保持优秀节奏，当前连续 {report['streak']} 天")
    if report.get("due_reviews", 0) > 0:
        goals.append(f"完成 {report['due_reviews']} 道到期复习题")
    return goals[:3]


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>编程学习报告</title>
<style>
  :root { --primary: #6366F1; --accent: #10B981; --warning: #F59E0B; --muted: #64748B; }
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    color: #0F172A; margin: 0; padding: 24px; background: #F8FAFC;
  }
  .page { max-width: 800px; margin: 0 auto; background: #fff;
           border-radius: 12px; padding: 36px 40px;
           box-shadow: 0 4px 16px rgba(15,23,42,.06); }
  h1 { font-size: 24px; margin: 0 0 4px; }
  .meta { color: var(--muted); font-size: 13px; margin-bottom: 24px; }
  h2 { font-size: 16px; margin: 28px 0 10px; padding-bottom: 6px;
       border-bottom: 2px solid #EEF2FF; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 10px; }
  .card { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px;
          padding: 12px 14px; }
  .card .num { font-size: 22px; font-weight: 700; color: var(--primary); }
  .card .lbl { font-size: 12px; color: var(--muted); margin-top: 2px; }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid #EEF2FF; }
  th { color: var(--muted); font-weight: 600; font-size: 12px; }
  .bar { height: 8px; border-radius: 4px; background: #E2E8F0; min-width: 120px; }
  .bar > div { height: 8px; border-radius: 4px; background: var(--primary); }
  ol li { margin: 6px 0; line-height: 1.6; }
  .hint { color: var(--muted); font-size: 12px; margin-top: 24px;
          border-top: 1px dashed #E2E8F0; padding-top: 10px; }
  @media print {
    body { background: #fff; padding: 0; }
    .page { box-shadow: none; border-radius: 0; padding: 0; }
    h2 { page-break-after: avoid; }
    .card, tr { page-break-inside: avoid; }
  }
</style>
</head>
<body>
<div class="page">
{content}
</div>
</body>
</html>"""


def report_to_html(report: Dict) -> str:
    """将报告转为自包含 HTML（浏览器打开后 Ctrl+P 打印或另存为 PDF）。

    零依赖替代 PDF 导出：无第三方库也能获得打印级报告。
    """
    import html as _html

    e = _html.escape
    period = report["period_days"]
    cards = "".join(f'''
        <div class="card"><div class="num">{e(str(v))}</div><div class="lbl">{e(k)}</div></div>'''
        for k, v in (
            ("连续打卡（天）", report["streak"]),
            (f"本周期提交（{period} 天）", report["period_attempts"]),
            (f"本周期通过（{period} 天）", report["period_passed"]),
            ("累计通过题数", report["grand_solved"]),
            ("待改错题", report["grand_wrong"]),
            ("到期复习", report.get("due_reviews", 0)),
        ))

    lang_rows = []
    for lang, info in report["lang_progress"].items():
        pct = info["pct"]
        lang_rows.append(f'''
        <tr><td>{e(info["icon"])} {e(info["name"])}</td>
            <td>{e(str(info["solved"]))} / {e(str(info["total"]))}</td>
            <td>{e(f"{pct}%")}</td>
            <td><div class="bar"><div style="width:{min(pct, 100):.1f}%"></div></div></td></tr>''')

    if report["weak_topics"]:
        weak_html = "<ol>" + "".join(
            f"<li>{e(tk)}（弱项分 {score:.2f}）</li>"
            for tk, score in report["weak_topics"]) + "</ol>"
    else:
        weak_html = "<p>暂无明显薄弱项，继续保持！</p>"

    goals = _build_goals(report)
    goals_html = "<ol>" + "".join(f"<li>{e(g)}</li>" for g in goals) + "</ol>"
    if not goals:
        goals_html = "<p>全部完成，保持节奏！</p>"

    content = f"""
<h1>📚 编程学习报告</h1>
<div class="meta">生成日期：{e(report["generated_date"])} ｜ 统计周期：最近 {e(str(period))} 天</div>

<h2>总览</h2>
<div class="grid">{cards}</div>

<h2>各语言进度</h2>
<table><thead><tr><th>语言</th><th>已通过</th><th>完成率</th><th style="width:30%">进度</th></tr></thead>
<tbody>{"".join(lang_rows)}</tbody></table>

<h2>薄弱知识点（需重点练习）</h2>
{weak_html}

<h2>下一步建议（3 个可执行目标）</h2>
{goals_html}

<div class="hint">📄 由编程学习平台自动生成。浏览器打开后按 Ctrl+P 可打印或另存为 PDF。</div>
"""
    return _HTML_TEMPLATE.replace("{content}", content)


def report_to_markdown(report: Dict) -> str:
    """将报告转为 Markdown 文本（可复制/导出）。"""
    lines = [
        f"# 📚 编程学习报告",
        f"",
        f"> 生成日期：{report['generated_date']} | 统计周期：最近 {report['period_days']} 天",
        f"",
        f"## 总览",
        f"",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 🔥 连续打卡 | {report['streak']} 天 |",
        f"| 📝 本周期提交 | {report['period_attempts']} 次 |",
        f"| ✅ 本周期通过 | {report['period_passed']} 次 |",
        f"| 📊 累计通过题数 | {report['grand_solved']} |",
        f"| ❌ 待改错题 | {report['grand_wrong']} |",
        f"",
        f"## 各语言进度",
        f"",
        f"| 语言 | 已通过 | 总题数 | 完成率 |",
        f"|------|--------|--------|--------|",
    ]
    for lang, info in report["lang_progress"].items():
        lines.append(f"| {info['icon']} {info['name']} | {info['solved']} | {info['total']} | {info['pct']}% |")

    lines.extend([
        f"",
        f"## 薄弱知识点（需重点练习）",
        f"",
    ])
    if report["weak_topics"]:
        for topic_key, score in report["weak_topics"]:
            lines.append(f"- **{topic_key}**（弱项分 {score:.2f}）")
    else:
        lines.append("- 暂无明显薄弱项，继续保持！")

    lines.extend([
        f"",
        f"## 下一步建议（3 个可执行目标）",
        f"",
    ])
    goals = []
    if report["grand_wrong"] > 0:
        goals.append(f"清理 {report['grand_wrong']} 道错题——错题是最高效的学习材料")
    if report["weak_topics"]:
        top_weak = report["weak_topics"][0][0]
        goals.append(f"重点攻克 **{top_weak}** 知识点（做 3-5 道相关题）")
    if report["streak"] == 0:
        goals.append("恢复每日打卡——哪怕只做 1 道题也比断连好")
    elif report["streak"] < 7:
        goals.append(f"保持打卡到 7 天连续（当前 {report['streak']} 天）")
    else:
        goals.append(f"保持优秀节奏，当前连续 {report['streak']} 天")
    if report.get("due_reviews", 0) > 0:
        goals.append(f"完成 {report['due_reviews']} 道到期复习题")
    for i, g in enumerate(goals[:3], 1):
        lines.append(f"{i}. {g}")

    lines.extend([
        f"",
        f"---",
        f"*由编程学习平台自动生成*",
    ])
    return "\n".join(lines)
