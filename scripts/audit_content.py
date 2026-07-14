"""Content quality audit — checks all YAML problem files for completeness and consistency.

Usage:
    python scripts/audit_content.py           # Full audit
    python scripts/audit_content.py --strict  # Warnings are errors (except known accepts)
"""
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ACCEPTED_TOPICS = {"cpp/12_file_io", "r/11_survival", "agent_dev/04_review_agent"}


def audit():
    from core.loader import load_language
    from core.paths import load_all_paths

    errors = []
    warnings = []
    langs = ["python", "sql", "cpp", "r", "agent_dev"]

    for lang in langs:
        topics = load_language(lang, str(ROOT / "content"))
        for topic in topics:
            if not topic.problems:
                warnings.append(f"[{lang}/{topic.slug}] Topic has no problems")
                continue

            if not topic.lesson_md.strip():
                warnings.append(f"[{lang}/{topic.slug}] Missing or empty _lesson.md")
            elif len(topic.lesson_md.strip()) < 200:
                warnings.append(f"[{lang}/{topic.slug}] Lesson too short ({len(topic.lesson_md.strip())} chars)")

            difficulties = [p.difficulty for p in topic.problems]
            for p in topic.problems:
                if not p.statement.strip():
                    errors.append(f"[{p.id}] Missing statement")
                if not p.starter_code.strip() and p.judge_mode != "ai_open":
                    warnings.append(f"[{p.id}] Missing starter_code")
                if p.difficulty < 1 or p.difficulty > 5:
                    errors.append(f"[{p.id}] difficulty={p.difficulty} out of 1-5 range")
                if p.judge_mode == "run":
                    if lang == "sql":
                        if not p.setup_sql and p.expected_rows is None:
                            warnings.append(f"[{p.id}] SQL problem without setup_sql or expected_rows")
                    else:
                        if p.expected_output is None and not p.tests:
                            errors.append(f"[{p.id}] run-mode problem without expected_output or tests")
                elif p.judge_mode == "ai_open":
                    if not p.rubric:
                        errors.append(f"[{p.id}] ai_open problem without rubric")

            if len(difficulties) >= 3:
                if max(difficulties) == min(difficulties):
                    warnings.append(f"[{lang}/{topic.slug}] All problems same difficulty ({difficulties[0]})")
                else:
                    from collections import Counter
                    dist = Counter(difficulties)
                    most_common_count = dist.most_common(1)[0][1]
                    if most_common_count > len(difficulties) * 0.7:
                        warnings.append(f"[{lang}/{topic.slug}] >70% problems at same difficulty")

    paths = load_all_paths()
    for path in paths:
        for m in path.milestones:
            for topic_ref in m.topics:
                parts = topic_ref.split("/", 1)
                if len(parts) == 2:
                    lang_ref, slug_ref = parts
                else:
                    lang_ref, slug_ref = path.id.split("_")[0], parts[0]
                if lang_ref in langs:
                    topics = load_language(lang_ref, str(ROOT / "content"))
                    if not any(t.slug == slug_ref for t in topics):
                        errors.append(f"[path:{path.id}/{m.id}] references non-existent topic: {topic_ref}")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Audit content quality")
    parser.add_argument("--strict", action="store_true", help="Warnings are errors (except accepted)")
    args = parser.parse_args()

    errors, warnings = audit()

    accepted = [w for w in warnings if any(t in w for t in ACCEPTED_TOPICS)]
    unaccepted = [w for w in warnings if not any(t in w for t in ACCEPTED_TOPICS)]

    if unaccepted:
        print(f"WARNINGS ({len(unaccepted)}):")
        for w in unaccepted:
            print(f"  {w}")
        print()

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        print()

    fail_count = len(errors) + (len(unaccepted) if args.strict else 0)
    if fail_count == 0:
        print(f"PASS: 0 errors, {len(accepted)} accepted, {len(unaccepted)} warnings")
    else:
        print(f"FAIL: {len(errors)} errors, {len(unaccepted)} unaccepted warnings")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
