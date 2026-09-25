# -*- coding: utf-8 -*-
"""导入前 **dry-run 体检器**（全程只读；桥接单 20260925-120605-f1d8，风险档 B / 工作类型 import）。

它回答的是 `core/data_portability.import_all()` 今天**不回答**的问题：
`import_all` 一上来就写库，学生点「确认导入」之前没有任何地方能告诉他
"这份文件会往我的进度里加多少、覆盖多少、和什么打架"。

六个体检面（卷宗点名的四类 ＋ 本档补的两类）：
  字段 / 编码 / 重复 id / 引用资源 / 非法答案 / **新增·更新·冲突** 三态计数

用法（仓库根执行）：
    python scripts/import_dry_run.py                       # 自检态：现库导出件回灌现库
    python scripts/import_dry_run.py --payload x.json      # 体检一份真实导出件
    python scripts/import_dry_run.py --json                # 机器可读输出

设计约束（写在码内，防后来者顺手"修好"）：
  · 🔴 **只读**：库以 `mode=ro` ＋ `PRAGMA query_only=ON` 打开，末尾自证写句柄被拒；
  · 🔴 **不改 `import_all` 的去重语义**：append 表在 `import_all` 层面刻意不去重，
    那是 `tests/test_data_portability.py:46-59` 的 by-design 断言（`total == before*2`），
    l923-09 已把二次点击的口子堵在 UI 层（sha256 指纹）。本脚本只**报**，不**替**。
  · 未接进任何门禁/CI：属"只建本体、不接线"，接线与否交主班裁。
"""
import argparse
import hashlib
import io
import json
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DB_REL = "data/progress.db"
APPEND_TABLES = ("attempts", "learning_events", "rubric_scores")
KEYED_TABLES = ("problems_status", "review_state", "meta")

#: 每张表的业务键——「重复 id」与「冲突」都按它判（自增 id 跨机迁移必然重排，不可当键）
BUSINESS_KEYS = {
    "attempts": ("lang", "problem_id", "ts"),
    "learning_events": ("event_type", "lang", "problem_id", "created_at", "payload_json"),
    "rubric_scores": ("lang", "problem_id", "dimension_id", "ts"),
    "problems_status": ("lang", "problem_id"),
    "review_state": ("lang", "problem_id"),
    "meta": ("key",),
}
#: 导出文件声明的列（与 core/data_portability.py 的 SELECT 列表面向同一口径）
PAYLOAD_COLUMNS = {
    "attempts": ["lang", "problem_id", "code", "passed", "ai_feedback", "ts"],
    "problems_status": ["lang", "problem_id", "status", "last_attempt_ts"],
    "review_state": ["lang", "problem_id", "interval_days", "ease", "review_streak",
                     "next_due_date", "last_result", "updated_ts"],
    "rubric_scores": ["lang", "problem_id", "attempt_id", "dimension", "dimension_id",
                      "score", "comment", "prompt_version", "model", "ts"],
    "learning_events": ["event_type", "lang", "topic_id", "problem_id", "path_id",
                        "milestone_id", "payload_json", "created_at", "local_date"],
    "meta": ["key", "value", "updated_ts"],
}
#: `core/progress.py:159` 只写这两个值；:232 的统计口径也把其它值直接丢弃 ⇒ 其它值＝非法
LEGAL_STATUS = {"solved", "wrong"}
LEGAL_PASSED = {0, 1, True, False}
#: **真正不得为空**的键。注意别拿 BUSINESS_KEYS 当它用——`learning_events` 的
#: topic_id/path_id/milestone_id/payload_json 对多数事件类型**本就设计为 NULL**
#: （`lesson_viewed` 没有 problem_id、`achievement_unlocked` 没有 payload_json），
#: 按 BUSINESS_KEYS 判空会把 30 行正常数据报成缺陷＝体检器自己造出假阳性。
REQUIRED_KEYS = {
    "attempts": ("lang", "problem_id"),
    "learning_events": ("event_type",),
    "rubric_scores": ("lang", "problem_id"),
    "problems_status": ("lang", "problem_id", "status"),
    "review_state": ("lang", "problem_id"),
    "meta": ("key",),
}


def db_fingerprint(db_path: Path) -> dict:
    """库文件指纹：size ＋ mtime(ns) ＋ 全文件 sha256。dry-run 前后必须逐位相同。"""
    st = db_path.stat()
    with open(db_path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    return {"size": st.st_size, "mtime_ns": st.st_mtime_ns, "sha256": digest}


def open_ro(db_path: Path) -> sqlite3.Connection:
    """只读连接。§十四 的教训：读写打开的末次连接会 checkpoint 改掉生产库本身。"""
    con = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True, isolation_level=None)
    con.execute("PRAGMA query_only=ON")
    return con


def _content_index() -> Dict[str, set]:
    """题号索引：lang -> {problem_id}。只读 content/，与 core/loader 的 id 拼法同型。"""
    import yaml
    from ui.components import ALL_LANGS  # 语言词表的唯一权威（见 l924-tag-spec §2.1）

    idx: Dict[str, set] = {lang: set() for lang in ALL_LANGS}
    for lang in ALL_LANGS:
        lang_dir = ROOT / "content" / lang
        if not lang_dir.is_dir():
            continue
        for y in sorted(lang_dir.rglob("*.yaml")):
            try:
                data = yaml.safe_load(io.open(y, encoding="utf-8").read())
            except Exception:  # noqa 坏文件由 loader/audit 面负责，这里只当"没这道题"
                continue
            if isinstance(data, dict) and "statement" in data:
                idx[lang].add(f"{lang}/{y.parent.name}/{y.stem}")
    return idx


def _is_well_formed_str(v) -> Optional[str]:
    """字符串能否无损 UTF-8 往返。返回问题标签或 None。

    JSON 允许把孤立代理对（\\ud800）塞进字符串——`encode('utf-8')` 当场抛，
    这种值写进库后会在下游任何一次打印/序列化时炸，属导入前必须拦的一类。
    """
    if not isinstance(v, str):
        return None
    if "\x00" in v:
        return "NUL"
    try:
        v.encode("utf-8")
    except UnicodeEncodeError:
        return "孤立代理对"
    if "\ufffd" in v:
        return "替换字符（疑似上游编码已损坏）"
    return None


def inspect_payload(payload: dict, con: sqlite3.Connection,
                    content_index: Dict[str, set]) -> dict:
    """六面体检。纯读：一次 SELECT 都不写，返回值全为计数与样例。"""
    from core.data_portability import _validate

    rep: dict = {"errors": [], "fields": [], "encoding": [], "duplicates": [],
                 "references": [], "illegal": [], "merge": {}, "scanned": {}}
    err = _validate(payload) if isinstance(payload, dict) else "不是 JSON 对象"
    if err:
        rep["errors"].append(f"结构校验失败：{err}")
        return rep
    data = payload["data"]

    for table in APPEND_TABLES + KEYED_TABLES:
        rows = [r for r in data[table] if isinstance(r, dict)]
        rep["scanned"][table] = len(rows)
        known = {d[1] for d in con.execute(f"PRAGMA table_info({table})").fetchall()}

        # ① 字段面：未知列会被 _insert_rows 静默丢掉（学生数据无声蒸发）
        declared = set()
        for r in rows:
            declared |= {k for k in r if k not in known}
        if declared:
            rep["fields"].append({"table": table, "unknown_columns_dropped": sorted(declared),
                                  "count": len(rows)})
        missing_key = [i for i, r in enumerate(rows)
                       if any(r.get(k) is None or (isinstance(r.get(k), str) and not r.get(k).strip())
                              for k in REQUIRED_KEYS[table])]
        if missing_key:
            rep["fields"].append({"table": table, "missing_business_key_rows": len(missing_key)})

        # ② 编码面
        bad_enc = Counter()
        for r in rows:
            for k, v in r.items():
                tag = _is_well_formed_str(v)
                if tag:
                    bad_enc[f"{k}:{tag}"] += 1
        if bad_enc:
            rep["encoding"].append({"table": table, "issues": dict(bad_enc)})

        # ③ 重复 id 面：文件内部 ＋ 与现库现有行
        keys = [tuple(str(r.get(k)) for k in BUSINESS_KEYS[table]) for r in rows]
        inner_dup = {k: c for k, c in Counter(keys).items() if c > 1}
        existing = set()
        bk = BUSINESS_KEYS[table]
        try:
            for row in con.execute(f"SELECT {','.join(bk)} FROM {table}"):
                existing.add(tuple(str(x) for x in row))
        except sqlite3.Error as e:            # 只读库里没这张表/列：如实记，不猜
            rep["errors"].append(f"{table} 现库取键失败：{e}")
        overlap = [k for k in keys if k in existing]
        rep["duplicates"].append({"table": table, "inner_duplicate_keys": len(inner_dup),
                                  "already_in_db_rows": len(overlap),
                                  "sample": [list(x) for x in (list(inner_dup)[:2] + overlap[:2])]})

        # ④ 引用资源面
        langs = {str(r.get("lang")) for r in rows if r.get("lang") is not None}
        unknown_lang = sorted(langs - set(content_index))
        if unknown_lang:
            rep["references"].append({"table": table, "unknown_lang": unknown_lang})
        if table in ("attempts", "problems_status", "review_state", "rubric_scores"):
            orphan = []
            for r in rows:
                lang, pid = r.get("lang"), r.get("problem_id")
                if lang in content_index and pid is not None and str(pid) not in content_index[lang]:
                    orphan.append(f"{lang}|{pid}")
            if orphan:
                # 报数不报名等于没报：主班要靠这几个题号去核"是题被删了还是键拼错了"
                rep["references"].append({"table": table, "problem_id_not_in_content": len(orphan),
                                          "sample": sorted(set(orphan))[:5]})
        if table == "rubric_scores":
            try:
                live = {x[0] for x in con.execute("SELECT id FROM attempts")}
            except sqlite3.Error:
                live = set()
            dangling = sum(1 for r in rows
                           if r.get("attempt_id") is not None and int(r["attempt_id"]) not in live)
            if dangling:
                # 自增 id 跨机必然重排：导入后 attempt_id 指向的是**别的**作答
                rep["references"].append({"table": table,
                                          "attempt_id_will_dangle_or_shift": dangling})

        # ⑤ 非法答案面（不改任何判分口径，只报"导入后统计会失真"的行）
        if table == "attempts":
            bad = sum(1 for r in rows if r.get("passed") not in LEGAL_PASSED)
            if bad:
                rep["illegal"].append({"table": table, "passed_not_boolean_like": bad})
        if table == "problems_status":
            bad = Counter(str(r.get("status")) for r in rows if r.get("status") not in LEGAL_STATUS)
            if bad:
                rep["illegal"].append({"table": table, "status_illegal_will_silently_vanish": dict(bad)})
        if table == "review_state":
            neg = sum(1 for r in rows
                      if isinstance(r.get("interval_days"), (int, float)) and r["interval_days"] < 0
                      or isinstance(r.get("ease"), (int, float)) and r["ease"] <= 0
                      or isinstance(r.get("review_streak"), (int, float)) and r["review_streak"] < 0)
            if neg:
                rep["illegal"].append({"table": table, "negative_or_zero_bounds": neg})
        if table == "rubric_scores":
            nonnum = sum(1 for r in rows
                         if r.get("score") is not None and not isinstance(r.get("score"), (int, float)))
            if nonnum:
                # 代码里没定义 score 的上界，故只报"根本不是数值"，不发明阈值
                rep["illegal"].append({"table": table, "score_not_numeric": nonnum})

        # ⑥ 三态计数：新增 / 更新 / 冲突（逐表镜像 import_all 的真实命运，含它的跳过条件）
        skipped = 0
        if table in KEYED_TABLES:
            new = upd = conflict = 0
            for r in rows:
                if _prod_skips(table, r):
                    skipped += 1
                    continue
                k = tuple(str(r.get(x)) for x in BUSINESS_KEYS[table])
                if k not in existing:
                    new += 1
                    continue
                upd += 1
                if _row_differs(con, table, r, existing):
                    conflict += 1
            rep["merge"][table] = {"insert_new": new, "overwrite_same_key": upd,
                                  "conflict_value_differs": conflict,
                                  "skipped_by_import_all": skipped,
                                  "mode": "INSERT OR REPLACE（导入方覆盖本地）"
                                          if table != "meta" else "UPSERT（导入方覆盖本地）"}
        else:
            dup = sum(1 for k in keys if k in existing)
            rep["merge"][table] = {"insert_new": len(keys) - dup, "overwrite_same_key": 0,
                                   "conflict_value_differs": dup,
                                   "skipped_by_import_all": skipped,
                                   "mode": "纯追加（import_all 刻意不去重＝by design，"
                                           "见 tests/test_data_portability.py 的 before*2 断言）"}
    return rep


def _prod_skips(table: str, row: dict) -> bool:
    """镜像 `core/data_portability.import_all` 的跳过条件，别让体检报告说假话。

    生产侧只有这一处丢行：`meta` 表的 `if not r.get("key"): continue`。
    其余键控表即使 lang/problem_id 为空也照样写——那是**真会写**，本函数不能替它"修正"。
    """
    return table == "meta" and not row.get("key")


def _row_differs(con, table: str, incoming: dict, _existing) -> bool:
    """同业务键下，非键列是否有任一值与现库不同（不同＝覆盖会改数据，属冲突）。"""
    keys = BUSINESS_KEYS[table]
    where = " AND ".join(f"{k}=?" for k in keys)
    try:
        cur = con.execute(f"SELECT * FROM {table} WHERE {where}",
                          tuple(incoming.get(k) for k in keys))
    except sqlite3.Error:
        return False
    cols = [d[0] for d in cur.description or []]
    row = cur.fetchone()
    if row is None:
        return False
    live = dict(zip(cols, row))
    return any(str(live.get(c)) != str(incoming.get(c))
               for c in incoming if c in live and c not in keys)


def self_export_payload(con: sqlite3.Connection) -> dict:
    """自检态载荷：在只读连接上现算一份"本库导出件"。

    不 import `export_all`——它要一个 ProgressDAO（读写句柄），而本脚本连一次读写打开都不该做。
    列与 `core/data_portability.py` 的 SELECT 表面向同一口径，故等价。
    """
    def rows(sql):
        cur = con.execute(sql)
        cols = [d[0] for d in cur.description or []]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

    from core.data_portability import FORMAT_NAME, FORMAT_VERSION
    return {
        "format": FORMAT_NAME, "version": FORMAT_VERSION,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "data": {
            "attempts": rows("SELECT lang, problem_id, code, passed, ai_feedback, ts "
                             "FROM attempts ORDER BY id"),
            "problems_status": rows("SELECT lang, problem_id, status, last_attempt_ts "
                                    "FROM problems_status"),
            "review_state": rows("SELECT lang, problem_id, interval_days, ease, review_streak, "
                                 "next_due_date, last_result, updated_ts FROM review_state"),
            "rubric_scores": rows("SELECT lang, problem_id, attempt_id, dimension, dimension_id, "
                                  "score, comment, prompt_version, model, ts FROM rubric_scores ORDER BY id"),
            "learning_events": rows("SELECT event_type, lang, topic_id, problem_id, path_id, "
                                    "milestone_id, payload_json, created_at, local_date "
                                    "FROM learning_events ORDER BY id"),
            "meta": rows("SELECT key, value, updated_ts FROM meta"),
        },
    }


def assert_write_refused(con: sqlite3.Connection) -> str:
    """正面自证"这个连接写不进去"：真试一次 INSERT，必须抛，且抛完库仍是原态。"""
    try:
        con.execute("INSERT INTO meta (key, value, updated_ts) VALUES ('__dryrun_probe__','1','')")
    except sqlite3.OperationalError as e:
        return f"写句柄被拒（OperationalError: {e}）"
    raise AssertionError("只读连接竟然写进去了——本脚本的只读前提不成立，必须停手")


def _print_human(rep: dict, mode: str) -> None:
    print(f"== 导入 dry-run 体检（{mode}）==")
    if rep["errors"]:
        print("  🔴 结构面失败：", rep["errors"])
        return
    print(f"  扫描行数：{rep['scanned']}")
    print("\n  【新增/更新/冲突】（键控表按业务键判，append 表按是否与现库同键判）")
    for t, m in rep["merge"].items():
        print(f"    {t:16} 新增 {m['insert_new']:>4} / 更新 {m['overwrite_same_key']:>4} / "
              f"冲突 {m['conflict_value_differs']:>4}   ← {m['mode']}")
    for label, key in (("字段", "fields"), ("编码", "encoding"), ("重复 id", "duplicates"),
                       ("引用资源", "references"), ("非法答案", "illegal")):
        items = rep[key]
        print(f"\n  【{label}】")
        if not items:
            print("    （无发现）")
            continue
        for it in items:
            print(f"    {it.pop('table', '-') if isinstance(it, dict) else it}: "
                  + json.dumps(it, ensure_ascii=False)[:220])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="导入前 dry-run 体检（只读，不写库）")
    ap.add_argument("--payload", help="待体检的导出 .json；缺省＝现库自导出回灌自检")
    ap.add_argument("--db", default=str(ROOT / DB_REL))
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = ap.parse_args(argv)

    db_path = Path(args.db)
    if not db_path.is_file():
        print(f"找不到库：{db_path}", file=sys.stderr)
        return 2
    before = db_fingerprint(db_path)
    con = open_ro(db_path)
    try:
        payload = (json.loads(Path(args.payload).read_text(encoding="utf-8"))
                   if args.payload else self_export_payload(con))
        mode = f"外部载荷 {args.payload}" if args.payload else "自检态：现库导出件回灌现库"
        rep = inspect_payload(payload, con, _content_index())
        refusal = assert_write_refused(con)
    finally:
        con.close()
    after = db_fingerprint(db_path)

    rep["dry_run_proof"] = {
        "write_refused": refusal,
        "before": before, "after": after,
        "unchanged": before == after,
    }
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        _print_human(rep, mode)
        print(f"\n  【只读自证】{refusal}")
        print(f"    指纹 before={before['size']}B/{before['sha256'][:16]}"
              f" after={after['size']}B/{after['sha256'][:16]} → "
              f"{'逐位相同 ✅' if before == after else '🔴 变了！dry-run 前提被破坏'}")
    return 0 if before == after and not rep["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
