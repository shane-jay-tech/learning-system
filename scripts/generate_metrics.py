# -*- coding: utf-8 -*-
"""最小归仓版 metrics 出口（l918-07）。

历史：172e7e0 提及 generate_metrics 命令但脚本未随仓留存（README 399 题官方口径因此不可复核）。
本脚本归仓该出口：转调 scripts/generate_system_report.py 的 generate_metrics 实现（单一真源），
以 JSON 输出 dict（含 total_problems/total_topics/paths/by_lang）。

用法：python scripts/generate_metrics.py
"""
import json

from generate_system_report import generate_metrics

if __name__ == "__main__":
    metrics = generate_metrics()
    print(json.dumps({
        "total_problems": metrics["total_problems"],
        "total_topics": metrics["total_topics"],
        "paths": metrics["paths"],
        "paths_detail": metrics["paths_detail"],
        "by_lang": metrics["by_lang"],
    }, ensure_ascii=False, indent=1))
