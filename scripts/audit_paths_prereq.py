# -*- coding: utf-8 -*-
"""l920-08：content/paths/*.yaml 的 topics / prereqs 引用 vs 五语言 content/ 实况 双向对账（只读）。

用途：复跑即得 docs/insights/learn-paths-prereq-20260919.md 的两张清单表。
用法：python scripts/audit_paths_prereq.py
零写库、零源码改动、零网络；仅读 content/ 下 yaml 与目录名。

口径：
  · topic 引用形如 "lang/slug"，落点 content/<lang>/<slug>/（存在性以目录为准）
  · prereq 引用为同 path 内 milestone id
  · 「未被引用」= 磁盘存在的 topic 目录，未被任何 path 的任何 milestone 引用
  · 「跨 path 重复」= 同一 topic 出现在 >1 个 path（与 tests/test_paths_reconcile.py 的
    「同 path 内重复」是两个不同口径，二者都保留）
"""
import collections
import glob
import os
import sys

import yaml

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONTENT = os.path.join(_ROOT, "content")
LANGS = ("python", "r", "cpp", "sql", "agent_dev")


def disk_topics():
    """{lang: sorted(slug)}——以 content/<lang>/<slug>/ 目录存在为准。"""
    out = {}
    for lang in LANGS:
        d = os.path.join(_CONTENT, lang)
        out[lang] = sorted(
            os.path.basename(p.rstrip("\\/")) for p in glob.glob(os.path.join(d, "*/"))
        )
    return out


def load_paths():
    """[{key,title,hours,ms_ids,refs:[(milestone_id, topic)], prereqs:[(mid, prereq)]}]"""
    out = []
    for f in sorted(glob.glob(os.path.join(_CONTENT, "paths", "*.yaml"))):
        key = os.path.basename(f)[:-5]
        d = yaml.safe_load(open(f, encoding="utf-8")) or {}
        ms = d.get("milestones", []) or []
        out.append({
            "key": key,
            "title": d.get("title", ""),
            "hours": d.get("estimated_hours"),
            "ms_ids": [m["id"] for m in ms],
            "ms_count": len(ms),
            "refs": [(m["id"], t) for m in ms for t in (m.get("topics") or [])],
            "prereqs": [(m["id"], pr) for m in ms for pr in (m.get("prereqs") or [])],
        })
    return out


def audit():
    disk = disk_topics()
    paths = load_paths()

    topic_refs = collections.defaultdict(list)   # "lang/slug" -> [(path, mid)]
    for p in paths:
        for mid, t in p["refs"]:
            topic_refs[t].append((p["key"], mid))

    # ① 悬空 topic 引用
    dangling = {}
    for t, where in topic_refs.items():
        parts = t.split("/", 1)
        if len(parts) != 2:
            dangling[t] = ("缺 lang/ 前缀", where)
        elif parts[0] not in disk:
            dangling[t] = ("语言目录不存在", where)
        elif parts[1] not in disk[parts[0]]:
            dangling[t] = ("同语言下 slug 目录不存在", where)

    # ② 未被任何 path 引用的 topic
    unreferenced = {lang: [s for s in disk[lang] if lang + "/" + s not in topic_refs]
                    for lang in LANGS}

    # ③ 悬空 prereq
    dangling_prereq = {}
    for p in paths:
        ids = set(p["ms_ids"])
        bad = [(mid, pr) for mid, pr in p["prereqs"] if pr not in ids]
        if bad:
            dangling_prereq[p["key"]] = bad

    # ④ 跨 path 重复引用
    cross = {t: v for t, v in topic_refs.items() if len({k for k, _ in v}) > 1}

    return {
        "disk": disk, "paths": paths, "topic_refs": topic_refs,
        "dangling": dangling, "unreferenced": unreferenced,
        "dangling_prereq": dangling_prereq, "cross_path_dup": cross,
    }


def render(a):
    L = []
    w = L.append
    disk, paths = a["disk"], a["paths"]
    refs = a["topic_refs"]
    w("## 一、口径与总量")
    w("")
    w("| 项 | 值 |")
    w("|---|---|")
    w("| 磁盘 topic 目录总数 | %d |" % sum(len(v) for v in disk.values()))
    w("| 其中 " + " / ".join(LANGS) + " | "
      + " / ".join(str(len(disk[l])) for l in LANGS) + " |")
    w("| paths 文件数 | %d |" % len(paths))
    w("| milestone 总数 | %d |" % sum(p["ms_count"] for p in paths))
    w("| topic 引用次数（含重复） | %d |" % sum(len(p["refs"]) for p in paths))
    w("| topic 去重后被引用数 | %d |" % len(refs))
    w("| 悬空 topic 引用 | %d |" % len(a["dangling"]))
    w("| 悬空 prereq 引用 | %d |" % sum(len(v) for v in a["dangling_prereq"].values()))
    w("| 未被任何 path 引用的 topic | %d |"
      % sum(len(v) for v in a["unreferenced"].values()))
    w("")
    w("### 各 path 概况")
    w("")
    w("| path | 标题 | header 时数 | milestone 数 | topic 引用次数 | 去重 |")
    w("|---|---|---|---|---|---|")
    for p in paths:
        uniq = len({t for _, t in p["refs"]})
        w("| %s | %s | %s | %d | %d | %d |"
          % (p["key"], p["title"], p["hours"], p["ms_count"], len(p["refs"]), uniq))
    w("")
    w("## 二、方向 A：path → content（悬空引用）")
    w("")
    if not a["dangling"]:
        w("**悬空 topic 引用：0 条。** 全部 %d 个去重 topic 引用都能在 content/<lang>/<slug>/ 找到实目录。" % len(refs))
    else:
        w("| 引用 | 落点检查 | 出现位置 |")
        w("|---|---|---|")
        for t, (why, where) in sorted(a["dangling"].items()):
            w("| %s | %s | %s |" % (t, why, ", ".join("%s/%s" % x for x in where)))
    w("")
    w("prereq 引用：%s" % ("**悬空 0 条**" if not a["dangling_prereq"]
                            else "悬空 %d 条" % sum(len(v) for v in a["dangling_prereq"].values())))
    w("")
    w("## 三、方向 B：content → path（未被引用 topic）")
    w("")
    w("| lang | 磁盘 topic | 被引用 | **未被引用** | 覆盖率 |")
    w("|---|---|---|---|---|")
    for lang in LANGS:
        tot = len(disk[lang])
        un = len(a["unreferenced"][lang])
        w("| %s | %d | %d | %d | %.1f%% |"
          % (lang, tot, tot - un, un, (tot - un) / tot * 100 if tot else 0))
    w("| **合计** | **%d** | **%d** | **%d** | **%.1f%%** |"
      % (sum(len(v) for v in disk.values()),
         len(refs), sum(len(v) for v in a["unreferenced"].values()),
         len(refs) / sum(len(v) for v in disk.values()) * 100))
    w("")
    for lang in LANGS:
        un = a["unreferenced"][lang]
        if not un:
            continue
        w("### %s 未被引用 %d 项" % (lang, len(un)))
        w("")
        for s in un:
            w("- `%s/%s`" % (lang, s))
        w("")
    w("## 四、跨 path 重复引用")
    w("")
    if not a["cross_path_dup"]:
        w("无。")
    else:
        w("| topic | 引用处 |")
        w("|---|---|")
        for t, where in sorted(a["cross_path_dup"].items()):
            w("| `%s` | %s |" % (t, "; ".join("%s/%s" % x for x in where)))
    w("")
    return "\n".join(L)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(render(audit()))
