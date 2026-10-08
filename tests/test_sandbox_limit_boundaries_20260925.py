# -*- coding: utf-8 -*-
"""沙箱限额的**边界样本**＋**异常进程回收**证据包。

对应信箱单 `20260925-120548-16e3`（A 档／test；执行班 `qoder-executor-20260925-1630-learn38`）。

卷宗原文：「验证 CPU、内存、输出长度、进程数和超时限制。
验收：每项限制有边界样本、退出码和用户提示；异常进程被回收。」

**先证其在世**（本仓实况，逐条可复算；与卷宗不符处按实况收窄，不判 failed）：

| 卷宗点名的限额 | 本仓是否存在 | 实际生效物（单一来源） |
|---|---|---|
| 输出长度 | ✅ 有 | `python_runner.MAX_STDOUT_BYTES`(1 MB)／`MAX_STDERR_BYTES`(100 KB)／`_MAX_STDIN_BYTES`(1 MB) |
| 超时 | ✅ 有 | `PythonRunner.timeout_sec`(5 秒，**墙钟**) |
| 进程数 | ❌ **无此限额** | 仅事后回收：`_kill_tree`（Windows `taskkill /F /T`） |
| CPU 时间 | ❌ **无此限额** | 只有上面的墙钟兜底，无 CPU 时间片核算 |
| 内存 | ❌ **无此限额** | 学生代码越界由 OS 抛 `MemoryError`，失败被隔离在子进程 |

⇒ 后三项作为**缺陷登记**（见 `TestMissingCapsLedgerPin`）随 result 交回主班；
本包**不改任何判分口径／分值／通过失败判定**，只把"实际边界"钉成可复算断言。

覆盖面自证（纪律 §五）：每条负向断言都配一条**同量的正向对照**
（限额内不截断／活进程探得／子进程真被收），避免"恒绿假断言"。
"""
import subprocess
import sys
from pathlib import Path

import pytest

from core.progress import ProgressDAO
from core.runners.error_feedback import timeout_message
from core.runners.python_runner import (
    MAX_STDERR_BYTES,
    MAX_STDOUT_BYTES,
    _MAX_STDIN_BYTES,
    PythonRunner,
)

REPO = Path(__file__).resolve().parents[1]

TRUNC_MARK = "输出过长，已截断"


@pytest.fixture(scope="module")
def runner():
    return PythonRunner()


@pytest.fixture(autouse=True)
def _sandbox_progress_db(monkeypatch, tmp_path):
    """头号硬警示的防线：`judge._record_attempt(dao=None)` 会自开**生产库**。

    本包只跑 runner、不碰判题链；仍把无参回退关进 `tmp_path`，
    这样将来有人往本文件里加 `judge()` 用例时不会打到 `data/progress.db`。
    """
    fake = tmp_path / "learn38-limits-sandbox.db"
    monkeypatch.setenv("LS_PROGRESS_DB", str(fake))
    assert ProgressDAO().db_path == str(fake)
    yield fake


def _pid_alive(pid: int) -> bool:
    """只读存活探测（不 kill、不写盘）；Windows 用 `tasklist`，其余用信号 0。"""
    if sys.platform == "win32":
        # l1010-33 修：中文 Windows 的 tasklist 输出是 GBK（无匹配时的提示行含中文字节），
        # text=True 按 UTF-8 解码会在 reader 线程抛 UnicodeDecodeError ⇒ stdout=None。
        # 探测只依赖 ASCII 的 pid 子串：按字节取回再 ignore 解码即可。
        out = subprocess.run(
            ["tasklist", "/FI", "PID eq %d" % pid, "/NH"],
            capture_output=True,
        ).stdout
        out = (out or b"").decode("utf-8", errors="ignore")
        return "No tasks are running" not in out and str(pid) in out
    import os
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _spawn_sleepers(n: int) -> list:
    procs = [subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
             for _ in range(n)]
    return procs


# ---------------------------------------------------------------------------
# 1) 输出长度限额：边界样本（限额整／限额＋1）＋退出码＋用户提示
# ---------------------------------------------------------------------------

class TestStdoutCapBoundary:
    def test_exactly_at_cap_emits_no_truncation_hint(self, runner):
        """边界样本·下沿：字节数 == 限额时**不得**出现截断提示（`<=` 不是 `<`）。"""
        r = runner.run("import sys\nsys.stdout.write('A' * %d)" % MAX_STDOUT_BYTES)
        assert r.exit_code == 0
        assert TRUNC_MARK not in r.stdout
        assert len(r.stdout.encode("utf-8")) == MAX_STDOUT_BYTES

    def test_one_byte_over_cap_truncates_to_cap_and_shows_hint(self, runner):
        """边界样本·上沿：限额＋1 字节即截断，正文恰为限额字节，且带用户可读提示。"""
        r = runner.run("import sys\nsys.stdout.write('A' * %d)" % (MAX_STDOUT_BYTES + 1))
        assert TRUNC_MARK in r.stdout, "越界必须给出可读提示，不能静默丢内容"
        body, _, _mark = r.stdout.partition("\n[")
        assert len(body.encode("utf-8")) == MAX_STDOUT_BYTES
        assert r.exit_code == 0
        assert r.ok is True  # 截断不是学生的错：不改判分口径

    def test_multibyte_char_is_never_split(self, runner):
        """截断点落在 UTF-8 半个字符上：丢整字符，**不许**留替换符。"""
        n = MAX_STDOUT_BYTES // 3 + 99  # 3 字节/字 ⇒ 限额处必切在半字符上
        assert n * 3 > MAX_STDOUT_BYTES
        r = runner.run("import sys\nsys.stdout.write('中' * %d)" % n)
        assert "\ufffd" not in r.stdout, "半个字符会变成 ? 乱码，学生读不懂"
        assert r.stdout.count("中") == MAX_STDOUT_BYTES // 3
        assert TRUNC_MARK in r.stdout

    def test_windows_crlf_bytes_count_toward_the_cap(self, runner):
        """实况登记：Windows 下 `print` 的换行是 `\r\n`，**两个字节都算进限额**。

        这正是"限额整的 `print`"会被截断的原因（多出的 1 字节就是那个 `\r`）。
        卷宗说"每项限制有边界样本"——边界必须按**字节**而非"字符数"表述。
        """
        at_chars = runner.run("print('A' * %d)" % (MAX_STDOUT_BYTES - 1))
        assert TRUNC_MARK in at_chars.stdout  # 1_000_000 A + \r\n = 1_000_002 > 限额
        assert at_chars.exit_code == 0
        under = runner.run("print('A' * %d)" % (MAX_STDOUT_BYTES - 2))
        assert TRUNC_MARK not in under.stdout  # 999_998 A + \r\n = 1_000_000 == 限额


# ---------------------------------------------------------------------------
# 2) stderr 限额（100 KB）：同样两侧夹逼
# ---------------------------------------------------------------------------

class TestStderrCapBoundary:
    @pytest.mark.parametrize("count,expect_hint", [
        (MAX_STDERR_BYTES, False),
        (MAX_STDERR_BYTES + 1, True),
    ])
    def test_stderr_cap_edges(self, runner, count, expect_hint):
        r = runner.run("import sys\nsys.stderr.write('E' * %d)" % count)
        assert (TRUNC_MARK in r.stderr) is expect_hint
        assert r.exit_code == 0
        assert len(r.stderr.encode("utf-8")) <= MAX_STDERR_BYTES + 60
        assert r.stderr.count("E") <= MAX_STDERR_BYTES

    def test_stderr_flood_never_kills_the_host_process(self, runner):
        """用户提示口径：stderr 洪泛不触发超时、不改判定（服务进程不退出）。"""
        r = runner.run("import sys\n"
                       "for _ in range(5000):\n"
                       "    sys.stderr.write('x' * 100)\n"
                       "print('survived')\n")
        assert r.timed_out is False
        assert r.stdout.strip() == "survived"
        assert r.exit_code == 0


# ---------------------------------------------------------------------------
# 3) stdin 限额：静默截断＝缺陷登记（D-1）
# ---------------------------------------------------------------------------

class TestStdinCap:
    def test_stdin_over_cap_is_truncated_silently(self, runner):
        """**缺陷 D-1**：输入超 1 MB 被截断，但 `stdout`／`stderr` 里**一个字都没提**，
        退出码仍是 0 ⇒ 学生只会看到"答案错了"，看不到原因。只登记不改行为。
        """
        payload = "a" * (_MAX_STDIN_BYTES + 4096)
        r = runner.run("import sys\nprint(len(sys.stdin.buffer.read()))", stdin=payload)
        assert r.stdout.strip() == str(_MAX_STDIN_BYTES)  # 实况：截到限额
        assert r.exit_code == 0
        assert TRUNC_MARK not in r.stderr and TRUNC_MARK not in r.stdout
        assert "截断" not in r.stderr and "截断" not in r.stdout

    def test_stdin_within_cap_arrives_byte_for_byte(self, runner):
        """正向对照：限额内一字不差（证明上一条不是"输入根本没送到"）。"""
        payload = "b" * (_MAX_STDIN_BYTES - 1)
        r = runner.run("import sys\nprint(len(sys.stdin.buffer.read()))", stdin=payload)
        assert r.stdout.strip() == str(_MAX_STDIN_BYTES - 1)

    def test_surrogate_pair_input_does_not_raise(self, runner):
        """孤立代理对：`_safe_stdin` 用 `errors='replace'`，不得让执行器抛异常。

        实况钉子：UTF-8 编码器遇孤立代理对时替换为**单字节 `?`**（不是 U+FFFD 的 3 字节）
        ⇒ 4×("\ud800"→1B + "abc"→3B) = 16 字节送达，而不是卷面直觉的 24。
        """
        r = runner.run("import sys\nprint(len(sys.stdin.buffer.read()))",
                       stdin="\ud800abc" * 4)
        assert r.exit_code == 0
        assert r.stdout.strip() == "16"
        shown = runner.run("import sys\nprint(sys.stdin.buffer.read().decode())",
                           stdin="\ud800ok")
        assert "?ok" in shown.stdout


# ---------------------------------------------------------------------------
# 4) 超时限额：墙钟边界＋统一话术＋退出码
# ---------------------------------------------------------------------------

class TestTimeoutBoundary:
    def test_within_budget_exits_zero(self, runner):
        """边界样本·下沿：预算内的慢程序正常判定，退出码 0、无超时话术。"""
        budget = runner.timeout_sec
        r = runner.run("import time\ntime.sleep(%d)\nprint('done')" % max(1, budget - 3))
        assert r.timed_out is False
        assert r.exit_code == 0
        assert r.stdout.strip() == "done"
        assert r.stderr == ""

    def test_runaway_cpu_is_cut_at_wall_clock_budget(self, runner):
        """边界样本·上沿：死循环被墙钟砍掉；退出码为 `None`（进程是被杀的）。

        本仓**没有 CPU 时间片限额**——这里能观察到的唯一上界就是墙钟，
        实测含 `taskkill` 开销约 5.8 秒（断言给到 20 秒防并发机时抖动）。
        """
        r = runner.run("while True: pass")
        assert r.timed_out is True
        assert r.ok is False
        assert r.exit_code is None
        assert r.error_kind == "timeout"
        assert "%d 秒" % runner.timeout_sec in r.stderr, "用户提示必须带上预算秒数"
        assert runner.timeout_sec * 1000 <= r.elapsed_ms < 20_000

    def test_timeout_wording_comes_from_the_shared_table(self, runner):
        """话术单一来源：Python 侧超时文案 == `error_feedback.timeout_message`。"""
        r = runner.run("while True: pass")
        assert r.stderr == timeout_message("代码运行", runner.timeout_sec,
                                           "已强制终止，可能存在死循环")

    def test_sleeping_process_also_times_out_and_returns_hint(self, runner):
        """睡死型超时（不烧 CPU）同样被回收，验证限额是墙钟而非 CPU。"""
        r = runner.run("import time\ntime.sleep(300)")
        assert r.timed_out is True
        assert r.exit_code is None
        assert "超时" in r.stderr


# ---------------------------------------------------------------------------
# 5) 异常进程回收：孙进程也要收，且探测器本身要先证明有牙
# ---------------------------------------------------------------------------

class TestProcessTreeReaping:
    def test_pid_detector_distinguishes_alive_from_dead(self):
        """探测器正向对照：活进程读真、终止后读假——否则下面的"已回收"是恒真断言。"""
        procs = _spawn_sleepers(1)
        pid = procs[0].pid
        try:
            assert _pid_alive(pid) is True
        finally:
            procs[0].terminate()
            procs[0].wait(timeout=15)
        assert _pid_alive(pid) is False

    def test_direct_children_of_runaway_code_are_all_reaped(self, runner, tmp_path):
        """学生代码派生的子进程：超时后不得留在机器上（"异常进程被回收"）。

        PID 走**文件回传**而非 stdout：真·树杀后管道才会 EOF，
        并发机时下 `communicate(timeout=2)` 有取空的风险（变异件 m3 就是这一面）。
        """
        pidfile = tmp_path / "learn38_pids.txt"
        code = (
            "import subprocess, sys, time\n"
            "ps = [subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)'])"
            " for _ in range(4)]\n"
            "open(%r, 'w').write(' '.join(str(p.pid) for p in ps))\n"
            "time.sleep(600)\n" % str(pidfile)
        )
        r = runner.run(code)
        assert r.timed_out is True
        assert pidfile.exists(), "子进程 PID 没回传就无法证明回收"
        pids = [int(t) for t in pidfile.read_text().split()]
        try:
            assert len(pids) == 4
            for pid in pids:
                assert _pid_alive(pid) is False, "残留孤儿进程：%d" % pid
        finally:
            for pid in pids:  # 兜底清理：断言失败也不把 600 秒进程留在机器上
                if _pid_alive(pid):
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                                   capture_output=True)


# ---------------------------------------------------------------------------
# 6) 缺失限额的缺陷登记（D-2/D-3/D-4）＋既有限额单一来源
# ---------------------------------------------------------------------------

#: 卷宗点名的三类限额在本仓的"实现痕迹"关键词（POSIX rlimit / Windows Job Object / 自研计数）
_MISSING_CAP_MARKERS = (
    "setrlimit", "RLIMIT_", "resource.", "Job Object", "CreateJobObject",
    "AssignProcessToJobObject", "MAX_PROCESSES", "memory_limit", "MAX_MEMORY",
    "cpu_time", "CPU_TIME", "nproc",
)

#: 只扫这些件——扫描面必须非空，否则"零命中"是假象
_CAP_SCAN_GLOBS = ("core/runners/*.py", "core/config.py")

#: 分母＝真的有内容的件（`core/runners/__init__.py` 是 0 字节空件，不参与"读到内容"自证）
_CAP_SCAN_FILES = sorted(
    p for g in _CAP_SCAN_GLOBS for p in REPO.glob(g) if p.is_file() and p.stat().st_size > 0
)


class TestMissingCapsLedgerPin:
    def test_scan_surface_is_not_empty(self):
        """覆盖面自证：先证明"扫过几份文件"，再谈"扫到 0 处"（纪律 §五.6）。

        实况：`core/runners/__init__.py` 是 0 字节空件，计入分母会让
        "每份都读到了内容"这条自证恒假 ⇒ 分母只算非空件（现值 8 份）。
        """
        all_files = sorted({p for g in _CAP_SCAN_GLOBS for p in REPO.glob(g) if p.is_file()})
        assert len(all_files) == len(_CAP_SCAN_FILES) + 1, all_files  # 只允许那一份空 __init__
        assert len(_CAP_SCAN_FILES) >= 7, _CAP_SCAN_FILES
        assert all(f.read_text(encoding="utf-8").strip() for f in _CAP_SCAN_FILES)

    def test_no_cpu_memory_or_process_count_cap_is_implemented(self):
        """**缺陷登记 D-2/D-3/D-4**：CPU 时间、内存、进程数三类限额**全无实现**。

        本用例是"缺席钉子"：将来真接了 rlimit/Job Object，它会转红——
        那时应连同 result 里的缺陷条目一起改写，而不是当回归消红。
        """
        files = _CAP_SCAN_FILES
        hits = [(f.relative_to(REPO).as_posix(), m)
                for f in files
                for m in _MISSING_CAP_MARKERS
                if m in f.read_text(encoding="utf-8")]
        assert hits == [], (
            "限额已实现？请同步撤销本钉子并回报主班。扫描面 %d 份文件，命中 %r"
            % (len(files), hits)
        )

    def test_runaway_memory_surfaces_as_child_error_not_runner_crash(self, runner):
        """D-3 的可观察后果：没有内存上限 ⇒ 兜底只剩 OS 的 `MemoryError`。

        退出码非 0、错误落在**子进程**里，执行器（pytest 进程）安然无恙。
        """
        r = runner.run("x = bytearray(10 ** 12)\nprint('allocated')")
        assert r.ok is False
        assert r.exit_code not in (0, None)
        assert "MemoryError" in r.stderr
        assert "%d 秒" % runner.timeout_sec not in r.stderr  # 不是被超时救的

    def test_children_are_not_capped_at_spawn_time(self, runner):
        """D-4 的可观察后果：派生子进程在**创建时**不受任何计数限制。

        与 `TestProcessTreeReaping` 配对：那里证"事后回收"，这里证"事前不挡"。
        """
        code = (
            "import subprocess, sys\n"
            "ps = [subprocess.Popen([sys.executable, '-c', 'pass']) for _ in range(5)]\n"
            "print(len(ps), flush=True)\n"
            "for p in ps:\n"
            "    p.wait(timeout=20)\n"
            "print('waited', flush=True)\n"
        )
        r = runner.run(code)
        assert "5" in r.stdout.splitlines()[0]
        assert r.exit_code == 0
        assert r.timed_out is False


class TestCapsSingleSource:
    """正向钉子：既有限额**只有一处定义**，四语言 runner 共用（防限额漂移）。"""

    def test_r_and_cpp_runners_import_the_python_byte_caps(self):
        py = (REPO / "core" / "runners" / "python_runner.py").read_text(encoding="utf-8")
        assert "MAX_STDOUT_BYTES = 1_000_000" in py
        assert "MAX_STDERR_BYTES = 100_000" in py
        assert "_MAX_STDIN_BYTES = 1_000_000" in py
        for lang in ("r_runner", "cpp_runner"):
            src = (REPO / "core" / "runners" / f"{lang}.py").read_text(encoding="utf-8")
            assert "MAX_STDOUT_BYTES, MAX_STDERR_BYTES" in src, lang
            assert "python_runner import" in src, lang

    def test_byte_cap_values_are_the_documented_ones(self):
        assert (MAX_STDOUT_BYTES, MAX_STDERR_BYTES, _MAX_STDIN_BYTES) == (
            1_000_000, 100_000, 1_000_000,
        )
