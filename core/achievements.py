"""Achievement system: badges, streaks, milestones."""
from dataclasses import dataclass
from typing import Dict, List, Optional

from core.progress import ProgressDAO


@dataclass
class Achievement:
    id: str
    title: str
    icon: str
    description: str
    category: str  # streak, language, path, special


ACHIEVEMENTS: List[Achievement] = [
    # Streak achievements
    Achievement("streak_3", "初露锋芒", "🔥", "连续打卡 3 天", "streak"),
    Achievement("streak_7", "一周不辍", "⚡", "连续打卡 7 天", "streak"),
    Achievement("streak_14", "半月坚持", "💪", "连续打卡 14 天", "streak"),
    Achievement("streak_30", "月度达人", "🏆", "连续打卡 30 天", "streak"),
    # Submission milestones
    Achievement("first_solve", "初窥门径", "🌱", "第一次通过一道题", "special"),
    Achievement("solve_10", "渐入佳境", "📗", "累计通过 10 道题", "special"),
    Achievement("solve_50", "半百突破", "📘", "累计通过 50 道题", "special"),
    Achievement("solve_100", "百题斩将", "📕", "累计通过 100 道题", "special"),
    Achievement("solve_200", "双百勇士", "🎖️", "累计通过 200 道题", "special"),
    # Language achievements
    Achievement("python_first", "Python 启程", "🐍", "通过第一道 Python 题", "language"),
    Achievement("sql_first", "SQL 起步", "🗃️", "通过第一道 SQL 题", "language"),
    Achievement("cpp_first", "C++ 初体验", "⚙️", "通过第一道 C++ 题", "language"),
    Achievement("r_first", "R 入门", "📊", "通过第一道 R 题", "language"),
    Achievement("agent_first", "Agent 觉醒", "🤖", "通过第一道 Agent 开发题", "language"),
    Achievement("python_half", "Python 过半", "🐍", "完成 Python 题库 50%", "language"),
    Achievement("sql_half", "SQL 过半", "🗃️", "完成 SQL 题库 50%", "language"),
    Achievement("agent_half", "Agent 过半", "🤖", "完成 Agent 开发题库 50%", "language"),
    # Path achievements
    Achievement("path_first_milestone", "里程碑之始", "🏁", "完成任意一个路径里程碑", "path"),
    Achievement("path_agent_done", "Agent 指挥官", "🎯", "完成 Agent 指挥主线全部里程碑", "path"),
    Achievement("path_pa_done", "数据分析师", "📈", "完成 People Analytics 主线全部里程碑", "path"),
    # Special
    Achievement("no_mistakes", "完美主义", "✨", "清空所有错题", "special"),
    Achievement("multi_lang", "多面手", "🌍", "在 3 种以上语言中各通过至少 1 题", "special"),
]

_ACHIEVEMENT_MAP: Dict[str, Achievement] = {a.id: a for a in ACHIEVEMENTS}


def get_achievement(aid: str) -> Optional[Achievement]:
    return _ACHIEVEMENT_MAP.get(aid)


def check_achievements(dao: ProgressDAO) -> List[str]:
    """Check all achievements and return newly earned IDs."""
    earned = _get_earned(dao)
    newly = []

    # Streak checks
    streak = dao.daily_streak()
    for threshold, aid in [(3, "streak_3"), (7, "streak_7"), (14, "streak_14"), (30, "streak_30")]:
        if streak >= threshold and aid not in earned:
            newly.append(aid)

    # Solve count checks
    summary = dao.summary_by_lang()
    total_solved = sum(s.get("solved", 0) for s in summary.values())
    for threshold, aid in [(1, "first_solve"), (10, "solve_10"), (50, "solve_50"),
                           (100, "solve_100"), (200, "solve_200")]:
        if total_solved >= threshold and aid not in earned:
            newly.append(aid)

    # Language first solve
    lang_map = {
        "python": "python_first", "sql": "sql_first",
        "cpp": "cpp_first", "r": "r_first", "agent_dev": "agent_first",
    }
    for lang, aid in lang_map.items():
        if summary.get(lang, {}).get("solved", 0) >= 1 and aid not in earned:
            newly.append(aid)

    # Language half completion
    from core.loader import load_language
    from ui.components import ALL_LANGS
    half_map = {"python": "python_half", "sql": "sql_half", "agent_dev": "agent_half"}
    for lang, aid in half_map.items():
        if aid in earned:
            continue
        total_problems = sum(len(t.problems) for t in load_language(lang))
        solved = summary.get(lang, {}).get("solved", 0)
        if total_problems > 0 and solved >= total_problems * 0.5:
            newly.append(aid)

    # Multi-language
    if "multi_lang" not in earned:
        langs_with_solve = sum(1 for s in summary.values() if s.get("solved", 0) >= 1)
        if langs_with_solve >= 3:
            newly.append("multi_lang")

    # No mistakes
    if "no_mistakes" not in earned:
        mistakes = dao.list_mistakes()
        if not mistakes and total_solved >= 10:
            newly.append("no_mistakes")

    # Path milestones
    if "path_first_milestone" not in earned or "path_agent_done" not in earned or "path_pa_done" not in earned:
        from core.paths import load_all_paths, get_milestone_topics_flat
        from core.loader import load_language as _load_lang
        paths = load_all_paths()
        any_milestone_done = False
        for p in paths:
            all_done = True
            for m in p.milestones:
                topic_problems = []
                for lang_id, topic_slug in get_milestone_topics_flat(m):
                    for t in _load_lang(lang_id):
                        if t.slug == topic_slug:
                            for prob in t.problems:
                                topic_problems.append({"lang": lang_id, "problem_id": prob.id})
                            break
                if not topic_problems:
                    all_done = False
                    continue
                progress = dao.milestone_progress(topic_problems)
                if progress["pct"] >= 1.0:
                    any_milestone_done = True
                else:
                    all_done = False

            if all_done and p.id == "agent_mastery" and "path_agent_done" not in earned:
                newly.append("path_agent_done")
            if all_done and p.id == "people_analytics" and "path_pa_done" not in earned:
                newly.append("path_pa_done")

        if any_milestone_done and "path_first_milestone" not in earned:
            newly.append("path_first_milestone")

    # Persist newly earned + emit events
    for aid in newly:
        _mark_earned(dao, aid)
        try:
            dao.emit_event("achievement_unlocked", payload={"achievement_id": aid})
        except Exception:
            pass

    return newly


def get_all_earned(dao: ProgressDAO) -> List[Achievement]:
    """Return all earned achievements as Achievement objects."""
    earned = _get_earned(dao)
    return [_ACHIEVEMENT_MAP[aid] for aid in earned if aid in _ACHIEVEMENT_MAP]


def get_progress_summary(dao: ProgressDAO) -> Dict:
    """Return achievement progress summary."""
    earned = _get_earned(dao)
    total = len(ACHIEVEMENTS)
    return {"earned": len(earned), "total": total, "pct": len(earned) / total if total else 0}


def get_all_with_state(dao: ProgressDAO) -> List[Dict]:
    """Return all achievements with state: earned / approaching / locked.

    approaching = progress >= 50% of the trigger threshold.
    """
    earned_ids = _get_earned(dao)
    summary = dao.summary_by_lang()
    total_solved = sum(s.get("solved", 0) for s in summary.values())
    streak = dao.daily_streak()
    langs_with_solve = sum(1 for s in summary.values() if s.get("solved", 0) >= 1)

    results = []
    for a in ACHIEVEMENTS:
        if a.id in earned_ids:
            results.append({"achievement": a, "state": "earned", "progress": 1.0})
            continue

        pct = _estimate_progress(a, total_solved, streak, langs_with_solve, summary)
        state = "approaching" if pct >= 0.5 else "locked"
        results.append({"achievement": a, "state": state, "progress": pct})
    return results


def _estimate_progress(a, total_solved: int, streak: int, langs_count: int,
                       summary: Dict) -> float:
    """Estimate progress toward an achievement as 0.0-1.0."""
    thresholds = {
        "streak_3": (streak, 3), "streak_7": (streak, 7),
        "streak_14": (streak, 14), "streak_30": (streak, 30),
        "first_solve": (total_solved, 1), "solve_10": (total_solved, 10),
        "solve_50": (total_solved, 50), "solve_100": (total_solved, 100),
        "solve_200": (total_solved, 200),
        "multi_lang": (langs_count, 3),
    }
    if a.id in thresholds:
        current, target = thresholds[a.id]
        return min(1.0, current / target) if target > 0 else 0.0

    lang_first = {"python_first": "python", "sql_first": "sql",
                  "cpp_first": "cpp", "r_first": "r", "agent_first": "agent_dev"}
    if a.id in lang_first:
        solved = summary.get(lang_first[a.id], {}).get("solved", 0)
        return 1.0 if solved >= 1 else 0.0

    return 0.0


def _get_earned(dao: ProgressDAO) -> set:
    raw = dao.get_meta("achievements_earned", "")
    if not raw:
        return set()
    return set(raw.split(","))


def _mark_earned(dao: ProgressDAO, aid: str) -> None:
    earned = _get_earned(dao)
    earned.add(aid)
    dao.set_meta("achievements_earned", ",".join(sorted(earned)))
