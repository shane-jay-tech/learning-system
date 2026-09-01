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
    from core import loader
    loader.invalidate_cache()  # 签名 memo 有 TTL，显式失效保证测试立即感知
    t2 = load_language("python", content_dir=str(base))
    assert "v2" in t2[0].lesson_md

def test_signature_memo_expires_after_ttl(tmp_path):
    """签名 memo 有 TTL：过期后自动重新扫描并感知文件变化。"""
    from core import loader
    base = tmp_path / "content"
    topic_dir = base / "python" / "01_x"
    _write(topic_dir / "_lesson.md", "v1")
    _write(topic_dir / "01_q.yaml",
           "title: t\ntopic: 01_x\ndifficulty: 1\ntags: []\n"
           "statement: ''\nstarter_code: ''\nexpected_output: 'a'\n")
    t1 = load_language("python", content_dir=str(base))
    assert "v1" in t1[0].lesson_md

    # memo 生效期内改文件：同一渲染内不会重新扫描（性能优化点）
    import time as _t
    import os as _os
    lang_dir = str(topic_dir.parent)
    (topic_dir / "_lesson.md").write_text("v2", encoding="utf-8")
    _os.utime(topic_dir / "_lesson.md", None)
    # 固定 memo 时间戳为"现在"，保证测试不因机器慢而超过 TTL
    _sig, _ = loader._sig_cache[lang_dir]
    loader._sig_cache[lang_dir] = (_sig, _t.monotonic())
    t_same = load_language("python", content_dir=str(base))
    assert "v1" in t_same[0].lesson_md  # TTL 内仍是旧签名

    # 显式失效后立即感知变化
    loader.invalidate_cache()
    t2 = load_language("python", content_dir=str(base))
    assert "v2" in t2[0].lesson_md

    # TTL 过期后自动感知变化（拨回 memo 时间戳模拟过期，避免依赖真实时钟的睡眠）
    _t.sleep(0.05)  # 确保 v3 的 mtime 与 v2 不同（文件系统时间粒度）
    (topic_dir / "_lesson.md").write_text("v3", encoding="utf-8")
    _os.utime(topic_dir / "_lesson.md", None)
    _sig, _ts = loader._sig_cache[lang_dir]
    loader._sig_cache[lang_dir] = (_sig, _t.monotonic() - loader._SIG_TTL_SEC - 1)
    t3 = load_language("python", content_dir=str(base))
    assert "v3" in t3[0].lesson_md
    loader.invalidate_cache()

