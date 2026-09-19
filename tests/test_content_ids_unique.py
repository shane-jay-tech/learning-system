# -*- coding: utf-8 -*-
"""五语言题目 id 唯一性与 slug 跨语言冲突契约（l918-28）。

全量加载 399 题断言：
  ① 各语言内 problem id 全局唯一（id 形如 <lang>/<topic_slug>/<nnn>，天然带语言前缀）；
  ② 跨语言 topic slug 冲突面 == 已知清单（agent_dev 的 07_write_spec 等「目录名即 slug」
     例外已计入；当前唯一真冲突 = 04_functions 同时出现在 python 与 cpp）——钉桩现状，
     修复（改名）或新增冲突都须有意翻桩；
  ③ 目录名与 frontmatter id 前缀一致（problem.id 以 <lang>/<topic_slug>/ 开头）。
"""
from collections import Counter

from core.loader import load_language

LANGS = ("python", "sql", "cpp", "r", "agent_dev")

# 已知跨语言 slug 冲突现状（l918-28 钉桩；修复后更新此清单）
KNOWN_CROSS_SLUG_CONFLICTS = ["04_functions"]


def _all():
    for lang in LANGS:
        for topic in load_language(lang):
            yield lang, topic


def test_各语言内题目id唯一():
    for lang in LANGS:
        ids = [p.id for _, t in _all() if _ == lang for p in t.problems] if False else \
              [p.id for lang2, t in _all() for p in t.problems if lang2 == lang]
        dup = [k for k, v in Counter(ids).items() if v > 1]
        assert not dup, f"{lang} 内重复题目 id：{dup}"


def test_跨语言slug冲突_仅已知04_functions():
    slugs = Counter(t.slug for _, t in _all())
    conflicts = sorted(s for s, c in slugs.items() if c > 1)
    assert conflicts == sorted(KNOWN_CROSS_SLUG_CONFLICTS), f"跨语言 slug 冲突漂移：{conflicts}"


def test_题目id前缀与语言目录一致():
    for lang, t in _all():
        for p in t.problems:
            assert p.id.startswith(f"{lang}/{t.slug}/"), f"{p.id} 前缀与 {lang}/{t.slug} 不一致"
