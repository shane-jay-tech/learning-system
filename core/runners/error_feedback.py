# -*- coding: utf-8 -*-
"""执行器错误 → 学生可读的**行级**反馈（单一映射源，四语言共用）。

为什么需要这一层（本单在 HEAD `ea18caf` 实测的三处自相矛盾，全部可复算）：

1. **同一个错误两个行号**：`python_runner` 在学生代码前拼了一段 preamble，
   于是编辑器里第 3 行的 `NameError` 在 stderr 里写作 `line 9`。学生照着 stderr 找第 9 行，
   自己的代码只有 3 行 ⇒ 反馈与代码互相矛盾。
2. **提示口径分叉**：SQL 与 C++ 各自维护一张「英文报错 → 中文提示」表，
   SQL 侧带 `re.IGNORECASE`、C++ 侧大小写敏感；Python 与 R 则**根本没有表**——
   同一类"标识符拼错"的错误，四语言里两种待遇。
3. **超时话术分叉**：同一个 timeout 在四处分别写作「代码运行超过 5 秒，已强制终止…」
   「R 脚本运行超过 5 秒。」「编译超时（>7 秒）。」「程序运行超时。」——最后一句连预算几秒都没说。

⇒ 本模块只负责**把错误映射成人看得懂的行级反馈**：分类、行号折算、统一话术。
  🔴 **不改判题结论**：不碰 `ok` / `passed` / `exit_code` / `error_kind`，
     也不改写 runner 的 `stderr`——**原始诊断仍逐字可追溯**（本模块只读它）。
"""
import re
from typing import Optional

# ---------------------------------------------------------------------------
# 1) 行号折算：preamble 的**单一来源**（长度算出来，绝不写死数字）
# ---------------------------------------------------------------------------

#: 注入到学生代码之前的引导段。`python_runner` 写文件用的就是这一个常量，
#: 因此 `PREAMBLE_LINES` 与学生可见行号的偏移量永远同步——改 preamble 不会把折算打歪。
PREAMBLE = (
    "import sys\n"
    "try:\n"
    "    sys.stdout.reconfigure(encoding='utf-8')\n"
    "    sys.stderr.reconfigure(encoding='utf-8')\n"
    "except Exception:\n"
    "    pass\n"
)

#: preamble 占多少行 = 学生代码在 main.py 里的整体下移量
PREAMBLE_LINES = len(PREAMBLE.splitlines())

#: 跑在"学生代码"视角下的语言（agent_dev 复用 PythonRunner，见 core/judge._RUNNERS）
_PY_LIKE = ("python", "agent_dev")
_STUDENT_LANGS = _PY_LIKE


def to_editor_line(lang: str, reported_line: int) -> int:
    """把解释器报的行号折回学生编辑器里的行号。"""
    if lang in _STUDENT_LANGS:
        return max(1, reported_line - PREAMBLE_LINES)
    return reported_line


# ---------------------------------------------------------------------------
# 2) 错误分类：同一个 stderr 在四语言里必须落到同一个类（矛盾面的根因就在这里）
# ---------------------------------------------------------------------------

#: 学生可见的错误类（稳定词表；新增须同时给 headline）
KINDS = (
    "toolchain",       # 编译器/解释器不在位——不是学生的错
    "policy",          # 被沙箱/授权规则拒绝（公开部署、非 SELECT、setup 白名单）
    "timeout",         # 超时
    "syntax",          # 语法错（编译期或解析期）
    "undefined_name",  # 标识符未定义/未声明/找不到
    "type",            # 类型不匹配
    "runtime",         # 其它运行期错误
    "none",            # 没有错误
)

_HEADLINE = {
    "toolchain": "本机缺少运行环境",
    "policy": "写法被规则拦下",
    "timeout": "运行超时",
    "syntax": "语法错误",
    "undefined_name": "名字找不到",
    "type": "类型不匹配",
    "runtime": "运行出错",
    "none": "",
}

# 顺序敏感：先具体后泛化。四语言共用同一张表 ⇒ 同串必同类。
_CLASSIFY_RULES = (
    ("toolchain", r"未检测到 (g\+\+|Rscript)|编译器启动失败"),
    ("policy", r"公开部署模式|不允许执行学生代码|只允许查询|只支持一条 SQL 语句|"
               r"setup_sql 含不允许的语句|not authorized"),
    ("timeout", r"超时|超过 \d+ 秒|interrupt"),
    ("undefined_name", r"NameError|is not defined|was not declared in this scope|"
                       r"undeclared|could not find function|no such table|no such column|"
                       r"UnboundLocalError"),
    ("type", r"TypeError|no match for 'operator|mismatched types|cannot be applied"),
    ("syntax", r"SyntaxError|syntax error|expected ';'|expected '\}'|解析|invalid token"),
)
_COMPILED_RULES = tuple((kind, re.compile(pat, re.IGNORECASE)) for kind, pat in _CLASSIFY_RULES)

_TIMEOUT_RE = re.compile(r"超过 (\d+) 秒|>\s*(\d+) 秒")


def classify(lang: str, stderr: str, timed_out: bool = False) -> str:
    """stderr（＋超时标志）→ 错误类。四语言走同一条规则链，故不会互相矛盾。"""
    text = stderr or ""
    if timed_out:
        return "timeout"
    for kind, rx in _COMPILED_RULES:
        if rx.search(text):
            return kind
    return "runtime" if text.strip() else "none"


def headline(kind: str) -> str:
    return _HEADLINE.get(kind, "")


# ---------------------------------------------------------------------------
# 3) 行级定位：从各语言的原始诊断里抽"第几行"，统一折算回编辑器行号
# ---------------------------------------------------------------------------

_PY_FILE_LINE_RE = re.compile(r'File "[^"]*main\.(?:py|R)", line (\d+)')
_PY_ANY_LINE_RE = re.compile(r'File "[^"]*main\.py", line (\d+)')
#: 帧头（不带行号捕获，取**位置**用）：caret 必须锚定"最后一个 main.py 帧"——
#: 库帧会排在学生帧之后（3.11+ 每帧都带 caret），取"最后一个 caret 块"会指到库帧头上。
_PY_FRAME_RE = re.compile(r'File "[^"]*main\.(?:py|R)"')
#: caret 标记行：只有空白与 ^/~（`~~~~^~~~~` 形态也算），3.12 会把 `~` 画在非错误端上
_PY_CARET_LINE_RE = re.compile(r"[ \t]*[\^~]+")
_CPP_RE = re.compile(r"main\.cpp\((\d+)(?::(\d+))?\)\s*:\s*(?:fatal\s+)?(?:error|warning)")
_CPP_COLON_RE = re.compile(r"main\.cpp:(\d+)(?::(\d+))?\s*:\s*(?:fatal\s+)?(?:error|warning)")
_R_LINE_RE = re.compile(r"at\s+#?(\d+)\s*[:|]|line\s+(\d+)\b|main\.R\((\d+)\)")
#: R ≥ 4.3 解析错报文自带 `行:列:`（如 `Error: main.R:2:7: unexpected symbol`）。
#: 只在含 "Error" 的行上找，防把学生自己打印的时间戳（12:30: …）当成坐标。
_R_LINE_COL_RE = re.compile(r"(?<!\d)(\d+):(\d+):(?=\s)")
_SQL_NEAR_RE = re.compile(r'near "([^"]*)"')


def locate(lang: str, stderr: str) -> Optional[int]:
    """返回**学生编辑器里**的行号；抽不到就返回 None（绝不瞎猜一个行号给学生）。"""
    text = stderr or ""
    if lang in _STUDENT_LANGS:
        hits = _PY_FILE_LINE_RE.findall(text) or _PY_ANY_LINE_RE.findall(text)
        if hits:
            # 最后一个指向 main.py 的帧才是学生自己那行（前面的帧是调用栈）
            return to_editor_line(lang, int(hits[-1]))
        return None
    if lang == "cpp":
        for rx in (_CPP_RE, _CPP_COLON_RE):
            m = rx.search(text)
            if m:
                return int(m.group(1))
        return None
    if lang == "r":
        for m in _R_LINE_RE.finditer(text):
            for g in m.groups():
                if g and g.isdigit():
                    return int(g)
        return None
    return None  # sql 跑的是内存里的一条语句，没有"第几行"可言


def _py_caret_column(stderr: str) -> Optional[int]:
    """从 CPython 诊断里抽 caret 列：锚定最后一个 main.py 帧，取其后**本帧段**内首个 caret 行。

    列号口径＝CPython 3.12 把源码行**去缩进**后打印（4 空格打印前缀），
    故这里给出的是"去缩进显示行"上的列——与解释器自己画的 caret 同一口径。
    学生行首有缩进时，编辑器里的绝对列还要加上缩进宽（stderr 里无从得知，如实缺省）。
    """
    frames = list(_PY_FRAME_RE.finditer(stderr))
    if not frames:
        return None
    start = frames[-1].end()
    nxt = stderr.find('File "', start)
    segment = stderr[start: nxt] if nxt != -1 else stderr[start:]
    for line in segment.splitlines():
        m = _PY_CARET_LINE_RE.match(line)
        if m and set(line.strip()) <= {"^", "~"}:
            idx = len(m.group(0)) - len(m.group(0).lstrip(" \t"))  # 首个 ^/~ 的下标
            if idx >= 4:  # 前缀 4 空格是打印产物；caret 不该落在前缀里
                return idx - 3
            return None
    return None


def locate_column(lang: str, stderr: str) -> Optional[int]:
    """返回**学生代码里**的列号；抽不到返回 None（宁缺勿错，绝不瞎猜）。

    - cpp：g++ 报文 `main.cpp(行:列)`／`main.cpp:行:列:`。
    - python/agent_dev：CPython 3.11+ 的 caret 标记行（含 `~~~^~~~` 形态），
      列号相对去缩进显示行（见 `_py_caret_column`）。
    - r：R ≥ 4.3 解析错报文自带 `行:列:`；运行期错误不带位置 ⇒ None。
      （本机暂无 Rscript，形态按 R 4.3 报文钉合成用例；工具链在位窗复测。）
    - sql：SQLite 报文不带任何位置信息 ⇒ 恒 None（实测契约，不是缺口）。
    """
    text = stderr or ""
    if lang == "cpp":
        for rx in (_CPP_RE, _CPP_COLON_RE):
            m = rx.search(text)
            if m and m.group(2):
                return int(m.group(2))
        return None
    if lang in _STUDENT_LANGS:
        return _py_caret_column(text)
    if lang == "r":
        for line in text.splitlines():
            if "Error" in line:
                m = _R_LINE_COL_RE.search(line)
                if m:
                    return int(m.group(2))
        return None
    return None  # sql：SQLite 报文不带位置信息，见 docstring


def where_phrase(lang: str, stderr: str) -> str:
    """行级前缀，如「第 3 行：」；定位不到返回空串（宁缺勿错）。"""
    ln = locate(lang, stderr)
    if ln is None:
        return ""
    col = locate_column(lang, stderr)
    return f"第 {ln} 行" + (f"第 {col} 列：" if col else "：")


# ---------------------------------------------------------------------------
# 4) 中文提示表：四语言共用一张，匹配口径统一为大小写不敏感
# ---------------------------------------------------------------------------

#: (正则, 提示模板, 生效语言)；`langs=None` 表示四语言通用。模板用 {0}/{1} 引用捕获组。
#: SQL/C++ 两段沿用**原文案**，以免改变 stderr 既有内容（有测试逐字钉着「中文提示」形态）；
#: 分语言限定是必要的——SQL 的 `near "X"` 也会命中 R 的 "unexpected symbol near ')'"，
#: 不限定就会让共用表把原表的语义搅浑。
HINTS = (
    # —— 原 _SQL_FRIENDLY_HINTS，文案逐字保留 ——
    (r"no such table: (\S+)", "表「{0}」不存在——检查表名拼写（题目 setup 建了哪些表？）", ("sql",)),
    (r"no such column: (\S+)", "列「{0}」不存在——检查字段名拼写。", ("sql",)),
    (r"no such function: (\S+)", "函数「{0}」不存在——SQLite 内置函数有限，检查拼写。", ("sql",)),
    (r'near "(\S+)"', "「{0}」附近有语法错误——检查关键字、逗号与括号。", ("sql",)),
    (r"syntax error", "语法错误——检查关键字、逗号与括号是否配对。", ("sql",)),
    (r"ambiguous column name", "列名有歧义——多表查询时给列名加表名前缀（如 t.id）。", ("sql",)),
    # —— 原 _CPP_FRIENDLY_HINTS，文案逐字保留 ——
    (r"error: expected ';'", "漏了分号 ;（看报错指出的行）", ("cpp",)),
    (r"error: expected '}'", "少了一个 }（检查大括号配对）", ("cpp",)),
    (r"error: '(\w+)' was not declared in this scope", "「{0}」未定义——检查拼写与作用域", ("cpp",)),
    (r"undefined reference", "函数只有声明没有定义（或没把对应源文件一起编译）", ("cpp",)),
    (r"error: no match for 'operator", "运算符不匹配——检查操作数类型", ("cpp",)),
    (r"error: '([^']+)' undeclared", "「{0}」未声明——是否漏了头文件 #include？", ("cpp",)),
    # —— 本单新增：Python / R 此前**完全没有**中文兜底，同一类错误两种待遇 ——
    (r"NameError: name '(\w+)' is not defined", "「{0}」还没赋值就用——检查拼写，或是否漏了上面的赋值行", _PY_LIKE),
    (r"NameError", "名字未定义——检查拼写与是否先赋值", _PY_LIKE),
    (r"UnboundLocalError: local variable '(\w+)'", "「{0}」在赋值前就被读了——函数里先用后赋", _PY_LIKE),
    (r"SyntaxError: invalid syntax", "这一行语法不合法——常见于漏冒号 :、括号不配对、中文标点", _PY_LIKE),
    (r"IndentationError", "缩进不对齐——Python 用 4 个空格缩进，别混用 Tab", _PY_LIKE),
    (r"TypeError: unsupported operand", "两个类型不能这样运算——检查是数字还是字符串", _PY_LIKE),
    (r"IndexError", "下标越界——序列没有这么长，先看 len()", _PY_LIKE),
    (r"KeyError: '?([^,\n']+)'?", "键「{0}」不在字典/DataFrame 列里——先确认列名拼写", _PY_LIKE),
    (r"ZeroDivisionError", "除数是 0——检查分母来源", _PY_LIKE),
    (r"ModuleNotFoundError: No module named '([\w.]+)'", "本机没有「{0}」这个库——题目不要求它，检查拼写", _PY_LIKE),
    (r"could not find function \"([^\"]+)\"", "R 里找不到函数「{0}」——检查拼写，或是否漏了 library()", ("r",)),
    (r"object '([^']+)' not found", "R 里找不到对象「{0}」——检查拼写与是否先赋值", ("r",)),
    (r"non-numeric argument", "R 要的是数值，传进了非数值——先看该列是什么类型", ("r",)),
)
_COMPILED_HINTS = tuple((re.compile(p, re.IGNORECASE), t, langs) for p, t, langs in HINTS)

_HINT_SEP = "\n\n💡 中文提示："


def _match_hint(lang: str, stderr: str):
    text = stderr or ""
    for rx, tmpl, langs in _COMPILED_HINTS:
        if langs and lang not in langs:
            continue
        m = rx.search(text)
        if m:
            try:
                return tmpl.format(*m.groups()) if m.groups() else tmpl
            except (IndexError, KeyError):  # 模板与捕获组不匹配时宁可不出提示
                continue
    return ""


def friendly_hint(lang: str, stderr: str) -> str:
    """按共用表给原始诊断附一句中文提示；**不命中则原样返回**（不编造提示）。"""
    text = stderr or ""
    hint = _match_hint(lang, text)
    return text + _HINT_SEP + hint if hint else text


def hint_only(lang: str, stderr: str) -> str:
    """只要提示那一句（给 diff_hint 用，避免把整段 stderr 再抄一遍）。"""
    return _match_hint(lang, stderr or "")


# ---------------------------------------------------------------------------
# 5) 超时话术：一处定义，四语言共用；预算秒数必上屏幕
# ---------------------------------------------------------------------------

def timeout_budget(stderr: str) -> Optional[int]:
    """从既有 stderr 里读回真实预算秒数（读不到返回 None，不瞎报一个数）。"""
    m = _TIMEOUT_RE.search(stderr or "")
    if not m:
        return None
    return int(next(g for g in m.groups() if g))


def timeout_message(what: str, seconds, note: str = "") -> str:
    """统一超时文案：`<主语>超时（超过 N 秒）[，note]。`

    `what="编译"` 时输出恰为「编译超时（超过 7 秒）。」——与既有文案同形态，
    既有测试钉的是「编译超时」这个子串，仍成立。
    """
    body = f"{what}超时（超过 {seconds} 秒）"
    return f"{body}，{note}。" if note else f"{body}。"


# ---------------------------------------------------------------------------
# 6) 面向学生的一行反馈（judge 的 diff_hint 用这个）
# ---------------------------------------------------------------------------

def feedback(lang: str, stderr: str, timed_out: bool = False) -> str:
    """把一段原始诊断映射成「第 N 行：<类>——<提示>」形态的单行反馈。

    定位不到行号时不写行号；抽不到提示时只给类名。**永不返回空串之外的假信息**。
    """
    kind = classify(lang, stderr, timed_out=timed_out)
    if kind == "none":
        return ""
    head = headline(kind)
    if kind == "timeout":
        budget = timeout_budget(stderr)
        head = "运行超时" + (f"（超过 {budget} 秒）" if budget is not None else "")
    where = where_phrase(lang, stderr)
    hint = hint_only(lang, stderr)
    msg = head
    if hint:
        msg = f"{msg}——{hint}" if not hint.startswith(head) else hint
    return (where + msg) if where else msg
