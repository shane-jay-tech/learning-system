# -*- coding: utf-8 -*-
"""hints 展示与条数契约（l1006-05 转正件；用户 2026-10-06 拍板）。

l1004-14 出口②判据转正：**「一次性展示」是正确口径**（用户提问拍板，不采出口①逐级展示）。
原 `test_hints_are_rendered_in_one_pass_without_a_failure_gate` 在
tests/test_mistakes_redo_lifecycle.py 里以「按实况收窄」的身份存在；本件把它挪出为正式契约
测试——判据不再是「实况如此」而是「契约如此」：单 expander 一次遍历、块内唯一渲染点、
无尝试数门控、无会话态前置；组合词扫描保留防暗做逐级展示。

l1004-15 条数契约：`core/ai_generate.py` 对 AI 写的是「hints 1-3 条」；
l1006-05 起该契约在装载层有机器夹钳（`core/loader.py::_build_problem` 的 `hints[:3]`），
本件按全量 content 扫描钉「无越界」——分布现值 1:26 / 2:33 / 3:347 / 4:0（2026-10-07 实测，
两道 4 条题已同批合并整改：agent_dev/05_modular_config/03_split_function 与
r/10_stringr_lubridate/06_date_parsing，语义零丢失）。

复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_hints_disclosure_contract.py -q
"""
import re
from pathlib import Path

import yaml

from core.loader import _build_problem, load_language

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_一次性展示是契约口径_单expander一次遍历无门控():
    """l1004-14 出口②转正：一次性展示＝正确契约（拍板口径），不再以「实况收窄」身份存在。"""
    src = (REPO_ROOT / "ui" / "pages" / "language.py").read_text(encoding="utf-8")

    assert 'if active.get("hints"):' in src
    assert 'st.expander("💡 不会做？看提示", expanded=False)' in src

    block = src.split('if active.get("hints"):')[1].split('\n        with st.expander')[0]
    assert 'for h in active["hints"]:' in block, block
    assert block.count('st.markdown(f"- {h}")') == 1, block
    assert "attempt_count" not in src                      # 没有按尝试次数门控
    assert "if st.session_state" not in block              # 提示块前没有任何会话态条件


def test_组合词扫描_防暗做逐级展示():
    """防暗做：ui/ 全目录扫「提示/hint × level|stage|step|逐级|分档|递进」组合词，现值 0 命中。
    若日后真做逐级展示，本条先红，逼改动回来重过拍板判据。"""
    pat = re.compile(r"(hint|提示).{0,24}(level|stage|step|index|逐级|分档|递进)")
    hits = []
    for path in sorted((REPO_ROOT / "ui").rglob("*.py")):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pat.search(line):
                hits.append(f"{path.name}:{i}:{line.strip()}")
    assert hits == [], hits


def test_hints条数契约_全量无越界且装载层夹钳在位():
    """l1004-15 机器判据：全量 content hints 条数 ≤3（夹钳＋源头双保险）；装载层 hints[:3] 在位。"""
    loader_src = (REPO_ROOT / "core" / "loader.py").read_text(encoding="utf-8")
    assert "hints[:3]" in loader_src, "装载层夹钳不在位 ⇒ 1-3 条契约退回口头约定"

    lengths: dict = {}
    over_cap: list = []
    for lang in ("python", "agent_dev", "cpp", "r", "sql"):
        for topic in load_language(lang):
            for p in topic.problems:
                assert isinstance(p.hints, list), (p.id, type(p.hints))
                assert len(p.hints) <= 3, (p.id, len(p.hints))
                lengths[len(p.hints)] = lengths.get(len(p.hints), 0) + 1
                if len(p.hints) > 3:
                    over_cap.append(p.id)
    assert sum(lengths.values()) > 0, "一道题都没读到 ⇒ 本用例空跑"
    assert over_cap == [], over_cap


def test_hints条数契约_源头分布_无四条题():
    """源头面（yaml 原文）分布复扫：4 条＝0（夹钳只护装载层，源头也要干净——
    截断会丢第 4 条内容，源头合并才是语义零丢失的正道）。"""
    lengths: dict = {}
    for f in REPO_ROOT.glob("content/**/*.y*ml"):
        try:
            d = yaml.safe_load(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(d, dict) or "hints" not in d:
            continue
        h = d.get("hints") or []
        lengths[len(h)] = lengths.get(len(h), 0) + 1
    assert sum(lengths.values()) > 0
    assert lengths.get(4, 0) == 0, f"仍有 4 条题：{lengths}"
