# -*- coding: utf-8 -*-
"""achievements 定义面 ↔ 解锁面 ↔ 存量 earned 三向 id 对账钉桩（l923-26，2026-09-23）。

补的缺口
--------
成就有三份互不引用的 id 清单，任一侧改名都不会有任何测试变红：

1. **定义面** `core/achievements.py:21 ACHIEVEMENTS`（现值 22 条 `Achievement(...)`）——决定展示层列什么。
2. **解锁面** `core/achievements.py:58 check_achievements`——22 个 aid **全部以字面量硬编码在函数体内**
   （`streak_3..30` / `first_solve`,`solve_10..200` / `lang_map` 的 `*_first` / `half_map` 的 `*_half` /
   `multi_lang` / `no_mistakes` / `path_first_milestone`,`path_agent_done`,`path_pa_done`），
   没有一处 `for a in ACHIEVEMENTS` 的驱动。
3. **存量面** `meta.achievements_earned`——用户库里已落地的 id 串。

改名后果是**双向静默**的：只改定义面 ⇒ 解锁面继续往 meta 写旧 id，而
`get_all_earned:157` 的 `if aid in _ACHIEVEMENT_MAP` 会把它们**静默丢掉**（不报错、不自愈），
用户已解锁的成就凭空消失＝**幽灵 id**；只改解锁面 ⇒ 定义面那条永不可达＝**死成就**。
本桩把三向收成一次等值判定，当场变红。

口径说明
--------
- **不锁 `22` 字面量**：个数一律 `len(ACHIEVEMENTS)` 现取（完成标准①点名）。
  加/减成就只要两侧同步即绿；只动一侧即红。
- 解锁面取数用 **AST 抽 `check_achievements` 函数体内的字符串常量**，再减去「非 id 白名单」。
  不用正则、不 `import` 后反射（函数体内没有可枚举的 id 登记表，反射拿不到）。
  白名单里每一项都注明它为什么不是成就 id，并由 `test_白名单不得吞掉真成就id_*` 单独把守，
  防「误把真 id 挂进白名单 ⇒ 主例假绿」这条路。
- 与 l923-04（存储序列化格式改 JSON 数组）边界：本桩**只钉 id 集合**，不碰格式契约——
  格式断言在 `tests/test_achievements_branches.py:142-193`。本文件的存量面用例
  **同时喂 JSON 数组与旧裸逗号串两种形态**，因为真实库今天仍是旧串（见 `_LIVE_EARNED_SNAPSHOT` 注）。
- 零写盘：夹具库全用 `ProgressDAO(":memory:")`（照 `test_achievements_branches.py:132` 同型），
  **不碰 `data/progress.db`**（本仓惯例：`tests/` 一律不读真实库，见 `test_app_flow.py:1` 等处声明）。

复跑：PYTHONIOENCODING=utf-8 python -m pytest tests/test_achievements_id_reconcile.py -q
"""
import ast
import json
from pathlib import Path

import pytest

from core.achievements import ACHIEVEMENTS, _get_earned, _mark_earned, get_all_earned
from core.progress import ProgressDAO

ROOT = Path(__file__).resolve().parents[1]
ACHIEVEMENTS_SRC = ROOT / "core" / "achievements.py"

# ---------------------------------------------------------------------------
# 取数：定义面 / 解锁面
# ---------------------------------------------------------------------------

# `check_achievements` 函数体里**不是成就 id** 的字符串常量（15 条，逐项标身份）。
# 这份白名单是本桩唯一的"人工登记面"：往解锁实现里新增非 id 字面量（新事件名、新 dict 键…）
# 必须显式登记一次，否则主例会把那条字面量当成"解锁面多出一个未定义的成就 id"判红。
# 这是**刻意的噪声**——它保证白名单不会悄悄长大到能吞掉真 id。
_NON_ID_LITERALS = frozenset({
    "achievement_unlocked",   # dao.emit_event 的事件名
    "achievement_id",         # emit_event payload 的键
    "achievements: 解锁事件上报失败（不影响成就发放）",   # logger.debug 文案
    "agent_mastery",          # 路径 id（Path.id），不是成就 id
    "people_analytics",       # 路径 id，同上
    "python", "sql", "cpp", "r", "agent_dev",   # lang_map 的键：语言码
    "lang", "problem_id",     # milestone_progress 入参的字典键
    "solved", "pct",          # summary_by_lang / milestone_progress 的返回键
})


def _definition_ids() -> set:
    """定义面：ACHIEVEMENTS 的 id 全集（个数现取，不锁字面量）。"""
    return {a.id for a in ACHIEVEMENTS}


def _unlock_literal_ids() -> set:
    """解锁面：从 check_achievements 源码抽硬编码 aid 字面量（AST，非正则）。"""
    tree = ast.parse(ACHIEVEMENTS_SRC.read_text(encoding="utf-8"))
    fn = next((n for n in tree.body
               if isinstance(n, ast.FunctionDef) and n.name == "check_achievements"), None)
    assert fn is not None, (
        "check_achievements 不在 core/achievements.py 顶层了（被搬进类/改名/拆分？）"
        "⇒ 本桩的取数口径失效，请按磁盘实况改本函数，别放宽断言"
    )
    lits = {n.value for n in ast.walk(fn) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    lits.discard(ast.get_docstring(fn))          # 函数 docstring 也是 str 常量
    unknown = lits - _NON_ID_LITERALS
    return unknown


def _reconcile(definition_ids: set, unlock_ids: set) -> tuple:
    """纯函数：返回 (死成就 = 有定义无解锁, 幽灵 id = 有解锁无定义)。

    抽成纯函数是为了给 `test_哨兵有牙_*` 喂合成集合——不这样就只能真去改生产码才能验牙，
    那属写盘外的风险面（照 tests/test_insights_index_closure.py:_closure_diff 的同型做法）。
    """
    return (sorted(definition_ids - unlock_ids), sorted(unlock_ids - definition_ids))


# ---------------------------------------------------------------------------
# ① 定义面 ↔ 解锁面
# ---------------------------------------------------------------------------

def test_定义面与解锁面id集合相等():
    """主判据：两份清单必须逐个相同——任一侧改名即红（完成标准①）。"""
    defs, unlocks = _definition_ids(), _unlock_literal_ids()
    assert defs, "定义面取到空集——空循环会让本例假绿，判口径失效"
    dead, ghost = _reconcile(defs, unlocks)
    assert not dead, f"死成就（有定义、解锁面永不出它）：{dead}"
    assert not ghost, f"幽灵成就（解锁面会写、定义面无此条）：{ghost}"
    # 个数不锁字面量：只要求"两侧同数"，加/减成就同步改即绿
    assert len(defs) == len(unlocks), f"{len(defs)} != {len(unlocks)}"


def test_定义面无重复id且每条都有解锁位():
    """`{a.id}` 会静默折叠重复 ⇒ 主例可能因"定义面 21 唯一 + 解锁面 21"而假绿，故先钉长度等式。"""
    raw = [a.id for a in ACHIEVEMENTS]
    assert len(raw) == len(set(raw)), f"定义面有重复 id：{sorted({x for x in raw if raw.count(x) > 1})}"


@pytest.mark.parametrize("aid", sorted(_definition_ids()))
def test_每个定义id都出现在解锁面源码里(aid):
    """主例的逐条版：红名直接给出是哪一条成就的两侧漂移，不用再去 diff 两个集合。"""
    src = ACHIEVEMENTS_SRC.read_text(encoding="utf-8")
    fn = next(n for n in ast.parse(src).body
              if isinstance(n, ast.FunctionDef) and n.name == "check_achievements")
    lits = {n.value for n in ast.walk(fn) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert aid in lits, f"成就 {aid!r} 在定义面，但 check_achievements 函数体内无该字面量 ⇒ 改名所致"


# ---------------------------------------------------------------------------
# ② 白名单自证（防主例假绿的三道）
# ---------------------------------------------------------------------------

def test_白名单不得吞掉真成就id_且每项都仍在源码里():
    """白名单是本桩唯一的人工登记面，两条方向都要有牙：

    ① 白名单 ∩ 定义面 必须为空 ⇒ 否则真 id 被减掉，主例当场失明；
    ② 白名单每一项必须仍是 `check_achievements` 里的字面量 ⇒ 实现删了某条而白名单留着，
       说明本桩的取数口径已与实现脱节，要人来复核而不是静默通过。
    """
    defs = _definition_ids()
    overlap = sorted(_NON_ID_LITERALS & defs)
    assert overlap == [], f"非 id 白名单里挂着真成就 id，主例会被它骗过：{overlap}"
    src_lits = {n.value for n in ast.walk(ast.parse(ACHIEVEMENTS_SRC.read_text(encoding="utf-8")))
                if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    stale = sorted(x for x in _NON_ID_LITERALS if x not in src_lits)
    assert stale == [], f"白名单条目已不在 achievements.py 源码里（实现变了或登记过期）：{stale}"


def test_哨兵有牙_改名与漏改都必须红():
    """合成集合自证 `_reconcile` 不是永绿（零写盘、不碰生产码）。"""
    base = sorted(_definition_ids())
    assert len(base) >= 2, "定义面太少，合成不出可判的改名场景"
    victim, other = base[0], base[1]

    # ① 只改定义面（解锁面留旧名）⇒ 新名成死成就（有定义无解锁），
    #    旧名成幽灵（解锁面仍往 meta 写它，而 get_all_earned 会把它静默掩掉）
    defs_only = {("renamed_" + v if v == victim else v) for v in base}
    dead, ghost = _reconcile(defs_only, set(base))
    assert dead == ["renamed_" + victim] and ghost == [victim], (
        f"改名自检失败：应报 死=renamed_{victim} 幽灵={victim}，实报 {dead}/{ghost}")

    # ①' 反方向：只改解锁面（定义面留旧名）⇒ 旧定义变死成就、新写出的 id 无定义可归
    unlock_only = {("renamed_" + v if v == victim else v) for v in base}
    dead, ghost = _reconcile(set(base), unlock_only)
    assert dead == [victim] and ghost == ["renamed_" + victim], (
        f"漏改定义面自检失败：应报 死={victim} 幽灵=renamed_{victim}，实报 {dead}/{ghost}")

    # ② 定义面漏一条（新增成就只写了定义）⇒ 必须报死成就，且不报幽灵
    missing = {v for v in base if v != other}
    dead, ghost = _reconcile(set(base), missing)
    assert dead == [other] and ghost == [], f"漏解锁自检失败：{dead}/{ghost}"

    # ③ 两侧同步改名 ⇒ 必须绿（本桩只钉一致性，不钉具体 id 值）
    sync = {("renamed_" + v if v == victim else v) for v in base}
    assert _reconcile(sync, sync) == ([], []), "同步改名被误判——本桩不该拦正确升级"


# ---------------------------------------------------------------------------
# ③ 夹具库 roundtrip：每个定义 id 都能 _mark_earned → _get_earned 全量回收
# ---------------------------------------------------------------------------

def test_roundtrip_全量定义id可回收_现役json格式():
    """逐个标、最后一次性读：22 条（个数现取）必须全数回收，且落盘是现役 JSON 数组。

    l923-04 边界：本例**不验格式**（格式契约在 test_achievements_branches.py），
    只借 `startswith("[")` 一行确认夹具走的是现役分支而非旧串——否则本例测的其实是兼容读路径。
    """
    dao = ProgressDAO(":memory:")
    try:
        defs = _definition_ids()
        for aid in sorted(defs):
            _mark_earned(dao, aid)
            assert aid in _get_earned(dao), f"标完 {aid} 立刻读不到"
        earned = _get_earned(dao)
        assert earned == defs, f"roundtrip 丢失/多出：丢 {sorted(defs - earned)} 多 {sorted(earned - defs)}"
        raw = dao.get_meta("achievements_earned", "")
        assert raw.startswith("["), f"夹具库没走现役 JSON 写路径：{raw[:40]!r}"
        assert json.loads(raw) == sorted(defs)
        # 健康库不需要掩码：get_all_earned 的 `if aid in _ACHIEVEMENT_MAP` 不该过滤掉任何一条
        assert len(get_all_earned(dao)) == len(earned), "健康存量库竟被 get_all_earned 静默过滤 ⇒ 出现幽灵 id"
    finally:
        dao.close()


def test_roundtrip_旧逗号串形态同样可回收():
    """存量库里躺着旧格式（本仓真实库今天就是旧串，见 _LIVE_EARNED_SNAPSHOT）⇒
    定义面全量必须以"旧串进、同集合出"的方式过兼容读，否则改名风险会被格式迁移掩盖。"""
    dao = ProgressDAO(":memory:")
    try:
        defs = sorted(_definition_ids())
        dao.set_meta("achievements_earned", ",".join(defs))
        assert _get_earned(dao) == set(defs)
        # 兼容读不得产出幽灵空 id（_split_legacy 的过滤空段就是为这个）
        assert "" not in _get_earned(dao)
        dao.set_meta("achievements_earned", ",".join(defs) + ",,")
        assert "" not in _get_earned(dao), "旧串尾部空段被读成幽灵成就 id ''"
    finally:
        dao.close()


# ---------------------------------------------------------------------------
# ④ 存量对账：真实库 meta 实值 ⊆ 定义面
# ---------------------------------------------------------------------------

# 2026-09-23 由 l923-26 从 data/progress.db 实取的快照（**旧裸逗号串**形态）。
# 复算命令（只读法，本仓 progress.db 实测 journal_mode=delete、无 -wal/-shm 侧车）：
#   PYTHONIOENCODING=utf-8 python -c "import sqlite3;print(sqlite3.connect('file:data/progress.db?mode=ro&immutable=1',uri=True).execute(\"select value from meta where key='achievements_earned'\").fetchone())"
# 本常量的作用**不是**钉住用户拿了几成就（那是数据，会变），而是钉住
# "存量里已落地的 id 必须仍在定义面内"——改名当天即红。新拿成就只会从解锁面产生，
# 而解锁面已由主例钉成与定义面同集 ⇒ ⊆ 关系恒成立，除非有人改名。
_LIVE_EARNED_SNAPSHOT = "first_solve,multi_lang,no_mistakes,python_first,r_first,solve_10,sql_first"


def test_存量earned快照全在定义面内():
    earned = {s for s in _LIVE_EARNED_SNAPSHOT.split(",") if s}
    assert earned, "快照为空 ⇒ 本例假绿，重新取一次现值"
    defs = _definition_ids()
    ghosts = sorted(earned - defs)
    assert ghosts == [], (
        f"存量库里这些 id 已不在定义面（改名所致，用户侧已解锁成就会被静默掩掉）：{ghosts}")


def test_存量快照经兼容读后仍与定义面同向():
    """把真实存量串喂进夹具库走一遍读路径，再和定义面比 ⇒ 覆盖"存量 ⊆ 定义"的传递性。"""
    dao = ProgressDAO(":memory:")
    try:
        dao.set_meta("achievements_earned", _LIVE_EARNED_SNAPSHOT)
        earned = _get_earned(dao)
        assert earned <= _definition_ids(), f"经读路径后出现非定义面 id：{sorted(earned - _definition_ids())}"
        assert len(earned) == len(_LIVE_EARNED_SNAPSHOT.split(",")), "读路径丢了成就（分隔符/空段处理退化）"
    finally:
        dao.close()
