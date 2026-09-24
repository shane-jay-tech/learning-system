# -*- coding: utf-8 -*-
"""docs/insights 索引闭合哨兵（l923-01，2026-09-23）。

补的缺口（上游原话见 `zcode-bridge/done/l922-127-insights-index-rebuild.result.md`）：
「本索引是『手工维护型』资产，无自动哨兵：本次靠脚本重算闭合，但没有任何测试钉
『条目数 == 磁盘数』，下一浪新增档会再次无声漂移」。9/22 那轮重建前 A=59/B=37/C=22 行
就是这种漂移的实际代价——本桩让同样的事当场变红。

口径 = 权威索引档头的对账三条（现值落在
`docs/insights/learn-insights-index-20260918.md` 第 3-12 行的 bash 块）：
    A = 磁盘 docs/insights/*.md 数
    B = 索引表 `^| docs/insights/` 条目数（**含索引自身 1 份**）
    C = 「磁盘有、表里没」的差集（应为空）
    闭合等式：**A == B 且 C 为空 且 B 去重后条数 == B（无重复）**

绑磁盘实取、**断言里零条目数字面量**（照 `tests/test_paths_reconcile.py` l922-125
的比例式风格）：增删 insights 档只要在索引表同步登记即绿，漏登记当场红。
本桩不锁任何绝对值。同族 `tests/test_paths.py` 的条数下界是另一条线，且已于 l923-12（2026-09-23）钉成 `== 6`
（断言现落该文件 :35，:29 现为收口注记），代码侧 `metrics["paths"]` 副本另由 l924-14（2026-09-24）同步钉 6；两条都跟本桩无关——本桩仍零条目数字面量。

权威索引的取法（磁盘实取、不写死文件名）：`docs/insights/*insights-index*.md` 里文件名
8 位日期最新的一份。盘上天然有 2 份候选——l922-127 把 09-17 旧索引按「历史快照原样保留」
原则留着并已列入表；下一浪若另建新索引文件，本哨兵自动跟着最新那份走，不必改用例。
落笔时读数（**非断言对象**，会随 insights 增长过期，别当基线引用）：2026-09-23 @ HEAD
1eebffb 复算 A=B=62、C 空、重复 0 ⇒ 现值闭合。

复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_insights_index_closure.py -q
只读 docs/insights/，零写盘、零网络、零他仓依赖。
"""
import re

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INSIGHTS_DIR = REPO_ROOT / "docs" / "insights"

# 索引表条目行的形状：`| docs/insights/<file>.md | 日期 | 主题 | git 入库 | 引用数 |`
_ENTRY_ROW = re.compile(r"^\|\s*(docs/insights/[^\s|]+)")
# 文件名里的 8 位日期（用于挑权威索引，不做数值比较）
_DATE_TOKEN = re.compile(r"(\d{8})")


def _rel(p: Path) -> str:
    """仓库根相对路径 + 正斜杠，与索引表第一列的写法同型（Windows 盘上 "\\" 需归一）。"""
    return p.relative_to(REPO_ROOT).as_posix()


def _disk_md_paths() -> list:
    """A 的取数（口径 == `ls docs/insights/*.md`，只算一层、不含子目录）。"""
    return sorted(_rel(p) for p in INSIGHTS_DIR.glob("*.md"))


def _index_candidates() -> list:
    return sorted(_rel(p) for p in INSIGHTS_DIR.glob("*insights-index*.md"))


def _date_key(rel_path: str) -> str:
    m = _DATE_TOKEN.search(Path(rel_path).name)
    return m.group(1) if m else ""


def _authoritative_index() -> str:
    """文件名 8 位日期最新的索引档；同日期时按文件名兜底（保证可复算、无并列歧义）。"""
    candidates = _index_candidates()
    assert candidates, "docs/insights 下没有任何 *insights-index*.md，闭合等式无从算起"
    return max(candidates, key=lambda rel: (_date_key(rel), rel))


def _table_entries(index_rel: str) -> list:
    """B 的取数（口径 == `grep -c '^| docs/insights/'`，顺序保留以便报出重复项）。"""
    text = (REPO_ROOT / index_rel).read_text(encoding="utf-8")
    return [m.group(1) for line in text.splitlines() for m in [_ENTRY_ROW.match(line)] if m]


def _closure_diff(disk: list, entries: list) -> tuple:
    """纯函数：返回 (未登记项 C, 表内多余项, 重复条目)。

    抽出来是给 `test_哨兵有牙_*` 喂合成盘态用的——不这样写就只能靠真往 docs/insights
    扔文件来验哨兵有没有牙，那属于写盘（本仓库口径：测试零写盘）。
    """
    missing = sorted(set(disk) - set(entries))
    extra = sorted(set(entries) - set(disk))
    dupes = sorted({e for e in entries if entries.count(e) > 1})
    return missing, extra, dupes


def test_权威索引在盘且自登记():
    """档头声明「B 已含索引自身 1 份」——本例把这句话钉成断言，防自登记行被删。"""
    index = _authoritative_index()
    assert Path(REPO_ROOT / index).is_file(), f"权威索引 {index} 不在盘上"
    entries = _table_entries(index)
    assert index in entries, f"权威索引未自登记于自己的表内（档头口径要求 B 含自身 1 份）：{index}"


def test_闭合等式_A等于B_且C为空_且无重复():
    """任务书的主判据：A == B、C 为空、B 去重后条数 == B，三个数全部绑磁盘实取。"""
    disk = _disk_md_paths()
    entries = _table_entries(_authoritative_index())
    missing, extra, dupes = _closure_diff(disk, entries)

    assert disk and entries, "磁盘或索引表取到空集——空循环会让本例假绿，判口径失效"
    assert len(disk) == len(entries), (
        f"A != B：磁盘 {len(disk)} 份 .md，索引表 {len(entries)} 条。"
        f"未登记 {missing}／表内多余 {extra}"
    )
    assert missing == [], f"C 非空：以下 insights 档未登记进索引 {missing}"
    assert dupes == [], f"索引表有重复条目（B 去重后 != B）：{dupes}"
    assert extra == [], f"索引表列了盘上不存在的档（改名或误删所致）：{extra}"


def test_新档漏登记必红_改名必红_有牙自检():
    """合成盘态自证三条判据不是永绿（零写盘，照 test_paths_reconcile 的缩半自检同型）。

    只做「关系」判定，不引入条目数字面量——现值涨到多少都不影响本例。
    """
    disk = _disk_md_paths()
    entries = _table_entries(_authoritative_index())
    base_missing, base_extra, base_dupes = _closure_diff(disk, entries)
    assert (base_missing, base_extra, base_dupes) == ([], [], []), "现值本身不闭合，先修盘子再谈自检"

    # ① 磁盘多 1 份未登记档（真实场景：同班只写档不改索引）→ C 必须抓到它
    ghost = "docs/insights/zz-synthetic-unregistered-probe.md"
    missing, extra, dupes = _closure_diff(disk + [ghost], entries)
    assert missing == [ghost], f"漏登记自检失败：新增未登记档被判 {missing}（应恰为该档本身）"
    assert len(set(disk + [ghost])) != len(entries), "A==B 自检失败：多 1 份未登记档后仍判等"

    # ② 把某条登记项改名（表里写的与盘上不一致）→ 必须同时报出「未登记」和「多余」
    renamed = "docs/insights/zz-synthetic-renamed-entry.md"
    shifted = [renamed if e == entries[0] else e for e in entries]
    missing, extra, dupes = _closure_diff(disk, shifted)
    assert extra == [renamed] and missing == [entries[0]], (
        f"改名自检失败：应报 未登记={entries[0]!r} 多余={renamed!r}，实报 {missing}/{extra}"
    )

    # ③ 重复登记同一档（去重后条数 != 条数，但 A 可能仍 == B）→ 重复项必须现形
    duped = entries + [entries[0]]
    missing, extra, dupes = _closure_diff(disk, duped)
    assert dupes == [entries[0]], f"重复自检失败：{dupes}"
    assert len(disk) != len(duped), "A==B 自检失败：重复登记后仍判等（说明只算了去重数）"
