"""find_port 纯函数钉桩（l923-29）。

被测件 `scripts/find_port.py`（20 行）此前 **tests/ 零引用**（`git grep -n find_port -- tests/` 空），
而它是 `start.bat` 的**唯一端口来源**：

    start.bat:26  for /f %%p in ('"%PYTHON%" scripts\\find_port.py') do set "PORT=%%p"

⇒ find_port 一旦抛异常（而非走 `sys.exit` 出口）或改掉出口消息，`%PORT%` 变空、
整条 streamlit 启动链静默坏。本桩**零生产码改动**，只钉四条出口 + 入口接线：

① 有空闲口时：先真 bind 占掉区间起点，返回值仍落在 [start, end] 且不等于已占口；
② 全段占用时：走 SystemExit，消息含 `no free port in` 且与 find_port.py:16 字面一致；
③ 边界 start == end：空闲口与占用口两分支各一例；
④ 入口接线与两处源码锚点（:6 签名 / :16 出口 / start.bat:26）钉死，防静默改线。

①③ 用真 socket（bind 端口 0 让内核挑口，避免与本机服务抢口）；② 用注入的假 socket 模块，
只替换被测件的视图 ⇒ 不 patch 全局 stdlib、不碰别的用例。
"""

import inspect
import socket
from pathlib import Path

import pytest

from scripts import find_port as fp

ROOT = Path(__file__).resolve().parents[1]


def _hold_a_port():
    """真占一个内核分配的空闲 TCP 口并持有它（返回 (socket, port)）。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    return s, s.getsockname()[1]


class FakeSock:
    """假 socket：bind 按 bind_ok 决定成败（False 模拟 EADDRINUSE），并登记自身供 close 审计。"""

    def __init__(self, registry, bind_ok=True):
        self.registry = registry
        self.bind_ok = bind_ok
        self.closed = False
        registry.append(self)

    def bind(self, addr):
        if not self.bind_ok:
            raise OSError(10048, "Only one usage of each socket address is normally permitted")

    def close(self):
        self.closed = True


class FakeSocketModule:
    """替换 fp.socket 用：只提供 find_port 用到的三个名字，真 stdlib 全程不受影响。"""

    AF_INET = socket.AF_INET
    SOCK_STREAM = socket.SOCK_STREAM

    def __init__(self, bind_ok=True):
        self.bind_ok = bind_ok
        self.created = []

    def socket(self, *args, **kwargs):
        return FakeSock(self.created, self.bind_ok)


# ① ---------------------------------------------------------------- 正常路径
def test_有空闲口时返回值落在区间内且跳过已占口():
    sock, busy = _hold_a_port()
    try:
        got = fp.find_port(busy, busy + 2)  # 已占口正好当区间起点 ⇒ 它必不可返回
        assert busy <= got <= busy + 2, f"返回值 {got} 越界 [{busy}, {busy + 2}]"
        assert got != busy, "返回了刚被自己占住的端口 ⇒ find_port 的占用检测失效"
    finally:
        sock.close()


def test_返回的口在返回后确实可绑定_即函数没有把口泄漏出去():
    """find_port 是 bind 完立刻 close 再返回（靠 OS 重新放行）；
    若哪天改成「持有 socket 返回」，第二个 bind 就会失败 ⇒ 本例当场转红。"""
    sock, busy = _hold_a_port()
    try:
        got = fp.find_port(busy, busy + 2)
    finally:
        sock.close()
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind(("127.0.0.1", got))  # 不抛＝该口当前空闲
    finally:
        probe.close()


# ② ---------------------------------------------------------------- 全段占用
def test_全段占用时走SystemExit出口且消息含_no_free_port_in(monkeypatch):
    mod = FakeSocketModule(bind_ok=False)
    monkeypatch.setattr(fp, "socket", mod)  # 只换被测件视图，monkeypatch 自动还原真 stdlib 引用
    with pytest.raises(SystemExit) as ei:
        fp.find_port(9000, 9003)
    msg = str(ei.value)
    assert "no free port in" in msg, f"出口消息变了：{msg!r}"
    assert msg == "no free port in 9000-9003", msg
    assert len(mod.created) == 4, f"应对 9000..9003 逐个试口，实得 {len(mod.created)}"
    assert all(s.closed for s in mod.created), "试口失败后必须 close，否则每次启动漏 4 个 fd"


def test_试口成功即返回_不再往下多绑(monkeypatch):
    """区段够长时只应创建 1 个 socket（第 2 个的语义是「别把整个区间扫一遍」）。"""
    mod = FakeSocketModule(bind_ok=True)
    monkeypatch.setattr(fp, "socket", mod)
    assert fp.find_port(9100, 9105) == 9100
    assert len(mod.created) == 1, "首个空闲口即返回，不该继续扫"
    assert all(s.closed for s in mod.created)


# ③ ---------------------------------------------------------------- 边界 start == end
def test_单口区间_空闲时原样返回该口():
    # bind 端口 0 由内核挑 ⇒ 必成功 ⇒ find_port(0, 0) 的返回值必是 0，与本机环境无关
    assert fp.find_port(0, 0) == 0


def test_单口区间_被占时SystemExit且消息形如_no_free_port_in_P_P():
    sock, busy = _hold_a_port()
    try:
        with pytest.raises(SystemExit) as ei:
            fp.find_port(busy, busy)
        assert str(ei.value) == f"no free port in {busy}-{busy}"
    finally:
        sock.close()


def test_默认区间是_8511_到_8530_且签名未漂():
    """签名默认值一被改动，start.bat 与心理系统 8501 的错开口径就变了 ⇒ 钉字面。"""
    sig = inspect.signature(fp.find_port)
    assert (sig.parameters["start"].default, sig.parameters["end"].default) == (8511, 8530)


# ④ ---------------------------------------------------------------- 入口接线与源码锚点
def test_源码锚点与start_bat接线仍与磁盘一致():
    lines = (ROOT / "scripts" / "find_port.py").read_text(encoding="utf-8").splitlines()
    assert lines[5].startswith("def find_port(start: int = 8511, end: int = 8530)"), lines[5]
    assert lines[15].strip() == 'sys.exit(f"no free port in {start}-{end}")', lines[15]

    bat = (ROOT / "start.bat").read_text(encoding="utf-8", errors="replace").splitlines()
    wiring = [l for l in bat if "find_port.py" in l]
    assert len(wiring) == 1, f"start.bat 里 find_port 接线应恰 1 条，实得 {len(wiring)}"
    assert "for /f" in wiring[0] and "PORT" in wiring[0], wiring[0]
    assert bat.index(wiring[0]) + 1 == 26, (
        f"start.bat 接线行号漂到 {bat.index(wiring[0]) + 1}（本桩钉 :26）"
        "⇒ 要么入口动了、要么该同步本桩，两者都必须显式改")
