"""Performance baseline — measures key operations with multi-sampling.

Usage:
    python scripts/perf_baseline.py          # 5 samples per operation
    python scripts/perf_baseline.py --quick  # 1 sample (CI / quick check)
    python scripts/perf_baseline.py --json   # Output JSON to stdout
"""
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SAMPLES = 5
WARMUP = 1
_quiet = False


def measure_multi(name, fn, target_ms, samples=SAMPLES):
    """Run fn multiple times, report median and p95."""
    for _ in range(WARMUP):
        fn()

    timings = []
    for _ in range(samples):
        start = time.perf_counter()
        fn()
        elapsed_ms = (time.perf_counter() - start) * 1000
        timings.append(elapsed_ms)

    med = statistics.median(timings)
    p95 = sorted(timings)[int(len(timings) * 0.95)] if len(timings) >= 5 else max(timings)
    mn = min(timings)

    ok = med <= target_ms and p95 <= target_ms * 2
    status = "OK" if ok else "SLOW"
    if not _quiet:
        print(f"  [{status}] {name:<40} med={med:>7.1f}ms  p95={p95:>7.1f}ms  min={mn:>7.1f}ms  (target: <{target_ms}ms)")
    return med, status, p95


def measure_once(name, fn, target_ms):
    """Single sample (for quick mode or inherently-cached ops)."""
    start = time.perf_counter()
    fn()
    elapsed_ms = (time.perf_counter() - start) * 1000
    status = "OK" if elapsed_ms <= target_ms else "SLOW"
    if not _quiet:
        print(f"  [{status}] {name:<40} {elapsed_ms:>8.1f}ms (target: <{target_ms}ms)")
    return elapsed_ms, status, None


def main():
    global _quiet
    quick = "--quick" in sys.argv
    json_out = "--json" in sys.argv
    md_out = "--markdown" in sys.argv
    _quiet = json_out or md_out
    samples = 1 if quick else SAMPLES
    mode = "quick (1 sample)" if quick else f"multi-sample ({samples}x + {WARMUP} warmup)"

    if not _quiet:
        print(f"=== Performance Baseline ({mode}) ===\n")

    from core import loader
    from core.recommend import recommend
    from core.progress import ProgressDAO
    from core.report import generate_report
    from scripts.generate_system_report import generate_metrics

    results = []
    json_records = []

    def record(name, target_ms, measure_result):
        med_or_val, status, p95 = measure_result
        results.append((med_or_val, status))
        rec = {"name": name, "median_ms": round(med_or_val, 1), "target_ms": target_ms, "status": status}
        if p95 is not None:
            rec["p95_ms"] = round(p95, 1)
        json_records.append(rec)

    # Cold load — clear cache before each sample（走公开 API，勿动私有字典）
    def cold_load():
        loader.invalidate_cache()
        loader.load_language("python")

    if quick:
        loader.invalidate_cache()
        record("load_language cold", 800, measure_once("load_language('python') cold", lambda: loader.load_language("python"), 800))
    else:
        record("load_language cold", 800, measure_multi("load_language('python') cold", cold_load, 800, samples))

    # Warm load (cached) — single sample is fine since cache hit is deterministic
    loader.load_language("python")  # ensure cached
    record("load_language cached", 100, measure_once("load_language('python') cached", lambda: loader.load_language("python"), 100))

    # Recommend
    if quick:
        record("recommend", 800, measure_once("recommend(n=5)", lambda: recommend(n=5), 800))
    else:
        record("recommend", 800, measure_multi("recommend(n=5)", lambda: recommend(n=5), 800, samples))

    # Report generation
    dao = ProgressDAO()
    if quick:
        record("generate_report", 3000, measure_once("generate_report(days=7)", lambda: generate_report(dao, days=7), 3000))
    else:
        record("generate_report", 3000, measure_multi("generate_report(days=7)", lambda: generate_report(dao, days=7), 3000, samples))
    dao.close()

    # System report metrics (regex-based, fast)
    if quick:
        record("system_metrics", 3500, measure_once("generate_system_report metrics", generate_metrics, 3500))
    else:
        record("system_metrics", 3500, measure_multi("generate_system_report metrics", generate_metrics, 3500, samples))

    slow = sum(1 for _, s in results if s == "SLOW")
    if json_out:
        print(json.dumps(json_records, ensure_ascii=False, indent=2))
    elif md_out:
        print("| 操作 | 中位数 | p95 | 目标 | 状态 |")
        print("|------|--------|-----|------|------|")
        for rec in json_records:
            name = rec["name"]
            med = f"{rec['median_ms']:.0f}ms"
            target = f"<{rec['target_ms']:.0f}ms"
            status = rec["status"]
            p95 = f"{rec.get('p95_ms', rec['median_ms']):.0f}ms" if rec.get("p95_ms") else "—"
            print(f"| {name} | {med} | {p95} | {target} | {status} |")
    else:
        print()
        if slow:
            print(f"WARNING: {slow} operation(s) exceeded target")
        else:
            print("All operations within target")

    return 1 if slow else 0


if __name__ == "__main__":
    sys.exit(main())
