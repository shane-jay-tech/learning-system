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


@pytest.mark.xfail(strict=True, reason=f"{_TITLE_ERROR}……（HEAD 长期红，l923-25 遗留；修复出口见模块 docstring）")
def test_真README必须过check_readme(capsys, metrics):
    """显性化的就是这条红：`check_readme` 判真 README 不过。"""
    ok = generate_system_report.check_readme(README, metrics)
    capsys.readouterr()
    assert ok is True, "README 首行仍缺版本串，门禁判红——本例应维持 XFAIL"


def test_现状红的成因恰为标题版本一条(capsys, metrics):
    """把 XFAIL 的成因钉死：有且只有"首行无版本串"这一条，别的一律不许藏进 XFAIL。

    本例转红只有两种可能，都该有人来看：
    ① README 首行已补版本串 ⇒ 上一条 xfail 桩该删（见 docstring 修复出口）；
    ② 又长出一条新的失败原因（如题量/知识点数与 README 脱钩）⇒ 那是真缺陷，不是本档的债。
    """
    ok = generate_system_report.check_readme(README, metrics)
    out = capsys.readouterr().out
    first_line = README.read_text(encoding='utf-8').split(chr(10), 1)[0].strip()
    assert ok is False, (
        'check_readme 已判真 README 通过，但本例还钉着「现状红」——README 首行补过版本串了，'
        '请删掉 test_真README必须过check_readme 的 xfail 桩并把本例翻正'
    )
    causes = [ln.strip()[2:] for ln in out.splitlines() if ln.strip().startswith('- ')]
    assert len(causes) == 1, f'长期红的成因应当只有一条，实测 {len(causes)} 条：{causes}'
    assert causes[0].startswith(_TITLE_ERROR), f'成因换人了（不是标题版本）：{causes}'
    assert first_line and first_line in causes[0], (
        f'成因文案里没引用到 README 首行（{first_line!r}）：{causes}'
    )


def test_修好后门禁真的会绿(tmp_path, capsys, metrics):
    """反向自证：这条 xfail 不是恒假门——首行补上版本串做成副本后 `check_readme` 必须判 True。

    副本只写在 `tmp_path`，README 本体零改动。
    """
    text = README.read_text(encoding="utf-8")
    head, _, rest = text.partition("\n")
    assert VERSION not in head, "README 首行已含版本串，本例的夹具前提失效，请连同 xfail 桩一起收口"
    patched = f"{head} v{VERSION}\n{rest}"
    copy = tmp_path / "README.patched.md"
    copy.write_text(patched, encoding="utf-8")
    assert copy.read_text(encoding="utf-8") == patched, "副本落盘后读回不一致"
    ok = generate_system_report.check_readme(copy, metrics)
    out = capsys.readouterr().out
    assert ok is True, f"补了版本串仍判不过 ⇒ 门禁还有别的红没被成因桩显性化：{out}"
    assert "PASS" in out, out
    assert README.read_text(encoding="utf-8") == text, "README 本体被污染"
