import glob
import logging
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

logger = logging.getLogger(__name__)

_DEFAULT_CONTENT = str(Path(__file__).resolve().parent.parent / "content")


@dataclass
class Problem:
    id: str
    title: str
    topic: str
    difficulty: int
    tags: list
    statement: str
    starter_code: str
    expected_output: Optional[str] = None
    expected_rows: Optional[list] = None
    setup_sql: Optional[str] = None
    tests: Optional[list] = None
    hints: list = field(default_factory=list)
    judge_mode: str = "run"
    rubric: Optional[str] = None
    reference_answer: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Topic:
    slug: str
    title: str
    lesson_md: str
    problems: List[Problem]


_cache: dict = {}
_cache_key: dict = {}


_H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$", re.MULTILINE)


def _topic_title(slug: str, lesson_md: str) -> str:
    """优先取 _lesson.md 第一个 # 标题；fallback 用 slug 人话化。"""
    if lesson_md:
        m = _H1_RE.search(lesson_md)
        if m:
            return m.group(1).strip()
    s = re.sub(r"^\d+[a-z]?_", "", slug)
    return s.replace("_", " ").strip().title()


_SIG_EXTENSIONS = {".yaml", ".yml", ".md"}


def _signature(lang_dir: str) -> tuple:
    """内容文件 mtime 元组——仅统计 .yaml/.md，避免无关文件触发缓存失效。"""
    sig = []
    for base, _, files in os.walk(lang_dir):
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            if ext not in _SIG_EXTENSIONS:
                continue
            fp = os.path.join(base, f)
            try:
                sig.append((os.path.relpath(fp, lang_dir).replace("\\", "/"), os.path.getmtime(fp)))
            except OSError:
                pass
    return tuple(sig)


def load_language(lang: str, content_dir: Optional[str] = None) -> List[Topic]:
    base = content_dir or _DEFAULT_CONTENT
    lang_dir = os.path.join(base, lang)
    if not os.path.isdir(lang_dir):
        return []

    key = (base, lang)
    sig = _signature(lang_dir)
    if _cache_key.get(key) == sig and key in _cache:
        return _cache[key]

    topics: List[Topic] = []
    for topic_path in sorted(glob.glob(os.path.join(lang_dir, "*/"))):
        slug = os.path.basename(os.path.normpath(topic_path))
        lesson_path = os.path.join(topic_path, "_lesson.md")
        lesson_md = ""
        if os.path.exists(lesson_path):
            try:
                with open(lesson_path, "r", encoding="utf-8") as f:
                    lesson_md = f.read()
            except OSError as e:
                logger.warning("Read lesson failed %s: %s", lesson_path, e)

        problems: List[Problem] = []
        for yaml_path in sorted(glob.glob(os.path.join(topic_path, "*.yaml"))):
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
            except (yaml.YAMLError, OSError) as e:
                logger.warning("Skip broken yaml %s: %s", yaml_path, e)
                continue
            problem_slug = os.path.splitext(os.path.basename(yaml_path))[0]
            pid = f"{lang}/{slug}/{problem_slug}"
            # 防御：tags / hints 是字符串时不要当 iterable 拆字符
            raw_tags = data.get("tags") or []
            tags = list(raw_tags) if isinstance(raw_tags, list) else [str(raw_tags)]
            raw_hints = data.get("hints") or []
            hints = list(raw_hints) if isinstance(raw_hints, list) else [str(raw_hints)]
            # difficulty=0 应保留 0（之前 `or 1` 把 0 强转 1）
            raw_diff = data.get("difficulty")
            difficulty = int(raw_diff) if raw_diff is not None else 1

            # rubric：list 转「- 」要点字符串；空 list -> None；字符串原样
            rubric_raw = data.get("rubric")
            if isinstance(rubric_raw, list):
                rubric = "\n".join("- " + str(item) for item in rubric_raw) or None
            elif rubric_raw is not None:
                rubric = str(rubric_raw)
            else:
                rubric = None

            reference_answer = data.get("reference_answer")

            problems.append(Problem(
                id=pid,
                title=str(data.get("title") or problem_slug),
                topic=str(data.get("topic") or slug),
                difficulty=difficulty,
                tags=tags,
                statement=str(data.get("statement") or ""),
                starter_code=str(data.get("starter_code") or ""),
                expected_output=data.get("expected_output"),
                expected_rows=data.get("expected_rows"),
                setup_sql=data.get("setup_sql"),
                tests=data.get("tests"),
                hints=hints,
                judge_mode=str(data.get("judge_mode") or "run"),
                rubric=rubric,
                reference_answer=reference_answer,
            ))
        topics.append(Topic(
            slug=slug,
            title=_topic_title(slug, lesson_md),
            lesson_md=lesson_md,
            problems=problems,
        ))

    _cache[key] = topics
    _cache_key[key] = sig
    return topics


def find_problem(lang: str, problem_id: str, content_dir: Optional[str] = None):
    for t in load_language(lang, content_dir):
        for p in t.problems:
            if p.id == problem_id:
                return t, p
    return None, None
