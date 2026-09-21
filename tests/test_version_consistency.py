# -*- coding: utf-8 -*-
"""版本号与对外文案的一致性钉桩（l922-122）。

对外版本号 **0.6.5** 目前写在四处，其中三处是人肉副本：
- `core/version.py:1` VERSION —— 唯一的真单源（:2 RELEASE_DATE 也只此一处）
- `README.md:3`「当前版本 v0.6.5」、`README.md:59`「## 当前能力亮点（v0.6.5）」—— 双写
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


def _readme_version_lines():
    """README 里含**当前**版本串的行号（1 起）。"""
    needle = f"v{VERSION}"
    return [i + 1 for i, line in enumerate(README.splitlines()) if needle in line]


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


def test_README版本串两处且逐处等于单源推导值(monkeypatch):
    """完成标准 ②的可执行等价形：含 `v{VERSION}` 的行数 == 2（实测锚定 README:3/:59）。

    写成「等于当前单源」而不是等于字面量 0.6.5 —— 升版本时两处一起改仍为 2，
    只改一处则变 1 立刻红；把字面量钉死反而会在正确升级后误红。
    """
    lines = _readme_version_lines()
    assert len(lines) == 2, f"README 含当前版本串的行数应为 2，实测 {lines}"
    assert lines == [3, 59], f"版本串位置漂了（现值 {lines}）：README 结构变了，请复核本桩前提"
    # 陈旧副本探测：README 里任何 v 语义版本都必须等于单源
    stale = {m for m in SEMVER_IN_MD.findall(README) if m != f"v{VERSION}"}
    assert not stale, f"README 残留其它版本号写法（升级漏改）：{sorted(stale)}"


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
