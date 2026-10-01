# -*- coding: utf-8 -*-
"""l930-11：学习路径 YAML「缺口占位文案」命题级防回归桩（l927-53 note §三 可批形状落地）。

命题（l922-11 遗留 1／learn-path-claim-audit-20260924 表一第 4 行）：
`content/paths/*.yaml` 是**对外展示**的学习路径定义，不得出现「还没有／暂无／待解锁／
待补充／待题目／尚未」这类缺口占位话术——出现即说明路径内容未灌满就上了展示面。

三条腿（照 l927-53 可批形状逐条落地）：
  ① 命题断言：GAP 正则对全部 `content/paths/*.yaml` 零命中，命中即红并列「文件:行:原文」；
  ② 有牙自检（照 tests/test_insights_index_closure.py:111 的零写盘做法）：
     断言抽成纯函数 `_gap_hits(text)`，自检喂合成串（含「（待题目新增后解锁）」）要求恰命中 1 处
     ——防"永绿桩"（正则写坏时自检先红）；
  ③ 分工：本件是**命题级**（展示面不许有缺口话术）；分支级证据在
     tests/test_export_cache_hit_path.py（l927-55）——两件互不顶替。

零生产码改动；回滚＝删本文件（无跨件耦合，不触碰 strict-XFAIL 两桩）。
复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_paths_no_gap_claim.py -q
"""
import re
from pathlib import Path

PATHS_DIR = Path(__file__).resolve().parent.parent / "content" / "paths"

# 命题正则（l927-53 note §三 逐字口径）
GAP = re.compile(r"还没有|暂无|待解锁|待补充|待题目|尚未")


def _gap_hits(text: str) -> list:
    """纯函数：返回 [(行号, 行原文)]——有牙自检的注入点（零写盘）。"""
    return [(i, line.strip()) for i, line in enumerate(text.splitlines(), 1) if GAP.search(line)]


def test_paths_yaml_have_no_gap_placeholder_claims():
    """命题断言：全部路径 YAML 零缺口占位话术；命中即红并列出文件:行:原文。"""
    files = sorted(PATHS_DIR.glob("*.yaml"))
    assert files, "content/paths/ 下没有 YAML——目录结构变更，先复查判据对象"
    offenders = []
    for path in files:
        for lineno, line in _gap_hits(path.read_text(encoding="utf-8")):
            offenders.append(f"{path.name}:{lineno}:{line}")
    assert not offenders, (
        f"路径 YAML 出现缺口占位话术 {len(offenders)} 处"
        "（展示面不许有「待灌满」话术，请补齐内容或改写文案）：\n" + "\n".join(offenders)
    )


def test_gap_hits_detector_has_teeth():
    """有牙自检：合成串恰命中 1 处（「（待题目新增后解锁）」命中「待题目」）；干净串零命中。"""
    dirty = "- title: 某章节\n  description: 练习题（待题目新增后解锁）\n- title: 另一章\n"
    hits = _gap_hits(dirty)
    assert len(hits) == 1, f"合成串应恰命中 1 处，实得 {hits}"
    assert "待题目" in hits[0][1]
    assert _gap_hits("- title: 正常章节\n  description: 已有 20 题\n") == [], "干净串不得误伤"
