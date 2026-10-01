# -*- coding: utf-8 -*-
"""报告下载区两个 `st.download_button`（.md / .html）的**行为面**补测（l924-02）。

锚点（开工前实测，2026-09-24 磁盘实况）：
- `ui/pages/dashboard.py:262` 下载 .md 口（:264 data=last_report_md、:265 file_name、:266 mime）
- `ui/pages/dashboard.py:270` 下载 .html 口（:272 data=last_report_html、:273 file_name、:276 help）
- l923-11 遗留：两口的**按钮文案与 help 参数在全仓零覆盖**（开工前复现该锚点的关键词检索 → 0 命中）。

本档按 l923-11 建议的「单源常量 + 行为断言」路线走，**一个字的界面文案都不抄**：
- 期别段调生产函数 `dashboard_page._report_file_tag(days)` 现推，不写死 week/month；
- 「哪个口是 md、哪个口是 html」由**自家产物自证**（data 能否被 HTMLParser 解析成闭合文档）定类，
  再回头要求 file_name 后缀 / mime / 按钮标签与自证的类别一致
  ⇒ 把两口的 data 对调、把标签对调、把后缀写错，都会转红；
- 报告正文用**真实** `report_to_markdown` / `report_to_html` 渲染（只桩 `generate_report` 供数据），
  所以「data 可解析」是在真产物上断言，不是在桩字符串上自娱；
- 同一帧两口必须出自**同一期同一份**报告：往 report 里塞期别标记 `tok<days>d`，
  md 与 html 两路产物都得带上它。

🔴 桩的失明面（不改基类，改法同 test_dashboard_report_persistence 的实例级覆盖）：
`tests/test_ui_behavior.py::FakeStreamlit` 的 `button` / `expander` / `tabs` 三处**不留入参**
（button 只回布尔、expander 只给上下文管理器、tabs 只回上下文列表），实测 `columns` 同样只回上下文
列表且不写 calls ——共**四处**失明；靠基类断言「某标签/某参数存在」必然永绿。
`_fake()` 在实例上挂录制版覆盖这四个口（`__getattr__` 只在常规属性查找失败时触发，实例属性优先）。
`download_button` 基类本就录 `(name, args, kwargs)`，是本档能取 data/file_name/mime/help 的前提。

只加测试，不改 ui/pages/dashboard.py。可复跑：
python -m pytest tests/test_report_download_buttons.py -q
"""
from datetime import date
from html.parser import HTMLParser

import pytest

import app  # noqa: F401  # 与既有 dashboard 桩同模式：app 侧 import 预绑定 st
import ui.components as components
import ui.pages.dashboard as dashboard_page
from core.report import CALIBER_NOTE, report_to_html, report_to_markdown
from tests.test_dashboard_page_render import DashboardFakeStreamlit, _dao
from tests.test_report_markdown_contract import _report
from tests.test_ui_behavior import Context

# HTML 里的空元素：闭合体检时不该入栈
_VOID_TAGS = {"meta", "br", "hr", "img", "input", "link"}


# ---------------------------------------------------------------------------
# 假件与接线
# ---------------------------------------------------------------------------

def _fake():
    """DashboardFakeStreamlit + button/expander/tabs 的实例级入参录制（绕开基类失明面）。"""
    fake = DashboardFakeStreamlit()

    def make(name):
        def call(*a, **kw):
            fake.calls.append((name, a, kw))
            if name == "button":
                return fake.buttons.get(a[0] if a else kw.get("label"), False)
            if name == "tabs":
                return [Context() for _ in (a[0] if a else kw.get("labels", []))]
            if name == "columns":
                spec = a[0] if a else kw.get("spec")
                return [Context() for _ in range(spec if isinstance(spec, int) else len(spec))]
            return Context()
        return call

    # 基类这四处都不留入参：button 只回布尔、expander 只给上下文管理器、
    # tabs 只回上下文列表、columns 只回上下文列表且**不写 calls**——列槽参数无从断言。
    for name in ("button", "expander", "tabs", "columns"):
        setattr(fake, name, make(name))
    return fake


def _wire(monkeypatch, fake, buttons=None):
    """打桩 dashboard 的重依赖；**只桩数据源 generate_report**，两条渲染函数用生产实现。

    返回 list 是 generate_report 实际收到的 days 序列（按调用顺序），同一 fake 多次接线共用一条流水。
    """
    fake.buttons = dict(buttons or {})  # 显式覆盖：空 dict 表示本轮一个按钮都不点
    monkeypatch.setattr(dashboard_page, "st", fake)
    monkeypatch.setattr(components, "st", fake)
    monkeypatch.setattr(dashboard_page, "ProgressDAO", lambda: _dao())
    monkeypatch.setattr(dashboard_page, "check_achievements", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_progress_summary", lambda dao: {"earned": 2, "total": 22})
    monkeypatch.setattr(dashboard_page, "get_all_with_state", lambda dao: [])
    monkeypatch.setattr(dashboard_page, "get_achievement", lambda aid: {"name": f"成就{aid}"})
    monkeypatch.setattr(dashboard_page, "recommend", lambda n=5, dao=None: [])
    monkeypatch.setattr(dashboard_page, "cross_recommend", lambda *a, **kw: [])
    import core.loader as _loader
    monkeypatch.setattr(_loader, "load_language", lambda lang: [])

    seen = getattr(fake, "_seen", None)
    if seen is None:
        seen = []
        fake._seen = seen
    monkeypatch.setattr(
        dashboard_page, "generate_report",
        lambda dao, days=7: seen.append(days) or _report_for(days))
    return seen


def _report_for(days):
    """真实报告字典（复用 test_report_markdown_contract 的构造单源），只把期别标记编进 weak_topics。"""
    return _report(period_days=days, weak_topics=[(f"tok{days}d", 1.0)])


def _caliber_index(fake):
    """报告区起点：面板口径 caption（引 CALIBER_NOTE 单源，不抄文案）。"""
    for i, c in enumerate(fake.calls):
        if c[0] == "caption" and c[1] and c[1][0] == CALIBER_NOTE:
            return i
    raise AssertionError("报告导出区的 caption（CALIBER_NOTE 单源）没渲染到——下面的断言会全部失据")


def _generator_buttons(fake):
    """报告区的「生成」入口：CALIBER caption 之后、下一个 download_button 之前出现的 st.button。

    按**渲染顺序**定位，不抄按钮文案 ⇒ 改措辞不会让本档找不到入口，而入口增减会立刻改变数量。
    """
    out = []
    for c in fake.calls[_caliber_index(fake) + 1:]:
        if c[0] == "download_button":
            break
        if c[0] == "button":
            out.append(c)
    return out


def _report_downloads(fake):
    """只筛报告区的下载口：按**自家文件名的后缀**认，学习数据区的 .json 口自动出局。"""
    return [c for c in fake.calls
            if c[0] == "download_button" and _ext(c[2].get("file_name")) in ("md", "html")]


def _buttons_of(fake):
    """把下载口摊成可读记录（label 是位置参，余下全是关键字参）。"""
    return [{"label": str(c[1][0]), "data": c[2].get("data"), "file_name": str(c[2].get("file_name")),
             "mime": c[2].get("mime"), "help": c[2].get("help"), "kw": c[2]} for c in _report_downloads(fake)]


def _ext(file_name):
    return str(file_name or "").rsplit(".", 1)[-1].lower()


def _generate(monkeypatch, click, rerender=False):
    """两帧法复现真实交互：第一帧只盘点入口，第二帧只按下其中一个生成口。

    返回 (fake, seen, 按钮记录列表)；rerender=True 时再来一帧「谁都不点」，
    对应「下载区靠 session_state 常驻」这条真实路径。
    """
    fake = _fake()
    seen = _wire(monkeypatch, fake)
    dao = _dao()
    dashboard_page._render_dashboard_body(dao)
    labels = [c[1][0] for c in _generator_buttons(fake)]
    assert len(labels) == 2, f"报告区应有且只有 2 个生成入口，实得 {len(labels)}：{labels}"

    fake.calls.clear()
    _wire(monkeypatch, fake, {labels[click]: True})
    dashboard_page._render_dashboard_body(dao)
    if rerender:
        fake.calls.clear()
        _wire(monkeypatch, fake, {})
        dashboard_page._render_dashboard_body(dao)
    return fake, seen, _buttons_of(fake)


# ---------------------------------------------------------------------------
# 产物的自证：HTML 解析 / Markdown 表格结构
# ---------------------------------------------------------------------------

class _HtmlDoc(HTMLParser):
    """极简但严格的 HTML 体检器：声明、标签闭合、可见文本。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.decls, self.opened, self.problems = [], [], []
        self.stack, self._skip = [], 0
        self.text = []

    def handle_decl(self, decl):
        self.decls.append(str(decl))

    def handle_starttag(self, tag, attrs):
        self.opened.append(tag)
        if tag in ("script", "style"):
            self._skip += 1
        if tag not in _VOID_TAGS:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = max(0, self._skip - 1)
        if tag in _VOID_TAGS:
            return
        if not self.stack or self.stack[-1] != tag:
            self.problems.append(f"</{tag}> 处闭合失配（栈顶 {self.stack[-1:] or '空'}）")
            return
        self.stack.pop()

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.text.append(data.strip())

    @property
    def ok(self):
        return bool(self.decls) and "html" in self.opened and not self.problems and not self.stack


def _parse_html(text):
    doc = _HtmlDoc()
    doc.feed(str(text))
    doc.close()
    return doc


def _md_table_blocks(md):
    """把 markdown 里的表格切成连续块（行首是 `|` 的相邻行）。"""
    blocks, cur = [], []
    for line in str(md).split("\n"):
        if line.strip().startswith("|"):
            cur.append(line.strip())
        elif cur:
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    return blocks


def _is_delimiter_row(line):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return bool(cells) and all(set(c) <= set(":-") and "-" in c for c in cells)


# ---------------------------------------------------------------------------
# 例 1～2：下载区的出现条件（点了才有产物，产物才有出口）
# ---------------------------------------------------------------------------

def test_未生成报告时一个下载口都不许出现(monkeypatch):
    """行为面前件：session_state 无产物 ⇒ 报告下载区整段不存在。

    对照组（报告区确实渲染到了）由 CALIBER caption 与两个生成入口把守——
    否则「空集」可能只是整段没跑出来的假绿。
    """
    fake = _fake()
    _wire(monkeypatch, fake)
    dashboard_page._render_dashboard_body(_dao())
    assert _caliber_index(fake) >= 0
    assert len(_generator_buttons(fake)) == 2
    assert _report_downloads(fake) == [], "没生成过报告却已经摆出下载按钮"
    assert "last_report_md" not in fake.session_state


def test_按下生成口后同帧出现两个下载口并写入产物(monkeypatch):
    """点击的可观察后果：generate_report 收到 days、session 三键落定、两口气同时出现。"""
    fake, seen, btns = _generate(monkeypatch, click=0)
    assert len(seen) == 1, f"一次点击应只生成一份报告，实为 {seen}"
    days = fake.session_state["last_report_days"]
    assert seen == [days], "生成入参应与落进 session 的期别一致"
    assert fake.session_state["last_report_md"] == report_to_markdown(_report_for(days))
    assert fake.session_state["last_report_html"] == report_to_html(_report_for(days))
    assert len(btns) == 2, f"应同时出现 .md 与 .html 两个下载口，实得 {len(btns)}"
    assert all(b["data"] for b in btns), f"下载口不许挂空 data：{[(b['file_name'], b['data']) for b in btns]}"


# ---------------------------------------------------------------------------
# 例 3～5：两口的产物自证——格式、文件名、mime、标签四者互相对齐
# ---------------------------------------------------------------------------

def test_两个下载口按各自产物定类后文件名后缀与mime与标签全对齐(monkeypatch):
    """"谁是 md、谁是 html"由 data 自证（能否解析成闭合 HTML），再回头核对三件事。

    对调 data、对调标签、写错后缀、mime 挂错——任一种都会在这里转红，
    而本例一个字面文案都没抄。
    """
    _fake_report, _seen, btns = _generate(monkeypatch, click=0)
    assert len(btns) == 2

    by_kind = {}
    for b in btns:
        doc = _parse_html(b["data"])
        kind = "html" if doc.ok else "md"
        assert kind not in by_kind, f"两口的产物判成了同一种（{kind}）：{[x['file_name'] for x in btns]}"
        by_kind[kind] = b

    md_b, html_b = by_kind["md"], by_kind["html"]
    # 后缀跟着自证类别走
    assert _ext(md_b["file_name"]) == "md" and _ext(html_b["file_name"]) == "html"
    # mime 也跟着走（这里唯一允许的字面量是媒体类型，不是界面文案）
    assert md_b["mime"] == "text/markdown" and html_b["mime"] == "text/html"
    # 标签里点明的格式与实际发货一致：可接受的名字**从 file_name 后缀与 mime 子类型推导**，
    # 抄不进本档（改措辞只要还标得出格式就不红；把两个标签对调、或删成「点这里」才红）
    for kind, b in by_kind.items():
        hints = {_ext(b["file_name"]), str(b["mime"]).split("/")[-1].lower()}
        label = b["label"].lower()
        assert any(h and h in label for h in hints), \
            f"标签没点明实际发货的格式 {sorted(hints)}：{b['label']!r} vs {b['file_name']!r}"
    assert md_b["label"] != html_b["label"], "两个口标签一模一样，用户分不出拿的是哪份"
    # 两份产物互不为子串：data 对调会当场红
    assert md_b["data"] != html_b["data"]


def test_md口发货的是结构完好的markdown文档(monkeypatch):
    """:264 data 的「可解析」= 有唯一 H1 首行 + 每张表格列数自洽且带分隔行，且不是一页 HTML。"""
    _fake_, _seen, btns = _generate(monkeypatch, click=0)
    md = next(b["data"] for b in btns if not _parse_html(b["data"]).ok)
    text = str(md)
    lines = text.split("\n")
    assert lines[0].startswith("# "), f"markdown 应以 ATX 一级标题起头，首行为 {lines[0]!r}"
    assert sum(1 for l in lines if l.startswith("# ") and not l.startswith("## ")) == 1, "H1 不止一个"
    blocks = _md_table_blocks(text)
    assert len(blocks) >= 2, f"报告至少应有总览/语言进度两张表，实得 {len(blocks)}"
    for block in blocks:
        assert len(block) >= 3, f"表格不足三行（表头/分隔/数据）：{block}"
        assert all(l.startswith("|") and l.endswith("|") for l in block), f"表格行未闭合：{block}"
        widths = {l.count("|") for l in block}
        assert len(widths) == 1, f"同一张表列数漂移：{block}"
        assert _is_delimiter_row(block[1]), f"第二行不是 markdown 分隔行：{block[1]!r}"
    assert "<html" not in text.lower(), "md 口里出现了 HTML 骨架"


def test_html口发货的是声明齐全且标签闭合的自包含页面(monkeypatch):
    """:272 data 的「可解析」= 有 doctype 声明、单一 html 根、标签全闭合、正文可见文本非空。"""
    _fake_, _seen, btns = _generate(monkeypatch, click=0)
    html_b = next(b for b in btns if _ext(b["file_name"]) == "html")
    doc = _parse_html(html_b["data"])
    assert doc.decls and doc.decls[0].lower().startswith("doctype"), f"缺文档声明：{doc.decls}"
    assert doc.opened.count("html") == 1, "html 根元素数量异常"
    assert {"head", "body", "table", "style"} <= set(doc.opened), doc.opened
    assert not doc.problems and not doc.stack, f"标签闭合破裂：{doc.problems} 残留栈 {doc.stack}"
    assert len("".join(doc.text)) > 100, "可见文本近乎为空，这份导出件等于一张白纸"


# ---------------------------------------------------------------------------
# 例 6～8：期别（file_name 单源段 / 同期同份 / 切换后不混档）
# ---------------------------------------------------------------------------

def test_文件名含单源期别段与渲染当日(monkeypatch):
    """:265/:273 file_name = 前缀 + `_report_file_tag(days)` 段 + 当日日期段。

    期别段现调生产函数推导（不写死 week/month），days 取自 session_state；
    日期段取**渲染当日**而非生成日。
    """
    fake, _seen, btns = _generate(monkeypatch, click=0, rerender=True)
    days = fake.session_state["last_report_days"]
    tag = dashboard_page._report_file_tag(days)
    today = date.today().isoformat()
    for b in btns:
        assert f"_{tag}_" in b["file_name"], f"期别段未按单源函数落进文件名：{b['file_name']} (tag={tag})"
        assert b["file_name"].endswith(f"{today}.{_ext(b['file_name'])}"), \
            f"文件名日期段应为渲染当日 {today}：{b['file_name']}"


def test_两个下载口出自同一期同一份报告(monkeypatch):
    """同一帧里 .md 与 .html 两路必须带同一期标记——只更新一条写入就是混档。"""
    fake, _seen, btns = _generate(monkeypatch, click=0)
    days = fake.session_state["last_report_days"]
    marker = f"tok{days}d"
    got = sorted(marker in str(b["data"]) for b in btns)
    assert got == [True, True], f"两份产物未同时带上本期标记 {marker}：{[(b['file_name'], marker in str(b['data'])) for b in btns]}"
    assert len({str(b["data"]) for b in btns}) == 2, "两口 data 撞成同一串，等于同一个格式发了两次"


def test_切到另一期后两个口与文件名一起跟上且旧期标记消失(monkeypatch):
    """点另一个生成口：两口的 data 与 file_name 同步换期，且不得残留上一期标记；重复渲染不重生。"""
    fake = _fake()
    seen = _wire(monkeypatch, fake)
    dao = _dao()
    dashboard_page._render_dashboard_body(dao)
    labels = [c[1][0] for c in _generator_buttons(fake)]

    fake.calls.clear()
    _wire(monkeypatch, fake, {labels[0]: True})
    dashboard_page._render_dashboard_body(dao)
    first_days = fake.session_state["last_report_days"]

    fake.calls.clear()
    _wire(monkeypatch, fake, {labels[1]: True})
    dashboard_page._render_dashboard_body(dao)
    second_days = fake.session_state["last_report_days"]
    assert seen == [first_days, second_days] and first_days != second_days, \
        f"两个生成口应分别投出不同期别，实为 {seen}"

    # 同一 fake 再渲染一帧、谁都不点：不该重新生成（下载区常驻靠的是 session_state）
    fake.calls.clear()
    _wire(monkeypatch, fake, {})
    dashboard_page._render_dashboard_body(dao)
    assert len(seen) == 2, f"未点按钮的渲染重新生成了一份报告：{seen}"

    btns = _buttons_of(fake)
    assert len(btns) == 2
    tag = dashboard_page._report_file_tag(second_days)
    for b in btns:
        assert f"tok{second_days}d" in str(b["data"]), f"产物仍停在上一期：{b['file_name']}"
        assert f"tok{first_days}d" not in str(b["data"]), f"混进了上一期的内容：{b['file_name']}"
        assert f"_{tag}_" in b["file_name"], f"文件名期别没跟上：{b['file_name']}"


# ---------------------------------------------------------------------------
# 例 9～10：help 与列布局（l923-11 登记的零覆盖面）
# ---------------------------------------------------------------------------

def test_html格式口带非空help且两个口的help不重复(monkeypatch):
    """:276 help 的覆盖面：需要交代「拿回去怎么用」的那张口必须真的交代了。

    「哪张口该有 help」由产物自证的类别决定（浏览器打开才能打印的那份才需要操作说明），
    不比对 help 内容本身——改措辞不红，删掉、清空或两条抄成一样才红。
    """
    _fake_, _seen, btns = _generate(monkeypatch, click=0)
    html_b = next(b for b in btns if _parse_html(b["data"]).ok)
    help_ = html_b["help"]
    assert isinstance(help_, str) and help_.strip(), "HTML 格式口的 help 缺失或为空串——用户无从知道下载回去干什么"
    helps = [str(b["help"] or "") for b in btns]
    assert len({h for h in helps if h}) == len([h for h in helps if h]), f"两口的 help 雷同：{helps}"
    assert help_ in str(html_b["kw"]["help"])


def test_两个下载口各占一列且都按容器宽度铺开(monkeypatch):
    """:254 的列槽与 :267/:275 的 use_container_width：布局参数是行为面，不是文案。"""
    fake, _seen, btns = _generate(monkeypatch, click=0)
    assert len(btns) == 2
    assert all(b["kw"].get("use_container_width") is True for b in btns), \
        f"下载口未铺开：{[(b['file_name'], b['kw'].get('use_container_width')) for b in btns]}"
    # 报告区的列布局：两卡一空槽（第三个槽位吃掉剩余宽度）
    idx = _caliber_index(fake)
    col_specs = [c[1][0] for c in fake.calls[idx:] if c[0] == "columns"]
    assert col_specs[:2] and len(col_specs[0]) == 3, f"报告区列槽结构漂移：{col_specs[:2]}"
    exp = [c for c in fake.calls if c[0] == "expander"]
    assert exp, "预览 expander 未被录制（实例级覆盖失效，基类失明面回来了）"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))


# ── l930-10：学习数据 .json 口三面看守（k927-38 遗留①收口——l924-02 只盖报告两枚，
#    本枚按 84d76ed 引入的导出口补：文案／mime／help 三面逐字钉）─────────────────────────
def test_学习数据json口_文案mime_help三面看守(monkeypatch):
    """render_dashboard 全渲染后收集**全部** download_button（不做报告区过滤），
    按 file_name 认出学习数据 .json 口，三面逐字钉：
    文案「⬇️ 导出全部学习数据 (.json)」／mime application/json／
    help「包含答题记录、错题、复习状态、成就与事件——可导入到另一台机器」。
    """
    fake = _fake()
    _wire(monkeypatch, fake)
    dashboard_page._render_dashboard_body(_dao())
    # label 是位置参（c[1][0]），mime/file_name/help 是关键字参（c[2]）——录参形状照 _buttons_of。
    all_downloads = [{"label": str(c[1][0]), "kw": c[2]} for c in fake.calls
                     if c[0] == "download_button"]
    json_btns = [d for d in all_downloads
                 if str(d["kw"].get("file_name", "")).startswith("learning_data_")]
    assert len(json_btns) == 1, f"学习数据 .json 口应恰 1 枚，实得 {len(json_btns)}"
    btn = json_btns[0]["kw"]
    label = json_btns[0]["label"]
    assert label == "⬇️ 导出全部学习数据 (.json)", f"文案漂移：{label!r}"
    assert btn.get("mime") == "application/json", f"mime 漂移：{btn.get('mime')!r}"
    assert btn.get("help") == "包含答题记录、错题、复习状态、成就与事件——可导入到另一台机器",         f"help 漂移：{btn.get('help')!r}"
