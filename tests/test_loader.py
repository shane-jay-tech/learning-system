import textwrap
from pathlib import Path

from core.loader import load_language, find_problem


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")


def test_load_language_basic(tmp_path):
    base = tmp_path / "content"
    topic_dir = base / "python" / "01_demo"
    _write(topic_dir / "_lesson.md", "# 测试讲解\n内容")
    _write(topic_dir / "01_one.yaml", """\
        title: 第一题
        topic: 01_demo
        difficulty: 1
        tags: [io]
        statement: 输出 1
        starter_code: |
          print(1)
        expected_output: |
          1
        hints:
          - 用 print
    """)
    topics = load_language("python", content_dir=str(base))
    assert len(topics) == 1
    t = topics[0]
    assert t.slug == "01_demo"
    assert "测试讲解" in t.lesson_md
    assert len(t.problems) == 1
    p = t.problems[0]
    assert p.id == "python/01_demo/01_one"
    assert p.title == "第一题"
    assert p.expected_output.strip() == "1"
    assert p.hints == ["用 print"]


def test_find_problem(tmp_path):
    base = tmp_path / "content"
    topic_dir = base / "sql" / "01_t"
    _write(topic_dir / "01_q.yaml", """\
        title: SQL Q
        topic: 01_t
        difficulty: 1
        tags: []
        statement: ''
        starter_code: ''
        expected_output: 1
    """)
    topic, problem = find_problem("sql", "sql/01_t/01_q", content_dir=str(base))
    assert topic is not None
    assert problem.title == "SQL Q"


def test_missing_language_returns_empty(tmp_path):
    assert load_language("nope", content_dir=str(tmp_path)) == []


def test_cache_invalidates_on_file_change(tmp_path):
    base = tmp_path / "content"
    topic_dir = base / "python" / "01_x"
    _write(topic_dir / "_lesson.md", "v1")
    _write(topic_dir / "01_q.yaml", "title: t\ntopic: 01_x\ndifficulty: 1\ntags: []\nstatement: ''\nstarter_code: ''\nexpected_output: 'a'\n")
    t1 = load_language("python", content_dir=str(base))
    assert "v1" in t1[0].lesson_md
    import time as _t
    _t.sleep(0.05)
    (topic_dir / "_lesson.md").write_text("v2", encoding="utf-8")
    # Force mtime bump in case the filesystem clock granularity hides the change.
    import os as _os
    _os.utime(topic_dir / "_lesson.md", None)
    t2 = load_language("python", content_dir=str(base))
    assert "v2" in t2[0].lesson_md
