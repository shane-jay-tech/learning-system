from typing import Dict, List, Optional, Tuple

from core.loader import load_language
from core.progress import ProgressDAO
from ui.components import ALL_LANGS

_problems_cache: Optional[List[Dict]] = None
_problems_cache_sig: Optional[object] = None


def all_problems() -> List[Dict]:
    """加载所有题目元数据（带模块级缓存，避免重复扫描）。"""
    global _problems_cache, _problems_cache_sig
    from core.loader import _signature, _DEFAULT_CONTENT
    import os
    sig = tuple(
        _signature(os.path.join(_DEFAULT_CONTENT, lang))
        for lang in ALL_LANGS
        if os.path.isdir(os.path.join(_DEFAULT_CONTENT, lang))
    )
    if _problems_cache is not None and _problems_cache_sig == sig:
        return _problems_cache
    out = []
    for lang in ALL_LANGS:
        for topic in load_language(lang):
            for p in topic.problems:
                out.append({
                    "lang": lang,
                    "topic_slug": topic.slug,
                    "topic_title": topic.title,
                    "problem_id": p.id,
                    "title": p.title,
                    "difficulty": p.difficulty,
                })
    _problems_cache = out
    _problems_cache_sig = sig
    return out


def _topic_weakness(items: List[Dict], status: Dict) -> Dict[str, float]:
    """Per-topic weakness score: higher = weaker (more wrong, fewer solved)."""
    topic_stats: Dict[str, Dict[str, int]] = {}
    for p in items:
        key = f"{p['lang']}/{p['topic_slug']}"
        s = topic_stats.setdefault(key, {"total": 0, "solved": 0, "wrong": 0})
        s["total"] += 1
        st = status.get((p["lang"], p["problem_id"]))
        if st == "solved":
            s["solved"] += 1
        elif st == "wrong":
            s["wrong"] += 1

    weakness = {}
    for key, s in topic_stats.items():
        if s["total"] == 0:
            continue
        pass_rate = s["solved"] / s["total"]
        fail_rate = s["wrong"] / s["total"]
        weakness[key] = fail_rate * 2 + (1 - pass_rate)
    return weakness


def _due_reviews_from_state(dao: ProgressDAO) -> set:
    """从 review_state 表获取到期复习题目，由真实间隔算法驱动（轻量 id 查询）。"""
    return dao.due_review_ids(limit=1000)


def recommend(n: int = 5, dao: Optional[ProgressDAO] = None) -> List[Dict]:
    """Smart recommender with priority:
    阻塞路径错题 → 到期复习 → 当前路径下一题 → 弱项巩固 → 跨路径互补 → 探索新题.

    Each item has a 'reason' field explaining why it's recommended.
    """
    own = dao is None
    d = dao or ProgressDAO()
    try:
        items = all_problems()
        wrong_ids = {(m["lang"], m["problem_id"]) for m in d.list_mistakes()}
        status = d.all_problems_status()
        weakness = _topic_weakness(items, status)
        due_review = _due_reviews_from_state(d)
        path_next = _path_next_problems(d, status)
        path_blocking = _path_blocking_wrong(d, wrong_ids)
    finally:
        if own:
            d.close()

    # 1. Path-blocking wrong (错题阻碍路径推进)
    blocking = [p for p in items if (p["lang"], p["problem_id"]) in path_blocking]
    blocking.sort(key=lambda x: -weakness.get(f"{x['lang']}/{x['topic_slug']}", 0))

    # 2. Due reviews
    review = [p for p in items if (p["lang"], p["problem_id"]) in due_review
              and (p["lang"], p["problem_id"]) not in wrong_ids]
    review.sort(key=lambda x: x["difficulty"])

    # 3. Path next (当前路径下一题)
    path_items = [p for p in items if (p["lang"], p["problem_id"]) in path_next]

    # 4. Weak topic unseen
    weak_topics = {k for k, v in weakness.items() if v > 0.5}
    unseen = [p for p in items if status.get((p["lang"], p["problem_id"])) is None]
    unseen_weak = [p for p in unseen if f"{p['lang']}/{p['topic_slug']}" in weak_topics
                   and (p["lang"], p["problem_id"]) not in path_next]
    unseen_weak.sort(key=lambda x: (
        -weakness.get(f"{x['lang']}/{x['topic_slug']}", 0), x["difficulty"]))

    # 5. Non-blocking wrong
    other_wrong = [p for p in items if (p["lang"], p["problem_id"]) in wrong_ids
                   and (p["lang"], p["problem_id"]) not in path_blocking]
    other_wrong.sort(key=lambda x: -weakness.get(f"{x['lang']}/{x['topic_slug']}", 0))

    # 6. Explore new
    unseen_new = [p for p in unseen if f"{p['lang']}/{p['topic_slug']}" not in weak_topics
                  and (p["lang"], p["problem_id"]) not in path_next]
    unseen_new.sort(key=lambda x: (x["difficulty"], x["problem_id"]))

    plan: List[Dict] = []
    seen_ids: set = set()

    def _fill(source, reason, reason_code, limit=None):
        count = 0
        for p in source:
            if len(plan) >= n:
                break
            if limit and count >= limit:
                break
            key = (p["lang"], p["problem_id"])
            if key in seen_ids:
                continue
            seen_ids.add(key)
            plan.append({**p, "reason": reason, "reason_code": reason_code})
            count += 1

    _fill(blocking, "路径阻塞错题", "path_blocking", 2)
    _fill(review, "到期复习", "review_due", 2)
    _fill(path_items, "路径下一题", "path_next", 2)
    _fill(unseen_weak, "弱项巩固", "weak_topic")
    _fill(other_wrong, "错题复习", "wrong_retry")
    _fill(unseen_new, "探索新题", "explore")
    return plan[:n]


def _path_next_problems(dao: ProgressDAO, status: Dict) -> set:
    """Find the next unsolved problems in active learning paths."""
    try:
        from core.paths import load_all_paths, get_milestone_topics_flat
        from core.loader import load_language
    except ImportError:
        return set()

    next_set = set()
    for path in load_all_paths():
        for m in path.milestones:
            found_unsolved = False
            for lang, topic_slug in get_milestone_topics_flat(m):
                for t in load_language(lang):
                    if t.slug == topic_slug:
                        for p in t.problems:
                            if status.get((lang, p.id)) is None or status.get((lang, p.id)) == "wrong":
                                next_set.add((lang, p.id))
                                found_unsolved = True
                                break
                        break
                if found_unsolved:
                    break
            if found_unsolved:
                break
    return next_set


def _path_blocking_wrong(dao: ProgressDAO, wrong_ids: set) -> set:
    """Find wrong problems that block path milestone completion."""
    try:
        from core.paths import load_all_paths, get_milestone_topics_flat
        from core.loader import load_language
    except ImportError:
        return set()

    blocking = set()
    for path in load_all_paths():
        for m in path.milestones:
            for lang, topic_slug in get_milestone_topics_flat(m):
                for t in load_language(lang):
                    if t.slug == topic_slug:
                        for p in t.problems:
                            if (lang, p.id) in wrong_ids:
                                blocking.add((lang, p.id))
                        break
    return blocking


# ===== 多路径交叉推荐 =====

_CROSS_LINKS: List[Dict] = [
    # Agent 路径用户 → 推荐 Python 进阶（帮助读懂 agent 代码）
    {"from_path": "agent_mastery", "from_milestone": "a2",
     "suggest_topics": ["python/07_dicts_sets", "python/08_files_exceptions"],
     "reason": "读代码时常见字典和文件操作"},
    {"from_path": "agent_mastery", "from_milestone": "a3",
     "suggest_topics": ["python/06_strings", "python/19_regex"],
     "reason": "写 Spec 时需要处理文本和格式"},
    {"from_path": "agent_mastery", "from_milestone": "a5",
     "suggest_topics": ["python/16_classes_oop"],
     "reason": "理解模块化设计的面向对象基础"},
    # People Analytics 路径用户 → 推荐 Agent 技能（自动化分析流程）
    {"from_path": "people_analytics", "from_milestone": "m3",
     "suggest_topics": ["agent_dev/01_git_basics"],
     "reason": "版本管理保护你的分析脚本"},
    {"from_path": "people_analytics", "from_milestone": "m6",
     "suggest_topics": ["agent_dev/03_spec_writing"],
     "reason": "学会写需求让 AI 帮你生成 SQL"},
    {"from_path": "people_analytics", "from_milestone": "m10",
     "suggest_topics": ["agent_dev/09_decompose", "agent_dev/10_debug_logs"],
     "reason": "让 AI 帮你自动化重复的分析工作"},
    # 统计速成线用户 → 推荐数据处理补充
    {"from_path": "quick_stats", "from_milestone": "s3",
     "suggest_topics": ["python/13_scipy_stats"],
     "reason": "Python 也能跑统计，多一条路"},
    {"from_path": "quick_stats", "from_milestone": "s4",
     "suggest_topics": ["sql/01_select_where", "sql/02_aggregate"],
     "reason": "从数据库取数据比手动导入快得多"},
]


def cross_recommend(n: int = 3, dao: Optional[ProgressDAO] = None) -> List[Dict]:
    """跨路径推荐：根据用户已完成的里程碑，推荐其他路径/语言的互补内容。

    Returns items with extra 'cross_reason' field explaining why.
    """
    from core.paths import load_all_paths, get_milestone_topics_flat

    own = dao is None
    d = dao or ProgressDAO()
    try:
        status = d.all_problems_status()
        items = all_problems()
        completed_milestones = _detect_completed_milestones(d)

        if not completed_milestones:
            return []

        candidates = []
        seen_topics = set()

        for link in _CROSS_LINKS:
            key = (link["from_path"], link["from_milestone"])
            if key not in completed_milestones:
                continue
            for topic_ref in link["suggest_topics"]:
                if topic_ref in seen_topics:
                    continue
                seen_topics.add(topic_ref)
                parts = topic_ref.split("/", 1)
                if len(parts) != 2:
                    continue
                lang, topic_slug = parts
                unseen_in_topic = [
                    p for p in items
                    if p["lang"] == lang and p["topic_slug"] == topic_slug
                    and status.get((p["lang"], p["problem_id"])) is None
                ]
                if unseen_in_topic:
                    pick = min(unseen_in_topic, key=lambda x: x["difficulty"])
                    candidates.append({**pick, "cross_reason": link["reason"]})

        return candidates[:n]
    finally:
        if own:
            d.close()


def _detect_completed_milestones(dao: ProgressDAO) -> set:
    """检测用户已完成哪些路径里程碑。返回 {(path_id, milestone_id), ...}。"""
    from core.paths import load_all_paths, get_milestone_topics_flat
    from core.loader import load_language

    completed = set()
    for path in load_all_paths():
        for m in path.milestones:
            topic_problems = []
            for lang, topic_slug in get_milestone_topics_flat(m):
                for t in load_language(lang):
                    if t.slug == topic_slug:
                        for p in t.problems:
                            topic_problems.append({"lang": lang, "problem_id": p.id})
                        break
            if not topic_problems:
                continue
            progress = dao.milestone_progress(topic_problems)
            if progress["pct"] >= 1.0:
                completed.add((path.id, m.id))
    return completed
