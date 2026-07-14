import os
import pytest

from core.runners.cpp_runner import CppRunner


def _gpp_available():
    if CppRunner()._resolve_compiler():
        return True
    return False


pytestmark = pytest.mark.skipif(not _gpp_available(), reason="g++ not available; skipping C++ runner tests")


def test_hello_world():
    code = (
        '#include <iostream>\n'
        'using namespace std;\n'
        'int main() { cout << "Hello, World!" << endl; return 0; }\n'
    )
    r = CppRunner().run(code)
    assert r.ok
    assert "Hello, World!" in r.stdout


def test_compile_error():
    code = '#include <iostream>\nint main() { cout << "oops" }\n'
    r = CppRunner().run(code)
    assert not r.ok
    assert r.error_kind == "compile"


def test_stdin_passed():
    code = (
        '#include <iostream>\nusing namespace std;\n'
        'int main() { int a, b; cin >> a >> b; cout << a + b << endl; return 0; }\n'
    )
    r = CppRunner().run(code, stdin="3 5\n")
    assert r.ok
    assert r.stdout.strip() == "8"


def test_sandbox_when_no_gpp(monkeypatch):
    monkeypatch.setattr("core.runners.cpp_runner.shutil.which", lambda _: None)
    monkeypatch.setattr(CppRunner, "fallback_paths", [])
    r = CppRunner().run('int main(){return 0;}')
    assert not r.ok
    assert r.error_kind == "sandbox"
