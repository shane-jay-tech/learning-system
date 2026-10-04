"""README 首屏语言名列表单源生成器（l1002-14，l922-122 遗留落地）。

LANG_META 是语言显示名的唯一事实源；README 首屏简介行的 `**Python · SQL · …**`
段由本脚本按 LANG_META 重写（幂等：已对齐时零 diff）。与
tests/test_version_consistency.py::test_README语言名列表与LANG_META逐项一致 共存——
测试抓漂移（红），本脚本提供修复命令（绿）。

用法：python scripts/sync_readme_langs.py    # rc 0=已对齐或已重写；rc 3=形态漂移需人工
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ui.components import LANG_META  # noqa: E402


def main() -> int:
    readme = ROOT / "README.md"
    raw = readme.read_text(encoding="utf-8")
    langs = " · ".join(m["name"] for m in LANG_META.values())
    new_raw, n = re.subn(
        r"\*\*[^*\n]+\*\* 交互式学习系统",
        f"**{langs}** 交互式学习系统",
        raw,
        count=1,
    )
    if n != 1:
        print("未找到「**…** 交互式学习系统」段（README 形态漂移，请人工复核）")
        return 3
    if new_raw == raw:
        print(f"README 语言名行已与 LANG_META 对齐（幂等，零 diff）：{langs}")
        return 0
    readme.write_text(new_raw, encoding="utf-8", newline="")
    print(f"README 语言名行已按 LANG_META 重写：{langs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
