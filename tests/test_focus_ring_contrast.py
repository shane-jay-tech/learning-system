# -*- coding: utf-8 -*-
"""l930-08：焦点环对比度静态哨兵（l927-43 遗留 2 的 tests/ 实装，零生产码改动）。

三条口径（承 l927-43-recolor.md 第四节，复算器形状照搬、从磁盘声明取值而非抄表）：
  ① 按 CSS 规则块取值：ui/styles.py 里 `outline: 3px solid #4547B9 !important; outline-offset: 2px;`
     恰好 3 处（分组选择器跨行 ⇒ 按规则块切、不按行锚——前置档第七节①的坑）；
  ② 浅色面全集断言对比度 min ≥ 3.0（sRGB 编码域 source-over 合成＋WCAG 相对亮度，
     offset 2px ⇒ 比较对象＝父面；假想深底 #172033 本仓无载体，不计入达标判据）；
  ③ 反向自证：同一函数喂旧值 rgba(91,91,214,.28) 合成 ⇒ 全集 < 3（证明判据真能判红，
     防恒真空壳——l927-43 改前 rc=1/改后 rc=0 的两次 rc 差即此判据的正面闭合）。

复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_focus_ring_contrast.py -q
"""
import re
from pathlib import Path

STYLES = Path(__file__).resolve().parent.parent / "ui" / "styles.py"

# 在册浅色 token（styles.py :15-21 一带的声明，测试从磁盘现取）
TOKEN_SURFACES = ["--bg", "--surface", "--surface-muted", "--primary-soft"]
# 两处硬编码浅色面（侧栏 :77／hover :197——前置档遗留 3 登记的"不在 token 里"小债，值静态）
HARDCODED_SURFACES = ["#F8F8FC", "#F8F8FF"]
# 假想深底（无载体，只进反向自证与备注，不进达标判据）
HYPOTHETICAL_DARK = (0x17, 0x20, 0x33)

RING_NEW = (0x45, 0x47, 0xB9)          # #4547B9（档 A 实色）
RING_OLD_BASE = (91, 91, 214)          # 旧 rgba(91, 91, 214, .28) 的基色
OLD_ALPHA = 0.28


def _hex_to_rgb(value: str):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def _composite(fg, alpha, bg):
    """sRGB 编码域 source-over 合成（前置档第二节口径）。"""
    return tuple(round(alpha * f + (1 - alpha) * b) for f, b in zip(fg, bg))


def _rel_luminance(rgb):
    def channel(v):
        v = v / 255
        return ((v + 0.055) / 1.055) ** 2.4 if v > 0.03928 else v / 12.92
    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(fg, bg):
    lo, hi = sorted((_rel_luminance(fg), _rel_luminance(bg)))
    return (hi + 0.05) / (lo + 0.05)


def _styles_text() -> str:
    return STYLES.read_text(encoding="utf-8")


def _ring_blocks(text: str):
    """按规则块切（不按行锚）：返回含焦点环 outline 声明的块列表。"""
    return [block for block in text.split("}")
            if "outline:" in block and "outline-offset: 2px" in block]


def _primary_dark_from_disk():
    """环色单源现取：--primary-dark token（l930-21 班已把字面 #4547B9 等价替换为 var 引用，
    计算值同值；哨兵从 token 声明解析，改 token 即改判据对象）。"""
    m = re.search(r"--primary-dark\s*:\s*(#[0-9A-Fa-f]{6})", _styles_text())
    assert m, "--primary-dark token 声明缺失"
    return _hex_to_rgb(m.group(1))


def test_rule_blocks_three_occurrences_with_new_ring():
    """口径①：焦点环声明按规则块计恰好 3 处，环色全部走 --primary-dark（解析值=#4547B9）。"""
    text = _styles_text()
    blocks = _ring_blocks(text)
    assert len(blocks) == 3, f"焦点环规则块应恰 3 处，实得 {len(blocks)}"
    dark = _primary_dark_from_disk()
    assert dark == RING_NEW, f"--primary-dark 应为 #4547B9（档 A 实色），现值 {dark}"
    for block in blocks:
        assert "var(--primary-dark)" in block or "#4547B9" in block,             f"规则块环色应引用 --primary-dark（或字面 #4547B9）：{block.strip()[:120]}"
    # 旧串归零（l927-43 的声明计数自证口径）
    assert text.count("rgba(91, 91, 214, .28)") == 0, "旧 rgba 环色应已归零"


def _light_surfaces():
    """浅色面全集：token 四面从磁盘现取（改 token 即改判据对象）＋两处硬编码静态值。"""
    text = _styles_text()
    surfaces = []
    for token in TOKEN_SURFACES:
        m = re.search(rf"{token}\s*:\s*(#[0-9A-Fa-f]{{6}})", text)
        assert m, f"token {token} 在 styles.py 声明缺失"
        surfaces.append((token, _hex_to_rgb(m.group(1))))
    for value in HARDCODED_SURFACES:
        surfaces.append((value, _hex_to_rgb(value)))
    return surfaces


def test_light_surfaces_min_contrast_at_least_3():
    """口径②：焦点环新色对全部浅色面的对比度 min ≥ 3.0（在册读数 min=6.41@primary-soft）。"""
    ring = _primary_dark_from_disk()
    for name, bg in _light_surfaces():
        ratio = _contrast(ring, bg)
        assert ratio >= 3.0, f"焦点环对 {name} 对比度 {ratio:.2f} < 3.0（焦点环不可辨）"


def test_reverse_old_value_would_fail():
    """口径③反向自证：旧 rgba(91,91,214,.28) 合成后全集 < 3 ⇒ 判据真能判红（防恒真空壳）。"""
    ratios = [_contrast(_composite(RING_OLD_BASE, OLD_ALPHA, bg), bg)
              for _name, bg in _light_surfaces()]
    assert max(ratios) < 3.0, f"旧值合成后仍有面 ≥3 ⇒ 反向自证失真：{ratios}"
    # 假想深底同喂（在册读数 1.33/2.21，均不可辨——登记形态，不断言达标）
    old_dark = _contrast(_composite(RING_OLD_BASE, OLD_ALPHA, HYPOTHETICAL_DARK), HYPOTHETICAL_DARK)
    new_dark = _contrast(RING_NEW, HYPOTHETICAL_DARK)
    assert old_dark < 3.0 and new_dark < 3.0, "深底两面均不可辨是已知形态（档四表格末行），若翻转须复查口径"
