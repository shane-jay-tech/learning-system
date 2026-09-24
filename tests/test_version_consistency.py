# -*- coding: utf-8 -*-
"""版本号与对外文案的一致性钉桩（l922-122）。

对外版本号 **0.6.5** 目前写在四处，其中三处是人肉副本：
- `core/version.py:1` VERSION —— 唯一的真单源（:2 RELEASE_DATE 也只此一处）
- `README.md` 首屏简介行 与 「当前能力亮点」标题行 —— 双写（两处副本）
- `app.py:28` 侧栏 `v{APP_VERSION}` —— **这一处是推导的，不算副本**；
  但同一行里的「5 门课程」是硬编码，`LANG_META` 现值也是 5 —— 第四处副本

门数副本最阴：新增第 6 门语言时 README:3 的语言名列表、app.py:28 的「5 门课程」
都不会自动跟着变，且 `LANG_META` 与 README 语言名是**两条独立的人肉清单**。

本桩把「副本数 == 实测值」与「推导处不含裸字面量」钉成机械断言：
升版本或加语言时只要漏改任意一处即红，**而不是**把 0.6.5 这个字符串本身钉死
（钉死字面量会在正确升级后误红）。只加测试，不改任何生产码。
"""
import re
from pathlib import Path

import pytest

import app
import ui.components as components
from core.version import RELEASE_DATE, VERSION
from tests.test_ui_behavior import FakeStreamlit

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")

# 只认带 v 前缀的语义版本，避免把 README:31 的 127.0.0.1 当版本号
SEMVER_IN_MD = re.compile(r"v\d+\.\d+\.\d+")
SEMVER_LITERAL_IN_PY = re.compile(r"""["'][0-9]+\.[0-9]+\.[0-9]+["']""")

LANG_META_KEYS = tuple(components.LANG_META.keys())


def _readme_version_lines(text=None):
    """提取器 A：README 里含**当前**版本串的行号（1 起）。

    `text=None` 时取 import 期的模块常量；传入文本时可对任意副本实取（l924-11 变异自检用）。
    """
    text = README if text is None else text
    needle = f"v{VERSION}"
    return [i + 1 for i, line in enumerate(text.splitlines()) if needle in line]


def _readme_semver_lines(text=None):
    """提取器 B（二次实取的第二路）：README 里**任意** v 语义版本的行号（1 起）。

    刻意与 A 不同源：不预设 VERSION（否则两路必然同错、判等恒真）、按匹配偏移量数换行
    推行号而不是按行枚举。⇒ A==B 同时钉住「行号算法两实现相符」与「无单源之外的版本号」。
    """
    text = README if text is None else text
    return sorted({text.count("\n", 0, m.start()) + 1 for m in SEMVER_IN_MD.finditer(text)})


def _check_readme_version_shape(text):
    """本桩对 README 的全部判据，收敛成可按副本实取的纯函数（变异自检的靶子）。

    不再钉字面行号：`l923-22` 实测那种「在 :59 之前另起段落」的合法改写会把字面行号推红，
    代价是 README 被迫写成一行 460 字符的长句。判据改为「结构锚点 + 两路实取判等」：
    合法改结构两路一起移动 ⇒ 不红；漏改/多写版本号两路不等 ⇒ 必红。
    """
    lines = text.splitlines()
    hits = _readme_version_lines(text)
    semver = _readme_semver_lines(text)
    # ① 二次实取判等值（替代原先的字面行号快照）
    assert hits == semver, (
        f"两条独立提取路径读数不等：按单源取 {hits}、按任意版本取 {semver}"
        "——README 里有单源之外的版本号（升级漏改）或版本串被抹掉"
    )
    # ② 双写不变量：整篇恰好两处，且严格递增
    assert len(hits) == 2, f"README 含当前版本串的行数应为 2，实测 {hits}"
    assert hits[0] < hits[1], f"版本串行号未严格递增：{hits}"
    # ③ 结构锚点（内容式，不随插入行漂移）：第一处在首个 ## 标题之前，第二处就是亮点标题
    first_heading = next((i + 1 for i, l in enumerate(lines) if l.startswith("## ")), None)
    assert first_heading is not None, "README 没有任何 ## 标题，本桩前提不成立"
    assert hits[0] < first_heading, (
        f"首屏版本串（第 {hits[0]} 行）落到了首个标题（第 {first_heading} 行）之后：结构变了"
    )
    assert lines[hits[1] - 1].startswith("## ") and "当前能力亮点" in lines[hits[1] - 1], (
        f"第二处版本串应在「当前能力亮点」标题行，实为第 {hits[1]} 行：{lines[hits[1] - 1]!r}"
    )
    # ④ 陈旧副本探测（与 ① 同义但报因更直白，保留）
    stale = {m for m in SEMVER_IN_MD.findall(text) if m != f"v{VERSION}"}
    assert not stale, f"README 残留其它版本号写法（升级漏改）：{sorted(stale)}"
    return hits


def _stale_sentinel():
    """造一个必定不等于单源现值的语义版本串（不把当前版本号字面抄进断言）。"""
    for cand in ("v0.0.0", "v0.0.1", "v0.0.2"):
        if cand != f"v{VERSION}":
            return cand
    raise AssertionError("陈旧哨兵与单源撞车，换个候选")


def test_README版本串两处且逐处等于单源推导值(monkeypatch):
    """完成标准 ②的可执行等价形（l924-11 改「二次实取」案）：

    同一份 README 经两条**独立**提取路径实取，行号必须逐位相同，且满足
    「两处 / 递增 / 首屏在首个标题前 / 第二处是亮点标题」四个结构锚点。
    写成「等于二次实取」而不是等于字面行号 —— 在 :59 之前另起段落时两路一起移动仍为绿
    （l923-22 的 README 可读性债源此），只改一处版本号则两路立刻不等。
    """
    live = _readme_version_lines()
    assert _check_readme_version_shape(README) == live
    # 同一提取函数两次独立调用判等值（钉「读数与调用次数无关」＝没有隐藏游标/缓存态）
    assert _readme_version_lines(README) == _readme_version_lines(README) == live
    assert _readme_semver_lines(README) == _readme_semver_lines(README) == live


def test_有牙自检_副本第四十行前插一行时行号必显性位移(tmp_path):
    """完成标准 ②（l924-11）：结构漂移**可检**性仍在——对 tmp 副本在第 40 行前插一行，

    ① 桩取的行号必须整体位移（红＝位移敏感性丢了，例如有人把按行取号改成只判存在）；
    ② 判据本身对该合法改写**不脆断**（两路一起移动，仍绿）——这正是 l923-22 欠的可读性债。
    README 本体全程只读，副本落在 pytest `tmp_path`（仓外，不进工作树）。
    """
    raw = (ROOT / "README.md").read_text(encoding="utf-8")
    src = raw.splitlines(keepends=True)
    assert len(src) >= 60, f"README 只有 {len(src)} 行，:40 锚点已失效，本例前提不成立"
    mutated = "".join(src[:39] + ["\n"] + src[39:])
    copy = tmp_path / "README.mutated.md"
    copy.write_text(mutated, encoding="utf-8")
    back = copy.read_text(encoding="utf-8")
    assert back == mutated, "副本落盘后读回不一致"

    base = _readme_version_lines(raw)
    got = _readme_version_lines(back)
    assert got != base, f"插一行后行号纹丝不动（{got}）：本桩已失去位移敏感性，需复核提取器"
    assert got == [base[0], base[1] + 1], f"位移量不符（:40 前插一行只应推动 ≥40 的行）：{base} → {got}"
    assert _check_readme_version_shape(back) == got, "合法改结构被判据误红（脆断言复活）"
    assert (ROOT / "README.md").read_text(encoding="utf-8") == raw, "README 本体被污染"


def test_有牙自检_漏改一处版本号时桩必红():
    """反向自证（完成标准 ② 的「能红」）：把第二处改成陈旧版本号 ⇒ 两路实取不等，桩必炸。"""
    stale = _stale_sentinel()
    hits = _readme_version_lines()
    lines = README.splitlines()
    target = lines[hits[1] - 1]
    mutated = "\n".join(lines[: hits[1] - 1] + [target.replace(f"v{VERSION}", stale)] + lines[hits[1]:])
    assert mutated != README and stale in mutated, "夹具没把副本改成陈旧态，本例是恒真的假自证"
    with pytest.raises(AssertionError):
        _check_readme_version_shape(mutated)


def test_有牙自检_抹掉一处版本串时桩必红():
    """反向自证 ②：抹掉第二处的版本串 ⇒ 「双写」不变量被破坏，桩必炸。"""
    hits = _readme_version_lines()
    lines = README.splitlines()
    target = lines[hits[1] - 1]
    mutated = "\n".join(lines[: hits[1] - 1] + [target.replace(f"v{VERSION}", "")] + lines[hits[1]:])
    assert mutated != README, "夹具没改动到文本，本例是恒真的假自证"
    with pytest.raises(AssertionError):
        _check_readme_version_shape(mutated)


def test_有牙自检_另有一处提到非单源版本时桩必红():
    """判据 ①「二次实取判等」的独任面（防止它被写成恒真装饰）。

    在亮点标题行**之后**另起一行提到别的版本号：按单源取的行号两处原封不动（判据 ②③ 看不见），
    只有不预设版本号的第二路实取（或 ④ 的陈旧探测）会红。
    两条同族断言互为主从属：删掉任一条本例仍绿，两条都删即红（变异取证见 result）。
    """
    stale = _stale_sentinel()
    base = _readme_version_lines()
    lines = README.splitlines()
    injected = lines[: base[1]] + [f"- 历史变更：{stale} 起版本号收敛到单源。"] + lines[base[1]:]
    copy = "\n".join(injected)
    assert _readme_version_lines(copy) == base, "夹具让单源串的数量变了，本例退化成判据 ② 的重复"
    assert _readme_semver_lines(copy) != base, "第二路实取没看到新增版本串，夹具失效"
    with pytest.raises(AssertionError):
        _check_readme_version_shape(copy)



def _sidebar_brand_meta(monkeypatch):
    """真渲染 app._sidebar()，取 sidebar-brand-meta 那一帧的完整 HTML。"""
    fake = FakeStreamlit()
    monkeypatch.setattr(app, "st", fake)
    monkeypatch.setattr(components, "st", fake)
    app._sidebar()
    hits = [str(a[0]) for name, a, _ in fake.calls
            if name == "markdown" and "sidebar-brand-meta" in str(a[0])]
    assert len(hits) == 1, f"侧栏品牌行应恰好渲染一次，实为 {len(hits)}"
    return hits[0]


def test_侧栏版本串由单源推导且不含裸字面量(monkeypatch):
    """app.py:28 用 f"v{APP_VERSION}"：渲染结果必须含 v{VERSION}，且 app.py 源码内无裸版本字面量。"""
    html = _sidebar_brand_meta(monkeypatch)
    assert f"v{VERSION} ·" in html, html
    src = (ROOT / "app.py").read_text(encoding="utf-8")
    assert not SEMVER_LITERAL_IN_PY.search(src), "app.py 里出现了硬编码版本字面量，单源被绕过"


def test_侧栏课程门数与LANG_META一致(monkeypatch):
    """「5 门课程」是硬编码副本：必须等于 len(LANG_META) == len(ALL_LANGS) == 5。"""
    html = _sidebar_brand_meta(monkeypatch)
    m = re.search(r"(\d+) 门课程", html)
    assert m, f"侧栏未渲染出「N 门课程」文案：{html}"
    n = int(m.group(1))
    assert n == len(LANG_META_KEYS) == len(components.ALL_LANGS) == 5, \
        f"侧栏门数 {n} 与 LANG_META {len(LANG_META_KEYS)} 脱节，加语言时漏改文案"


def test_README语言名列表与LANG_META逐项一致():
    """README:3 的人肉语言清单是**第四处副本**：五个显示名必须逐个出现且顺序与 LANG_META 相同。

    加第 6 门语言时本例与上一例同时红，两处文案一起改。
    """
    head = README.splitlines()[2]  # :3
    names = [components.LANG_META[k]["name"] for k in LANG_META_KEYS]
    assert names == ["Python", "SQL", "C++", "R", "Agent 开发"], names
    pos = [head.find(n) for n in names]
    assert all(p >= 0 for p in pos), f"README:3 缺语言名 {names} → {head}"
    assert pos == sorted(pos), f"README:3 语言顺序与 LANG_META 不一致：{list(zip(names, pos))}"


def test_全仓生产码版本字面量只有单源一处():
    """单源守卫：core/version.py 之外，ui/ core/ scripts/ app.py 不得出现裸版本字符串字面量。

    测试与 docs 不在范围内（历史报告 docs/system-report-v0.6.5.md 是**按版本归档的产物**，
    版本号进文件名属设计而非漂移；docs/insights/* 是巡检留痕，同样不钉）。
    """
    offenders = []
    for sub in ("core", "ui", "scripts"):
        for p in sorted((ROOT / sub).rglob("*.py")):
            if p.name == "version.py" and sub == "core":
                continue
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if SEMVER_LITERAL_IN_PY.search(line):
                    offenders.append(f"{p.relative_to(ROOT).as_posix()}:{i}")
    assert not offenders, f"发现单源之外的版本字面量：{offenders}"


def test_发布单源含VERSION与RELEASE_DATE两键():
    """core/version.py 现值快照：VERSION 形如 x.y.z、RELEASE_DATE 形如 YYYY-MM-DD。

    钉形状不钉值 —— 升级不改口径；generate_system_report.py:120 靠这两个键取数。
    """
    assert re.fullmatch(r"\d+\.\d+\.\d+", VERSION), VERSION
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", RELEASE_DATE), RELEASE_DATE
    vsrc = (ROOT / "core" / "version.py").read_text(encoding="utf-8")
    assert vsrc.splitlines()[0] == f'VERSION = "{VERSION}"', "VERSION 不再是 core/version.py:1，引用面需复核"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
