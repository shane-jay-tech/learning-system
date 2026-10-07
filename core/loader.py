import glob
import logging
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml

logger = logging.getLogger(__name__)

_DEFAULT_CONTENT = str(Path(__file__).resolve().parent.parent / "content")


def content_root() -> str:
    """内容根目录公开出口（l1002-85，l923-19 遗留：跨模块消费方不再摸 _DEFAULT_CONTENT 私有名）。

    返回现值而非拷贝——monkeypatch.setattr(loader, "_DEFAULT_CONTENT", …) 的测试手法
    仍生效（函数每次现读模块全局）。
    """
    return _DEFAULT_CONTENT



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


@dataclass
class LoadDiag:
    """单条坏文件诊断：路径 + 错误类型 + 消息摘要（隔离，不中断整批）。

    error_type 分组口径（l1007-32）：内容错 {YAMLError, UnicodeDecodeError, OSError}
    vs 结构错 {TypeError, ValueError, AttributeError}——新消费方按 error_type ∈ 两组
    分组，勿匹配 message 文本。"""
    path: str
    error_type: str
    message: str


_cache: dict = {}
_cache_key: dict = {}
_last_load_errors: List[LoadDiag] = []


def get_load_diagnostics() -> List[LoadDiag]:
    """最近一次 load_language 实际加载（缓存未命中）收集到的坏文件诊断。"""
    return list(_last_load_errors)


def _record_load_error(yaml_path: str, exc: BaseException) -> None:
    # l1007-02 同族（l1004-04 遗留）：[:200] 头切吃掉异常尾部（出错位置通常在 message 尾），
    # 改头尾保留——头＋省略标记＋尾总量 ≤200：头 115（异常类型/上下文）＋尾 60（出错点）＋标记。
    full = str(exc)
    if len(full) <= 200:
        message = full
    else:
        tail = full[-60:]
        head_n = 200 - len(tail) - 30  # 30 = 省略标记长度上限余量
        message = full[:head_n] + f"...[中段省略 {len(full) - head_n - 60} 字符]..." + tail
    _last_load_errors.append(
        LoadDiag(path=str(yaml_path), error_type=type(exc).__name__,
                 message=message)
    )
    logger.warning("Isolate broken content file %s: %s: %s",
                   yaml_path, type(exc).__name__, message)


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

# 性能关键：_signature 的 os.walk 一次约 10-20ms，而单次页面渲染会通过
# load_language 触发上百次（推荐/成就/路径扫描各自循环调用）。
# 加一个 2 秒 TTL 的 memo：同一次渲染内所有调用共享一次扫描结果，
# 页面渲染时间因此从 1.2s+ 降到 ~100ms。2 秒的陈旧窗口对「改题后刷新」无感。
_SIG_TTL_SEC = 2.0
_sig_cache: dict = {}  # lang_dir -> (sig, monotonic_ts)


def _signature(lang_dir: str) -> tuple:
    """内容文件 mtime 元组——仅统计 .yaml/.md，避免无关文件触发缓存失效。"""
    now = time.monotonic()
    hit = _sig_cache.get(lang_dir)
    if hit is not None and now - hit[1] < _SIG_TTL_SEC:
        return hit[0]
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
    sig = tuple(sig)
    _sig_cache[lang_dir] = (sig, now)
    return sig


def invalidate_cache() -> None:
    """清空题库缓存（含签名 memo）。测试与性能基线使用；正常运行时无需调用。"""
    _cache.clear()
    _cache_key.clear()
    _sig_cache.clear()


def load_language(lang: str, content_dir: Optional[str] = None) -> List[Topic]:
    base = content_dir or _DEFAULT_CONTENT
    lang_dir = os.path.join(base, lang)
    _last_load_errors.clear()
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
            # 错误分组口径（l1007-32 执行，l1007-18 遗留——新消费方分组按 error_type 勿匹配 message）：
            #   内容错组 = {YAMLError, UnicodeDecodeError, OSError}（yaml 语法/编码/IO——文件本身的问题）；
            #   结构错组 = {TypeError, ValueError, AttributeError}（yaml 可解析但字段形状/类型/缺键——内容对形态错）。
            # 两组对应下方三个 except 捕获段与 _record_load_error 的 error_type 记录面。
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
            except (yaml.YAMLError, OSError, UnicodeDecodeError) as e:
                _record_load_error(yaml_path, e)
                continue
            if not isinstance(data, dict):
                _record_load_error(
                    yaml_path,
                    TypeError(f"yaml root is {type(data).__name__}, expected mapping"))
                continue
            try:
                problem = _build_problem(lang, slug, yaml_path, data)
            except (TypeError, ValueError, AttributeError) as e:
                _record_load_error(yaml_path, e)
                continue
            problems.append(problem)
        topics.append(Topic(
            slug=slug,
            title=_topic_title(slug, lesson_md),
            lesson_md=lesson_md,
            problems=problems,
        ))

    _cache[key] = topics
    _cache_key[key] = sig
    return topics


def _build_problem(lang: str, slug: str, yaml_path: str, data: dict) -> Problem:
    """data → Problem 的字段转换；转换异常由调用方隔离为诊断记录。"""
    problem_slug = os.path.splitext(os.path.basename(yaml_path))[0]
    pid = f"{lang}/{slug}/{problem_slug}"
    # 防御：tags / hints 是字符串时不要当 iterable 拆字符
    raw_tags = data.get("tags") or []
    tags = list(raw_tags) if isinstance(raw_tags, list) else [str(raw_tags)]
    raw_hints = data.get("hints") or []
    hints = list(raw_hints) if isinstance(raw_hints, list) else [str(raw_hints)]
    # l1006-05/l1004-15：「1-3 条」契约的机器夹钳——超界行截断（内容源头已合并整改，
    # 此处防未来手写/AI 写越界；截断留档见 yaml 原文）
    hints = hints[:3]
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

    return Problem(
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
        reference_answer=data.get("reference_answer"),
    )


def find_problem(lang: str, problem_id: str, content_dir: Optional[str] = None):
    for t in load_language(lang, content_dir):
        for p in t.problems:
            if p.id == problem_id:
                return t, p
    return None, None
