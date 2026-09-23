"""l923-32：`scripts/bench_imports.py`／`bench_pages.py`／`prof_pages.py` 三件 dev 工具的烟雾钉桩。

为什么要有这个文件（卷宗原话的展开）：三件是**无 CI 面**的开发工具，`tests/` 此前对它们
**零引用**（实测 `rg -n "bench_imports|bench_pages|prof_pages" tests/` rc=1）。页面或模块改名时
最先静默坏的就是这类清单型脚本——坏的时候没人看见，要用的时候才发现跑不起来。

三条设计约束（都在下面的断言里兑现）：
1. **绝不在本测试里 import `bench_imports`**：它的模块体没有 `main()`、也没有 `if __name__` 守卫，
   `MODS` 后面那段 `for name, stmt in MODS:` 在 **import 期就会起 9 个子进程跑基准**（`timeout=180`）。
   所以清单一律用 `ast` 静态解析取，目标可解析性用 `importlib.util.find_spec`（`ui`／`core`／`ui.pages`
   三个 `__init__.py` 实测均为 0 字节空档 ⇒ find_spec 不会把 streamlit/pandas 拖进本进程）。
2. `bench_pages` / `prof_pages` 顶层导入**必须在子进程里做**：两者 import 期就会把
   `streamlit.cache_data` / `cache_resource` 换成直通装饰器（全局副作用），污染 pytest 进程里的真 streamlit。
3. 卷宗写「以 `--help` 或参数解析干跑（**若有 argparse**）」。实测三件**全无 argparse**
   （`prof_pages.py:34` 只是裸读 `sys.argv[1]`）⇒ 走「main() 存在性 ＋ 顶层导入零异常」这一支；
   下面的用例把这个条件写成**运行期分支**，将来真加了 CLI 它会自动改跑 `--help` 而不会假绿。

另外钉一条数据面护栏：两件的 `main()` 会把 `core.progress._DEFAULT_DB` 指向临时副本（docstring 自称
"Read-only by design"）。若有人把 `main()` 的调用挪到模块级，导入即改库指向 ⇒ 本文件当场红。
"""
import ast
import py_compile
import subprocess
import sys
from importlib.util import find_spec
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
TOOLS = ["bench_imports.py", "bench_pages.py", "prof_pages.py"]
PAGES_TOOLS = ["bench_pages", "prof_pages"]


def _src(name: str) -> str:
    return (SCRIPTS / name).read_text(encoding="utf-8")


def _resolvable(modname: str) -> bool:
    """find_spec 对缺失的顶层包会抛 ModuleNotFoundError，统一收成 False。"""
    try:
        return find_spec(modname) is not None
    except (ModuleNotFoundError, ValueError, ImportError):
        return False


def _mods_assignment():
    for node in ast.parse(_src("bench_imports.py")).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "MODS" for t in node.targets
        ):
            return node
    pytest.fail("scripts/bench_imports.py 里找不到模块级 MODS 赋值"
                "（清单被改名、被搬进函数或整件删除 ⇒ 本钉桩要的红）")


# ① 编译烟测：三件都要能编译（零落盘语法闸 ＋ 真 py_compile 写进 tmp_path）
@pytest.mark.parametrize("name", TOOLS)
def test_dev_tool_compiles(name, tmp_path):
    src = _src(name)
    compile(src, str(SCRIPTS / name), "exec")
    out = py_compile.compile(str(SCRIPTS / name), cfile=str(tmp_path / "x.pyc"), doraise=True)
    assert Path(out).exists()


# ② 清单锚定 A：MODS 必须是 (label, stmt) 字符串对，label 不得重复
def test_bench_imports_mods_is_label_stmt_pairs():
    elts = _mods_assignment().value.elts
    assert elts, "MODS 被清空 ⇒ 导入基准失去看守对象"
    labels = []
    for entry in elts:
        assert isinstance(entry, ast.Tuple) and len(entry.elts) == 2, \
            f"MODS 条目必须是 (label, stmt) 二元组，实得 {ast.dump(entry)[:120]}"
        label, stmt = entry.elts
        assert isinstance(label, ast.Constant) and isinstance(label.value, str) and label.value.strip()
        assert isinstance(stmt, ast.Constant) and isinstance(stmt.value, str) and stmt.value.strip()
        labels.append(label.value)
    assert len(set(labels)) == len(labels), f"MODS label 重复：{labels}"


# ② 清单锚定 B：每个 stmt 侧的 import 目标必须在盘上解析得到（改名／删除当场红）
def test_bench_imports_mods_targets_exist():
    for entry in _mods_assignment().value.elts:
        label, stmt = (c.value for c in entry.elts)
        tree = ast.parse(stmt)
        assert tree.body, f"MODS 条目 {label!r} 的 stmt 是空语句"
        targets = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                targets += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                assert node.level == 0, f"{label!r} 用了相对导入，find_spec 口径不适用：{stmt!r}"
                targets.append(node.module)
            else:
                pytest.fail(f"MODS 条目 {label!r} 的 stmt 含非 import 语句：{stmt!r}")
        assert targets, f"MODS 条目 {label!r} 解析不出任何 import 目标"
        for modname in targets:
            assert _resolvable(modname), \
                f"MODS 条目 {label!r} 的 import 目标 {modname!r} 已不在盘上（模块改名或删除）"


# ③ 两件页面级基准：main() 存在 ＋ 顶层导入零异常（有 argparse 就改跑 --help），全部在子进程里做
@pytest.mark.parametrize("modname", PAGES_TOOLS)
def test_pages_tool_imports_clean_without_running_main(modname):
    path = SCRIPTS / f"{modname}.py"
    has_argparse = "argparse" in _src(path.name)
    code = (
        "import importlib.util as iu, sys\n"
        f"spec = iu.spec_from_file_location({modname!r}, {str(path)!r})\n"
        "mod = iu.module_from_spec(spec)\n"
        "spec.loader.exec_module(mod)\n"
        "import core.progress as cp\n"
        "print('IMPORT_OK')\n"
        "print('MAIN_CALLABLE', callable(getattr(mod, 'main', None)))\n"
        "print('DEFAULT_DB', cp._DEFAULT_DB)\n"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       encoding="utf-8", timeout=180, cwd=str(ROOT))
    assert r.returncode == 0, f"{modname} 顶层导入失败 rc={r.returncode}\n{r.stderr[-900:]}"
    lines = r.stdout.splitlines()
    assert "IMPORT_OK" in lines, f"{modname} 导入未走完：stdout={r.stdout[-300:]!r}"
    assert "MAIN_CALLABLE True" in r.stdout, f"{modname} 没有可调用的 main()"
    # main() 一旦在导入期被误调用，_DEFAULT_DB 会被换成 ls_bench_/ls_prof_ 临时副本
    db_line = next(l for l in lines if l.startswith("DEFAULT_DB "))
    assert "ls_bench_" not in db_line and "ls_prof_" not in db_line, \
        f"{modname} 在导入期就跑了 main()（_DEFAULT_DB 已被换成临时副本）：{db_line}"
    if has_argparse:  # 将来加了 CLI ⇒ 顺手把 --help 干跑一次
        h = subprocess.run([sys.executable, str(path), "--help"], capture_output=True,
                           text=True, encoding="utf-8", timeout=180, cwd=str(ROOT))
        assert h.returncode == 0, f"{modname} --help 失败：{h.stderr[-300:]}"


# ③ 附：三件都不得在模块级被 import 时就产生真库写入（钉住 dev 工具的只读自我承诺）
def test_pages_tools_declare_temp_copy_before_real_db():
    for modname in PAGES_TOOLS:
        tree = ast.parse(_src(f"{modname}.py"))
        assigns = [n for n in tree.body if isinstance(n, ast.Assign)]
        assert not any(
            any(isinstance(t, ast.Attribute) and t.attr == "_DEFAULT_DB" for t in n.targets)
            for n in assigns
        ), f"{modname} 在模块级改了 core.progress._DEFAULT_DB ⇒ dev 工具不再保证不碰真库"
