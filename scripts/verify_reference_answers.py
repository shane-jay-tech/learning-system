"""参考解对拍工具（l1002-15 收编自 tmp/l923_verify_new_questions.py，l923-03 台账 73 承接）。

判据＝学生答对的那条路径：PythonRunner 跑**参考解**，stdout 经 core.judge._normalize
后与题面 expected_output 逐字节相等。把「expected_output 与参考解零绑定」（l923-03 🔴）
从无守卫升为可跑门禁。

口径边界（有意为之）：
- 参考解**内嵌**于本脚本 REFS（题面 yaml 不加 reference_solution 字段——内容 schema
  变更需有意授权，见 l923-03 遗留）；新绑题在此追加 REFS 条目。
- datasets 类题（sklearn/随机 fold）**不收**（l923-27：随机性复算超最小落地）。
- 退出码：全对 0；任一 MISMATCH/LOAD FAIL 1；--help 2 由 argparse 自带。

用法：
    python scripts/verify_reference_answers.py                 # 全量 REFS
    python scripts/verify_reference_answers.py --lang python   # 按语言
    python scripts/verify_reference_answers.py --topic 20_numpy_basics
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.judge import _normalize  # noqa: E402
from core.loader import find_problem  # noqa: E402
from core.runners.python_runner import PythonRunner  # noqa: E402

REFS = {
    "python/20_numpy_basics/04_shape_and_sum": (
        "import numpy as np\n\n"
        "stock = np.array([12, 7, 0, 25, 3])\n\n"
        'print(f"形状: {stock.shape}")\n'
        'print(f"总件数: {stock.sum()}")\n'
    ),
    "python/20_numpy_basics/05_price_uplift": (
        "import numpy as np\n\n"
        "prices = np.array([100.0, 120.0, 90.0, 150.0])\n\n"
        "new_prices = prices * 1.08\n"
        "for p in new_prices:\n"
        '    print(f"{p:.2f}")\n'
        'print(f"均值: {new_prices.mean():.1f}")\n'
    ),
    "python/21_datetime_ts/04_finish_date": (
        "from datetime import date, timedelta\n\n"
        "start = date(2024, 3, 1)\n"
        "duration = 45\n\n"
        "done = start + timedelta(days=duration)\n"
        "print(done.strftime('%Y-%m-%d'))\n"
    ),
    "python/21_datetime_ts/05_attendance_duration": (
        "from datetime import datetime\n\n"
        'check_in = "2024-06-10 08:30"\n'
        'check_out = "2024-06-10 11:45"\n\n'
        "fmt = '%Y-%m-%d %H:%M'\n"
        "ci = datetime.strptime(check_in, fmt)\n"
        "co = datetime.strptime(check_out, fmt)\n"
        "secs = (co - ci).total_seconds()\n"
        'print(f"时长: {secs / 3600:.2f} 小时")\n'
        'print(f"换算: {int(secs // 3600)}小时{int(secs % 3600 // 60)}分钟")\n'
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="参考解对拍：PythonRunner 跑 REFS 参考解，_normalize 后与 expected_output 逐字节比对")
    parser.add_argument("--lang", default=None, help="按语言过滤（如 python）")
    parser.add_argument("--topic", default=None, help="按 topic 目录名过滤（如 20_numpy_basics）")
    args = parser.parse_args()

    selected = {
        pid: code for pid, code in REFS.items()
        if (args.lang is None or pid.startswith(args.lang + "/"))
        and (args.topic is None or f"/{args.topic}/" in pid)
    }
    if not selected:
        print(f"过滤后无题：lang={args.lang} topic={args.topic}（REFS 全量 {len(REFS)} 条）")
        return 1

    failed = []
    for pid, code in selected.items():
        lang = pid.split("/")[0]
        topic, problem = find_problem(lang, pid)
        if problem is None:
            print("LOAD FAIL", pid)
            failed.append(pid)
            continue
        res = PythonRunner().run(code)
        exp = _normalize(problem.expected_output, lang)
        act = _normalize(res.stdout, lang)
        ok = res.ok and act == exp
        print("---", pid, "difficulty=%s hints=%s judge_mode=%s" % (
            problem.difficulty, len(problem.hints), problem.judge_mode))
        print("    returncode=%s stderr=%r" % (res.exit_code, res.stderr.strip()[:120]))
        print("    expected=%r" % exp)
        print("    actual  =%r" % act)
        print("    MATCH" if ok else "    MISMATCH")
        if not ok:
            failed.append(pid)

    import numpy
    print("=== interpreter:", sys.executable, "| numpy", numpy.__version__,
          "| checked:", len(selected), "| fail:", failed or "none")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
