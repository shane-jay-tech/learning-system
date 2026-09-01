"""Auto-generate system report metrics from source code.

Usage:
    python scripts/generate_system_report.py              # Print metrics
    python scripts/generate_system_report.py --check FILE # Verify report numbers
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def count_problems():
    from core.loader import load_language
    langs = ["python", "sql", "cpp", "r", "agent_dev"]
    result = {}
    total = 0
    for lang in langs:
        topics = load_language(lang, str(ROOT / "content"))
        n_topics = len(topics)
        n_problems = sum(len(t.problems) for t in topics)
        result[lang] = {"topics": n_topics, "problems": n_problems}
        total += n_problems
    result["_total_problems"] = total
    result["_total_topics"] = sum(v["topics"] for k, v in result.items() if not k.startswith("_"))
    return result


def count_lessons():
    count = 0
    content_dir = ROOT / "content"
    for md in content_dir.rglob("_lesson.md"):
        if md.stat().st_size > 0:
            count += 1
    return count


def count_paths():
    paths_dir = ROOT / "content" / "paths"
    if not paths_dir.exists():
        return 0
    return len(list(paths_dir.glob("*.yaml")))


def get_paths_detail():
    import yaml
    paths_dir = ROOT / "content" / "paths"
    if not paths_dir.exists():
        return {}
    result = {}
    for f in sorted(paths_dir.glob("*.yaml")):
        with open(f, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        slug = f.stem
        result[slug] = {
            "title": data.get("title", slug),
            "milestones": len(data.get("milestones", [])),
            "estimated_hours": data.get("estimated_hours", 0),
        }
    return result


_SKIP_DIRS = {".venv", "__pycache__", "node_modules", ".git", ".pytest_cache"}


def count_source_lines():
    import os
    result = {"core": 0, "ui": 0, "tests": 0, "scripts": 0, "other": 0, "total": 0}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            fpath = Path(dirpath) / fname
            rel = fpath.relative_to(ROOT)
            parts = rel.parts
            lines = len(fpath.read_text(encoding="utf-8", errors="replace").splitlines())
            if parts[0] == "core":
                result["core"] += lines
            elif parts[0] == "ui":
                result["ui"] += lines
            elif parts[0] == "tests":
                result["tests"] += lines
            elif parts[0] == "scripts":
                result["scripts"] += lines
            else:
                result["other"] += lines
            result["total"] += lines
    return result


def count_tests(strict=False):
    """Count test cases. Default uses fast regex; --strict uses pytest collection."""
    if strict:
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q", str(ROOT / "tests")],
                capture_output=True, text=True, cwd=str(ROOT), timeout=30
            )
            m = re.search(r"(\d+) tests? collected", proc.stdout)
            if m:
                return int(m.group(1))
        except Exception:
            pass
    count = 0
    for f in (ROOT / "tests").glob("test_*.py"):
        text = f.read_text(encoding="utf-8", errors="replace")
        # 允许行首缩进：类内的 def test_ 也要计入
        count += len(re.findall(r"^\s*def test_", text, re.MULTILINE))
    return count


def get_version():
    from core.version import VERSION, RELEASE_DATE
    return VERSION, RELEASE_DATE


def generate_metrics(strict=False):
    version, release_date = get_version()
    problems = count_problems()
    lessons = count_lessons()
    paths = count_paths()
    paths_detail = get_paths_detail()
    lines = count_source_lines()
    tests = count_tests(strict=strict)

    return {
        "version": version,
        "release_date": release_date,
        "total_problems": problems["_total_problems"],
        "total_topics": problems["_total_topics"],
        "lessons": lessons,
        "paths": paths,
        "paths_detail": paths_detail,
        "tests": tests,
        "lines": lines,
        "by_lang": {k: v for k, v in problems.items() if not k.startswith("_")},
    }


def print_metrics(metrics):
    print(f"=== 学习平台系统指标 (v{metrics['version']}, {metrics['release_date']}) ===\n")
    print(f"题目总数: {metrics['total_problems']}")
    print(f"知识点数: {metrics['total_topics']}")
    print(f"课程讲解: {metrics['lessons']} 篇")
    print(f"学习路径: {metrics['paths']} 条")
    print(f"测试用例: {metrics['tests']} 个")
    print(f"\n源码行数:")
    for k, v in metrics["lines"].items():
        print(f"  {k}: {v}")
    print(f"\n各语言明细:")
    for lang, data in metrics["by_lang"].items():
        print(f"  {lang}: {data['topics']} topics, {data['problems']} problems")


def _contains_number(text: str, value: int) -> bool:
    """整词匹配：避免 total=5 时 "15"/"50" 之类的裸子串假 PASS。"""
    return re.search(rf"(?<!\d){re.escape(str(value))}(?!\d)", text) is not None


def check_report(filepath, metrics):
    text = Path(filepath).read_text(encoding="utf-8")
    errors = []

    if not _contains_number(text, metrics["total_problems"]):
        errors.append(f"题目总数 {metrics['total_problems']} 未在报告中找到")

    if not _contains_number(text, metrics["total_topics"]):
        errors.append(f"知识点数 {metrics['total_topics']} 未在报告中找到")

    for lang, data in metrics["by_lang"].items():
        if not _contains_number(text, data["problems"]):
            errors.append(f"{lang} 题目数 {data['problems']} 未在报告中找到")

    for slug, pdata in metrics.get("paths_detail", {}).items():
        ms = str(pdata["milestones"])
        title = pdata["title"]
        title_key = title.replace("主线", "").replace("线", "").strip()
        found = False
        for line in text.splitlines():
            if title_key in line and _contains_number(line, pdata["milestones"]):
                found = True
                break
        if not found:
            errors.append(f"路径「{title}」里程碑数 {ms} 未在同一行找到（查找关键词：{title_key}）")

    if errors:
        print("FAIL: 报告数字与实测不一致:")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("PASS: 报告数字与实测一致")
        return True


def check_readme(readme_path, metrics):
    """Check README title version, key numbers, and roadmap."""
    text = Path(readme_path).read_text(encoding="utf-8")
    errors = []
    version = metrics["version"]

    first_line = text.split("\n", 1)[0]
    if version not in first_line:
        errors.append(f"README 标题版本不含 {version}（当前：{first_line.strip()}）")

    if not _contains_number(text, metrics["total_problems"]):
        errors.append(f"README 未包含题目数 {metrics['total_problems']}")

    if not _contains_number(text, metrics["total_topics"]):
        errors.append(f"README 未包含知识点数 {metrics['total_topics']}")

    if f"v{version}" not in text:
        errors.append(f"README 路线图中未包含当前版本 v{version}")

    if errors:
        print("FAIL: README 检查不通过:")
        for e in errors:
            print(f"  - {e}")
        return False
    else:
        print("PASS: README 版本、数字与路线一致")
        return True


def main():
    parser = argparse.ArgumentParser(description="Generate or check system report metrics")
    parser.add_argument("--check", metavar="FILE", help="Check report file against live metrics")
    parser.add_argument("--check-readme", metavar="FILE", help="Check README version matches")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--strict", action="store_true", help="Use pytest collection for test count (slower)")
    args = parser.parse_args()

    metrics = generate_metrics(strict=args.strict)

    if args.check:
        ok = check_report(args.check, metrics)
        if args.check_readme:
            ok = check_readme(args.check_readme, metrics) and ok
        sys.exit(0 if ok else 1)
    elif args.check_readme:
        ok = check_readme(args.check_readme, metrics)
        sys.exit(0 if ok else 1)
    elif args.json:
        print(json.dumps(metrics, ensure_ascii=False, indent=2))
    else:
        print_metrics(metrics)


if __name__ == "__main__":
    main()
