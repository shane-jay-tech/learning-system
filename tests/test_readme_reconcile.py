# -*- coding: utf-8 -*-
"""README 对外数字 ⇄ 磁盘/代码实取对账桩（l923-12，2026-09-23）。

起因：docs/insights/learn-readme-numbers-20260922.md 第四节 —— README:52 写「3 条学习路径」
而磁盘实为 6 条，失真存活 68 天无人拦。该档给了两个出口（把 tests/test_paths.py:29 的
`>= 3` 收紧为等值 / 加一条「读 README 抽数 vs 磁盘计数」对账测试），本单一起落地：
等值收口在 tests/test_paths.py::test_all_paths_load，README 侧对账在本文件。

接档前先复核，两处锚点说法已被现状否证（按磁盘实况修正，读数见 result 的「证据」节）：
  - 「路径数没有等价的精确守卫」→ 现役已有 tests/test_paths_order_consistency.py
    `test_覆盖全部path` 钉 `len(paths) == 6`（09-22 补）。
  - 「徽章 22 同样无钉」→ 现役已有 tests/test_achievements.py::test_count_is_22
    钉 `len(ACHIEVEMENTS) == 22`。
  两条都是**代码侧**等值（实取变了它红），**README 侧**「抽数 vs 实取」此前仍零测试，
  所以本文件补的是另外两个方向：改了实取忘改 README、以及把 README 那句话改写/删掉
  从而让门禁空转。

钉五件事：
  ① README「N 条学习路径」== load_all_paths() 运行时条数。
  ② README「N 枚徽章」== len(core.achievements.ACHIEVEMENTS)。
  ③ 三方一致：content/paths/*.yaml 磁盘数 == 运行时数（core/paths.py:76 现在无过滤
     开关，一旦有人加白名单/enabled 字段，磁盘与实取会先分手，本例即红）。
  ④ 变异自证（内存串，零写盘）：①/② 的 README 数字各 +1，对账必须红，且只点名被改那条。
  ⑤ 把承载数字的行整行删掉，对账同样必须红（防「删句＝静默关门禁」）。
"""
import re
from pathlib import Path

import pytest

from core.achievements import ACHIEVEMENTS
from core.paths import load_all_paths

README_PATH = Path(__file__).resolve().parent.parent / "README.md"
PATHS_DIR = README_PATH.parent / "content" / "paths"

_PATHS_PAT = re.compile(r"(\d+)\s*条学习路径")
_BADGE_PAT = re.compile(r"(\d+)\s*枚徽章")

# (展示名, README 抽取正则, 实取值函数)
_SPECS = (
    ("学习路径数", _PATHS_PAT, lambda: len(load_all_paths())),
    ("徽章数", _BADGE_PAT, lambda: len(ACHIEVEMENTS)),
)


def _readme_text() -> str:
    text = README_PATH.read_text(encoding="utf-8")
    assert text.strip(), f"README 读不到内容：{README_PATH}"
    return text


def _claimed(text: str, name: str, pat: re.Pattern) -> int:
    hits = [int(g) for g in pat.findall(text)]
    assert len(hits) == 1, (
        f"README 抽数失败（{name}）：正则 {pat.pattern!r} 命中 {len(hits)} 次 {hits}，须恰好 1 次。"
        "命中 0 次＝承载这句话的 README 文本被改写或删除（等于悄悄关掉本门禁），"
        "命中多次＝同一数字有了多份副本，请先合流再改本桩。")
    return hits[0]


def _reconcile(text: str):
    """逐条比对 README 宣称值与实取值；相符返回读数表，任一不符即 AssertionError。"""
    rows, bad = [], []
    for name, pat, truth in _SPECS:
        claimed = _claimed(text, name, pat)
        actual = truth()
        rows.append((name, claimed, actual))
        if claimed != actual:
            bad.append(f"{name}：README 宣称 {claimed} != 实取 {actual}")
    if bad:
        raise AssertionError(
            "README 对外数字静默失真（同步 README 或回退实取侧改动）：" + "；".join(bad)
            + f"；全部读数（名称, README, 实取）={rows}")
    return rows


def test_README对外数字与实取逐项对账():
    rows = _reconcile(_readme_text())
    # 覆盖性自检：两条都得真的比过（防空循环/漏项假绿）
    assert [r[0] for r in rows] == [s[0] for s in _SPECS], f"对账项缺失：{rows}"
    assert all(c == a for _, c, a in rows), f"走到这里不该有失配：{rows}"


def test_路径yaml磁盘数与运行时加载数三方一致():
    """README ⇄ 磁盘 ⇄ load_all_paths() 三方同值（③）。"""
    disk = sorted(p.stem for p in PATHS_DIR.glob("*.yaml"))
    runtime = sorted(p.id for p in load_all_paths())
    assert disk, f"content/paths/ 下一个 yaml 都没有：{PATHS_DIR}"
    assert disk == runtime, (
        f"磁盘 path 与运行时加载不符集（core/paths.py 是否新增了过滤/enabled 开关？）：\n"
        f"  磁盘 {len(disk)} = {disk}\n  实取 {len(runtime)} = {runtime}")


@pytest.mark.parametrize("idx", range(len(_SPECS)))
def test_变异自证改一位README数字对账必转红(idx):
    """④：README 数字 +1 必须让对账红，且失败消息只点名被改那一条。"""
    assert len(_SPECS) == 2, f"本夹具按两条对账项写死，现 {len(_SPECS)} 条"
    name, pat, _ = _SPECS[idx]
    other = _SPECS[1 - idx][0]
    text = _readme_text()
    _reconcile(text)  # 前置：README 现值须与实取相符，否则「只点名一条」的判据不成立（先修主对账用例）

    def _bump(m: re.Match) -> str:
        digits = m.group(1)
        # sub 换的是整个命中段，只回填数字会把「枚徽章」尾巴吃掉 ⇒ 抽数命中 0 次，
        # 变异夹具就退化成「删句自证」那一条（l923-12 首跑实测踩过）。保留原文只动数字。
        return m.group(0).replace(digits, str(int(digits) + 1), 1)

    mutated = pat.sub(_bump, text, count=1)
    assert mutated != text, f"变异失效：README 里 {pat.pattern!r} 没匹配到可改的数字"
    assert _claimed(mutated, name, pat) == _claimed(text, name, pat) + 1, "变异没落到数字上"
    with pytest.raises(AssertionError) as ei:
        _reconcile(mutated)
    msg = str(ei.value)
    assert f"{name}：README 宣称" in msg, f"被改的 {name} 未出现在失败消息里：{msg}"
    assert f"{other}：README 宣称" not in msg, f"未被改动的 {other} 被判成失配（对账项互相污染）：{msg}"


def test_变异自证删掉承载数字的行同样转红():
    """⑤：删句不得退化成「无数字可比所以绿灯」。"""
    text = _readme_text()
    lines = text.splitlines()
    kept = [ln for ln in lines if not any(p.search(ln) for _, p, _ in _SPECS)]
    assert len(kept) < len(lines), "夹具失效：README 里找不到承载对账数字的行"
    with pytest.raises(AssertionError) as ei:
        _reconcile("\n".join(kept))
    assert "抽数失败" in str(ei.value), f"删句后应是抽数失败而非静默放行：{ei.value}"
