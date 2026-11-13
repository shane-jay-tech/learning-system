# -*- coding: utf-8 -*-
"""内容等值点哨兵（l1114 任务4）——README 对外口径与磁盘实况的对账桩。

README.md「437 题、85 知识点」与三处版本串副本（:1 标题 / :3 正文 / :72 亮点标题）
是 plan.md「版本等值点登记」的对外承诺面。此前靠人肉自觉（plan.md 登记表原话
「无哨兵（人肉自觉）」），本档把全部等值点钉成断言：

  ① 题数：content/**/{*.yaml} 题目文件（剔除 content/paths/ 路径定义）== 437；
  ② 知识点数：content/{python,sql,cpp,r,agent_dev}/ 的 topic 目录数 == 85；
  ③ 版本串：core/version.py VERSION 出现在 README 三处副本；
  ④ README 文本里的「437 题、85 知识点」数字与 ①② 实测一致。

任何一侧漂移（补题/删题/改版本号漏改 README，或 README 抢跑）都会红。
补题翻代时：改 content/ 的同批必须同步本桩钉值与 README:54 —— 三点一批改。
"""
from pathlib import Path

from core.version import VERSION

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content"

# 与 ui.components.ALL_LANGS 同轴（R-04：语言轴单一来源）；此处直接引以防两处漂移
from ui.components import ALL_LANGS  # noqa: E402

EXPECTED_PROBLEMS = 437   # l1028-05 世代（408→437）
EXPECTED_TOPICS = 85
README_COPIES = {  # plan.md「版本等值点登记」#2/#3/#4 三处副本
    "title": f"（{VERSION}）",       # README:1 标题尾
    "body": f"v{VERSION}",           # README:3 正文「当前版本 vX.Y.Z」
    "highlight": f"（v{VERSION}）",  # README:72 亮点标题
}


def _problem_yaml_files():
    """题目文件口径：content/<lang>/<topic>/<problem>.yaml（content/paths/ 是路径定义非题目）。"""
    return sorted(
        p for p in CONTENT_DIR.rglob("*.yaml")
        if p.relative_to(CONTENT_DIR).parts[0] != "paths"
    )


def _topic_dirs():
    """知识点口径：五语言下的直接子目录（每目录一 topic）。"""
    out = []
    for lang in ALL_LANGS:
        lang_dir = CONTENT_DIR / lang
        assert lang_dir.is_dir(), f"content/{lang}/ 不存在——语言轴与磁盘漂移"
        out.extend(d for d in lang_dir.iterdir() if d.is_dir())
    return sorted(out)


def test_题数_437_yaml文件口径():
    files = _problem_yaml_files()
    assert len(files) == EXPECTED_PROBLEMS, (
        f"题目 yaml 实测 {len(files)} != {EXPECTED_PROBLEMS}——题库总量漂移。"
        "补题/删题须同批翻本桩、tests/test_content_census.py 钉值与 README:54（三点一批）")


def test_题数_与loader实载对账():
    """yaml 文件口径与 core.loader 实载口径互证——两口径分叉即红（防 loader 静默吞题）。"""
    from core.loader import load_language
    loader_total = sum(
        len(topic.problems) for lang in ALL_LANGS for topic in load_language(lang)
    )
    assert loader_total == len(_problem_yaml_files()) == EXPECTED_PROBLEMS


def test_知识点数_85_topic目录口径():
    topics = _topic_dirs()
    assert len(topics) == EXPECTED_TOPICS, (
        f"知识点（topic 目录）实测 {len(topics)} != {EXPECTED_TOPICS}——"
        "扩知识点须同批翻本桩与 README:54")


def test_README计数串与实测一致():
    """README「437 题、85 知识点、6 条学习路径」逐数字与磁盘实取对账（含 6 条路径）。"""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    n_paths = len(list((CONTENT_DIR / "paths").glob("*.yaml")))
    expected = f"{EXPECTED_PROBLEMS} 题、{EXPECTED_TOPICS} 知识点、{n_paths} 条学习路径"
    assert expected in readme, (
        f"README 未含实况口径「{expected}」——README 计数与 content/ 磁盘漂移，先修文档数字")


def test_版本串_core单源与README三副本一致():
    """core/version.py 为版本唯一单源；README 三处副本（标题/正文/亮点）必须同版。"""
    readme_lines = (REPO_ROOT / "README.md").read_text(encoding="utf-8").splitlines()
    # 副本1：首行标题「……（0.6.5）」
    assert readme_lines[0].endswith(README_COPIES["title"]), (
        f"README:1 标题版本副本漂移：{readme_lines[0]!r} 应以 {README_COPIES['title']!r} 收尾")
    # 副本2：正文「当前版本 v0.6.5」
    assert readme_lines[2].count(README_COPIES["body"]) == 1, (
        f"README:3 正文版本副本漂移：应恰含一次 {README_COPIES['body']!r}")
    # 副本3：亮点标题「## 当前能力亮点（v0.6.5）」——按内容定位（行号易碎）
    hits = [l for l in readme_lines if l.startswith("## 当前能力亮点")]
    assert len(hits) == 1 and hits[0].endswith(README_COPIES["highlight"]), (
        f"README 亮点标题版本副本漂移：{hits!r} 应以 {README_COPIES['highlight']!r} 收尾")


def test_README不含旧版本串残迹():
    """防升版后 README 残留旧版本号（副本改漏一处即红）。"""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    major, minor, _patch = VERSION.split(".")
    prev_minor = f"v{major}.{int(minor) - 1}."  # 0.6.5 ⇒ v0.5.
    assert prev_minor not in readme and f"（{major}.{int(minor) - 1}." not in readme, (
        f"README 残留上一代版本串 {prev_minor}*——升版改漏副本")
