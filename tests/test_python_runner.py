from core.runners.python_runner import PythonRunner


def test_hello_world():
    r = PythonRunner().run('print("Hello, World!")')
    assert r.ok
    assert "Hello, World!" in r.stdout
    assert r.exit_code == 0
    assert not r.timed_out


def test_syntax_error_kind():
    """r5 B3（2026-09-27 用户裁决）：未闭合括号＝**编译期**错误 ⇒ error_kind='syntax'。

    改前一律 'runtime'（词表里没有 syntax），判分反馈看不出是"解释器拒收"还是"跑起来才炸"。
    """
    r = PythonRunner().run("print('oops'")
    assert not r.ok
    assert r.error_kind == "syntax"
    assert "SyntaxError" in r.stderr or "EOF" in r.stderr


def test_stdin_passed():
    code = "import sys\nline = sys.stdin.readline().strip()\nprint(int(line) * 2)"
    r = PythonRunner().run(code, stdin="7\n")
    assert r.ok
    assert r.stdout.strip() == "14"


def test_timeout():
    r = PythonRunner().run("while True: pass")
    assert not r.ok
    assert r.timed_out
    assert r.error_kind == "timeout"
