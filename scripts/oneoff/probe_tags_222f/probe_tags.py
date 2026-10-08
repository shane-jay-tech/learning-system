# -*- coding: utf-8 -*-
"""只读探针 · 单 20260925-154244-222f

扫描三处标签漂移：题库（content/**/*.yaml 的 tags）、学习记录（progress.db 副本的标签型字段）、
报告（core/report.py + ui 侧消费口径）。产出＝规范化映射 + 不可自动合并项，零写入。
"""
import collections
import io
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# l1010-36 迁点：tmp/20260925-154244-222f/ → scripts/oneoff/probe_tags_222f/（深一层），
# ROOT 改三级上溯保持指向仓根（原 parent.parent 只适配 tmp 一层）。
ROOT = HERE.parents[2]
DB_COPY = HERE / "prod_copy.db"
PROD_DB = ROOT / "data" / "progress.db"

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
sys.path.insert(0, str(ROOT))


def sha8(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:8]


out = {"prod_db_sha8_before": sha8(PROD_DB), "db_copy_sha8": sha8(DB_COPY),
       "db_copy_sidecars": sorted(p.name for p in HERE.glob("prod_copy.db*"))}

# ---------------------------------------------------------------------------
# 1. 题库面：content/**/*.yaml 的 tags
# ---------------------------------------------------------------------------
counts = collections.Counter()
tag_files = collections.defaultdict(set)
lang_roots = collections.defaultdict(collections.Counter)
files = sorted((ROOT / "content").rglob("*.yaml"))
no_tags = []
raw_types = collections.Counter()
import yaml  # noqa: E402

for p in files:
    d = yaml.safe_load(io.open(p, encoding="utf-8").read()) or {}
    tags = d.get("tags")
    rel = p.relative_to(ROOT).as_posix()
    root_lang = rel.split("/")[1]
    if not tags:
        no_tags.append(rel)
        continue
    raw_types[type(tags).__name__] += 1
    vals = []
    for x in (tags if isinstance(tags, list) else [tags]):
        raw_types[f"item:{type(x).__name__}"] += 1
        vals.append(str(x))
    for v in vals:
        counts[v] += 1
        tag_files[v].add(rel)
        lang_roots[root_lang][v] += 1

out["bank_census"] = {
    "yaml_files": len(files),
    "unique_tags": len(counts),
    "occurrences": sum(counts.values()),
    "singletons": sum(1 for v in counts.values() if v == 1),
    "files_without_tags": len(no_tags),
    "files_without_tags_list": no_tags,
    "raw_yaml_types": dict(raw_types),
    "top30": counts.most_common(30),
}

SEPS = r"[\s\-]+"

multi_word = [v for v in counts if re.search(r"[\s\-_]", v)]
sep_mix = collections.Counter()
for v in multi_word:
    kinds = "+".join(sorted({("hyphen" if "-" in v else ""),
                             ("under" if "_" in v else ""),
                             ("space" if " " in v else "")} - {""})) or "single-token"
    sep_mix[kinds] += 1
out["bank_separator_convention"] = {
    "multi_word_tags": len(multi_word),
    "separator_mix": dict(sep_mix),
    "note": "多词 tag 的分隔符主流写法（映射方向按现值多数派，不改语义）",
}


def canon(s):
    k = s.strip().lower()
    k = re.sub(SEPS, "_", k)
    return re.sub(r"_+", "_", k)


groups = collections.defaultdict(list)
for v in counts:
    groups[canon(v)].append(v)

auto = {}
for k, vs in groups.items():
    if len(vs) > 1:
        auto[k] = sorted(vs, key=lambda x: -counts[x])
out["bank_auto_mergeable"] = {
    "rule": "A 级：trim + lowercase + 空白/连字符→下划线；只合并同形不同分隔符",
    "cluster_count": len(auto),
    "clusters": {k: {v: counts[v] for v in vs} for k, vs in sorted(auto.items())},
    "evidence_files": {k: sorted(tag_files[vs[0]])[:2] for k, vs in sorted(auto.items())},
}

# B 级：完全去分隔符（连字符/下划线/空格/点）后同形 ⇒ 字母集一致，只差分隔符
def canon2(s):
    return re.sub(r"[\s\-_.]+", "", s.lower())


groups2 = collections.defaultdict(list)
for v in counts:
    groups2[canon2(v)].append(v)
auto2 = {k: sorted(vs, key=lambda x: -counts[x]) for k, vs in groups2.items() if len(vs) > 1}
out["bank_auto_mergeable_tierB"] = {
    "rule": "B 级：去掉所有分隔符（- _ 空格 .）后完全同形 ⇒ 同一词只差分隔符",
    "cluster_count": len(auto2),
    "clusters": {k: {v: counts[v] for v in vs} for k, vs in sorted(auto2.items())},
    "evidence_files": {k: sorted({f for v in vs for f in tag_files[v]})[:3]
                       for k, vs in sorted(auto2.items())},
    "superset_of_tierA": all(k in auto2 for k in auto),
}

# 大小写敏感项（不可无脑小写化）
out["bank_case_significant"] = {v: counts[v] for v in counts if v != v.lower()}

# 含点号（语言原生语法，点号不是分隔符）
out["bank_dot_bearing"] = {v: counts[v] for v in counts if "." in v}
# 含运算符/其它标点
out["bank_other_punct"] = {v: counts[v] for v in counts
                           if re.search(r"[^A-Za-z0-9_\- \u4e00-\u9fff.]", v)}


def lev(a, b):
    if abs(len(a) - len(b)) > 2:
        return 9
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


vals = sorted(counts)
near = []
for i, a in enumerate(vals):
    for b in vals[i + 1:]:
        if canon(a) == canon(b):
            continue
        d = lev(a, b)
        # 收紧噪声：短词（<4）不参与近似判定；距离 1 需两侧都 ≥4 字符，
        # 距离 2 需两侧都 ≥6 字符且共享 ≥4 字前缀
        la, lb = len(a), len(b)
        ok = ((d == 1 and min(la, lb) >= 4
               and (a[:4] == b[:4] or sorted(a) == sorted(b)))          # 同前缀或字母转置＝typo 面
              or (d == 1 and abs(la - lb) == 1 and (a in b or b in a))   # 纯加尾缀＝单复数面
              or (d == 2 and min(la, lb) >= 6 and a[:4] == b[:4]))
        if ok:
            near.append({"pair": [a, b], "edit_distance": d,
                         "counts": [counts[a], counts[b]],
                         "roots": sorted({f.split("/")[1] for f in tag_files[a] | tag_files[b]}),
                         "files": sorted(tag_files[a] | tag_files[b])[:3]})
out["bank_near_duplicate_candidates"] = {
    "rule": "编辑距离1(两侧≥4字符) 或 距离2(两侧≥6字符且同 4 字前缀)，且归一后仍不同名 ⇒ 不可自动合并",
    "pair_count": len(near),
    "pairs": near,
}
out["bank_near_duplicate_raw_unfiltered"] = {
    "note": "宽口径（编辑距离≤2 不加长度门槛）的 pair 数，用来说明为什么必须收紧",
    "count": sum(1 for i, a in enumerate(vals) for b in vals[i + 1:]
                 if canon(a) != canon(b) and lev(a, b) <= 2),
}

# 词根家族（同主题不同措辞＝语义漂移，需人工）
fam = collections.defaultdict(set)
for v in vals:
    for tok in re.split(r"[_\- ]+", canon(v)):
        if len(tok) >= 4:
            fam[tok].add(v)
out["bank_token_families_top"] = {
    "note": "同一 token 下挂了 ≥3 种写法；跨概念，不可自动合并，只列前 12 个家族",
    "families": {t: sorted(vs) for t, vs in
                 sorted(((t, vs) for t, vs in fam.items() if len(vs) >= 3),
                        key=lambda x: -len(x[1]))[:12]},
}

# 同一归一概念在不同语言根下的写法分布（跨语言口径漂移）
cross = {}
for k, vs in groups.items():
    roots = {f.split("/")[1] for v in vs for f in tag_files[v]}
    if len(vs) > 1 or len(roots) > 1:
        cross[k] = {"spellings": vs, "roots": sorted(roots)}
out["bank_cross_root_variants"] = {"count": len(cross), "items": dict(sorted(cross.items()))}

# tag 与 topic slug 的重叠（同一信息两种标签面）
from core import loader  # noqa: E402

slug_tokens = collections.Counter()
bank_ids = set()
for lang in ("python", "sql", "cpp", "r", "agent_dev"):
    for t in loader.load_language(lang):
        bank_ids.add(f"{lang}/{t.slug}")
        for tok in re.split(r"[_\- ]+", canon(t.slug)):
            if len(tok) >= 4:
                slug_tokens[tok] += 1
out["bank_vs_topic_slug"] = {
    "note": "tag 词与 topic slug 词的重叠面（同一概念两处标签，非缺陷但属漂移面）",
    "topics": len(bank_ids),
    "tag_tokens_also_in_slug": sum(1 for t in fam if t in slug_tokens),
    "tag_tokens_total": len(fam),
}

# ---------------------------------------------------------------------------
# 2. 学习记录面（progress.db 的**只读副本**，mode=ro，无 immutable）
# ---------------------------------------------------------------------------
conn = sqlite3.connect(f"file:{DB_COPY.as_posix()}?mode=ro", uri=True)
out["db_journal_mode"] = conn.execute("PRAGMA journal_mode").fetchone()[0]


def distinct(sql):
    return [{"value": r[0], "rows": r[1]} for r in conn.execute(sql)]


out["record_vocab"] = {
    "attempts.lang": distinct("SELECT lang,COUNT(*) FROM attempts GROUP BY 1"),
    "problems_status.lang": distinct("SELECT lang,COUNT(*) FROM problems_status GROUP BY 1"),
    "problems_status.status": distinct("SELECT status,COUNT(*) FROM problems_status GROUP BY 1"),
    "learning_events.event_type": distinct("SELECT event_type,COUNT(*) FROM learning_events GROUP BY 1"),
    "learning_events.lang": distinct("SELECT COALESCE(lang,'<NULL>') AS lang,COUNT(*) FROM learning_events GROUP BY 1"),
    "meta.keys": distinct("SELECT key,COUNT(*) FROM meta GROUP BY 1"),
    "review_state rows": conn.execute("SELECT COUNT(*) FROM review_state").fetchone()[0],
    "rubric_scores rows": conn.execute("SELECT COUNT(*) FROM rubric_scores").fetchone()[0],
}

# 代码侧词表 vs 库侧实测值
code_status = {"solved", "wrong"}
code_events = {"attempt_submitted", "problem_passed", "problem_failed", "ai_open_scored",
               "recommendation_shown", "recommendation_clicked", "recommendation_completed",
               "path_started", "path_milestone_completed", "lesson_viewed", "achievement_unlocked"}
db_events = {r["value"] for r in out["record_vocab"]["learning_events.event_type"]}
db_status = {r["value"] for r in out["record_vocab"]["problems_status.status"]}
from ui.components import LANG_META  # noqa: E402

code_langs = set(LANG_META.keys())
db_langs = {r["value"] for r in out["record_vocab"]["attempts.lang"]}
out["record_drift"] = {
    "code_status_vocabulary": sorted(code_status),
    "db_status_values": sorted(db_status),
    "status_in_code_not_in_records": sorted(code_status - db_status),
    "code_event_vocabulary": sorted(code_events),
    "db_event_values": sorted(db_events),
    "events_in_code_not_in_records": sorted(code_events - db_events),
    "events_in_records_not_in_code": sorted(db_events - code_events),
    "code_lang_vocabulary": sorted(code_langs),
    "db_lang_values": sorted(db_langs),
    "langs_in_code_not_in_records": sorted(code_langs - db_langs),
    "content_roots": sorted(lang_roots),
    "langs_in_content_not_in_records": sorted(set(lang_roots) - db_langs),
}

# 记录引用的题号是否在世
rec_pids = {r[0] for r in conn.execute(
    "SELECT DISTINCT problem_id FROM attempts UNION SELECT DISTINCT problem_id FROM problems_status "
    "UNION SELECT DISTINCT problem_id FROM learning_events WHERE problem_id IS NOT NULL")}
live_pids = {p.id for lang in ("python", "sql", "cpp", "r", "agent_dev")
             for t in loader.load_language(lang) for p in t.problems}
out["record_id_orphans"] = {
    "referenced_problem_ids": len(rec_pids),
    "live_problem_ids": len(live_pids),
    "referenced_but_not_in_bank": sorted(rec_pids - live_pids),
    "shape_check": {
        "total": len(rec_pids),
        "three_segment_slug": sum(1 for p in rec_pids if len(p.split("/")) == 3),
        "other_shape": sorted(p for p in rec_pids if len(p.split("/")) != 3),
    },
}

# 事件与作答的计数不对称（只报数，不作废）
out["record_count_asymmetry"] = {
    "attempts_rows": conn.execute("SELECT COUNT(*) FROM attempts").fetchone()[0],
    "attempt_submitted_events": conn.execute(
        "SELECT COUNT(*) FROM learning_events WHERE event_type='attempt_submitted'").fetchone()[0],
    "problem_passed_events": conn.execute(
        "SELECT COUNT(*) FROM learning_events WHERE event_type='problem_passed'").fetchone()[0],
    "problem_failed_events": conn.execute(
        "SELECT COUNT(*) FROM learning_events WHERE event_type='problem_failed'").fetchone()[0],
    "attempts_passed_0": conn.execute("SELECT COUNT(*) FROM attempts WHERE passed=0").fetchone()[0],
    "attempts_passed_1": conn.execute("SELECT COUNT(*) FROM attempts WHERE passed=1").fetchone()[0],
    "distinct_created_at_clusters": conn.execute(
        "SELECT created_at, COUNT(*) FROM learning_events GROUP BY created_at ORDER BY COUNT(*) DESC LIMIT 4"
    ).fetchall(),
    "note": "题面标签漂移不依赖这些计数；此节仅登记不对称，不作归因（在册观察项见纪律档 23.3 learning 行）",
}

# ---------------------------------------------------------------------------
# 3. 报告面：报告/UI 消费的标签口径
# ---------------------------------------------------------------------------
from core.recommend import _topic_weakness, all_problems  # noqa: E402

status = {(r[0], r[1]): r[2] for r in conn.execute(
    "SELECT lang, problem_id, status FROM problems_status")}
items = all_problems()
wk = _topic_weakness(items, status)
import core.report as _rep  # noqa: E402
import inspect  # noqa: E402

out["report_surface"] = {
    "weakness_key_shape": sorted({k.split("/")[0] for k in wk}) if wk else [],
    "weakness_keys_total": len(wk),
    "weakness_sample_keys": sorted(wk)[:3],
    "note": "报告侧弱项标签用 `lang/topic_slug` 两段键（不含 tags 词表）⇒ tags 在报告面同样零消费",
}
src = inspect.getsource(_rep)
out["report_surface"]["report_status_literals"] = sorted(set(re.findall(r'"(solved|wrong|todo|done)"', src)))
out["report_surface"]["generate_report_signature"] = str(inspect.signature(_rep.generate_report))

# tags 在生产侧的读者（复核前档「零读者」口径是否仍成立）
hits = []
for py in sorted(list((ROOT / "core").rglob("*.py")) + list((ROOT / "ui").rglob("*.py"))
                 + list((ROOT / "scripts").rglob("*.py"))):
    text = py.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"(?:\.get\([\"']tags[\"']\)|\[([\"'])tags\1\]|\.tags\b)", text):
        ln = text[:m.start()].count("\n") + 1
        hits.append(f"{py.relative_to(ROOT).as_posix()}:{ln}")
out["tags_readers"] = {
    "note": "AST 之外的正则轨：生产/脚本面读 tags 值的行号",
    "hit_count": len(hits),
    "hits": hits,
    "lang_vocab_in_ui": sorted(LANG_META.keys()) if "LANG_META" in dir() else None,
}
conn.close()

out["prod_db_sha8_after"] = sha8(PROD_DB)
out["prod_untouched"] = out["prod_db_sha8_before"] == out["prod_db_sha8_after"]
print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
