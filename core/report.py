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
