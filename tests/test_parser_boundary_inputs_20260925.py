# -*- coding: utf-8 -*-
"""解析器边界输入包：空文件／编码声明／语法错／超大输入／Unicode 标识符。

对应信箱单 `20260925-120550-1247`（A 档／test；执行班 `qoder-executor-20260925-1630-learn38`）。

卷宗原文：「用空文件、编码声明、语法错、超大输入和 Unicode 标识符测试解析器。
验收：错误能定位行列且不会使服务进程退出。」

**"解析器"在本仓有两处实体**（先 `rg` 证其在世，两处都真、都测）：

1. **内容解析器** `core/loader.py:126 load_language` → `yaml.safe_load`，
   坏文件隔离成 `LoadDiag(path, error_type, message)`（`message` 被 `[:200]` 截断）。
2. **学生代码前端** `core/runners/python_runner.py`（拼 preamble 后交给解释器）
   ＋ `core/runners/error_feedback.py`（`locate`／`locate_column`／`classify`）。

按实况收窄的两点（登记为缺陷，不改行为）：
- 卷宗说"能定位**行列**"——**Python 侧只有行，列恒为 `None`**（`locate_column` 只认 cpp）⇒ D-12。
- 卷宗暗示"编码声明"会被解析——**恰恰不会**：preamble 把学生第 1 行挤到第 7 行，
  CPython 只在**前两行**认编码声明 ⇒ 声明被静默忽略 ⇒ D-13（信息级）。

覆盖面自证：每条负向断言配正向对照（正常题仍加载／CJK 标识符仍可运行／探测器分得死活）。
"""
import json
import sys
import time
from pathlib import Path

import pytest
import yaml

from core import loader
from core.progress import ProgressDAO
from core.runners.error_feedback import classify, locate, locate_column
from core.runners.python_runner import MAX_STDERR_BYTES, PythonRunner

REPO = Path(__file__).resolve().parents[1]
TRUNC_MARK = "输出过长，已截断"

GOOD_YAML = "id: ok\ntitle: 正常题\ndifficulty: 2\nstatement: 题面\nstarter_code: ''\n"
GOOD_YAML_NAME = "z_good.yaml"
GOOD_STEM = "z_good"


@pytest.fixture(scope="module")
def runner():
    return PythonRunner()


@pytest.fixture(autouse=True)
def _sandbox_progress_db(monkeypatch, tmp_path):
    """与单 1 同一道防线：`judge._record_attempt(dao=None)` 会自开生产库。"""
    fake = tmp_path / "learn38-parser-sandbox.db"
    monkeypatch.setenv("LS_PROGRESS_DB", str(fake))
    assert ProgressDAO().db_path == str(fake)
    yield fake


@pytest.fixture
def content_dir(tmp_path):
    """造一个隔离的 content 根（绝不碰仓内 `content/**` 真实题库）。"""
    root = tmp_path / "content"

    def _make(files, slug="t1", lang="python"):
        d = root / lang / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "_lesson.md").write_text("# 课时\n", encoding="utf-8")
        for name, body in files.items():
            p = d / name
            if isinstance(body, bytes):
                p.write_bytes(body)
            else:
                p.write_text(body, encoding="utf-8")
        loader.invalidate_cache()
        topics = loader.load_language(lang, str(root))
        return topics, loader.get_load_diagnostics()

    return _make


def _loaded_ids(topics):
    return [p.id for t in topics for p in t.problems]


def _diag_names(diags):
    return sorted(Path(x.path).name for x in diags)


# ---------------------------------------------------------------------------
# 1) 空文件与退化文件
# ---------------------------------------------------------------------------

class TestEmptyFiles:
    def test_zero_byte_yaml_becomes_a_ghost_problem_with_no_diagnostic(self, content_dir):
        """**缺陷 D-6**：0 字节 yaml **不产诊断**，静默生成一道幽灵题。

        `yaml.safe_load` → `None` → `or {}` → 空 dict 被判"合法 mapping"
        ⇒ `title` 回退成文件名、题面/代码全空，学生端会看到一条点开的空题。
        """
        topics, diags = content_dir({"empty.yaml": "", GOOD_YAML_NAME: GOOD_YAML})
        assert diags == []                       # 实况：无诊断（缺陷所在）
        ids = _loaded_ids(topics)
        assert "python/t1/empty" in ids          # 实况：进了题库（缺陷所在）
        ghost = [p for t in topics for p in t.problems if p.id == "python/t1/empty"][0]
        assert ghost.title == "empty" and ghost.statement == ""

    def test_comment_only_yaml_is_also_silent(self, content_dir):
        topics, diags = content_dir({"only_comment.yaml": "# 只有注释\n"})
        assert diags == [] and "python/t1/only_comment" in _loaded_ids(topics)

    def test_non_mapping_root_is_caught_and_reported(self, content_dir):
        """正向对照：根不是 mapping 时**有**隔离诊断（说明上一条不是"诊断机制坏了"）。"""
        topics, diags = content_dir({"root_list.yaml": "- a\n- b\n",
                                     "scalar.yaml": "just a string\n",
                                     GOOD_YAML_NAME: GOOD_YAML})
        assert _diag_names(diags) == ["root_list.yaml", "scalar.yaml"]
        assert {x.error_type for x in diags} == {"TypeError"}
        assert _loaded_ids(topics) == ["python/t1/" + GOOD_STEM]

    def test_empty_and_blank_student_code_still_exits_zero(self, runner):
        """学生代码侧的空输入：空串／纯空白／只有注释 ⇒ rc 0，宿主无事。"""
        for code in ("", "   \n\t\n", "# 只有注释\n", "\n\n\n"):
            r = runner.run(code)
            assert r.exit_code == 0, repr(code)
            assert r.error_kind is None and r.stderr == ""


# ---------------------------------------------------------------------------
# 2) 编码声明
# ---------------------------------------------------------------------------

class TestEncodingDeclarations:
    def test_coding_declaration_is_silently_ignored_after_preamble(self, runner):
        """**缺陷 D-13（信息级）**：学生第 1 行的编码声明被 preamble 挤到第 7 行
        ⇒ CPython 只认前两行 ⇒ 声明**根本不生效**。

        用**不存在的 codec 名**才有牙：若声明真被读取，必然 `SyntaxError: unknown encoding`；
        实测 rc 0 ⇒ 证明它连"是否合法编码"都没看过。
        """
        bogus = runner.run("# -*- coding: koi8-nonexistent-99 -*-\nprint('ran')\n")
        assert bogus.exit_code == 0
        assert "unknown encoding" not in bogus.stderr
        assert bogus.stdout.strip() == "ran"

    def test_bom_at_start_of_student_code_is_a_located_syntax_error(self, runner):
        """UTF-8 BOM 当首字符：解释器报"invalid non-printable character"，行号要折回第 1 行。"""
        r = runner.run("\ufeffx = 1\n")
        assert r.exit_code == 1
        assert "invalid non-printable character U+FEFF" in r.stderr
        assert classify("python", r.stderr) == "syntax"
        assert locate("python", r.stderr) == 1, "preamble 偏移必须折回来"

    def test_content_parser_tolerates_a_utf8_bom(self, content_dir):
        """口径差异登记：内容解析器**容忍** BOM，学生代码前端**拒绝** BOM。"""
        topics, diags = content_dir({"bom.yaml": ("﻿" + GOOD_YAML).encode("utf-8")})
        assert diags == []
        ids = _loaded_ids(topics)
        assert ids == ["python/t1/bom"]
        prob = [p for t in topics for p in t.problems][0]
        assert prob.title == "正常题"


# ---------------------------------------------------------------------------
# 3) 语法错：行列定位（卷宗主判据）
# ---------------------------------------------------------------------------

class TestSyntaxErrorLocation:
    def test_multiline_error_locates_the_editor_line(self, runner):
        """行：解释器报 `main.py, line 9`，学生编辑器里其实是第 3 行。"""
        r = runner.run("a = 1\nb = 2\nprint(\n")
        assert r.exit_code == 1
        assert "'(' was never closed" in r.stderr
        assert classify("python", r.stderr) == "syntax"
        assert locate("python", r.stderr) == 3
        # 反向对照：不折算的原始行号确实是 9（证明 3 不是"恰好等于行数"的巧合）
        assert "line 9" in r.stderr

    def test_column_now_located_for_python_d12_fixed(self, runner):
        """**D-12 已修（l927-02，2026-09-30）**：解释器 caret 行里的列不再被丢掉。
        原钉（本文件旧版）钉的是缺陷实况 `locate_column("python", …) is None`；
        修法落地后本钉翻转为修复钉，cpp 对照原样保留。列号口径＝去缩进显示行
        （CPython 3.12 打印即去缩进，4 空格打印前缀），详见 error_feedback docstring。
        """
        r = runner.run("a = 1\nb = 2\nprint(\n")
        caret = [ln for ln in r.stderr.splitlines() if set(ln.strip()) == {"^"}]
        assert caret, "解释器本身是给了列位置的"
        assert caret[0].index("^") > 0
        assert locate_column("python", r.stderr) == caret[0].index("^") - 3
        assert locate_column("cpp", "main.cpp(3:6): error: expected ';'") == 6  # 对照：cpp 有列

    def test_undefined_name_and_syntax_land_in_different_classes(self, runner):
        """分类链有牙：同一套 `classify` 下 NameError ≠ SyntaxError。"""
        nm = runner.run("x = 1\nprint(yyy)\n")
        assert classify("python", nm.stderr) == "undefined_name"
        assert locate("python", nm.stderr) == 2
        sx = runner.run("x = 1\nif True\n    print(x)\n")
        assert classify("python", sx.stderr) == "syntax"
        assert locate("python", sx.stderr) == 2

    def test_no_bad_input_kills_the_host_process(self, runner, tmp_path):
        """卷宗「不会使服务进程退出」：一批坏输入逐个返回，宿主继续活着。"""
        bad_inputs = [
            "\ufeffx = 1", "x = (", "① = 1", "x\u200b = 1", "print 'py2'",
            "def f(:)", "x = " + "(" * 5000 + ")" * 5000, "import \n",
            "@", "x = *", "lambda", "class", "\x00", "x = 1\x0c",
        ]
        for code in bad_inputs:
            r = runner.run(code)
            assert isinstance(r.exit_code, int) and not r.timed_out, repr(code)
            assert r.elapsed_ms >= 0
        marker = tmp_path / "host-alive.txt"
        marker.write_text("alive", encoding="utf-8")   # 走到这里就说明没被解释器带下水
        assert marker.read_text(encoding="utf-8") == "alive"


# ---------------------------------------------------------------------------
# 4) 超大输入
# ---------------------------------------------------------------------------

class TestHugeInput:
    def test_deeply_nested_parentheses_give_a_located_syntax_error(self, runner):
        r = runner.run("x = " + "(" * 5000 + ")" * 5000 + "\n")
        assert r.exit_code == 1
        assert "too many nested parentheses" in r.stderr
        assert classify("python", r.stderr) == "syntax"
        assert locate("python", r.stderr) == 1

    def test_huge_source_keeps_the_verdict_after_headtail_truncation(self, runner):  # l1028-05 翻钉：D-11 已修复
        """**缺陷 D-11**（本单最有牙的一条）：CPython 把"错在哪"放在 stderr **末尾**，
        而 `_truncate` 从**尾部**切 100 KB ⇒ 超长源码行会把结论整条切掉，
        学生只剩「输出过长，已截断」。
        """
        r = runner.run("x = " + "(" * 200_000 + ")" * 200_000 + "\n")
        assert r.exit_code == 1
        assert TRUNC_MARK in r.stderr
        assert len(r.stderr.encode("utf-8")) <= MAX_STDERR_BYTES + 60
        assert "SyntaxError" in r.stderr, "头尾保留后错误结论必须在 stderr 可见（D-11 修复验收，l1028-05 翻钉）"
        assert "TypeError" in r.stderr or "parenthesis" in r.stderr or "x = " in r.stderr, "截断保留的是可读内容而非空壳"
        assert r.stderr.count(TRUNC_MARK) == 1

    def test_content_parser_has_no_input_size_guard(self, content_dir):
        """**缺陷 D-9**：内容解析器**没有体积上限**（runner 侧反而有 1 MB 字节限额）。

        正向对照＝真的读进来了（不是"文件没被看见"）；负向＝约 30 万键的 yaml
        照样解析成功、零诊断 ⇒ 一个坏投料的大文件就能拖慢整页渲染。
        """
        big = "".join("k%06d: %s\n" % (i, "v" * 6) for i in range(20_000))
        assert len(big.encode("utf-8")) > 300_000
        t0 = time.time()
        topics, diags = content_dir({"big.yaml": big, GOOD_YAML_NAME: GOOD_YAML})
        spent = time.time() - t0
        assert diags == [] and spent < 20
        assert "python/t1/big" in _loaded_ids(topics)
        guards = [m for m in ("MAX_BYTES", "st_size", "getsize", "seek(", "size >")
                  if m in (REPO / "core" / "loader.py").read_text(encoding="utf-8")]
        assert guards == [], "限额出现了？请同步撤销本钉子：%r" % guards

    def test_oversized_stdin_still_parses_line_by_line(self, runner):
        """超大输入的**可读**面：1 MB 内的一行超长文本，学生代码自己 `splitlines` 不炸宿主。"""
        payload = ("x" * 200_000 + "\n") * 3
        r = runner.run("import sys\nlines = sys.stdin.read().splitlines()\n"
                       "print(len(lines), max(len(l) for l in lines))", stdin=payload)
        assert r.exit_code == 0
        assert r.stdout.strip() == "3 200000"


# ---------------------------------------------------------------------------
# 5) Unicode 标识符
# ---------------------------------------------------------------------------

class TestUnicodeIdentifiers:
    def test_cjk_and_accented_identifiers_run(self, runner):
        for code in ("变量 = 7\nprint(变量)\n", "café = 2\nprint(café * 3)\n",
                     "Ω = '欧米伽'\nprint(Ω)\n"):
            r = runner.run(code)
            assert r.exit_code == 0, code
            assert r.stdout.strip() != ""

    @pytest.mark.parametrize("label,code,frag", [
        ("zero-width-space", "x\u200b = 1\n", "invalid non-printable character U+200B"),
        ("circled-digit", "① = 1\n", "invalid character"),
        ("astral-emoji", "\U0001f600x = 1\n", "invalid character"),
        ("fullwidth-comma", "a＝1\n", "invalid character"),
    ])
    def test_invalid_unicode_identifiers_are_located_syntax_errors(self, runner, label,
                                                                    code, frag):
        r = runner.run(code)
        assert r.exit_code == 1, label
        assert frag in r.stderr, label
        assert classify("python", r.stderr) == "syntax", label
        assert locate("python", r.stderr) == 1, label

    def test_homoglyph_top_level_key_falls_back_without_warning(self, content_dir):
        """**缺陷 D-10**：顶层键写成同形异码（`titlе` 的 е 是 U+0435）
        ⇒ 内容解析器**既不报错也不告警**，`title` 静默回退成文件名。
        """
        topics, diags = content_dir({"homoglyph.yaml": "titlе: 西里尔 е\nstatement: 有题面\n"})
        assert diags == []
        prob = [p for t in topics for p in t.problems][0]
        assert prob.title == "homoglyph"          # 回退：不是"西里尔 е"
        assert prob.statement == "有题面"          # 正向对照：认识的键照样读到了

    def test_unicode_and_emoji_file_names_keep_stable_ids(self, content_dir):
        topics, diags = content_dir({"变量_测试.yaml": "title: 中文标题\n",
                                     "emoji_\U0001f3af.yaml": "title: emoji\n"})
        assert diags == []
        ids = sorted(p.id for t in topics for p in t.problems)
        assert ids == ["python/t1/emoji_\U0001f3af", "python/t1/变量_测试"]

    def test_yaml_directive_and_encoding_header_lines_are_accepted(self, content_dir):
        """YAML 世界的"编码声明"＝`%YAML`/`%TAG` 指令行：实况为**容忍不报错**。"""
        topics, diags = content_dir({"dir1.yaml": "%YAML 1.1\n---\ntitle: 指令\n",
                                     "dir2.yaml": "%TAG ! tag:example.com,2024:\n---\ntitle: 标签\n"})
        assert diags == []
        assert sorted(_loaded_ids(topics)) == ["python/t1/dir1", "python/t1/dir2"]

    def test_recursive_anchor_loads_and_bites_only_later(self, content_dir):
        """**缺陷 D-8**：递归锚点 `&x [1, *x]` 在**加载期**完全合法（自引用对象进内存），
        要等到序列化/深拷贝才炸 ⇒ 爆炸点与坏文件已经分离，诊断里查不到。
        """
        topics, diags = content_dir({"rec.yaml": "title: 递归\nid: &x [1]\n"})
        assert diags == [] and "python/t1/rec" in _loaded_ids(topics)
        raw = yaml.safe_load("a: &x [1, *x]\n")
        assert raw["a"][1] is raw["a"], "safe_load 不做递归防护（对象确实自引用）"
        with pytest.raises((RecursionError, ValueError)):
            json.dumps(raw)
