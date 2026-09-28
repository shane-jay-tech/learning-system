# -*- coding: utf-8 -*-
"""真 README 的版本串门禁进 pytest：把 `--check-readme` 的长期红显性化（l924-12）。

补的缺口（原话见 `zcode-bridge/done/l923-25.result.md`）：
`python scripts/generate_system_report.py --check-readme README.md` 在 HEAD 上**长期红**
（README 首行没有版本串），而这条红**不在 pytest 覆盖内**——`tests/test_scripts.py:338`
只拿 tmp 里的微型 README 打桩，真档从没被 `check_readme` 扫过 ⇒ 一个"谁都看得见、
门看不见"的长期红。本档把它显性化。

钉法（为什么是 xfail 而不是直接 assert False）：
- `test_真README必须过check_readme` 以 `xfail(strict=True)` 钉**现状红**。
  补好 README 首行后它会 XPASS ⇒ strict 当场转红 ⇒ 逼着来删这条桩，不会留下无声失效的门。
- 光有 xfail 会把「新长出来的别的失败原因」也一并吞进 XFAIL，所以再配两条**绿桩**：
  ① `test_现状红的成因恰为标题版本一条`（成因清单逐条钉，多一条少一条都红）；
  ② `test_修好后门禁真的会绿`（把首行补上版本串做成副本，`check_readme` 必须判 True
     ⇒ 钉"这条红是可修的、不是恒假门"，同时也钉住另三条子判据在真 README 上本来就过）。
- 版本号一律从单源 `core.version.VERSION` 推导，**不把当前版本字面抄进断言**。

本档零改动 `README.md`（完成标准 ④）与 `scripts/generate_system_report.py`（那是 l924-13 的被试件）。
修复出口：给 README 首行补版本串后，本档第 1 例会 XPASS 转红 ⇒ 删该 xfail 桩、
把成因桩改成"过"，并同步复核 `tests/test_version_consistency.py`（它钉 README 的两处版本串
与单源一致；l924-11 已把该桩从"字面行号快照"改成"二次实取判等"，故首行补串不会误红它）。

复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_readme_version_gate.py -q

l927-46 收口（2026-09-28，README 首行已补裸版本串，上述修复出口按预述兑现）：
第 1 例的 xfail 桩已删 ⇒ 本档转为常驻绿门禁；第 2 例翻正并更名
`test_现状红的成因恰为标题版本一条` → `test_真README过门且FAIL清单为空`；第 3 例反向自证翻正并更名
`test_修好后门禁真的会绿` → `test_抹掉首行版本串门禁必判红`。旧名在册档（l924-12／l927-46 note）
按其当时盘态留痕，不回改。
"""
from pathlib import Path

import pytest

from core.version import VERSION
from scripts import generate_system_report

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

# check_readme 的第 1 条子判据在真 README 上的失败文案（版本由单源推导）
_TITLE_ERROR = f"README 标题版本不含 {VERSION}"


@pytest.fixture(scope="module")
def metrics():
    """真取一次指标（约 0.5s，本模块三条用例共用；不打桩任何计数函数）。"""
    return generate_system_report.generate_metrics()


def test_真README必须过check_readme(capsys, metrics):
    """l927-46 起常驻绿：README 首行含版本串 ⇒ `check_readme` 必须判真 README 通过。"""
    ok = generate_system_report.check_readme(README, metrics)
    capsys.readouterr()
    assert ok is True, "README 首行缺版本串（或被改写），门禁判红"


def test_真README过门且FAIL清单为空(capsys, metrics):
    """翻正版（原名 `test_现状红的成因恰为标题版本一条`）：钉"过门 ＋ FAIL 清单为空"。

    本例转红只有两种可能，都该有人来看：
    ① README 首行的版本串被抹掉或改写 ⇒ 与上一条同因，先看首行；
    ② 长出别的失败原因（如题量/知识点数与 README 脱钩）⇒ 那是真缺陷，不是本档的债，
       FAIL 清单会把它的条数与文案直接钉在这里。
    """
    ok = generate_system_report.check_readme(README, metrics)
    out = capsys.readouterr().out
    assert ok is True, f"门禁判红（README 首行或别的面）：{out}"
    causes = [ln.strip()[2:] for ln in out.splitlines() if ln.strip().startswith('- ')]
    assert len(causes) == 0, f"过门却仍有 FAIL 清单 {len(causes)} 条：{causes}"
    assert "PASS" in out, out
    head = README.read_text(encoding='utf-8').split(chr(10), 1)[0]
    assert VERSION in head, f"README 首行不含单源版本 {VERSION}：{head!r}"


def test_抹掉首行版本串门禁必判红(tmp_path, capsys, metrics):
    """反向自证（原名 `test_修好后门禁真的会绿`）：牙还在——把首行的版本串抹掉做成 tmp 副本，
    `check_readme` 必须判 False 且 FAIL 文案点名标题版本。副本只写在 `tmp_path`，README 本体零改动。
    """
    text = README.read_text(encoding="utf-8")
    head, _, rest = text.partition("\n")
    assert VERSION in head, "README 首行已不含版本串，本例的夹具前提失效，先看上一条"
    stripped = head.replace(VERSION, "").strip()
    copy = tmp_path / "README.stripped.md"
    copy.write_text(f"{stripped}\n{rest}", encoding="utf-8")
    assert copy.read_text(encoding="utf-8").split(chr(10), 1)[0] == stripped, "副本落盘后读回不一致"
    ok = generate_system_report.check_readme(copy, metrics)
    out = capsys.readouterr().out
    assert ok is False, f"抹掉版本串仍判通过 ⇒ 该子判据是恒真门：{out}"
    assert _TITLE_ERROR in out, f"FAIL 文案没点名标题版本：{out}"
    assert README.read_text(encoding="utf-8") == text, "README 本体被污染"
